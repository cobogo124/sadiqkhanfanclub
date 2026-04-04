from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path
from typing import Any

from pypdf import PdfReader


def uri_safe_fragment(value: str) -> str:
    cleaned = value.strip().lower()
    cleaned = cleaned.replace("&", " and ")
    cleaned = re.sub(r"['’]", "", cleaned)
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned)
    return cleaned.strip("_")


def split_zone_string(zone_value: str | None) -> list[str]:
    if not zone_value:
        return []
    if zone_value.strip().upper() == "NA":
        return []
    return [part.strip() for part in re.split(r"[+/]", zone_value) if part.strip()]


def bool_from_tfl_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if value is None:
        return False

    text = str(value).strip().lower()
    if not text or text in {"no", "false", "none", "n/a", "na"}:
        return False
    if text in {"yes", "true"}:
        return True

    digits = [int(match) for match in re.findall(r"\d+", text)]
    if digits:
        return any(number > 0 for number in digits)

    return True


def facility_lookup(additional_properties: list[dict[str, Any]] | None) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for item in additional_properties or []:
        if item.get("category") not in {"Facility", "Accessibility", "Geo"}:
            continue
        key = item.get("key")
        value = item.get("value")
        if key:
            lookup[key] = value
    return lookup


def classify_line(mode_name: str, line_id: str, is_night_service: bool) -> str:
    if mode_name == "tube":
        return "NightTubeLine" if is_night_service else "TubeLine"
    if mode_name == "bus":
        return "NightBusRoute" if line_id.lower().startswith("n") else "BusRoute"
    if mode_name == "dlr":
        return "DLRLine"
    if mode_name == "overground":
        return "OvergroundLine"
    if mode_name == "elizabeth-line":
        return "ElizabethLine"
    return "TfLLine"


def classify_stop(modes: list[str], stop_type: str, is_terminus: bool = False) -> str:
    stop_type_lower = (stop_type or "").lower()
    modes_set = set(modes or [])
    if is_terminus and modes_set == {"bus"}:
        return "BusTerminus"
    if len(modes_set) > 1 or "interchange" in stop_type_lower:
        return "InterchangeStation"
    if modes_set == {"tube"} or "metrostation" in stop_type_lower:
        return "TubeStation"
    if modes_set == {"dlr"}:
        return "DLRStation"
    if modes_set == {"overground"}:
        return "OvergroundStation"
    if modes_set == {"elizabeth-line"}:
        return "ElizabethLineStation"
    if modes_set == {"bus"}:
        return "BusStop"
    return "TransitStop"


def parse_step_free_guide(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    # Page 1 is the map and creates noisy matches. The useful station index starts later.
    return "\n".join((page.extract_text() or "") for page in reader.pages[1:])


def _station_name_patterns(station_name: str) -> list[str]:
    base = station_name.replace(" Underground Station", "").replace(" DLR Station", "").replace(" Rail Station", "")
    patterns = {base, base.replace("St.", "St"), base.replace("&", "and")}
    return [pattern for pattern in patterns if pattern]


def extract_step_free_note(station_name: str, step_free_index_text: str) -> str | None:
    for pattern in _station_name_patterns(station_name):
        match = re.search(re.escape(pattern), step_free_index_text, flags=re.IGNORECASE)
        if not match:
            continue
        after = step_free_index_text[match.start() : match.start() + 900]
        next_entry = re.search(r"\n[A-F]\d\s{2,}", after[5:])
        snippet = after[: next_entry.start() + 5] if next_entry else after
        return " ".join(snippet.split())
    return None


def extract_overground_operator(page_text: str) -> str | None:
    match = re.search(r"operated on our behalf by\s+([A-Z][A-Za-z ]+?)(?:\s*\(|,|\.)", page_text, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    if "Arriva Rail London" in page_text:
        return "Arriva Rail London"
    return None
