from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from rdflib import DCTERMS, Graph, Literal, Namespace, RDF, RDFS, URIRef

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from data_retrieval.fetch_tfl_sources import fetch_tfl_snapshot, repo_root, snapshot_path_for
from data_retrieval.tfl_transform import (
    bool_from_tfl_value,
    classify_line,
    classify_stop,
    extract_overground_operator,
    extract_step_free_note,
    facility_lookup,
    parse_step_free_guide,
    split_zone_string,
    uri_safe_fragment,
)


LT = Namespace("http://kcl.ac.uk/ontology/london-transport#")
GTFS = Namespace("http://vocab.gtfs.org/terms#")

MODE_URIS = {
    "tube": LT.underground_mode,
    "bus": LT.bus_mode,
    "dlr": LT.dlr_mode,
    "overground": LT.overground_mode,
    "elizabeth-line": LT.elizabeth_line_mode,
}

MODE_CLASSES = {
    "tube": LT.UndergroundMode,
    "bus": LT.BusMode,
    "dlr": LT.DLRMode,
    "overground": LT.OvergroundMode,
    "elizabeth-line": LT.ElizabethLineMode,
}

MODE_LABELS = {
    "tube": "Underground",
    "bus": "Bus",
    "dlr": "DLR",
    "overground": "Overground",
    "elizabeth-line": "Elizabeth line",
}

LINE_COLOURS = {
    "bakerloo": "#B36305",
    "central": "#E32017",
    "circle": "#FFD300",
    "district": "#00782A",
    "hammersmith-city": "#F3A9BB",
    "jubilee": "#A0A5A9",
    "metropolitan": "#9B0056",
    "northern": "#000000",
    "piccadilly": "#003688",
    "victoria": "#0098D4",
    "waterloo-city": "#95CDBA",
    "lioness": "#FDBB30",
    "mildmay": "#0067AD",
    "windrush": "#EF7B10",
    "weaver": "#9B0058",
    "suffragette": "#00A0A8",
    "liberty": "#616161",
    "elizabeth": "#6950A1",
}


def latest_snapshot_date(download_root: Path) -> str | None:
    if not download_root.exists():
        return None
    candidates = sorted(path.name for path in download_root.iterdir() if path.is_dir())
    return candidates[-1] if candidates else None


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_snapshot(snapshot_date: str | None = None) -> tuple[Path, list[dict[str, Any]]]:
    repo = repo_root()
    raw_root = repo / "downloads" / "raw"
    snapshot_date = snapshot_date or latest_snapshot_date(raw_root)
    if snapshot_date is None:
        fetch_tfl_snapshot()
        snapshot_date = latest_snapshot_date(raw_root)
    if snapshot_date is None:
        raise RuntimeError("No TfL snapshot is available.")
    snapshot_dir = raw_root / snapshot_date
    manifest = load_json(snapshot_dir / "meta" / "source_manifest.json")
    return snapshot_dir, manifest


def build_source_manifest(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "name": row["name"],
            "url": row["url"],
            "retrieved_at": row["retrieved_at"],
            "category": row.get("category", "unknown"),
            "filename": row.get("filename"),
        }
        for row in source_rows
    ]


def _is_night_service(line: dict[str, Any], status_payload: list[dict[str, Any]] | None) -> bool:
    if line.get("modeName") == "bus" and line["id"].lower().startswith("n"):
        return True
    line_service_types = line.get("serviceTypes", [])
    if any(item.get("name", "").lower() == "night" for item in line_service_types):
        return True
    if status_payload:
        for status_line in status_payload:
            if any(item.get("name", "").lower() == "night" for item in status_line.get("serviceTypes", [])):
                return True
    return False


def _collect_termini(route_sequence: dict[str, Any]) -> set[str]:
    termini: set[str] = set()
    for sequence in route_sequence.get("stopPointSequences", []):
        stop_points = sequence.get("stopPoint", [])
        if stop_points:
            termini.add(stop_points[0]["id"])
            termini.add(stop_points[-1]["id"])
    return termini


def _collect_line_stop_ids(route_sequence: dict[str, Any], line_stop_points: list[dict[str, Any]]) -> set[str]:
    stop_ids = {stop["id"] for stop in line_stop_points if stop.get("id")}
    for sequence in route_sequence.get("stopPointSequences", []):
        stop_ids.update(stop["id"] for stop in sequence.get("stopPoint", []) if stop.get("id"))
    for station in route_sequence.get("stations", []):
        if station.get("id"):
            stop_ids.add(station["id"])
    return stop_ids


def _build_stop_seed_map(snapshot_dir: Path, lines: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, set[str]], dict[str, set[str]]]:
    stop_seed_map: dict[str, dict[str, Any]] = {}
    line_to_stop_ids: dict[str, set[str]] = {}
    line_to_termini: dict[str, set[str]] = {}
    for line in lines:
        line_id = line["id"]
        route_sequence = load_json(snapshot_dir / "route_sequences" / f"{line_id}.json")
        line_stop_points_path = snapshot_dir / "line_stop_points" / f"{line_id}.json"
        line_stop_points = load_json(line_stop_points_path) if line_stop_points_path.exists() else []
        line_to_stop_ids[line_id] = _collect_line_stop_ids(route_sequence, line_stop_points)
        line_to_termini[line_id] = _collect_termini(route_sequence)

        for stop in line_stop_points:
            stop_id = stop.get("id")
            if not stop_id:
                continue
            seed = stop_seed_map.setdefault(stop_id, {"raw_stops": [], "line_ids": set()})
            seed["raw_stops"].append(stop)
            seed["line_ids"].add(line_id)

        for station in route_sequence.get("stations", []):
            stop_id = station.get("id")
            if not stop_id:
                continue
            seed = stop_seed_map.setdefault(stop_id, {"raw_stops": [], "line_ids": set()})
            seed["raw_stops"].append(station)
            seed["line_ids"].add(line_id)

        if not line_stop_points:
            for sequence in route_sequence.get("stopPointSequences", []):
                for stop in sequence.get("stopPoint", []):
                    stop_id = stop.get("id")
                    if not stop_id:
                        continue
                    seed = stop_seed_map.setdefault(stop_id, {"raw_stops": [], "line_ids": set()})
                    seed["raw_stops"].append(stop)
                    seed["line_ids"].add(line_id)

    return stop_seed_map, line_to_stop_ids, line_to_termini


def normalise_records(snapshot_dir: Path, manifest: list[dict[str, Any]]) -> dict[str, Any]:
    lines = load_json(snapshot_dir / "core" / "all_lines.json")
    stop_seed_map, line_to_stop_ids, line_to_termini = _build_stop_seed_map(snapshot_dir, lines)

    step_free_pdf = (snapshot_dir / "textual" / "step-free-tube-guide-map.pdf").read_bytes()
    step_free_text = parse_step_free_guide(step_free_pdf)
    overground_page = (snapshot_dir / "textual" / "overground_operator_page.html").read_text(encoding="utf-8")
    overground_operator = extract_overground_operator(overground_page) or "Arriva Rail London"

    line_records: list[dict[str, Any]] = []
    operators = [
        {
            "id": uri_safe_fragment(overground_operator),
            "name": overground_operator,
            "source": "https://tfl.gov.uk/corporate/transparency/freedom-of-information/foi-request-detail?referenceId=FOI-1487-1819",
        }
    ]

    for line in lines:
        line_id = line["id"]
        status_path = snapshot_dir / "line_statuses" / f"{line_id}.json"
        status_payload = load_json(status_path) if status_path.exists() else None
        is_night_service = _is_night_service(line, status_payload)
        line_records.append(
            {
                "id": line_id,
                "name": line.get("name", line_id),
                "modeName": line.get("modeName"),
                "line_class": classify_line(line.get("modeName", ""), line_id, is_night_service),
                "is_night_service": is_night_service,
                "stop_ids": sorted(line_to_stop_ids.get(line_id, set())),
                "terminus_ids": sorted(line_to_termini.get(line_id, set())),
                "operator_ids": [uri_safe_fragment(overground_operator)] if line.get("modeName") == "overground" else [],
                "line_colour": LINE_COLOURS.get(line_id),
                "source_urls": [
                    f"https://api.tfl.gov.uk/Line/{line_id}/Route/Sequence/all",
                    f"https://api.tfl.gov.uk/Line/{line_id}/StopPoints",
                ],
            }
        )

    stop_records: list[dict[str, Any]] = []
    for stop_id, seed in stop_seed_map.items():
        detail_path = snapshot_dir / "stop_points" / f"{stop_id}.json"
        detail = load_json(detail_path) if detail_path.exists() else None
        merged = detail or seed["raw_stops"][0]
        additional_properties = facility_lookup((detail or {}).get("additionalProperties"))
        name = merged.get("commonName") or merged.get("name") or stop_id
        line_ids = sorted(seed["line_ids"])
        stop_records.append(
            {
                "id": stop_id,
                "name": name,
                "stop_class": classify_stop(merged.get("modes", []), merged.get("stopType", ""), stop_id in {tid for ids in line_to_termini.values() for tid in ids}),
                "modes": merged.get("modes", []),
                "zones": split_zone_string(merged.get("zone") or additional_properties.get("Zone")),
                "line_ids": line_ids,
                "has_public_toilets": bool_from_tfl_value(additional_properties.get("Toilets")),
                "has_car_parking": bool_from_tfl_value(additional_properties.get("Car park")),
                "has_wifi": bool_from_tfl_value(additional_properties.get("WiFi")),
                "is_step_free": bool(extract_step_free_note(name, step_free_text)),
                "step_free_access_note": extract_step_free_note(name, step_free_text),
                "lat": merged.get("lat"),
                "lon": merged.get("lon"),
                "sources": [f"https://api.tfl.gov.uk/StopPoint/{stop_id}"] if detail else [],
            }
        )

    return {"lines": line_records, "stops": stop_records, "operators": operators, "sources": manifest}


def ensure_mode_individual(graph: Graph, mode_name: str) -> URIRef | None:
    mode_uri = MODE_URIS.get(mode_name)
    mode_class = MODE_CLASSES.get(mode_name)
    mode_label = MODE_LABELS.get(mode_name)
    if not (mode_uri and mode_class and mode_label):
        return None
    graph.add((mode_uri, RDF.type, mode_class))
    graph.add((mode_uri, RDFS.label, Literal(mode_label)))
    return mode_uri


def build_graph_from_records(records: dict[str, Any]) -> Graph:
    graph = Graph()
    graph.bind("lt", LT)
    graph.bind("gtfs", GTFS)
    graph.bind("dcterms", DCTERMS)

    for operator in records.get("operators", []):
        operator_uri = LT[f"operator_{operator['id']}"]
        graph.add((operator_uri, RDF.type, LT.TransportOperator))
        graph.add((operator_uri, RDFS.label, Literal(operator["name"])))
        graph.add((operator_uri, DCTERMS.source, Literal(operator["source"])))

    for line in records.get("lines", []):
        line_uri = LT[f"line_{uri_safe_fragment(line['id'])}"]
        line_class = line.get("line_class") or classify_line(line.get("modeName", ""), line["id"], line.get("is_night_service", False))
        graph.add((line_uri, RDF.type, LT[line_class]))
        if line_class == "NightTubeLine":
            graph.add((line_uri, RDF.type, LT.TubeLine))
        if line_class == "NightBusRoute":
            graph.add((line_uri, RDF.type, LT.BusRoute))
        graph.add((line_uri, LT.lineId, Literal(line["id"])))
        graph.add((line_uri, LT.lineName, Literal(line["name"])))
        graph.add((line_uri, LT.isNightService, Literal(line.get("is_night_service", False))))
        if line.get("line_colour"):
            graph.add((line_uri, LT.lineColour, Literal(line["line_colour"])))
        mode_uri = ensure_mode_individual(graph, line["modeName"])
        if mode_uri is not None:
            graph.add((line_uri, LT.servesMode, mode_uri))
        for operator_id in line.get("operator_ids", []):
            graph.add((line_uri, LT.operatedBy, LT[f"operator_{operator_id}"]))
        for source_url in line.get("source_urls", []):
            graph.add((line_uri, DCTERMS.source, Literal(source_url)))

    for zone_number in {zone for stop in records.get("stops", []) for zone in stop.get("zones", [])}:
        zone_uri = LT[f"zone_{zone_number}"]
        graph.add((zone_uri, RDF.type, LT.FareZone))
        graph.add((zone_uri, LT.zoneNumber, Literal(int(zone_number))))

    for stop in records.get("stops", []):
        stop_uri = LT[f"stop_{stop['id']}"]
        stop_class = stop.get("stop_class", "TransitStop")
        graph.add((stop_uri, RDF.type, LT[stop_class]))
        graph.add((stop_uri, LT.stopName, Literal(stop["name"])))
        graph.add((stop_uri, LT.naptanId, Literal(stop["id"])))
        graph.add((stop_uri, LT.hasPublicToilets, Literal(stop.get("has_public_toilets", False))))
        graph.add((stop_uri, LT.hasCarParking, Literal(stop.get("has_car_parking", False))))
        graph.add((stop_uri, LT.hasWifi, Literal(stop.get("has_wifi", False))))
        graph.add((stop_uri, LT.isStepFree, Literal(stop.get("is_step_free", False))))
        if stop.get("step_free_access_note"):
            graph.add((stop_uri, LT.stepFreeAccessNote, Literal(stop["step_free_access_note"])))
        for zone in stop.get("zones", []):
            graph.add((stop_uri, LT.inFareZone, LT[f"zone_{zone}"]))
        for mode_name in stop.get("modes", []):
            mode_uri = ensure_mode_individual(graph, mode_name)
            if mode_uri is not None:
                graph.add((stop_uri, LT.hasAvailableMode, mode_uri))
        for line_id in stop.get("line_ids", []):
            line_uri = LT[f"line_{uri_safe_fragment(line_id)}"]
            graph.add((line_uri, LT.hasStop, stop_uri))
            graph.add((stop_uri, LT.isServedBy, line_uri))
        if stop.get("lat") is not None and stop.get("lon") is not None:
            geo_uri = LT[f"geo_{stop['id']}"]
            graph.add((geo_uri, RDF.type, LT.GeoPoint))
            graph.add((geo_uri, LT.latitude, Literal(stop["lat"])))
            graph.add((geo_uri, LT.longitude, Literal(stop["lon"])))
            graph.add((stop_uri, LT.hasCoordinates, geo_uri))
        for source_url in stop.get("sources", []):
            graph.add((stop_uri, DCTERMS.source, Literal(source_url)))

    for line in records.get("lines", []):
        line_uri = LT[f"line_{uri_safe_fragment(line['id'])}"]
        for terminus_id in line.get("terminus_ids", []):
            graph.add((line_uri, LT.hasTerminus, LT[f"stop_{terminus_id}"]))

    return graph


def build_gtfs_alignment_graph() -> Graph:
    graph = Graph()
    graph.bind("lt", LT)
    graph.bind("gtfs", GTFS)
    graph.add((LT.TfLLine, RDFS.subClassOf, GTFS.Route))
    graph.add((LT.TransitStop, RDFS.subClassOf, GTFS.Stop))
    graph.add((LT.InterchangeStation, RDFS.subClassOf, GTFS.Station))
    graph.add((LT.TransportOperator, RDFS.subClassOf, GTFS.Agency))
    graph.add((LT.hasStop, RDFS.subPropertyOf, GTFS.stop))
    graph.add((LT.inFareZone, RDFS.subPropertyOf, GTFS.zone))
    return graph


def write_source_outputs(repo: Path, manifest_rows: list[dict[str, Any]]) -> None:
    generated_dir = repo / "docs" / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_source_manifest(manifest_rows)
    (generated_dir / "tfl-sources.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    lines = ["# TfL Sources", ""]
    for row in manifest:
        lines.append(f"- `{row['name']}`: {row['url']} ({row['retrieved_at']})")
    (generated_dir / "tfl-sources.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_graph_outputs(repo: Path, instance_graph: Graph, alignment_graph: Graph) -> None:
    ontology_graph = Graph().parse(repo / "ontologies" / "london-transport-ontology.ttl", format="turtle")
    instance_path = repo / "ontologies" / "london-transport-instances.ttl"
    kg_path = repo / "ontologies" / "london-transport-kg.ttl"
    protege_path = repo / "ontologies" / "london-transport-protege.owl"
    alignment_path = repo / "ontologies" / "gtfs-alignment.ttl"

    instance_graph.serialize(instance_path, format="turtle")
    alignment_graph.serialize(alignment_path, format="turtle")

    merged = ontology_graph + instance_graph
    merged.serialize(kg_path, format="turtle")
    merged.serialize(protege_path, format="pretty-xml")


def main(snapshot_date: str | None = None) -> None:
    repo = repo_root()
    snapshot_dir, manifest = load_snapshot(snapshot_date)
    records = normalise_records(snapshot_dir, manifest)
    instance_graph = build_graph_from_records(records)
    alignment_graph = build_gtfs_alignment_graph()
    write_graph_outputs(repo, instance_graph, alignment_graph)
    write_source_outputs(repo, manifest)
    print(
        json.dumps(
            {
                "snapshot_dir": str(snapshot_dir),
                "instances": len(instance_graph),
                "sources": len(manifest),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
