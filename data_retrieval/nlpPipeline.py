import spacy
from rdflib import Graph, URIRef, Literal, RDF, Namespace

# Load spaCy model as per Lab 7
nlp = spacy.load("en_core_web_sm")
LT = Namespace("http://kcl.ac.uk/ontology/london-transport#")

# Standardize how URIs are generated across both scripts
def get_uri(name):
    # Convert "Green Park" to "green_park" for consistency
    clean_name = name.strip().lower().replace(" ", "_")
    return URIRef(LT[clean_name])

def extract_transport_entities(text):
    doc = nlp(text)
    g = Graph()
    
    for ent in doc.ents:
        entity_uri = get_uri(ent.text)
        
        # Logic to distinguish between Lines and Stops
        if "line" in ent.text.lower():
            g.add((entity_uri, RDF.type, LT.TfLLine)) # Use TfLLine from your ontology
            g.add((entity_uri, LT.lineName, Literal(ent.text)))
        elif ent.label_ in ["FAC", "GPE", "ORG"]:
            g.add((entity_uri, RDF.type, LT.TransitStop))
            g.add((entity_uri, LT.stopName, Literal(ent.text)))
            
    return g

# Example usage with a news snippet
text_source = "The Victoria line serves Brixton and Green Park."
graph = extract_transport_entities(text_source)
graph.serialize(destination="data/text_instances.ttl", format="turtle")