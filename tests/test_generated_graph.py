from pathlib import Path

from rdflib import Graph


KG_PATH = Path("ontologies/london-transport-kg.ttl")
PROTEGE_PATH = Path("ontologies/london-transport-protege.owl")


def load_graph() -> Graph:
    assert KG_PATH.exists(), "expected generated graph at ontologies/london-transport-kg.ttl"
    return Graph().parse(KG_PATH, format="turtle")


def test_protege_bundle_exists_and_is_parseable() -> None:
    assert PROTEGE_PATH.exists(), "expected Protégé bundle at ontologies/london-transport-protege.owl"
    graph = Graph().parse(PROTEGE_PATH)
    assert len(graph) > 0


def test_victoria_line_has_expected_termini() -> None:
    graph = load_graph()
    query = """
    PREFIX lt: <http://kcl.ac.uk/ontology/london-transport#>
    SELECT DISTINCT ?stopName WHERE {
      ?line lt:lineId "victoria" ; lt:hasTerminus ?stop .
      ?stop lt:stopName ?stopName .
    }
    ORDER BY ?stopName
    """
    rows = [str(row[0]) for row in graph.query(query)]
    assert rows == ["Brixton", "Walthamstow Central"]


def test_stratford_has_expected_tfl_interchange_modes() -> None:
    graph = load_graph()
    query = """
    PREFIX lt: <http://kcl.ac.uk/ontology/london-transport#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT DISTINCT ?modeLabel WHERE {
      ?station lt:stopName "Stratford" ; lt:hasAvailableMode ?mode .
      ?mode rdfs:label ?modeLabel .
    }
    ORDER BY ?modeLabel
    """
    rows = [str(row[0]) for row in graph.query(query)]
    assert rows == ["Bus", "DLR", "Elizabeth line", "Overground", "Underground"]


def test_baker_street_station_records_public_toilets() -> None:
    graph = load_graph()
    query = """
    PREFIX lt: <http://kcl.ac.uk/ontology/london-transport#>
    SELECT ?toilets WHERE {
      ?station lt:stopName "Baker Street Underground Station" ;
               lt:hasPublicToilets ?toilets .
    }
    """
    rows = [bool(row[0]) for row in graph.query(query)]
    assert rows == [True]


def test_overground_lines_are_mapped_to_arriva_rail_london() -> None:
    graph = load_graph()
    query = """
    PREFIX lt: <http://kcl.ac.uk/ontology/london-transport#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT DISTINCT ?operatorName WHERE {
      ?line a lt:OvergroundLine ; lt:operatedBy ?operator .
      ?operator rdfs:label ?operatorName .
    }
    """
    rows = [str(row[0]) for row in graph.query(query)]
    assert rows == ["Arriva Rail London"]


def test_night_tube_lines_match_official_service_set() -> None:
    graph = load_graph()
    query = """
    PREFIX lt: <http://kcl.ac.uk/ontology/london-transport#>
    SELECT DISTINCT ?lineName WHERE {
      ?line a lt:NightTubeLine ; lt:lineName ?lineName .
    }
    ORDER BY ?lineName
    """
    rows = [str(row[0]) for row in graph.query(query)]
    assert rows == ["Central", "Jubilee", "Northern", "Piccadilly", "Victoria"]
