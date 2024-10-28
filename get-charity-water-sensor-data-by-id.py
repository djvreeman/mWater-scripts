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
    filename = f"sensor-{qr_code}-hourly-logs-start-{safe_datetime}.csv"
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