"""
Context intake for Clarks Hill Lake EDA.

This script is intentionally conservative. It reads the search and collection
manifests, classifies what is already usable, what is blocked, and what is only
discovered, and writes an initial inventory for the EDA workspace.

It does not create staging or analytic tables.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EDA_DIR = Path(__file__).resolve().parent
DEFAULT_SEARCH_MANIFEST = ROOT / "data" / "runs" / "perplexity-intel-8ba66531" / "manifest.json"
DEFAULT_RANKED_DATASETS = ROOT / "data" / "runs" / "perplexity-intel-8ba66531" / "processing" / "03-ranked-datasets.json"
DEFAULT_HARVESTER_HANDOFF = ROOT / "data" / "runs" / "perplexity-intel-8ba66531" / "processing" / "04-harvester-handoff.json"
DEFAULT_COLLECTION_MANIFEST = ROOT / "data" / "runs" / "operational-collect-clarkshill-20260401-225924" / "manifest.json"
DEFAULT_OUTPUT_JSON = EDA_DIR / "initial_source_inventory.partial.json"
DEFAULT_OUTPUT_MD = EDA_DIR / "initial_source_inventory.partial.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the initial Clarks Hill source inventory.")
    parser.add_argument("--search-manifest", type=Path, default=DEFAULT_SEARCH_MANIFEST)
    parser.add_argument("--ranked-datasets", type=Path, default=DEFAULT_RANKED_DATASETS)
    parser.add_argument("--harvester-handoff", type=Path, default=DEFAULT_HARVESTER_HANDOFF)
    parser.add_argument("--collection-manifest", type=Path, default=DEFAULT_COLLECTION_MANIFEST)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def index_ranked_datasets(ranked_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for item in ranked_payload.get("ranked_datasets", []):
        dataset_name = item.get("dataset_name") or item.get("title")
        if dataset_name:
            indexed[dataset_name] = item
    return indexed


def normalize_collection_target(target: dict[str, Any]) -> dict[str, Any]:
    artifacts = target.get("raw_artifacts", [])
    first_artifact = artifacts[0] if artifacts else {}
    return {
        "target_id": target.get("target_id"),
        "dataset_name": target.get("dataset_name"),
        "source_name": target.get("source_name"),
        "collection_status": target.get("collection_status"),
        "collection_method": target.get("collection_method"),
        "access_type": target.get("access_type"),
        "local_artifacts": [artifact.get("relative_path") for artifact in artifacts if artifact.get("relative_path")],
        "provenance_urls": target.get("provenance_urls", []),
        "blockers": target.get("blockers", []),
        "notes": target.get("notes", []),
        "join_keys": target.get("join_keys", []),
        "artifact_format": first_artifact.get("file_format"),
    }


def classify_targets(collection_manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    usable_now: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for raw_target in collection_manifest.get("targets", []):
        target = normalize_collection_target(raw_target)
        status = target.get("collection_status")
        if status == "collected":
            usable_now.append(target)
        elif status and status.startswith("blocked"):
            blocked.append(target)
    return usable_now, blocked


def discovered_only(handoff_payload: dict[str, Any], collection_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    collected_ids = {target.get("target_id") for target in collection_manifest.get("targets", [])}
    remaining: list[dict[str, Any]] = []
    for target in handoff_payload.get("targets", []):
        if target.get("source_slug") in collected_ids:
            continue
        remaining.append(
            {
                "rank": target.get("rank"),
                "source_slug": target.get("source_slug"),
                "dataset_name": target.get("dataset_name"),
                "source_name": target.get("source_name"),
                "access_type": target.get("access_type"),
                "collection_method_hint": target.get("collection_method_hint"),
                "spatial_coverage": target.get("spatial_coverage"),
                "temporal_coverage": target.get("temporal_coverage"),
                "key_parameters": target.get("key_parameters", []),
            }
        )
    return remaining


def build_inventory(search_manifest: dict[str, Any], handoff_payload: dict[str, Any], collection_manifest: dict[str, Any]) -> dict[str, Any]:
    usable_now, blocked = classify_targets(collection_manifest)
    discovered = discovered_only(handoff_payload, collection_manifest)
    return {
        "study": "Clarks Hill Lake contextual EDA",
        "search_run_id": search_manifest.get("research_id"),
        "collection_run_id": collection_manifest.get("run_id"),
        "search_summary": {
            "ranked_dataset_count": search_manifest.get("ranked_dataset_count"),
            "search_plan_count": search_manifest.get("search_plan_count"),
            "session_count": search_manifest.get("session_count"),
        },
        "collection_summary": {
            "target_count": collection_manifest.get("target_count"),
            "collected_count": collection_manifest.get("collected_count"),
            "blocked_count": collection_manifest.get("blocked_count"),
            "partial_count": collection_manifest.get("partial_count"),
        },
        "usable_now": usable_now,
        "blocked": blocked,
        "discovered_only": discovered,
        "next_analytic_layer": [
            "extract watershed and land-cover context from the two collected PDFs",
            "wait for structured operational and water-quality endpoints before creating staging or analytic tables",
            "define join strategy once station ids, basin ids, or time keys arrive from collection",
        ],
        "not_ready_for_figures": [
            "no structured reservoir operations time series collected yet",
            "no structured inflow or outflow time series collected yet",
            "no structured water-quality table collected yet",
        ],
    }


def render_markdown(inventory: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Clarks Hill Initial Source Inventory")
    lines.append("")
    lines.append(f"- Search run: `{inventory['search_run_id']}`")
    lines.append(f"- Collection run: `{inventory['collection_run_id']}`")
    lines.append(f"- Ranked datasets: `{inventory['search_summary']['ranked_dataset_count']}`")
    lines.append(f"- Collected now: `{inventory['collection_summary']['collected_count']}`")
    lines.append(f"- Blocked now: `{inventory['collection_summary']['blocked_count']}`")
    lines.append("")
    lines.append("## Usable Now")
    lines.append("")
    if inventory["usable_now"]:
        for item in inventory["usable_now"]:
            lines.append(f"- `{item['target_id']}` | {item['dataset_name']}")
            for artifact in item.get("local_artifacts", []):
                lines.append(f"  local: `{artifact}`")
            for note in item.get("notes", []):
                lines.append(f"  note: {note}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Blocked")
    lines.append("")
    if inventory["blocked"]:
        for item in inventory["blocked"]:
            lines.append(f"- `{item['target_id']}` | {item['dataset_name']}")
            for blocker in item.get("blockers", []):
                lines.append(f"  blocker: {blocker}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Next Analytic Layer")
    lines.append("")
    for item in inventory["next_analytic_layer"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Not Ready For Figures")
    lines.append("")
    for item in inventory["not_ready_for_figures"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    search_manifest = load_json(args.search_manifest)
    handoff_payload = load_json(args.harvester_handoff)
    collection_manifest = load_json(args.collection_manifest)

    inventory = build_inventory(search_manifest, handoff_payload, collection_manifest)

    args.output_json.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")
    args.output_md.write_text(render_markdown(inventory), encoding="utf-8")

    print(f"Inventory written to: {args.output_json}")
    print(f"Markdown summary written to: {args.output_md}")
    print("No staging or analytic tables were created.")


if __name__ == "__main__":
    main()
