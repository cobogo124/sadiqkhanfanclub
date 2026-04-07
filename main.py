import os
from rdflib import Graph
from generateOntology import generateOntology

# Import modules from the existing pipeline structure
from data_retrieval.unstructured_retrieval import wiki_scraper
from data_retrieval.unstructured_retrieval import extract_triples
from data_retrieval.unstructured_retrieval import triples_to_rdf
from data_retrieval.structured_retrieval import tfl_api_processor
from data_retrieval.unstructured_retrieval.triples_to_rdf import TFL

def main():
    print("--- 1. Programmatically Generating Base Ontology Schema (TBox) ---")
    tbox_path = "ontologies/manual/tfl_kamyar_final.ttl"
    # Call the generator to create the .ttl file and return the graph
    final_graph = generateOntology(tbox_path)
    
    # Load GTFS standard if available
    gtfs_path = "ontologies/manual/gtfs.ttl"
    if os.path.exists(gtfs_path):
        final_graph.parse(gtfs_path, format="turtle")
    
    print("\n--- 2. Running Unstructured Pipeline ---")
    print("  -> Step 2a: Scraping Wikipedia...")
    wiki_scraper.run_wiki_scraper()
    
    print("  -> Step 2b: Extracting Triples (LLM/Cache)...")
    extract_triples.run_extract_triples()
    
    print("  -> Step 2c: Building Unstructured RDF Graph...")
    triples_to_rdf.run_triples_to_rdf()
    
    unstructured_path = "ontologies/pipeline_output/unstructured_london_transport.ttl"
    if os.path.exists(unstructured_path):
        final_graph.parse(unstructured_path, format="turtle")

    print("\n--- 3. Running Structured Pipeline ---")
    # Fetch API data and merge into the graph
    structured_g = tfl_api_processor.run()
    final_graph += structured_g
    
    print("\n--- 4. Merging and Saving Final Knowledge Graph ---")
    output_path = "ontologies/pipeline_output/final_london_transport_kg.ttl"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_graph.serialize(destination=output_path, format="turtle")
    
    print(f"\nSuccess! Final KG saved to: {output_path}")
    print(f"Total Triples in Graph: {len(final_graph)}")

if __name__ == "__main__":
    main()