from pathlib import Path


def test_readme_mentions_how_to_build_the_generated_kg() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "python3 data_retrieval/fetch_tfl_sources.py" in readme
    assert "python3 data_retrieval/build_tfl_ontology.py" in readme
