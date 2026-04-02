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


def build_targets(ranked_datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for item in ranked_datasets:
        rank = int(item.get("rank") or len(targets) + 1)
        dataset_name = (item.get("dataset_name") or item.get("title") or f"target-{rank}").strip()
        source_name = (item.get("source_domain") or "").strip() or "unknown-source"
        target = {
            "rank": rank,
            "source_name": source_name,
            "source_slug": f"{rank:02d}-{slugify(dataset_name)[:72]}",
            "dataset_name": dataset_name,
            "title": (item.get("title") or "").strip(),
            "start_url": (item.get("url") or "").strip(),
            "source_domain": source_name,
            "track_origin": item.get("track_origin") or "",
            "track_priority": item.get("track_priority") or "",
            "track_intent": item.get("track_intent") or "",
            "data_format": item.get("data_format") or "",
            "access_type": item.get("access_type") or "",
            "access_notes": item.get("access_notes") or "",
            "temporal_coverage": item.get("temporal_coverage") or "",
            "spatial_coverage": item.get("spatial_coverage") or "",
            "key_parameters": item.get("key_parameters") or [],
            "needs_review": bool(item.get("needs_review")),
            "collection_method_hint": collection_method_hint(item.get("access_type") or ""),
            "handoff_status": handoff_status(item),
        }
        targets.append(target)
    return sorted(targets, key=lambda row: row["rank"])


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

    targets = build_targets(ranked_datasets)
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
