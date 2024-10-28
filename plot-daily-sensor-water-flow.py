import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os

def plot_daily_water_flow(csv_file):
    """Load CSV data, calculate daily water flow, and plot it."""
    # Load the CSV data
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: The file '{csv_file}' was not found.")
        exit(1)

    # Ensure the necessary columns are present
    required_columns = {'gmt_datetime', 'liters', 'water_point_name', 'qr_code', 'service_provider'}
    if not required_columns.issubset(df.columns):
        print(f"Error: The CSV file must contain the following columns: {required_columns}")
        exit(1)

    # Convert 'gmt_datetime' to datetime type and extract the date
    df['gmt_datetime'] = pd.to_datetime(df['gmt_datetime'])
    df['date'] = df['gmt_datetime'].dt.date

    # Calculate daily water flow (sum of liters by day)
    daily_flow = df.groupby('date')['liters'].sum().reset_index()

    # Extract metadata for labeling the plot
    water_point_name = df['water_point_name'].iloc[0]
    qr_code = df['qr_code'].iloc[0]
    service_provider = df['service_provider'].iloc[0]

    # Plot the data without vertical grid lines
    plt.figure(figsize=(10, 6))
    plt.plot(daily_flow['date'], daily_flow['liters'], marker='o', linestyle='-', markersize=5)

    # Add labels and title
    plt.title(
        f'Daily Water Flow for {water_point_name} (Sensor ID: {qr_code})\n'
        f'Service Provider: {service_provider}', 
        fontsize=14
    )
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Water Flow (Liters)', fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(axis='y')  # Only horizontal grid lines

    # Construct output PNG file path in the same directory as the input CSV
    csv_dir = os.path.dirname(csv_file)
    output_image = os.path.join(csv_dir, f"daily-water-flow-{qr_code}.png")

    # Save the plot as a PNG image
    plt.tight_layout()
    plt.savefig(output_image)
    print(f"Plot saved as '{output_image}'")

    # Show the plot
    plt.show()

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Visualize daily water flow from a CSV file.")
    parser.add_argument(
        "-f", "--csv_file", required=True, help="Path to the CSV file containing sensor data"
    )
    args = parser.parse_args()

    # Validate the CSV file path
    if not os.path.isfile(args.csv_file):
        print(f"Error: The file '{args.csv_file}' does not exist.")
        exit(1)

    # Generate the plot
    plot_daily_water_flow(args.csv_file)

if __name__ == "__main__":
    main()