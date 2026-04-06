import os
import json
import requests
from rdflib import Graph, RDF, RDFS, Literal
# Import the renamed TFL namespace from your colleague's script
from data_retrieval.unstructured_retrieval.triples_to_rdf import label_to_uri, TFL

CACHE_PATH = "downloads/tfl_api_cache.json"
OUTPUT_PATH = "ontologies/pipeline_output/structured_london_transport.ttl"

def fetch_or_load_data():
    """Loads from local JSON cache to ensure professor can run it offline."""
    if os.path.exists(CACHE_PATH):
        print(f"  -> Loading TfL data from local cache: {CACHE_PATH}")
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
            
    print("  -> Local cache not found. Fetching live TfL API data...")
    # Added overground and bus to the API request to cover all CQs
    modes = "tube,dlr,elizabeth-line,overground,bus"
    url = f"https://api.tfl.gov.uk/Line/Mode/{modes}/Route"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Fetch stop points for each line
        for line in data:
            stops_url = f"https://api.tfl.gov.uk/Line/{line['id']}/StopPoints"
            stops_res = requests.get(stops_url)
            if stops_res.status_code == 200:
                line['stop_points'] = stops_res.json()
            else:
                line['stop_points'] = []
                
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        return data
    except Exception as e:
        print(f"Failed to fetch TfL data: {e}")
        return []

def run():
    print("Running Structured Pipeline (TfL API)...")
    g = Graph()
    g.bind("tfl", TFL)
    
    data = fetch_or_load_data()
    
    for line in data:
        line_name = line.get('name', '')
        line_uri = label_to_uri(line_name)
        mode_name = line.get('modeName', '')
        
        # Map Line using Kamyar's specific subclasses
        if mode_name == 'tube':
            g.add((line_uri, RDF.type, TFL.UndergroundLine))
        elif mode_name == 'dlr':
            g.add((line_uri, RDF.type, TFL.DLRLine))
        elif mode_name == 'elizabeth-line':
            g.add((line_uri, RDF.type, TFL.ElizabethLineService))
        elif mode_name == 'overground':
            g.add((line_uri, RDF.type, TFL.OvergroundLine))
        elif mode_name == 'bus':
            g.add((line_uri, RDF.type, TFL.BusRoute))
        else:
            g.add((line_uri, RDF.type, TFL.TfLLine))
            
        g.add((line_uri, RDFS.label, Literal(line_name)))

        # Map Stops and Facilities
        for stop in line.get('stop_points', []):
            stop_name = stop.get('commonName', '')
            stop_uri = label_to_uri(stop_name)
            
            # Use TfLStation and servedByLine (Station -> Line direction)
            g.add((stop_uri, RDF.type, TFL.TfLStation))
            g.add((stop_uri, RDFS.label, Literal(stop_name)))
            g.add((stop_uri, TFL.servedByLine, line_uri)) 
            
            # Distinguish between Facilities and Accessibility Features
            for prop in stop.get('additionalProperties', []):
                val = str(prop.get('value', '')).lower()
                key = str(prop.get('key', ''))
                
                if val in ['true', 'yes']:
                    facility_uri = label_to_uri(key)
                    g.add((facility_uri, RDFS.label, Literal(key)))
                    
                    # Check if it's a facility (Toilet / Car Park)
                    if 'toilet' in key.lower() or 'car park' in key.lower():
                        g.add((stop_uri, TFL.hasFacility, facility_uri))
                        if 'toilet' in key.lower():
                            g.add((facility_uri, RDF.type, TFL.PublicToilet))
                        elif 'car park' in key.lower():
                            g.add((facility_uri, RDF.type, TFL.CarPark))
                            
                    # Otherwise it is an accessibility feature
                    else:
                        g.add((stop_uri, TFL.hasAccessibilityFeature, facility_uri))
                        if 'step free' in key.lower() or 'step-free' in key.lower():
                            g.add((facility_uri, RDF.type, TFL.StepFreeAccess))
                            g.add((stop_uri, TFL.hasStepFreeStreetToPlatform, Literal(True)))
                        elif 'audio' in key.lower() or 'visual' in key.lower():
                            g.add((facility_uri, RDF.type, TFL.AudioVisualAid))
                            
    print(f"  -> Structured Pipeline generated {len(g)} triples.")
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    g.serialize(destination=OUTPUT_PATH, format="turtle")
    print(f"  -> Saved structured intermediate file to: {OUTPUT_PATH}")
    
    return g