import requests
import json
import re
import argparse
import os

# Function to read client_id from a file
def read_client_id(file_path):
    try:
        with open(file_path, 'r') as file:
                client_id = file.read().strip()
                #print(f"Client ID read from file: {client_id}")
                return client_id
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return None

# Function to search for water points by ID or name and write the output to a file
def get_water_source_by_id(client_id, water_source_id, output_file, brief):
    output_file = os.path.join('output', f'{water_source_id}.json')

    url = f'https://api.mwater.co/v3/entities/water_point/{water_source_id}'
    headers = {
        'Authorization': f'Bearer {client_id}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data:
                if not os.path.exists('output'):
                    os.makedirs('output')

                with open(output_file, 'w') as f:

                    if brief:
                        brief_data = [{'_id': wp['_id'], 'name': wp['name']} for wp in data]
                        json.dump(brief_data, f, indent=4)
                    else:
                        json.dump(data, f, indent=4)
                        print(f"Data successfully written to '{output_file}'.")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        print(f"Failed to fetch data. Status Code: {response.status_code}")
        print(f"Response: {response.text}")

    
def search_flexible_sites(client_id, search_string, output_file, brief):
    cleaned_search_string = re.sub(r'[^a-zA-Z0-9]+', '-', search_string.lower().strip())
    output_file = os.path.join('output', f'{cleaned_search_string}.json')

    url = 'https://api.mwater.co/v3/entities/water_point'
    headers = {
        'Authorization': f'Bearer {client_id}',
        'Content-Type': 'application/json'
    }

    params = {
        'limit': 100,
        'filter': json.dumps({
            '$or': [
                {'name': {'$regex': search_string, '$options': 'i'}},
                {'desc': {'$regex': search_string, '$options': 'i'}}
            ]
        })
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
                data = response.json()
                if data:
                    if not os.path.exists('output'):
                        os.makedirs('output')

                    with open(output_file, 'w') as f:
                        # Handle brief output if specified
                            
                        if brief:
                            brief_data = [{'_id': wp['_id'], 'name': wp['name']} for wp in data]
                            json.dump(brief_data, f, indent=4)
                        else:
                            json.dump(data, f, indent=4)
                            print(f"Data successfully written to '{output_file}'.")

                else:
                    print(f"Failed to fetch data. Status Code: {response.status_code}")
                    print(f"Response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# Main function to handle search and output
def main():
    # Command-line argument parsing
    parser = argparse.ArgumentParser(description="Search mWater sites by name and output to a file")
    parser.add_argument('-c', '--config', type=str, default='client_id.txt',
                        help="Path to the file containing the client_id (default: 'client_id.txt')")
    parser.add_argument('-s', '--search-string', type=str, required=False,
                        help="String to search for in the water point names/descriptions")
    
    parser.add_argument('-id', '--water-source-id', type=str, help="Specify a water source ID to retrieve its data")
    parser.add_argument('-b'
    , '--brief', action='store_true',
                        help="Only output the name and _id of the water point")
    parser.add_argument('-o', '--output-file', type=str, default='output.json',
                        help="Path to the output file where the JSON data will be written (default: 'output.json')")
    args = parser.parse_args()

    # Step 1: Read the client_id from the file
    client_id = read_client_id(args.config)

    if client_id:
    
        # Step 2: Check if a water source ID is specified
        if args.water_source_id:
            if not os.path.exists('output'):
                os.makedirs('output')
            get_water_source_by_id(client_id, args.water_source_id, args.output_file, args.brief)
        elif args.search_string:
        
                if args.water_source_id:
                    get_water_source_by_id(client_id, args.water_source_id, args.output_file, args.brief)
            
                else:
                    # Use the client_id to search for water points by name and write the result        
                    search_flexible_sites(client_id, args.search_string, args.output_file, args.brief)

# Run the main function
if __name__ == "__main__":
    main()