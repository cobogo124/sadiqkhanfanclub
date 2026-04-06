import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()
TFL_KEY = os.getenv("TFL_KEY")

def get_tube_network_data():
    output_dir = "downloads/tube_network"
    os.makedirs(output_dir, exist_ok=True)
    
    params = {"app_key": TFL_KEY} if TFL_KEY else {}

    # distinction between tube, dlr, elizabeth-line and overground
    modes = "tube,dlr,elizabeth-line"
    lines_url = f"https://api.tfl.gov.uk/Line/Mode/{modes}"
    
    try:
        print(f"Fetching line IDs for modes: {modes}...")
        response = requests.get(lines_url, params=params)
        response.raise_for_status()
        lines_data = response.json()
        
        line_ids = [line['id'] for line in lines_data]
        all_tube_data = {}

        # fetch ordered stations and the geographic 'line strings'
        for line_id in line_ids:
            print(f"Processing route sequence for: {line_id}")
            
            # endpoint for Rail than the generic /StopPoints one
            sequence_url = f"https://api.tfl.gov.uk/Line/{line_id}/Route/Sequence/all"
            
            res = requests.get(sequence_url, params=params)
            if res.status_code == 200:
                all_tube_data[line_id] = res.json()
            else:
                print(f"  ! Failed to get sequence for {line_id}")
            
            time.sleep(0.1)

        # Save the data
        output_file = os.path.join(output_dir, "tube_sequences.json")
        with open(output_file, "w", encoding='utf-8') as f:
            json.dump(all_tube_data, f, indent=2)
            
        print(f"\nSuccess! Tube network data saved to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_tube_network_data()