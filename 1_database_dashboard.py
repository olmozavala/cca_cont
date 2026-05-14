from typing import Any, Dict, List, Tuple

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html
from datetime import datetime, timedelta

from db_utils.queries_select import (
    get_forecast_otres_all_stations_spatial_mean_max,
    get_forecast_otres_mean_hour_p01,
    get_meteorology_availability_data,
    get_meteorology_data,
    get_pollutant_availability_data,
    get_pollutant_data,
    get_station_name,
    get_stations_data,
)
from db_utils.sql_con import METEOROLOGY_MAPPING, POLLUTANT_MAPPING

default_station = "CCA"
days_before = 5

POLLUTANT_KEYS: List[str] = ["otres", "co", "no", "nox", "pmdiez", "pmdoscinco", "sodos"]
MET_KEYS: List[str] = ["pba", "rh", "tmp", "wdr", "wsp"]

DASHBOARD_CONFIG: Dict[str, Any] = {
    "host": "0.0.0.0",
    "port": 8050,
    "debug": True,
}

SLIDER_MAX_HOURS: int = 24 * 30 * 6
DEFAULT_WINDOW_HOURS: int = 12 * 24


def get_stations_list() -> List[Dict[str, str]]:
    """Return options for station dropdowns."""
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
    """Hour marks for time-window sliders."""
    return {
        i: f"{i // 24}d" if i % 24 == 0 else f"{i}h"
        for i in [1, 24, 7 * 24, 10 * 24, 30 * 24, 90 * 24, 180 * 24]
    }


def _graph_card(title: str, graph_id: str, height: str = "440px") -> dbc.Card:
    """Bootstrap card wrapping a Plotly graph."""
    return dbc.Card(
        [
            dbc.CardHeader(title, className="fw-semibold py-2 bg-light border-0"),
            dbc.CardBody(
                dcc.Graph(id=graph_id, style={"height": height}, config={"displayModeBar": True}),
                className="p-2 pt-0",
            ),
        ],
        className="mb-3 shadow-sm border-0 h-100",
    )


def _control_card_pollution() -> dbc.Card:
    """Filters for pollution tab."""
    return dbc.Card(
        dbc.CardBody(
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Station", className="small text-muted mb-1"),
                            dcc.Dropdown(
                                id="station-dropdown",
                                options=get_stations_list(),
                                value=default_station,
                                clearable=False,
                                className="dash-bootstrap",
                            ),
                        ],
                        xs=12,
                        md=6,
                        lg=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Start date", className="small text-muted mb-1"),
                            dcc.DatePickerSingle(
                                id="date-picker",
                                date=(datetime.now() - timedelta(days=days_before)).strftime("%Y-%m-%d"),
                                display_format="YYYY-MM-DD",
                                className="w-100",
                            ),
                        ],
                        xs=12,
                        md=6,
                        lg=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Time window (hours)", className="small text-muted mb-1"),
                            dcc.Slider(
                                id="window-slider",
                                min=1,
                                max=SLIDER_MAX_HOURS,
                                step=1,
                                value=DEFAULT_WINDOW_HOURS,
                                marks=_slider_marks(),
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                        ],
                        xs=12,
                        lg=5,
                    ),
                ],
                className="g-3 align-items-end",
            )
        ),
        className="mb-3 border-0 shadow-sm",
    )


def _control_card_meteorology() -> dbc.Card:
    """Filters for meteorology tab."""
    return dbc.Card(
        dbc.CardBody(
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Station", className="small text-muted mb-1"),
                            dcc.Dropdown(
                                id="met-station-dropdown",
                                options=get_stations_list(),
                                value=default_station,
                                clearable=False,
                                className="dash-bootstrap",
                            ),
                        ],
                        xs=12,
                        md=6,
                        lg=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Start date", className="small text-muted mb-1"),
                            dcc.DatePickerSingle(
                                id="met-date-picker",
                                date=(datetime.now() - timedelta(days=days_before)).strftime("%Y-%m-%d"),
                                display_format="YYYY-MM-DD",
                                className="w-100",
                            ),
                        ],
                        xs=12,
                        md=6,
                        lg=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Time window (hours)", className="small text-muted mb-1"),
                            dcc.Slider(
                                id="met-window-slider",
                                min=1,
                                max=SLIDER_MAX_HOURS,
                                step=1,
                                value=DEFAULT_WINDOW_HOURS,
                                marks=_slider_marks(),
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                        ],
                        xs=12,
                        lg=5,
                    ),
                ],
                className="g-3 align-items-end",
            )
        ),
        className="mb-3 border-0 shadow-sm",
    )


def _control_card_availability() -> dbc.Card:
    """Filters for data availability tab."""
    return dbc.Card(
        dbc.CardBody(
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Station", className="small text-muted mb-1"),
                            dcc.Dropdown(
                                id="availability-station-dropdown",
                                options=get_stations_list(),
                                value=default_station,
                                clearable=False,
                                className="dash-bootstrap",
                            ),
                        ],
                        xs=12,
                        md=6,
                        lg=4,
                    ),
                ],
                className="g-3",
            )
        ),
        className="mb-3 border-0 shadow-sm",
    )


def _rows_of_cards(pairs: List[Tuple[str, str]], height: str = "440px") -> List[dbc.Row]:
    """Build responsive rows with two graph cards per row on medium+ screens."""
    rows: List[dbc.Row] = []
    for i in range(0, len(pairs), 2):
        chunk = pairs[i : i + 2]
        cols = [
            dbc.Col(_graph_card(title, gid, height=height), xs=12, md=6, className="mb-0")
            for title, gid in chunk
        ]
        rows.append(dbc.Row(cols, className="g-3 mb-1"))
    return rows


def _pollution_plot_pairs() -> List[Tuple[str, str]]:
    return [(POLLUTANT_MAPPING[k], f"plot-{k}") for k in POLLUTANT_KEYS]


def _meteorology_plot_pairs() -> List[Tuple[str, str]]:
    return [(METEOROLOGY_MAPPING[k], f"plot-{k}") for k in MET_KEYS]


def _availability_plot_pairs() -> List[Tuple[str, str]]:
    poll = [
        (f"{POLLUTANT_MAPPING[k]} — monthly counts", f"availability-plot-{k}")
        for k in POLLUTANT_KEYS
    ]
    met = [
        (f"{METEOROLOGY_MAPPING[k]} — monthly counts", f"availability-plot-{k}")
        for k in MET_KEYS
    ]
    return poll + met


def _build_layout() -> dbc.Container:
    """Assemble the full app layout with Bootstrap components."""
    pollution_body = [_control_card_pollution()]
    pollution_body.extend(_rows_of_cards(_pollution_plot_pairs()))

    met_body = [_control_card_meteorology()]
    met_body.extend(_rows_of_cards(_meteorology_plot_pairs()))

    avail_body = [_control_card_availability()]
    avail_body.extend(_rows_of_cards(_availability_plot_pairs(), height="400px"))

    tabs = dbc.Tabs(
        [
            dbc.Tab(
                dbc.Container(pollution_body, fluid=True, className="py-2"),
                label="Pollution by station",
                tab_id="tab-pollution",
            ),
            dbc.Tab(
                dbc.Container(met_body, fluid=True, className="py-2"),
                label="Meteorology by station",
                tab_id="tab-meteorology",
            ),
            dbc.Tab(
                dbc.Container(avail_body, fluid=True, className="py-2"),
                label="Data availability",
                tab_id="tab-availability",
            ),
            dbc.Tab(
                dbc.Container(
                    dbc.Alert(
                        [
                            html.Strong("Coming soon."),
                            " Additional analysis views can be added here.",
                        ],
                        color="info",
                        className="mt-2 border-0 shadow-sm",
                    ),
                    fluid=True,
                    className="py-4",
                ),
                label="Additional analysis",
                tab_id="tab-extra",
            ),
        ],
        id="main-tabs",
        active_tab="tab-pollution",
        className="mb-2 nav-pills",
        persistence=True,
        persistence_type="session",
    )

    return dbc.Container(
        [
            dcc.Store(id="initial-trigger", data=True),
            dbc.NavbarSimple(
                children=[
                    dbc.Badge("Live data", color="light", className="text-primary ms-2", pill=True),
                ],
                brand="Air quality analysis",
                brand_href="#",
                color="primary",
                dark=True,
                className="mb-3 shadow-sm rounded",
                fluid=True,
            ),
            html.P(
                "Explore station time series and monthly record counts. "
                "Use the time window control to adjust the range after the selected start date.",
                className="text-muted lead small mb-3",
            ),
            tabs,
            html.Footer(
                dbc.Container(
                    html.Small(
                        "Dashboard · PostgreSQL contingencia schema",
                        className="text-muted",
                    ),
                    fluid=True,
                    className="py-4 text-center",
                )
            ),
        ],
        fluid=True,
        className="px-3 pb-5 app-container",
    )


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP],
    title="Air quality dashboard",
    suppress_callback_exceptions=False,
)
app.layout = _build_layout()


def _apply_figure_style(fig: go.Figure) -> None:
    """Align Plotly with Bootstrap light theme."""
    fig.update_layout(
        template="plotly_white",
        font=dict(family="system-ui, -apple-system, 'Segoe UI', sans-serif", size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,249,250,0.6)",
        margin=dict(l=48, r=24, t=56, b=48),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )


def _append_forecast_otres_mean_hour_p01(
    fig: go.Figure,
    forecast_df: pd.DataFrame,
    selected_station: str,
) -> None:
    """
    Overlay forecast from ``forecast_otres``.

    * Single station: one black line (mean ``COALESCE(hour_p01, val)`` per time).
    * All stations: black solid = spatial mean across stations; blue dashed = spatial max.
    """
    if forecast_df.empty:
        return

    if selected_station == "all_stations" and "max_hour_p01" in forecast_df.columns:
        mean_df = forecast_df.dropna(subset=["mean_hour_p01"])
        if not mean_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=mean_df["fecha"],
                    y=mean_df["mean_hour_p01"],
                    mode="lines",
                    name="Forecast mean (all stations)",
                    line=dict(color="#000000", width=2.5),
                    legendgroup="forecast_otres_mean",
                )
            )
        max_df = forecast_df.dropna(subset=["max_hour_p01"])
        if not max_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=max_df["fecha"],
                    y=max_df["max_hour_p01"],
                    mode="lines",
                    name="Forecast max (all stations)",
                    line=dict(color="#2171b5", width=2.5, dash="dash"),
                    legendgroup="forecast_otres_max",
                )
            )
        return

    plot_df = forecast_df.dropna(subset=["mean_hour_p01"])
    if plot_df.empty:
        return
    fig.add_trace(
        go.Scatter(
            x=plot_df["fecha"],
            y=plot_df["mean_hour_p01"],
            mode="lines",
            name="Forecast mean (lead 1 h)",
            line=dict(color="#000000", width=2.5),
            legendgroup="forecast_otres",
        )
    )


def _forecast_otres_has_any_points(forecast_df: pd.DataFrame) -> bool:
    """True if any forecast trace would have at least one y value."""
    if forecast_df.empty:
        return False
    if "max_hour_p01" in forecast_df.columns:
        return bool(
            forecast_df["mean_hour_p01"].notna().any()
            or forecast_df["max_hour_p01"].notna().any()
        )
    return bool(forecast_df["mean_hour_p01"].notna().any())


def _annotate_forecast_missing_in_range(fig: go.Figure) -> None:
    """Explain on-chart when observations exist but no forecast rows were returned."""
    fig.add_annotation(
        x=0.01,
        y=0.99,
        xref="paper",
        yref="paper",
        text=(
            "No forecast_otres rows in this date range (or query failed — check DB and logs). "
            "All-stations view expects spatial mean/max series."
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


@app.callback(
    [
        Output("plot-otres", "figure"),
        Output("plot-co", "figure"),
        Output("plot-no", "figure"),
        Output("plot-nox", "figure"),
        Output("plot-pmdiez", "figure"),
        Output("plot-pmdoscinco", "figure"),
        Output("plot-sodos", "figure"),
    ],
    [
        Input("station-dropdown", "value"),
        Input("date-picker", "date"),
        Input("window-slider", "value"),
        Input("initial-trigger", "data"),
    ],
)
def update_all_pollutant_plots(
    selected_station: str,
    date: str,
    window_hours: int,
    initial_trigger: bool,
) -> Tuple[go.Figure, ...]:
    """Update all pollutant plots based on selected station and parameters."""
    del initial_trigger  # present to run on load

    if not selected_station:
        empty = go.Figure()
        empty.add_annotation(
            text="No station selected",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        _apply_figure_style(empty)
        return tuple([empty] * 7)

    if not date:
        empty = go.Figure()
        empty.add_annotation(
            text="No date selected",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        _apply_figure_style(empty)
        return tuple([empty] * 7)

    start_date = datetime.fromisoformat(date)
    station_display_name = get_station_name(selected_station)
    figures: List[go.Figure] = []

    for pollutant in POLLUTANT_KEYS:
        df = get_pollutant_data(selected_station, pollutant, start_date, window_hours)
        label = POLLUTANT_MAPPING.get(pollutant, pollutant)
        forecast_df = (
            (
                get_forecast_otres_all_stations_spatial_mean_max(start_date, window_hours)
                if selected_station == "all_stations"
                else get_forecast_otres_mean_hour_p01(
                    selected_station, start_date, window_hours
                )
            )
            if pollutant == "otres"
            else pd.DataFrame()
        )

        if df.empty:
            if pollutant == "otres" and _forecast_otres_has_any_points(forecast_df):
                fig = go.Figure()
                _append_forecast_otres_mean_hour_p01(fig, forecast_df, selected_station)
                if selected_station == "all_stations":
                    title = f"All stations — {label} (forecast mean / max only)"
                else:
                    title = (
                        f"{station_display_name} — {label} "
                        "(forecast mean hour_p01 only; no observations)"
                    )
                fig.update_layout(
                    title=dict(text=title, font=dict(size=14)),
                    xaxis_title="Date / time (UTC)",
                    yaxis_title="Value",
                    hovermode="closest",
                )
            else:
                fig = go.Figure()
                fig.add_annotation(
                    text=f"No data available for {label}",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                )
        else:
            fig = go.Figure()
            if selected_station == "all_stations" and "id_est" in df.columns:
                for station in df["id_est"].unique():
                    station_data = df[df["id_est"] == station]
                    fig.add_trace(
                        go.Scatter(
                            x=station_data["fecha"],
                            y=station_data["val"],
                            mode="lines+markers",
                            name=str(station),
                            marker=dict(size=3),
                            line=dict(width=1),
                        )
                    )
                title = f"All stations — {label}"
            else:
                fig.add_trace(
                    go.Scatter(
                        x=df["fecha"],
                        y=df["val"],
                        mode="lines+markers",
                        name=label,
                        line=dict(color="#d62728", width=2),
                        marker=dict(size=4),
                    )
                )
                title = f"{station_display_name} — {label}"

            fig.update_layout(
                title=dict(text=title, font=dict(size=14)),
                xaxis_title="Date / time (UTC)",
                yaxis_title="Value",
                hovermode="closest",
            )
            if pollutant == "otres":
                _append_forecast_otres_mean_hour_p01(fig, forecast_df, selected_station)
                if not _forecast_otres_has_any_points(forecast_df):
                    _annotate_forecast_missing_in_range(fig)

        _apply_figure_style(fig)
        figures.append(fig)

    return tuple(figures)


@app.callback(
    [
        Output("plot-pba", "figure"),
        Output("plot-rh", "figure"),
        Output("plot-tmp", "figure"),
        Output("plot-wdr", "figure"),
        Output("plot-wsp", "figure"),
    ],
    [
        Input("met-station-dropdown", "value"),
        Input("met-date-picker", "date"),
        Input("met-window-slider", "value"),
        Input("initial-trigger", "data"),
    ],
)
def update_all_meteorology_plots(
    selected_station: str,
    date: str,
    window_hours: int,
    initial_trigger: bool,
) -> Tuple[go.Figure, ...]:
    """Update all meteorology plots based on selected station and parameters."""
    del initial_trigger

    if not selected_station:
        empty = go.Figure()
        empty.add_annotation(
            text="No station selected",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        _apply_figure_style(empty)
        return tuple([empty] * 5)

    if not date:
        empty = go.Figure()
        empty.add_annotation(
            text="No date selected",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        _apply_figure_style(empty)
        return tuple([empty] * 5)

    start_date = datetime.fromisoformat(date)
    station_display_name = get_station_name(selected_station)
    figures: List[go.Figure] = []

    for field in MET_KEYS:
        df = get_meteorology_data(selected_station, field, start_date, window_hours)
        label = METEOROLOGY_MAPPING.get(field, field)

        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text=f"No data available for {label}",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
        else:
            fig = go.Figure()
            if selected_station == "all_stations" and "id_est" in df.columns:
                for station in df["id_est"].unique():
                    station_data = df[df["id_est"] == station]
                    fig.add_trace(
                        go.Scatter(
                            x=station_data["fecha"],
                            y=station_data["val"],
                            mode="lines+markers",
                            name=str(station),
                            marker=dict(size=3),
                            line=dict(width=1),
                        )
                    )
                title = f"All stations — {label}"
            else:
                fig.add_trace(
                    go.Scatter(
                        x=df["fecha"],
                        y=df["val"],
                        mode="lines+markers",
                        name=label,
                        line=dict(color="#1f77b4", width=2),
                        marker=dict(size=4),
                    )
                )
                title = f"{station_display_name} — {label}"

            fig.update_layout(
                title=dict(text=title, font=dict(size=14)),
                xaxis_title="Date / time (UTC)",
                yaxis_title="Value",
                hovermode="closest",
            )

        _apply_figure_style(fig)
        figures.append(fig)

    return tuple(figures)


@app.callback(
    [
        Output("availability-plot-otres", "figure"),
        Output("availability-plot-co", "figure"),
        Output("availability-plot-no", "figure"),
        Output("availability-plot-nox", "figure"),
        Output("availability-plot-pmdiez", "figure"),
        Output("availability-plot-pmdoscinco", "figure"),
        Output("availability-plot-sodos", "figure"),
        Output("availability-plot-pba", "figure"),
        Output("availability-plot-rh", "figure"),
        Output("availability-plot-tmp", "figure"),
        Output("availability-plot-wdr", "figure"),
        Output("availability-plot-wsp", "figure"),
    ],
    [Input("availability-station-dropdown", "value"), Input("initial-trigger", "data")],
)
def update_all_availability_plots(
    selected_station: str,
    initial_trigger: bool,
) -> Tuple[go.Figure, ...]:
    """Update all data availability plots based on selected station."""
    del initial_trigger

    if not selected_station:
        empty = go.Figure()
        empty.add_annotation(
            text="No station selected",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        _apply_figure_style(empty)
        return tuple([empty] * 12)

    station_display_name = get_station_name(selected_station)
    figures: List[go.Figure] = []

    for pollutant in POLLUTANT_KEYS:
        df = get_pollutant_availability_data(selected_station, pollutant)
        label = POLLUTANT_MAPPING.get(pollutant, pollutant)

        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text=f"No data available for {label}",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
        else:
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=df["month"],
                        y=df["count"],
                        name=label,
                        marker_color="#c0392b",
                        opacity=0.85,
                    )
                ]
            )
            fig.update_layout(
                title=dict(
                    text=f"{station_display_name} — {label}",
                    font=dict(size=14),
                ),
                xaxis_title="Month",
                yaxis_title="Hourly record count",
                hovermode="closest",
                xaxis=dict(range=["2000-01-01", "2025-12-31"], type="date"),
            )

        _apply_figure_style(fig)
        figures.append(fig)

    for field in MET_KEYS:
        df = get_meteorology_availability_data(selected_station, field)
        label = METEOROLOGY_MAPPING.get(field, field)

        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text=f"No data available for {label}",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
        else:
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=df["month"],
                        y=df["count"],
                        name=label,
                        marker_color="#2980b9",
                        opacity=0.85,
                    )
                ]
            )
            fig.update_layout(
                title=dict(
                    text=f"{station_display_name} — {label}",
                    font=dict(size=14),
                ),
                xaxis_title="Month",
                yaxis_title="Hourly record count",
                hovermode="closest",
                xaxis=dict(range=["2000-01-01", "2025-12-31"], type="date"),
            )

        _apply_figure_style(fig)
        figures.append(fig)

    return tuple(figures)


if __name__ == "__main__":
    app.run(
        debug=DASHBOARD_CONFIG["debug"],
        host=DASHBOARD_CONFIG["host"],
        port=DASHBOARD_CONFIG["port"],
    )
