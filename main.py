import os
from rdflib import Graph
from data_retrieval.unstructured_retrieval import wiki_to_rdf
from data_retrieval.structured_retrieval import tfl_api_processor
from data_retrieval.unstructured_retrieval.wiki_to_rdf import TFL

def main():
    final_graph = Graph()
    final_graph.bind("tfl", TFL)
    
    print("--- 1. Loading Base Ontologies ---")
    tbox_path = "ontologies/manual/tfl_kamyar_final.ttl"
    if os.path.exists(tbox_path):
        final_graph.parse(tbox_path, format="turtle")
    else:
        print(f"Error: Could not find {tbox_path}")
        
    # Load GTFS standard
    gtfs_path = "ontologies/manual/gtfs.ttl"
    if os.path.exists(gtfs_path):
        final_graph.parse(gtfs_path, format="turtle")
    
    print("\n--- 2. Running Unstructured Pipeline ---")
    # Run the colleague's script
    wiki_to_rdf.run()
    
    # Load the ABox their script just generated
    unstructured_path = "ontologies/pipeline_output/unstructured_london_transport.ttl"
    if os.path.exists(unstructured_path):
        final_graph.parse(unstructured_path, format="turtle")
    else:
        print(f"Warning: {unstructured_path} was not found.")

    print("\n--- 3. Running Structured Pipeline ---")
    # Run your code and merge the resulting graph directly
    structured_g = tfl_api_processor.run()
    final_graph += structured_g
    
    print("\n--- 4. Merging and Saving Final Knowledge Graph ---")
    output_path = "ontologies/pipeline_output/final_london_transport_kg.ttl"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_graph.serialize(destination=output_path, format="turtle")
    
    print(f"\nSuccess! Final populated ontology saved to: {output_path}")
    print(f"Total Triples in Graph: {len(final_graph)}")

if __name__ == "__main__":
    main()