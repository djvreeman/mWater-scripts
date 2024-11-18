"""
search-mwater.py

This script is designed to interact with the mWater API to search for water points based on a given name or query. 
It performs the following key functions:

1. Reads a client ID (authentication token) from a specified file.
2. Uses the client ID to send a request to the mWater API to search for water points matching the specified query.
3. Outputs the results, including the names of the matching water points or any relevant error messages.

Script Features:
- Reads the client ID securely from a file to avoid hardcoding sensitive credentials.
- Performs a case-insensitive search using a regular expression (regex) filter on water point names.
- Limits the results to 10 for debugging purposes to avoid overwhelming output.
- Handles API errors gracefully and provides meaningful error messages for troubleshooting.
- Allows flexible configuration of the client ID file path through command-line arguments.

Usage:
1. Save your mWater API `client_id` in a file (default: `client_id.txt`).
2. Run the script using Python:
   python search-mwater.py --client-id-file <path_to_client_id_file>
   Replace `<path_to_client_id_file>` with the path to the file containing your `client_id`. 
   If not specified, the script defaults to using `client_id.txt`.

Example:
   python search-mwater.py --client-id-file /path/to/client_id.txt

Dependencies:
- Python 3.x
- Required libraries:
  - `requests` (for making HTTP requests to the mWater API)
  - `json` (for handling JSON data)
  - `argparse` (for parsing command-line arguments)

Error Handling:
- Handles `FileNotFoundError` if the specified client ID file does not exist.
- Handles API response errors (e.g., invalid client ID, network issues) and displays detailed error messages.
- Prints a message if no matching water points are found or if an unexpected error occurs.

Notes:
- The API endpoint (`https://api.mwater.co/v3/entities/water_point`) is currently configured to search for water points.
  This can be updated for other entity types as needed.
- Modify the `query_name` argument in the `search_sites` function call within `main()` to search for a different name.
- For production use, consider enhancing security by encrypting the `client_id` and/or using environment variables.
"""

import requests
import json
import argparse

# Function to read client_id from a file
def read_client_id(file_path):
    try:
        with open(file_path, 'r') as file:
            client_id = file.read().strip()
            print(f"Client ID read from file: {client_id}")
            return client_id
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return None

# Function to search for water points by name (e.g., "Kibimba") using the client_id
def search_sites(client_id, query_name):
    url = 'https://api.mwater.co/v3/entities/water_point'  # Update the entity type as needed

    headers = {
        'Authorization': f'Bearer {client_id}',
        'Content-Type': 'application/json'
    }

    # Add a filter to search for water points whose name contains "Kibimba"
    params = {
        'limit': 10,  # Limit the results for debugging
        'filter': json.dumps({
            'name': {
                '$regex': query_name,
                '$options': 'i'  # Case-insensitive search
            }
        })
    }

    try:
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            if data:
                print(f"Found {len(data)} water points matching '{query_name}' (limited to 10).")
                for site in data:
                    if 'name' in site:
                        print(f"Water Point Name: {site['name']}")
                    else:
                        print("Water point does not have a 'name' field.")
                        print("Here is the raw data for this water point:")
                        print(json.dumps(site, indent=4))
            else:
                print(f"No water points found matching '{query_name}'.")
        else:
            print(f"Failed to fetch data. Status Code: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# Main function to handle search
def main():
    # Command-line argument parsing
    parser = argparse.ArgumentParser(description="Search mWater sites by name")
    parser.add_argument('--client-id-file', type=str, default='client_id.txt',
                        help="Path to the file containing the client_id (default: 'client_id.txt')")
    args = parser.parse_args()

    # Step 1: Read the client_id from the file (either provided via command line or default file)
    client_id = read_client_id(args.client_id_file)

    if client_id:
        # Step 2: Use the client_id to search for water points matching "Kibimba"
        search_sites(client_id, "Kibimba")

# Run the main function
if __name__ == "__main__":
    main()