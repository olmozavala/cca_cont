import pandas as pd
from datetime import datetime, timedelta
from .sql_con import get_db_engine, POLLUTANT_MAPPING, METEOROLOGY_MAPPING


def get_stations_data():
    """Fetch stations data for the dropdown."""
    engine = get_db_engine()
    if engine is None:
        return pd.DataFrame()
    
    try:
        query = "SELECT id, nombre, ST_X(geom) as longitude, ST_Y(geom) as latitude, altitude FROM cont_estaciones"
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