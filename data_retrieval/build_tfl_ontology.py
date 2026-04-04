from __future__ import annotations
import json
from pathlib import Path
from rdflib import DCTERMS, Graph, Literal, Namespace, RDF, RDFS, URIRef
from data_retrieval.fetch_tfl_sources import repo_root, snapshot_path_for
from data_retrieval.tfl_transform import (
    bool_from_tfl_value, classify_line, classify_stop, 
    parse_step_free_guide, split_zone_string, uri_safe_fragment, extract_step_free_note, facility_lookup
)

LT = Namespace("http://kcl.ac.uk/ontology/london-transport#")
GTFS = Namespace("http://vocab.gtfs.org/terms#")

def build_graph_from_records(records: dict) -> Graph:
    g = Graph()
    g.bind("lt", LT)
    g.bind("gtfs", GTFS)

    # Populate Modes (CQ 12: HighCapacity vs Surface)
    for m_name in ["tube", "dlr", "elizabeth-line", "bus", "overground"]:
        m_uri = LT[f"mode_{uri_safe_fragment(m_name)}"]
        g.add((m_uri, RDF.type, LT.TransportMode))
        if m_name in ["tube", "dlr", "elizabeth-line"]:
            g.add((m_uri, RDF.type, LT.HighCapacityMode))
        else:
            g.add((m_uri, RDF.type, LT.SurfaceMode))

    # Populate Lines (CQ 15: Ordered Sequences)
    for line in records['lines']:
        l_uri = LT[f"line_{uri_safe_fragment(line['id'])}"]
        g.add((l_uri, RDF.type, LT[line['line_class']]))
        for idx, sid in enumerate(line['stop_ids']):
            s_uri = LT[f"stop_{sid}"]
            g.add((s_uri, LT.stopOrderOnLine, Literal(idx)))
            g.add((l_uri, LT.hasStop, s_uri))

    # Populate Stops (CQs 6, 7: Facilities; CQ 11: Zones)
    for stop in records['stops']:
        s_uri = LT[f"stop_{stop['id']}"]
        g.add((s_uri, RDF.type, LT[stop['stop_class']]))
        g.add((s_uri, LT.stopName, Literal(stop['name'])))
        g.add((s_uri, LT.hasPublicToilets, Literal(stop['has_public_toilets'])))
        g.add((s_uri, LT.hasCarParking, Literal(stop['has_car_parking'])))
        for z in stop['zones']:
            g.add((s_uri, LT.inFareZone, LT[f"zone_{z}"]))
        if stop.get("step_free_access_note"): # Unstructured Data Requirement
            g.add((s_uri, LT.stepFreeAccessNote, Literal(stop['step_free_access_note'])))

    return g

def main(snapshot_date: str):
    repo = repo_root()
    # Logic to load raw JSONs and call build_graph_from_records goes here...
    # (Matches original build_tfl_ontology.py logic but uses the new main.py trigger)
    print(f"Building Knowledge Graph for snapshot: {snapshot_date}")