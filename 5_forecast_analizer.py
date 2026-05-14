"""
Dash app: ozone (otres) observations vs ``forecast_otres`` with sampled lead hours
(hour_p01, p07, p13, p19 within 01–24), spatial max series, and daily-max verification (p01–p17).

Each ``forecast_otres`` row is an ML **issue** at ``fecha``; ``hour_pNN`` is valid at
``fecha + NN`` hours. Traces are plotted at that **valid** time, and queries pull earlier
issue rows so the first hours of the selected window are covered for every lead.

Run with ``uv run python 5_forecast_analizer.py`` (or your project runner).
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.colors as plc
import plotly.graph_objects as go
from dash import Input, Output, State, callback, dcc, html
from dash.exceptions import PreventUpdate

from db_utils.queries_select import (
    get_cont_otres_max_val_per_timestamp_all_stations,
    get_daily_max_forecast_otres_leads_p01_p17,
    get_daily_max_obs_otres,
    get_forecast_otres_all_stations_spatial_mean_max,
    get_forecast_otres_hours_p01_to_p24,
    get_pollutant_data,
    get_station_name,
    get_stations_data,
)
from db_utils.sql_con import POLLUTANT_MAPPING

default_station: str = "CCA"
days_before: int = 5
pollutant_key: str = "otres"

DASHBOARD_CONFIG: Dict[str, Any] = {
    "host": "0.0.0.0",
    "port": 8051,
    "debug": True,
}

SLIDER_MAX_HOURS: int = 24 * 30 * 6
DEFAULT_WINDOW_HOURS: int = 12 * 24

# Single-station panel: which ``hour_pNN`` leads to plot (01–24, step 6 h).
FORECAST_SINGLE_STATION_PLOT_LEADS: Tuple[int, ...] = tuple(range(1, 25, 6))
FORECAST_SINGLE_STATION_PLOT_LEADS_LABEL: str = ", ".join(
    f"hour_p{n:02d}" for n in FORECAST_SINGLE_STATION_PLOT_LEADS
)

FORECAST_HOUR_COLS: Tuple[str, ...] = tuple(
    f"hour_p{n:02d}" for n in FORECAST_SINGLE_STATION_PLOT_LEADS
)

DAILY_FC_MAX_COLS: Tuple[str, ...] = tuple(
    f"daily_fc_max_p{i:02d}" for i in range(1, 18)
)

# Line traces: do not connect across periods longer than this multiple of the median Δt.
_GAP_BREAK_FACTOR: float = 3.0
_GAP_BREAK_MIN: pd.Timedelta = pd.Timedelta(minutes=90)
_GAP_BREAK_CAP: pd.Timedelta = pd.Timedelta(hours=72)

# Legend uses the same compact trace ``name`` strings; hover text uses this template.
HOVER_TEMPLATE: str = (
    "<b>%{fullData.name}</b><br>%{x|%Y-%m-%d %H:%M}<br>%{y:.2f}<extra></extra>"
)

# Qualitative colors for many per-station observation traces (legend + hover match line).
_STATION_OBS_COLORS: Tuple[str, ...] = tuple(plc.qualitative.Plotly)


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Parse ``#RRGGBB`` into 0–255 RGB components."""
    h = hex_color.strip().lstrip("#")
    if len(h) == 6:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    raise ValueError(f"Unsupported hex color: {hex_color!r}")


def _hoverlabel_for_line_color(line_color: str) -> Dict[str, Any]:
    """
    Build Plotly ``hoverlabel`` kwargs so the tooltip background matches the trace color.

    Chooses white or near-black label text for contrast on the given background.

    Args:
        line_color: ``#RRGGBB`` used for the trace line (and marker, when set).

    Returns:
        Dict suitable for ``go.Scatter(..., hoverlabel=...)``.
    """
    try:
        r, g, b = _hex_to_rgb(line_color)
    except ValueError:
        line_color = "#6c757d"
        r, g, b = _hex_to_rgb(line_color)
    luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
    font_color = "#ffffff" if luminance < 0.45 else "#111111"
    return {
        "bgcolor": line_color,
        "font": {"color": font_color, "size": 12},
    }


FORECAST_LEAD_COLORS: Tuple[str, ...] = (
    "#000000",
    "#636363",
    "#2171b5",
    "#6baed6",
    "#fd8d3c",
    "#e6550d",
    "#31a354",
    "#74c476",
)


def _valid_time_axis(issue_times: pd.Series, lead_hours: int) -> pd.Series:
    """
    Map ML **issue** times (``fecha``) to the **valid** time for that lead.

    Each ``forecast_otres`` row is one forecast run at ``fecha``; ``hour_pNN`` applies
    at ``fecha + NN hours``. Lead ``N`` at valid time ``T`` therefore uses the row issued
    at ``T - N``; plotting ``hour_pN`` from that row at ``x = issue + N`` is the point ``(T, y)``.

    Args:
        issue_times: Series of issue datetimes (``fecha`` from the database).
        lead_hours: Lead index ``N`` from ``hour_pNN`` (valid at ``issue + N hours``).

    Returns:
        Series of valid datetimes ``issue_times + N hours``.
    """
    return pd.to_datetime(issue_times, errors="coerce") + pd.to_timedelta(
        int(lead_hours), unit="h"
    )


def _clip_valid_time_series(
    valid_x: pd.Series,
    y_vals: pd.Series,
    plot_start: datetime,
    plot_end: datetime,
) -> Tuple[pd.Series, pd.Series]:
    """
    Restrict a valid-time series to the dashboard window ``[plot_start, plot_end]``.

    Forecast queries include earlier **issue** rows so each lead can be built; this
    drops valid times outside the user-selected range.

    Args:
        valid_x: Valid-time axis (e.g. issue + lead hours).
        y_vals: Values aligned with ``valid_x``.
        plot_start: Inclusive start of the visible window.
        plot_end: Inclusive end of the visible window.

    Returns:
        Filtered ``(valid_x, y_vals)`` with the same index subset.
    """
    df = pd.DataFrame(
        {
            "x": pd.to_datetime(valid_x, errors="coerce"),
            "y": y_vals,
        }
    ).dropna(subset=["x"])
    if df.empty:
        return df["x"], df["y"]
    ps = pd.Timestamp(plot_start)
    pe = pd.Timestamp(plot_end)
    m = (df["x"] >= ps) & (df["x"] <= pe)
    return df.loc[m, "x"], df.loc[m, "y"]


def _median_time_step_seconds(x_dt: pd.Series) -> float:
    """
    Median positive spacing between consecutive timestamps (in seconds).

    Args:
        x_dt: Timestamp-like series.

    Returns:
        Median delta in seconds, at least 60 (1 minute) when undefined.
    """
    dts = pd.to_datetime(x_dt, errors="coerce").dropna().sort_values()
    if len(dts) < 2:
        return 3600.0
    deltas = dts.diff().dropna().dt.total_seconds()
    deltas = deltas[deltas > 0]
    if deltas.empty:
        return 3600.0
    med = float(deltas.median())
    return max(med, 60.0)


def _gap_break_threshold_seconds(x_dt: pd.Series) -> float:
    """
    Maximum allowed gap (seconds) before inserting a line break.

    Uses ``median(Δt) * factor``, clamped between ``_GAP_BREAK_MIN`` and ``_GAP_BREAK_CAP``.

    Args:
        x_dt: Timestamp-like series used to infer typical sampling.

    Returns:
        Threshold in seconds for consecutive point spacing.
    """
    med_s = _median_time_step_seconds(x_dt)
    raw = med_s * _GAP_BREAK_FACTOR
    lo = _GAP_BREAK_MIN.total_seconds()
    hi = _GAP_BREAK_CAP.total_seconds()
    return float(min(max(raw, lo), hi))


def _scatter_xy_break_time_gaps(
    x_dt: pd.Series,
    y_vals: pd.Series,
) -> Tuple[List[Any], List[Any]]:
    """
    Sort by time and insert ``(None, None)`` pairs when consecutive Δt is too large.

    Plotly then renders separate segments instead of long chords across missing data.

    Args:
        x_dt: X axis (datetimes).
        y_vals: Y values aligned with ``x_dt``.

    Returns:
        ``(x_list, y_list)`` for ``go.Scatter`` with ``connectgaps=False``.
    """
    if x_dt.empty or y_vals.empty:
        return [], []
    df = (
        pd.DataFrame({"x": pd.to_datetime(x_dt, errors="coerce"), "y": y_vals})
        .dropna(subset=["x"])
        .sort_values("x")
    )
    if df.empty:
        return [], []
    max_gap_s = _gap_break_threshold_seconds(df["x"])
    out_x: List[Any] = []
    out_y: List[Any] = []
    for i in range(len(df)):
        if i > 0:
            delta_s = (df["x"].iloc[i] - df["x"].iloc[i - 1]).total_seconds()
            if delta_s > max_gap_s:
                out_x.append(None)
                out_y.append(None)
        out_x.append(df["x"].iloc[i])
        yv = df["y"].iloc[i]
        if yv is None or (isinstance(yv, float) and math.isnan(yv)) or pd.isna(yv):
            out_y.append(None)
        else:
            out_y.append(float(yv))
    return out_x, out_y


def _sorted_xy_for_forecast(
    x_dt: pd.Series,
    y_vals: pd.Series,
) -> Tuple[List[Any], List[Any]]:
    """
    Sort points by time for a single forecast **column** trace (one ``hour_pNN``).

    Each trace is built by walking many issue-time **rows** and reading the same column on
    each row, with ``x = issue_fecha + N`` (valid time). We do **not** insert artificial line
    breaks here — missing issue hours simply leave a longer chord on the line when using
    ``connectgaps=True`` in Plotly.

    Args:
        x_dt: Valid-time axis (e.g. from :func:`_valid_time_axis`).
        y_vals: Values from exactly one ``hour_pNN`` column, aligned with ``x_dt``.

    Returns:
        ``(x_list, y_list)`` for ``go.Scatter`` (finite pairs only, sorted by ``x``).
    """
    if x_dt.empty or y_vals.empty:
        return [], []
    df = pd.DataFrame(
        {
            "x": pd.to_datetime(x_dt, errors="coerce"),
            "y": pd.to_numeric(y_vals, errors="coerce"),
        }
    ).dropna(subset=["x", "y"])
    if df.empty:
        return [], []
    df = df.sort_values("x")
    return df["x"].tolist(), df["y"].astype(float).tolist()


def get_stations_list() -> List[Dict[str, str]]:
    """Return options for the station dropdown, including *All stations*."""
    df = get_stations_data()
    if df.empty:
        return [{"label": default_station, "value": default_station}]
    options = [
        {"label": f"{row['nombre']} ({row['id']})", "value": row["id"]}
        for _, row in df.iterrows()
    ]
    options.append({"label": "All stations", "value": "all_stations"})
    return options


def _slider_marks() -> Dict[int, str]:
    """Hour marks for the time-window slider."""
    return {
        i: f"{i // 24}d" if i % 24 == 0 else f"{i}h"
        for i in [1, 24, 7 * 24, 10 * 24, 30 * 24, 90 * 24, 180 * 24]
    }


def _sidebar_controls_card() -> dbc.Card:
    """
    Vertical filter panel: station, start date, window navigation, time window.

    Placed in a left column on large screens; stacks above charts on small screens.
    """
    return dbc.Card(
        [
            dbc.CardHeader("Selection", className="fw-semibold py-2 bg-light border-0 small"),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            dbc.Label("Station", className="small text-muted mb-1"),
                            dcc.Dropdown(
                                id="fc-station-dropdown",
                                options=get_stations_list(),
                                value=default_station,
                                clearable=False,
                                className="dash-bootstrap",
                            ),
                        ],
                        className="mb-3",
                    ),
                    html.Div(
                        [
                            dbc.Label("Start date", className="small text-muted mb-1"),
                            dcc.DatePickerSingle(
                                id="fc-date-picker",
                                date=(
                                    datetime.now() - timedelta(days=days_before)
                                ).strftime("%Y-%m-%d"),
                                display_format="YYYY-MM-DD",
                                className="w-100",
                            ),
                        ],
                        className="mb-2",
                    ),
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                "◀ Prev",
                                id="fc-date-prev",
                                outline=True,
                                color="secondary",
                                size="sm",
                                title="Move start date back by the current window length",
                            ),
                            dbc.Button(
                                "Next ▶",
                                id="fc-date-next",
                                outline=True,
                                color="secondary",
                                size="sm",
                                title="Move start date forward by the current window length",
                            ),
                        ],
                        className="w-100 mb-3",
                    ),
                    html.Div(
                        [
                            dbc.Label("Time window (hours)", className="small text-muted mb-1"),
                            dcc.Slider(
                                id="fc-window-slider",
                                min=1,
                                max=SLIDER_MAX_HOURS,
                                step=1,
                                value=DEFAULT_WINDOW_HOURS,
                                marks=_slider_marks(),
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                        ],
                    ),
                ],
                className="py-3",
            ),
        ],
        className="border-0 shadow-sm mb-3 mb-lg-0",
    )


def _graph_card(title: str, graph_id: str, height: str = "520px") -> dbc.Card:
    """Bootstrap card wrapping a Plotly graph."""
    return dbc.Card(
        [
            dbc.CardHeader(title, className="fw-semibold py-2 bg-light border-0"),
            dbc.CardBody(
                dcc.Graph(
                    id=graph_id,
                    style={"height": height},
                    config={"displayModeBar": True},
                ),
                className="p-2 pt-0",
            ),
        ],
        className="mb-3 shadow-sm border-0 h-100",
    )


def _metrics_table_card() -> dbc.Card:
    """Card with daily-max verification metrics (RMSE / MAE / R² for hour_p01–p17)."""
    return dbc.Card(
        [
            dbc.CardHeader(
                "Daily maximum ozone — forecast vs observations",
                className="fw-semibold py-2 bg-light border-0",
            ),
            dbc.CardBody(
                [
                    html.P(
                        "Each calendar day contributes one observed daily maximum (max hourly "
                        "value that day) and one predicted daily maximum per lead, where each "
                        "lead is assigned to the **valid** calendar day (issue + lead hours). "
                        "Metrics use only days with both observation and forecast available.",
                        className="text-muted small mb-2",
                    ),
                    html.Div(id="fc-metrics-table"),
                ],
                className="p-2 pt-0",
            ),
        ],
        className="mb-3 shadow-sm border-0 h-100",
    )


def _build_layout() -> dbc.Container:
    """Root layout for the forecast analyzer."""
    label = POLLUTANT_MAPPING.get(pollutant_key, pollutant_key)
    main_content = html.Div(
        [
            html.P(
                f"Compare {label} observations with model forecasts on the first panel using "
                f"{FORECAST_SINGLE_STATION_PLOT_LEADS_LABEL} (every 6 h from hour_p01 through hour_p24). "
                "Each forecast row is one ML **issue** at ``fecha``; ``hour_pNN`` is the value at **valid** "
                "time ``fecha + NN`` hours. Traces are drawn on the valid-time axis; earlier issue rows are "
                "loaded and then clipped to your window. This matches ``nn_model_corrector.dataset_generator`` "
                "column naming. The second panel shows max observation vs max forecast (lead 1) across all "
                "stations at valid time. The table compares daily maxima for each lead hour_p01–hour_p17.",
                className="text-muted lead small mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        _graph_card(f"{label}: observations vs forecast", "fc-plot-otres"),
                        xs=12,
                    ),
                ],
                className="g-3 mb-1",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        _graph_card(
                            f"{label}: max observation (all stations) vs max forecast lead 1 (valid time)",
                            "fc-plot-max-all",
                            height="400px",
                        ),
                        xs=12,
                    ),
                ],
                className="g-3 mb-1",
            ),
            dbc.Row(
                [
                    dbc.Col(_metrics_table_card(), xs=12),
                ],
                className="g-3 mb-1",
            ),
            html.Footer(
                dbc.Container(
                    html.Small(
                        "Forecast analyzer · PostgreSQL contingencia",
                        className="text-muted",
                    ),
                    fluid=True,
                    className="py-4 text-center",
                )
            ),
        ],
    )
    return dbc.Container(
        [
            dcc.Store(id="fc-initial-trigger", data=True),
            dbc.NavbarSimple(
                children=[
                    dbc.Badge("forecast_otres", color="light", className="text-primary ms-2", pill=True),
                ],
                brand="Ozone forecast analysis",
                brand_href="#",
                color="primary",
                dark=True,
                className="mb-3 shadow-sm rounded",
                fluid=True,
            ),
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            _sidebar_controls_card(),
                            className="sticky-lg-top",
                            style={"top": "0.75rem", "zIndex": 100},
                        ),
                        xs=12,
                        lg=3,
                        className="mb-3 mb-lg-0",
                    ),
                    dbc.Col(main_content, xs=12, lg=9),
                ],
                className="g-3 align-items-start",
            ),
        ],
        fluid=True,
        className="px-3 pb-5 app-container",
    )


def _apply_figure_style(fig: go.Figure) -> None:
    """Align Plotly with Bootstrap light theme; legend on the right outside the plot area."""
    fig.update_layout(
        template="plotly_white",
        font=dict(family="system-ui, -apple-system, 'Segoe UI', sans-serif", size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,249,250,0.6)",
        margin=dict(l=48, r=150, t=56, b=48),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor="#dee2e6",
            borderwidth=1,
            font=dict(size=11),
        ),
        hovermode="closest",
        hoverlabel=dict(namelength=-1, font_size=12),
    )


def _append_forecast_all_stations_mean_max(
    fig: go.Figure,
    forecast_df: pd.DataFrame,
    plot_start: datetime,
    plot_end: datetime,
) -> None:
    """
    Add spatial mean (black) and spatial max (blue dashed) for ``hour_p01`` at valid time.

    Valid time is ``issue_fecha + 1 hour`` (P01). Extra issue rows before ``plot_start``
    are expected in ``forecast_df`` so the first window hour is covered.

    Args:
        fig: Target figure.
        forecast_df: Output of :func:`get_forecast_otres_all_stations_spatial_mean_max`.
        plot_start: Inclusive start of the visible valid-time window.
        plot_end: Inclusive end of the visible valid-time window.
    """
    if forecast_df.empty:
        return
    mean_df = forecast_df.dropna(subset=["mean_hour_p01"])
    if not mean_df.empty:
        xv = _valid_time_axis(mean_df["fecha"], 1)
        xv_c, yv_c = _clip_valid_time_series(xv, mean_df["mean_hour_p01"], plot_start, plot_end)
        xl, yl = _sorted_xy_for_forecast(xv_c, yv_c)
        fig.add_trace(
            go.Scatter(
                x=xl,
                y=yl,
                mode="lines",
                name="hour_p01 (mean)",
                line=dict(color="#000000", width=2.5),
                connectgaps=True,
                hovertemplate=HOVER_TEMPLATE,
                hoverlabel=_hoverlabel_for_line_color("#000000"),
            )
        )
    max_df = forecast_df.dropna(subset=["max_hour_p01"])
    if not max_df.empty:
        xv = _valid_time_axis(max_df["fecha"], 1)
        xv_c, yv_c = _clip_valid_time_series(xv, max_df["max_hour_p01"], plot_start, plot_end)
        xl, yl = _sorted_xy_for_forecast(xv_c, yv_c)
        fc_blue = "#2171b5"
        fig.add_trace(
            go.Scatter(
                x=xl,
                y=yl,
                mode="lines",
                name="hour_p01 (max)",
                line=dict(color=fc_blue, width=2.5, dash="dash"),
                connectgaps=True,
                hovertemplate=HOVER_TEMPLATE,
                hoverlabel=_hoverlabel_for_line_color(fc_blue),
            )
        )


def _append_forecast_single_station_leads_sampled(
    fig: go.Figure,
    forecast_df: pd.DataFrame,
    plot_start: datetime,
    plot_end: datetime,
) -> None:
    """
    Add one trace per sampled lead: each trace is a single DB **column** (``hour_pNN``).

    For each ``N`` in :data:`FORECAST_SINGLE_STATION_PLOT_LEADS`, we read only
    ``hour_pNN`` across issue-time **rows** (raw values from :func:`get_forecast_otres_hours_p01_to_p24`,
    no per-timestamp averaging). Point ``(x, y)`` is ``(issue_fecha + N hours, hour_pNN)``.

    Args:
        fig: Target figure.
        forecast_df: Output of :func:`get_forecast_otres_hours_p01_to_p24`.
        plot_start: Inclusive start of the visible valid-time window.
        plot_end: Inclusive end of the visible valid-time window.
    """
    if forecast_df.empty:
        return
    for trace_i, db_suffix in enumerate(FORECAST_SINGLE_STATION_PLOT_LEADS):
        col = f"hour_p{db_suffix:02d}"
        if col not in forecast_df.columns:
            continue
        sub = forecast_df.dropna(subset=[col])
        if sub.empty:
            continue
        lead_idx = db_suffix - 1
        color = (
            "#000000"
            if db_suffix == 1
            else FORECAST_LEAD_COLORS[lead_idx % len(FORECAST_LEAD_COLORS)]
        )
        dash_style = "solid" if trace_i == 0 else "dot" if trace_i % 2 else "dash"
        xv = _valid_time_axis(sub["fecha"], db_suffix)
        xv_c, yv_c = _clip_valid_time_series(xv, sub[col], plot_start, plot_end)
        xl, yl = _sorted_xy_for_forecast(xv_c, yv_c)
        fig.add_trace(
            go.Scatter(
                x=xl,
                y=yl,
                mode="lines",
                name=f"hour_p{db_suffix:02d}",
                line=dict(color=color, width=2, dash=dash_style),
                connectgaps=True,
                hovertemplate=HOVER_TEMPLATE,
                hoverlabel=_hoverlabel_for_line_color(color),
            )
        )


def _forecast_all_stations_has_points(forecast_df: pd.DataFrame) -> bool:
    """Return True if either spatial mean or max series has at least one value."""
    if forecast_df.empty:
        return False
    return bool(
        forecast_df["mean_hour_p01"].notna().any()
        or forecast_df["max_hour_p01"].notna().any()
    )


def _forecast_single_station_leads_has_points(forecast_df: pd.DataFrame) -> bool:
    """Return True if any sampled lead column has a non-null value."""
    if forecast_df.empty:
        return False
    for col in FORECAST_HOUR_COLS:
        if col in forecast_df.columns and forecast_df[col].notna().any():
            return True
    return False


def _annotate_forecast_missing(fig: go.Figure) -> None:
    """On-chart note when no forecast rows were returned."""
    fig.add_annotation(
        x=0.01,
        y=0.99,
        xref="paper",
        yref="paper",
        text=(
            "No forecast_otres rows in this window (or query failed — check DB and logs)."
        ),
        showarrow=False,
        xanchor="left",
        yanchor="top",
        font=dict(size=11, color="#6c757d"),
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor="#dee2e6",
        borderwidth=1,
        borderpad=6,
    )


def _rmse_mae_r2(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float, float]:
    """
    Compute RMSE, MAE, and R² for aligned finite pairs.

    Args:
        y_true: Observed daily maxima.
        y_pred: Forecast daily maxima for one lead.

    Returns:
        Tuple ``(rmse, mae, r2)`` using ``nan`` when undefined.
    """
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    yt = y_true[mask].astype(float)
    yp = y_pred[mask].astype(float)
    if yt.size == 0:
        return (float("nan"), float("nan"), float("nan"))
    err = yp - yt
    rmse = float(math.sqrt(float(np.mean(err**2))))
    mae = float(np.mean(np.abs(err)))
    ss_res = float(np.sum(err**2))
    mean_y = float(np.mean(yt))
    ss_tot = float(np.sum((yt - mean_y) ** 2))
    if ss_tot == 0.0 or yt.size < 2:
        r2 = float("nan")
    else:
        r2 = float(1.0 - ss_res / ss_tot)
    return (rmse, mae, r2)


def _format_metric_cell(value: float) -> str:
    """Format a scalar for the metrics table, or em dash if non-finite."""
    if value is None or not math.isfinite(value):
        return "—"
    return f"{value:.3f}"


def _build_daily_max_metrics_table(
    selected_station: str, start_date: datetime, window_hours: int
) -> html.Div:
    """
    Build Bootstrap table of RMSE, MAE, R² for daily max vs each forecast lead.

    Args:
        selected_station: Station id or ``all_stations`` (defines daily-max scope).
        start_date: Interval start.
        window_hours: Window length in hours.

    Returns:
        Dash HTML fragment with the table or an explanatory message.
    """
    obs_df = get_daily_max_obs_otres(selected_station, start_date, window_hours)
    fc_df = get_daily_max_forecast_otres_leads_p01_p17(
        selected_station, start_date, window_hours
    )
    if obs_df.empty or fc_df.empty:
        return html.P(
            "No daily maximum data available for observations or forecast in this window.",
            className="text-muted small mb-0",
        )

    obs_df = obs_df.copy()
    fc_df = fc_df.copy()
    obs_df["day_date"] = pd.to_datetime(obs_df["day_date"]).dt.normalize()
    fc_df["day_date"] = pd.to_datetime(fc_df["day_date"]).dt.normalize()
    merged = obs_df.merge(fc_df, on="day_date", how="inner")
    if merged.empty:
        return html.P(
            "No overlapping calendar days with both observed and forecast daily maxima.",
            className="text-muted small mb-0",
        )

    y_obs = merged["obs_daily_max"].to_numpy(dtype=float)
    header_cells = [html.Th("Metric", className="text-start")]
    header_cells.extend(
        html.Th(f"hour_p{i:02d}", className="text-end") for i in range(1, 18)
    )

    rows_out: List[List[Union[html.Th, html.Td]]] = []
    for metric_name in ("RMSE", "MAE", "R²"):
        row_cells: List[Union[html.Th, html.Td]] = [
            html.Th(metric_name, scope="row", className="text-start")
        ]
        for col in DAILY_FC_MAX_COLS:
            if col not in merged.columns:
                row_cells.append(html.Td("—", className="text-end"))
                continue
            y_fc = merged[col].to_numpy(dtype=float)
            rmse, mae, r2 = _rmse_mae_r2(y_obs, y_fc)
            val = rmse if metric_name == "RMSE" else mae if metric_name == "MAE" else r2
            row_cells.append(html.Td(_format_metric_cell(val), className="text-end"))
        rows_out.append(row_cells)

    table = dbc.Table(
        [html.Thead(html.Tr(header_cells)), html.Tbody([html.Tr(r) for r in rows_out])],
        bordered=True,
        hover=True,
        responsive=True,
        size="sm",
        className="mb-0",
    )
    return html.Div(
        [
            html.P(
                f"Days used: {len(merged)} (inner join on calendar day).",
                className="text-muted small mb-2",
            ),
            table,
        ]
    )


def _build_panel1_figure(
    selected_station: str,
    start_date: datetime,
    window_hours: int,
) -> go.Figure:
    """
    First panel: observations plus forecast (all-stations mean/max p01, or sampled station leads).

    For a single station, forecast traces use :data:`FORECAST_SINGLE_STATION_PLOT_LEADS`
    (hour_p01 … through hour_p24 in steps of 6 h by default).

    Args:
        selected_station: Station id or ``all_stations``.
        start_date: Interval start.
        window_hours: Window length in hours.

    Returns:
        Plotly figure for ``fc-plot-otres``.
    """
    label = POLLUTANT_MAPPING.get(pollutant_key, pollutant_key)
    station_display = get_station_name(selected_station)
    plot_end = start_date + timedelta(hours=window_hours)
    obs_df = get_pollutant_data(selected_station, pollutant_key, start_date, window_hours)

    if selected_station == "all_stations":
        forecast_df = get_forecast_otres_all_stations_spatial_mean_max(start_date, window_hours)
    else:
        forecast_df = get_forecast_otres_hours_p01_to_p24(
            selected_station, start_date, window_hours
        )

    fig = go.Figure()

    if obs_df.empty:
        if selected_station == "all_stations":
            if _forecast_all_stations_has_points(forecast_df):
                _append_forecast_all_stations_mean_max(fig, forecast_df, start_date, plot_end)
                title = f"All stations — {label} (forecast mean / max only)"
            else:
                fig.add_annotation(
                    text="No observations or forecast in this window",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                )
                title = f"All stations — {label}"
        else:
            if _forecast_single_station_leads_has_points(forecast_df):
                _append_forecast_single_station_leads_sampled(
                    fig, forecast_df, start_date, plot_end
                )
                title = (
                    f"{station_display} — {label} "
                    f"({FORECAST_SINGLE_STATION_PLOT_LEADS_LABEL} only; no observations)"
                )
            else:
                fig.add_annotation(
                    text="No observations or forecast in this window",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                )
                title = f"{station_display} — {label}"
    else:
        if selected_station == "all_stations" and "id_est" in obs_df.columns:
            for i, station in enumerate(obs_df["id_est"].unique()):
                station_data = obs_df[obs_df["id_est"] == station]
                line_color = _STATION_OBS_COLORS[i % len(_STATION_OBS_COLORS)]
                xl, yl = _scatter_xy_break_time_gaps(
                    station_data["fecha"], station_data["val"]
                )
                fig.add_trace(
                    go.Scatter(
                        x=xl,
                        y=yl,
                        mode="lines+markers",
                        name=f"Obs_{station}",
                        marker=dict(size=3, color=line_color),
                        line=dict(width=1, color=line_color),
                        opacity=0.42,
                        connectgaps=False,
                        hovertemplate=HOVER_TEMPLATE,
                        hoverlabel=_hoverlabel_for_line_color(line_color),
                    )
                )
            title = f"All stations — {label}"
            _append_forecast_all_stations_mean_max(fig, forecast_df, start_date, plot_end)
            if not _forecast_all_stations_has_points(forecast_df):
                _annotate_forecast_missing(fig)
        else:
            xl, yl = _scatter_xy_break_time_gaps(obs_df["fecha"], obs_df["val"])
            obs_red = "#d62728"
            fig.add_trace(
                go.Scatter(
                    x=xl,
                    y=yl,
                    mode="lines+markers",
                    name="Obs",
                    line=dict(color=obs_red, width=2),
                    marker=dict(size=4, color=obs_red),
                    opacity=0.78,
                    connectgaps=False,
                    hovertemplate=HOVER_TEMPLATE,
                    hoverlabel=_hoverlabel_for_line_color(obs_red),
                )
            )
            title = f"{station_display} — {label}"
            _append_forecast_single_station_leads_sampled(fig, forecast_df, start_date, plot_end)
            if not _forecast_single_station_leads_has_points(forecast_df):
                _annotate_forecast_missing(fig)

    fig.update_layout(
        title=dict(text=title, font=dict(size=14)),
        xaxis_title="Date / time (UTC)",
        yaxis_title="Value",
    )
    _apply_figure_style(fig)
    return fig


def _build_panel2_max_all_stations_figure(
    start_date: datetime, window_hours: int
) -> go.Figure:
    """
    Second panel: max observation across stations vs max forecast (lead 1) at valid time.

    Args:
        start_date: Interval start.
        window_hours: Window length in hours.

    Returns:
        Plotly figure for ``fc-plot-max-all``.
    """
    label = POLLUTANT_MAPPING.get(pollutant_key, pollutant_key)
    plot_end = start_date + timedelta(hours=window_hours)
    obs_max = get_cont_otres_max_val_per_timestamp_all_stations(start_date, window_hours)
    fc_spatial = get_forecast_otres_all_stations_spatial_mean_max(start_date, window_hours)
    fig = go.Figure()

    if not obs_max.empty:
        sub = obs_max.dropna(subset=["max_val"])
        if not sub.empty:
            xl, yl = _scatter_xy_break_time_gaps(sub["fecha"], sub["max_val"])
            obs_red = "#d62728"
            fig.add_trace(
                go.Scatter(
                    x=xl,
                    y=yl,
                    mode="lines",
                    name="Obs_max",
                    line=dict(color=obs_red, width=2.5),
                    connectgaps=False,
                    hovertemplate=HOVER_TEMPLATE,
                    hoverlabel=_hoverlabel_for_line_color(obs_red),
                )
            )
    if not fc_spatial.empty:
        sub_fc = fc_spatial.dropna(subset=["max_hour_p01"])
        if not sub_fc.empty:
            xv = _valid_time_axis(sub_fc["fecha"], 1)
            xv_c, yv_c = _clip_valid_time_series(xv, sub_fc["max_hour_p01"], start_date, plot_end)
            xl, yl = _sorted_xy_for_forecast(xv_c, yv_c)
            fc_blue = "#2171b5"
            fig.add_trace(
                go.Scatter(
                    x=xl,
                    y=yl,
                    mode="lines",
                    name="hour_p01",
                    line=dict(color=fc_blue, width=2.5, dash="dash"),
                    connectgaps=True,
                    hovertemplate=HOVER_TEMPLATE,
                    hoverlabel=_hoverlabel_for_line_color(fc_blue),
                )
            )

    if not fig.data:
        fig.add_annotation(
            text="No max observation or max forecast series in this window",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )

    fig.update_layout(
        title=dict(
            text=f"All stations — {label} spatial maxima (obs at sample time, forecast at valid time)",
            font=dict(size=14),
        ),
        xaxis_title="Date / time (UTC)",
        yaxis_title="Value",
    )
    _apply_figure_style(fig)
    return fig


def _empty_figure(message: str) -> go.Figure:
    """Minimal styled figure carrying a center annotation."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
    )
    _apply_figure_style(fig)
    return fig


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP],
    title="Ozone forecast analyzer",
    suppress_callback_exceptions=False,
)
app.layout = _build_layout()


@callback(
    Output("fc-date-picker", "date"),
    [
        Input("fc-date-prev", "n_clicks"),
        Input("fc-date-next", "n_clicks"),
    ],
    [
        State("fc-date-picker", "date"),
        State("fc-window-slider", "value"),
    ],
    prevent_initial_call=True,
)
def shift_fc_start_date_by_window(
    _prev_clicks: Optional[int],
    _next_clicks: Optional[int],
    current_date: Optional[str],
    window_hours: Optional[int],
) -> str:
    """
    Move the start date backward or forward by the current time-window length.

    For example, with a 288 h window, *Prev* moves the start **date** backward by
    288 hours (12 calendar days when counting from midnight of the selected date).

    Args:
        _prev_clicks: ``n_clicks`` on the previous-window button (unused).
        _next_clicks: ``n_clicks`` on the next-window button (unused).
        current_date: Current ISO date string from the date picker.
        window_hours: Current slider value (hours).

    Returns:
        New ``YYYY-MM-DD`` string for the date picker.
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    if not current_date:
        raise PreventUpdate
    wh = int(window_hours) if window_hours is not None else DEFAULT_WINDOW_HOURS
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    day_str = current_date.split("T")[0]
    base = datetime.fromisoformat(day_str)
    step = timedelta(hours=wh)
    if trigger_id == "fc-date-prev":
        new_dt = base - step
    elif trigger_id == "fc-date-next":
        new_dt = base + step
    else:
        raise PreventUpdate
    return new_dt.strftime("%Y-%m-%d")


@callback(
    [
        Output("fc-plot-otres", "figure"),
        Output("fc-plot-max-all", "figure"),
        Output("fc-metrics-table", "children"),
    ],
    [
        Input("fc-station-dropdown", "value"),
        Input("fc-date-picker", "date"),
        Input("fc-window-slider", "value"),
        Input("fc-initial-trigger", "data"),
    ],
)
def update_forecast_analyzer(
    selected_station: Optional[str],
    date: Optional[str],
    window_hours: Optional[int],
    initial_trigger: Any,
) -> Tuple[go.Figure, go.Figure, html.Div]:
    """
    Update panel 1, panel 2, and the daily-max metrics table.

    Args:
        selected_station: Station id or ``all_stations``.
        date: ISO start date string or None.
        window_hours: Window length in hours.
        initial_trigger: Unused store payload to trigger first render.

    Returns:
        Tuple of (figure panel 1, figure panel 2, metrics table children).
    """
    del initial_trigger

    if not selected_station:
        f1 = _empty_figure("No station selected")
        f2 = _empty_figure("No station selected")
        tbl = html.P("Select a station.", className="text-muted small mb-0")
        return f1, f2, tbl

    if not date:
        f1 = _empty_figure("No date selected")
        f2 = _empty_figure("No date selected")
        tbl = html.P("Select a start date.", className="text-muted small mb-0")
        return f1, f2, tbl

    if window_hours is None:
        f1 = _empty_figure("Invalid time window")
        f2 = _empty_figure("Invalid time window")
        tbl = html.P("Invalid time window.", className="text-muted small mb-0")
        return f1, f2, tbl

    start_date = datetime.fromisoformat(date)
    fig1 = _build_panel1_figure(selected_station, start_date, int(window_hours))
    fig2 = _build_panel2_max_all_stations_figure(start_date, int(window_hours))
    table_children = _build_daily_max_metrics_table(
        selected_station, start_date, int(window_hours)
    )
    return fig1, fig2, table_children


if __name__ == "__main__":
    app.run(
        debug=DASHBOARD_CONFIG["debug"],
        host=DASHBOARD_CONFIG["host"],
        port=DASHBOARD_CONFIG["port"],
    )
