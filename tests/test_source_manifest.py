from data_retrieval.build_tfl_ontology import build_source_manifest


def test_build_source_manifest_records_url_and_retrieval_time() -> None:
    manifest = build_source_manifest(
        [
            {
                "name": "all_lines",
                "url": "https://api.tfl.gov.uk/Line/Mode/tube,dlr,overground,elizabeth-line,bus",
                "retrieved_at": "2026-03-31T10:00:00Z",
                "category": "core",
            }
        ]
    )
    assert manifest[0]["name"] == "all_lines"
    assert manifest[0]["url"].startswith("https://api.tfl.gov.uk/Line/Mode/")
    assert manifest[0]["retrieved_at"] == "2026-03-31T10:00:00Z"
