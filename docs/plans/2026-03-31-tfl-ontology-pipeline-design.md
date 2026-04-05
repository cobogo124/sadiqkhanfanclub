# TfL Ontology Population Pipeline Design

## Goal

Build a repeatable pipeline that fetches authoritative London public transport data, normalizes it, and regenerates a coursework-ready knowledge graph for TfL with strong coverage of the initial competency questions and explicit source tracking.

## Context

The repository already contains:

- A custom transport ontology in `ontologies/london-transport-ontology.ttl`
- Two copied GTFS ontology files in `ontologies/gtfs.ttl` and `ontologies/sadiqkhanfanclub.ttl`
- Early retrieval scripts in `data_retrieval/`

The coursework specification requires:

- A knowledge graph with ontology and instances
- At least one textual source and one structured source
- At least two existing ontologies extended by subclasses and subproperties
- An automated construction pipeline rather than a manually authored graph

## Recommended Approach

Adopt an API-first hybrid pipeline:

1. Use the official TfL Unified API as the primary structured source for lines, route sequences, stop points, zones, facilities, service types, and station metadata.
2. Use official TfL guides or station pages only for fields the API does not expose reliably, especially step-free access semantics.
3. Keep NaPTAN as a fallback normalization source when stop identifiers or parent-station relationships need support.

This approach is preferred over scrape-first enrichment because it is more reproducible, easier to justify in the report, and better aligned with the coursework requirement for an automated system.

## Source Strategy

### Structured sources

- TfL Unified API
  - `/Line/Mode/...`
  - `/Line/{id}/Route/Sequence/...`
  - `/Line/{id}/StopPoints`
  - `/Line/{id}/Status`
  - `/StopPoint/{id}`
  - `/StopPoint/Search/{query}`
- NaPTAN API fallback for London access nodes

### Textual or semi-structured sources

- Official TfL step-free guide or station accessibility pages
- Official TfL network/service pages for operator and Night Tube confirmation where needed

## Ontology Strategy

### Main ontology

`ontologies/london-transport-ontology.ttl` remains the primary coursework ontology.

### Existing ontology extensions

Preserve the existing Schema.org and DBpedia extensions already present in the TBox so the coursework requirement remains clearly satisfied.

### Secondary ontology influence

Use GTFS as the transport-domain ontology that influences the model and the pipeline:

- `:TfLLine rdfs:subClassOf gtfs:Route`
- `:TransitStop rdfs:subClassOf gtfs:Stop`
- `:InterchangeStation rdfs:subClassOf gtfs:Station`
- `:TransportOperator rdfs:subClassOf gtfs:Agency`
- `:hasStop rdfs:subPropertyOf gtfs:stop`
- `:inFareZone rdfs:subPropertyOf gtfs:zone`

This keeps Schema.org as a broad web ontology, DBpedia as a linked-data ontology, and GTFS as the transport ontology shaping the population logic.

## Population Scope

The generated graph should include, at minimum:

- TfL modes: Tube, Bus, DLR, Overground, Elizabeth line
- Lines and routes for those modes
- Stations, hubs, and bus stops returned by the official line and stop APIs
- Fare zones
- Operators
- Current service-type metadata such as Night service availability
- Interchange relationships
- Facilities and accessibility facts needed for the competency questions
- Source manifests and retrieval timestamps

## Competency Question Coverage

The current 10 manually defined competency questions can be covered as follows:

1. Lines intersecting at King’s Cross St Pancras:
   use station `lines` from the stop-point record
2. Victoria line terminal stations:
   derive first and last stations from the route sequence
3. Modes available at Stratford:
   use station hub `modes`
4. DLR fare zones:
   aggregate zone membership across DLR stations
5. Jubilee stations with step-free access from street to train:
   use API accessibility/facility data, with official guide fallback
6. Baker Street public restrooms:
   use station `additionalProperties` for `Toilets`
7. Central line stations with public car parking:
   use station `additionalProperties` for `Car park`
8. London Overground operating company:
   populate from official TfL operator information
9. Bus routes terminating at Trafalgar Square:
   derive termini from bus route sequences and terminal stop matching
10. Night Tube lines on Fridays and Saturdays:
    use official TfL Night service evidence and line service types

## Data Flow

### Stage 1: Fetch

- Snapshot raw responses into dated directories such as `downloads/raw/2026-03-31/`
- Preserve source URLs and retrieval time for provenance

### Stage 2: Normalize

- Convert raw line, station, hub, and facility payloads into consistent Python records
- Standardize URI-safe identifiers based on TfL IDs
- Normalize zone strings such as `2/3` into separate zone references

### Stage 3: Materialize RDF

- Generate:
  - ontology-aligned instances
  - GTFS alignment triples
  - source manifest triples or source metadata output
- Keep ABox generation separate from the TBox

### Stage 4: Merge

- Optionally create a single coursework-ready Turtle file combining ontology, mappings, and instances

## Output Files

Planned generated outputs:

- `ontologies/london-transport-instances.ttl`
- `ontologies/london-transport-kg.ttl`
- `ontologies/gtfs-alignment.ttl`
- `docs/generated/tfl-sources.md`
- `docs/generated/tfl-sources.json`

## Ontology Improvements Needed

The current ontology is close, but the pipeline will be cleaner if we add:

- explicit GTFS prefix and alignment axioms
- facility properties for public toilets and car parking
- a transport-mode relation that can be attached directly to stations if needed
- a text property for step-free access detail or coverage
- optional provenance-friendly properties or reuse of `dcterms:source`

## Validation Strategy

Create a lightweight verification suite that:

- builds the graph from raw snapshots
- runs SPARQL checks for the manually defined competency questions
- performs structural sanity checks on critical entities and line coverage

Representative assertions:

- Victoria line has exactly two termini
- Stratford includes Tube, Bus, DLR, Overground, and Elizabeth line
- Baker Street includes a toilets facility fact
- At least one Jubilee station is marked with step-free access detail

## Risks And Mitigations

- TfL API gaps for nuanced accessibility:
  mitigate with official TfL step-free guide fallback
- Bus termini ambiguity:
  derive from route sequence endpoints and retain source evidence
- Duplicate stop or hub identifiers:
  normalize by parent/top-most parent relationships and keep TfL IDs as canonical
- Overly broad graph size:
  prioritize competency-question coverage first, then enrich comprehensively for the rest of the network

## Notes For Implementation

- Prefer `ontologies/gtfs.ttl` as the reference GTFS ontology file; `ontologies/sadiqkhanfanclub.ttl` appears to be a separate local copy and should be treated as legacy unless there is a specific reason to keep using it.
- Keep the pipeline deterministic: same raw snapshot should produce the same URIs and triple patterns.
- Prefer official TfL and government sources over Wikipedia or community-maintained sources.
