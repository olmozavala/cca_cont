from typing import List, Dict, Any
import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import os

# Initialize the Dash app
app = dash.Dash(__name__)

# Import database utilities and queries
from db_utils.sql_con import POLLUTANT_MAPPING, METEOROLOGY_MAPPING
from db_utils.queries_select import get_stations_data, get_station_name, get_pollutant_data, get_meteorology_data, get_pollutant_availability_data, get_meteorology_availability_data

default_station = 'ACO'

# Dashboard configuration
DASHBOARD_CONFIG = {
    'host': '0.0.0.0',
    'port': 8050,
    'debug': True
}

# Get stations for dropdown
def get_stations_list():
    """Get list of stations for dropdown."""
    df = get_stations_data()
    if df.empty:
        return [{'label': default_station, 'value': default_station}]
    
    station_options = [{'label': f"{row['nombre']} ({row['id']})", 'value': row['id']} for _, row in df.iterrows()]
    station_options.append({'label': 'All stations', 'value': 'all_stations'})
    return station_options

# App layout
app.layout = html.Div([
    # Store component to trigger initial callback
    dcc.Store(id='initial-trigger', data=True),
    
    html.H1("Air Quality Data Analysis Dashboard", 
             style={'textAlign': 'center', 'marginBottom': 30}),
    
    dcc.Tabs([
        # Tab 1: Pollution By Station
        dcc.Tab(label="Pollution By Station", children=[
            html.Div([
                # Controls row
                html.Div([
                    html.Div([
                        html.Label("Station:"),
                        dcc.Dropdown(
                            id='station-dropdown',
                            options=get_stations_list(),
                            value=default_station,
                            style={'width': '250px'}
                        )
                    ], style={'display': 'inline-block', 'marginRight': '20px'}),
                    
                    html.Div([
                        html.Label("Start Date:"),
                        dcc.DatePickerSingle(
                            id='date-picker',
                            date=(datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
                            style={'width': '200px'}
                        )
                    ], style={'display': 'inline-block', 'marginRight': '20px'}),
                    
                    html.Div([
                        html.Label("Window Size (hours):", style={'fontSize': '16px', 'fontWeight': 'bold'}),
                        dcc.Slider(
                            id='window-slider',
                            min=1,
                            max=24*30*6,  # 6 months in hours
                            step=1,
                            value=12*24,  # 12 days default
                            marks={i: f'{i//24}d' if i % 24 == 0 else f'{i}h' 
                                   for i in [1, 24, 7*24, 10*24, 30*24, 90*24, 180*24]},
                            tooltip={"placement": "bottom", "always_visible": True}
                        )
                    ], style={'display': 'inline-block', 'width': '700px', 'marginTop': '10px'})
                ], style={'marginBottom': '20px'}),
                
                # Pollutant plots - 2x3 grid
                html.Div([
                    # Row 1
                    html.Div([
                        html.Div([
                            html.H4("Ozone (O₃)"),
                            dcc.Graph(id='plot-otres', style={'height': '450px'})
                        ], style={'width': '50%', 'display': 'inline-block'}),
                        html.Div([
                            html.H4("Carbon monoxide (CO)"),
                            dcc.Graph(id='plot-co', style={'height': '450px'})
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ]),
                    # Row 2
                    html.Div([
                        html.Div([
                            html.H4("Nitric oxide (NO)"),
                            dcc.Graph(id='plot-no', style={'height': '450px'})
                        ], style={'width': '50%', 'display': 'inline-block'}),
                        html.Div([
                            html.H4("Nitrogen oxides (NOₓ)"),
                            dcc.Graph(id='plot-nox', style={'height': '450px'})
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ]),
                    # Row 3
                    html.Div([
                        html.Div([
                            html.H4("Particulate matter ≤ 10 µm (PM₁₀)"),
                            dcc.Graph(id='plot-pmdiez', style={'height': '450px'})
                        ], style={'width': '50%', 'display': 'inline-block'}),
                        html.Div([
                            html.H4("Particulate matter ≤ 2.5 µm (PM₂.₅)"),
                            dcc.Graph(id='plot-pmdoscinco', style={'height': '450px'})
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ]),
                    # Row 4 - Single plot for CO₂
                    html.Div([
                        html.Div([
                            html.H4("Carbon dioxide (CO₂)"),
                            dcc.Graph(id='plot-sodos', style={'height': '450px'})
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ])
                ])
            ])
        ]),
        
        # Tab 2: Meteorology By Station
        dcc.Tab(label="Meteorology By Station", children=[
            html.Div([
                # Controls row
                html.Div([
                    html.Div([
                        html.Label("Station:"),
                        dcc.Dropdown(
                            id='met-station-dropdown',
                            options=get_stations_list(),
                            value=default_station,
                            style={'width': '250px'}
                        )
                    ], style={'display': 'inline-block', 'marginRight': '20px'}),
                    
                    html.Div([
                        html.Label("Start Date:"),
                        dcc.DatePickerSingle(
                            id='met-date-picker',
                            date=(datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
                            style={'width': '200px'}
                        )
                    ], style={'display': 'inline-block', 'marginRight': '20px'}),
                    
                    html.Div([
                        html.Label("Window Size (hours):", style={'fontSize': '16px', 'fontWeight': 'bold'}),
                        dcc.Slider(
                            id='met-window-slider',
                            min=1,
                            max=24*30*6,  # 6 months in hours
                            step=1,
                            value=12*24,  # 12 days default
                            marks={i: f'{i//24}d' if i % 24 == 0 else f'{i}h' 
                                   for i in [1, 24, 7*24, 10*24, 30*24, 90*24, 180*24]},
                            tooltip={"placement": "bottom", "always_visible": True}
                        )
                    ], style={'display': 'inline-block', 'width': '700px', 'marginTop': '10px'})
                ], style={'marginBottom': '20px'}),
                
                # Meteorology plots - 2x3 grid
                html.Div([
                    # Row 1
                    html.Div([
                        html.Div([
                            html.H4("Atmospheric pressure (PBA)"),
                            dcc.Graph(id='plot-pba', style={'height': '450px'})
                        ], style={'width': '50%', 'display': 'inline-block'}),
                        html.Div([
                            html.H4("Relative humidity (RH)"),
                            dcc.Graph(id='plot-rh', style={'height': '450px'})
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ]),
                    # Row 2
                    html.Div([
                        html.Div([
                            html.H4("Temperature (TMP)"),
                            dcc.Graph(id='plot-tmp', style={'height': '450px'})
                        ], style={'width': '50%', 'display': 'inline-block'}),
                        html.Div([
                            html.H4("Wind direction (WDR)"),
                            dcc.Graph(id='plot-wdr', style={'height': '450px'})
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ]),
                    # Row 3 - Single plot for Wind speed
                    html.Div([
                        html.Div([
                            html.H4("Wind speed (WSP)"),
                            dcc.Graph(id='plot-wsp', style={'height': '450px'})
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ])
                ])
            ])
        ]),
        
        # Tab 3: Data Availability
        dcc.Tab(label="Data Availability", children=[
            html.Div([
                # Controls row
                html.Div([
                    html.Div([
                        html.Label("Station:"),
                        dcc.Dropdown(
                            id='availability-station-dropdown',
                            options=get_stations_list(),
                            value=default_station,
                            style={'width': '250px'}
                        )
                    ], style={'display': 'inline-block', 'marginRight': '20px'})
                ], style={'marginBottom': '20px'}),
                
                # Data availability plots - 2-column grid
                html.Div([
                    # Row 1 - Pollutants
                    html.Div([
                        html.Div([
                            html.H4("Ozone (O₃) - Data Availability"),
                            dcc.Graph(id='availability-plot-otres', style={'height': '400px'})
                        ], style={'width': '50%', 'display': 'inline-block'}),
                        html.Div([
                            html.H4("Carbon monoxide (CO) - Data Availability"),
                            dcc.Graph(id='availability-plot-co', style={'height': '400px'})
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ]),
                    # Row 2 - Pollutants
                    html.Div([
                        html.Div([
                            html.H4("Nitric oxide (NO) - Data Availability"),
                            dcc.Graph(id='availability-plot-no', style={'height': '400px'})
                        ], style={'width': '50%', 'display': 'inline-block'}),
                        html.Div([
                            html.H4("Nitrogen oxides (NOₓ) - Data Availability"),
                            dcc.Graph(id='availability-plot-nox', style={'height': '400px'})
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ]),
                    # Row 3 - Pollutants
                    html.Div([
                        html.Div([
                            html.H4("Particulate matter ≤ 10 µm (PM₁₀) - Data Availability"),
                            dcc.Graph(id='availability-plot-pmdiez', style={'height': '400px'})
                        ], style={'width': '50%', 'display': 'inline-block'}),
                        html.Div([
                            html.H4("Particulate matter ≤ 2.5 µm (PM₂.₅) - Data Availability"),
                            dcc.Graph(id='availability-plot-pmdoscinco', style={'height': '400px'})
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ]),
                    # Row 4 - Pollutants
                    html.Div([
                        html.Div([
                            html.H4("Carbon dioxide (CO₂) - Data Availability"),
                            dcc.Graph(id='availability-plot-sodos', style={'height': '400px'})
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ]),
                    # Row 5 - Meteorology
                    html.Div([
                        html.Div([
                            html.H4("Atmospheric pressure (PBA) - Data Availability"),
                            dcc.Graph(id='availability-plot-pba', style={'height': '400px'})
                        ], style={'width': '50%', 'display': 'inline-block'}),
                        html.Div([
                            html.H4("Relative humidity (RH) - Data Availability"),
                            dcc.Graph(id='availability-plot-rh', style={'height': '400px'})
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ]),
                    # Row 6 - Meteorology
                    html.Div([
                        html.Div([
                            html.H4("Temperature (TMP) - Data Availability"),
                            dcc.Graph(id='availability-plot-tmp', style={'height': '400px'})
                        ], style={'width': '50%', 'display': 'inline-block'}),
                        html.Div([
                            html.H4("Wind direction (WDR) - Data Availability"),
                            dcc.Graph(id='availability-plot-wdr', style={'height': '400px'})
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ]),
                    # Row 7 - Meteorology
                    html.Div([
                        html.Div([
                            html.H4("Wind speed (WSP) - Data Availability"),
                            dcc.Graph(id='availability-plot-wsp', style={'height': '400px'})
                        ], style={'width': '50%', 'display': 'inline-block'})
                    ])
                ])
            ])
        ]),
        
        # Placeholder for additional tabs
        dcc.Tab(label="Additional Analysis", children=[
            html.H3("Additional analysis tabs will be added here")
        ])
    ])
])

# Callback to update all pollutant plots
@app.callback(
    [Output('plot-otres', 'figure'),
     Output('plot-co', 'figure'),
     Output('plot-no', 'figure'),
     Output('plot-nox', 'figure'),
     Output('plot-pmdiez', 'figure'),
     Output('plot-pmdoscinco', 'figure'),
     Output('plot-sodos', 'figure')],
    [Input('station-dropdown', 'value'),
     Input('date-picker', 'date'),
     Input('window-slider', 'value'),
     Input('initial-trigger', 'data')]
)
def update_all_pollutant_plots(selected_station, date, window_hours, initial_trigger):
    """Update all pollutant plots based on selected station and parameters."""
    if not selected_station:
        empty_fig = go.Figure().add_annotation(
            text="No station selected",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return [empty_fig] * 7  # Return empty figures for all 7 pollutants
    
    if not date:
        empty_fig = go.Figure().add_annotation(
            text="No date selected",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return [empty_fig] * 7  # Return empty figures for all 7 pollutants
    
    start_date = datetime.fromisoformat(date.replace('-', '-'))
    station_display_name = get_station_name(selected_station)
    
    # Define pollutants and their plot IDs
    pollutants = ['otres', 'co', 'no', 'nox', 'pmdiez', 'pmdoscinco', 'sodos']
    
    figures = []
    
    for pollutant in pollutants:
        df = get_pollutant_data(selected_station, pollutant, start_date, window_hours)
        
        if df.empty:
            fig = go.Figure().add_annotation(
                text=f"No data available for {POLLUTANT_MAPPING.get(pollutant, pollutant)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        else:
            fig = go.Figure()
            
            if selected_station == 'all_stations' and 'id_est' in df.columns:
                # Plot data for all stations
                for station in df['id_est'].unique():
                    station_data = df[df['id_est'] == station]
                    fig.add_trace(go.Scatter(
                        x=station_data['fecha'],
                        y=station_data['val'],
                        mode='lines+markers',
                        name=f"Station {station}",
                        marker=dict(size=3)
                    ))
                title = f"All Stations - {POLLUTANT_MAPPING.get(pollutant, pollutant)}"
            else:
                # Plot data for single station
                fig.add_trace(go.Scatter(
                    x=df['fecha'],
                    y=df['val'],
                    mode='lines+markers',
                    name=POLLUTANT_MAPPING.get(pollutant, pollutant),
                    line=dict(color='red', width=2),
                    marker=dict(size=3)
                ))
                title = f"{station_display_name} - {POLLUTANT_MAPPING.get(pollutant, pollutant)}"
            
            fig.update_layout(
                title=title,
                xaxis_title="Date/Time",
                yaxis_title="Concentration",
                hovermode='x unified',
                margin=dict(l=50, r=20, t=50, b=50)
            )
        
        figures.append(fig)
    
    return figures


# Callback to update all meteorology plots
@app.callback(
    [Output('plot-pba', 'figure'),
     Output('plot-rh', 'figure'),
     Output('plot-tmp', 'figure'),
     Output('plot-wdr', 'figure'),
     Output('plot-wsp', 'figure')],
    [Input('met-station-dropdown', 'value'),
     Input('met-date-picker', 'date'),
     Input('met-window-slider', 'value'),
     Input('initial-trigger', 'data')]
)
def update_all_meteorology_plots(selected_station, date, window_hours, initial_trigger):
    """Update all meteorology plots based on selected station and parameters."""
    if not selected_station:
        empty_fig = go.Figure().add_annotation(
            text="No station selected",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return [empty_fig] * 5  # Return empty figures for all 5 meteorology fields
    
    if not date:
        empty_fig = go.Figure().add_annotation(
            text="No date selected",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return [empty_fig] * 5  # Return empty figures for all 5 meteorology fields
    
    start_date = datetime.fromisoformat(date.replace('-', '-'))
    station_display_name = get_station_name(selected_station)
    
    # Define meteorology fields and their plot IDs
    meteorology_fields = ['pba', 'rh', 'tmp', 'wdr', 'wsp']
    
    figures = []
    
    for field in meteorology_fields:
        df = get_meteorology_data(selected_station, field, start_date, window_hours)
        
        if df.empty:
            fig = go.Figure().add_annotation(
                text=f"No data available for {METEOROLOGY_MAPPING.get(field, field)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        else:
            fig = go.Figure()
            
            if selected_station == 'all_stations' and 'id_est' in df.columns:
                # Plot data for all stations
                for station in df['id_est'].unique():
                    station_data = df[df['id_est'] == station]
                    fig.add_trace(go.Scatter(
                        x=station_data['fecha'],
                        y=station_data['val'],
                        mode='lines+markers',
                        name=f"Station {station}",
                        marker=dict(size=3)
                    ))
                title = f"All Stations - {METEOROLOGY_MAPPING.get(field, field)}"
            else:
                # Plot data for single station
                fig.add_trace(go.Scatter(
                    x=df['fecha'],
                    y=df['val'],
                    mode='lines+markers',
                    name=METEOROLOGY_MAPPING.get(field, field),
                    line=dict(color='blue', width=2),
                    marker=dict(size=3)
                ))
                title = f"{station_display_name} - {METEOROLOGY_MAPPING.get(field, field)}"
            
            fig.update_layout(
                title=title,
                xaxis_title="Date/Time",
                yaxis_title="Value",
                hovermode='x unified',
                margin=dict(l=50, r=20, t=50, b=50)
            )
        
        figures.append(fig)
    
    return figures


# Callback to update all data availability plots
@app.callback(
    [Output('availability-plot-otres', 'figure'),
     Output('availability-plot-co', 'figure'),
     Output('availability-plot-no', 'figure'),
     Output('availability-plot-nox', 'figure'),
     Output('availability-plot-pmdiez', 'figure'),
     Output('availability-plot-pmdoscinco', 'figure'),
     Output('availability-plot-sodos', 'figure'),
     Output('availability-plot-pba', 'figure'),
     Output('availability-plot-rh', 'figure'),
     Output('availability-plot-tmp', 'figure'),
     Output('availability-plot-wdr', 'figure'),
     Output('availability-plot-wsp', 'figure')],
    [Input('availability-station-dropdown', 'value'),
     Input('initial-trigger', 'data')]
)
def update_all_availability_plots(selected_station, initial_trigger):
    """Update all data availability plots based on selected station."""
    if not selected_station:
        empty_fig = go.Figure().add_annotation(
            text="No station selected",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return [empty_fig] * 12  # Return empty figures for all 12 plots
    
    station_display_name = get_station_name(selected_station)
    
    # Define pollutants and meteorology fields
    pollutants = ['otres', 'co', 'no', 'nox', 'pmdiez', 'pmdoscinco', 'sodos']
    meteorology_fields = ['pba', 'rh', 'tmp', 'wdr', 'wsp']
    
    figures = []
    
    # Process pollutant availability plots
    for pollutant in pollutants:
        df = get_pollutant_availability_data(selected_station, pollutant)
        
        if df.empty:
            fig = go.Figure().add_annotation(
                text=f"No data available for {POLLUTANT_MAPPING.get(pollutant, pollutant)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        else:
            fig = go.Figure()
            
            # Create bar chart
            fig.add_trace(go.Bar(
                x=df['month'],
                y=df['count'],
                name=POLLUTANT_MAPPING.get(pollutant, pollutant),
                marker_color='red'
            ))
            
            title = f"{station_display_name} - {POLLUTANT_MAPPING.get(pollutant, pollutant)} Data Availability"
            
            fig.update_layout(
                title=title,
                xaxis_title="Month",
                yaxis_title="Hourly Data Count",
                xaxis=dict(
                    range=['2000-01-01', '2025-12-31'],
                    type='date'
                ),
                margin=dict(l=50, r=20, t=50, b=50)
            )
        
        figures.append(fig)
    
    # Process meteorology availability plots
    for field in meteorology_fields:
        df = get_meteorology_availability_data(selected_station, field)
        
        if df.empty:
            fig = go.Figure().add_annotation(
                text=f"No data available for {METEOROLOGY_MAPPING.get(field, field)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        else:
            fig = go.Figure()
            
            # Create bar chart
            fig.add_trace(go.Bar(
                x=df['month'],
                y=df['count'],
                name=METEOROLOGY_MAPPING.get(field, field),
                marker_color='blue'
            ))
            
            title = f"{station_display_name} - {METEOROLOGY_MAPPING.get(field, field)} Data Availability"
            
            fig.update_layout(
                title=title,
                xaxis_title="Month",
                yaxis_title="Hourly Data Count",
                xaxis=dict(
                    range=['2000-01-01', '2025-12-31'],
                    type='date'
                ),
                margin=dict(l=50, r=20, t=50, b=50)
            )
        
        figures.append(fig)
    
    return figures


if __name__ == '__main__':
    app.run(
        debug=DASHBOARD_CONFIG['debug'], 
        host=DASHBOARD_CONFIG['host'], 
        port=DASHBOARD_CONFIG['port']
    ) 