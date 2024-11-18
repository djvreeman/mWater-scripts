import requests
import os
import argparse
import urllib.parse

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

# Function to fetch water point details by ID and download images
def download_images(client_id, water_point_id, download_folder):
    # Properly encode the filter parameter
    filter_param = urllib.parse.quote(f'{{"meter_id":"{water_point_id}"}}')
    url = f'https://api.mwater.co/v3/entities/water_point?filter={filter_param}'
    
    headers = {
        'Authorization': f'Bearer {client_id}',
        'Content-Type': 'application/json'
    }

    try:
        # Fetch water point details
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            #print(data)

            # Check if data is a non-empty list
            if isinstance(data, list) and len(data) > 0:
                # Access the first element of the list
                water_point = data[0]
                
                # Check if 'photos' key exists in the water_point dictionary
                if 'photos' in water_point:
                    photos = water_point['photos']
                    
                    # Ensure the photos list is not empty
                    if photos:
                        print(f"Found {len(photos)} photos for water point {water_point_id}.")
                        
                        # Create the download folder if it doesn't exist
                        if not os.path.exists(download_folder):
                            os.makedirs(download_folder)

                        # Download each photo
                        for idx, photo in enumerate(photos, start=1):
                            photo_id = photo['id']
                            photo_url = f'https://api.mwater.co/v3/images/{photo_id}'
                            photo_path = os.path.join(download_folder, f"{water_point_id}-{idx}.jpg")

                            # Download and save the image
                            photo_response = requests.get(photo_url)
                            if photo_response.status_code == 200:
                                with open(photo_path, 'wb') as f:
                                    f.write(photo_response.content)
                                print(f"Downloaded image {idx} to {photo_path}")
                            else:
                                print(f"Failed to download image {idx}. Status Code: {photo_response.status_code}")
                    else:
                        print(f"No photos found for water point {water_point_id}.")
                else:
                    print(f"No 'photos' key found for water point {water_point_id}.")
            else:
                print(f"No valid data returned for water point {water_point_id}.")
        else:
            print(f"Failed to fetch water point details. Status Code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# Main function to handle arguments and trigger image download
def main():
    # Command-line argument parsing
    parser = argparse.ArgumentParser(description="Download images for a given water point ID")
    parser.add_argument('-c', '--config', type=str, default='config/client_id.txt',
                        help="Path to the file containing the client_id (default: 'client_id.txt')")
    parser.add_argument('-id', '--water-point-id', type=str, required=True,
                        help="ID of the water point to download images for")
    parser.add_argument('-o', '--output-folder', type=str, default='output/images/',
                        help="Folder to save the downloaded images (default: 'output/images/')")
    args = parser.parse_args()

    # Step 1: Read the client_id from the file
    client_id = read_client_id(args.config)

    if client_id:
        # Step 2: Download images for the specified water point ID
        download_images(client_id, args.water_point_id, args.output_folder)

# Run the main function
if __name__ == "__main__":
    main()