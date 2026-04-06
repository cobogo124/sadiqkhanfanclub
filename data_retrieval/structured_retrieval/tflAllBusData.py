import requests
import json
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TFL_KEY = os.getenv("TFL_KEY")

def get_all_bus_data():
    output_dir = "downloads/bus_network"
    os.makedirs(output_dir, exist_ok=True)
    
    # headers for authentication
    params = {"app_key": TFL_KEY} if TFL_KEY else {}

    print("--- Starting TFL Data Extraction ---")
    lines_url = "https://api.tfl.gov.uk/Line/Mode/bus"
    
    try:
        response = requests.get(lines_url, params=params)
        response.raise_for_status()
        lines_data = response.json()
        
        # extract line IDs
        line_ids = [line['id'] for line in lines_data]
        total_lines = len(line_ids)
        print(f"Found {total_lines} bus lines. Starting stop-point extraction...")

        all_data = {}

        for index, line_id in enumerate(line_ids, 1):
            # ldog progress every 20 lines
            if index % 20 == 0 or index == total_lines:
                print(f"Processing: {index}/{total_lines} ({line_id})")
            
            stops_url = f"https://api.tfl.gov.uk/Line/{line_id}/StopPoints"
            
            try:
                stops_res = requests.get(stops_url, params=params)
                if stops_res.status_code == 200:
                    all_data[line_id] = stops_res.json()
                else:
                    print(f"  ! Warning: Could not fetch stops for {line_id} (Status: {stops_res.status_code})")
            except requests.exceptions.RequestException as e:
                print(f"  ! Connection error on line {line_id}: {e}")

            # rate limiter to prevent bad request code from TFL
            time.sleep(0.05)

        # Save the full structured dataset
        output_file = os.path.join(output_dir, "all_bus_stops.json")
        with open(output_file, "w", encoding='utf-8') as f:
            json.dump(all_data, f, indent=2)
        
        print(f"\nSuccess! Data for {len(all_data)} routes saved to: {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Critical API Error: {e}")

if __name__ == "__main__":
    get_all_bus_data()