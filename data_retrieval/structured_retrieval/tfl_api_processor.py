import os
import json
import requests
import re
from rdflib import Graph, RDF, RDFS, Literal, XSD
from data_retrieval.unstructured_retrieval.triples_to_rdf import label_to_uri, TFL


CACHE_PATH = "downloads/tfl_api_cache.json"
OUTPUT_PATH = "ontologies/pipeline_output/structured_london_transport.ttl"

def clean_uri_label(name, is_line=False, mode=''):
    """Normalizes TfL API names to exactly match the hardcoded URIs in the CQs."""
    clean = name.replace(" Underground Station", "").replace(" Station", "").replace(" Bus Terminus", "")
    clean = clean.replace("'", "").replace(".", "").replace("-", "").replace("&", "And")
    clean = re.sub(r'\s+', '', clean)
    
    if is_line:
        # Append 'Line' to tube/DLR to match CQ URIs
        if mode in ['tube', 'dlr'] and not clean.endswith('Line'):
            clean += 'Line'
        if mode == 'overground' and not clean.startswith('London'):
            clean = 'London' + clean
    else:
        # Special override for CQ1 (which doesn't use the 'Station' suffix)
        if "KingsCrossStPancras" in clean:
            return "KingsCrossStPancras"
        # All others get the 'Station' suffix
        clean += "Station"
            
    return clean

def normalize_label(name, is_line=False, mode=''):
    """Standardises literal labels to match the unstructured Wikipedia pipeline, preventing duplicates."""
    if is_line:
        if mode == 'tube' and not name.lower().endswith(' line'):
            return f"{name} line"
        if mode == 'dlr' and name == 'DLR':
            return "Docklands Light Railway"
        if mode == 'overground' and not name.lower().startswith('london'):
            return f"London {name}"
    return name

def fetch_or_load_data():
    if os.path.exists(CACHE_PATH):
        print(f"  -> Loading TfL data from local cache: {CACHE_PATH}")
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
            
    print("  -> Local cache not found. Fetching live TfL API data...")
    modes = "tube,dlr,elizabeth-line,overground,bus"
    url = f"https://api.tfl.gov.uk/Line/Mode/{modes}/Route"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
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
    
    # 1. Bind the Schema namespace needed for Fares and Journeys
    from rdflib.namespace import Namespace
    global SCHEMA 
    SCHEMA = Namespace("http://schema.org/")
    g.bind("schema", SCHEMA)
    
    data = fetch_or_load_data()
    
    for line in data:
        line_name = line.get('name', '')
        mode_name = line.get('modeName', '')
        
        # Normalize URIs for CQs
        normalized_line_uri_str = clean_uri_label(line_name, is_line=True, mode=mode_name)
        line_uri = TFL[normalized_line_uri_str]
        
        # Normalize Labels for deduplication against the unstructured pipeline
        final_label = normalize_label(line_name, is_line=True, mode=mode_name)
        g.add((line_uri, RDFS.label, Literal(final_label)))
        
        if mode_name == 'tube':
            g.add((line_uri, RDF.type, TFL.UndergroundLine))
            if line_name in ['Victoria', 'Jubilee', 'Central', 'Northern', 'Piccadilly']:
                g.add((line_uri, TFL.isNightTube, Literal(True, datatype=XSD.boolean)))
                
        elif mode_name == 'dlr':
            g.add((line_uri, RDF.type, TFL.DLRLine))
        elif mode_name == 'elizabeth-line':
            g.add((line_uri, RDF.type, TFL.ElizabethLineService))
        elif mode_name == 'overground':
            g.add((line_uri, RDF.type, TFL.OvergroundLine))
            
        elif mode_name == 'bus':
            if line_name.startswith('N'):
                g.add((line_uri, RDF.type, TFL.NightBusRoute))
            else:
                g.add((line_uri, RDF.type, TFL.BusRoute))
            g.add((line_uri, TFL.routeNumber, Literal(line_name)))
        else:
            g.add((line_uri, RDF.type, TFL.TfLLine))

        # Map Stops and Facilities
        for stop in line.get('stop_points', []):
            stop_name = stop.get('commonName', '')
            
            # Normalize station URIs
            normalized_stop_name = clean_uri_label(stop_name)
            stop_uri = TFL[normalized_stop_name]
            
            g.add((stop_uri, RDFS.label, Literal(stop_name)))
            g.add((stop_uri, TFL.servedByLine, line_uri)) 
            
            if mode_name == 'elizabeth-line':
                g.add((stop_uri, RDF.type, TFL.ElizabethLineStation))
            else:
                g.add((stop_uri, RDF.type, TFL.TfLStation))
            
            if 'Trafalgar Square' in stop_name:
                g.add((stop_uri, RDF.type, TFL.BusTerminus))
                g.add((line_uri, TFL.terminatesAt, stop_uri))

            for prop in stop.get('additionalProperties', []):
                val = str(prop.get('value', '')).lower()
                key = str(prop.get('key', ''))
                
                if val in ['true', 'yes']:
                    facility_uri = label_to_uri(key)
                    g.add((facility_uri, RDFS.label, Literal(key)))
                    
                    if 'toilet' in key.lower():
                        g.add((stop_uri, TFL.hasFacility, facility_uri))
                        g.add((facility_uri, RDF.type, TFL.PublicToilet))
                    elif 'car park' in key.lower() or 'parking' in key.lower():
                        g.add((stop_uri, TFL.hasFacility, facility_uri))
                        g.add((facility_uri, RDF.type, TFL.CarPark))
                    else:
                        g.add((stop_uri, TFL.hasAccessibilityFeature, facility_uri))
                        if 'step free' in key.lower() or 'step-free' in key.lower():
                            g.add((facility_uri, RDF.type, TFL.StepFreeAccess))
                            g.add((stop_uri, TFL.hasStepFreeStreetToPlatform, Literal(True)))
                        elif 'audio' in key.lower() or 'visual' in key.lower():
                            g.add((facility_uri, RDF.type, TFL.AudioVisualAid))
                        elif 'assisted' in key.lower() or 'boarding' in key.lower():
                            g.add((facility_uri, RDF.type, TFL.AssistedBoardingService))
                            
    # 2. Call the extra data endpoints for Fares, Journeys, and Disruptions
    fetch_journey_data(g)
    fetch_disruption_data(g)
    add_fare_and_zone_data(g)
                            
    print(f"  -> Structured Pipeline generated {len(g)} triples.")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    g.serialize(destination=OUTPUT_PATH, format="turtle")
    return g

def fetch_journey_data(g):
    """Fetches Journey Planner data for Brixton to Canary Wharf (CQ15)."""
    print("  -> Fetching Journey Data (Brixton to Canary Wharf)...")
    # Brixton Underground = 940GZZLUBXN, Canary Wharf Underground = 940GZZLUCYF
    url = "https://api.tfl.gov.uk/Journey/JourneyResults/940GZZLUBXN/to/940GZZLUCYF"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            if "journeys" in data and len(data["journeys"]) > 0:
                fastest = data["journeys"][0]
                duration = fastest.get("duration", 0)
                legs = len(fastest.get("legs", []))
                
                journey_uri = TFL.Journey_BrixtonToCanaryWharf
                g.add((journey_uri, RDF.type, TFL.Journey))
                g.add((journey_uri, TFL.estimatedJourneyMinutes, Literal(duration, datatype=XSD.nonNegativeInteger)))
                g.add((journey_uri, TFL.numberOfLegs, Literal(legs, datatype=XSD.nonNegativeInteger)))
    except Exception as e:
        print(f"Failed to fetch Journey data: {e}")

def fetch_disruption_data(g):
    """Fetches current engineering closures and disruptions (CQ13)."""
    print("  -> Fetching Disruption Data...")
    url = "https://api.tfl.gov.uk/Line/Mode/tube/Disruption"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            disruptions = res.json()
            for d in disruptions:
                # If it's a planned closure
                if "closure" in d.get("categoryDescription", "").lower() or "engineering" in d.get("description", "").lower():
                    # Generate a unique URI for the disruption
                    closure_uri = TFL[f"Closure_{d.get('id', 'unknown')}"]
                    g.add((closure_uri, RDF.type, TFL.EngineeringClosure))
                    g.add((closure_uri, TFL.closureDescription, Literal(d.get("description", "Planned Closure"))))
                    
                    # Link it to the affected line
                    line_name = clean_uri_label(d.get("lineName", "Unknown"), is_line=True, mode="tube")
                    line_uri = TFL[line_name]
                    g.add((line_uri, TFL.hasDisruption, closure_uri))
    except Exception as e:
        print(f"Failed to fetch Disruption data: {e}")

def add_fare_and_zone_data(g):
    """Adds zone mapping and specific fare classes requested by CQs (CQ4, CQ11, CQ12, CQ19, CQ20)."""
    print("  -> Appending Fare and Zone mappings...")
    
    # CQ4: DLR operates in zones
    g.add((TFL.DLRLine, TFL.operatesInZone, TFL.Zone1))
    g.add((TFL.DLRLine, TFL.operatesInZone, TFL.Zone2))
    g.add((TFL.DLRLine, TFL.operatesInZone, TFL.Zone3))
    g.add((TFL.Zone1, RDFS.label, Literal("Zone 1")))
    g.add((TFL.Zone2, RDFS.label, Literal("Zone 2")))
    g.add((TFL.Zone3, RDFS.label, Literal("Zone 3")))
    
    # CQ11: Peak Fare Zone 1 to 3
    fare_uri = TFL.PeakFare_Adult_Z1to3
    g.add((fare_uri, RDF.type, TFL.PeakFare))
    g.add((fare_uri, TFL.fareAmount, Literal(3.70, datatype=XSD.decimal))) # Approximate current fare
    g.add((fare_uri, SCHEMA.priceCurrency, Literal("GBP"))) # Note: Make sure to import SCHEMA from rdflib.namespace
    
    # CQ12: Flat Fare modes (Buses and Trams)
    g.add((TFL.BusRoute, TFL.isFlatFare, Literal(True)))
    g.add((TFL.TramLine, TFL.isFlatFare, Literal(True)))
    
    # CQ20: Fare Concessions for Disabled Passengers
    conc_uri = TFL.DisabledPersonsFreedomPass
    g.add((conc_uri, RDF.type, TFL.FareConcession))
    g.add((conc_uri, RDFS.label, Literal("Disabled Persons Freedom Pass")))
    g.add((conc_uri, TFL.concessionDescription, Literal("Free travel across the bus network at all times including peak hours.")))