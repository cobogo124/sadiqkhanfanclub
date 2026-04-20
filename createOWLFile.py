from rdflib import Graph
g = Graph()
g.parse("ontologies/pipeline_output/final_london_transport_kg.ttl", format="turtle")
g.serialize("ontologies/pipeline_output/final_kg.owl", format="xml")