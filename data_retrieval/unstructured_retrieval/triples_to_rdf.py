import json
import os
import re
from datetime import date
from rdflib import Graph, Literal, Namespace, RDF, RDFS, XSD, URIRef
from rdflib.namespace import DCTERMS

TFL = Namespace("http://example.org/tfl#")
PROV = Namespace("http://www.w3.org/ns/prov#")

# Priority 1: Align emitted classes with the generated ontology
LABEL_CLASS_MAP = {
    "ORG":     TFL.TfLOperator,      # TransportOperator -> TfLOperator
    "FAC":     TFL.TfLStation,       # TransitStop -> TfLStation
    "GPE":     TFL.TfLStation,       # Location -> TfLStation (Contextual)
    "LOC":     TFL.TfLStation,       
    "PRODUCT": TFL.TfLLine,          # TransportService -> TfLLine
    "EVENT":   TFL.ServiceDisruption # TransportEvent -> ServiceDisruption
}

# Known tube lines for Night Tube validation
TUBE_LINES = {
    TFL.BakerlooLine, TFL.CentralLine, TFL.CircleLine, TFL.DistrictLine,
    TFL.HammersmithCityLine, TFL.JubileeLine, TFL.MetropolitanLine,
    TFL.NorthernLine, TFL.PiccadillyLine, TFL.VictoriaLine,
    TFL.WaterlooAndCityLine, TFL.ElizabethLineRoute, TFL.DLR, 
    TFL.LondonOverground, TFL.Tramlink,
}

PREDICATE_MAP = {
    "hasstop": TFL.hasStop,
    "hasterminus": TFL.hasTerminus,
    "operatedby": TFL.operatedBy,
    "connectsto": TFL.connectsTo,
    "infarezone": TFL.operatesInZone,
    "operatesinzone": TFL.operatesInZone,
    "servedby": TFL.servedByLine,
    "servedbyline": TFL.servedByLine,
    "isnighttube": TFL.isNightTube,
    "isflatfare": TFL.isFlatFare,
    "hasfacility": TFL.hasFacility,
    "routenumber": TFL.routeNumber,
    "isstepfree": TFL.hasStepFreeStreetToPlatform,
    "hasstepfreeaccess": TFL.hasStepFreeStreetToPlatform,
    "hasaccessibilityfeature": TFL.hasAccessibilityFeature,
    "fareamount": TFL.fareAmount,
    "openedin": TFL.openedDate,
    "acceptedon": TFL.acceptedOn,
    "partof": TFL.partOf,
    "locatedin": TFL.locatedIn,
    "terminatesat": TFL.terminatesAt,
}

CANONICAL = {
    'Dlr': 'DLR',
    'Tfl': 'TfL',
    'Jubilee': 'JubileeLine',
    'Central': 'CentralLine',
    'Victoria': 'VictoriaLine',
    'Northern': 'NorthernLine',
    'Piccadilly': 'PiccadillyLine',
    'Bakerloo': 'BakerlooLine',
    'Circle': 'CircleLine',
    'District': 'DistrictLine',
    'Metropolitan': 'MetropolitanLine',
    'HammersmithCity': 'HammersmithCityLine',
    'WaterlooCity': 'WaterlooAndCityLine',
    'ElizabethLine': 'ElizabethLineRoute',
    'BakerStreet': 'BakerStreetStation',
    'KingsCross': 'KingsCrossStPancras',
    'Stratford': 'StratfordStation',
    'TrafalgarSquare': 'TrafalgarSquareBusTerminus',
}

def normalize_entity(text: str) -> str:
    text = text.strip().lower().replace("&", "and")
    for s in [" line", " railway", " station"]:
        if text.endswith(s): text = text[: -len(s)]
    return " ".join(text.split())

def slugify(text):
    text = normalize_entity(text) 
    text = re.sub(r"[^\w\s-]", "", text)
    text = "".join(word.capitalize() for word in text.split())
    return CANONICAL.get(text, text)

def label_to_uri(label):
    return TFL[slugify(label)]

def map_predicate(raw):
    key = raw.lower().replace(" ", "").replace("_", "")
    return PREDICATE_MAP.get(key)

def build_wiki_graph(all_results):
    g = Graph()
    g.bind("tfl", TFL)
    g.bind("dcterms", DCTERMS)
    g.bind("prov", PROV)
    
    pipeline_uri = TFL["UnstructuredPipeline"]
    g.add((pipeline_uri, RDF.type, PROV.Activity))
    
    labelled = set() 
    for article in all_results:
        source_uri = URIRef(f"https://en.wikipedia.org/wiki/{article['title'].replace(' ', '_')}")
        
        for ent in article.get("entities", []):
            text = ent["text"]
            if len(text) <= 2 or len(text) > 40: continue
            cls = LABEL_CLASS_MAP.get(ent["label"])
            if cls:
                ent_uri = label_to_uri(text)
                g.add((ent_uri, RDF.type, cls))
                if ent_uri not in labelled: 
                    g.add((ent_uri, RDFS.label, Literal(text)))
                    labelled.add(ent_uri)
        
        for triple in article["triples"]:
            subj_uri = label_to_uri(triple["subject"])
            pred_uri = map_predicate(triple["predicate"])
            if pred_uri is None: continue

            obj_label = triple["object"]
            if pred_uri == TFL.openedDate:
                obj_node = Literal(obj_label, datatype=XSD.gYear)
            elif obj_label.lower() in ("true", "false"): 
                obj_node = Literal(obj_label.lower() == "true", datatype=XSD.boolean)
            elif len(obj_label.split()) <= 5:
                obj_node = label_to_uri(obj_label)
                if obj_node not in labelled: 
                    g.add((obj_node, RDFS.label, Literal(obj_label)))
                    labelled.add(obj_node)
            else:
                obj_node = Literal(obj_label)

            g.add((subj_uri, pred_uri, obj_node))
            g.add((subj_uri, DCTERMS.source, source_uri))
            g.add((subj_uri, PROV.wasGeneratedBy, pipeline_uri))
    return g

def enrich_graph(g):
    # Priority 4: Tighten Night Tube Precision
    # Only Underground Lines can be Night Tube
    for line in list(g.subjects(TFL.isNightTube, Literal(True))):
        if (line, RDF.type, TFL.UndergroundLine) not in g:
            g.remove((line, TFL.isNightTube, Literal(True)))

    # Derived inversions
    for station, line in g.subject_objects(TFL.servedByLine):
        g.add((line, TFL.hasStop, station))
    
    # Facility classification
    FACILITY_CLASSES = {"toilets": TFL.PublicToilet, "car park": TFL.CarPark}
    for s, o in list(g.subject_objects(TFL.hasFacility)):
        for label in g.objects(o, RDFS.label):
            key = str(label).lower()
            if key in FACILITY_CLASSES: g.add((o, RDF.type, FACILITY_CLASSES[key]))

    return g

def run_triples_to_rdf():
    processed_dir = os.path.join("data", "processed")
    latest = sorted(os.listdir(processed_dir))[-1]
    with open(os.path.join(processed_dir, latest, "wiki_triples.json"), encoding="utf-8") as f:
        all_results = json.load(f)
    g = build_wiki_graph(all_results)
    g = enrich_graph(g)
    out_path = "ontologies/pipeline_output/unstructured_london_transport.ttl"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    g.serialize(out_path, format="turtle")

if __name__ == "__main__":
    run_triples_to_rdf()