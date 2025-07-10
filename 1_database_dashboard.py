import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import os

# Initialize the Dash app
app = dash.Dash(__name__)

# Import database utilities and queries
from db_utils.sql_common import POLLUTANT_MAPPING
from db_utils.queries import get_stations_data, get_station_name, get_pollutant_data

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
        return [{'label': 'MER', 'value': 'MER'}]
    
    station_options = [{'label': f"{row['nombre']} ({row['id']})", 'value': row['id']} for _, row in df.iterrows()]
    station_options.append({'label': 'All stations', 'value': 'all_stations'})
    return station_options

# App layout
app.layout = html.Div([
    html.H1("Air Quality Data Analysis Dashboard", 
             style={'textAlign': 'center', 'marginBottom': 30}),
    
    dcc.Tabs([
        # Tab 1: By Station
        dcc.Tab(label="By Station", children=[
            html.Div([
                # Controls row
                html.Div([
                    html.Div([
                        html.Label("Station:"),
                        dcc.Dropdown(
                            id='station-dropdown',
                            options=get_stations_list(),
                            value='MER',
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
                            value=7*24,  # 7 days default
                            marks={i: f'{i//24}d' if i % 24 == 0 else f'{i}h' 
                                   for i in [1, 24, 7*24, 30*24, 90*24, 180*24]},
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
     Input('window-slider', 'value')]
)
def update_all_pollutant_plots(selected_station, date, window_hours):
    """Update all pollutant plots based on selected station and parameters."""
    if not selected_station:
        empty_fig = go.Figure().add_annotation(
            text="No station selected",
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



if __name__ == '__main__':
    app.run(
        debug=DASHBOARD_CONFIG['debug'], 
        host=DASHBOARD_CONFIG['host'], 
        port=DASHBOARD_CONFIG['port']
    ) 