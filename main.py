import os
from rdflib import Graph
from generateOntology import generateOntology
from data_retrieval.unstructured_retrieval import wiki_scraper, extract_triples, triples_to_rdf
from data_retrieval.structured_retrieval import tfl_api_processor

def main():
    final_kg_path = "ontologies/pipeline_output/final_london_transport_kg.ttl"
    
    print("--- 1. Generating Base Ontology Schema (TBox) ---")
    final_graph = generateOntology("ontologies/manual/tfl_kamyar_final.ttl")
    
    gtfs_path = "ontologies/manual/gtfs.ttl"
    if os.path.exists(gtfs_path):
        final_graph.parse(gtfs_path, format="turtle")

    print("\n--- 2. Unstructured Pipeline ---")
    unstructured_path = "ontologies/pipeline_output/unstructured_london_transport.ttl"
    
    print("  -> Running full Wikipedia extraction...")
    wiki_scraper.run_wiki_scraper()
    extract_triples.run_extract_triples()
    triples_to_rdf.run_triples_to_rdf()
    if os.path.exists(unstructured_path):
        final_graph.parse(unstructured_path, format="turtle")

    print("\n--- 3. Structured Pipeline ---")
    # Pure extraction. No manual layers.
    structured_g = tfl_api_processor.run()
    final_graph += structured_g

    print("\n--- 4. Merging and Saving Final Knowledge Graph ---")
    os.makedirs(os.path.dirname(final_kg_path), exist_ok=True)
    final_graph.serialize(destination=final_kg_path, format="turtle")
    
    print(f"\nSuccess! Final KG saved to: {final_kg_path}")

if __name__ == "__main__":
    main()