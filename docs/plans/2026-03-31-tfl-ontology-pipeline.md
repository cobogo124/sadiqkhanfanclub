# TfL Ontology Population Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a repeatable TfL ingestion pipeline that fetches authoritative source data, generates ontology instances, aligns with GTFS, and produces coursework-ready Turtle outputs plus source manifests.

**Architecture:** The implementation will use an API-first pipeline with explicit fetch, normalize, and RDF materialization stages. The existing TBox remains the center of the knowledge graph, while GTFS provides additional transport-domain alignment and the generated ABox is emitted into separate Turtle artifacts.

**Tech Stack:** Python 3, requests, rdflib, pandas, pytest, TfL Unified API, NaPTAN fallback data, Turtle/OWL

---

### Task 1: Capture The Fetch Layer

**Files:**
- Create: `data_retrieval/fetch_tfl_sources.py`
- Test: `tests/test_fetch_tfl_sources.py`
- Modify: `requirements.txt`

**Step 1: Write the failing test**

```python
from pathlib import Path

from data_retrieval.fetch_tfl_sources import snapshot_path_for


def test_snapshot_path_for_uses_dated_raw_directory(tmp_path):
    result = snapshot_path_for(tmp_path, "2026-03-31", "lines", "tube.json")
    assert result == tmp_path / "downloads" / "raw" / "2026-03-31" / "lines" / "tube.json"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_fetch_tfl_sources.py::test_snapshot_path_for_uses_dated_raw_directory -v`
Expected: FAIL with import or missing function errors

**Step 3: Write minimal implementation**

```python
from pathlib import Path


def snapshot_path_for(repo_root: Path, snapshot_date: str, category: str, filename: str) -> Path:
    return repo_root / "downloads" / "raw" / snapshot_date / category / filename
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_fetch_tfl_sources.py::test_snapshot_path_for_uses_dated_raw_directory -v`
Expected: PASS

**Step 5: Commit**

```bash
git add requirements.txt tests/test_fetch_tfl_sources.py data_retrieval/fetch_tfl_sources.py
git commit -m "feat: add TfL fetch layer scaffolding"
```

### Task 2: Add Source Fetching For Core TfL Data

**Files:**
- Modify: `data_retrieval/fetch_tfl_sources.py`
- Modify: `tests/test_fetch_tfl_sources.py`

**Step 1: Write the failing test**

```python
def test_build_core_source_requests_includes_modes_and_key_station_queries():
    requests = build_core_source_requests()
    urls = {request.url for request in requests}
    assert "https://api.tfl.gov.uk/Line/Mode/tube,dlr,overground,elizabeth-line,bus" in urls
    assert "https://api.tfl.gov.uk/StopPoint/Search/Stratford" in urls
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_fetch_tfl_sources.py::test_build_core_source_requests_includes_modes_and_key_station_queries -v`
Expected: FAIL because `build_core_source_requests` is missing

**Step 3: Write minimal implementation**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class SourceRequest:
    name: str
    url: str


def build_core_source_requests() -> list[SourceRequest]:
    return [
        SourceRequest("all_lines", "https://api.tfl.gov.uk/Line/Mode/tube,dlr,overground,elizabeth-line,bus"),
        SourceRequest("search_stratford", "https://api.tfl.gov.uk/StopPoint/Search/Stratford"),
    ]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_fetch_tfl_sources.py::test_build_core_source_requests_includes_modes_and_key_station_queries -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_fetch_tfl_sources.py data_retrieval/fetch_tfl_sources.py
git commit -m "feat: define core TfL source requests"
```

### Task 3: Extend The Ontology For GTFS Alignment And Facilities

**Files:**
- Modify: `ontologies/london-transport-ontology.ttl`
- Test: `tests/test_ontology_contract.py`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_ontology_declares_gtfs_alignment_and_facility_properties():
    ontology = Path("ontologies/london-transport-ontology.ttl").read_text(encoding="utf-8")
    assert "@prefix gtfs:" in ontology
    assert ":hasPublicToilets" in ontology
    assert ":hasCarParking" in ontology
    assert "rdfs:subPropertyOf gtfs:stop" in ontology
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_ontology_contract.py::test_ontology_declares_gtfs_alignment_and_facility_properties -v`
Expected: FAIL because those additions are not present yet

**Step 3: Write minimal implementation**

```ttl
@prefix gtfs:   <http://vocab.gtfs.org/terms#> .

:hasPublicToilets rdf:type owl:DatatypeProperty ;
    rdfs:domain :TransitStop ;
    rdfs:range xsd:boolean .

:hasCarParking rdf:type owl:DatatypeProperty ;
    rdfs:domain :TransitStop ;
    rdfs:range xsd:boolean .
```

Also add GTFS subclass and subproperty alignments to the relevant classes and properties.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_ontology_contract.py::test_ontology_declares_gtfs_alignment_and_facility_properties -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_ontology_contract.py ontologies/london-transport-ontology.ttl
git commit -m "feat: align ontology with GTFS and add facility predicates"
```

### Task 4: Build Normalization Helpers For TfL Payloads

**Files:**
- Create: `data_retrieval/tfl_transform.py`
- Test: `tests/test_tfl_transform.py`

**Step 1: Write the failing test**

```python
from data_retrieval.tfl_transform import split_zone_string


def test_split_zone_string_handles_boundary_zone_values():
    assert split_zone_string("2/3") == ["2", "3"]
    assert split_zone_string("1") == ["1"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_tfl_transform.py::test_split_zone_string_handles_boundary_zone_values -v`
Expected: FAIL because the module does not exist yet

**Step 3: Write minimal implementation**

```python
def split_zone_string(zone_value: str | None) -> list[str]:
    if not zone_value:
        return []
    return [part.strip() for part in zone_value.split("/") if part.strip() and part.strip() != "NA"]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_tfl_transform.py::test_split_zone_string_handles_boundary_zone_values -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_tfl_transform.py data_retrieval/tfl_transform.py
git commit -m "feat: add TfL normalization helpers"
```

### Task 5: Materialize RDF Instances And GTFS Alignment

**Files:**
- Create: `data_retrieval/build_tfl_ontology.py`
- Modify: `data_retrieval/tfl_transform.py`
- Test: `tests/test_build_tfl_ontology.py`

**Step 1: Write the failing test**

```python
from rdflib import Graph, Namespace

from data_retrieval.build_tfl_ontology import build_graph_from_records


LT = Namespace("http://kcl.ac.uk/ontology/london-transport#")


def test_build_graph_from_records_emits_line_stop_and_zone_triples():
    records = {
        "lines": [{"id": "victoria", "name": "Victoria", "modeName": "tube"}],
        "stations": [{"id": "940GZZLUGPK", "name": "Green Park Underground Station", "zone": "1", "lines": ["victoria"]}],
    }
    graph = build_graph_from_records(records)
    assert (LT.line_victoria, LT.lineName, None) in graph
    assert (LT.stop_940GZZLUGPK, LT.inFareZone, LT.zone_1) in graph
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_build_tfl_ontology.py::test_build_graph_from_records_emits_line_stop_and_zone_triples -v`
Expected: FAIL because the builder does not exist yet

**Step 3: Write minimal implementation**

```python
from rdflib import Graph, Literal, Namespace, RDF


LT = Namespace("http://kcl.ac.uk/ontology/london-transport#")


def build_graph_from_records(records: dict) -> Graph:
    graph = Graph()
    graph.bind("lt", LT)
    for line in records["lines"]:
        line_uri = LT[f"line_{line['id']}"]
        graph.add((line_uri, RDF.type, LT.TubeLine))
        graph.add((line_uri, LT.lineName, Literal(line["name"])))
    return graph
```

Then extend it to emit stops, zones, operators, GTFS alignment triples, facilities, Night service flags, and source links.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_build_tfl_ontology.py::test_build_graph_from_records_emits_line_stop_and_zone_triples -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_build_tfl_ontology.py data_retrieval/tfl_transform.py data_retrieval/build_tfl_ontology.py
git commit -m "feat: materialize TfL RDF instances"
```

### Task 6: Generate Source Manifest Outputs

**Files:**
- Modify: `data_retrieval/build_tfl_ontology.py`
- Create: `tests/test_source_manifest.py`

**Step 1: Write the failing test**

```python
from data_retrieval.build_tfl_ontology import build_source_manifest


def test_build_source_manifest_records_url_and_retrieval_time():
    manifest = build_source_manifest(
        [{"name": "all_lines", "url": "https://api.tfl.gov.uk/Line/Mode/tube,dlr,overground,elizabeth-line,bus", "retrieved_at": "2026-03-31T10:00:00Z"}]
    )
    assert manifest[0]["name"] == "all_lines"
    assert manifest[0]["url"].startswith("https://api.tfl.gov.uk/Line/Mode/")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_source_manifest.py::test_build_source_manifest_records_url_and_retrieval_time -v`
Expected: FAIL because the function does not exist yet

**Step 3: Write minimal implementation**

```python
def build_source_manifest(source_rows: list[dict]) -> list[dict]:
    return [
        {
            "name": row["name"],
            "url": row["url"],
            "retrieved_at": row["retrieved_at"],
        }
        for row in source_rows
    ]
```

Then extend it to write `docs/generated/tfl-sources.md` and `docs/generated/tfl-sources.json`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_source_manifest.py::test_build_source_manifest_records_url_and_retrieval_time -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_source_manifest.py data_retrieval/build_tfl_ontology.py
git commit -m "feat: generate source manifests for TfL pipeline"
```

### Task 7: Add End-To-End Verification For Competency Questions

**Files:**
- Create: `tests/test_competency_questions.py`
- Modify: `data_retrieval/build_tfl_ontology.py`

**Step 1: Write the failing test**

```python
from rdflib import Graph


def test_generated_graph_can_answer_baker_street_toilets_query():
    graph = Graph().parse("ontologies/london-transport-kg.ttl", format="turtle")
    query = '''
    PREFIX lt: <http://kcl.ac.uk/ontology/london-transport#>
    SELECT ?toilets WHERE {
      ?station lt:stopName "Baker Street Underground Station" ;
               lt:hasPublicToilets ?toilets .
    }
    '''
    rows = list(graph.query(query))
    assert rows
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_competency_questions.py::test_generated_graph_can_answer_baker_street_toilets_query -v`
Expected: FAIL until the generated graph exists and contains the facility triple

**Step 3: Write minimal implementation**

```python
def main() -> None:
    records = load_records()
    graph = build_graph_from_records(records)
    graph.serialize("ontologies/london-transport-kg.ttl", format="turtle")
```

Then complete the pipeline so the generated graph exists and includes competency-question coverage for the initial 10 questions.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_competency_questions.py::test_generated_graph_can_answer_baker_street_toilets_query -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_competency_questions.py data_retrieval/build_tfl_ontology.py ontologies/london-transport-kg.ttl
git commit -m "test: verify generated graph answers core competency queries"
```

### Task 8: Refresh Repository Documentation And Usage

**Files:**
- Modify: `README.md`
- Create: `docs/generated/tfl-sources.md`
- Create: `docs/generated/tfl-sources.json`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_readme_mentions_how_to_build_the_generated_kg():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "python3 data_retrieval/fetch_tfl_sources.py" in readme
    assert "python3 data_retrieval/build_tfl_ontology.py" in readme
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_readme_usage.py::test_readme_mentions_how_to_build_the_generated_kg -v`
Expected: FAIL because the build instructions are not documented yet

**Step 3: Write minimal implementation**

```markdown
# sadiqkhanfanclub

## Build

Run `python3 data_retrieval/fetch_tfl_sources.py`
Run `python3 data_retrieval/build_tfl_ontology.py`
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_readme_usage.py::test_readme_mentions_how_to_build_the_generated_kg -v`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md docs/generated/tfl-sources.md docs/generated/tfl-sources.json tests/test_readme_usage.py
git commit -m "docs: document TfL ontology build workflow"
```

## Final Verification

After all tasks:

1. Run `pytest -v`
2. Run `python3 data_retrieval/fetch_tfl_sources.py`
3. Run `python3 data_retrieval/build_tfl_ontology.py`
4. Run `pytest tests/test_competency_questions.py -v`
5. Inspect generated outputs:
   - `ontologies/london-transport-instances.ttl`
   - `ontologies/london-transport-kg.ttl`
   - `docs/generated/tfl-sources.md`
   - `docs/generated/tfl-sources.json`

## Implementation Notes

- Use `ontologies/gtfs.ttl` as the GTFS reference file.
- Keep `ontologies/sadiqkhanfanclub.ttl` untouched unless a later cleanup task explicitly addresses it.
- Treat TfL IDs as canonical for generated URIs to keep the build deterministic.
- Prefer fallbacks to official TfL text sources only when the API payload does not expose the needed value directly.
