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