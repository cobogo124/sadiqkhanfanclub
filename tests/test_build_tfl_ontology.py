from rdflib import Literal, Namespace

from data_retrieval.build_tfl_ontology import build_graph_from_records


LT = Namespace("http://kcl.ac.uk/ontology/london-transport#")


def test_build_graph_from_records_emits_line_stop_and_zone_triples() -> None:
    records = {
        "lines": [
            {
                "id": "victoria",
                "name": "Victoria",
                "modeName": "tube",
                "is_night_service": True,
            }
        ],
        "operators": [],
        "stops": [
            {
                "id": "940GZZLUGPK",
                "name": "Green Park Underground Station",
                "stop_class": "TubeStation",
                "modes": ["tube"],
                "zones": ["1"],
                "line_ids": ["victoria"],
                "has_public_toilets": False,
                "has_car_parking": False,
                "is_step_free": True,
                "step_free_access_note": "Station appears in the official TfL step-free guide.",
                "lat": 51.506947,
                "lon": -0.142787,
                "sources": ["https://api.tfl.gov.uk/StopPoint/940GZZLUGPK"],
            }
        ],
        "sources": [],
    }
    graph = build_graph_from_records(records)
    assert (LT.line_victoria, LT.lineName, Literal("Victoria")) in graph
    assert (LT.line_victoria, LT.isNightService, Literal(True)) in graph
    assert (LT.stop_940GZZLUGPK, LT.inFareZone, LT.zone_1) in graph
    assert (LT.stop_940GZZLUGPK, LT.isServedBy, LT.line_victoria) in graph
    assert (LT.stop_940GZZLUGPK, LT.hasPublicToilets, Literal(False)) in graph
