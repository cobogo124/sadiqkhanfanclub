from pathlib import Path

import requests

from data_retrieval.fetch_tfl_sources import (
    SourceRequest,
    build_core_source_requests,
    fetch_payload,
    unique_station_like_ids,
    needs_stop_point_snapshot,
    save_request,
    snapshot_path_for,
)


def test_snapshot_path_for_uses_dated_raw_directory(tmp_path: Path) -> None:
    result = snapshot_path_for(tmp_path, "2026-03-31", "lines", "tube.json")
    assert result == tmp_path / "downloads" / "raw" / "2026-03-31" / "lines" / "tube.json"


def test_build_core_source_requests_includes_structured_and_text_sources() -> None:
    requests = build_core_source_requests()
    assert SourceRequest(
        name="all_lines",
        url="https://api.tfl.gov.uk/Line/Mode/tube,dlr,overground,elizabeth-line,bus",
        kind="json",
        category="core",
        filename="all_lines.json",
    ) in requests
    assert any(request.name == "step_free_guide" and request.kind == "binary" for request in requests)
    assert any(request.name == "overground_operator_page" and request.kind == "text" for request in requests)


def test_fetch_payload_retries_after_rate_limit() -> None:
    class FakeResponse:
        def __init__(self, status_code: int, payload: list[dict[str, str]]) -> None:
            self.status_code = status_code
            self._payload = payload
            self.headers = {"content-type": "application/json"}

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise requests.HTTPError(response=self)

        def json(self) -> list[dict[str, str]]:
            return self._payload

    class FakeSession:
        def __init__(self) -> None:
            self.calls = 0

        def get(self, *_args, **_kwargs) -> FakeResponse:
            self.calls += 1
            if self.calls == 1:
                return FakeResponse(429, [])
            return FakeResponse(200, [{"id": "victoria"}])

    payload, content_type = fetch_payload(
        FakeSession(),
        SourceRequest(
            name="all_lines",
            url="https://api.tfl.gov.uk/Line/Mode/tube,dlr,overground,elizabeth-line,bus",
            kind="json",
            category="core",
            filename="all_lines.json",
        ),
    )
    assert payload == [{"id": "victoria"}]
    assert content_type == "application/json"


def test_save_request_reuses_existing_snapshot_file(tmp_path: Path) -> None:
    request = SourceRequest(
        name="all_lines",
        url="https://api.tfl.gov.uk/Line/Mode/tube,dlr,overground,elizabeth-line,bus",
        kind="json",
        category="core",
        filename="all_lines.json",
    )
    destination = snapshot_path_for(tmp_path, "2026-03-31", "core", "all_lines.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text('[{"id": "victoria"}]', encoding="utf-8")

    class FakeSession:
        def get(self, *_args, **_kwargs) -> None:
            raise AssertionError("existing snapshot should be reused without another API call")

    row = save_request(FakeSession(), tmp_path, "2026-03-31", request)
    assert row["filename"] == "downloads/raw/2026-03-31/core/all_lines.json"
    assert row["kind"] == "json"


def test_bus_lines_do_not_need_redundant_stop_point_snapshots() -> None:
    assert needs_stop_point_snapshot("tube") is True
    assert needs_stop_point_snapshot("bus") is False


def test_unique_station_like_ids_ignores_bus_route_sequence_stations() -> None:
    route_sequences = {
        "1": {
            "mode": "bus",
            "stations": [
                {
                    "id": "490000020K",
                    "name": "Belsize Park Station",
                    "modes": ["bus"],
                    "stopType": "NaptanPublicBusCoachTram",
                    "topMostParentId": "490000020K",
                }
            ],
        },
        "victoria": {
            "mode": "tube",
            "stations": [
                {
                    "id": "940GZZLUGPK",
                    "name": "Green Park Underground Station",
                    "modes": ["tube"],
                    "stopType": "NaptanMetroStation",
                    "topMostParentId": "940GZZLUGPK",
                }
            ],
        },
    }
    stop_points_by_line = {"1": [], "victoria": []}
    assert unique_station_like_ids(stop_points_by_line, route_sequences) == ["940GZZLUGPK"]
