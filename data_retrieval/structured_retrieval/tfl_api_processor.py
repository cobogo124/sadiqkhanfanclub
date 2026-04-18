import os
import json
import requests
import re
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
    g = Graph()
    g.bind("tfl", TFL)
    g.bind("schema", SCHEMA)
    
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f: data = json.load(f)
    else:
        url = "https://api.tfl.gov.uk/Line/Mode/tube,dlr,overground,elizabeth-line,bus/Route"
        data = requests.get(url).json()
        for line in data:
            s_res = requests.get(f"https://api.tfl.gov.uk/Line/{line['id']}/StopPoints")
            line['stop_points'] = s_res.json() if s_res.status_code == 200 else []
        with open(CACHE_PATH, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

    for line in data:
        line_name, mode_name = line.get('name'), line.get('modeName')
        line_uri = generate_cleaned_uri(line_name, "Line" if mode_name in ['tube', 'dlr'] else "")
        g.add((line_uri, RDFS.label, Literal(line_name)))
        
        # Priority 3: Operator Resolution (CQ8 & CQ14)
        if mode_name == 'dlr':
            op = TFL.KeolisAmeyDocklands
            g.add((op, RDF.type, TFL.TfLOperator))
            g.add((op, RDFS.label, Literal("KeolisAmey Docklands")))
            g.add((line_uri, TFL.operatedBy, op))
        elif mode_name == 'overground':
            op = TFL.ArrivaRailLondon
            g.add((op, RDF.type, TFL.TfLOperator))
            g.add((op, RDFS.label, Literal("Arriva Rail London")))
            g.add((line_uri, TFL.operatedBy, op))

        # CQ9: Bus Terminus
        if mode_name == 'bus' and line.get('stop_points'):
            if any("Trafalgar Square" in s.get('commonName', '') for s in line['stop_points']):
                g.add((line_uri, TFL.terminatesAt, TFL.TrafalgarSquareBusTerminus))

        for stop in line.get('stop_points', []):
            stop_name = stop.get('commonName', '')
            stop_uri = generate_cleaned_uri(stop_name, "Station")
            g.add((stop_uri, TFL.servedByLine, line_uri))
            
            for prop in stop.get('additionalProperties', []):
                key, val = str(prop.get('key', '')).lower(), str(prop.get('value', '')).lower()
                if 'toilet' in key and val != 'no':
                    t = TFL[f"Toilet_{slugify(stop_name)}"]
                    g.add((stop_uri, TFL.hasFacility, t))
                    g.add((t, RDF.type, TFL.PublicToilet))
                    g.add((t, RDFS.label, Literal("Public Toilet")))

    g.serialize(destination=OUTPUT_PATH, format="turtle")
    return g