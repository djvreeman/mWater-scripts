"""
Script Name: get-charity-water-sensor-data-by-id.py

Purpose:
This script fetches hourly sensor data from the charity: water API for a specified sensor identified by its QR code. 
The data is fetched starting from a given datetime, paginated as needed, and saved into a CSV file. 

Functionality:
1. Loads API credentials (API key and client ID) from a JSON configuration file.
2. Constructs the appropriate API request based on the QR code and start datetime.
3. Iterates through paginated responses to collect all data.
4. Saves the data to a CSV file in a specified directory.

Usage:
Run the script from the command line with the following required arguments:
    -q, --qr_code: The QR code of the sensor to fetch data for.
    -s, --start_datetime: The start datetime for data collection in the format 'YYYY-MM-DD HH:MM:SS'.
    -d, --output_dir: The directory where the resulting CSV file will be saved.

Example:
    python get-charity-water-sensor-data-by-id.py -q 910401 -s "2024-01-01 00:00:01" -d "./output"

Inputs:
- JSON Configuration File (config/charity-water-config.json): Contains the API key and client ID required for authentication.
- Command-line arguments:
  - QR code of the sensor
  - Start datetime
  - Output directory

Outputs:
- CSV File: Contains all the fetched hourly logs for the sensor, saved with a descriptive filename that includes the QR code and start datetime.

Dependencies:
- Python 3.x
- Libraries: requests, pandas, argparse, os, json, datetime

Author: Daniel J. Vreeman, PT, DPT, MS, FACMI, FIAHSI

Notes:
- Ensure the configuration file is present at the specified path and contains valid API credentials.
- Make sure the output directory exists before running the script.
"""

import requests
import pandas as pd
import json
import os
import argparse
from datetime import datetime

def load_config(config_file):
    """Load configuration from a JSON file."""
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file '{config_file}' not found.")
    with open(config_file, 'r') as file:
        config = json.load(file)
    return config.get("api_key"), config.get("client_id")

def construct_output_file(output_dir, qr_code, start_datetime):
    """Construct the output file name."""
    # Replace characters that are not suitable for file names
    safe_datetime = start_datetime.replace(":", "-").replace(" ", "-")
    #filename = f"sensor-{qr_code}-hourly-logs-start-{safe_datetime}.csv"
    filename = f"sensor-{qr_code}-hourly-logs.csv"
    return os.path.join(output_dir, filename)

def fetch_sensor_data(api_key, client_id, qr_code, start_datetime, output_file):
    base_url = "https://api-charitywater.org/v1/hourly-logs"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    params = {
        "clientId": client_id,
        "qrCode": qr_code,
        "startDatetime": start_datetime,
        "page": 1
    }

    all_logs = []

    while True:
        response = requests.get(base_url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break

        data = response.json()
        logs = data.get("hourly_logs", [])
        all_logs.extend(logs)

        next_page = data.get("next_page_number")
        if not next_page:
            break
        params["page"] = next_page

    if all_logs:
        df = pd.DataFrame(all_logs)
        df.to_csv(output_file, index=False)
        print(f"Data saved to {output_file}")
    else:
        print("No data found.")

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Fetch sensor data from charity: water API.")
    parser.add_argument("-q", "--qr_code", required=True, help="QR code of the sensor")
    parser.add_argument("-s", "--start_datetime", required=True, help="Start datetime in 'YYYY-MM-DD HH:MM:SS' format")
    parser.add_argument("-d", "--output_dir", required=True, help="Directory to save the output CSV file")
    args = parser.parse_args()

    # Validate the output directory
    if not os.path.isdir(args.output_dir):
        print(f"Error: The directory '{args.output_dir}' does not exist.")
        exit(1)

    # Load API credentials from the config file
    config_file = "config/charity-water-config.json"
    try:
        api_key, client_id = load_config(config_file)
    except Exception as e:
        print(e)
        exit(1)

    # Construct the output file path
    output_file = construct_output_file(args.output_dir, args.qr_code, args.start_datetime)

    # Fetch and save sensor data
    fetch_sensor_data(api_key, client_id, args.qr_code, args.start_datetime, output_file)

if __name__ == "__main__":
    main()