# sadiqkhanfanclub

## Build the TfL snapshot

Run:

`python3 data_retrieval/fetch_tfl_sources.py`

This downloads a dated snapshot of the official TfL sources into `downloads/raw/<date>/`.

## Build the ontology outputs

Run:

`python3 data_retrieval/build_tfl_ontology.py`

This generates:

- `ontologies/london-transport-instances.ttl`
- `ontologies/london-transport-kg.ttl`
- `ontologies/gtfs-alignment.ttl`
- `docs/generated/tfl-sources.md`
- `docs/generated/tfl-sources.json`
