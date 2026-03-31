import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()
TFL_KEY = os.getenv("TFL_KEY")

def get_all_bus_data():
    output_dir = "downloads/bus_network"
    os.makedirs(output_dir, exist_ok=True)
    
    print("Fetching all active bus line IDs...")
    # Endpoint for all lines of a specific mode
    lines_url = "https://api.tfl.gov.uk/Line/Mode/bus"
    
    try:
        response = requests.get(lines_url)
        response.raise_for_status()
        lines_data = response.json()
        
        # xxtract just the line IDs
        line_ids = [line['id'] for line in lines_data]
        print(f"Found {len(line_ids)} bus lines. Starting stop-point extraction...")

        all_data = {}

        # iterate through every line to find its stops
        for index, line_id in enumerate(line_ids):
            if index % 20 == 0:
                print(f"Processing line {index}/{len(line_ids)}: {line_id}")
            
            stops_url = f"https://api.tfl.gov.uk/Line/{line_id}/StopPoints"
            stops_res = requests.get(stops_url)
            
            if stops_res.status_code == 200:
                all_data[line_id] = stops_res.json()
            else:
                print(f"Warning: Could not fetch stops for line {line_id}")

            # small sleep to prevent being blocked by TFL
            time.sleep(0.1)

        # save the full structured dataset for the mapping pipeline
        output_file = os.path.join(output_dir, "all_bus_stops.json")
        with open(output_file, "w") as f:
            json.dump(all_data, f, indent=2)
        
        print(f"Success! Data for {len(all_data)} routes saved to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")

if __name__ == "__main__":
    get_all_bus_data()