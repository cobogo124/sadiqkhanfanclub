import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

from data_retrieval.fetch_tfl_sources import fetch_tfl_snapshot
from data_retrieval.build_tfl_ontology import main as build_kg

def run_pipeline():
    print("--- Step 1: Fetching TfL Data (Structured & Unstructured) ---")
    fetch_summary = fetch_tfl_snapshot()
    print(f"Success: Fetched {fetch_summary['source_count']} sources.")

    print("\n--- Step 2: Building and Populating Knowledge Graph ---")
    build_kg(snapshot_date=fetch_summary['snapshot_date'])
    
    print("\n--- Pipeline Complete ---")
    print("Outputs generated in 'ontologies/' and 'docs/generated/'")

if __name__ == "__main__":
    run_pipeline()