import pandas as pd
import pytz
from timezonefinder import TimezoneFinder
import dash
from dash import dcc, html
import plotly.express as px
import argparse

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

def create_dashboard(csv_file):
    df, metadata, timezone_str = load_data(csv_file)
    key_metrics = calculate_key_metrics(df)
    seasonal_averages = calculate_seasonal_averages(df)

    app = dash.Dash(__name__)

    app.layout = html.Div([
        html.H1(metadata['water_point_name'], style={'textAlign': 'center', 'fontFamily': 'Arial, sans-serif'}),

        # Combined Sensor Information, Map, and Key Metrics Section
        html.Div([
            html.Div([
                html.H2("Sensor Information", style={'fontFamily': 'Arial, sans-serif'}),
                *[html.P([html.B(f"{key.replace('_', ' ').title()}: "), str(value)], 
                          style={'margin': '5px', 'fontFamily': 'Arial, sans-serif'}) for key, value in metadata.items()]
            ], style={'flex': '1', 'padding': '10px'}),

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
                style={'flex': '1', 'height': '300px', 'width': '100%', 'backgroundColor': 'transparent'}
            ),

            html.Div([
                html.H3("Key Metrics", style={'fontFamily': 'Arial, sans-serif'}),
                *[html.P([html.B(label), f": {value}"], 
                          style={'margin': '5px', 'fontFamily': 'Arial, sans-serif'}) 
                  for label, value in key_metrics.items()]
            ], style={'flex': '1', 'padding': '10px'})
        ], style={
            'display': 'flex', 'border': '1px solid #ddd', 'border-radius': '10px', 
            'padding': '20px', 'margin-bottom': '20px', 'backgroundColor': '#f9f9f9'
        }),
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
    ], style={'padding': '20px'})

    app.run_server(debug=True)

def main():
    parser = argparse.ArgumentParser(description="Create a dashboard for sensor data visualization.")
    parser.add_argument("-f", "--csv_file", required=True, help="Path to the CSV file")
    args = parser.parse_args()

    create_dashboard(args.csv_file)

if __name__ == "__main__":
    main()