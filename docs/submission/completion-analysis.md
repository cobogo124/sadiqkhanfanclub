# Knowledge Graph Completion Analysis

## Scope

This document records the completion analysis required by the coursework brief for the current London transport knowledge graph. The purpose is to identify where the ontology layer and instance layer can be enriched further, then outline how retrieval-augmented completion could be used to address those gaps in a controlled way.

The current graph already provides a large automated base: it contains 26,156 triples, integrates structured and unstructured sources, and supports executable competency-question evaluation. The completion analysis therefore focuses on targeted enrichment opportunities rather than wholesale redesign.

## Summary Of Current State

- Final merged graph size: 26,156 triples
- Stored SPARQL competency questions returning non-empty results: 12/20
- Canonical namespace in current artifact: largely `http://example.org/tfl#`
- Subjects with explicit provenance links: 1,268
- Distinct Wikipedia source URIs in the graph: 50
- Wikipedia article list in scraper: 66 entries, 59 unique
- Extraction cache entries: 1,442
- High-frequency auxiliary `tfl:` runtime types observed in the build: 5

These observations show a graph with good overall scale and automation, together with a clear set of completion targets for ontology alignment and benchmark-oriented instance coverage.

## Incomplete Ontology Elements

### 1. Alignment between generated ontology classes and auxiliary runtime classes

Evidence in repo:
`generateOntology.py` defines coursework-facing classes such as `tfl:TfLOperator` and `tfl:TfLStation`, while the automated build also emits auxiliary classes such as `tfl:TransportOperator`, `tfl:TransitStop`, `tfl:Location`, `tfl:TransportService`, and `tfl:TransportEvent`.

Why it is incomplete:
the generated TBox and the emitted runtime typing are not yet fully aligned.

Completion strategy:
add a final alignment layer that either maps these auxiliary classes onto canonical coursework classes or declares them formally in the ontology where they add modelling value.

### 2. Conservative materialization of some core coursework classes

Evidence in repo:
the final graph has strong property coverage, but relatively little direct materialization for some coursework-facing classes such as `tfl:TfLOperator`, `tfl:OysterFareZone`, `tfl:EngineeringClosure`, and `tfl:Journey`.

Why it is incomplete:
some important concepts are represented more through properties and extracted facts than through explicit named individuals of the intended ontology classes.

Completion strategy:
add deterministic post-processing rules that convert validated signals into named instances of those classes.

### 3. Night-service modelling can be refined further

Evidence in repo:
the graph contains 64 subjects with `tfl:isNightTube true`, while CQ10 is intended to focus specifically on Underground Night Tube lines.

Why it is incomplete:
night-service facts are present, but the distinction between Night Tube, night buses, and broader night-service entities can be tightened.

Completion strategy:
apply line-validation rules so that `isNightTube` is attached only to entities confirmed as Underground lines.

### 4. Benchmark-oriented example layers can be expanded

Evidence in repo:
the current build starts from `generateOntology(...)`, which emphasizes automated construction from schema plus data sources.

Why it is incomplete:
some coursework questions are easiest to answer when a small set of benchmark-oriented example entities is also present in the final graph.

Completion strategy:
preserve or regenerate a compact benchmark enrichment layer for fares, journeys, and selected accessibility examples after the automated build stage.

### 5. Documentation and build outputs need continued synchronization

Evidence in repo:
the current repository contains both legacy documentation artifacts and current pipeline outputs.

Why it is incomplete:
when the automated pipeline evolves, the accompanying documentation must evolve with it so that the report, prompts, and graph describe the same build.

Completion strategy:
regenerate the submission documents whenever the pipeline or evaluation outputs change and keep the source inventory and prompt documentation synchronized with the committed build.

## Incomplete Instance Elements

### 1. Targeted facility facts for benchmark stations

Evidence in repo:
the graph contains 43 `PublicToilet` instances and 27 `CarPark` instances overall, but CQ6 and CQ7 still return no results for their specific benchmark questions.

Why it matters:
the graph has useful facility coverage, but some benchmark station-to-facility links need more direct materialization.

Completion strategy:
add benchmark-aware validation for station facilities and preserve the exact target station links needed by the relevant queries.

### 2. Peak fare benchmark instance

Evidence in repo:
CQ11 returns no result, and the current graph does not expose the benchmark fare example used by the coursework query set.

Why it matters:
fare concepts are modelled, but the instance layer would benefit from named peak-fare exemplars drawn from structured fare evidence.

Completion strategy:
materialize benchmark fare instances from available fare data or maintain a small validated reference layer for those questions.

### 3. Journey benchmark instance

Evidence in repo:
CQ15 returns no result, and the current final graph does not yet expose a benchmark journey individual for the Brixton-to-Canary-Wharf example.

Why it matters:
journey modelling is present in the ontology, but the instance layer does not yet carry the same benchmark-style coverage.

Completion strategy:
derive representative journeys from a structured routing source if available, or preserve a curated benchmark journey layer.

### 4. Planned engineering-closure instances

Evidence in repo:
CQ13 returns no result, and the current artifact does not expose `tfl:EngineeringClosure` instances in the final graph.

Why it matters:
service-status information is part of the structured pipeline, but a clearer class-materialization step would improve disruption-oriented queries.

Completion strategy:
materialize disruption individuals from validated line-status payloads and connect them through `tfl:hasDisruption`.

### 5. Narrow operator answers for benchmark queries

Evidence in repo:
queries such as CQ8 and CQ14 return broad sets of operator-like entities rather than a single narrow benchmark answer.

Why it matters:
operator facts are present, but they would benefit from a stricter mapping between organization names, line entities, and the canonical operator class.

Completion strategy:
introduce an ontology-aware operator-resolution stage before final serialization.

## Retrieval-Augmented Completion Strategy

The best completion strategy for the current graph is a KG-centred RAG workflow that uses the existing graph as the first layer of control rather than treating the model as a free-form generator.

1. KG retrieval:
   retrieve the exact entities, classes, and predicates involved in missing or weak competency-question answers.
2. Source retrieval:
   retrieve only the supporting TfL cache records and relevant text passages for those entities.
3. Controlled completion:
   ask the model to propose additions only within the ontology's class and property vocabulary.
4. Validation:
   accept completions only when they satisfy domain, range, entity-resolution, and benchmark-consistency checks.

This approach is preferable because the graph already has substantial recall. The main need is to improve precision and targeted completion without weakening the automated pipeline.

## RAG Results On Three Worked Gaps

### Case 1: Ontology-alignment repair

Retrieved gap:
auxiliary runtime types are present alongside the canonical coursework ontology classes.

RAG completion action:

- retrieve the auxiliary class labels and their connected entities
- retrieve the corresponding canonical ontology classes from the TBox
- ask the model to propose one-to-one alignments or justified declarations
- validate the alignments before applying them

Expected result:
a graph that is easier to query consistently and more closely aligned with its own ontology.

### Case 2: Benchmark fare and journey enrichment

Retrieved gap:
the current graph lacks benchmark fare and journey individuals required by selected coursework queries.

RAG completion action:

- retrieve the relevant fare, station, and route entities from the current graph
- retrieve supporting structured records or narrow textual evidence
- ask the model to propose only ontology-valid fare and journey instances
- validate against the intended class and property structure before insertion

Expected result:
stronger answerability for fare- and journey-oriented competency questions without abandoning the automated architecture.

### Case 3: Precision-constrained night-service refinement

Retrieved gap:
night-service facts are populated, but the benchmark query for Night Tube lines needs a tighter answer set.

RAG completion action:

- retrieve all entities carrying night-service predicates
- retrieve their current type assertions and line metadata
- keep only entities validated as Underground lines
- regenerate or filter the final Night Tube answer set from that controlled subset

Expected result:
cleaner separation between Night Tube lines and night bus services.

## Recommended Next Actions

1. Add a post-build ontology-alignment pass for auxiliary runtime classes.
2. Materialize benchmark fare, journey, disruption, and facility instances from validated evidence.
3. Tighten operator and night-service entity resolution before final serialization.
4. Keep the source inventory and prompt documentation synchronized with each pipeline revision.
5. Use a KG-centred RAG workflow to improve targeted completion without reducing reproducibility.

## Conclusion

The current graph is already substantial in scale, provenance, and automation. Its completion work is therefore best understood as targeted enrichment: aligning auxiliary classes with the ontology, materializing a small number of high-value benchmark instances, and refining selected query-sensitive entity types. This keeps the project faithful to the coursework brief while providing a clear path to stronger competency-question coverage.
