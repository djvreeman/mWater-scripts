"""
Script Name: run_sensor_dashboard_for_web.py

Purpose:
This script generates an interactive dashboard to visualize water usage sensor data. It processes data from a CSV file, extracts key insights, and provides several visualizations to help monitor water usage and sensor activity over time.

Functionality:
1. Loads sensor data from a CSV file and preprocesses it.
2. Determines the local timezone of the sensor based on latitude and longitude and converts timestamps to local time.
3. Calculates key metrics such as average water usage, estimated beneficiaries, and seasonal usage trends.
4. Creates an interactive dashboard using Dash with various plots and metrics, including:
   - Daily Water Flow
   - Average Hourly Water Usage
   - Water Usage vs Sensor Temperature
   - Seasonal Water Usage Comparison
   - Red Flag Events Over Time
5. Displays sensor metadata, including location, installation date, and service provider.

Usage:
Run the script from the command line with the following required arguments:
    python create-sensor-dashboard.py -f <path_to_csv_file>
Example:
    python create-sensor-dashboard.py -f sensor_data.csv

Inputs:
- CSV File: Contains water usage data with fields such as:
  - 'gmt_datetime': UTC timestamps for water usage events.
  - 'latitude' and 'longitude': Sensor location.
  - 'liters': Amount of water used per reading.
  - 'red_flag': Indicator of potential issues.

Outputs:
- Interactive Dashboard: Provides visual insights through the following plots:
  - Daily Water Flow
  - Average Hourly Water Usage
  - Water Usage vs Sensor Temperature
  - Seasonal Water Usage Comparison
  - Red Flag Events Over Time

Dependencies:
- Python 3.x
- Libraries: pandas, pytz, timezonefinder, dash, plotly, argparse

Author: Daniel J. Vreeman, PT, DPT, MS, FACMI, FIAHSI
Date: [Creation or Last Modified Date]

Notes:
- Ensure the CSV file contains valid and complete data for the sensor.
- The dashboard will automatically detect and adjust timestamps based on the sensor's location.
- This script assumes a consistent schema in the input CSV file.
"""

import os
import json
import pandas as pd
import pytz
from timezonefinder import TimezoneFinder
import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px

# Directory containing sensor data files
DATA_DIR = "/var/www/sensor-data"

# Define the path to the configuration file
CONFIG_PATH = os.path.join(DATA_DIR ,"config", "dashboard-config.json")

def load_passwords(config_path):
    """Load passwords from a JSON configuration file."""
    try:
        with open(config_path, "r") as file:
            config = json.load(file)
            return config.get("passwords", [])
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{config_path}'.")
        return []

def load_data(csv_file):
    """Load and preprocess sensor data from CSV."""
    df = pd.read_csv(csv_file)

    # Convert datetime fields to UTC
    df['gmt_datetime'] = pd.to_datetime(df['gmt_datetime'], utc=True)

    # Extract robust metadata
    metadata = extract_metadata(df)

    # Find the timezone using latitude and longitude
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lat=metadata['latitude'], lng=metadata['longitude'])

    if timezone_str is None:
        raise ValueError("Could not determine the timezone for the given location.")

    # Convert timestamps to local timezone
    local_tz = pytz.timezone(timezone_str)
    df['local_datetime'] = df['gmt_datetime'].dt.tz_convert(local_tz)

    # Extract date, month, and hour in local time
    df['date'] = df['local_datetime'].dt.date
    df['month'] = df['local_datetime'].dt.month
    df['hour'] = df['local_datetime'].dt.hour

    # Assign seasons based on the month
    df['season'] = df['month'].apply(determine_season)

    return df, metadata, timezone_str

def extract_metadata(df):
    """Extract robust metadata by scanning the dataset."""
    valid_lat_lon = df[['latitude', 'longitude']].dropna().iloc[0] if not df[['latitude', 'longitude']].dropna().empty else {'latitude': 0, 'longitude': 0}

    metadata = {
        'latitude': valid_lat_lon['latitude'],
        'longitude': valid_lat_lon['longitude'],
        'community_name': df['community_name'].mode().values[0] if not df['community_name'].mode().empty else 'Unknown',
        'service_provider': df['service_provider'].mode().values[0] if not df['service_provider'].mode().empty else 'Unknown',
        'water_point_name': df['water_point_name'].mode().values[0] if not df['water_point_name'].mode().empty else 'Unknown',
        'installation_date': df['installation_date'].mode().values[0] if 'installation_date' in df and not df['installation_date'].mode().empty else 'Unknown',
        'model': df['model'].mode().values[0] if not df['model'].mode().empty else 'Unknown',
        'qr_code': df['qr_code'].mode().values[0] if not df['qr_code'].mode().empty else 'Unknown'
    }

    return metadata

def determine_season(month):
    """Assign a season based on the month."""
    if month in [12, 1, 2]:
        return 'Hot Dry (Dec-Feb)'
    elif month in [3, 4, 5]:
        return 'Long Rains (Mar-May)'
    elif month in [6, 7, 8]:
        return 'Cool Dry (Jun-Aug)'
    else:
        return 'Short Rains (Sep-Nov)'

def calculate_key_metrics(df):
    """Calculate key metrics for display."""
    recent_day_data = df[df['date'] == df['date'].max()]
    avg_liters_hour_recent_day = recent_day_data.groupby('hour')['liters'].mean().mean()

    last_7_days = df[df['date'] >= (df['date'].max() - pd.Timedelta(days=7))]
    avg_liters_hour_7_days = last_7_days.groupby('hour')['liters'].mean().mean()
    avg_liters_day_7_days = last_7_days.groupby('date')['liters'].sum().mean()

    est_beneficiaries = round(avg_liters_day_7_days / 15)

    return {
        "Avg Liters/Hour (Recent Day)": round(avg_liters_hour_recent_day),
        "Avg Liters/Hour (Last 7 Days)": round(avg_liters_hour_7_days),
        "Avg Liters/Day (Last 7 Days)": round(avg_liters_day_7_days),
        "Estimated Beneficiaries": est_beneficiaries
    }

def calculate_seasonal_averages(df):
    """Calculate average daily volume per season, excluding incomplete seasons."""
    season_data = df.groupby(['season', 'date'])['liters'].sum().reset_index()
    days_per_season = season_data.groupby('season')['date'].nunique()
    complete_seasons = days_per_season[days_per_season >= 85].index
    season_data = season_data[season_data['season'].isin(complete_seasons)]
    avg_volume_per_season = season_data.groupby('season')['liters'].mean().reset_index()
    avg_volume_per_season.rename(columns={'liters': 'avg_daily_volume'}, inplace=True)
    return avg_volume_per_season

def create_dashboard_layout(df, metadata, timezone_str, key_metrics, seasonal_averages):
    """Create the layout for the sensor dashboard."""
    return html.Div([
        html.H1(metadata['water_point_name'], style={'textAlign': 'center', 'fontFamily': 'Arial, sans-serif'}),

        # Combined Sensor Information, Map, and Key Metrics Section
        html.Div([
            html.Div([
                html.H2("Sensor Information", style={'fontFamily': 'Arial, sans-serif'}),
                *[html.P([html.B(f"{key.replace('_', ' ').title()}: "), str(value)], 
                          style={'margin': '5px', 'fontFamily': 'Arial, sans-serif'}) for key, value in metadata.items()]
            ], className="dashboard-section"),

            dcc.Graph(
                id='sensor-location',
                figure=px.scatter_mapbox(
                    df, lat='latitude', lon='longitude',
                    hover_name='community_name', zoom=10,
                    mapbox_style="open-street-map"
                ).update_layout(
                    margin=dict(l=0, r=0, t=0, b=0),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                ),
                style={'height': '300px', 'backgroundColor': 'transparent', 'padding-right': '15px'}

            ),

            html.Div([
                html.H2("Key Metrics", style={'fontFamily': 'Arial, sans-serif'}),
                *[html.P([html.B(label), f": {value}"], 
                          style={'margin': '5px', 'fontFamily': 'Arial, sans-serif'}) 
                  for label, value in key_metrics.items()]
            ], className="dashboard-section")
        ], className="dashboard-container"),  # Add class for responsive styling

        # Red Flag Events Warning Box
        html.Div([
            html.P(f"Last Reading: {df['local_datetime'].max()}", style={
                'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Arial, sans-serif'
            }),
            html.H4(f"Red Flag Events (Last 30 Days): {df[df['red_flag'] == 1].shape[0]}", style={
                'color': 'red', 'margin': '0', 'fontFamily': 'Arial, sans-serif'
            })
        ], style={
            'border': '1px solid red', 'border-radius': '10px', 'padding': '10px', 
            'backgroundColor': '#ffe6e6', 'margin-bottom': '20px', 'textAlign': 'center'
        }),

        # Daily Water Flow Plot
        dcc.Graph(
            id='daily-water-flow',
            figure=px.line(
                df.groupby('date')['liters'].sum().reset_index(), 
                x='date', y='liters', title='Daily Water Flow'
            ).update_traces(line_color='rgb(229, 142, 45)').update_layout(xaxis_showgrid=False)
        ),

        # Average Hourly Usage Plot
        dcc.Graph(
            id='hourly-usage-pattern',
            figure=px.bar(
                df.groupby('hour')['liters'].mean().reset_index(),
                x='hour', y='liters',
                title=f'Average Hourly Water Usage (Local Time: {timezone_str})',
                labels={'hour': 'Hour (Local Time)', 'liters': 'Water Flow (Liters)'}
            ).update_traces(marker_color='rgb(229, 142, 45)')
        ),

        # Usage vs Temperature Scatter Plot
        dcc.Graph(
            id='usage-vs-temperature',
            figure=px.scatter(
                df, x='temperature', y='liters',
                title='Water Usage vs Sensor Temperature',
                labels={'temperature': 'Temperature (°C)', 'liters': 'Water Flow (Liters)'}
            ).update_traces(marker=dict(color='rgb(229, 142, 45)')).update_layout(xaxis_showgrid=False)
        ),

        # Seasonal Usage Plot
        dcc.Graph(
            id='seasonal-usage',
            figure=px.bar(
                seasonal_averages, x='season', y='avg_daily_volume',
                title='Average Daily Water Usage per Season',
                labels={'season': 'Season', 'avg_daily_volume': 'Avg Daily Volume (Liters)'}
            ).update_traces(marker_color='rgb(229, 142, 45)')
        )
    ])

# Dash App Setup
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=['assets/style.css'])
server = app.server  # Flask app exposed for WSGI

def get_available_sensors():
    """List available sensor IDs based on file names."""
    files = [f for f in os.listdir(DATA_DIR) if f.startswith("sensor-") and f.endswith("-hourly-logs.csv")]
    return [f.split('-')[1] for f in files]

def get_sensor_metadata():
    """Retrieve metadata for all available sensors."""
    sensor_ids = get_available_sensors()
    metadata_list = []
    for sensor_id in sensor_ids:
        file_path = os.path.join(DATA_DIR, f"sensor-{sensor_id}-hourly-logs.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, nrows=2000)  # Read a limited number of rows for metadata
            metadata = extract_metadata(df)
            metadata['sensor_id'] = sensor_id  # Add sensor ID to metadata
            metadata_list.append(metadata)
    return metadata_list

# Login layout
def login_layout():
    return html.Div([
        html.H1("Sensor Dashboard Login", style={'textAlign': 'center', 'fontFamily': 'Arial, sans-serif'}),
        html.Div([
            dcc.Input(
                id="password-input",
                type="password",
                placeholder="Enter your password",
                style={
                    'width': '70%',  # Increased width
                    'height': '40px',  # Increased height
                    'margin': '10px auto',
                    'display': 'block',
                    'fontFamily': 'Arial, sans-serif',
                    'fontSize': '16px',  # Larger font
                    'padding': '5px'
                }
            ),
            html.Button(
                "Submit", 
                id="login-button", 
                n_clicks=0,
                style={'display': 'block', 'margin': '10px auto', 'fontSize': '16px', 'padding': '10px 20px'}
            ),
            html.Div(
                id="login-message", 
                style={'textAlign': 'center', 'color': 'red', 'fontFamily': 'Arial, sans-serif'}
            )
        ], style={'textAlign': 'center'})
    ])

# Landing Page Layout
def landing_page_layout():
    sensors = get_sensor_metadata()

    return html.Div([
        html.H1("Sensor Dashboard", style={'textAlign': 'center', 'fontFamily': 'Arial, sans-serif'}),

        # Center the dropdown while keeping text left-aligned
        html.Div([
            dcc.Dropdown(
                id='sensor-dropdown',
                options=[
                    {
                        'label': f"{sensor.get('water_point_name', 'Unknown')} (Sensor {sensor.get('sensor_id', 'Unknown')})", 
                        'value': sensor.get('sensor_id', 'Unknown')
                    }
                    for sensor in sensors
                ],
                placeholder="Select a sensor...",
                style={
                    'fontFamily': 'Arial, sans-serif',
                    'width': '80%',  # Adjust width as needed
                    'margin': '0 auto',  # Centers the dropdown control
                    'padding': '5px',  # Padding for aesthetics
                    'textAlign': 'left',  # Keeps the selected text left-aligned
                }
            ),
        dcc.Loading(  # Wrap the Go button in a loading spinner
                        id="loading-go",
                        type="circle",
                        children=html.Button(
                            "Go",
                            id="go-button",
                            n_clicks=0,
                            style={
                                'display': 'block', 
                                'margin': '10px auto',  # Center the button
                                'fontSize': '16px', 
                                'padding': '10px 20px'
                            },
                            disabled=True  # Initially disabled
                        )
                    )
                ], style={'textAlign': 'center', 'marginBottom': '20px'}),
            ])

@app.callback(
    Output("go-button", "disabled"),
    [Input("sensor-dropdown", "value")]
)
def enable_go_button(sensor_selection):
    return sensor_selection is None  # Disable if no sensor is selected

@app.callback(
    Output("url", "pathname"),
    [Input("go-button", "n_clicks")],  # Triggered by button clicks
    [State("sensor-dropdown", "value")],  # Get the selected sensor ID
    prevent_initial_call=True  # Only trigger after an actual click
)
def navigate_to_dashboard(n_clicks, sensor_id):
    if n_clicks and sensor_id:
        return f"/sensor/{sensor_id}"  # Navigate to the selected sensor's dashboard
    return "/"  # Fallback to home if no selection

# Main Layout
app.layout = html.Div([
    dcc.Store(id="auth-state", storage_type="session", data={"authenticated": False}),
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

@app.callback(
    [Output("auth-state", "data"), Output("login-message", "children")],
    [Input("login-button", "n_clicks"), Input("password-input", "n_submit")],  # Listen for Enter key with `n_submit`
    [State("password-input", "value"), State("auth-state", "data")]
)
def authenticate_user(n_clicks, n_submit, password, auth_state):
    """Authenticate user based on password input."""
    # Load passwords from the configuration file
    passwords = load_passwords(CONFIG_PATH)

    if (n_clicks or n_submit) and password in passwords:  # Check against list of passwords
        auth_state["authenticated"] = True
        return auth_state, ""
    elif n_clicks or n_submit:
        return auth_state, "Incorrect password. Please try again."
    return auth_state, ""

@app.callback(
    Output("page-content", "children"),
    [Input("auth-state", "data"), Input("url", "pathname")]
)
def render_page(auth_state, pathname):
    if not auth_state.get("authenticated", False):
        return login_layout()  # Show login page if not authenticated
    if pathname == "/":
        return landing_page_layout()
    elif pathname.startswith("/sensor/"):
        sensor_id = pathname.split("/")[-1]
        csv_file = os.path.join(DATA_DIR, f"sensor-{sensor_id}-hourly-logs.csv")
        if os.path.exists(csv_file):
            df, metadata, timezone_str = load_data(csv_file)
            key_metrics = calculate_key_metrics(df)
            seasonal_averages = calculate_seasonal_averages(df)
            return create_dashboard_layout(df, metadata, timezone_str, key_metrics, seasonal_averages)
    return html.Div([html.H2("404: Page not found")])

if __name__ == "__main__":
    app.run_server(debug=True)