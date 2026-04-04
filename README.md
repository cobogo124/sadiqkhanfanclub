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
- `ontologies/london-transport-protege.owl`
- `ontologies/gtfs-alignment.ttl`
- `docs/generated/tfl-sources.md`
- `docs/generated/tfl-sources.json`

## Open In Protégé

Open:

`ontologies/london-transport-protege.owl`

That file is a self-contained OWL export of the generated knowledge graph and is the easiest bundle to inspect in Protégé.

## CQs
Manual
1. ​Which London Underground lines intersect at King's Cross St Pancras station?
2. ​What are the terminal stations for the Victoria Line?
3. ​Which transport modes (e.g., Tube, Bus, DLR, Elizabeth Line) are available for interchange at Stratford station?
4. ​Which fare zones does the Docklands Light Railway (DLR) operate within?
5. Which stations on the Jubilee Line feature step-free access from the street to the train?
6. Does Baker Street station have public restroom facilities available?
7. Which stations on the Central Line provide public car parking facilities?
8. Who is the designated operating company for the London Overground network?
9. Which specific bus routes terminate at Trafalgar Square?
10. Which London Underground lines operate the Night Tube service on Fridays and Saturdays?

LLM
11. Which stations act as boundary points between two or more fare zones?
12. Which transport modes in the TfL network are classified as "High Capacity" (e.g., Elizabeth Line, Tube) versus "Surface" (Bus)?
13. Which London Underground lines are explicitly designated as "Night Tube" lines in the TBox?
14. Which stations are classified as "Interchange Stations" and serve more than three different transport modes?
15. What is the ordered sequence of stations for the Victoria Line, starting from Brixton?
16. Which stations on the Overground network offer staff-assisted boarding for passengers, as noted in the accessibility guide?
17. Which specific bus routes operate as night bus services with an N-prefix in the TfL network?
18. Which Elizabeth Line stations are equipped with "step-free from street to train" access? (Extracted from your PDF textual source)
19. Which TfL lines serve stations located in both zone 2 and zone 3?
20. Which transport operators are responsible for the management of the London Overground and Elizabeth Line?