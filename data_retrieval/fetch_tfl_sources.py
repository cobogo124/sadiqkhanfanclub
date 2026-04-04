from __future__ import annotations
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import requests

DEFAULT_MODES = ("tube", "dlr", "overground", "elizabeth-line", "bus")

def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]

def snapshot_path_for(repo_root_path: Path, snapshot_date: str, category: str, filename: str) -> Path:
    return repo_root_path / "downloads" / "raw" / snapshot_date / category / filename

def build_core_requests() -> list[dict]:
    modes = ",".join(DEFAULT_MODES)
    return [
        {"name": "all_lines", "url": f"https://api.tfl.gov.uk/Line/Mode/{modes}", "kind": "json", "cat": "core", "file": "all_lines.json"},
        {"name": "step_free_guide", "url": "https://tfl.gov.uk/cdn/static/cms/documents/step-free-tube-guide-map.pdf", "kind": "binary", "cat": "textual", "file": "step-free-tube-guide-map.pdf"},
        {"name": "overground_operator", "url": "https://tfl.gov.uk/corporate/transparency/freedom-of-information/foi-request-detail?referenceId=FOI-1487-1819", "kind": "text", "cat": "textual", "file": "overground_operator.html"}
    ]

def fetch_tfl_snapshot():
    snapshot_date = datetime.now().date().isoformat()
    repo = repo_root()
    manifest = []
    session = requests.Session()

    # 1. Fetch Core Data
    for req in build_core_requests():
        dest = snapshot_path_for(repo, snapshot_date, req['cat'], req['file'])
        dest.parent.mkdir(parents=True, exist_ok=True)
        resp = session.get(req['url'])
        if req['kind'] == "json": dest.write_text(json.dumps(resp.json(), indent=2))
        elif req['kind'] == "text": dest.write_text(resp.text)
        else: dest.write_bytes(resp.content)
        manifest.append({"name": req['name'], "url": req['url'], "retrieved_at": datetime.now(timezone.utc).isoformat(), "category": req['cat'], "filename": str(dest.relative_to(repo))})

    # 2. Fetch Line & Stop Specifics
    all_lines = json.loads(snapshot_path_for(repo, snapshot_date, "core", "all_lines.json").read_text())
    for line in all_lines:
        lid = line["id"]
        # Sequences (for CQ 15 - Order)
        s_url = f"https://api.tfl.gov.uk/Line/{lid}/Route/Sequence/all"
        s_dest = snapshot_path_for(repo, snapshot_date, "route_sequences", f"{lid}.json")
        s_dest.parent.mkdir(parents=True, exist_ok=True)
        s_dest.write_text(json.dumps(session.get(s_url).json(), indent=2))
        
        # StopPoints (for facilities)
        p_url = f"https://api.tfl.gov.uk/Line/{lid}/StopPoints"
        p_dest = snapshot_path_for(repo, snapshot_date, "line_stop_points", f"{lid}.json")
        p_dest.parent.mkdir(parents=True, exist_ok=True)
        p_dest.write_text(json.dumps(session.get(p_url).json(), indent=2))

    # Save Manifest
    m_path = snapshot_path_for(repo, snapshot_date, "meta", "source_manifest.json")
    m_path.parent.mkdir(parents=True, exist_ok=True)
    m_path.write_text(json.dumps(manifest, indent=2))
    return {"snapshot_date": snapshot_date, "source_count": len(manifest)}