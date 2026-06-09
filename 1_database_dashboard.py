from typing import Any, Dict, List, Optional, Tuple

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html
from datetime import datetime, timedelta

import dash_cytoscape as cyto

from db_utils.schema_introspect import load_schema_snapshot, snapshot_from_store_dict, snapshot_to_store_dict
from db_utils.schema_viz import (
    CATEGORY_COLORS,
    CATEGORY_LABELS,
    build_cytoscape_elements,
    build_cytoscape_stylesheet,
    build_relationship_summary,
    filter_object_names,
    format_tap_edge_detail,
    table_detail_info,
)
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

PLOTLY_GRAPH_CONFIG: Dict[str, Any] = {
    "displayModeBar": True,
    "displaylogo": False,
    "scrollZoom": True,
    "modeBarButtonsToRemove": ["zoomIn", "zoomOut", "lasso2d"],
}


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
                dcc.Graph(id=graph_id, style={"height": height}, config=PLOTLY_GRAPH_CONFIG),
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


def _schema_category_options() -> List[Dict[str, str]]:
    """Dropdown options for schema object category filter."""
    options = [{"label": "All categories", "value": "all"}]
    options.extend(
        {"label": label, "value": key}
        for key, label in CATEGORY_LABELS.items()
    )
    return options


def _schema_role_badge(role: str) -> html.Td:
    """Render a PK/FK badge for the schema detail table."""
    if role == "pk":
        return html.Td(dbc.Badge("PK", color="warning", className="schema-role-badge"))
    if role == "fk":
        return html.Td(dbc.Badge("FK", color="info", className="schema-role-badge"))
    return html.Td(html.Span("—", className="text-muted"))


def _schema_selection_detail(
    snapshot: Any,
    table_id: Optional[str],
) -> html.Div:
    """
    Build the sidebar panel for a selected table or view.

    Args:
        snapshot: Parsed schema metadata.
        table_id: Selected Cytoscape node id.

    Returns:
        Dash HTML for the selection panel.
    """
    if not table_id:
        return html.Div(
            [
                html.P(
                    "Click a table or view in the diagram.",
                    className="mb-2 text-muted",
                ),
                html.P(
                    "Pan: drag background · Zoom: scroll",
                    className="mb-0 small text-muted",
                ),
            ],
            className="schema-sidebar-panel",
        )

    detail = table_detail_info(snapshot, table_id)
    if not detail:
        return html.Div(
            f"Unknown object: {table_id}",
            className="schema-sidebar-panel text-muted",
        )

    category = detail["category"]
    border_color = CATEGORY_COLORS.get(category, "#6c757d")
    kind_label = "VIEW" if detail["kind"] == "view" else "TABLE"
    kind_color = "secondary" if detail["kind"] == "view" else "primary"

    header = html.Div(
        [
            html.Div(
                [
                    html.Strong(detail["name"], className="schema-detail-title"),
                    dbc.Badge(
                        kind_label,
                        color=kind_color,
                        className="ms-2 align-middle",
                    ),
                    dbc.Badge(
                        CATEGORY_LABELS.get(category, category),
                        color="light",
                        text_color="dark",
                        className="ms-1 align-middle",
                    ),
                ],
                className="mb-2",
            ),
            html.P(
                f"{len(detail['columns'])} column(s)",
                className="small text-muted mb-2",
            ),
        ],
        className="schema-detail-header",
        style={"borderLeftColor": border_color},
    )

    body_rows = [
        html.Tr(
            [
                _schema_role_badge(col["role"]),
                html.Td(col["name"], className="schema-col-name"),
                html.Td(
                    [
                        html.Code(col["type"], className="schema-col-type"),
                        html.Span(
                            " nullable" if col["nullable"] == "yes" else "",
                            className="text-muted small",
                        ),
                    ]
                ),
            ]
        )
        for col in detail["columns"]
    ]

    table = dbc.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("", className="schema-th-role"),
                        html.Th("Column"),
                        html.Th("Type"),
                    ]
                )
            ),
            html.Tbody(body_rows),
        ],
        bordered=True,
        hover=True,
        size="sm",
        responsive=True,
        className="schema-detail-table mb-0",
    )

    return html.Div([header, table], className="schema-sidebar-panel")


def _schema_legend() -> html.Div:
    """Color legend for schema graph node categories."""
    items = [
        html.Span(
            [
                html.Span(className="schema-legend-dot", style={"background": color}),
                CATEGORY_LABELS.get(key, key),
            ],
            className="me-3 small",
        )
        for key, color in CATEGORY_COLORS.items()
    ]
    return html.Div(items, className="d-flex flex-wrap mb-2")


def _schema_tab_body() -> List[Any]:
    """Interactive ER diagram (Dash Cytoscape)."""
    return [
        dcc.Store(id="schema-metadata"),
        dcc.Store(id="schema-tapped-node"),
        dbc.Card(
            dbc.CardBody(
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("Search tables / columns", className="small text-muted mb-1"),
                                dbc.Input(
                                    id="schema-search",
                                    type="search",
                                    placeholder="e.g. cont_otres, id_est…",
                                    debounce=True,
                                ),
                            ],
                            xs=12,
                            md=4,
                            lg=3,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Category", className="small text-muted mb-1"),
                                dcc.Dropdown(
                                    id="schema-category-filter",
                                    options=_schema_category_options(),
                                    value="all",
                                    clearable=False,
                                ),
                            ],
                            xs=12,
                            md=4,
                            lg=2,
                        ),
                        dbc.Col(
                            dbc.Checklist(
                                id="schema-show-views",
                                options=[{"label": " Views", "value": "views"}],
                                value=["views"],
                                inline=True,
                                className="mt-4",
                            ),
                            xs="auto",
                        ),
                        dbc.Col(
                            dbc.Checklist(
                                id="schema-show-system",
                                options=[{"label": " PostGIS / system", "value": "system"}],
                                value=[],
                                inline=True,
                                className="mt-4",
                            ),
                            xs="auto",
                        ),
                        dbc.Col(
                            dbc.Checklist(
                                id="schema-show-inferred",
                                options=[
                                    {
                                        "label": " Inferred id_est links",
                                        "value": "inferred",
                                    }
                                ],
                                value=["inferred"],
                                inline=True,
                                className="mt-4",
                            ),
                            xs="auto",
                        ),
                        dbc.Col(
                            dbc.Button(
                                [html.I(className="bi bi-arrow-clockwise me-1"), "Refresh schema"],
                                id="schema-refresh-btn",
                                color="secondary",
                                outline=True,
                                size="sm",
                                className="mt-3",
                            ),
                            xs="auto",
                            className="ms-auto",
                        ),
                    ],
                    className="g-2 align-items-start",
                )
            ),
            className="mb-3 border-0 shadow-sm",
        ),
        _schema_legend(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H6("Selection", className="fw-semibold mb-2"),
                        html.Div(
                            id="schema-selected-detail",
                            children=_schema_selection_detail(None, None),
                            className="schema-sidebar-panel-wrap",
                        ),
                        html.H6("Foreign keys", className="fw-semibold mb-2 mt-3"),
                        html.Pre(id="schema-edge-detail", className="schema-sidebar-pre mb-2"),
                        html.Ul(id="schema-fk-summary", className="schema-fk-list mb-0"),
                        html.P(
                            "PK = primary key · FK = outgoing foreign key",
                            className="text-muted small mt-3 mb-0",
                        ),
                    ],
                    xs=12,
                    lg=3,
                    className="mb-3 mb-lg-0",
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            cyto.Cytoscape(
                                id="schema-erd",
                                elements=[],
                                stylesheet=[],
                                layout={"name": "preset"},
                                style={"width": "100%", "height": "100%"},
                                className="schema-erd-cy",
                                minZoom=0.15,
                                maxZoom=2.5,
                                wheelSensitivity=0.15,
                                userPanningEnabled=True,
                                userZoomingEnabled=True,
                                boxSelectionEnabled=False,
                            ),
                            className="p-2 schema-erd-panel",
                        ),
                        className="border-0 shadow-sm h-100",
                    ),
                    xs=12,
                    lg=9,
                ),
            ],
            className="g-3",
        ),
    ]


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
                dbc.Container(_schema_tab_body(), fluid=True, className="py-2"),
                label="Database schema",
                tab_id="tab-schema",
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
    suppress_callback_exceptions=True,
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


@app.callback(
    Output("schema-metadata", "data"),
    [Input("initial-trigger", "data"), Input("schema-refresh-btn", "n_clicks")],
)
def load_schema_metadata(initial_trigger: bool, refresh_clicks: Optional[int]) -> Dict[str, object]:
    """Load PostgreSQL schema into a session store (on load and on refresh)."""
    del initial_trigger, refresh_clicks
    snapshot = load_schema_snapshot()
    return snapshot_to_store_dict(snapshot)


def _schema_filter_flags(
    show_views_values: Optional[List[str]],
    show_system_values: Optional[List[str]],
    show_inferred_values: Optional[List[str]],
) -> Tuple[bool, bool, bool]:
    """Parse schema tab checklist values."""
    return (
        "views" in (show_views_values or []),
        "system" in (show_system_values or []),
        "inferred" in (show_inferred_values or []),
    )


@app.callback(
    Output("schema-tapped-node", "data"),
    [Input("schema-erd", "tapNodeData")],
)
def store_tapped_node(node_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Remember the last tapped table/view for highlighting."""
    return node_data


@app.callback(
    Output("schema-erd", "elements"),
    [
        Input("schema-metadata", "data"),
        Input("schema-category-filter", "value"),
        Input("schema-show-views", "value"),
        Input("schema-show-system", "value"),
        Input("schema-show-inferred", "value"),
    ],
)
def update_schema_erd_elements(
    metadata: Optional[Dict[str, object]],
    category: str,
    show_views_values: Optional[List[str]],
    show_system_values: Optional[List[str]],
    show_inferred_values: Optional[List[str]],
) -> List[Dict[str, Any]]:
    """Build Cytoscape nodes and edges from live PostgreSQL metadata."""
    snapshot = snapshot_from_store_dict(metadata)
    if not snapshot.tables and not snapshot.views:
        return []

    show_views, show_system, include_inferred = _schema_filter_flags(
        show_views_values, show_system_values, show_inferred_values
    )
    visible = filter_object_names(
        snapshot,
        "",
        category or "all",
        show_views,
        show_system,
        apply_search=False,
    )
    return build_cytoscape_elements(snapshot, visible, include_inferred)


@app.callback(
    Output("schema-erd", "stylesheet"),
    [
        Input("schema-metadata", "data"),
        Input("schema-search", "value"),
        Input("schema-category-filter", "value"),
        Input("schema-show-views", "value"),
        Input("schema-show-system", "value"),
        Input("schema-show-inferred", "value"),
        Input("schema-tapped-node", "data"),
    ],
)
def update_schema_erd_stylesheet(
    metadata: Optional[Dict[str, object]],
    search: Optional[str],
    category: str,
    show_views_values: Optional[List[str]],
    show_system_values: Optional[List[str]],
    show_inferred_values: Optional[List[str]],
    tapped_node: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Apply search hits and neighborhood highlighting on the ER diagram."""
    snapshot = snapshot_from_store_dict(metadata)
    show_views, show_system, include_inferred = _schema_filter_flags(
        show_views_values, show_system_values, show_inferred_values
    )
    visible = filter_object_names(
        snapshot,
        search or "",
        category or "all",
        show_views,
        show_system,
    )
    selected_id = str(tapped_node["id"]) if tapped_node and tapped_node.get("id") else None
    return build_cytoscape_stylesheet(
        search,
        selected_id,
        snapshot,
        visible,
        include_inferred,
    )


@app.callback(
    [
        Output("schema-selected-detail", "children"),
        Output("schema-fk-summary", "children"),
    ],
    [Input("schema-erd", "tapNodeData"), Input("schema-metadata", "data"), Input("schema-show-inferred", "value")],
)
def show_tapped_table_detail(
    node_data: Optional[Dict[str, Any]],
    metadata: Optional[Dict[str, object]],
    show_inferred_values: Optional[List[str]],
) -> Tuple[html.Div, List[html.Li]]:
    """Show column list and FK summary when a table node is tapped."""
    snapshot = snapshot_from_store_dict(metadata)
    include_inferred = "inferred" in (show_inferred_values or [])
    table_id = str(node_data["id"]) if node_data and node_data.get("id") else None
    fk_lines = build_relationship_summary(snapshot, table_id, include_inferred)
    fk_items = [html.Li(line, className="mb-1") for line in fk_lines] or [
        html.Li("No foreign keys for this object.", className="text-muted")
    ]
    return _schema_selection_detail(snapshot, table_id), fk_items


@app.callback(
    Output("schema-edge-detail", "children"),
    [Input("schema-erd", "tapEdgeData")],
)
def show_tapped_edge_detail(edge_data: Optional[Dict[str, Any]]) -> str:
    """Show FK detail when an edge is tapped."""
    return format_tap_edge_detail(edge_data) or "Click an edge to see the foreign key."


if __name__ == "__main__":
    app.run(
        debug=DASHBOARD_CONFIG["debug"],
        host=DASHBOARD_CONFIG["host"],
        port=DASHBOARD_CONFIG["port"],
    )
