from pathlib import Path


def test_ontology_declares_gtfs_alignment_and_facility_properties() -> None:
    ontology = Path("ontologies/london-transport-ontology.ttl").read_text(encoding="utf-8")
    assert "@prefix gtfs:" in ontology
    assert ":hasPublicToilets" in ontology
    assert ":hasCarParking" in ontology
    assert ":stepFreeAccessNote" in ontology
    assert "rdfs:subPropertyOf gtfs:stop" in ontology
    assert ":TfLLine rdf:type owl:Class ;" in ontology
    assert "rdfs:subClassOf dbo:RouteOfTransportation ," in ontology or "rdfs:subClassOf dbo:RouteOfTransportation," in ontology
    assert "gtfs:Route" in ontology
