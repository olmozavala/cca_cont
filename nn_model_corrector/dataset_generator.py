from __future__ import annotations

import argparse
import ast
import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from db_utils.sql_con import get_db_engine


DEFAULT_CONFIG_PATH = Path(__file__).with_name("config.yaml")


@dataclass(frozen=True)
class DatasetConfig:
    issue_hour: int = 5
    lead_forecast: int = 1
    horizon_hours: int = 20
    start_date: date | None = None
    end_date: date | None = None
    station_ids: tuple[str, ...] = ()
    drop_missing: bool = True
    output_path: Path = Path("nn_model_corrector/data/otres_daily_max_dataset.csv")

    @property
    def lead_columns(self) -> list[str]:
        last_lead = self.lead_forecast + self.horizon_hours - 1
        return [lead_column_name(i) for i in range(self.lead_forecast, last_lead + 1)]


def lead_column_name(lead_hour: int) -> str:
    """Return the forecast_otres lead column name for a 1-based lead hour."""
    if lead_hour < 1:
        raise ValueError("lead_forecast must be >= 1")
    return f"hour_p{lead_hour:02d}"


def rmse(y_true: Iterable[float], y_pred: Iterable[float]) -> float:
    """Root mean squared error with NaN pairs removed."""
    pairs = [
        (float(obs), float(pred))
        for obs, pred in zip(y_true, y_pred)
        if pd.notna(obs) and pd.notna(pred)
    ]
    if not pairs:
        return math.nan
    return math.sqrt(sum((obs - pred) ** 2 for obs, pred in pairs) / len(pairs))


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> DatasetConfig:
    """Load dataset settings from YAML.

    PyYAML is used when installed. A small key/value fallback keeps this script
    runnable for the simple config format committed with the project.
    """
    config_path = Path(path)
    raw = _read_yaml_like(config_path)
    return DatasetConfig(
        issue_hour=int(raw.get("issue_hour", 5)),
        lead_forecast=_read_lead_forecast(raw),
        horizon_hours=int(raw.get("horizon_hours", 20)),
        start_date=_parse_date(raw.get("start_date")),
        end_date=_parse_date(raw.get("end_date")),
        station_ids=tuple(str(s).strip() for s in raw.get("station_ids", []) if str(s).strip()),
        drop_missing=bool(raw.get("drop_missing", True)),
        output_path=Path(raw.get("output_path", "nn_model_corrector/data/otres_daily_max_dataset.csv")),
    )


def generate_dataset(config: DatasetConfig) -> pd.DataFrame:
    """Build one supervised sample per issue date.

    Feature columns are ordered station-major, then lead-major, for example
    ``forecast_AJU_p01``, ``forecast_AJU_p02`` ... ``forecast_CUA_p01``.
    The target ``target_max_otres`` is the maximum observed ``cont_otres.val``
    across all stations during the same valid-time window.
    """
    _validate_config(config)
    engine = get_db_engine()
    if engine is None:
        raise RuntimeError("Could not create a database engine")

    issue_times = _issue_times(config)
    if not issue_times:
        return pd.DataFrame()

    station_ids = list(config.station_ids) or _fetch_station_ids(engine, config, issue_times)
    if not station_ids:
        raise RuntimeError("No stations found in forecast_otres for the configured period")

    forecast_df = _fetch_forecasts(engine, config, issue_times, station_ids)
    obs_df = _fetch_observations(engine, config, issue_times)

    rows: list[dict[str, Any]] = []
    grouped_forecasts = {
        pd.Timestamp(fecha).to_pydatetime().replace(tzinfo=None): group
        for fecha, group in forecast_df.groupby("fecha")
    }

    for issue_time in issue_times:
        fc_group = grouped_forecasts.get(issue_time, pd.DataFrame())
        row = _build_sample_row(config, issue_time, station_ids, fc_group, obs_df)
        if config.drop_missing and _has_missing_sample_values(row, station_ids, config.lead_columns):
            continue
        rows.append(row)

    columns = _dataset_columns(station_ids, config.lead_columns)
    dataset = pd.DataFrame(rows, columns=columns)
    if not dataset.empty:
        dataset["baseline_error"] = dataset["baseline_forecast_max"] - dataset["target_max_otres"]
    return dataset


def save_dataset(dataset: pd.DataFrame, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(path, index=False)


def _build_sample_row(
    config: DatasetConfig,
    issue_time: datetime,
    station_ids: list[str],
    forecast_group: pd.DataFrame,
    obs_df: pd.DataFrame,
) -> dict[str, Any]:
    valid_start = issue_time + timedelta(hours=config.lead_forecast)
    valid_end = valid_start + timedelta(hours=config.horizon_hours - 1)

    row: dict[str, Any] = {
        "issue_time": issue_time,
        "valid_start": valid_start,
        "valid_end": valid_end,
        "lead_forecast": config.lead_forecast,
        "horizon_hours": config.horizon_hours,
    }

    feature_values: list[float] = []
    by_station = forecast_group.set_index("id_est") if not forecast_group.empty else pd.DataFrame()
    for station_id in station_ids:
        station_row = by_station.loc[station_id] if station_id in by_station.index else None
        for lead_col in config.lead_columns:
            value = pd.NA if station_row is None else station_row.get(lead_col, pd.NA)
            value = pd.to_numeric(value, errors="coerce")
            feature_values.append(value)
            row[_feature_column(station_id, lead_col)] = value

    valid_obs = obs_df[(obs_df["fecha"] >= valid_start) & (obs_df["fecha"] <= valid_end)]
    target = pd.to_numeric(valid_obs["val"], errors="coerce").max()
    row["target_max_otres"] = target
    row["baseline_forecast_max"] = pd.Series(feature_values, dtype="float64").max()
    row["n_forecast_values"] = int(pd.Series(feature_values).notna().sum())
    row["n_obs_values"] = int(valid_obs["val"].notna().sum())
    return row


def _fetch_station_ids(engine: Any, config: DatasetConfig, issue_times: list[datetime]) -> list[str]:
    query = """
        SELECT DISTINCT id_est
        FROM forecast_otres
        WHERE fecha >= %(start_time)s
          AND fecha <= %(end_time)s
          AND EXTRACT(HOUR FROM fecha) = %(issue_hour)s
        ORDER BY id_est
    """
    df = pd.read_sql(
        query,
        engine,
        params={
            "start_time": min(issue_times),
            "end_time": max(issue_times),
            "issue_hour": config.issue_hour,
        },
    )
    return [str(s) for s in df["id_est"].dropna().tolist()]


def _fetch_forecasts(
    engine: Any,
    config: DatasetConfig,
    issue_times: list[datetime],
    station_ids: list[str],
) -> pd.DataFrame:
    select_leads = ",\n            ".join(
        f"AVG(COALESCE({col}, val)) AS {col}" for col in config.lead_columns
    )
    query = f"""
        SELECT
            fecha,
            id_est,
            {select_leads}
        FROM forecast_otres
        WHERE fecha >= %(start_time)s
          AND fecha <= %(end_time)s
          AND EXTRACT(HOUR FROM fecha) = %(issue_hour)s
          AND id_est = ANY(%(station_ids)s)
        GROUP BY fecha, id_est
        ORDER BY fecha, id_est
    """
    return pd.read_sql(
        query,
        engine,
        params={
            "start_time": min(issue_times),
            "end_time": max(issue_times),
            "issue_hour": config.issue_hour,
            "station_ids": station_ids,
        },
    )


def _fetch_observations(
    engine: Any,
    config: DatasetConfig,
    issue_times: list[datetime],
) -> pd.DataFrame:
    obs_start = min(issue_times) + timedelta(hours=config.lead_forecast)
    obs_end = max(issue_times) + timedelta(hours=config.lead_forecast + config.horizon_hours - 1)
    query = """
        SELECT fecha, val, id_est
        FROM cont_otres
        WHERE fecha >= %(obs_start)s
          AND fecha <= %(obs_end)s
        ORDER BY fecha, id_est
    """
    return pd.read_sql(query, engine, params={"obs_start": obs_start, "obs_end": obs_end})


def _issue_times(config: DatasetConfig) -> list[datetime]:
    if config.start_date is None or config.end_date is None:
        raise ValueError("start_date and end_date are required")
    current = datetime.combine(config.start_date, time(hour=config.issue_hour))
    end = datetime.combine(config.end_date, time(hour=config.issue_hour))
    issue_times: list[datetime] = []
    while current <= end:
        issue_times.append(current)
        current += timedelta(days=1)
    return issue_times


def _dataset_columns(station_ids: list[str], lead_columns: list[str]) -> list[str]:
    features = [_feature_column(station_id, lead_col) for station_id in station_ids for lead_col in lead_columns]
    return [
        "issue_time",
        "valid_start",
        "valid_end",
        "lead_forecast",
        "horizon_hours",
        *features,
        "target_max_otres",
        "baseline_forecast_max",
        "baseline_error",
        "n_forecast_values",
        "n_obs_values",
    ]


def _feature_column(station_id: str, lead_col: str) -> str:
    lead = lead_col.removeprefix("hour_")
    clean_station = "".join(ch if ch.isalnum() else "_" for ch in station_id)
    return f"forecast_{clean_station}_{lead}"


def _has_missing_sample_values(row: dict[str, Any], station_ids: list[str], lead_columns: list[str]) -> bool:
    feature_cols = [_feature_column(station_id, lead_col) for station_id in station_ids for lead_col in lead_columns]
    required_cols = [*feature_cols, "target_max_otres"]
    return any(pd.isna(row.get(col)) for col in required_cols)


def _validate_config(config: DatasetConfig) -> None:
    if not 0 <= config.issue_hour <= 23:
        raise ValueError("issue_hour must be between 0 and 23")
    if config.lead_forecast < 1:
        raise ValueError("lead_forecast must be >= 1")
    if config.horizon_hours < 1:
        raise ValueError("horizon_hours must be >= 1")
    if config.start_date and config.end_date and config.start_date > config.end_date:
        raise ValueError("start_date must be <= end_date")


def _read_yaml_like(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except ModuleNotFoundError:
        return _minimal_yaml_parse(text)


def _minimal_yaml_parse(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        value = raw_value.strip()
        if value == "":
            data[key.strip()] = []
        else:
            data[key.strip()] = _parse_scalar(value)
    return data


def _parse_scalar(value: str) -> Any:
    lower = value.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if value.startswith("[") and value.endswith("]"):
        return ast.literal_eval(value)
    try:
        return int(value)
    except ValueError:
        return value.strip("\"'")


def _read_lead_forecast(raw: dict[str, Any]) -> int:
    if "lead_forecast" in raw:
        return int(raw["lead_forecast"])

    prefix = "lead_forecast_"
    for key, value in raw.items():
        if key.startswith(prefix) and value is not False and value is not None:
            suffix = key.removeprefix(prefix)
            if suffix.isdigit():
                return int(suffix)
    return 1


def _parse_date(value: Any) -> date | None:
    if value in {None, ""}:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the OTRES NN correction dataset.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to YAML config.")
    parser.add_argument("--output", default=None, help="Optional CSV output path override.")
    args = parser.parse_args()

    config = load_config(args.config)
    output_path = Path(args.output) if args.output else config.output_path
    dataset = generate_dataset(config)
    save_dataset(dataset, output_path)

    baseline_rmse = rmse(dataset["target_max_otres"], dataset["baseline_forecast_max"]) if not dataset.empty else math.nan
    print(f"Wrote {len(dataset)} samples to {output_path}")
    print(f"Features per sample: {max(len(dataset.columns) - 10, 0)}")
    print(f"Baseline forecast max RMSE: {baseline_rmse:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
