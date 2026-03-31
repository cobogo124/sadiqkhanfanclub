from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


load_dotenv()

TFL_KEY = os.getenv("TFL_KEY")
DEFAULT_MODES = ("tube", "dlr", "overground", "elizabeth-line", "bus")
DEFAULT_TIMEOUT = 60
MAX_RETRIES = 5


@dataclass(frozen=True)
class SourceRequest:
    name: str
    url: str
    kind: str
    category: str
    filename: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def snapshot_path_for(repo_root_path: Path, snapshot_date: str, category: str, filename: str) -> Path:
    return repo_root_path / "downloads" / "raw" / snapshot_date / category / filename


def build_core_source_requests() -> list[SourceRequest]:
    modes = ",".join(DEFAULT_MODES)
    return [
        SourceRequest(
            name="all_lines",
            url=f"https://api.tfl.gov.uk/Line/Mode/{modes}",
            kind="json",
            category="core",
            filename="all_lines.json",
        ),
        SourceRequest(
            name="step_free_guide",
            url="https://tfl.gov.uk/cdn/static/cms/documents/step-free-tube-guide-map.pdf",
            kind="binary",
            category="textual",
            filename="step-free-tube-guide-map.pdf",
        ),
        SourceRequest(
            name="overground_operator_page",
            url="https://tfl.gov.uk/corporate/transparency/freedom-of-information/foi-request-detail?referenceId=FOI-1487-1819",
            kind="text",
            category="textual",
            filename="overground_operator_page.html",
        ),
    ]


def request_params() -> dict[str, str]:
    return {"app_key": TFL_KEY} if TFL_KEY else {}


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "sadiqkhanfanclub-tfl-ingestion/1.0 (+https://github.com/)",
            "Accept": "*/*",
        }
    )
    return session


def fetch_payload(session: requests.Session, request: SourceRequest) -> tuple[Any, str]:
    for attempt in range(1, MAX_RETRIES + 1):
        response = session.get(request.url, params=request_params(), timeout=DEFAULT_TIMEOUT)
        try:
            response.raise_for_status()
            if request.kind == "json":
                return response.json(), response.headers.get("content-type", "application/json")
            if request.kind == "text":
                return response.text, response.headers.get("content-type", "text/html")
            return response.content, response.headers.get("content-type", "application/octet-stream")
        except requests.HTTPError:
            if getattr(response, "status_code", None) != 429 or attempt == MAX_RETRIES:
                raise
            retry_after = response.headers.get("Retry-After")
            wait_seconds = float(retry_after) if retry_after else min(2 ** (attempt - 1), 8)
            time.sleep(wait_seconds)
    raise RuntimeError(f"Failed to fetch payload for {request.url}")


def write_payload(destination: Path, payload: Any, kind: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if kind == "json":
        destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return
    if kind == "text":
        destination.write_text(payload, encoding="utf-8")
        return
    destination.write_bytes(payload)


def save_request(
    session: requests.Session,
    repo_root_path: Path,
    snapshot_date: str,
    request: SourceRequest,
) -> dict[str, Any]:
    retrieved_at = datetime.now(timezone.utc).isoformat()
    destination = snapshot_path_for(repo_root_path, snapshot_date, request.category, request.filename)
    if destination.exists():
        content_type = {
            "json": "application/json",
            "text": "text/html",
            "binary": "application/octet-stream",
        }[request.kind]
    else:
        payload, content_type = fetch_payload(session, request)
        write_payload(destination, payload, request.kind)
    return {
        "name": request.name,
        "url": request.url,
        "category": request.category,
        "kind": request.kind,
        "filename": str(destination.relative_to(repo_root_path)),
        "retrieved_at": retrieved_at,
        "content_type": content_type,
    }


def line_request(line_id: str, category: str, suffix: str) -> SourceRequest:
    return SourceRequest(
        name=f"{category}_{line_id}",
        url=f"https://api.tfl.gov.uk/Line/{line_id}/{suffix}",
        kind="json",
        category=category,
        filename=f"{line_id}.json",
    )


def needs_stop_point_snapshot(mode_name: str) -> bool:
    return mode_name != "bus"


def stop_request(stop_id: str) -> SourceRequest:
    return SourceRequest(
        name=f"stop_{stop_id}",
        url=f"https://api.tfl.gov.uk/StopPoint/{stop_id}",
        kind="json",
        category="stop_points",
        filename=f"{stop_id}.json",
    )


def focus_search_requests() -> list[SourceRequest]:
    return [
        SourceRequest(
            name="search_kings_cross_st_pancras",
            url="https://api.tfl.gov.uk/StopPoint/Search/King%27s%20Cross%20St%20Pancras",
            kind="json",
            category="search",
            filename="kings_cross_st_pancras.json",
        ),
        SourceRequest(
            name="search_stratford",
            url="https://api.tfl.gov.uk/StopPoint/Search/Stratford",
            kind="json",
            category="search",
            filename="stratford.json",
        ),
        SourceRequest(
            name="search_trafalgar_square",
            url="https://api.tfl.gov.uk/StopPoint/Search/Trafalgar%20Square",
            kind="json",
            category="search",
            filename="trafalgar_square.json",
        ),
    ]


def unique_station_like_ids(stop_points_by_line: dict[str, list[dict[str, Any]]], route_sequences: dict[str, dict[str, Any]]) -> list[str]:
    station_ids: set[str] = set()
    for stops in stop_points_by_line.values():
        for stop in stops:
            modes = stop.get("modes", [])
            stop_type = (stop.get("stopType") or "").lower()
            if modes and modes != ["bus"]:
                station_ids.add(stop.get("id"))
                top_parent = stop.get("topMostParentId")
                if top_parent:
                    station_ids.add(top_parent)
            elif "station" in stop_type or "interchange" in stop_type:
                station_ids.add(stop.get("topMostParentId") or stop.get("id"))

    for sequence in route_sequences.values():
        if sequence.get("mode") == "bus":
            continue
        for stop in sequence.get("stations", []):
            if stop.get("id"):
                station_ids.add(stop["id"])
            top_parent = stop.get("topMostParentId")
            if top_parent:
                station_ids.add(top_parent)
    return sorted(stop_id for stop_id in station_ids if stop_id)


def fetch_tfl_snapshot(snapshot_date: str | None = None, pause_seconds: float = 0.05) -> dict[str, Any]:
    snapshot_date = snapshot_date or datetime.now().date().isoformat()
    repo = repo_root()
    manifest: list[dict[str, Any]] = []
    session = build_session()

    core_requests = build_core_source_requests()
    for request in core_requests:
        manifest.append(save_request(session, repo, snapshot_date, request))
        time.sleep(pause_seconds)

    all_lines_path = snapshot_path_for(repo, snapshot_date, "core", "all_lines.json")
    all_lines = json.loads(all_lines_path.read_text(encoding="utf-8"))
    route_sequences: dict[str, dict[str, Any]] = {}
    stop_points_by_line: dict[str, list[dict[str, Any]]] = {}

    rail_modes = {"tube", "dlr", "overground", "elizabeth-line"}
    rail_line_ids = [line["id"] for line in all_lines if line.get("modeName") in rail_modes]

    for line in all_lines:
        line_id = line["id"]
        sequence_request = line_request(line_id, "route_sequences", "Route/Sequence/all")
        manifest.append(save_request(session, repo, snapshot_date, sequence_request))
        route_sequences[line_id] = json.loads(
            snapshot_path_for(repo, snapshot_date, "route_sequences", f"{line_id}.json").read_text(encoding="utf-8")
        )
        time.sleep(pause_seconds)

        if needs_stop_point_snapshot(line.get("modeName", "")):
            stop_request_for_line = line_request(line_id, "line_stop_points", "StopPoints")
            manifest.append(save_request(session, repo, snapshot_date, stop_request_for_line))
            stop_points_by_line[line_id] = json.loads(
                snapshot_path_for(repo, snapshot_date, "line_stop_points", f"{line_id}.json").read_text(encoding="utf-8")
            )
            time.sleep(pause_seconds)
        else:
            stop_points_by_line[line_id] = []

        if line_id in rail_line_ids:
            status_request = line_request(line_id, "line_statuses", "Status")
            manifest.append(save_request(session, repo, snapshot_date, status_request))
            time.sleep(pause_seconds)

    for request in focus_search_requests():
        manifest.append(save_request(session, repo, snapshot_date, request))
        time.sleep(pause_seconds)

    for stop_id in unique_station_like_ids(stop_points_by_line, route_sequences):
        manifest.append(save_request(session, repo, snapshot_date, stop_request(stop_id)))
        time.sleep(pause_seconds)

    manifest_path = snapshot_path_for(repo, snapshot_date, "meta", "source_manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    summary = {"snapshot_date": snapshot_date, "manifest_path": str(manifest_path), "source_count": len(manifest)}
    summary_path = snapshot_path_for(repo, snapshot_date, "meta", "summary.json")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    summary = fetch_tfl_snapshot()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
