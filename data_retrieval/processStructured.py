import pandas as pd
from rdflib import Graph, Literal, RDF, URIRef, Namespace
import json

LT = Namespace("http://kcl.ac.uk/ontology/london-transport#")

def map_naptan_to_rdf(csv_path, output_path):
    df = pd.read_csv(csv_path)
    g = Graph()
    g.bind("lt", LT)
    
    for _, row in df.iterrows():
        stop_uri = URIRef(LT[f"stop_{row['AtcoCode']}"])
        g.add((stop_uri, RDF.type, LT.TransitStop))
        g.add((stop_uri, LT.stopName, Literal(row['CommonName'])))
        g.add((stop_uri, LT.naptanId, Literal(row['AtcoCode'])))
    
    g.serialize(destination=output_path, format='turtle')
    print(f"Serialized NaPTAN data to {output_path}")

if __name__ == "__main__":
    map_naptan_to_rdf("downloads/naptan_london.csv", "data/naptan_instances.ttl")