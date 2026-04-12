from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "target"


def collection_method_hint(access_type: str) -> str:
    mapping = {
        "pdf_extraction": "direct_download_or_pdf",
        "web_portal": "portal_first",
        "api": "api",
        "api_access": "api",
        "direct_download": "direct_download",
        "file_download": "direct_download",
        "wfs": "wfs",
        "wms": "wms",
        "unknown": "manual_triage",
    }
    return mapping.get((access_type or "").strip().lower(), "manual_triage")


def handoff_status(item: dict[str, Any]) -> str:
    if not (item.get("url") or "").strip():
        return "blocked"
    if item.get("needs_review"):
        return "needs_review"
    if (item.get("access_type") or "").strip().lower() == "unknown":
        return "needs_review"
    return "ready"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def extract_usgs_site_no(value: str) -> str:
    text = value or ""
    explicit = re.search(r"USGS[-\s]?(\d{8,9})", text, flags=re.IGNORECASE)
    if explicit:
        return explicit.group(1)
    fallback = re.search(r"\b(0\d{7,8})\b", text)
    if fallback:
        return fallback.group(1)
    return ""


def extract_wqp_site_id(value: str) -> str:
    text = value or ""
    explicit = re.search(r"(USGS-\d{8,9})", text, flags=re.IGNORECASE)
    if explicit:
        return explicit.group(1).upper()
    site_no = extract_usgs_site_no(text)
    if site_no:
        return f"USGS-{site_no}"
    return ""


def canonicalize_start_url(item: dict[str, Any]) -> tuple[str, str]:
    url = (item.get("url") or "").strip()
    text = normalize_text(
        " ".join(
            [
                url,
                item.get("dataset_name") or "",
                item.get("title") or "",
                item.get("snippet") or "",
            ]
        )
    )
    domain = normalize_text(item.get("source_domain") or "")
    site_no = extract_usgs_site_no(text)
    site_id = extract_wqp_site_id(text)

    if domain == "catalog.data.gov" and "water quality measurements in savannah river" in text:
        return "https://www.sciencebase.gov/catalog/item/5f8746c182cebef40f1970e3?format=json", "direct_download"

    if domain in {"catalog.data.gov", "epa.gov"} and "echo" in text:
        return "https://echo.epa.gov/tools/data-downloads", "web_portal"

    if domain == "open.clemson.edu" and "water quality study of savannah river basin" in text:
        return "https://open.clemson.edu/cgi/viewcontent.cgi?article=1000&context=water-resources", "direct_download"

    if domain == "epd.georgia.gov" and "water quality in georgia" in text:
        return "https://epd.georgia.gov/https%3A/epd.georgia.gov/assessment/water-quality-georgia", "web_portal"

    if domain == "waterqualitydata.us":
        normalized_url = normalize_text(url).rstrip("/")
        if "water quality data sites in georgia" in text or normalized_url.endswith("provider/nwis/usgs-ga"):
            station_url = (
                "https://www.waterqualitydata.us/data/Station/search"
                "?organization=USGS-GA&mimeType=csv&zip=no&providers=NWIS"
            )
            return station_url, "direct_download"
        if site_id:
            result_url = (
                "https://www.waterqualitydata.us/data/Result/search"
                f"?siteid={site_id}&mimeType=csv&zip=no&providers=NWIS"
            )
            return result_url, "direct_download"

    if domain == "waterdata.usgs.gov":
        if "water quality conditions in georgia" in text:
            return "https://waterdata.usgs.gov/ga/nwis/uv", "web_portal"
        if site_no:
            return f"https://waterdata.usgs.gov/monitoring-location/USGS-{site_no}", "web_portal"

    return url, item.get("access_type") or ""


def parse_temporal_coverage(value: str) -> tuple[str, str]:
    years = re.findall(r"(?:19|20)\d{2}", value or "")
    if not years:
        return "", ""
    if len(years) == 1:
        return years[0], years[0]
    return years[0], years[-1]


def infer_river_scope(item: dict[str, Any]) -> str:
    text = normalize_text(
        " ".join(
            [
                item.get("dataset_name") or "",
                item.get("title") or "",
                item.get("track_origin") or "",
                item.get("spatial_coverage") or "",
                item.get("snippet") or "",
            ]
        )
    )
    if any(term in text for term in ("calhoun falls", "above hartwell", "hartwell headwater")):
        return "mainstem_above_hartwell"
    if any(term in text for term in ("below hartwell", "hartwell to russell", "between hartwell and russell")):
        return "mainstem_between_hartwell_russell"
    if any(term in text for term in ("below russell", "between russell and thurmond", "russell to thurmond")):
        return "mainstem_between_russell_thurmond"
    if any(term in text for term in ("augusta", "below thurmond", "us 1", "thurmond downstream")):
        return "mainstem_below_thurmond_augusta"
    if any(term in text for term in ("hartwell", "russell", "thurmond")):
        return "reservoir_support"
    if any(term in text for term in ("echo", "attains", "npdes", "tmdl", "303(d)", "impairment", "pollut")):
        return "corridor_pressure"
    return "systemwide_mainstem"


def infer_source_family(item: dict[str, Any]) -> str:
    domain = normalize_text(item.get("source_domain") or "")
    if "usgs" in domain or "waterqualitydata.us" in domain:
        return "usgs_wqp"
    if "epa.gov" in domain or "echo." in domain:
        return "epa_pressure"
    if "usace" in domain:
        return "usace_operations"
    if "weather.gov" in domain or "noaa" in domain:
        return "noaa_nws"
    if "data.gov" in domain:
        return "data_gov"
    return "other"


def infer_priority(item: dict[str, Any]) -> str:
    track = normalize_text(item.get("track_origin") or "")
    text = normalize_text(
        " ".join(
            [
                item.get("dataset_name") or "",
                item.get("title") or "",
                item.get("track_origin") or "",
            ]
        )
    )
    if any(term in track for term in ("gap1_", "gap2_", "gap3_", "gap5_")):
        return "high"
    if "gap4_" in track:
        return "medium"
    if any(term in text for term in ("echo", "attains", "npdes", "tmdl", "gauge", "waterservices", "water quality")):
        return "high"
    return str(item.get("track_priority") or "medium")


def infer_notes_on_asymmetry(item: dict[str, Any], start_year: str, end_year: str) -> str:
    river_scope = infer_river_scope(item)
    notes: list[str] = []
    if river_scope in {"mainstem_below_thurmond_augusta", "reservoir_support"}:
        notes.append("Downstream or reservoir-support coverage may still be stronger than upstream mainstem parity.")
    if not start_year or not end_year:
        notes.append("Actual period of record still needs confirmation during collection.")
    else:
        try:
            if int(end_year) - int(start_year) + 1 < 20:
                notes.append(f"Returned coverage shorter than 20 years: {start_year}-{end_year}.")
        except ValueError:
            notes.append("Temporal coverage string requires manual review.")
    return " ".join(notes)


def domain_allowed(domain: str, profile: str) -> bool:
    if profile != "savannah-river-gapfill":
        return True
    normalized = normalize_text(domain)
    blocked_domains = {
        "des.sc.gov",
        "www.des.sc.gov",
        "riverapp.net",
        "snoflo.org",
        "en.wikipedia.org",
        "opennetzero.org",
        "geoaquawatch.org",
        "hsls.libguides.com",
        "wateringeorgia.com",
        "savannahwaterquality.com",
        "savannahrivercleanwater.org",
        "savannahriverkeeper.org",
        "data.cnra.ca.gov",
        "fedcenter.gov",
        "cwfnc.org",
        "core.ac.uk",
        "opennetzero.org",
        "phinizycenter.org",
    }
    if normalized in blocked_domains:
        return False
    allowed_domains = {
        "waterqualitydata.us",
        "waterdata.usgs.gov",
        "water.usgs.gov",
        "waterservices.usgs.gov",
        "echo.epa.gov",
        "epa.gov",
        "catalog.data.gov",
        "erddap.secoora.org",
        "open.clemson.edu",
        "epd.georgia.gov",
        "deq.nc.gov",
        "sas.usace.army.mil",
        "water.usace.army.mil",
        "hec.usace.army.mil",
        "nrc.gov",
    }
    return normalized in allowed_domains


def item_relevant(item: dict[str, Any], profile: str) -> bool:
    if profile != "savannah-river-gapfill":
        return True
    text = normalize_text(
        " ".join(
            [
                item.get("dataset_name") or "",
                item.get("title") or "",
                item.get("track_origin") or "",
                item.get("snippet") or "",
            ]
        )
    )
    negative = (
        "organization domain values",
        "water system number",
        "drinking water analysis",
        "betty's branch",
        "usgs-wi",
        "macroinvertebrate data - savannah river basin",
        "savannah river water quality data (1959-1964)",
        "savannah river site environmental report 2020",
        "reservoirs in the savannah river basin",
        "estuarine salinity zones, bathymetric data, and shoreline data for us coastal areas",
    )
    if any(term in text for term in negative):
        return False
    positive = (
        "savannah river",
        "hartwell",
        "russell",
        "thurmond",
        "augusta",
        "echo",
        "attains",
        "npdes",
        "tmdl",
        "waterservices",
        "water quality",
        "turbidity",
        "suspended sediment",
        "suspended solids",
        "usgs-021",
    )
    return any(term in text for term in positive)


def sort_key(row: dict[str, Any]) -> tuple[int, int, int]:
    priority_score = {"high": 0, "medium": 1, "low": 2}.get(row.get("priority", "medium"), 1)
    method_score = {"api": 0, "direct_download": 1, "portal_first": 2, "manual_triage": 3}.get(
        row.get("collection_method_hint", "manual_triage"),
        3,
    )
    review_score = 1 if row.get("needs_review") else 0
    return (priority_score, method_score, review_score)


def build_targets(ranked_datasets: list[dict[str, Any]], profile: str) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for item in ranked_datasets:
        if not domain_allowed(item.get("source_domain") or "", profile):
            continue
        if not item_relevant(item, profile):
            continue
        rank = int(item.get("rank") or len(targets) + 1)
        dataset_name = (item.get("dataset_name") or item.get("title") or f"target-{rank}").strip()
        source_name = (item.get("source_domain") or "").strip() or "unknown-source"
        start_year, end_year = parse_temporal_coverage(str(item.get("temporal_coverage") or ""))
        normalized_start_url, normalized_access_type = canonicalize_start_url(item)
        target = {
            "rank": rank,
            "source_name": source_name,
            "source_slug": f"{rank:02d}-{slugify(dataset_name)[:72]}",
            "dataset_name": dataset_name,
            "title": (item.get("title") or "").strip(),
            "start_url": normalized_start_url,
            "source_domain": source_name,
            "track_origin": item.get("track_origin") or "",
            "track_priority": item.get("track_priority") or "",
            "track_intent": item.get("track_intent") or "",
            "data_format": item.get("data_format") or "",
            "access_type": normalized_access_type,
            "access_notes": item.get("access_notes") or "",
            "temporal_coverage": item.get("temporal_coverage") or "",
            "spatial_coverage": item.get("spatial_coverage") or "",
            "key_parameters": item.get("key_parameters") or [],
            "needs_review": bool(item.get("needs_review")),
            "collection_method_hint": collection_method_hint(normalized_access_type),
            "handoff_status": handoff_status(item),
            "river_scope": infer_river_scope(item),
            "source_family": infer_source_family(item),
            "priority": infer_priority(item),
            "notes_on_asymmetry": infer_notes_on_asymmetry(item, start_year, end_year),
            "target_window_years": 20,
            "expected_period_start": start_year,
            "expected_period_end": end_year,
        }
        targets.append(target)
    ordered = sorted(targets, key=sort_key)
    for idx, row in enumerate(ordered, start=1):
        row["rank"] = idx
        row["source_slug"] = f"{idx:02d}-{slugify(row['dataset_name'])[:72]}"
    return ordered


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "rank",
        "source_name",
        "source_slug",
        "dataset_name",
        "title",
        "start_url",
        "source_domain",
        "track_origin",
        "track_priority",
        "track_intent",
        "data_format",
        "access_type",
        "access_notes",
        "temporal_coverage",
        "spatial_coverage",
        "key_parameters",
        "needs_review",
        "collection_method_hint",
        "handoff_status",
        "river_scope",
        "source_family",
        "priority",
        "notes_on_asymmetry",
        "target_window_years",
        "expected_period_start",
        "expected_period_end",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            serializable = dict(row)
            serializable["key_parameters"] = "|".join(serializable.get("key_parameters") or [])
            writer.writerow(serializable)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Harvester handoff files from a completed discovery run.")
    parser.add_argument("--run-dir", required=True, help="Path to the completed run directory.")
    parser.add_argument(
        "--profile",
        default="default",
        choices=["default", "savannah-river-gapfill"],
        help="Optional handoff profile for focused filtering and extra metadata.",
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    manifest_path = run_dir / "manifest.json"
    ranked_path = run_dir / "processing" / "03-ranked-datasets.json"

    if not manifest_path.exists():
        raise SystemExit(f"Manifest not found: {manifest_path}")
    if not ranked_path.exists():
        raise SystemExit(f"Ranked datasets file not found: {ranked_path}")

    manifest = load_json(manifest_path)
    ranked_payload = load_json(ranked_path)
    ranked_datasets = ranked_payload.get("ranked_datasets", [])

    if not ranked_datasets:
        raise SystemExit("No ranked datasets found; refusing to generate an empty Harvester handoff.")

    targets = build_targets(ranked_datasets, args.profile)
    processing_dir = run_dir / "processing"
    reports_dir = run_dir / "reports"
    processing_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    handoff_json_path = processing_dir / "04-harvester-handoff.json"
    handoff_csv_path = reports_dir / "harvester_targets.csv"

    payload = {
        "research_id": manifest.get("research_id"),
        "generated_at": manifest.get("generated_at"),
        "base_query": manifest.get("base_query"),
        "run_dir": str(run_dir),
        "source_manifest": str(manifest_path),
        "source_ranked_datasets": str(ranked_path),
        "target_count": len(targets),
        "ready_count": sum(1 for item in targets if item["handoff_status"] == "ready"),
        "needs_review_count": sum(1 for item in targets if item["handoff_status"] == "needs_review"),
        "blocked_count": sum(1 for item in targets if item["handoff_status"] == "blocked"),
        "profile": args.profile,
        "targets_by_river_scope": {
            scope: [item for item in targets if item["river_scope"] == scope]
            for scope in sorted({item["river_scope"] for item in targets})
        },
        "targets_by_source_family": {
            family: [item for item in targets if item["source_family"] == family]
            for family in sorted({item["source_family"] for item in targets})
        },
        "targets": targets,
    }

    handoff_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(handoff_csv_path, targets)

    print(f"Handoff JSON: {handoff_json_path}")
    print(f"Handoff CSV: {handoff_csv_path}")
    print(f"Targets: {len(targets)} | ready={payload['ready_count']} | review={payload['needs_review_count']} | blocked={payload['blocked_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
