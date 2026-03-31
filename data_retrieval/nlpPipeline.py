import spacy
from rdflib import Graph, URIRef, Literal, RDF, Namespace

# Load spaCy model as per Lab 7
nlp = spacy.load("en_core_web_sm")
LT = Namespace("http://kcl.ac.uk/ontology/london-transport#")

def extract_transport_entities(text):
    doc = nlp(text)
    g = Graph()
    
    for ent in doc.ents:
        # Custom logic to map 'GPE' or 'ORG' to TransitStops/Lines
        if ent.label_ in ["FAC", "GPE", "ORG"]:
            entity_uri = URIRef(LT[ent.text.replace(" ", "_")])
            g.add((entity_uri, RDF.type, LT.TransitStop))
            g.add((entity_uri, LT.stopName, Literal(ent.text)))
            
    return g

# Example usage with a news snippet
text_source = "The Victoria line serves Brixton and Green Park."
graph = extract_transport_entities(text_source)
graph.serialize(destination="data/text_instances.ttl", format="turtle")