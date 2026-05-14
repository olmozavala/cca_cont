import pandas as pd
from datetime import datetime, timedelta
from .sql_con import get_db_engine, POLLUTANT_MAPPING, METEOROLOGY_MAPPING

# When aligning ``hour_pNN`` to valid time ``issue_fecha + N hours``, the dashboard
# needs issue rows back to ``start_date - N`` (e.g. noon P01 needs the row issued at 11:00).
# Largest ``hour_pNN`` lead read in forecast queries (p24 time series; p17 in daily-max).
FORECAST_OTRES_ISSUE_PAD_HOURS: int = 24


def get_stations_data():
    """Fetch stations data for the dropdown, filtering for stations with lastyear > 3000."""
    engine = get_db_engine()
    if engine is None:
        return pd.DataFrame()
    
    try:
        query = """
        SELECT id, nombre, ST_X(geom) as longitude, ST_Y(geom) as latitude, altitude, lastyear 
        FROM cont_estaciones 
        WHERE lastyear > 3000
        ORDER BY nombre
        """
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        print(f"Error fetching stations: {e}")
        return pd.DataFrame()


def get_station_name(station_id: str) -> str:
    """Get the full name of a station by ID."""
    df = get_stations_data()
    if df.empty:
        return station_id
    
    station_row = df[df['id'] == station_id]
    if not station_row.empty:
        return f"{station_row.iloc[0]['nombre']} ({station_id})"
    return station_id


def get_pollutant_data(station_id: str, pollutant: str, start_date: datetime, window_hours: int):
    """Fetch pollutant data for a specific station and time period."""
    engine = get_db_engine()
    if engine is None:
        return pd.DataFrame()
    
    try:
        end_date = start_date + timedelta(hours=window_hours)
        table_name = f"cont_{pollutant}"
        
        if station_id == 'all_stations':
            # Query for all stations
            query = f"""
            SELECT fecha, val, id_est 
            FROM {table_name} 
            WHERE fecha >= %(start_date)s 
            AND fecha <= %(end_date)s 
            ORDER BY fecha, id_est
            """
            params = {
                'start_date': start_date,
                'end_date': end_date
            }
        else:
            # Query for specific station
            query = f"""
            SELECT fecha, val 
            FROM {table_name} 
            WHERE id_est = %(station_id)s 
            AND fecha >= %(start_date)s 
            AND fecha <= %(end_date)s 
            ORDER BY fecha
            """
            params = {
                'station_id': station_id,
                'start_date': start_date,
                'end_date': end_date
            }
        
        df = pd.read_sql(query, engine, params=params)
        return df
    except Exception as e:
        print(f"Error fetching pollutant data: {e}")
        return pd.DataFrame() 


def get_forecast_otres_mean_hour_p01(
    station_id: str, start_date: datetime, window_hours: int
) -> pd.DataFrame:
    """
    Fetch mean ozone forecast (``AVG(COALESCE(hour_p01, val))``) for one station per timestamp.

    When several rows share the same timestamp (e.g. multiple id_tipo_pronostico),
    values are averaged.

    Args:
        station_id: Station code (not ``all_stations``; use
            :func:`get_forecast_otres_all_stations_spatial_mean_max` for that).
        start_date: Interval start (inclusive).
        window_hours: Length of the interval in hours (end is start + window).

    Returns:
        DataFrame with columns ``fecha``, ``mean_hour_p01``.
    """
    engine = get_db_engine()
    if engine is None:
        return pd.DataFrame()

    if station_id == "all_stations":
        return pd.DataFrame()

    try:
        end_date = start_date + timedelta(hours=window_hours)
        query = """
            SELECT fecha, AVG(COALESCE(hour_p01, val)) AS mean_hour_p01
            FROM forecast_otres
            WHERE id_est = %(station_id)s
              AND fecha >= %(start_date)s
              AND fecha <= %(end_date)s
            GROUP BY fecha
            ORDER BY fecha
            """
        params = {
            "station_id": station_id,
            "start_date": start_date,
            "end_date": end_date,
        }
        return pd.read_sql(query, engine, params=params)
    except Exception as e:
        print(f"Error fetching forecast_otres mean hour_p01: {e}")
        return pd.DataFrame()


def get_forecast_otres_hours_p01_to_p24(
    station_id: str, start_date: datetime, window_hours: int
) -> pd.DataFrame:
    """
    Fetch raw ``hour_p01`` … ``hour_p24`` from ``forecast_otres`` for one station (no averaging).

    **Row semantics:** ``fecha`` is the ML forecast **issue** time. ``hour_pNN`` is stored
    for that issue row. The query includes issue times back to
    ``start_date - FORECAST_OTRES_ISSUE_PAD_HOURS`` so valid-time traces can start at
    ``start_date``.

    If more than one table row exists for the same ``fecha`` (e.g. different
    ``id_tipo_pronostico``), PostgreSQL ``DISTINCT ON (fecha)`` keeps a single row per
    issue time — the one with the largest ``id`` (typically the newest insert), still
    without averaging across products.

    Args:
        station_id: Station code (not ``all_stations``).
        start_date: Interval start (inclusive) for **valid times** shown in the UI.
        window_hours: Length of the interval in hours (end is start + window).

    Returns:
        DataFrame with ``fecha`` and ``hour_p01`` … ``hour_p24`` columns.
    """
    engine = get_db_engine()
    if engine is None:
        return pd.DataFrame()

    if station_id == "all_stations":
        return pd.DataFrame()

    try:
        end_date = start_date + timedelta(hours=window_hours)
        issue_start = start_date - timedelta(hours=FORECAST_OTRES_ISSUE_PAD_HOURS)
        lead_cols = ",\n                ".join(f"hour_p{i:02d}" for i in range(1, 25))
        query = f"""
            SELECT DISTINCT ON (fecha)
                fecha,
                {lead_cols}
            FROM forecast_otres
            WHERE id_est = %(station_id)s
              AND fecha >= %(issue_start)s
              AND fecha <= %(end_date)s
            ORDER BY fecha, id DESC
            """
        params = {
            "station_id": station_id,
            "issue_start": issue_start,
            "end_date": end_date,
        }
        return pd.read_sql(query, engine, params=params)
    except Exception as e:
        print(f"Error fetching forecast_otres hours p01–p24: {e}")
        return pd.DataFrame()


def get_forecast_otres_all_stations_spatial_mean_max(
    start_date: datetime, window_hours: int
) -> pd.DataFrame:
    """
    Spatial summary of ozone forecast for ``forecast_otres`` across all stations.

    For each ``fecha`` (ML **issue** time), first aggregates per station (mean and max of
    ``COALESCE(hour_p01, val)`` when multiple product rows exist), then:

    * ``mean_hour_p01``: average of those per-station means (equal weight per station).
    * ``max_hour_p01``: maximum of the per-station maxima (dashed envelope).

    Issue rows are loaded from ``start_date - FORECAST_OTRES_ISSUE_PAD_HOURS`` so
    ``hour_p01`` can be shifted to valid time without missing the first window hours.

    Args:
        start_date: Interval start (inclusive) for the displayed valid-time window.
        window_hours: Length of the interval in hours.

    Returns:
        DataFrame with columns ``fecha``, ``mean_hour_p01``, ``max_hour_p01``.
    """
    engine = get_db_engine()
    if engine is None:
        return pd.DataFrame()

    try:
        end_date = start_date + timedelta(hours=window_hours)
        issue_start = start_date - timedelta(hours=FORECAST_OTRES_ISSUE_PAD_HOURS)
        query = """
            WITH per_station AS (
                SELECT
                    fecha,
                    id_est,
                    AVG(COALESCE(hour_p01, val)) AS v_mean,
                    MAX(COALESCE(hour_p01, val)) AS v_max
                FROM forecast_otres
                WHERE fecha >= %(issue_start)s
                  AND fecha <= %(end_date)s
                GROUP BY fecha, id_est
            )
            SELECT
                fecha,
                AVG(v_mean) AS mean_hour_p01,
                MAX(v_max) AS max_hour_p01
            FROM per_station
            GROUP BY fecha
            ORDER BY fecha
            """
        params = {"issue_start": issue_start, "end_date": end_date}
        return pd.read_sql(query, engine, params=params)
    except Exception as e:
        print(f"Error fetching forecast_otres all-stations spatial stats: {e}")
        return pd.DataFrame()


def get_cont_otres_max_val_per_timestamp_all_stations(
    start_date: datetime, window_hours: int
) -> pd.DataFrame:
    """
    For each observation time, maximum ozone across all stations.

    Args:
        start_date: Interval start (inclusive).
        window_hours: Length of the interval in hours.

    Returns:
        DataFrame with columns ``fecha``, ``max_val``.
    """
    engine = get_db_engine()
    if engine is None:
        return pd.DataFrame()

    try:
        end_date = start_date + timedelta(hours=window_hours)
        query = """
            SELECT fecha, MAX(val) AS max_val
            FROM cont_otres
            WHERE fecha >= %(start_date)s
              AND fecha <= %(end_date)s
            GROUP BY fecha
            ORDER BY fecha
            """
        params = {"start_date": start_date, "end_date": end_date}
        return pd.read_sql(query, engine, params=params)
    except Exception as e:
        print(f"Error fetching cont_otres max across stations: {e}")
        return pd.DataFrame()


def get_daily_max_obs_otres(
    station_id: str, start_date: datetime, window_hours: int
) -> pd.DataFrame:
    """
    Calendar-day maximum observed ozone in the interval.

    * ``all_stations``: maximum ``val`` that day across every station-hour row.
    * Single station: maximum ``val`` that day for that station.

    Args:
        station_id: Station id or ``all_stations``.
        start_date: Interval start (inclusive).
        window_hours: Length of the interval in hours.

    Returns:
        DataFrame with ``day_date`` (date) and ``obs_daily_max``.
    """
    engine = get_db_engine()
    if engine is None:
        return pd.DataFrame()

    try:
        end_date = start_date + timedelta(hours=window_hours)
        if station_id == "all_stations":
            query = """
                SELECT CAST(fecha AS date) AS day_date, MAX(val) AS obs_daily_max
                FROM cont_otres
                WHERE fecha >= %(start_date)s
                  AND fecha <= %(end_date)s
                GROUP BY CAST(fecha AS date)
                ORDER BY day_date
                """
            params = {"start_date": start_date, "end_date": end_date}
        else:
            query = """
                SELECT CAST(fecha AS date) AS day_date, MAX(val) AS obs_daily_max
                FROM cont_otres
                WHERE id_est = %(station_id)s
                  AND fecha >= %(start_date)s
                  AND fecha <= %(end_date)s
                GROUP BY CAST(fecha AS date)
                ORDER BY day_date
                """
            params = {
                "station_id": station_id,
                "start_date": start_date,
                "end_date": end_date,
            }
        return pd.read_sql(query, engine, params=params)
    except Exception as e:
        print(f"Error fetching daily max obs otres: {e}")
        return pd.DataFrame()


def _forecast_otres_coalesced_avg_columns_sql(alias_prefix: str) -> str:
    """Build ``AVG(COALESCE(hour_pNN, val)) AS {prefix}NN`` for NN=01..17."""
    parts = [
        f"AVG(COALESCE(hour_p{i:02d}, val)) AS {alias_prefix}{i:02d}"
        for i in range(1, 18)
    ]
    return ",\n                ".join(parts)


def _sql_forecast_otres_valid_day_daily_max_query(
    inner_cte_name: str,
    inner_cte_body_sql: str,
) -> str:
    """
    Build SQL that buckets each lead by **valid-time** calendar day.

    ``hour_pNN`` is assumed to apply at ``fecha + NN hours``; the daily maximum
    for that lead uses the date of that valid instant.

    Args:
        inner_cte_name: ``per_ts_st`` or ``per_ts`` (must match ``FROM`` in lead CTEs).
        inner_cte_body_sql: The inner ``SELECT ... GROUP BY`` fragment inside the CTE.

    Returns:
        Full ``WITH ... SELECT`` statement string.
    """
    by_day_parts = []
    for i in range(1, 18):
        by_day_parts.append(
            f"by_day_p{i:02d} AS (\n"
            f"  SELECT CAST(fecha + (INTERVAL '1 hour' * {i}) AS date) AS day_date,\n"
            f"         MAX(m{i:02d}) AS daily_fc_max_p{i:02d}\n"
            f"  FROM {inner_cte_name}\n"
            f"  GROUP BY CAST(fecha + (INTERVAL '1 hour' * {i}) AS date)\n"
            f")"
        )
    by_day_sql = ",\n                ".join(by_day_parts)
    union_parts = " UNION ".join(
        f"SELECT day_date FROM by_day_p{i:02d}" for i in range(1, 18)
    )
    join_lines = "\n                ".join(
        f"LEFT JOIN by_day_p{i:02d} ON ad.day_date = by_day_p{i:02d}.day_date"
        for i in range(1, 18)
    )
    select_cols = ",\n                ".join(
        f"by_day_p{i:02d}.daily_fc_max_p{i:02d}" for i in range(1, 18)
    )
    return f"""
                WITH {inner_cte_name} AS (
                    {inner_cte_body_sql}
                ),
                {by_day_sql},
                all_days AS (
                    SELECT DISTINCT day_date
                    FROM (
                        {union_parts}
                    ) u
                )
                SELECT
                    ad.day_date,
                    {select_cols}
                FROM all_days ad
                {join_lines}
                ORDER BY ad.day_date
                """


def get_daily_max_forecast_otres_leads_p01_p17(
    station_id: str, start_date: datetime, window_hours: int
) -> pd.DataFrame:
    """
    Per calendar **valid** day, maximum predicted ozone for each lead hour_p01 … hour_p17.

    ``hour_pNN`` is interpreted as a prediction for ``issue_fecha + NN hours``; daily
    maxima are grouped by the calendar date of that valid time (not the issue date).

    Issue rows from ``start_date - FORECAST_OTRES_ISSUE_PAD_HOURS`` are included so
    valid-time days at the start of the selected window still aggregate all leads.

    Multiple ``id_tipo_pronostico`` rows at the same issue time are averaged per
    ``COALESCE(hour_pNN, val)`` before the daily maximum is taken.

    * ``all_stations``: for each issue time and station, average leads; then for
      each valid day and lead, take the maximum across contributing rows.
    * Single station: same, restricted to that station.

    Args:
        station_id: Station id or ``all_stations``.
        start_date: Interval start (inclusive).
        window_hours: Length of the interval in hours.

    Returns:
        DataFrame with ``day_date`` and ``daily_fc_max_p01`` … ``daily_fc_max_p17``.
    """
    engine = get_db_engine()
    if engine is None:
        return pd.DataFrame()

    inner_cols = _forecast_otres_coalesced_avg_columns_sql("m")

    try:
        end_date = start_date + timedelta(hours=window_hours)
        issue_start = start_date - timedelta(hours=FORECAST_OTRES_ISSUE_PAD_HOURS)
        if station_id == "all_stations":
            inner_body = f"""
                        SELECT
                            fecha,
                            id_est,
                            {inner_cols}
                        FROM forecast_otres
                        WHERE fecha >= %(issue_start)s
                          AND fecha <= %(end_date)s
                        GROUP BY fecha, id_est
                """
            query = _sql_forecast_otres_valid_day_daily_max_query("per_ts_st", inner_body)
            params = {"issue_start": issue_start, "end_date": end_date}
        else:
            inner_body = f"""
                        SELECT
                            fecha,
                            {inner_cols}
                        FROM forecast_otres
                        WHERE id_est = %(station_id)s
                          AND fecha >= %(issue_start)s
                          AND fecha <= %(end_date)s
                        GROUP BY fecha
                """
            query = _sql_forecast_otres_valid_day_daily_max_query("per_ts", inner_body)
            params = {
                "station_id": station_id,
                "issue_start": issue_start,
                "end_date": end_date,
            }
        return pd.read_sql(query, engine, params=params)
    except Exception as e:
        print(f"Error fetching daily max forecast otres p01–p17: {e}")
        return pd.DataFrame()


def get_meteorology_data(station_id: str, meteorology_field: str, start_date: datetime, window_hours: int):
    """Fetch meteorology data for a specific station and time period."""
    engine = get_db_engine()
    if engine is None:
        return pd.DataFrame()
    
    try:
        end_date = start_date + timedelta(hours=window_hours)
        table_name = f"met_{meteorology_field}"
        
        if station_id == 'all_stations':
            # Query for all stations
            query = f"""
            SELECT fecha, val, id_est 
            FROM {table_name} 
            WHERE fecha >= %(start_date)s 
            AND fecha <= %(end_date)s 
            ORDER BY fecha, id_est
            """
            params = {
                'start_date': start_date,
                'end_date': end_date
            }
        else:
            # Query for specific station
            query = f"""
            SELECT fecha, val 
            FROM {table_name} 
            WHERE id_est = %(station_id)s 
            AND fecha >= %(start_date)s 
            AND fecha <= %(end_date)s 
            ORDER BY fecha
            """
            params = {
                'station_id': station_id,
                'start_date': start_date,
                'end_date': end_date
            }
        
        df = pd.read_sql(query, engine, params=params)
        return df
    except Exception as e:
        print(f"Error fetching meteorology data: {e}")
        return pd.DataFrame() 


def get_pollutant_availability_data(station_id: str, pollutant: str):
    """Fetch monthly data availability counts for a pollutant."""
    engine = get_db_engine()
    if engine is None:
        return pd.DataFrame()
    
    try:
        table_name = f"cont_{pollutant}"
        
        if station_id == 'all_stations':
            # Query for all stations aggregated
            query = f"""
            SELECT 
                DATE_TRUNC('month', fecha) as month,
                COUNT(*) as count
            FROM {table_name} 
            WHERE fecha >= '2000-01-01' 
            AND fecha <= '2025-12-31'
            GROUP BY DATE_TRUNC('month', fecha)
            ORDER BY month
            """
            params = {}
        else:
            # Query for specific station
            query = f"""
            SELECT 
                DATE_TRUNC('month', fecha) as month,
                COUNT(*) as count
            FROM {table_name} 
            WHERE id_est = %(station_id)s 
            AND fecha >= '2000-01-01' 
            AND fecha <= '2025-12-31'
            GROUP BY DATE_TRUNC('month', fecha)
            ORDER BY month
            """
            params = {'station_id': station_id}
        
        df = pd.read_sql(query, engine, params=params)
        return df
    except Exception as e:
        print(f"Error fetching pollutant availability data: {e}")
        return pd.DataFrame()


def get_meteorology_availability_data(station_id: str, meteorology_field: str):
    """Fetch monthly data availability counts for a meteorology field."""
    engine = get_db_engine()
    if engine is None:
        return pd.DataFrame()
    
    try:
        table_name = f"met_{meteorology_field}"
        
        if station_id == 'all_stations':
            # Query for all stations aggregated
            query = f"""
            SELECT 
                DATE_TRUNC('month', fecha) as month,
                COUNT(*) as count
            FROM {table_name} 
            WHERE fecha >= '2000-01-01' 
            AND fecha <= '2025-12-31'
            GROUP BY DATE_TRUNC('month', fecha)
            ORDER BY month
            """
            params = {}
        else:
            # Query for specific station
            query = f"""
            SELECT 
                DATE_TRUNC('month', fecha) as month,
                COUNT(*) as count
            FROM {table_name} 
            WHERE id_est = %(station_id)s 
            AND fecha >= '2000-01-01' 
            AND fecha <= '2025-12-31'
            GROUP BY DATE_TRUNC('month', fecha)
            ORDER BY month
            """
            params = {'station_id': station_id}
        
        df = pd.read_sql(query, engine, params=params)
        return df
    except Exception as e:
        print(f"Error fetching meteorology availability data: {e}")
        return pd.DataFrame() 