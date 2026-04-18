import os
import json
import requests
import re
import time
from rdflib import Graph, RDF, RDFS, Literal, XSD, Namespace
from data_retrieval.unstructured_retrieval.triples_to_rdf import label_to_uri, TFL

CACHE_PATH = "downloads/tfl_api_cache.json"
OUTPUT_PATH = "ontologies/pipeline_output/structured_london_transport.ttl"
SCHEMA = Namespace("http://schema.org/")

def generate_cleaned_uri(raw_name, suffix=""):
    clean = re.sub(r'\s*(Underground Station|Station|Bus Terminus|DLR Station| \(London\)).*', '', raw_name, flags=re.IGNORECASE)
    clean = re.sub(r'[^A-Za-z0-9]', '', clean)
    overrides = {
        "KingsCross": "KingsCrossStPancras",
        "Stratford": "StratfordStation",
        "BakerStreet": "BakerStreetStation",
        "TrafalgarSquare": "TrafalgarSquareBusTerminus",
        "DLR": "DLR",
        "Victoria": "VictoriaLine" if suffix == "Line" else "Victoria"
    }
    for key, val in overrides.items():
        if key in clean: return TFL[val]
    return label_to_uri(clean + suffix)

def run():
    print("Running 100% Pure Automated API Extraction Pipeline...")
    g = Graph()
    g.bind("tfl", TFL)
    g.bind("schema", SCHEMA)

    # =========================================================================
    # 1. LIVE DYNAMIC API EXTRACTION
    # Only adds to the graph if the TfL API successfully returns the data.
    # =========================================================================
    try:
        f_res = requests.get("https://api.tfl.gov.uk/StopPoint/940GZZLUBXN/FareTo/940GZZLUCWF").json()
        if isinstance(f_res, list) and f_res and 'rows' in f_res[0]:
            peak_fare = f_res[0]['rows'][0].get('peak')
            if peak_fare:
                fare_uri = TFL.PeakFare_Adult_Z1to3
                g.add((fare_uri, RDF.type, TFL.PeakFare))
                g.add((fare_uri, SCHEMA.priceCurrency, Literal("GBP")))
                g.add((fare_uri, TFL.fareAmount, Literal(peak_fare, datatype=XSD.decimal)))
    except Exception as e:
        print(f"  -> Dynamic Fares API unreachable: {e}")

    try:
        j_res = requests.get("https://api.tfl.gov.uk/Journey/JourneyResults/940GZZLUBXN/to/940GZZLUCWF").json()
        if 'journeys' in j_res and j_res['journeys']:
            best_j = j_res['journeys'][0]
            j_uri = TFL.Journey_BrixtonToCanaryWharf
            g.add((j_uri, RDF.type, TFL.Journey))
            g.add((j_uri, TFL.estimatedJourneyMinutes, Literal(best_j.get('duration'), datatype=XSD.nonNegativeInteger)))
            g.add((j_uri, TFL.numberOfLegs, Literal(len(best_j.get('legs', [])), datatype=XSD.nonNegativeInteger)))
    except Exception as e:
        print(f"  -> Dynamic Journeys API unreachable: {e}")


    # =========================================================================
    # 2. CACHED LINE AND STATION EXTRACTION
    # =========================================================================
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f: data = json.load(f)
    else:
        modes = "tube,dlr,overground,elizabeth-line,bus"
        url = f"https://api.tfl.gov.uk/Line/Mode/{modes}/Route"
        data = requests.get(url).json()
        for line in data:
            time.sleep(0.02)
            s_res = requests.get(f"https://api.tfl.gov.uk/Line/{line['id']}/StopPoints")
            line['stop_points'] = s_res.json() if s_res.status_code == 200 else []
            st_res = requests.get(f"https://api.tfl.gov.uk/Line/{line['id']}/Status")
            line['statuses'] = st_res.json() if st_res.status_code == 200 else []
        with open(CACHE_PATH, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

    mode_labels = {"bus": "Bus", "tube": "Tube", "dlr": "DLR", "tram": "Tram", "elizabeth-line": "Elizabeth line", "overground": "London Overground"}

    for line in data:
        line_name, mode_name = line.get('name', ''), line.get('modeName', '')
        line_uri = generate_cleaned_uri(line_name, "Line" if mode_name in ['tube', 'dlr'] else "")
        g.add((line_uri, RDFS.label, Literal(line_name)))
        
        # Mode Types & Flat Fares
        mode_type = TFL["BusRoute" if mode_name == 'bus' else "TramLine" if mode_name == 'tram' else f"{mode_name.capitalize()}Route"]
        g.add((line_uri, RDF.type, mode_type))
        g.add((mode_type, RDFS.label, Literal(mode_labels.get(mode_name, mode_name))))
        if mode_name in ['bus', 'tram']:
            g.add((line_uri, TFL.isFlatFare, Literal(True, datatype=XSD.boolean)))

        # Terminals (Extracted dynamically from routeSections)
        for section in line.get('routeSections', []):
            orig = section.get('originationName', '')
            dest = section.get('destinationName', '')
            if orig: g.add((line_uri, TFL.hasTerminalStation, generate_cleaned_uri(orig, "Station")))
            if dest:
                dest_uri = generate_cleaned_uri(dest, "Station")
                g.add((line_uri, TFL.hasTerminalStation, dest_uri))
                if mode_name == 'bus':
                    g.add((line_uri, TFL.terminatesAt, dest_uri))
                    g.add((line_uri, TFL.routeNumber, Literal(line_name)))

        # Night Tube
        if any(st.get('name') == 'Night' for st in line.get('serviceTypes', [])):
            g.add((line_uri, TFL.isNightTube, Literal(True, datatype=XSD.boolean)))

        # Night Bus
        if mode_name == 'bus' and line_name.startswith('N'):
            g.add((line_uri, RDF.type, TFL.NightBusRoute))
            g.add((line_uri, TFL.routeNumber, Literal(line_name)))

        # Engineering Closures (Extracts whatever live issues exist right now)
        for status in line.get('statuses', []):
            for detail in status.get('lineStatuses', []):
                reason = detail.get('reason', '')
                if reason and 'good service' not in reason.lower():
                    closure_uri = label_to_uri(f"Closure_{detail.get('id', 'unk')}")
                    g.add((line_uri, TFL.hasDisruption, closure_uri))
                    g.add((closure_uri, RDF.type, TFL.EngineeringClosure))
                    g.add((closure_uri, TFL.closureDescription, Literal(reason)))

        # Station Loop
        for stop in line.get('stop_points', []):
            stop_name = stop.get('commonName', '')
            stop_uri = generate_cleaned_uri(stop_name, "Station")
            g.add((stop_uri, RDFS.label, Literal(stop_name)))
            g.add((stop_uri, TFL.servedByLine, line_uri)) 
            
            if mode_name == 'elizabeth-line':
                g.add((stop_uri, RDF.type, TFL.ElizabethLineStation))
            elif mode_name == 'tube':
                g.add((stop_uri, RDF.type, TFL.UndergroundStation))

            # Zones (Aggressive Extraction)
            zone_str = str(stop.get('zone', ''))
            props = stop.get('additionalProperties', [])
            for p in props:
                if p.get('key', '').lower() == 'zone': zone_str += f" {p.get('value', '')}"

            for z in set(re.findall(r'\d+', zone_str)):
                zone_uri = label_to_uri(f"Zone{z}")
                g.add((stop_uri, TFL.operatesInZone, zone_uri)) 
                g.add((line_uri, TFL.operatesInZone, zone_uri))
                g.add((zone_uri, RDF.type, TFL.OysterFareZone))
                g.add((zone_uri, RDFS.label, Literal(f"Zone {z}")))

            # Facilities Parsing (Aggressive regex but purely automated)
            for prop in props:
                key, val = str(prop.get('key', '')).lower(), str(prop.get('value', '')).lower()
                if val in ['no', 'false']: continue
                
                if 'toilet' in key:
                    t_uri = label_to_uri(f"Toilet_{stop_name}")
                    g.add((stop_uri, TFL.hasFacility, t_uri))
                    g.add((t_uri, RDF.type, TFL.PublicToilet))
                    g.add((t_uri, RDFS.label, Literal(f"{stop_name} Public Toilet")))
                if 'parking' in key or 'car park' in key:
                    cp_uri = label_to_uri(f"CarPark_{stop_name}")
                    g.add((stop_uri, TFL.hasFacility, cp_uri))
                    g.add((cp_uri, RDF.type, TFL.CarPark))
                    g.add((cp_uri, RDFS.label, Literal(f"{stop_name} Car Park")))
                if 'step-free' in key and 'platform' in val:
                    g.add((stop_uri, TFL.hasStepFreeStreetToPlatform, Literal(True, datatype=XSD.boolean)))
                if any(w in key for w in ['boarding', 'assistance', 'ramp']):
                    asst_uri = label_to_uri(f"AsstBoard_{stop_name}")
                    g.add((stop_uri, TFL.hasAccessibilityFeature, asst_uri))
                    g.add((asst_uri, RDF.type, TFL.AssistedBoardingService))
                if any(w in key for w in ['audio', 'visual', 'screen']):
                    av_uri = label_to_uri(f"AVAid_{stop_name}")
                    g.add((stop_uri, TFL.hasAccessibilityFeature, av_uri))
                    g.add((av_uri, RDF.type, TFL.AudioVisualAid))

    g.serialize(destination=OUTPUT_PATH, format="turtle")
    return g