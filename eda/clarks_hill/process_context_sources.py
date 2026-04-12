"""
Build reproducible staging tables and report context for the Savannah River study.

The analytical frame is river-first:
- the Savannah River mainstem is the primary storyline
- Hartwell, Russell, and Thurmond act as operational annexes
- the 20-year target window stays explicit for every temporal layer
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EDA_DIR = Path(__file__).resolve().parent
RUNS_DIR = ROOT / "data" / "runs"
RIVER_RUN_PREFIXES = ["operational-collect-savannah-river-"]
RESERVOIR_RUN_PREFIXES = ["operational-collect-savannah-system-"]
LEGACY_RUN_PREFIXES = ["operational-collect-clarkshill-"]
SAVANNAH_MAIN_RUN_PREFIXES = ["operational-collect-savannah-main-2021-2025-"]
DEFAULT_SEDIMENT_WORKBOOK = (
    ROOT / "analise_sedimentos" / "Most Corrected Master_Data Clarks Hill Lake (version 3).xlsb.xlsx"
)
DEFAULT_STAGING_DIR = ROOT / "data" / "staging" / "clarks_hill"
DEFAULT_ANALYTIC_DIR = ROOT / "data" / "analytic" / "clarks_hill"
DEFAULT_REPORT_CONTEXT = EDA_DIR / "report_context.json"
DEFAULT_INVENTORY_JSON = EDA_DIR / "initial_source_inventory.partial.json"
DEFAULT_INVENTORY_MD = EDA_DIR / "initial_source_inventory.partial.md"
TARGET_COVERAGE_YEARS = 20

DOMAIN_LABELS = {
    "river_core": "Savannah River mainstem behavior",
    "pressure_core": "Pollution, pressure, and treated-water compliance",
    "reservoir_support": "Reservoir operations and structural annex",
    "sediment_response": "Sediment-response interpretation",
    "supporting_context": "Coverage, provenance, and support context",
}
DOMAIN_ORDER = ["river_core", "pressure_core", "reservoir_support", "sediment_response", "supporting_context"]

RESERVOIR_ORDER = ["Hartwell", "Russell", "Thurmond"]
RIVER_SITE_ORDER = ["Calhoun Falls", "Augusta Intake", "US 1 Augusta"]
USGS_SITE_ORDER = ["Augusta", "USACE Dock"]
SAVANNAH_MAIN_SYSTEM_NAME = "Savannah Main System"
DRINKING_WATER_ATTRIBUTE_MAP = {
    "probable source": "probable_source",
    "amount detected": "amount_detected_raw",
    "meets drinking water standards": "meets_standard_raw",
    "maximum disinfectant residual level goal": "mrdlg_raw",
    "maximum disinfectant residual level allowed": "mrdl_raw",
    "maximum contaminant level goal": "mclg_raw",
    "maximum contaminant level allowed": "mcl_raw",
    "action level": "action_level_raw",
    "range detected during reporting year": "range_detected_raw",
    "required number of samples that should have been taken": "required_samples_raw",
    "number of samples that were taken if any": "samples_taken_raw",
    "when samples should have been taken": "sampling_required_period_raw",
    "when samples were taken if any or will be taken next": "sampling_actual_period_raw",
}
DRINKING_WATER_PARAMETER_META = {
    "chlorine": ("chlorine", "Chlorine"),
    "fluoride": ("fluoride", "Fluoride"),
    "total triahlomethanes tthms": ("tthms", "Total Triahlomethanes (TTHMs)"),
    "total trihalomethanes tthms": ("tthms", "Total Trihalomethanes (TTHMs)"),
    "total haloacetic acids thaas": ("thaas", "Total Haloacetic Acids (THAAs)"),
    "haloacetic acids haa5": ("haa5", "Haloacetic Acids (HAA5)"),
    "haa5": ("haa5", "HAA5"),
    "haa6br": ("haa6br", "HAA6Br"),
    "haa9": ("haa9", "HAA9"),
    "total organic carbon": ("total_organic_carbon", "Total Organic Carbon"),
    "total coliform bacteria": ("total_coliform_bacteria", "Total Coliform Bacteria"),
    "turbidity": ("turbidity", "Turbidity"),
    "nitrate": ("nitrate", "Nitrate"),
    "lead": ("lead", "Lead"),
    "copper": ("copper", "Copper"),
    "arsenic": ("arsenic", "Arsenic"),
    "manganese": ("manganese", "Manganese"),
    "bromide": ("bromide", "Bromide"),
}
RIVER_BEHAVIOR_CONFIG = [
    {
        "site_no": "02197000",
        "parameter_code": "00060",
        "statistic": "Mean",
        "series_slug": "augusta_flow_cfs",
        "series_label": "Augusta discharge",
        "parameter_group": "Flow",
    },
    {
        "site_no": "02197000",
        "parameter_code": "00065",
        "statistic": "Mean",
        "series_slug": "augusta_stage_ft",
        "series_label": "Augusta stage",
        "parameter_group": "Stage",
    },
    {
        "site_no": "021989773",
        "parameter_code": "00010",
        "statistic": "Mean",
        "series_slug": "dock_water_temp_c",
        "series_label": "Dock water temperature",
        "parameter_group": "Water temperature",
    },
    {
        "site_no": "021989773",
        "parameter_code": "00300",
        "statistic": "Mean",
        "series_slug": "dock_do_mg_l",
        "series_label": "Dock dissolved oxygen",
        "parameter_group": "DO",
    },
    {
        "site_no": "021989773",
        "parameter_code": "00095",
        "statistic": "Mean",
        "series_slug": "dock_conductance_us_cm",
        "series_label": "Dock specific conductance",
        "parameter_group": "Specific conductance",
    },
    {
        "site_no": "021989773",
        "parameter_code": "00400",
        "statistic": "Median",
        "series_slug": "dock_ph_su",
        "series_label": "Dock pH",
        "parameter_group": "pH",
    },
    {
        "site_no": "021989773",
        "parameter_code": "63680",
        "statistic": "Median",
        "series_slug": "dock_turbidity_fnu",
        "series_label": "Dock turbidity",
        "parameter_group": "Turbidity / sediment proxy",
    },
]
RIVER_BEHAVIOR_LOOKUP = {
    (item["site_no"], item["parameter_code"], item["statistic"]): item for item in RIVER_BEHAVIOR_CONFIG
}
RIVER_BEHAVIOR_CODE_LOOKUP = {
    (item["site_no"], item["parameter_code"]): item for item in RIVER_BEHAVIOR_CONFIG
}
RESERVOIR_TIMESERIES_CONFIG = {
    "elevation": {"metric_slug": "pool_elevation_ft", "metric_label": "Pool elevation", "parameter_group": "Elevation"},
    "inflow": {"metric_slug": "inflow_cfs", "metric_label": "Inflow", "parameter_group": "Flow"},
    "outflow": {"metric_slug": "outflow_cfs", "metric_label": "Outflow", "parameter_group": "Flow"},
    "storage": {"metric_slug": "storage_acft", "metric_label": "Storage", "parameter_group": "Storage"},
    "tailwater": {"metric_slug": "tailwater_ft", "metric_label": "Tailwater elevation", "parameter_group": "Tailwater"},
    "power_generation": {"metric_slug": "power_generation", "metric_label": "Power generation", "parameter_group": "Power"},
    "release": {"metric_slug": "release_cfs", "metric_label": "Release", "parameter_group": "Flow"},
}
PARAMETER_GROUP_ORDER = [
    "Water temperature",
    "pH",
    "DO",
    "Specific conductance",
    "Turbidity / sediment proxy",
    "Nitrogen",
    "Phosphorus",
    "Organic carbon",
    "Chlorophyll-a",
    "Metals / trace elements",
    "Microbiological",
]

RESERVOIR_NAME_ALIASES = {
    "hartwell": "Hartwell",
    "richard b. russell": "Russell",
    "richard b russell": "Russell",
    "russell": "Russell",
    "j. strom thurmond": "Thurmond",
    "j strom thurmond": "Thurmond",
    "thurmond": "Thurmond",
    "clarks hill": "Thurmond",
}

RIVER_SITE_ALIASES = {
    "USGS-02189000": {
        "short_label": "Calhoun Falls",
        "reach": "Upper mainstem near Calhoun Falls",
    },
    "USGS-02196560": {
        "short_label": "Augusta Intake",
        "reach": "Augusta river intake reach",
    },
    "USGS-02196671": {
        "short_label": "US 1 Augusta",
        "reach": "Augusta urban mainstem reach",
    },
    "02197000": {
        "short_label": "Augusta",
        "reach": "Savannah River at Augusta",
    },
    "021989773": {
        "short_label": "USACE Dock",
        "reach": "Savannah River at USACE dock, Savannah",
    },
}

PRESSURE_KEYWORDS = [
    "pollut",
    "pressure",
    "impair",
    "discharger",
    "landscape",
    "land use",
    "land cover",
    "bathymetry",
    "watershed",
    "basin",
    "restoration",
    "epa",
    "deq",
    "tmdl",
    "nutrient",
    "sediment",
    "turbidity",
    "wastewater",
]

FIGURE_SOURCE_REFS = {
    "fig1": [
        "data/staging/clarks_hill/river_monthly_behavior.csv",
        "docs/clarks-hill/figures/fig1_river_mainstem_hydrograph.svg",
    ],
    "fig2": [
        "data/staging/clarks_hill/reservoir_operations_monthly.csv",
        "data/staging/clarks_hill/reservoir_operations_summary.csv",
        "docs/clarks-hill/figures/fig2_cascade_operations.svg",
    ],
    "fig3": [
        "data/staging/clarks_hill/river_reservoir_bridge.csv",
        "data/staging/clarks_hill/reservoir_operations_summary.csv",
        "docs/clarks-hill/figures/fig3_thurmond_augusta_bridge.svg",
    ],
    "fig4": [
        "data/staging/clarks_hill/river_monthly_behavior.csv",
        "docs/clarks-hill/figures/fig4_lower_river_quality_timeseries.svg",
    ],
    "fig5": [
        "data/staging/clarks_hill/savannah_main_treated_water_summary.csv",
        "data/staging/clarks_hill/savannah_main_treated_water_long.csv",
        "data/analytic/clarks_hill/pressure_source_inventory.csv",
        "docs/clarks-hill/figures/fig5_pressures_pollutants.svg",
    ],
    "fig6": [
        "data/staging/clarks_hill/river_quality_flow_correlations.csv",
        "data/staging/clarks_hill/river_reservoir_bridge.csv",
        "docs/clarks-hill/figures/fig6_flow_quality_coupling.svg",
    ],
    "fig7": [
        "data/staging/clarks_hill/sediment_master_data.csv",
        "data/staging/clarks_hill/sediment_depositional_scores.csv",
        "docs/clarks-hill/figures/fig7_sediment_texture_score.svg",
    ],
    "fig8": [
        "data/staging/clarks_hill/sediment_master_data.csv",
        "data/staging/clarks_hill/sediment_pairwise_relations.csv",
        "docs/clarks-hill/figures/fig8_sediment_relations.svg",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Savannah River staging tables and report context.")
    parser.add_argument(
        "--river-manifest",
        type=Path,
        help="Optional explicit river collection manifest. Defaults to the latest Savannah River run.",
    )
    parser.add_argument(
        "--reservoir-manifest",
        type=Path,
        help="Optional explicit reservoir collection manifest. Defaults to the latest Savannah system run.",
    )
    parser.add_argument(
        "--legacy-thurmond-manifest",
        type=Path,
        help="Optional explicit legacy Thurmond manifest. Defaults to the latest focused legacy run when present.",
    )
    parser.add_argument(
        "--savannah-main-manifest",
        type=Path,
        help="Optional explicit Savannah Main annual report manifest. Defaults to the latest 2021-2025 Savannah Main collection when present.",
    )
    parser.add_argument(
        "--harvester-handoff",
        type=Path,
        help="Optional discovery handoff JSON. Defaults to the latest 04-harvester-handoff.json under data/runs.",
    )
    parser.add_argument("--sediment-workbook", type=Path, default=DEFAULT_SEDIMENT_WORKBOOK)
    parser.add_argument("--staging-dir", type=Path, default=DEFAULT_STAGING_DIR)
    parser.add_argument("--analytic-dir", type=Path, default=DEFAULT_ANALYTIC_DIR)
    parser.add_argument("--report-context", type=Path, default=DEFAULT_REPORT_CONTEXT)
    parser.add_argument("--inventory-json", type=Path, default=DEFAULT_INVENTORY_JSON)
    parser.add_argument("--inventory-md", type=Path, default=DEFAULT_INVENTORY_MD)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def manifest_generated_at(manifest_path: Path) -> str:
    try:
        payload = load_json(manifest_path)
        return str(
            payload.get("generated_at")
            or payload.get("collected_at")
            or payload.get("created_at")
            or ""
        )
    except (OSError, json.JSONDecodeError):
        return ""


def manifest_completeness_score(manifest_path: Path) -> tuple[float, int, int]:
    try:
        payload = load_json(manifest_path)
    except (OSError, json.JSONDecodeError):
        return (0.0, 0, 0)
    target_count = int(payload.get("target_count") or len(payload.get("targets", [])) or 0)
    collected_count = int(payload.get("collected_count") or 0)
    if target_count <= 0:
        return (0.0, collected_count, target_count)
    return (collected_count / target_count, collected_count, target_count)


def manifest_timeseries_artifact_count(manifest_path: Path) -> int:
    try:
        payload = load_json(manifest_path)
    except (OSError, json.JSONDecodeError):
        return 0
    count = 0
    for target in payload.get("targets", []):
        for artifact in target.get("raw_artifacts", []):
            relative_path = str(artifact.get("relative_path", "")).replace("\\", "/")
            if "/timeseries_" in relative_path:
                count += 1
    return count


def latest_manifest_path(prefixes: list[str]) -> Path | None:
    candidates = [
        path
        for path in RUNS_DIR.glob("*/manifest.json")
        if any(path.parent.name.startswith(prefix) for prefix in prefixes)
    ]
    if not candidates:
        return None
    prioritize_timeseries = prefixes == RESERVOIR_RUN_PREFIXES
    return max(
        candidates,
        key=lambda path: (
            manifest_timeseries_artifact_count(path) if prioritize_timeseries else 0,
            *manifest_completeness_score(path),
            manifest_generated_at(path),
            str(path.parent.name),
        ),
    )


def resolve_manifest_path(explicit_path: Path | None, prefixes: list[str], required: bool = True) -> Path | None:
    if explicit_path is not None:
        return explicit_path if explicit_path.is_absolute() else (ROOT / explicit_path)
    manifest_path = latest_manifest_path(prefixes)
    if manifest_path is not None or not required:
        return manifest_path
    joined_prefixes = ", ".join(prefixes)
    raise SystemExit(f"Unable to find a manifest under {RUNS_DIR} matching prefixes: {joined_prefixes}")


def latest_handoff_path() -> Path | None:
    candidates = list(RUNS_DIR.glob("perplexity-intel-*/processing/04-harvester-handoff.json"))
    if not candidates:
        return None
    return max(candidates, key=lambda path: str(path))


def resolve_handoff_path(explicit_path: Path | None) -> Path | None:
    if explicit_path is not None:
        return explicit_path if explicit_path.is_absolute() else (ROOT / explicit_path)
    return latest_handoff_path()


def normalized_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def humanize_slug(value: str) -> str:
    cleaned = re.sub(r"^\d+-", "", value or "")
    tokens = [token for token in cleaned.split("-") if token and token not in {"wqp", "usgs", "savannah", "river", "site", "flow"}]
    pieces: list[str] = []
    for token in tokens:
        if token == "us1":
            pieces.extend(["US", "1"])
        elif token == "usace":
            pieces.append("USACE")
        elif token.isupper():
            pieces.append(token)
        else:
            pieces.append(token.capitalize())
    return " ".join(pieces).strip() or value


def entity_sort_key(name: str, preferred_order: list[str]) -> tuple[int, int, str]:
    if name in preferred_order:
        return (0, preferred_order.index(name), name)
    return (1, 999, name)


def infer_reservoir_name(*values: Any) -> str | None:
    combined = " ".join(normalized_text(value) for value in values if value)
    for alias, canonical in RESERVOIR_NAME_ALIASES.items():
        if alias in combined:
            return canonical
    return None


def target_text_blob(target: dict[str, Any]) -> str:
    parts = [
        target.get("target_id", ""),
        target.get("source_name", ""),
        target.get("dataset_name", ""),
        " ".join(target.get("notes", [])),
        " ".join(target.get("provenance_urls", [])),
    ]
    return normalized_text(" ".join(parts))


def artifact_filename(target: dict[str, Any], prefix: str) -> str:
    path = artifact_path(target, prefix)
    return path.name if path is not None else ""


def wqp_station_metadata(target: dict[str, Any]) -> dict[str, str]:
    station_path = artifact_path(target, "/station_")
    if station_path is None:
        return {}
    station_rows = read_csv_rows(station_path)
    if not station_rows:
        return {}
    first = station_rows[0]
    return {
        "site_id": first.get("MonitoringLocationIdentifier", ""),
        "site_name": first.get("MonitoringLocationName", ""),
        "latitude": first.get("LatitudeMeasure", ""),
        "longitude": first.get("LongitudeMeasure", ""),
    }


def infer_river_site_metadata(identifier: str, fallback_name: str, target_id: str) -> dict[str, str]:
    alias = RIVER_SITE_ALIASES.get(identifier)
    if alias:
        return {
            "short_label": alias["short_label"],
            "reach": alias["reach"],
        }
    reach = fallback_name.strip() or humanize_slug(target_id)
    short_label = humanize_slug(target_id)
    if normalized_text(short_label) == normalized_text(target_id):
        short_label = reach[:42].strip() or target_id
    return {
        "short_label": short_label,
        "reach": reach,
    }


def is_river_target(target: dict[str, Any], station_name: str = "", station_id: str = "") -> bool:
    text_blob = " ".join([target_text_blob(target), normalized_text(station_name), normalized_text(station_id)])
    return "savannah river" in text_blob and infer_reservoir_name(text_blob) is None


def classify_context_target(target: dict[str, Any]) -> tuple[str, str]:
    text_blob = target_text_blob(target)
    source_name = normalized_text(target.get("source_name", ""))
    station_meta = wqp_station_metadata(target)
    reservoir_name = infer_reservoir_name(text_blob, station_meta.get("site_name", ""), station_meta.get("site_id", ""))
    if "city of savannah water quality reports" in source_name or text_blob.startswith("savannah main"):
        return "drinking_water_quality", "pressure_core"
    if artifact_path(target, "dv_") is not None and "usgs" in source_name:
        return "river_gauge", "river_core"
    if artifact_path(target, "/result_") is not None and "waterqualitydata" in source_name:
        if reservoir_name:
            return "reservoir_water_quality", "reservoir_support"
        if is_river_target(target, station_meta.get("site_name", ""), station_meta.get("site_id", "")):
            return "river_water_quality", "river_core"
    if artifact_path(target, "location_") is not None and "usace" in source_name:
        return "reservoir_operations", "reservoir_support"
    if artifact_path(target, "inventory_") is not None and "nid" in source_name:
        return "reservoir_structure", "reservoir_support"
    if any(keyword in text_blob for keyword in PRESSURE_KEYWORDS):
        return "environmental_pressure", "pressure_core"
    return "other_context", "supporting_context"


def target_coverage_years(target: dict[str, Any]) -> int | None:
    coverage = target.get("temporal_coverage_returned")
    if isinstance(coverage, dict):
        years_with_data = coverage.get("years_with_data")
        if years_with_data not in ("", None):
            return int(years_with_data)
        first_year = coverage.get("first_year")
        last_year = coverage.get("last_year")
        if first_year not in ("", None) and last_year not in ("", None):
            return int(last_year) - int(first_year) + 1
        first_date = coverage.get("first_date")
        last_date = coverage.get("last_date")
        if first_date and last_date:
            return int(str(last_date)[:4]) - int(str(first_date)[:4]) + 1
    if target.get("year") not in ("", None):
        return 1
    return None


def target_period_bounds(target: dict[str, Any]) -> tuple[str, str]:
    coverage = target.get("temporal_coverage_returned")
    if isinstance(coverage, dict):
        first_year = coverage.get("first_year") or str(coverage.get("first_date", ""))[:4]
        last_year = coverage.get("last_year") or str(coverage.get("last_date", ""))[:4]
        return (str(first_year or ""), str(last_year or ""))
    if target.get("year") not in ("", None):
        year = int(target["year"])
        if normalized_text(target.get("source_name", "")) == "city of savannah water quality reports":
            return (str(year - 1), str(year - 1))
        return (str(year), str(year))
    return ("", "")


def priority_gap_reason(target: dict[str, Any], thematic_axis: str) -> str:
    coverage_years = target_coverage_years(target)
    if thematic_axis == "river_water_quality" and (coverage_years is None or coverage_years < TARGET_COVERAGE_YEARS):
        return "Needs longer-horizon mainstem chemistry and pollutant context."
    if thematic_axis == "drinking_water_quality" and (coverage_years is None or coverage_years < TARGET_COVERAGE_YEARS):
        return "Useful lower-basin compliance layer, but it still needs raw-river chemistry and PFAS context around it."
    if thematic_axis == "river_gauge" and (coverage_years is None or coverage_years < TARGET_COVERAGE_YEARS):
        return "Needs additional mainstem gauges with full 20-year support."
    if thematic_axis == "reservoir_operations":
        return "Needs multi-decade operational series rather than snapshot-only support."
    if thematic_axis == "environmental_pressure":
        return "Needs structured pollutant and pressure layers that can join the river narrative."
    return ""


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def hydrate_manifest(manifest_path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    payload = dict(manifest)
    if not payload.get("targets"):
        processing_path = manifest_path.parent / "processing" / "01-collection-targets.json"
        if processing_path.exists():
            try:
                raw_targets = load_json(processing_path)
                if isinstance(raw_targets, list):
                    payload["targets"] = raw_targets
            except json.JSONDecodeError:
                payload["targets"] = []
    targets = payload.get("targets", [])
    if isinstance(targets, list):
        payload.setdefault("target_count", len(targets))
        if "collected_count" not in payload:
            payload["collected_count"] = sum(
                1 for target in targets if str(target.get("collection_status") or target.get("status") or "") == "collected"
            )
    return payload


def load_manifest_targets(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for target in manifest.get("targets", []):
        enriched = dict(target)
        enriched["run_id"] = manifest["run_id"]
        enriched.setdefault("target_id", target.get("target_id") or target.get("source_slug") or target.get("dataset_name", ""))
        enriched.setdefault("collection_status", target.get("collection_status") or target.get("status") or "")
        targets.append(enriched)
    return targets


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def artifact_path(target: dict[str, Any], pattern: str) -> Path | None:
    for artifact in target.get("raw_artifacts", []):
        rel = artifact.get("relative_path", "")
        normalized_rel = rel.replace("\\", "/")
        if pattern in normalized_rel:
            if normalized_rel.startswith("data/runs/"):
                candidate = ROOT / normalized_rel
            else:
                candidate = ROOT / "data" / "runs" / target["run_id"] / rel
            if candidate.exists():
                return candidate
    return None


def extract_latest_value(timeseries: list[dict[str, Any]], label: str) -> float | None:
    for item in timeseries:
        if item.get("label") == label:
            return item.get("latest_value")
    return None


def parameter_group(name: str) -> str | None:
    normalized = (name or "").strip().lower()
    if not normalized:
        return None
    if "chlorine" in normalized or "fluoride" in normalized:
        return "Drinking-water additives"
    if "triahlomethane" in normalized or "haloacetic" in normalized or normalized in {"haa5", "haa6br", "haa9"}:
        return "Disinfection byproducts"
    if "dissolved oxygen" in normalized:
        return "DO"
    if normalized == "ph":
        return "pH"
    if normalized == "temperature, water":
        return "Water temperature"
    if "specific conductance" in normalized or "conductivity" in normalized:
        return "Specific conductance"
    if "turbidity" in normalized or "suspended" in normalized:
        return "Turbidity / sediment proxy"
    if "chlorophyll" in normalized:
        return "Chlorophyll-a"
    if "phosphorus" in normalized:
        return "Phosphorus"
    if "nitrate" in normalized or "nitrogen" in normalized or "ammonia" in normalized:
        return "Nitrogen"
    if "organic carbon" in normalized:
        return "Organic carbon"
    if "bromide" in normalized:
        return "Halides"
    if "arsenic" in normalized or "cadmium" in normalized or "chromium" in normalized or "cobalt" in normalized or "copper" in normalized or "lead" in normalized or "mercury" in normalized or "manganese" in normalized or "nickel" in normalized or "zinc" in normalized:
        return "Metals / trace elements"
    if "coli" in normalized or "enterococcus" in normalized or "streptococci" in normalized:
        return "Microbiological"
    return None


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _xlsx_column_index(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref)
    if match is None:
        return 0
    column = 0
    for char in match.group(1):
        column = column * 26 + (ord(char) - 64)
    return column - 1


def load_xlsx_rows(path: Path, sheet_name: str) -> list[dict[str, str]]:
    ns_main = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    ns_rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    with zipfile.ZipFile(path) as workbook_zip:
        workbook_root = ET.fromstring(workbook_zip.read("xl/workbook.xml"))
        sheets_root = workbook_root.find(f"{{{ns_main}}}sheets")
        if sheets_root is None:
            return []
        sheet_rid = None
        for sheet in sheets_root:
            if sheet.attrib.get("name") == sheet_name:
                sheet_rid = sheet.attrib.get(f"{{{ns_rel}}}id")
                break
        if sheet_rid is None:
            return []

        rels_root = ET.fromstring(workbook_zip.read("xl/_rels/workbook.xml.rels"))
        rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels_root}
        sheet_target = rel_map[sheet_rid]
        if not sheet_target.startswith("xl/"):
            sheet_target = f"xl/{sheet_target}"

        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in workbook_zip.namelist():
            strings_root = ET.fromstring(workbook_zip.read("xl/sharedStrings.xml"))
            for item in strings_root:
                shared_strings.append("".join(node.text or "" for node in item.iter(f"{{{ns_main}}}t")))

        sheet_root = ET.fromstring(workbook_zip.read(sheet_target))
        rows: list[list[str]] = []
        for row in sheet_root.iter(f"{{{ns_main}}}row"):
            values: dict[int, str] = {}
            for cell in row:
                index = _xlsx_column_index(cell.attrib.get("r", "A1"))
                value_node = cell.find(f"{{{ns_main}}}v")
                if value_node is None:
                    value = ""
                elif cell.attrib.get("t") == "s":
                    value = shared_strings[int(value_node.text)]
                else:
                    value = value_node.text or ""
                values[index] = value
            if values:
                max_index = max(values)
                rows.append([values.get(i, "") for i in range(max_index + 1)])

    if not rows:
        return []
    headers = [str(value).strip() for value in rows[0]]
    records: list[dict[str, str]] = []
    for row in rows[1:]:
        padded = row + [""] * max(0, len(headers) - len(row))
        records.append({headers[index]: padded[index] for index in range(len(headers))})
    return records


def maybe_fix_mojibake(value: str) -> str:
    if not value:
        return value
    if any(token in value for token in ["Ã", "â", "Â"]):
        try:
            return value.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return value
    return value


def clean_html_text(value: str) -> str:
    value = maybe_fix_mojibake(unescape(value or ""))
    value = value.replace("\xa0", " ").replace("\r", "")
    lines = [re.sub(r"\s+", " ", part).strip() for part in value.split("\n")]
    return " | ".join(part for part in lines if part)


class HTMLTableExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._current_table: list[list[str]] | None = None
        self._current_row: list[str] | None = None
        self._current_cell: list[str] | None = None
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._ignored_depth += 1
            return
        if self._ignored_depth:
            return
        if tag == "table":
            self._current_table = []
        elif tag == "tr" and self._current_table is not None:
            self._current_row = []
        elif tag in {"td", "th"} and self._current_row is not None:
            self._current_cell = []
        elif tag == "br" and self._current_cell is not None:
            self._current_cell.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._ignored_depth:
            self._ignored_depth -= 1
            return
        if self._ignored_depth:
            return
        if tag in {"td", "th"} and self._current_cell is not None and self._current_row is not None:
            self._current_row.append(clean_html_text("".join(self._current_cell)))
            self._current_cell = None
        elif tag == "tr" and self._current_row is not None and self._current_table is not None:
            if any(cell.strip() for cell in self._current_row):
                self._current_table.append(self._current_row)
            self._current_row = None
        elif tag == "table" and self._current_table is not None:
            if self._current_table:
                self.tables.append(self._current_table)
            self._current_table = None

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        if self._current_cell is not None:
            self._current_cell.append(data)


def extract_html_tables(path: Path) -> list[list[list[str]]]:
    parser = HTMLTableExtractor()
    parser.feed(path.read_text(encoding="utf-8-sig"))
    return parser.tables


def parse_numeric_token(value: str) -> float | None:
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None


def parse_measurement(raw: str) -> dict[str, Any]:
    cleaned = clean_html_text(raw)
    if not cleaned:
        return {
            "raw": "",
            "value": None,
            "minimum": None,
            "maximum": None,
            "unit": "",
        }
    unit_match = re.search(r"\b(ppm|ppb|ppt|ntu|mg/l|ug/l|%)\b", cleaned.lower())
    numbers = [parse_numeric_token(token) for token in re.findall(r"\d+(?:,\d{3})*(?:\.\d+)?", cleaned)]
    numbers = [value for value in numbers if value is not None]
    value: float | None = None
    minimum: float | None = None
    maximum: float | None = None
    if len(numbers) >= 2 and re.search(r"\d[\d,\.]*\s*-\s*\d", cleaned):
        minimum = numbers[0]
        maximum = numbers[1]
    elif len(numbers) == 1:
        value = numbers[0]
    elif len(numbers) > 1:
        value = numbers[0]
    return {
        "raw": cleaned,
        "value": value,
        "minimum": minimum,
        "maximum": maximum,
        "unit": "" if unit_match is None else unit_match.group(1),
    }


def normalize_drinking_water_parameter(name: str) -> tuple[str, str]:
    normalized = normalized_text(name)
    slug, label = DRINKING_WATER_PARAMETER_META.get(normalized, ("", ""))
    if slug:
        return slug, label
    words = [token for token in normalized.split() if token]
    slug = "_".join(words[:6]) or "parameter"
    return slug, clean_html_text(name)


def extract_first_match(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if match is None:
        return ""
    if match.lastindex:
        return clean_html_text(match.group(1))
    return clean_html_text(match.group(0))


def parse_drinking_water_table(
    table_rows: list[list[str]],
    report_year: int,
    data_year: int,
    system_name: str,
    system_number: str,
    table_kind: str,
    report_notice: str,
    report_violation_flag: int,
) -> list[dict[str, Any]]:
    if not table_rows or len(table_rows[0]) < 2:
        return []
    parameter_headers = [clean_html_text(header) for header in table_rows[0][1:] if clean_html_text(header)]
    if not parameter_headers:
        return []

    per_parameter: dict[str, dict[str, Any]] = {}
    for header in parameter_headers:
        parameter_slug, parameter_label = normalize_drinking_water_parameter(header)
        per_parameter[header] = {
            "report_year": report_year,
            "data_year": data_year,
            "system_name": system_name,
            "system_number": system_number,
            "table_kind": table_kind,
            "parameter_slug": parameter_slug,
            "parameter_name": parameter_label,
            "parameter_group": parameter_group(parameter_label) or "",
            "probable_source": "",
            "amount_detected_raw": "",
            "amount_detected_value": "",
            "amount_detected_min": "",
            "amount_detected_max": "",
            "amount_detected_unit": "",
            "range_detected_raw": "",
            "range_detected_min": "",
            "range_detected_max": "",
            "range_detected_unit": "",
            "meets_standard_raw": "",
            "meets_standard_flag": "",
            "mrdlg_raw": "",
            "mrdl_raw": "",
            "mclg_raw": "",
            "mcl_raw": "",
            "action_level_raw": "",
            "required_samples_raw": "",
            "samples_taken_raw": "",
            "sampling_required_period_raw": "",
            "sampling_actual_period_raw": "",
            "report_notice": report_notice,
            "report_violation_flag": report_violation_flag,
        }

    for row in table_rows[1:]:
        if len(row) < 2:
            continue
        attribute_key = DRINKING_WATER_ATTRIBUTE_MAP.get(normalized_text(row[0]))
        if not attribute_key:
            continue
        for index, header in enumerate(parameter_headers):
            value = clean_html_text(row[index + 1]) if index + 1 < len(row) else ""
            per_parameter[header][attribute_key] = value

    records: list[dict[str, Any]] = []
    for record in per_parameter.values():
        amount = parse_measurement(record["amount_detected_raw"])
        range_detected = parse_measurement(record["range_detected_raw"])
        meets_text = normalized_text(record["meets_standard_raw"])
        record["amount_detected_value"] = "" if amount["value"] is None else round(float(amount["value"]), 6)
        record["amount_detected_min"] = "" if amount["minimum"] is None else round(float(amount["minimum"]), 6)
        record["amount_detected_max"] = "" if amount["maximum"] is None else round(float(amount["maximum"]), 6)
        record["amount_detected_unit"] = amount["unit"]
        record["range_detected_min"] = "" if range_detected["minimum"] is None else round(float(range_detected["minimum"]), 6)
        record["range_detected_max"] = "" if range_detected["maximum"] is None else round(float(range_detected["maximum"]), 6)
        record["range_detected_unit"] = range_detected["unit"]
        record["meets_standard_flag"] = (
            1 if any(token in meets_text for token in ["check", "met", "yes", "complies"]) else 0 if meets_text else ""
        )
        records.append(record)
    return records


def parse_savannah_main_violation_table(
    table_rows: list[list[str]],
    report_year: int,
    data_year: int,
    system_name: str,
    system_number: str,
    violation_summary: str,
    corrective_action_summary: str,
) -> list[dict[str, Any]]:
    if not table_rows or len(table_rows[0]) < 2:
        return []
    parameter_headers = [clean_html_text(header) for header in table_rows[0][1:] if clean_html_text(header)]
    if not parameter_headers:
        return []
    per_parameter: dict[str, dict[str, Any]] = {}
    for header in parameter_headers:
        parameter_slug, parameter_label = normalize_drinking_water_parameter(header)
        per_parameter[header] = {
            "report_year": report_year,
            "data_year": data_year,
            "system_name": system_name,
            "system_number": system_number,
            "parameter_slug": parameter_slug,
            "parameter_name": parameter_label,
            "required_samples": "",
            "samples_taken": "",
            "sampling_required_period": "",
            "sampling_actual_period": "",
            "violation_summary": violation_summary,
            "corrective_action_summary": corrective_action_summary,
        }
    for row in table_rows[1:]:
        if len(row) < 2:
            continue
        attribute_key = DRINKING_WATER_ATTRIBUTE_MAP.get(normalized_text(row[0]))
        if attribute_key == "required_samples_raw":
            field_name = "required_samples"
        elif attribute_key == "samples_taken_raw":
            field_name = "samples_taken"
        elif attribute_key == "sampling_required_period_raw":
            field_name = "sampling_required_period"
        elif attribute_key == "sampling_actual_period_raw":
            field_name = "sampling_actual_period"
        else:
            field_name = ""
        if not field_name:
            continue
        for index, header in enumerate(parameter_headers):
            per_parameter[header][field_name] = clean_html_text(row[index + 1]) if index + 1 < len(row) else ""
    return list(per_parameter.values())


def build_savannah_main_report_layers(
    targets: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    detail_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    violation_rows: list[dict[str, Any]] = []

    def gallons_to_billion(value_text: str, unit_text: str) -> float | None:
        value = parse_numeric_token(value_text)
        if value is None:
            return None
        return value if unit_text.lower() == "billion" else value / 1000.0

    def gallons_to_million(value_text: str, unit_text: str) -> float | None:
        value = parse_numeric_token(value_text)
        if value is None:
            return None
        return value * 1000.0 if unit_text.lower() == "billion" else value

    def parse_source_mix(raw_html_text: str) -> dict[str, Any]:
        normalized_html = maybe_fix_mojibake(raw_html_text)
        source_mix_match = re.search(
            (
                r"In\s+(\d{4}),\s+the\s+Savannah Main System supplied\s+"
                r"([\d,\.]+)\s+(billion|million)\s+gallons of groundwater and\s+"
                r"([\d,\.]+)\s+(billion|million)\s+gallons of surface water to a population of"
                r"(?:\s+approximately)?\s+([\d,]+)"
            ),
            normalized_html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if source_mix_match is None:
            return {
                "source_mix_data_year": None,
                "groundwater_billion_gal": None,
                "surface_water_million_gal": None,
                "surface_water_billion_gal": None,
                "population_served": None,
            }
        return {
            "source_mix_data_year": int(source_mix_match.group(1)),
            "groundwater_billion_gal": gallons_to_billion(source_mix_match.group(2), source_mix_match.group(3)),
            "surface_water_million_gal": gallons_to_million(source_mix_match.group(4), source_mix_match.group(5)),
            "surface_water_billion_gal": gallons_to_billion(source_mix_match.group(4), source_mix_match.group(5)),
            "population_served": int(source_mix_match.group(6).replace(",", "")),
        }

    for target in targets:
        report_year = int(target.get("year") or 0)
        if not report_year:
            continue
        landing_path = artifact_path(target, "/landing.html")
        if landing_path is None or not landing_path.exists():
            continue
        raw_html = landing_path.read_text(encoding="utf-8-sig")
        system_number = extract_first_match(r"Water System Number\s+([A-Z0-9]+)", raw_html)
        report_notice = extract_first_match(r"Notice of Violation:\s*([^<]+)", raw_html)
        report_violation_flag = 1 if report_notice else 0
        tables = extract_html_tables(landing_path)
        if tables:
            detail_rows.extend(
                parse_drinking_water_table(
                    tables[0],
                    report_year,
                    report_year - 1,
                    SAVANNAH_MAIN_SYSTEM_NAME,
                    system_number,
                    "regulated",
                    report_notice,
                    report_violation_flag,
                )
            )
        if len(tables) > 1:
            detail_rows.extend(
                parse_drinking_water_table(
                    tables[1],
                    report_year,
                    report_year - 1,
                    SAVANNAH_MAIN_SYSTEM_NAME,
                    system_number,
                    "unregulated",
                    report_notice,
                    report_violation_flag,
                )
            )

        surface_share = parse_measurement(extract_first_match(r"([0-9]+(?:\.[0-9]+)?)%\s+was drawn from Abercorn Creek", raw_html))
        source_mix = parse_source_mix(raw_html)
        testing_match = re.search(
            r"performed over\s+([\d,]+)\s+tests and procedures,\s+on over\s+([\d,]+)\s+water quality parameters in\s+(\d{4})",
            maybe_fix_mojibake(raw_html),
            flags=re.IGNORECASE | re.DOTALL,
        )
        source_excerpt = extract_first_match(r"<h4>Source</h4>.*?<div class=\"pl-4\">(.*?)</div>", raw_html)
        source_water_data_year = report_year - 1
        if testing_match is not None:
            source_water_data_year = int(testing_match.group(3))
        elif source_mix["source_mix_data_year"] is not None:
            source_water_data_year = int(source_mix["source_mix_data_year"])

        report_detail_rows = [row for row in detail_rows if int(row["report_year"]) == report_year]
        regulated_rows = [row for row in report_detail_rows if row["table_kind"] == "regulated"]
        unregulated_rows = [row for row in report_detail_rows if row["table_kind"] == "unregulated"]

        violation_summary = ""
        corrective_action_summary = ""
        violation_path = artifact_path(target, "/violation.html")
        if violation_path is not None and violation_path.exists():
            violation_html = violation_path.read_text(encoding="utf-8-sig")
            violation_summary = extract_first_match(
                r"We are required to monitor.*?for\s*<strong>(.*?)</strong>.*?compliance periods",
                violation_html,
            )
            if not violation_summary:
                violation_summary = extract_first_match(
                    r"We did not properly complete.*?</p>",
                    violation_html,
                )
            corrective_action_summary = extract_first_match(r"<p>We have since taken.*?</p>", violation_html)
            violation_tables = extract_html_tables(violation_path)
            if violation_tables:
                violation_rows.extend(
                    parse_savannah_main_violation_table(
                        violation_tables[0],
                        report_year,
                        source_water_data_year,
                        SAVANNAH_MAIN_SYSTEM_NAME,
                        system_number,
                        violation_summary,
                        corrective_action_summary,
                    )
                )

        summary_rows.append(
            {
                "report_year": report_year,
                "data_year": source_water_data_year,
                "system_name": SAVANNAH_MAIN_SYSTEM_NAME,
                "system_number": system_number,
                "regulated_parameter_count": len(regulated_rows),
                "unregulated_parameter_count": len(unregulated_rows),
                "parameters_meeting_standard_count": sum(1 for row in regulated_rows if row["meets_standard_flag"] == 1),
                "parameters_not_meeting_standard_count": sum(1 for row in regulated_rows if row["meets_standard_flag"] == 0),
                "violation_flag": 1 if violation_path is not None else report_violation_flag,
                "violation_parameter_count": len([row for row in violation_rows if int(row["report_year"]) == report_year]),
                "surface_water_share_pct": "" if surface_share["value"] is None else round(float(surface_share["value"]), 6),
                "groundwater_billion_gal": "" if source_mix["groundwater_billion_gal"] is None else round(float(source_mix["groundwater_billion_gal"]), 6),
                "surface_water_million_gal": "" if source_mix["surface_water_million_gal"] is None else round(float(source_mix["surface_water_million_gal"]), 6),
                "surface_water_billion_gal": "" if source_mix["surface_water_billion_gal"] is None else round(float(source_mix["surface_water_billion_gal"]), 6),
                "population_served": "" if source_mix["population_served"] is None else int(source_mix["population_served"]),
                "tests_performed": "" if testing_match is None else int(testing_match.group(1).replace(",", "")),
                "parameters_tested": "" if testing_match is None else int(testing_match.group(2).replace(",", "")),
                "report_notice": report_notice,
                "source_excerpt": source_excerpt,
                "violation_summary": violation_summary,
                "corrective_action_summary": corrective_action_summary,
            }
        )

    detail_rows.sort(key=lambda row: (int(row["report_year"]), row["table_kind"], row["parameter_slug"]))
    summary_rows.sort(key=lambda row: int(row["report_year"]))
    violation_rows.sort(key=lambda row: (int(row["report_year"]), row["parameter_slug"]))
    return detail_rows, summary_rows, violation_rows


def build_savannah_main_river_bridge(
    summary_rows: list[dict[str, Any]],
    detail_rows: list[dict[str, Any]],
    annual_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    annual_lookup: dict[tuple[str, int], float] = {}
    for row in annual_rows:
        annual_lookup[(str(row["series_slug"]), int(row["year"]))] = float(row["annual_mean"])

    parameter_lookup: dict[tuple[int, str], dict[str, Any]] = {}
    for row in detail_rows:
        data_year = int(row["data_year"])
        parameter_lookup[(data_year, row["parameter_slug"])] = row

    rows: list[dict[str, Any]] = []
    for row in summary_rows:
        data_year = int(row["data_year"])
        rows.append(
            {
                "report_year": row["report_year"],
                "data_year": data_year,
                "violation_flag": row["violation_flag"],
                "surface_water_share_pct": row["surface_water_share_pct"],
                "groundwater_billion_gal": row["groundwater_billion_gal"],
                "surface_water_million_gal": row["surface_water_million_gal"],
                "surface_water_billion_gal": row.get("surface_water_billion_gal", ""),
                "population_served": row["population_served"],
                "tests_performed": row["tests_performed"],
                "parameters_tested": row["parameters_tested"],
                "report_notice": row["report_notice"],
                "augusta_flow_cfs": annual_lookup.get(("augusta_flow_cfs", data_year), ""),
                "augusta_stage_ft": annual_lookup.get(("augusta_stage_ft", data_year), ""),
                "dock_conductance_us_cm": annual_lookup.get(("dock_conductance_us_cm", data_year), ""),
                "dock_do_mg_l": annual_lookup.get(("dock_do_mg_l", data_year), ""),
                "dock_turbidity_fnu": annual_lookup.get(("dock_turbidity_fnu", data_year), ""),
                "dock_water_temp_c": annual_lookup.get(("dock_water_temp_c", data_year), ""),
                "chlorine_ppm": parameter_lookup.get((data_year, "chlorine"), {}).get("amount_detected_value", ""),
                "fluoride_ppm": parameter_lookup.get((data_year, "fluoride"), {}).get("amount_detected_value", ""),
                "tthms_ppb": parameter_lookup.get((data_year, "tthms"), {}).get("amount_detected_value", ""),
                "thaas_ppb": parameter_lookup.get((data_year, "thaas"), {}).get("amount_detected_value", ""),
                "nitrate_ppm": parameter_lookup.get((data_year, "nitrate"), {}).get("amount_detected_value", ""),
                "lead_ppb": parameter_lookup.get((data_year, "lead"), {}).get("amount_detected_value", ""),
                "copper_ppm": parameter_lookup.get((data_year, "copper"), {}).get("amount_detected_value", ""),
                "arsenic_ppb": parameter_lookup.get((data_year, "arsenic"), {}).get("amount_detected_value", ""),
                "manganese_ppb": parameter_lookup.get((data_year, "manganese"), {}).get("amount_detected_value", ""),
                "bromide_ppb": parameter_lookup.get((data_year, "bromide"), {}).get("amount_detected_value", ""),
                "haa5_ppb": parameter_lookup.get((data_year, "haa5"), {}).get("amount_detected_value", ""),
                "haa6br_ppb": parameter_lookup.get((data_year, "haa6br"), {}).get("amount_detected_value", ""),
                "haa9_ppb": parameter_lookup.get((data_year, "haa9"), {}).get("amount_detected_value", ""),
            }
        )
    return rows


def compute_zscores(values: list[float]) -> list[float]:
    if not values:
        return []
    mean_value = sum(values) / len(values)
    variance = sum((value - mean_value) ** 2 for value in values) / max(len(values) - 1, 1)
    std_value = variance ** 0.5
    if std_value == 0:
        return [0.0 for _ in values]
    return [(value - mean_value) / std_value for value in values]


def compute_correlation(x_values: list[float], y_values: list[float]) -> tuple[float, float, float]:
    if len(x_values) != len(y_values) or len(x_values) < 2:
        return 0.0, 0.0, 0.0
    mean_x = sum(x_values) / len(x_values)
    mean_y = sum(y_values) / len(y_values)
    sum_xx = sum((value - mean_x) ** 2 for value in x_values)
    sum_yy = sum((value - mean_y) ** 2 for value in y_values)
    sum_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
    if sum_xx == 0 or sum_yy == 0:
        return 0.0, 0.0, mean_y
    slope = sum_xy / sum_xx
    intercept = mean_y - slope * mean_x
    correlation = sum_xy / ((sum_xx ** 0.5) * (sum_yy ** 0.5))
    return slope, intercept, correlation


def iso_date(value: str) -> str:
    return str(value or "")[:10]


def iso_year(value: str) -> int:
    return int(str(value or "")[:4])


def iso_month(value: str) -> int:
    return int(str(value or "")[5:7])


def ano_mes(value: str) -> str:
    return str(value or "")[:7]


def mean_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def median_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def build_sediment_tables(workbook_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    raw_rows = load_xlsx_rows(workbook_path, "Master Data")
    sediment_rows: list[dict[str, Any]] = []
    for raw in raw_rows:
        site = to_float(raw.get("Site"))
        fe_ppm = to_float(raw.get("Fe_ppm"))
        if site is None or fe_ppm is None or not (1 <= site <= 30):
            continue
        clay_pct = to_float(raw.get("%Clay"))
        silt_pct = to_float(raw.get("%Silt"))
        sand_pct = to_float(raw.get("%Sand"))
        d10 = to_float(raw.get("D10"))
        d50 = to_float(raw.get("D50"))
        d90 = to_float(raw.get("D90"))
        sediment_rows.append(
            {
                "site": int(site),
                "depth": to_float(raw.get("Depth")),
                "latitude": to_float(raw.get("Latitude")),
                "longitude": to_float(raw.get("Longitude")) or to_float(raw.get("Longtitude")),
                "clay_pct": clay_pct,
                "silt_pct": silt_pct,
                "sand_pct": sand_pct,
                "fine_fraction_pct": None if clay_pct is None or silt_pct is None else clay_pct + silt_pct,
                "water_pct": to_float(raw.get("Water_%")),
                "d10": d10,
                "d50": d50,
                "d90": d90,
                "valid_grain_order": (
                    ""
                    if d10 is None or d50 is None or d90 is None
                    else int(d10 <= d50 <= d90)
                ),
                "fe_ppm": fe_ppm,
                "mn_ppm": to_float(raw.get("Mn_ppm")),
                "carbon_pct": to_float(raw.get("%Carbon")),
                "ph": to_float(raw.get("pH")) or to_float(raw.get("Ph")),
                "do_pct": to_float(raw.get("DO (%)")),
                "cond": to_float(raw.get("Cond.")),
            }
        )
    sediment_rows.sort(key=lambda row: row["site"])

    score_fields = ["clay_pct", "water_pct", "fe_ppm", "carbon_pct", "d50", "sand_pct"]
    filtered_rows = [
        row for row in sediment_rows if all(row[field] is not None for field in score_fields)
    ]
    zscore_lookup: dict[str, list[float]] = {}
    for field in score_fields:
        zscore_lookup[field] = compute_zscores([float(row[field]) for row in filtered_rows])

    score_rows: list[dict[str, Any]] = []
    for index, row in enumerate(filtered_rows):
        score = (
            zscore_lookup["clay_pct"][index]
            + zscore_lookup["water_pct"][index]
            + zscore_lookup["fe_ppm"][index]
            + zscore_lookup["carbon_pct"][index]
            - zscore_lookup["d50"][index]
            - zscore_lookup["sand_pct"][index]
        )
        score_rows.append(
            {
                "site": row["site"],
                "fine_depositional_score": round(score, 6),
                "depth": row["depth"],
                "clay_pct": row["clay_pct"],
                "silt_pct": row["silt_pct"],
                "sand_pct": row["sand_pct"],
                "water_pct": row["water_pct"],
                "d50": row["d50"],
                "fe_ppm": row["fe_ppm"],
                "carbon_pct": row["carbon_pct"],
            }
        )
    score_rows.sort(key=lambda row: row["fine_depositional_score"], reverse=True)

    pair_definitions = [
        ("clay_pct", "fe_ppm"),
        ("d50", "fe_ppm"),
        ("fe_ppm", "carbon_pct"),
        ("depth", "fe_ppm"),
        ("depth", "d50"),
        ("clay_pct", "carbon_pct"),
    ]
    pairwise_rows: list[dict[str, Any]] = []
    for x_field, y_field in pair_definitions:
        clean_rows = [
            row for row in sediment_rows if row.get(x_field) is not None and row.get(y_field) is not None
        ]
        x_values = [float(row[x_field]) for row in clean_rows]
        y_values = [float(row[y_field]) for row in clean_rows]
        slope, intercept, correlation = compute_correlation(x_values, y_values)
        pairwise_rows.append(
            {
                "x_field": x_field,
                "y_field": y_field,
                "n": len(clean_rows),
                "slope": round(slope, 8),
                "intercept": round(intercept, 8),
                "correlation": round(correlation, 6),
                "direction": "positive" if correlation >= 0 else "negative",
            }
        )
    return sediment_rows, score_rows, pairwise_rows


def build_parameter_overlap_matrix(
    river_parameter_rows: list[dict[str, Any]],
    reservoir_parameter_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in river_parameter_rows:
        first_year = int(row["first_year"])
        last_year = int(row["last_year"])
        years_available = last_year - first_year + 1
        rows.append(
            {
                "entity_group": "River",
                "entity": row["site_label"],
                "parameter_group": row["parameter_group"],
                "years_available": years_available,
                "coverage_ratio": round(min(years_available, TARGET_COVERAGE_YEARS) / float(TARGET_COVERAGE_YEARS), 4),
                "first_year": first_year,
                "last_year": last_year,
                "result_count": int(row["result_count"]),
            }
        )
    for row in reservoir_parameter_rows:
        first_year = int(row["first_year"])
        last_year = int(row["last_year"])
        years_available = last_year - first_year + 1
        rows.append(
            {
                "entity_group": "Reservoir",
                "entity": row["reservoir"],
                "parameter_group": row["parameter_group"],
                "years_available": years_available,
                "coverage_ratio": round(min(years_available, TARGET_COVERAGE_YEARS) / float(TARGET_COVERAGE_YEARS), 4),
                "first_year": first_year,
                "last_year": last_year,
                "result_count": int(row["result_count"]),
            }
        )
    entity_order = {name: index for index, name in enumerate(RIVER_SITE_ORDER + RESERVOIR_ORDER)}
    parameter_order = {name: index for index, name in enumerate(PARAMETER_GROUP_ORDER)}
    rows.sort(
        key=lambda row: (
            0 if row["entity_group"] == "River" else 1,
            entity_order.get(row["entity"], 999),
            parameter_order.get(row["parameter_group"], 999),
        )
    )
    return rows


def build_usace_snapshot(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_reservoir: dict[str, dict[str, Any]] = {}
    for target in targets:
        location_artifact = artifact_path(target, "location_")
        if location_artifact is None:
            continue
        payload = json.loads(location_artifact.read_text(encoding="utf-8-sig"))[0]
        aliases = payload.get("aliases", {})
        reservoir = infer_reservoir_name(payload.get("public_name", ""), aliases.get("NIDID", "")) or infer_reservoir_name(
            target_text_blob(target)
        )
        if not reservoir:
            continue
        timeseries = payload.get("timeseries", [])
        storage = extract_latest_value(timeseries, "Conservation Storage")
        top_of_conservation = None
        for level in payload.get("levels", []):
            if level.get("label") == "Top of Conservation" and level.get("parameter") == "Stor":
                top_of_conservation = level.get("latest_value")
                break
        rows_by_reservoir[reservoir] = {
            "reservoir": reservoir,
            "public_name": payload.get("public_name", reservoir),
            "nidid": aliases.get("NIDID", ""),
            "nearest_city": payload.get("nearest_city", ""),
            "latitude": payload.get("geometry", {}).get("coordinates", [None, None])[1],
            "longitude": payload.get("geometry", {}).get("coordinates", [None, None])[0],
            "current_pool_elevation_ft": extract_latest_value(timeseries, "Elevation"),
            "rule_curve_ft": extract_latest_value(timeseries, "Elevation Rule Curve"),
            "delta_to_rule_curve_ft": (
                None
                if extract_latest_value(timeseries, "Elevation") is None
                or extract_latest_value(timeseries, "Elevation Rule Curve") is None
                else extract_latest_value(timeseries, "Elevation")
                - extract_latest_value(timeseries, "Elevation Rule Curve")
            ),
            "current_storage_acft": storage,
            "storage_pct_conservation": (
                None if storage in (None, 0) or top_of_conservation in (None, 0) else storage / top_of_conservation * 100.0
            ),
            "current_inflow_cfs": extract_latest_value(timeseries, "Inflow"),
            "current_outflow_cfs": extract_latest_value(timeseries, "Outflow"),
            "current_tailwater_ft": extract_latest_value(timeseries, "Elevation Tailwater"),
            "current_power_mwh": extract_latest_value(timeseries, "Power Generation"),
        }
    rows = list(rows_by_reservoir.values())
    rows.sort(key=lambda row: entity_sort_key(row["reservoir"], RESERVOIR_ORDER))
    return rows


def build_nid_summary(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_reservoir: dict[str, dict[str, Any]] = {}
    for target in targets:
        inventory_path = artifact_path(target, "inventory_")
        if inventory_path is None:
            continue
        try:
            payload = json.loads(inventory_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError:
            continue
        reservoir = infer_reservoir_name(payload.get("damName", ""), payload.get("nidId", "")) or infer_reservoir_name(
            target_text_blob(target)
        )
        if not reservoir:
            continue
        rows_by_reservoir[reservoir] = {
            "reservoir": reservoir,
            "nidid": payload.get("nidId", ""),
            "dam_name": payload.get("damName", ""),
            "hydraulic_height_ft": payload.get("hydraulicHeight", ""),
            "dam_length_ft": payload.get("damLength", ""),
            "max_storage_acft": payload.get("maxStorage", ""),
            "normal_storage_acft": payload.get("normalStorage", ""),
            "surface_area_acres": payload.get("surfaceArea", ""),
            "drainage_area_sqmi": payload.get("drainageArea", ""),
            "year_completed": payload.get("yearCompleted", ""),
        }
    rows = list(rows_by_reservoir.values())
    rows.sort(key=lambda row: entity_sort_key(row["reservoir"], RESERVOIR_ORDER))
    return rows


def summarize_wqp_target(target: dict[str, Any], label_key: str, label_value: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]] | None:
    result_path = artifact_path(target, "/result_")
    station_path = artifact_path(target, "/station_")
    if result_path is None:
        return None

    activity_ids_by_year: dict[int, set[str]] = defaultdict(set)
    result_count_by_year: dict[int, int] = defaultdict(int)
    parameter_counter: dict[str, int] = defaultdict(int)
    parameter_years: dict[str, set[int]] = defaultdict(set)
    years_seen: set[int] = set()

    site_name = label_value
    latitude = ""
    longitude = ""
    if station_path is not None:
        station_rows = read_csv_rows(station_path)
        if station_rows:
            site_name = station_rows[0].get("MonitoringLocationName", label_value)
            latitude = station_rows[0].get("LatitudeMeasure", "")
            longitude = station_rows[0].get("LongitudeMeasure", "")

    for row in read_csv_rows(result_path):
        date_text = row.get("ActivityStartDate", "")
        if len(date_text) < 4:
            continue
        year = int(date_text[:4])
        years_seen.add(year)
        result_count_by_year[year] += 1
        activity_identifier = row.get("ActivityIdentifier", "").strip()
        if activity_identifier:
            activity_ids_by_year[year].add(activity_identifier)
        group = parameter_group(row.get("CharacteristicName", ""))
        if group:
            parameter_counter[group] += 1
            parameter_years[group].add(year)

    years_sorted = sorted(years_seen)
    summary = {
        label_key: label_value,
        "site_name": site_name,
        "first_year": years_sorted[0] if years_sorted else "",
        "last_year": years_sorted[-1] if years_sorted else "",
        "years_with_data": len(years_sorted),
        "activity_count": sum(len(ids) for ids in activity_ids_by_year.values()),
        "result_count": sum(result_count_by_year.values()),
        "latitude": latitude,
        "longitude": longitude,
    }

    yearly_rows = [
        {
            label_key: label_value,
            "year": year,
            "activity_count": len(activity_ids_by_year[year]),
            "result_count": result_count_by_year[year],
        }
        for year in years_sorted
    ]

    parameter_rows = [
        {
            label_key: label_value,
            "parameter_group": group,
            "result_count": count,
            "first_year": min(parameter_years[group]),
            "last_year": max(parameter_years[group]),
        }
        for group, count in sorted(parameter_counter.items())
    ]
    return summary, yearly_rows, parameter_rows


def build_reservoir_wqp_summaries(targets: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    yearly_rows: list[dict[str, Any]] = []
    parameter_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    for target in targets:
        reservoir = infer_reservoir_name(target_text_blob(target), wqp_station_metadata(target).get("site_name", ""))
        if not reservoir:
            continue
        summary_tuple = summarize_wqp_target(target, "reservoir", reservoir)
        if summary_tuple is None:
            continue
        summary, yearly, parameters = summary_tuple
        summary_rows.append(summary)
        yearly_rows.extend(yearly)
        parameter_rows.extend(parameters)
    summary_rows.sort(key=lambda row: entity_sort_key(row["reservoir"], RESERVOIR_ORDER))
    yearly_rows.sort(key=lambda row: (entity_sort_key(row["reservoir"], RESERVOIR_ORDER), row["year"]))
    parameter_rows.sort(key=lambda row: (entity_sort_key(row["reservoir"], RESERVOIR_ORDER), row["parameter_group"]))
    return summary_rows, yearly_rows, parameter_rows


def build_river_wqp_summaries(targets: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    yearly_rows: list[dict[str, Any]] = []
    parameter_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    for target in targets:
        station_meta = wqp_station_metadata(target)
        if infer_reservoir_name(target_text_blob(target), station_meta.get("site_name", ""), station_meta.get("site_id", "")):
            continue
        if not is_river_target(target, station_meta.get("site_name", ""), station_meta.get("site_id", "")):
            continue
        mapping = infer_river_site_metadata(
            station_meta.get("site_id", ""),
            station_meta.get("site_name", ""),
            target.get("target_id", ""),
        )
        summary_tuple = summarize_wqp_target(target, "site_label", mapping["short_label"])
        if summary_tuple is None:
            continue
        summary, yearly, parameters = summary_tuple
        summary["site_id"] = station_meta.get("site_id", "")
        summary["reach"] = mapping["reach"]
        summary_rows.append(summary)
        for row in yearly:
            row["site_id"] = station_meta.get("site_id", "")
            row["reach"] = mapping["reach"]
            yearly_rows.append(row)
        for row in parameters:
            row["site_id"] = station_meta.get("site_id", "")
            row["reach"] = mapping["reach"]
            parameter_rows.append(row)
    summary_rows.sort(key=lambda row: entity_sort_key(row["site_label"], RIVER_SITE_ORDER))
    yearly_rows.sort(key=lambda row: (entity_sort_key(row["site_label"], RIVER_SITE_ORDER), row["year"]))
    parameter_rows.sort(key=lambda row: (entity_sort_key(row["site_label"], RIVER_SITE_ORDER), row["parameter_group"]))
    return summary_rows, yearly_rows, parameter_rows


def build_usgs_river_summaries(targets: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    site_rows: list[dict[str, Any]] = []
    series_rows: list[dict[str, Any]] = []
    for target in targets:
        json_path = artifact_path(target, "dv_")
        if json_path is None or not is_river_target(target):
            continue
        payload = json.loads(json_path.read_text(encoding="utf-8-sig"))
        time_series = payload.get("value", {}).get("timeSeries", [])
        site_name = target.get("dataset_name", "")
        site_no = ""
        first_dates: list[str] = []
        last_dates: list[str] = []
        unique_vars: set[str] = set()
        point_count = 0

        for item in time_series:
            source_info = item.get("sourceInfo", {})
            variable = item.get("variable", {})
            options = variable.get("options", {}).get("option", [])
            values = item.get("values", [])
            entries = values[0].get("value", []) if values else []
            dates = [entry.get("dateTime", "") for entry in entries if entry.get("dateTime")]
            if not dates:
                continue
            site_name = source_info.get("siteName", site_name)
            site_codes = source_info.get("siteCode", [])
            if site_codes:
                site_no = site_codes[0].get("value", site_no)
            variable_code = variable.get("variableCode", [{}])[0].get("value", "")
            variable_name = unescape(variable.get("variableName", ""))
            statistic = options[0].get("value", "") if options else ""
            first_dates.append(min(dates))
            last_dates.append(max(dates))
            unique_vars.add(variable_code)
            point_count += len(dates)
            mapping = infer_river_site_metadata(site_no, site_name, target.get("target_id", ""))
            series_rows.append(
                {
                    "site_label": mapping["short_label"],
                    "site_no": site_no,
                    "site_name": site_name,
                    "reach": mapping["reach"],
                    "parameter_code": variable_code,
                    "variable_name": variable_name,
                    "statistic": statistic,
                    "unit": variable.get("unit", {}).get("unitCode", ""),
                    "first_date": min(dates),
                    "last_date": max(dates),
                    "point_count": len(dates),
                }
            )
        if first_dates and last_dates:
            mapping = infer_river_site_metadata(site_no, site_name, target.get("target_id", ""))
            first_year = int(min(first_dates)[:4])
            last_year = int(max(last_dates)[:4])
            site_rows.append(
                {
                    "site_label": mapping["short_label"],
                    "site_no": site_no,
                    "site_name": site_name,
                    "reach": mapping["reach"],
                    "first_date": min(first_dates),
                    "last_date": max(last_dates),
                    "first_year": first_year,
                    "last_year": last_year,
                    "years_returned": last_year - first_year + 1,
                    "variable_count": len(unique_vars),
                    "point_count": point_count,
                    "variables": ", ".join(sorted(unique_vars)),
                }
            )
    site_rows.sort(key=lambda row: entity_sort_key(row["site_label"], USGS_SITE_ORDER))
    series_rows.sort(
        key=lambda row: (entity_sort_key(row["site_label"], USGS_SITE_ORDER), row["parameter_code"], row["statistic"])
    )
    return site_rows, series_rows


def build_usgs_river_behavior_layers(
    targets: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    daily_rows: list[dict[str, Any]] = []
    monthly_rows: list[dict[str, Any]] = []
    climatology_rows: list[dict[str, Any]] = []
    annual_rows: list[dict[str, Any]] = []
    correlation_rows: list[dict[str, Any]] = []
    monthly_buckets: dict[tuple[str, str], list[float]] = defaultdict(list)
    series_meta: dict[str, dict[str, Any]] = {}

    for target in targets:
        json_path = artifact_path(target, "dv_")
        if json_path is None or not is_river_target(target):
            continue
        payload = json.loads(json_path.read_text(encoding="utf-8-sig"))
        for item in payload.get("value", {}).get("timeSeries", []):
            source_info = item.get("sourceInfo", {})
            variable = item.get("variable", {})
            site_codes = source_info.get("siteCode", [])
            site_no = site_codes[0].get("value", "") if site_codes else ""
            options = variable.get("options", {}).get("option", [])
            statistic = options[0].get("value", "") if options else ""
            parameter_code = variable.get("variableCode", [{}])[0].get("value", "")
            behavior_config = RIVER_BEHAVIOR_LOOKUP.get((site_no, parameter_code, statistic))
            if behavior_config is None:
                behavior_config = RIVER_BEHAVIOR_CODE_LOOKUP.get((site_no, parameter_code))
            if behavior_config is None:
                continue
            site_name = source_info.get("siteName", target.get("dataset_name", ""))
            mapping = infer_river_site_metadata(site_no, site_name, target.get("target_id", ""))
            unit = variable.get("unit", {}).get("unitCode", "")
            variable_name = unescape(variable.get("variableName", ""))
            entries = item.get("values", [{}])[0].get("value", [])
            for entry in entries:
                date_text = iso_date(entry.get("dateTime", ""))
                if not date_text:
                    continue
                value = to_float(entry.get("value"))
                if value is None:
                    continue
                current_ano_mes = ano_mes(date_text)
                daily_rows.append(
                    {
                        "site_label": mapping["short_label"],
                        "site_no": site_no,
                        "site_name": site_name,
                        "reach": mapping["reach"],
                        "series_slug": behavior_config["series_slug"],
                        "series_label": behavior_config["series_label"],
                        "parameter_group": behavior_config["parameter_group"],
                        "parameter_code": parameter_code,
                        "variable_name": variable_name,
                        "statistic": statistic,
                        "unit": unit,
                        "date": date_text,
                        "year": iso_year(date_text),
                        "month": iso_month(date_text),
                        "ano_mes": current_ano_mes,
                        "value": round(value, 6),
                    }
                )
                monthly_buckets[(behavior_config["series_slug"], current_ano_mes)].append(value)
                series_meta[behavior_config["series_slug"]] = {
                    "site_label": mapping["short_label"],
                    "site_no": site_no,
                    "site_name": site_name,
                    "reach": mapping["reach"],
                    "series_slug": behavior_config["series_slug"],
                    "series_label": behavior_config["series_label"],
                    "parameter_group": behavior_config["parameter_group"],
                    "parameter_code": parameter_code,
                    "variable_name": variable_name,
                    "statistic": statistic,
                    "unit": unit,
                }

    for (series_slug, current_ano_mes), values in sorted(monthly_buckets.items()):
        meta = series_meta[series_slug]
        monthly_mean = mean_or_none(values)
        monthly_median = median_or_none(values)
        monthly_min = min(values) if values else None
        monthly_max = max(values) if values else None
        if monthly_mean is None or monthly_median is None or monthly_min is None or monthly_max is None:
            continue
        monthly_rows.append(
            {
                **meta,
                "year": int(current_ano_mes[:4]),
                "month": int(current_ano_mes[5:7]),
                "ano_mes": current_ano_mes,
                "monthly_mean": round(monthly_mean, 6),
                "monthly_median": round(monthly_median, 6),
                "monthly_min": round(monthly_min, 6),
                "monthly_max": round(monthly_max, 6),
                "point_count": len(values),
            }
        )

    climatology_buckets: dict[tuple[str, int], list[float]] = defaultdict(list)
    annual_buckets: dict[tuple[str, int], list[float]] = defaultdict(list)
    for row in monthly_rows:
        climatology_buckets[(row["series_slug"], int(row["month"]))].append(float(row["monthly_mean"]))
        annual_buckets[(row["series_slug"], int(row["year"]))].append(float(row["monthly_mean"]))

    for (series_slug, month), values in sorted(climatology_buckets.items()):
        meta = series_meta[series_slug]
        climatology_rows.append(
            {
                **meta,
                "month": month,
                "climatology_mean": round(mean_or_none(values) or 0.0, 6),
                "climatology_min": round(min(values), 6),
                "climatology_max": round(max(values), 6),
                "year_count": len(values),
            }
        )

    annual_means_by_slug: dict[str, list[float]] = defaultdict(list)
    annual_meta_rows: list[dict[str, Any]] = []
    for (series_slug, year), values in sorted(annual_buckets.items()):
        meta = series_meta[series_slug]
        annual_mean = mean_or_none(values)
        if annual_mean is None:
            continue
        annual_means_by_slug[series_slug].append(annual_mean)
        annual_meta_rows.append(
            {
                **meta,
                "year": year,
                "annual_mean": annual_mean,
            }
        )
    annual_zscores_by_slug = {
        series_slug: compute_zscores(values) for series_slug, values in annual_means_by_slug.items()
    }
    annual_counters: dict[str, int] = defaultdict(int)
    for row in annual_meta_rows:
        series_slug = row["series_slug"]
        series_values = annual_means_by_slug[series_slug]
        series_mean = mean_or_none(series_values)
        index = annual_counters[series_slug]
        annual_counters[series_slug] += 1
        annual_rows.append(
            {
                **row,
                "annual_mean": round(float(row["annual_mean"]), 6),
                "anomaly_vs_series_mean": round(float(row["annual_mean"]) - float(series_mean or 0.0), 6),
                "zscore": round(float(annual_zscores_by_slug.get(series_slug, [0.0])[index]), 6),
            }
        )

    monthly_lookup: dict[str, dict[str, float]] = defaultdict(dict)
    for row in monthly_rows:
        monthly_lookup[row["series_slug"]][row["ano_mes"]] = float(row["monthly_mean"])

    correlation_pairs = [
        ("augusta_flow_cfs", "dock_conductance_us_cm"),
        ("augusta_flow_cfs", "dock_do_mg_l"),
        ("augusta_flow_cfs", "dock_turbidity_fnu"),
        ("augusta_flow_cfs", "dock_water_temp_c"),
        ("augusta_stage_ft", "dock_conductance_us_cm"),
    ]
    for source_slug, target_slug in correlation_pairs:
        source_series = monthly_lookup.get(source_slug, {})
        target_series = monthly_lookup.get(target_slug, {})
        shared_months = sorted(set(source_series).intersection(target_series))
        if len(shared_months) < 3:
            continue
        x_values = [source_series[month_key] for month_key in shared_months]
        y_values = [target_series[month_key] for month_key in shared_months]
        slope, intercept, correlation = compute_correlation(x_values, y_values)
        correlation_rows.append(
            {
                "source_series_slug": source_slug,
                "source_series_label": series_meta[source_slug]["series_label"],
                "target_series_slug": target_slug,
                "target_series_label": series_meta[target_slug]["series_label"],
                "overlap_months": len(shared_months),
                "first_ano_mes": shared_months[0],
                "last_ano_mes": shared_months[-1],
                "slope": round(slope, 8),
                "intercept": round(intercept, 8),
                "correlation": round(correlation, 6),
            }
        )

    daily_rows.sort(key=lambda row: (entity_sort_key(row["site_label"], USGS_SITE_ORDER), row["series_slug"], row["date"]))
    monthly_rows.sort(key=lambda row: (entity_sort_key(row["site_label"], USGS_SITE_ORDER), row["series_slug"], row["ano_mes"]))
    climatology_rows.sort(key=lambda row: (entity_sort_key(row["site_label"], USGS_SITE_ORDER), row["series_slug"], row["month"]))
    annual_rows.sort(key=lambda row: (entity_sort_key(row["site_label"], USGS_SITE_ORDER), row["series_slug"], row["year"]))
    correlation_rows.sort(key=lambda row: (row["source_series_slug"], row["target_series_slug"]))
    return daily_rows, monthly_rows, climatology_rows, annual_rows, correlation_rows


def build_reservoir_operation_layers(
    targets: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    monthly_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    for target in targets:
        location_artifact = artifact_path(target, "location_")
        location_name = ""
        if location_artifact is not None:
            try:
                location_payload = json.loads(location_artifact.read_text(encoding="utf-8-sig"))[0]
                location_name = str(location_payload.get("public_name", ""))
            except (json.JSONDecodeError, IndexError, TypeError):
                location_name = ""
        target_id_text = normalized_text(target.get("target_id", ""))
        if "hartwell" in target_id_text:
            reservoir = "Hartwell"
        elif "russell" in target_id_text:
            reservoir = "Russell"
        elif "thurmond" in target_id_text or "clarks hill" in target_id_text:
            reservoir = "Thurmond"
        else:
            reservoir = infer_reservoir_name(target_text_blob(target), location_name, target.get("target_id", ""))
        if not reservoir:
            continue
        for artifact in target.get("raw_artifacts", []):
            relative_path = str(artifact.get("relative_path", "")).replace("\\", "/")
            if "/timeseries_" not in relative_path:
                continue
            metric_key = Path(relative_path).stem.replace("timeseries_", "")
            metric_config = RESERVOIR_TIMESERIES_CONFIG.get(metric_key)
            if metric_config is None:
                continue
            raw_path = ROOT / "data" / "runs" / target["run_id"] / relative_path
            if not raw_path.exists():
                continue
            payload = json.loads(raw_path.read_text(encoding="utf-8-sig"))
            values = payload.get("values", [])
            if not values:
                continue
            monthly_buckets: dict[str, list[float]] = defaultdict(list)
            min_date = ""
            max_date = ""
            for timestamp, raw_value in values:
                value = to_float(raw_value)
                current_date = iso_date(timestamp)
                if value is None or not current_date:
                    continue
                if not min_date or current_date < min_date:
                    min_date = current_date
                if not max_date or current_date > max_date:
                    max_date = current_date
                monthly_buckets[ano_mes(current_date)].append(value)
            if not monthly_buckets:
                continue
            for current_ano_mes, bucket in sorted(monthly_buckets.items()):
                monthly_mean = mean_or_none(bucket)
                monthly_median = median_or_none(bucket)
                if monthly_mean is None or monthly_median is None:
                    continue
                monthly_rows.append(
                    {
                        "reservoir": reservoir,
                        "metric_slug": metric_config["metric_slug"],
                        "metric_label": metric_config["metric_label"],
                        "parameter_group": metric_config["parameter_group"],
                        "unit": payload.get("unit", ""),
                        "year": int(current_ano_mes[:4]),
                        "month": int(current_ano_mes[5:7]),
                        "ano_mes": current_ano_mes,
                        "monthly_mean": round(monthly_mean, 6),
                        "monthly_median": round(monthly_median, 6),
                        "monthly_min": round(min(bucket), 6),
                        "monthly_max": round(max(bucket), 6),
                        "point_count": len(bucket),
                    }
                )
            summary_rows.append(
                {
                    "reservoir": reservoir,
                    "metric_slug": metric_config["metric_slug"],
                    "metric_label": metric_config["metric_label"],
                    "parameter_group": metric_config["parameter_group"],
                    "unit": payload.get("unit", ""),
                    "first_year": iso_year(min_date),
                    "last_year": iso_year(max_date),
                    "years_returned": iso_year(max_date) - iso_year(min_date) + 1,
                    "months_returned": len(monthly_buckets),
                    "point_count": sum(len(bucket) for bucket in monthly_buckets.values()),
                    "first_date": min_date,
                    "last_date": max_date,
                }
            )
    monthly_rows.sort(key=lambda row: (entity_sort_key(row["reservoir"], RESERVOIR_ORDER), row["metric_slug"], row["ano_mes"]))
    summary_rows.sort(key=lambda row: (entity_sort_key(row["reservoir"], RESERVOIR_ORDER), row["metric_slug"]))
    return monthly_rows, summary_rows


def build_river_reservoir_bridge(
    river_monthly_rows: list[dict[str, Any]],
    reservoir_monthly_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    river_lookup = {
        (row["series_slug"], row["ano_mes"]): float(row["monthly_mean"]) for row in river_monthly_rows
    }
    reservoir_lookup = {
        (row["reservoir"], row["metric_slug"], row["ano_mes"]): float(row["monthly_mean"])
        for row in reservoir_monthly_rows
    }
    months = sorted(
        {
            row["ano_mes"]
            for row in river_monthly_rows
            if row["series_slug"] in {"augusta_flow_cfs", "augusta_stage_ft", "dock_conductance_us_cm", "dock_do_mg_l", "dock_turbidity_fnu"}
        }
    )
    rows: list[dict[str, Any]] = []
    for current_ano_mes in months:
        rows.append(
            {
                "ano_mes": current_ano_mes,
                "year": int(current_ano_mes[:4]),
                "month": int(current_ano_mes[5:7]),
                "augusta_flow_cfs": river_lookup.get(("augusta_flow_cfs", current_ano_mes), ""),
                "augusta_stage_ft": river_lookup.get(("augusta_stage_ft", current_ano_mes), ""),
                "dock_conductance_us_cm": river_lookup.get(("dock_conductance_us_cm", current_ano_mes), ""),
                "dock_do_mg_l": river_lookup.get(("dock_do_mg_l", current_ano_mes), ""),
                "dock_turbidity_fnu": river_lookup.get(("dock_turbidity_fnu", current_ano_mes), ""),
                "thurmond_outflow_cfs": reservoir_lookup.get(("Thurmond", "outflow_cfs", current_ano_mes), ""),
                "thurmond_inflow_cfs": reservoir_lookup.get(("Thurmond", "inflow_cfs", current_ano_mes), ""),
                "thurmond_storage_acft": reservoir_lookup.get(("Thurmond", "storage_acft", current_ano_mes), ""),
                "thurmond_pool_elevation_ft": reservoir_lookup.get(("Thurmond", "pool_elevation_ft", current_ano_mes), ""),
                "hartwell_outflow_cfs": reservoir_lookup.get(("Hartwell", "outflow_cfs", current_ano_mes), ""),
                "russell_outflow_cfs": reservoir_lookup.get(("Russell", "outflow_cfs", current_ano_mes), ""),
            }
        )
    return rows


def coverage_status(returned_years: int | None, coverage_kind: str = "series") -> str:
    if coverage_kind == "snapshot":
        return "snapshot"
    if not returned_years:
        return "missing"
    if returned_years >= TARGET_COVERAGE_YEARS:
        return "meets_target"
    return "below_target"


def build_coverage_matrix(
    river_wqp_summary: list[dict[str, Any]],
    usgs_site_summary: list[dict[str, Any]],
    reservoir_wqp_summary: list[dict[str, Any]],
    reservoir_operation_summary: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in usgs_site_summary:
        rows.append(
            {
                "layer": "River hydrology",
                "entity": row["site_label"],
                "source": "USGS daily values",
                "returned_years": row["years_returned"],
                "target_years": TARGET_COVERAGE_YEARS,
                "coverage_status": coverage_status(int(row["years_returned"])),
                "first_year": row["first_year"],
                "last_year": row["last_year"],
                "coverage_kind": "series",
            }
        )
    for row in river_wqp_summary:
        rows.append(
            {
                "layer": "River chemistry",
                "entity": row["site_label"],
                "source": "WQP results",
                "returned_years": row["years_with_data"],
                "target_years": TARGET_COVERAGE_YEARS,
                "coverage_status": coverage_status(int(row["years_with_data"])),
                "first_year": row["first_year"],
                "last_year": row["last_year"],
                "coverage_kind": "series",
            }
        )
    for row in reservoir_wqp_summary:
        rows.append(
            {
                "layer": "Reservoir water quality",
                "entity": row["reservoir"],
                "source": "WQP forebay",
                "returned_years": row["years_with_data"],
                "target_years": TARGET_COVERAGE_YEARS,
                "coverage_status": coverage_status(int(row["years_with_data"])),
                "first_year": row["first_year"],
                "last_year": row["last_year"],
                "coverage_kind": "series",
            }
        )
    best_operation_rows: dict[str, dict[str, Any]] = {}
    for row in reservoir_operation_summary:
        current = best_operation_rows.get(row["reservoir"])
        if current is None or int(row["years_returned"]) > int(current["years_returned"]):
            best_operation_rows[row["reservoir"]] = row
    for reservoir in RESERVOIR_ORDER:
        row = best_operation_rows.get(reservoir)
        if row is None:
            continue
        rows.append(
            {
                "layer": "Reservoir operations",
                "entity": row["reservoir"],
                "source": f"USACE series ({row['metric_label']})",
                "returned_years": row["years_returned"],
                "target_years": TARGET_COVERAGE_YEARS,
                "coverage_status": coverage_status(int(row["years_returned"])),
                "first_year": row["first_year"],
                "last_year": row["last_year"],
                "coverage_kind": "series",
            }
        )
    return rows


def build_savannah_main_coverage_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not summary_rows:
        return []
    data_years = [int(row["data_year"]) for row in summary_rows]
    returned_years = len(summary_rows)
    return [
        {
            "layer": "Treated water compliance",
            "entity": SAVANNAH_MAIN_SYSTEM_NAME,
            "source": "City of Savannah annual reports",
            "returned_years": returned_years,
            "target_years": TARGET_COVERAGE_YEARS,
            "coverage_status": coverage_status(returned_years),
            "first_year": min(data_years),
            "last_year": max(data_years),
            "coverage_kind": "series",
        }
    ]


def build_context_source_inventory(manifests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for manifest in manifests:
        for target in load_manifest_targets(manifest):
            thematic_axis, analytical_role = classify_context_target(target)
            period_start, period_end = target_period_bounds(target)
            coverage_years = target_coverage_years(target)
            priority_reason = priority_gap_reason(target, thematic_axis)
            rows.append(
                {
                    "run_id": manifest["run_id"],
                    "target_id": target.get("target_id", ""),
                    "source_name": target.get("source_name", ""),
                    "dataset_name": target.get("dataset_name", ""),
                    "collection_status": target.get("collection_status", ""),
                    "thematic_axis": thematic_axis,
                    "analytical_role": analytical_role,
                    "requested_window": target.get("temporal_coverage_requested", ""),
                    "period_start": period_start,
                    "period_end": period_end,
                    "coverage_years": "" if coverage_years is None else coverage_years,
                    "target_years": TARGET_COVERAGE_YEARS,
                    "coverage_status": coverage_status(coverage_years),
                    "requires_priority_followup": "yes" if priority_reason else "",
                    "priority_reason": priority_reason,
                }
            )
    rows.sort(
        key=lambda row: (
            row["thematic_axis"],
            row["collection_status"] != "collected",
            row["run_id"],
            row["target_id"],
        )
    )
    return rows


def flatten_handoff_targets(handoff_payload: dict[str, Any]) -> list[dict[str, Any]]:
    grouped = handoff_payload.get("targets_by_river_scope")
    flattened: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    if isinstance(grouped, dict):
        for river_scope, targets in grouped.items():
            if not isinstance(targets, list):
                continue
            for target in targets:
                if not isinstance(target, dict):
                    continue
                enriched = dict(target)
                enriched.setdefault("river_scope", river_scope)
                key = (str(enriched.get("river_scope", "")), str(enriched.get("source_slug", "")))
                if key in seen:
                    continue
                seen.add(key)
                flattened.append(enriched)
    elif isinstance(handoff_payload.get("targets"), list):
        for target in handoff_payload["targets"]:
            if not isinstance(target, dict):
                continue
            flattened.append(dict(target))
    flattened.sort(key=lambda row: (str(row.get("river_scope", "")), int(row.get("rank", 9999))))
    return flattened


def handoff_target_matches_context(handoff_target: dict[str, Any], context_row: dict[str, Any]) -> bool:
    slug_tokens = [token for token in normalized_text(handoff_target.get("source_slug", "")).split() if len(token) > 2]
    context_blob = normalized_text(
        " ".join(
            [
                context_row.get("target_id", ""),
                context_row.get("source_name", ""),
                context_row.get("dataset_name", ""),
            ]
        )
    )
    if slug_tokens and all(token in context_blob for token in slug_tokens):
        return True
    handoff_dataset = normalized_text(handoff_target.get("dataset_name", ""))
    if handoff_dataset and handoff_dataset in context_blob:
        return True
    handoff_source = normalized_text(handoff_target.get("source_name", ""))
    return bool(handoff_source) and handoff_source in normalized_text(context_row.get("source_name", ""))


def build_handoff_target_inventory(
    handoff_payload: dict[str, Any] | None,
    context_inventory_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not handoff_payload:
        return []
    rows: list[dict[str, Any]] = []
    research_id = str(handoff_payload.get("research_id", ""))
    generated_at = str(handoff_payload.get("generated_at", ""))
    for target in flatten_handoff_targets(handoff_payload):
        matches = [row for row in context_inventory_rows if handoff_target_matches_context(target, row)]
        collected_matches = [row for row in matches if row.get("collection_status") == "collected"]
        best_match = collected_matches[0] if collected_matches else (matches[0] if matches else None)
        rows.append(
            {
                "research_id": research_id,
                "handoff_generated_at": generated_at,
                "river_scope": target.get("river_scope", ""),
                "rank": target.get("rank", ""),
                "source_slug": target.get("source_slug", ""),
                "source_name": target.get("source_name", ""),
                "dataset_name": target.get("dataset_name", ""),
                "source_family": target.get("source_family", ""),
                "collection_method_hint": target.get("collection_method_hint", ""),
                "access_type": target.get("access_type", ""),
                "handoff_status": target.get("handoff_status", ""),
                "target_window_years": target.get("target_window_years", TARGET_COVERAGE_YEARS),
                "expected_period_start": target.get("expected_period_start", ""),
                "expected_period_end": target.get("expected_period_end", ""),
                "notes_on_asymmetry": target.get("notes_on_asymmetry", ""),
                "currently_matched": "yes" if best_match else "",
                "current_run_id": "" if best_match is None else best_match.get("run_id", ""),
                "current_collection_status": "" if best_match is None else best_match.get("collection_status", ""),
                "current_thematic_axis": "" if best_match is None else best_match.get("thematic_axis", ""),
                "current_priority_reason": "" if best_match is None else best_match.get("priority_reason", ""),
            }
        )
    return rows


def build_river_mainstem_analytic(
    usgs_site_summary: list[dict[str, Any]],
    river_wqp_summary: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in usgs_site_summary:
        returned_years = int(row["years_returned"])
        rows.append(
            {
                "entity_group": "River",
                "entity": row["site_label"],
                "layer": "hydrology",
                "source": "USGS daily values",
                "reach": row["reach"],
                "first_year": row["first_year"],
                "last_year": row["last_year"],
                "returned_years": returned_years,
                "target_years": TARGET_COVERAGE_YEARS,
                "coverage_gap_years": max(TARGET_COVERAGE_YEARS - returned_years, 0),
                "coverage_status": coverage_status(returned_years),
                "record_count": row["point_count"],
                "parameter_count": row["variable_count"],
            }
        )
    for row in river_wqp_summary:
        returned_years = int(row["years_with_data"]) if row["years_with_data"] != "" else 0
        rows.append(
            {
                "entity_group": "River",
                "entity": row["site_label"],
                "layer": "water_quality",
                "source": "WQP results",
                "reach": row["reach"],
                "first_year": row["first_year"],
                "last_year": row["last_year"],
                "returned_years": returned_years,
                "target_years": TARGET_COVERAGE_YEARS,
                "coverage_gap_years": max(TARGET_COVERAGE_YEARS - returned_years, 0),
                "coverage_status": coverage_status(returned_years),
                "record_count": row["result_count"],
                "parameter_count": "",
            }
        )
    rows.sort(key=lambda row: (row["layer"], entity_sort_key(row["entity"], USGS_SITE_ORDER + RIVER_SITE_ORDER)))
    return rows


def build_reservoir_annex_analytic(
    usace_rows: list[dict[str, Any]],
    nid_rows: list[dict[str, Any]],
    reservoir_wqp_summary: list[dict[str, Any]],
    reservoir_operation_summary: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in nid_rows:
        rows.append(
            {
                "reservoir": row["reservoir"],
                "layer": "structure",
                "source": "NID inventory",
                "first_year": row["year_completed"],
                "last_year": row["year_completed"],
                "returned_years": "",
                "target_years": TARGET_COVERAGE_YEARS,
                "coverage_gap_years": "",
                "coverage_status": "metadata",
                "record_count": 1,
                "support_value_1": row["surface_area_acres"],
                "support_value_2": row["drainage_area_sqmi"],
            }
        )
    best_operation_rows: dict[str, dict[str, Any]] = {}
    for row in reservoir_operation_summary:
        current = best_operation_rows.get(row["reservoir"])
        if current is None or int(row["years_returned"]) > int(current["years_returned"]):
            best_operation_rows[row["reservoir"]] = row
    for row in usace_rows:
        operation_row = best_operation_rows.get(row["reservoir"])
        rows.append(
            {
                "reservoir": row["reservoir"],
                "layer": "operations_series",
                "source": "" if operation_row is None else f"USACE series ({operation_row['metric_label']})",
                "first_year": "" if operation_row is None else operation_row["first_year"],
                "last_year": "" if operation_row is None else operation_row["last_year"],
                "returned_years": 0 if operation_row is None else operation_row["years_returned"],
                "target_years": TARGET_COVERAGE_YEARS,
                "coverage_gap_years": TARGET_COVERAGE_YEARS if operation_row is None else max(TARGET_COVERAGE_YEARS - int(operation_row["years_returned"]), 0),
                "coverage_status": "snapshot" if operation_row is None else coverage_status(int(operation_row["years_returned"])),
                "record_count": "" if operation_row is None else operation_row["point_count"],
                "support_value_1": row["current_inflow_cfs"],
                "support_value_2": row["current_outflow_cfs"],
            }
        )
    for row in reservoir_wqp_summary:
        returned_years = int(row["years_with_data"]) if row["years_with_data"] != "" else 0
        rows.append(
            {
                "reservoir": row["reservoir"],
                "layer": "forebay_water_quality",
                "source": "WQP forebay",
                "first_year": row["first_year"],
                "last_year": row["last_year"],
                "returned_years": returned_years,
                "target_years": TARGET_COVERAGE_YEARS,
                "coverage_gap_years": max(TARGET_COVERAGE_YEARS - returned_years, 0),
                "coverage_status": coverage_status(returned_years),
                "record_count": row["result_count"],
                "support_value_1": row["activity_count"],
                "support_value_2": "",
            }
        )
    rows.sort(key=lambda row: (entity_sort_key(row["reservoir"], RESERVOIR_ORDER), row["layer"]))
    return rows


def build_pressure_source_analytic(
    context_inventory_rows: list[dict[str, Any]],
    handoff_inventory_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in context_inventory_rows:
        if row["analytical_role"] != "pressure_core":
            continue
        rows.append(
            {
                "source_stage": "collected_context",
                "scope": row["thematic_axis"],
                "dataset_name": row["dataset_name"],
                "source_name": row["source_name"],
                "status": row["collection_status"],
                "period_start": row["period_start"],
                "period_end": row["period_end"],
                "coverage_years": row["coverage_years"],
                "target_years": row["target_years"],
                "priority_reason": row["priority_reason"],
            }
        )
    for row in handoff_inventory_rows:
        if row["river_scope"] != "corridor_pressure":
            continue
        rows.append(
            {
                "source_stage": "discovery_handoff",
                "scope": row["river_scope"],
                "dataset_name": row["dataset_name"],
                "source_name": row["source_name"],
                "status": row["handoff_status"],
                "period_start": row["expected_period_start"],
                "period_end": row["expected_period_end"],
                "coverage_years": "",
                "target_years": row["target_window_years"],
                "priority_reason": row["notes_on_asymmetry"],
            }
        )
    rows.sort(key=lambda row: (row["source_stage"], row["scope"], row["dataset_name"]))
    return rows


def build_sediment_bridge_analytic(
    sediment_score_rows: list[dict[str, Any]],
    sediment_pairwise_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in sediment_score_rows[:10]:
        rows.append(
            {
                "record_type": "top_site",
                "site": row["site"],
                "metric": "fine_depositional_score",
                "value": row["fine_depositional_score"],
                "aux_1": row["fe_ppm"],
                "aux_2": row["carbon_pct"],
            }
        )
    for row in sediment_pairwise_rows:
        rows.append(
            {
                "record_type": "pairwise_relation",
                "site": "",
                "metric": f"{row['x_field']}__{row['y_field']}",
                "value": row["correlation"],
                "aux_1": row["slope"],
                "aux_2": row["direction"],
            }
        )
    return rows


def build_coverage_analytic(coverage_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in coverage_rows:
        returned_years = int(row["returned_years"]) if str(row["returned_years"]) not in ("", "None") else 0
        gap_years = TARGET_COVERAGE_YEARS if row["coverage_kind"] == "snapshot" else max(TARGET_COVERAGE_YEARS - returned_years, 0)
        enriched = dict(row)
        enriched["coverage_gap_years"] = gap_years
        rows.append(enriched)
    return rows


def build_domain_registry(
    context_inventory_rows: list[dict[str, Any]],
    river_daily_rows: list[dict[str, Any]],
    river_monthly_rows: list[dict[str, Any]],
    river_annual_rows: list[dict[str, Any]],
    river_wqp_summary: list[dict[str, Any]],
    savannah_main_detail_rows: list[dict[str, Any]],
    savannah_main_summary_rows: list[dict[str, Any]],
    reservoir_operation_monthly_rows: list[dict[str, Any]],
    reservoir_operation_summary_rows: list[dict[str, Any]],
    usace_rows: list[dict[str, Any]],
    nid_rows: list[dict[str, Any]],
    sediment_rows: list[dict[str, Any]],
    sediment_score_rows: list[dict[str, Any]],
    sediment_pairwise_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    handoff_inventory_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    def year_bounds(rows: list[dict[str, Any]], key: str) -> tuple[str, str]:
        years = sorted({int(row[key]) for row in rows if str(row.get(key, "")).strip() not in ("", "None")})
        if not years:
            return "", ""
        return str(years[0]), str(years[-1])

    def count_context(role: str) -> int:
        return sum(1 for row in context_inventory_rows if row["analytical_role"] == role)

    river_first, river_last = year_bounds(river_daily_rows, "year")
    monthly_first, monthly_last = year_bounds(river_monthly_rows, "year")
    annual_first, annual_last = year_bounds(river_annual_rows, "year")
    savannah_main_first, savannah_main_last = year_bounds(savannah_main_summary_rows, "data_year")

    best_reservoir_operation_years = 0
    reservoir_first = ""
    reservoir_last = ""
    if reservoir_operation_summary_rows:
        best_row = max(reservoir_operation_summary_rows, key=lambda row: int(row.get("years_returned") or 0))
        best_reservoir_operation_years = int(best_row.get("years_returned") or 0)
        reservoir_first = str(best_row.get("first_year") or "")
        reservoir_last = str(best_row.get("last_year") or "")

    rows = [
        {
            "domain_id": "river_core",
            "domain_label": DOMAIN_LABELS["river_core"],
            "layer_name": "usgs_river_daily_long",
            "layer_stage": "staging",
            "layer_path": "data/staging/clarks_hill/usgs_river_daily_long.csv",
            "grain": "daily",
            "entity_keys": "site_no|series_slug",
            "time_keys": "date|year|month|ano_mes",
            "join_keys": "site_no|series_slug|date|ano_mes|year",
            "crossing_priority": "primary",
            "readiness": "ready",
            "first_year": river_first,
            "last_year": river_last,
            "record_count": len(river_daily_rows),
            "coverage_note": "Main hydrologic and continuous sensor backbone for river-first analysis.",
        },
        {
            "domain_id": "river_core",
            "domain_label": DOMAIN_LABELS["river_core"],
            "layer_name": "river_monthly_behavior",
            "layer_stage": "staging",
            "layer_path": "data/staging/clarks_hill/river_monthly_behavior.csv",
            "grain": "monthly",
            "entity_keys": "site_no|series_slug",
            "time_keys": "ano_mes|year|month",
            "join_keys": "site_no|series_slug|ano_mes|year|month",
            "crossing_priority": "primary",
            "readiness": "ready",
            "first_year": monthly_first,
            "last_year": monthly_last,
            "record_count": len(river_monthly_rows),
            "coverage_note": "Canonical crossing layer for river x reservoir monthly behavior.",
        },
        {
            "domain_id": "river_core",
            "domain_label": DOMAIN_LABELS["river_core"],
            "layer_name": "river_annual_anomalies",
            "layer_stage": "staging",
            "layer_path": "data/staging/clarks_hill/river_annual_anomalies.csv",
            "grain": "annual",
            "entity_keys": "site_no|series_slug",
            "time_keys": "year",
            "join_keys": "site_no|series_slug|year",
            "crossing_priority": "primary",
            "readiness": "ready",
            "first_year": annual_first,
            "last_year": annual_last,
            "record_count": len(river_annual_rows),
            "coverage_note": "Canonical annual layer for river x pressure and river x compliance crossings.",
        },
        {
            "domain_id": "river_core",
            "domain_label": DOMAIN_LABELS["river_core"],
            "layer_name": "wqp_river_sites_summary",
            "layer_stage": "staging",
            "layer_path": "data/staging/clarks_hill/wqp_river_sites_summary.csv",
            "grain": "site_summary",
            "entity_keys": "site_id|site_label",
            "time_keys": "first_year|last_year",
            "join_keys": "site_id|site_label",
            "crossing_priority": "secondary",
            "readiness": "partial",
            "first_year": "" if not river_wqp_summary else str(min(int(row["first_year"]) for row in river_wqp_summary if row.get("first_year"))),
            "last_year": "" if not river_wqp_summary else str(max(int(row["last_year"]) for row in river_wqp_summary if row.get("last_year"))),
            "record_count": len(river_wqp_summary),
            "coverage_note": "Discrete river chemistry remains sparse, but the domain is still explicit and separable.",
        },
        {
            "domain_id": "pressure_core",
            "domain_label": DOMAIN_LABELS["pressure_core"],
            "layer_name": "savannah_main_treated_water_long",
            "layer_stage": "staging",
            "layer_path": "data/staging/clarks_hill/savannah_main_treated_water_long.csv",
            "grain": "parameter_year",
            "entity_keys": "system_number|parameter_slug|table_kind",
            "time_keys": "report_year|data_year",
            "join_keys": "system_number|parameter_slug|data_year",
            "crossing_priority": "primary",
            "readiness": "ready",
            "first_year": savannah_main_first,
            "last_year": savannah_main_last,
            "record_count": len(savannah_main_detail_rows),
            "coverage_note": "Lower-basin treated-water compliance layer; pressure-like, but not raw-river chemistry.",
        },
        {
            "domain_id": "pressure_core",
            "domain_label": DOMAIN_LABELS["pressure_core"],
            "layer_name": "savannah_main_treated_water_summary",
            "layer_stage": "staging",
            "layer_path": "data/staging/clarks_hill/savannah_main_treated_water_summary.csv",
            "grain": "annual",
            "entity_keys": "system_number",
            "time_keys": "report_year|data_year",
            "join_keys": "system_number|data_year",
            "crossing_priority": "primary",
            "readiness": "ready",
            "first_year": savannah_main_first,
            "last_year": savannah_main_last,
            "record_count": len(savannah_main_summary_rows),
            "coverage_note": "Best pressure/compliance annual crossing layer currently available.",
        },
        {
            "domain_id": "pressure_core",
            "domain_label": DOMAIN_LABELS["pressure_core"],
            "layer_name": "savannah_main_violation_details",
            "layer_stage": "staging",
            "layer_path": "data/staging/clarks_hill/savannah_main_violation_details.csv",
            "grain": "event_detail",
            "entity_keys": "system_number|parameter_slug",
            "time_keys": "report_year|data_year",
            "join_keys": "system_number|parameter_slug|data_year",
            "crossing_priority": "secondary",
            "readiness": "ready" if savannah_main_detail_rows else "partial",
            "first_year": savannah_main_first,
            "last_year": savannah_main_last,
            "record_count": len([row for row in savannah_main_summary_rows if int(row.get("violation_flag") or 0) == 1]),
            "coverage_note": "Violation/event layer for aligning compliance incidents with river conditions.",
        },
        {
            "domain_id": "pressure_core",
            "domain_label": DOMAIN_LABELS["pressure_core"],
            "layer_name": "pressure_source_inventory",
            "layer_stage": "analytic",
            "layer_path": "data/analytic/clarks_hill/pressure_source_inventory.csv",
            "grain": "source_inventory",
            "entity_keys": "dataset_name|source_name",
            "time_keys": "period_start|period_end",
            "join_keys": "dataset_name|source_name",
            "crossing_priority": "secondary",
            "readiness": "partial",
            "first_year": "",
            "last_year": "",
            "record_count": count_context("pressure_core"),
            "coverage_note": "Structured pressure inventory is present, but many sources still need tabular extraction before direct crossings.",
        },
        {
            "domain_id": "reservoir_support",
            "domain_label": DOMAIN_LABELS["reservoir_support"],
            "layer_name": "reservoir_operations_monthly",
            "layer_stage": "staging",
            "layer_path": "data/staging/clarks_hill/reservoir_operations_monthly.csv",
            "grain": "monthly",
            "entity_keys": "reservoir|metric_slug",
            "time_keys": "ano_mes|year|month",
            "join_keys": "reservoir|metric_slug|ano_mes|year|month",
            "crossing_priority": "primary",
            "readiness": "ready" if reservoir_operation_monthly_rows else "partial",
            "first_year": reservoir_first,
            "last_year": reservoir_last,
            "record_count": len(reservoir_operation_monthly_rows),
            "coverage_note": "Reservoir annex for monthly modulation of the river signal.",
        },
        {
            "domain_id": "reservoir_support",
            "domain_label": DOMAIN_LABELS["reservoir_support"],
            "layer_name": "usace_system_snapshot",
            "layer_stage": "staging",
            "layer_path": "data/staging/clarks_hill/usace_system_snapshot.csv",
            "grain": "snapshot",
            "entity_keys": "reservoir",
            "time_keys": "",
            "join_keys": "reservoir",
            "crossing_priority": "tertiary",
            "readiness": "ready" if usace_rows else "partial",
            "first_year": "",
            "last_year": "",
            "record_count": len(usace_rows),
            "coverage_note": "Useful structural and current-condition context, but not the main crossing layer.",
        },
        {
            "domain_id": "reservoir_support",
            "domain_label": DOMAIN_LABELS["reservoir_support"],
            "layer_name": "nid_system_summary",
            "layer_stage": "staging",
            "layer_path": "data/staging/clarks_hill/nid_system_summary.csv",
            "grain": "metadata",
            "entity_keys": "reservoir|nidid",
            "time_keys": "year_completed",
            "join_keys": "reservoir|nidid",
            "crossing_priority": "tertiary",
            "readiness": "ready" if nid_rows else "partial",
            "first_year": "",
            "last_year": "",
            "record_count": len(nid_rows),
            "coverage_note": "Structural support metadata only.",
        },
        {
            "domain_id": "sediment_response",
            "domain_label": DOMAIN_LABELS["sediment_response"],
            "layer_name": "sediment_master_data",
            "layer_stage": "staging",
            "layer_path": "data/staging/clarks_hill/sediment_master_data.csv",
            "grain": "site_sample",
            "entity_keys": "site",
            "time_keys": "campaign_snapshot",
            "join_keys": "site",
            "crossing_priority": "secondary",
            "readiness": "ready" if sediment_rows else "partial",
            "first_year": "2026" if sediment_rows else "",
            "last_year": "2026" if sediment_rows else "",
            "record_count": len(sediment_rows),
            "coverage_note": "Snapshot sediment-response layer; interpretive anchor, not a long time series.",
        },
        {
            "domain_id": "sediment_response",
            "domain_label": DOMAIN_LABELS["sediment_response"],
            "layer_name": "sediment_depositional_scores",
            "layer_stage": "staging",
            "layer_path": "data/staging/clarks_hill/sediment_depositional_scores.csv",
            "grain": "site_score",
            "entity_keys": "site",
            "time_keys": "campaign_snapshot",
            "join_keys": "site",
            "crossing_priority": "secondary",
            "readiness": "ready" if sediment_score_rows else "partial",
            "first_year": "2026" if sediment_score_rows else "",
            "last_year": "2026" if sediment_score_rows else "",
            "record_count": len(sediment_score_rows),
            "coverage_note": "Canonical response layer for linking fine depositional behavior back to river context.",
        },
        {
            "domain_id": "sediment_response",
            "domain_label": DOMAIN_LABELS["sediment_response"],
            "layer_name": "sediment_bridge_summary",
            "layer_stage": "analytic",
            "layer_path": "data/analytic/clarks_hill/sediment_bridge_summary.csv",
            "grain": "summary_relation",
            "entity_keys": "site|metric",
            "time_keys": "campaign_snapshot",
            "join_keys": "site|metric",
            "crossing_priority": "secondary",
            "readiness": "ready" if sediment_pairwise_rows else "partial",
            "first_year": "2026" if sediment_pairwise_rows else "",
            "last_year": "2026" if sediment_pairwise_rows else "",
            "record_count": len(sediment_pairwise_rows),
            "coverage_note": "Interpretive bridge layer for sediment-facing summaries used by the report.",
        },
        {
            "domain_id": "supporting_context",
            "domain_label": DOMAIN_LABELS["supporting_context"],
            "layer_name": "context_source_inventory",
            "layer_stage": "staging",
            "layer_path": "data/staging/clarks_hill/context_source_inventory.csv",
            "grain": "source_inventory",
            "entity_keys": "target_id|dataset_name",
            "time_keys": "period_start|period_end",
            "join_keys": "target_id|dataset_name",
            "crossing_priority": "control",
            "readiness": "ready",
            "first_year": "",
            "last_year": "",
            "record_count": len(context_inventory_rows),
            "coverage_note": "Provenance and gap-tracking layer, not a crossing layer.",
        },
        {
            "domain_id": "supporting_context",
            "domain_label": DOMAIN_LABELS["supporting_context"],
            "layer_name": "coverage_target_matrix",
            "layer_stage": "analytic",
            "layer_path": "data/analytic/clarks_hill/coverage_target_matrix.csv",
            "grain": "coverage_inventory",
            "entity_keys": "layer|entity",
            "time_keys": "first_year|last_year",
            "join_keys": "layer|entity",
            "crossing_priority": "control",
            "readiness": "ready",
            "first_year": "",
            "last_year": "",
            "record_count": len(coverage_rows),
            "coverage_note": "Coverage QA layer for every domain before crossing.",
        },
        {
            "domain_id": "supporting_context",
            "domain_label": DOMAIN_LABELS["supporting_context"],
            "layer_name": "collection_preflight_inventory",
            "layer_stage": "analytic",
            "layer_path": "data/analytic/clarks_hill/collection_preflight_inventory.csv",
            "grain": "handoff_inventory",
            "entity_keys": "research_id|source_slug",
            "time_keys": "handoff_generated_at",
            "join_keys": "research_id|source_slug",
            "crossing_priority": "control",
            "readiness": "ready" if handoff_inventory_rows else "partial",
            "first_year": "",
            "last_year": "",
            "record_count": len(handoff_inventory_rows),
            "coverage_note": "Discovery-to-collection audit layer.",
        },
    ]
    rows.sort(key=lambda row: (DOMAIN_ORDER.index(row["domain_id"]), row["layer_stage"], row["layer_name"]))
    return rows


def build_crosswalk_registry(
    reservoir_operation_monthly_rows: list[dict[str, Any]],
    savannah_main_summary_rows: list[dict[str, Any]],
    bridge_rows: list[dict[str, Any]],
    savannah_main_bridge_rows: list[dict[str, Any]],
    sediment_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = [
        {
            "crosswalk_id": "river_monthly__reservoir_monthly",
            "left_domain_id": "river_core",
            "right_domain_id": "reservoir_support",
            "left_layer": "river_monthly_behavior",
            "right_layer": "reservoir_operations_monthly",
            "output_layer": "data/analytic/clarks_hill/river_reservoir_bridge.csv",
            "join_grain": "monthly",
            "join_keys": "ano_mes|year|month",
            "crossing_status": "ready" if bridge_rows and reservoir_operation_monthly_rows else "partial",
            "interpretation_rule": "Use this crossing to test how cascade regulation modulates the river signal without replacing the river as protagonist.",
            "caveat": "Reservoir parity is still weaker than the river layer, especially outside Thurmond.",
        },
        {
            "crosswalk_id": "river_annual__pressure_annual",
            "left_domain_id": "river_core",
            "right_domain_id": "pressure_core",
            "left_layer": "river_annual_anomalies",
            "right_layer": "savannah_main_treated_water_summary",
            "output_layer": "data/analytic/clarks_hill/savannah_main_treated_water_bridge.csv",
            "join_grain": "annual",
            "join_keys": "data_year",
            "crossing_status": "ready" if savannah_main_bridge_rows and savannah_main_summary_rows else "partial",
            "interpretation_rule": "Use annual river behavior to contextualize treated-water compliance and pressure-like signals in the lower basin.",
            "caveat": "This is a lower-basin treated-water compliance bridge, not a substitute for raw-river chemistry.",
        },
        {
            "crosswalk_id": "river_core__pressure_inventory",
            "left_domain_id": "river_core",
            "right_domain_id": "pressure_core",
            "left_layer": "river_mainstem_layers",
            "right_layer": "pressure_source_inventory",
            "output_layer": "",
            "join_grain": "narrative_or_segment",
            "join_keys": "reach|year_window",
            "crossing_status": "partial",
            "interpretation_rule": "Use this crossing to move from river behavior to pollutant and discharge context once more pressure sources are tabularized.",
            "caveat": "Most pressure sources are still inventory-level, not joined event series.",
        },
        {
            "crosswalk_id": "river_core__sediment_response",
            "left_domain_id": "river_core",
            "right_domain_id": "sediment_response",
            "left_layer": "river_annual_anomalies",
            "right_layer": "sediment_depositional_scores",
            "output_layer": "data/analytic/clarks_hill/sediment_bridge_summary.csv",
            "join_grain": "interpretive_window",
            "join_keys": "thurmond_focus|campaign_context",
            "crossing_status": "partial" if sediment_rows else "pending",
            "interpretation_rule": "Use the river layer to explain whether hydrologic and quality context is compatible with the observed depositional pattern at Thurmond.",
            "caveat": "Sediments are a 2026 site campaign and should not be treated as a long time series.",
        },
        {
            "crosswalk_id": "pressure_core__sediment_response",
            "left_domain_id": "pressure_core",
            "right_domain_id": "sediment_response",
            "left_layer": "savannah_main_treated_water_summary",
            "right_layer": "sediment_depositional_scores",
            "output_layer": "",
            "join_grain": "interpretive_window",
            "join_keys": "lower_basin_context|campaign_context",
            "crossing_status": "partial" if savannah_main_summary_rows and sediment_rows else "pending",
            "interpretation_rule": "Use this crossing carefully as contextual support for sediment interpretation, never as direct causality.",
            "caveat": "Compliance data and sediment-response data operate at different spatial and causal grains.",
        },
    ]
    return rows


def build_inventory_markdown(
    river_manifest: dict[str, Any],
    reservoir_manifest: dict[str, Any],
    usgs_site_summary: list[dict[str, Any]],
    river_wqp_summary: list[dict[str, Any]],
    reservoir_wqp_summary: list[dict[str, Any]],
    sediment_rows: list[dict[str, Any]],
    score_rows: list[dict[str, Any]],
    context_inventory_rows: list[dict[str, Any]],
) -> str:
    river_core_gaps = [
        row for row in context_inventory_rows if row["requires_priority_followup"] == "yes" and row["analytical_role"] == "river_core"
    ]
    pressure_gaps = [
        row for row in context_inventory_rows if row["requires_priority_followup"] == "yes" and row["analytical_role"] == "pressure_core"
    ]
    operations_gaps = [
        row for row in context_inventory_rows if row["requires_priority_followup"] == "yes" and row["thematic_axis"] == "reservoir_operations"
    ]
    lines = [
        "# Savannah River Inventory",
        "",
        f"- River collection run: `{river_manifest['run_id']}`",
        f"- River targets collected: `{river_manifest['collected_count']}/{river_manifest['target_count']}`",
        f"- Reservoir annex run: `{reservoir_manifest['run_id']}`",
        f"- Reservoir annex targets collected: `{reservoir_manifest['collected_count']}/{reservoir_manifest['target_count']}`",
        "- Analytical frame: `river-first`",
        "- Target coverage rule: `always request 20 years when the source allows it`",
        "",
        "## Mainstem hydrology integrated now",
        "",
    ]
    for row in usgs_site_summary:
        lines.append(
            f"- `{row['site_label']}` | {row['first_year']} to {row['last_year']} | "
            f"{row['years_returned']} returned years | {row['variable_count']} parameter codes | {int(row['point_count']):,} daily points"
        )
    lines.extend(["", "## River chemistry integrated now", ""])
    for row in river_wqp_summary:
        lines.append(
            f"- `{row['site_label']}` | {row['first_year']} to {row['last_year']} | "
            f"{row['years_with_data']} years with data | {row['activity_count']} activities | {row['result_count']} results"
        )
    lines.extend(["", "## Reservoir annex integrated now", ""])
    for row in reservoir_wqp_summary:
        lines.append(
            f"- `{row['reservoir']}` | {row['first_year']} to {row['last_year']} | "
            f"{row['years_with_data']} years with data in the forebay WQP layer"
        )
    lines.extend(["", "## Sediment notebook materialized now", ""])
    lines.append(
        f"- `Master Data` parsed to `{len(sediment_rows)}` valid sediment sites using the same notebook filter (`Site` and `Fe_ppm` present, `1 <= Site <= 30`)."
    )
    if score_rows:
        top_sites = ", ".join(str(row["site"]) for row in score_rows[:5])
        lines.append(f"- Top fine-depositional-score sites in the current staging pass: `{top_sites}`.")
    lines.extend(
        [
            "",
            "## Analytical caveats",
            "",
            f"- The 20-year target is satisfied by `{len(usgs_site_summary)}` mainstem USGS endpoints in the current staging pass, but river WQP chemistry remains below that target at most sites.",
            "- River chemistry is now real and explicit, but it remains patchier and older than the daily hydrology layer.",
            "- Reservoir operations remain necessary as explanatory modulation, not as the protagonist of the report.",
            "- Thurmond stays the sediment-study target, but the causal path should now start from the river signal.",
            "",
            "## Next collection priorities",
            "",
        ]
    )
    if river_core_gaps:
        lines.append(f"- River-first gaps still active: `{len(river_core_gaps)}` priority targets or layers need stronger mainstem coverage.")
    if pressure_gaps:
        lines.append(f"- Pressure and pollutant gaps still active: `{len(pressure_gaps)}` contextual targets still need structured ingestion.")
    if operations_gaps:
        lines.append(f"- Operational long-series gaps still active: `{len(operations_gaps)}` reservoir-operation layers remain snapshot-only or short.")
    if not any([river_core_gaps, pressure_gaps, operations_gaps]):
        lines.append("- No priority follow-up rows are flagged in the current intake inventory.")
    lines.append("")
    return "\n".join(lines)


def build_report_context(
    river_manifest_path: Path,
    reservoir_manifest_path: Path,
    legacy_manifest_path: Path | None,
    river_manifest: dict[str, Any],
    reservoir_manifest: dict[str, Any],
    legacy_manifest: dict[str, Any] | None,
    usgs_site_summary: list[dict[str, Any]],
    river_monthly_rows: list[dict[str, Any]],
    river_climatology_rows: list[dict[str, Any]],
    river_correlation_rows: list[dict[str, Any]],
    river_wqp_summary: list[dict[str, Any]],
    reservoir_wqp_summary: list[dict[str, Any]],
    usace_rows: list[dict[str, Any]],
    reservoir_operation_summary_rows: list[dict[str, Any]],
    bridge_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    sediment_rows: list[dict[str, Any]],
    score_rows: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
    parameter_overlap_rows: list[dict[str, Any]],
    context_inventory_rows: list[dict[str, Any]],
    domain_registry_rows: list[dict[str, Any]],
    crosswalk_registry_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    reservoir_years = [
        int(row["first_year"]) for row in reservoir_wqp_summary if row.get("first_year")
    ]
    reservoir_last_years = [
        int(row["last_year"]) for row in reservoir_wqp_summary if row.get("last_year")
    ]
    river_first_years = [
        int(row["first_year"]) for row in river_wqp_summary if row.get("first_year")
    ]
    river_last_years = [
        int(row["last_year"]) for row in river_wqp_summary if row.get("last_year")
    ]
    hydrology_window = (
        f"{min(int(row['first_year']) for row in usgs_site_summary)}-"
        f"{max(int(row['last_year']) for row in usgs_site_summary)}"
        if usgs_site_summary
        else ""
    )
    monthly_window_lookup = {
        row["series_slug"]: (
            min(item["ano_mes"] for item in river_monthly_rows if item["series_slug"] == row["series_slug"]),
            max(item["ano_mes"] for item in river_monthly_rows if item["series_slug"] == row["series_slug"]),
        )
        for row in river_monthly_rows
    }
    dock_quality_window = ""
    if "dock_water_temp_c" in monthly_window_lookup:
        dock_quality_window = f"{monthly_window_lookup['dock_water_temp_c'][0][:4]}-{monthly_window_lookup['dock_water_temp_c'][1][:4]}"
    best_bridge = max(river_correlation_rows, key=lambda row: abs(float(row["correlation"]))) if river_correlation_rows else None
    operation_best_by_reservoir: dict[str, dict[str, Any]] = {}
    for row in reservoir_operation_summary_rows:
        current = operation_best_by_reservoir.get(row["reservoir"])
        if current is None or int(row["years_returned"]) > int(current["years_returned"]):
            operation_best_by_reservoir[row["reservoir"]] = row
    reservoir_operation_text = ", ".join(
        f"{reservoir} {operation_best_by_reservoir[reservoir]['first_year']}-{operation_best_by_reservoir[reservoir]['last_year']}"
        for reservoir in RESERVOIR_ORDER
        if reservoir in operation_best_by_reservoir
    )
    reservoir_wqp_first = min(reservoir_years) if reservoir_years else None
    reservoir_wqp_last = max(reservoir_last_years) if reservoir_last_years else None
    sparse_window = (
        f"{min(river_first_years)}-{max(river_last_years)}"
        if river_first_years and river_last_years
        else ""
    )
    top_score_sites = [row["site"] for row in score_rows[:5]]
    overlap_entities = len({row["entity"] for row in parameter_overlap_rows})
    strongest_pair = max(pairwise_rows, key=lambda row: abs(float(row["correlation"]))) if pairwise_rows else None
    priority_rows = [row for row in context_inventory_rows if row["requires_priority_followup"] == "yes"]
    reservoir_wqp_window = (
        f"{reservoir_wqp_first}-{reservoir_wqp_last}"
        if reservoir_wqp_first is not None and reservoir_wqp_last is not None
        else "window pending"
    )
    coverage_layers = []
    for row in coverage_rows:
        first_year = row.get("first_year")
        last_year = row.get("last_year")
        actual_period = ""
        if first_year and last_year:
            actual_period = f"{first_year}-{last_year}"
        returned_years = int(row.get("returned_years") or 0)
        target_years = int(row.get("target_years") or TARGET_COVERAGE_YEARS)
        gap_years = max(target_years - returned_years, 0)
        if row.get("coverage_status") == "snapshot":
            gap_years = target_years
        coverage_layers.append(
            {
                "layer": row["layer"],
                "entity": row["entity"],
                "source": row["source"],
                "returned_years": returned_years,
                "target_years": target_years,
                "coverage_gap_years": gap_years,
                "coverage_status": row["coverage_status"],
                "coverage_kind": row["coverage_kind"],
                "actual_period": actual_period,
            }
        )
    priority_text = [
        "River water quality on the mainstem remains the first priority when returned chemistry stays short of the 20-year target.",
        "Additional mainstem gauges should be added whenever they extend continuity above, between, or below Hartwell, Russell, and Thurmond.",
        "Pollutants and environmental pressures need structured joins, not only PDF references, before the river narrative can match the Tiete benchmark.",
        "Operational support should move from snapshots to long series wherever USACE or companion sources expose multi-decade histories.",
    ]
    ready_crosswalks = [row for row in crosswalk_registry_rows if row["crossing_status"] == "ready"]
    return {
        "report_title": "Savannah River Mainstem",
        "report_subtitle": "Behavior-first context for Clarks Hill sediments: river, reservoirs, pressures, then sediment response",
        "context_summary": (
            "This report is meant to tell a simple river story before it reaches the sediment notebook. It starts with the Savannah "
            "River near Augusta, then adds the reservoir cascade upstream of that reach, then turns to the pollutant and pressure-like "
            "signals we currently have for the lower basin, and only then closes with the sediment interpretation at Thurmond. "
            f"The backbone is {hydrology_window} of USGS mainstem behavior, operational series from Hartwell, Russell, and Thurmond, "
            "and the modern Savannah Main compliance reports that give the best current pollutant-like time slice available in the workspace."
        ),
        "metadata": {
            "date_label": "April 2026",
            "status_badge": "River-first + 20-year target explicit",
        },
        "output_path": "docs/clarks-hill/index.html",
        "narrative_rules": [
            "Keep the Savannah River as the protagonist of the HTML.",
            "Treat pressures and pollutants on the river as analytical core, not optional appendix.",
            "Use Hartwell, Russell, and Thurmond only as explanatory support for the river signal.",
            "Keep the 20-year target visible and separate from real returned coverage in every layer.",
            "Do not imply system-wide parity when evidence is stronger for some layers than others.",
        ],
        "domain_contract": {
            "rule": "Every layer must belong to an explicit domain before any crossing is interpreted.",
            "domains": [
                {
                    "domain_id": domain_id,
                    "domain_label": DOMAIN_LABELS[domain_id],
                    "layer_count": sum(1 for row in domain_registry_rows if row["domain_id"] == domain_id),
                }
                for domain_id in DOMAIN_ORDER
                if any(row["domain_id"] == domain_id for row in domain_registry_rows)
            ],
            "artifacts": [
                "data/staging/clarks_hill/domain_registry.csv",
                "data/analytic/clarks_hill/domain_registry.csv",
                "data/analytic/clarks_hill/crosswalk_registry.csv",
            ],
            "ready_crosswalks": len(ready_crosswalks),
        },
        "coverage_target_years": TARGET_COVERAGE_YEARS,
        "coverage_summary": {
            "rule": "Always request a 20-year historical window when the source allows it, and separate the returned coverage from the target.",
            "actual_summary": (
                f"USGS daily river endpoints meet the target window ({hydrology_window}), lower-river continuous quality extends across {dock_quality_window}, "
                f"and the best river-to-sensor monthly coupling is {best_bridge['source_series_label']} vs {best_bridge['target_series_label']} (r={float(best_bridge['correlation']):.2f})"
                if best_bridge
                else f"USGS daily river endpoints meet the target window ({hydrology_window}), while river WQP chemistry returns are sparse and discontinuous ({sparse_window})."
            ),
            "notes": [
                f"The river run collected {river_manifest['collected_count']} of {river_manifest['target_count']} curated targets with no blockers.",
                f"The reservoir annex run remains available with {reservoir_manifest['collected_count']} of {reservoir_manifest['target_count']} official targets collected.",
                f"Reservoir operational series currently return these best windows: {reservoir_operation_text}.",
                "Thurmond still keeps the strongest sediment-facing operational bridge to Augusta, but the story now starts from the river and only then crosses the cascade.",
                f"The sediment notebook works on {len(sediment_rows)} valid sites from the Master Data table and should be treated as the interpretive anchor for fine texture, Fe enrichment, and Fe-C coupling.",
                f"Cross-layer parameter overlap still covers {overlap_entities} entities across river and reservoir WQP layers, but the main analytical weight now sits in the continuous behavior series rather than the sparse WQP exports.",
                f"The current intake inventory flags {len(priority_rows)} priority follow-up rows for the next gap-focused collection round.",
            ],
        },
        "coverage_layers": coverage_layers,
        "metrics": [
            {
                "label": "River targets collected",
                "value": f"{river_manifest['collected_count']}/{river_manifest['target_count']}",
                "note": river_manifest["run_id"],
                "icon": "hub",
                "tone": "green",
            },
            {
                "label": "USGS daily mainstem coverage",
                "value": hydrology_window,
                "note": f"{len(usgs_site_summary)} official river endpoints returned multi-year daily data",
                "icon": "show_chart",
                "tone": "blue",
            },
            {
                "label": "Lower-river sensor behavior",
                "value": dock_quality_window,
                "note": "USACE Dock carries continuous water temperature, DO, conductance, pH and turbidity behavior",
                "icon": "science",
                "tone": "green",
            },
            {
                "label": "Best river-quality coupling",
                "value": "n/a" if best_bridge is None else f"r={float(best_bridge['correlation']):.2f}",
                "note": "n/a" if best_bridge is None else f"{best_bridge['source_series_label']} vs {best_bridge['target_series_label']}",
                "icon": "multiline_chart",
                "tone": "blue",
            },
            {
                "label": "Reservoir operational support",
                "value": reservoir_operation_text or "3/3",
                "note": "Best available operation windows from the annex series",
                "icon": "water",
                "tone": "gold",
            },
            {
                "label": "Sediment study support",
                "value": f"{len(sediment_rows)} sites",
                "note": "Master Data variables cover texture, water content, D10-D50-D90, Fe, Mn, carbon, pH, DO and conductivity",
                "icon": "experiment",
                "tone": "green",
            },
            {
                "label": "Cross-layer overlap entities",
                "value": str(overlap_entities),
                "note": "Still useful as support, but no longer the main visual anchor",
                "icon": "table_chart",
                "tone": "blue",
            },
            {
                "label": "Priority next-round gaps",
                "value": str(len(priority_rows)),
                "note": "River chemistry, pollutant-pressure joins, extra gauges, and long operational support remain the main backlog",
                "icon": "priority_high",
                "tone": "red",
            },
        ],
        "sources": {
            "river_collection_run": river_manifest["run_id"],
            "reservoir_annex_run": reservoir_manifest["run_id"],
            "legacy_thurmond_detail_run": legacy_manifest["run_id"] if legacy_manifest else "",
            "river_collection_manifest": str(river_manifest_path.relative_to(ROOT)),
            "reservoir_collection_manifest": str(reservoir_manifest_path.relative_to(ROOT)),
            "legacy_thurmond_manifest": str(legacy_manifest_path.relative_to(ROOT)) if legacy_manifest_path else "",
            "sediment_notebook": "analise_sedimentos/Analise_sedimentos_Clarks_Hill_Lake.ipynb",
            "sediment_master_data": "analise_sedimentos/Most Corrected Master_Data Clarks Hill Lake (version 3).xlsb.xlsx",
        },
        "source_note": {
            "text": "Metrics come from local staging tables, figures come from generated SVG artifacts under docs/clarks-hill/figures, and the main charts now prioritize monthly river and reservoir behavior instead of source-inventory coverage alone.",
            "artifacts": [
                "data/staging/clarks_hill/domain_registry.csv",
                "data/staging/clarks_hill/coverage_target_matrix.csv",
                "data/staging/clarks_hill/river_monthly_behavior.csv",
                "data/staging/clarks_hill/river_monthly_climatology.csv",
                "data/staging/clarks_hill/river_quality_flow_correlations.csv",
                "data/staging/clarks_hill/reservoir_operations_monthly.csv",
                "data/staging/clarks_hill/river_reservoir_bridge.csv",
                "data/analytic/clarks_hill/domain_registry.csv",
                "data/analytic/clarks_hill/crosswalk_registry.csv",
                "data/staging/clarks_hill/sediment_master_data.csv",
                "data/staging/clarks_hill/sediment_depositional_scores.csv",
                "data/staging/clarks_hill/sediment_pairwise_relations.csv",
            ],
        },
        "sections": [
            {
                "id": "river-first-frame",
                "title": "River signal first",
                "status": "ready",
                "body": "Open with the Savannah River near Augusta and show the monthly behavior that the rest of the story has to explain.",
            },
            {
                "id": "reservoir-modulation",
                "title": "Reservoir modulation as explanatory annex",
                "status": "ready",
                "body": "Use Hartwell, Russell, and Thurmond as the operational structure that helps explain the river behavior observed downstream of Clarks Hill.",
            },
            {
                "id": "river-pressures-pollutants",
                "title": "River pressures and pollutants",
                "status": "partial",
                "body": "After the behavior panels, show the pollutant and pressure evidence we actually have today: lower-river sensors, treated-water compliance, and the current pressure inventory.",
            },
            {
                "id": "coverage-status",
                "title": "Coverage status against the 20-year target",
                "status": "ready",
                "body": "Expose the real returned period by source, layer, and entity whenever it falls short of the 20-year target. Do not silently shorten the horizon.",
            },
            {
                "id": "thurmond-bridge",
                "title": "Bridge to the Thurmond sediment interpretation",
                "status": "ready",
                "body": "Keep Thurmond as the sediment-study focus, but only after the report shows how river conditions and regulated cascade behavior plausibly connect to the depositional pattern.",
            },
            {
                "id": "methods-and-gaps",
                "title": "Methods, provenance, and remaining gaps",
                "status": "partial",
                "body": "List the artifact paths behind metrics and figures, then state the unresolved river-pressure and long-series gaps plainly.",
            },
        ],
        "next_collection_priorities": priority_text,
        "current_caveats": [
            "Discrete river WQP chemistry is still sparse even after the river-first rebuild, so the stronger water-quality layer currently comes from the continuous USACE Dock sensor series.",
            "Pressure and pollutant context still needs more structured joins to reach the same maturity as hydrology and continuous sensor behavior.",
            "Reservoir operations are now analytical series instead of snapshots, but Hartwell and Russell still return shorter windows than Thurmond.",
            "Hartwell and Russell remain support layers for the river narrative, not independent protagonists of the HTML.",
            "Thurmond is still the sediment-study target, but the next round should deepen river-first explanation before adding more reservoir-first detail.",
        ],
        "sediment_summary": {
            "sample_count": len(sediment_rows),
            "master_data_fields": [
                "Site",
                "Depth",
                "Latitude",
                "Longitude",
                "%Clay",
                "%Silt",
                "%Sand",
                "Water_%",
                "D10",
                "D50",
                "D90",
                "Fe_ppm",
                "Mn_ppm",
                "%Carbon",
                "pH",
                "DO (%)",
                "Cond.",
            ],
            "interpretation_points": [
                "The sediment system is dominated by fine material, especially clay plus silt, with generally low sand fractions.",
                "Iron tracks the fine fraction: it increases with clay and decreases as median grain size D50 becomes coarser.",
                "Total carbon is strongly associated with iron, consistent with organo-mineral coupling and greater carbon preservation in Fe-rich sediments.",
                "Greater depth tends to coincide with finer and more Fe-enriched sediment, reinforcing the interpretation of low-energy depositional zones.",
                "A composite fine-depositional score identifies the sites most consistent with fine, wet, Fe-C enriched depositional settings.",
            ],
            "top_depositional_sites": top_score_sites,
            "strongest_pairwise_relation": strongest_pair,
            "caveat": "The notebook flags any use of D90 in final conclusions when D90 < D50 appears; those values still need manual checking.",
        },
        "figures": [
            {
                "id": "fig1",
                "title": "Savannah River behavior near Augusta: discharge and stage",
                "tag": "River Signal",
                "tag_color": "blue",
                "icon": "show_chart",
                "section": "river-first-frame",
                "image_path": "figures/fig1_river_mainstem_hydrograph.svg",
                "summary": "The opening panel now looks like a river-behavior chart instead of a data-inventory panel: monthly discharge and stage at Augusta, each with a 12-month mean.",
                "interpretation": "This is the mainstem reference for the whole report. Before we talk about reservoirs, pressures, or sediments, we first show how the river itself expands, contracts, and stabilizes across the 20-year window.",
                "highlight": f"Augusta contributes a continuous {hydrology_window} behavior record.",
                "source_refs": FIGURE_SOURCE_REFS["fig1"],
            },
            {
                "id": "fig2",
                "title": "Cascade behavior upstream of Augusta: Hartwell, Russell, and Thurmond outflow",
                "tag": "Operations",
                "tag_color": "orange",
                "icon": "water",
                "section": "reservoir-modulation",
                "image_path": "figures/fig2_cascade_operations.svg",
                "summary": "The reservoir annex now starts with behavior, not cards: three clean monthly outflow panels show how the cascade is operating through time.",
                "interpretation": "This is the first explanatory layer behind the river. The reservoirs are not the protagonist, but their release behavior helps frame why the Savannah signal near Augusta looks the way it does.",
                "highlight": "Hartwell, Russell, and Thurmond now appear as time series instead of static snapshots.",
                "source_refs": FIGURE_SOURCE_REFS["fig2"],
            },
            {
                "id": "fig3",
                "title": "Thurmond to Augusta: reservoir release and downstream response",
                "tag": "Operations",
                "tag_color": "orange",
                "icon": "hub",
                "section": "reservoir-modulation",
                "image_path": "figures/fig3_thurmond_augusta_bridge.svg",
                "summary": "A dedicated bridge panel now ties Thurmond outflow and storage to Augusta discharge, keeping the reservoir role explanatory and downstream-facing.",
                "interpretation": "This is the cleanest operational link in the current workspace. It shows how the river signal near Augusta can carry the imprint of release behavior before the report moves into pollutants and pressures.",
                "highlight": "Thurmond remains the strongest operational bridge into the sediment story.",
                "source_refs": FIGURE_SOURCE_REFS["fig3"],
            },
            {
                "id": "fig4",
                "title": "Lower-river water-quality behavior at USACE Dock",
                "tag": "River Chemistry",
                "tag_color": "green",
                "icon": "science",
                "section": "river-pressures-pollutants",
                "image_path": "figures/fig4_lower_river_quality_timeseries.svg",
                "summary": "Once the behavior of the river and the cascade is clear, the report moves into the continuous quality signals we have downstream: temperature, dissolved oxygen, conductance, and turbidity.",
                "interpretation": "These are still the strongest continuous water-quality-style records in the Savannah workspace. They let the report show real variation in the river corridor instead of only categorical coverage notes.",
                "highlight": f"USACE Dock contributes a continuous {dock_quality_window} quality-behavior layer.",
                "source_refs": FIGURE_SOURCE_REFS["fig4"],
            },
            {
                "id": "fig5",
                "title": "Pollutants and pressure indicators in the lower basin",
                "tag": "Basin Pressures",
                "tag_color": "green",
                "icon": "warning",
                "section": "river-pressures-pollutants",
                "image_path": "figures/fig5_pressures_pollutants.svg",
                "summary": "This panel turns the modern Savannah Main reports into a visual pollutant and pressure layer, instead of leaving them as raw tables or source inventory.",
                "interpretation": "It is not raw mainstem chemistry, but it is still one of the only modern time-structured pollutant-like datasets we currently have in the lower basin. It works as a practical bridge between river behavior and the pressure narrative.",
                "highlight": "The 2020 data year remains the main modern compliance outlier in the current lower-basin slice.",
                "source_refs": FIGURE_SOURCE_REFS["fig5"],
            },
            {
                "id": "fig6",
                "title": "Flow-quality coupling inside the river",
                "tag": "River Chemistry",
                "tag_color": "green",
                "icon": "multiline_chart",
                "section": "river-pressures-pollutants",
                "image_path": "figures/fig6_flow_quality_coupling.svg",
                "summary": "After the time-series panels, the report closes the river-quality block with direct flow-quality relationships.",
                "interpretation": "These scatterplots show which lower-river signals intensify with discharge and which oppose it. They are the clean behavioral bridge from river hydraulics into the pressure-response interpretation.",
                "highlight": "Flow versus conductance remains the strongest current river-only coupling.",
                "source_refs": FIGURE_SOURCE_REFS["fig6"],
            },
            {
                "id": "fig7",
                "title": "Sediment texture and fine-depositional score by site",
                "tag": "Sediment Texture",
                "tag_color": "green",
                "icon": "stacked_bar_chart",
                "section": "thurmond-bridge",
                "image_path": "figures/fig7_sediment_texture_score.svg",
                "summary": "The sediment notebook is materialized as a site-by-site view of texture and a composite depositional score that combines fine fraction, water content, Fe, carbon, D50, and sand.",
                "interpretation": "This figure makes the notebook visible in the report itself. It shows where fine material dominates and which sites are the strongest candidates for low-energy, Fe-C enriched depositional settings.",
                "highlight": f"Sites {', '.join(str(site) for site in top_score_sites[:3]) if top_score_sites else 'n/a'} emerge as the strongest fine-depositional candidates in the current staging pass.",
                "source_refs": FIGURE_SOURCE_REFS["fig7"],
            },
            {
                "id": "fig8",
                "title": "Key sediment geochemical relations: Fe, clay, carbon, depth, and D50",
                "tag": "Sediment Relations",
                "tag_color": "stone",
                "icon": "scatter_plot",
                "section": "thurmond-bridge",
                "image_path": "figures/fig8_sediment_relations.svg",
                "summary": "A multi-panel scatter view reconstructs the main sediment relations used in the notebook, including Fe vs clay, Fe vs D50, carbon vs Fe, and depth vs Fe.",
                "interpretation": "These crossplots close the report's analytical loop. They show that the final sediment claim is not generic: the low-energy interpretation is supported by coherent relations between texture, iron enrichment, carbon preservation, and depth.",
                "highlight": "The Fe-clay and Fe-carbon relations are the clearest visual anchors for the depositional interpretation at Thurmond.",
                "source_refs": FIGURE_SOURCE_REFS["fig8"],
            },
        ],
    }


def main() -> None:
    args = parse_args()
    ensure_dir(args.staging_dir)
    ensure_dir(args.analytic_dir)

    river_manifest_path = resolve_manifest_path(args.river_manifest, RIVER_RUN_PREFIXES)
    reservoir_manifest_path = resolve_manifest_path(args.reservoir_manifest, RESERVOIR_RUN_PREFIXES)
    legacy_manifest_path = resolve_manifest_path(args.legacy_thurmond_manifest, LEGACY_RUN_PREFIXES, required=False)
    savannah_main_manifest_path = resolve_manifest_path(args.savannah_main_manifest, SAVANNAH_MAIN_RUN_PREFIXES, required=False)
    handoff_path = resolve_handoff_path(args.harvester_handoff)

    if river_manifest_path is None or reservoir_manifest_path is None:
        raise SystemExit("Both river and reservoir manifests must be available to build the Savannah river-first staging layer.")

    river_manifest = hydrate_manifest(river_manifest_path, load_json(river_manifest_path))
    reservoir_manifest = hydrate_manifest(reservoir_manifest_path, load_json(reservoir_manifest_path))
    legacy_manifest = hydrate_manifest(legacy_manifest_path, load_json(legacy_manifest_path)) if legacy_manifest_path and legacy_manifest_path.exists() else None
    savannah_main_manifest = (
        hydrate_manifest(savannah_main_manifest_path, load_json(savannah_main_manifest_path))
        if savannah_main_manifest_path and savannah_main_manifest_path.exists()
        else None
    )
    handoff_payload = load_json(handoff_path) if handoff_path and handoff_path.exists() else None

    river_targets = load_manifest_targets(river_manifest)
    reservoir_targets = load_manifest_targets(reservoir_manifest)
    savannah_main_targets = [] if savannah_main_manifest is None else load_manifest_targets(savannah_main_manifest)
    context_inventory_rows = build_context_source_inventory(
        [manifest for manifest in [river_manifest, reservoir_manifest, legacy_manifest, savannah_main_manifest] if manifest]
    )

    usace_rows = build_usace_snapshot(reservoir_targets)
    nid_rows = build_nid_summary(reservoir_targets)
    reservoir_wqp_summary, reservoir_yearly_rows, reservoir_parameter_rows = build_reservoir_wqp_summaries(reservoir_targets)
    river_wqp_summary, river_wqp_yearly_rows, river_wqp_parameter_rows = build_river_wqp_summaries(river_targets)
    usgs_site_summary, usgs_series_rows = build_usgs_river_summaries(river_targets)
    river_daily_rows, river_monthly_rows, river_climatology_rows, river_annual_rows, river_correlation_rows = build_usgs_river_behavior_layers(river_targets)
    reservoir_operation_monthly_rows, reservoir_operation_summary_rows = build_reservoir_operation_layers(reservoir_targets)
    savannah_main_detail_rows, savannah_main_summary_rows, savannah_main_violation_rows = build_savannah_main_report_layers(savannah_main_targets)
    savannah_main_bridge_rows = build_savannah_main_river_bridge(
        savannah_main_summary_rows,
        savannah_main_detail_rows,
        river_annual_rows,
    )
    bridge_rows = build_river_reservoir_bridge(river_monthly_rows, reservoir_operation_monthly_rows)
    coverage_rows = build_coverage_matrix(river_wqp_summary, usgs_site_summary, reservoir_wqp_summary, reservoir_operation_summary_rows)
    coverage_rows.extend(build_savannah_main_coverage_rows(savannah_main_summary_rows))
    sediment_rows, sediment_score_rows, sediment_pairwise_rows = build_sediment_tables(args.sediment_workbook)
    parameter_overlap_rows = build_parameter_overlap_matrix(river_wqp_parameter_rows, reservoir_parameter_rows)
    handoff_inventory_rows = build_handoff_target_inventory(handoff_payload, context_inventory_rows)
    analytic_river_rows = build_river_mainstem_analytic(usgs_site_summary, river_wqp_summary)
    analytic_reservoir_rows = build_reservoir_annex_analytic(usace_rows, nid_rows, reservoir_wqp_summary, reservoir_operation_summary_rows)
    analytic_pressure_rows = build_pressure_source_analytic(context_inventory_rows, handoff_inventory_rows)
    analytic_sediment_rows = build_sediment_bridge_analytic(sediment_score_rows, sediment_pairwise_rows)
    analytic_coverage_rows = build_coverage_analytic(coverage_rows)
    domain_registry_rows = build_domain_registry(
        context_inventory_rows,
        river_daily_rows,
        river_monthly_rows,
        river_annual_rows,
        river_wqp_summary,
        savannah_main_detail_rows,
        savannah_main_summary_rows,
        reservoir_operation_monthly_rows,
        reservoir_operation_summary_rows,
        usace_rows,
        nid_rows,
        sediment_rows,
        sediment_score_rows,
        sediment_pairwise_rows,
        coverage_rows,
        handoff_inventory_rows,
    )
    crosswalk_registry_rows = build_crosswalk_registry(
        reservoir_operation_monthly_rows,
        savannah_main_summary_rows,
        bridge_rows,
        savannah_main_bridge_rows,
        sediment_rows,
    )

    write_csv(
        args.staging_dir / "usace_system_snapshot.csv",
        usace_rows,
        [
            "reservoir",
            "public_name",
            "nidid",
            "nearest_city",
            "latitude",
            "longitude",
            "current_pool_elevation_ft",
            "rule_curve_ft",
            "delta_to_rule_curve_ft",
            "current_storage_acft",
            "storage_pct_conservation",
            "current_inflow_cfs",
            "current_outflow_cfs",
            "current_tailwater_ft",
            "current_power_mwh",
        ],
    )
    write_csv(
        args.staging_dir / "nid_system_summary.csv",
        nid_rows,
        [
            "reservoir",
            "nidid",
            "dam_name",
            "hydraulic_height_ft",
            "dam_length_ft",
            "max_storage_acft",
            "normal_storage_acft",
            "surface_area_acres",
            "drainage_area_sqmi",
            "year_completed",
        ],
    )
    write_csv(
        args.staging_dir / "wqp_system_summary.csv",
        reservoir_wqp_summary,
        ["reservoir", "site_name", "first_year", "last_year", "years_with_data", "activity_count", "result_count", "latitude", "longitude"],
    )
    write_csv(
        args.staging_dir / "wqp_system_yearly_counts.csv",
        reservoir_yearly_rows,
        ["reservoir", "year", "activity_count", "result_count"],
    )
    write_csv(
        args.staging_dir / "wqp_parameter_coverage.csv",
        reservoir_parameter_rows,
        ["reservoir", "parameter_group", "result_count", "first_year", "last_year"],
    )
    write_csv(
        args.staging_dir / "wqp_river_sites_summary.csv",
        river_wqp_summary,
        ["site_label", "site_id", "site_name", "reach", "first_year", "last_year", "years_with_data", "activity_count", "result_count", "latitude", "longitude"],
    )
    write_csv(
        args.staging_dir / "wqp_river_yearly_counts.csv",
        river_wqp_yearly_rows,
        ["site_label", "site_id", "reach", "year", "activity_count", "result_count"],
    )
    write_csv(
        args.staging_dir / "wqp_river_parameter_coverage.csv",
        river_wqp_parameter_rows,
        ["site_label", "site_id", "reach", "parameter_group", "result_count", "first_year", "last_year"],
    )
    write_csv(
        args.staging_dir / "savannah_main_treated_water_long.csv",
        savannah_main_detail_rows,
        [
            "report_year",
            "data_year",
            "system_name",
            "system_number",
            "table_kind",
            "parameter_slug",
            "parameter_name",
            "parameter_group",
            "probable_source",
            "amount_detected_raw",
            "amount_detected_value",
            "amount_detected_min",
            "amount_detected_max",
            "amount_detected_unit",
            "range_detected_raw",
            "range_detected_min",
            "range_detected_max",
            "range_detected_unit",
            "meets_standard_raw",
            "meets_standard_flag",
            "mrdlg_raw",
            "mrdl_raw",
            "mclg_raw",
            "mcl_raw",
            "action_level_raw",
            "required_samples_raw",
            "samples_taken_raw",
            "sampling_required_period_raw",
            "sampling_actual_period_raw",
            "report_notice",
            "report_violation_flag",
        ],
    )
    write_csv(
        args.staging_dir / "savannah_main_treated_water_summary.csv",
        savannah_main_summary_rows,
        [
            "report_year",
            "data_year",
            "system_name",
            "system_number",
            "regulated_parameter_count",
            "unregulated_parameter_count",
            "parameters_meeting_standard_count",
            "parameters_not_meeting_standard_count",
            "violation_flag",
            "violation_parameter_count",
            "surface_water_share_pct",
            "groundwater_billion_gal",
            "surface_water_million_gal",
            "surface_water_billion_gal",
            "population_served",
            "tests_performed",
            "parameters_tested",
            "report_notice",
            "source_excerpt",
            "violation_summary",
            "corrective_action_summary",
        ],
    )
    write_csv(
        args.staging_dir / "savannah_main_violation_details.csv",
        savannah_main_violation_rows,
        [
            "report_year",
            "data_year",
            "system_name",
            "system_number",
            "parameter_slug",
            "parameter_name",
            "required_samples",
            "samples_taken",
            "sampling_required_period",
            "sampling_actual_period",
            "violation_summary",
            "corrective_action_summary",
        ],
    )
    write_csv(
        args.staging_dir / "usgs_river_daily_summary.csv",
        usgs_site_summary,
        ["site_label", "site_no", "site_name", "reach", "first_date", "last_date", "first_year", "last_year", "years_returned", "variable_count", "point_count", "variables"],
    )
    write_csv(
        args.staging_dir / "usgs_river_series_detail.csv",
        usgs_series_rows,
        ["site_label", "site_no", "site_name", "reach", "parameter_code", "variable_name", "statistic", "unit", "first_date", "last_date", "point_count"],
    )
    write_csv(
        args.staging_dir / "usgs_river_daily_long.csv",
        river_daily_rows,
        [
            "site_label",
            "site_no",
            "site_name",
            "reach",
            "series_slug",
            "series_label",
            "parameter_group",
            "parameter_code",
            "variable_name",
            "statistic",
            "unit",
            "date",
            "year",
            "month",
            "ano_mes",
            "value",
        ],
    )
    write_csv(
        args.staging_dir / "river_monthly_behavior.csv",
        river_monthly_rows,
        [
            "site_label",
            "site_no",
            "site_name",
            "reach",
            "series_slug",
            "series_label",
            "parameter_group",
            "parameter_code",
            "variable_name",
            "statistic",
            "unit",
            "year",
            "month",
            "ano_mes",
            "monthly_mean",
            "monthly_median",
            "monthly_min",
            "monthly_max",
            "point_count",
        ],
    )
    write_csv(
        args.staging_dir / "river_monthly_climatology.csv",
        river_climatology_rows,
        [
            "site_label",
            "site_no",
            "site_name",
            "reach",
            "series_slug",
            "series_label",
            "parameter_group",
            "parameter_code",
            "variable_name",
            "statistic",
            "unit",
            "month",
            "climatology_mean",
            "climatology_min",
            "climatology_max",
            "year_count",
        ],
    )
    write_csv(
        args.staging_dir / "river_annual_anomalies.csv",
        river_annual_rows,
        [
            "site_label",
            "site_no",
            "site_name",
            "reach",
            "series_slug",
            "series_label",
            "parameter_group",
            "parameter_code",
            "variable_name",
            "statistic",
            "unit",
            "year",
            "annual_mean",
            "anomaly_vs_series_mean",
            "zscore",
        ],
    )
    write_csv(
        args.staging_dir / "river_quality_flow_correlations.csv",
        river_correlation_rows,
        [
            "source_series_slug",
            "source_series_label",
            "target_series_slug",
            "target_series_label",
            "overlap_months",
            "first_ano_mes",
            "last_ano_mes",
            "slope",
            "intercept",
            "correlation",
        ],
    )
    write_csv(
        args.staging_dir / "reservoir_operations_monthly.csv",
        reservoir_operation_monthly_rows,
        [
            "reservoir",
            "metric_slug",
            "metric_label",
            "parameter_group",
            "unit",
            "year",
            "month",
            "ano_mes",
            "monthly_mean",
            "monthly_median",
            "monthly_min",
            "monthly_max",
            "point_count",
        ],
    )
    write_csv(
        args.staging_dir / "reservoir_operations_summary.csv",
        reservoir_operation_summary_rows,
        [
            "reservoir",
            "metric_slug",
            "metric_label",
            "parameter_group",
            "unit",
            "first_year",
            "last_year",
            "years_returned",
            "months_returned",
            "point_count",
            "first_date",
            "last_date",
        ],
    )
    write_csv(
        args.staging_dir / "river_reservoir_bridge.csv",
        bridge_rows,
        [
            "ano_mes",
            "year",
            "month",
            "augusta_flow_cfs",
            "augusta_stage_ft",
            "dock_conductance_us_cm",
            "dock_do_mg_l",
            "dock_turbidity_fnu",
            "thurmond_outflow_cfs",
            "thurmond_inflow_cfs",
            "thurmond_storage_acft",
            "thurmond_pool_elevation_ft",
            "hartwell_outflow_cfs",
            "russell_outflow_cfs",
        ],
    )
    write_csv(
        args.staging_dir / "coverage_target_matrix.csv",
        coverage_rows,
        ["layer", "entity", "source", "returned_years", "target_years", "coverage_status", "first_year", "last_year", "coverage_kind"],
    )
    write_csv(
        args.staging_dir / "domain_registry.csv",
        domain_registry_rows,
        [
            "domain_id",
            "domain_label",
            "layer_name",
            "layer_stage",
            "layer_path",
            "grain",
            "entity_keys",
            "time_keys",
            "join_keys",
            "crossing_priority",
            "readiness",
            "first_year",
            "last_year",
            "record_count",
            "coverage_note",
        ],
    )
    write_csv(
        args.staging_dir / "sediment_master_data.csv",
        sediment_rows,
        [
            "site",
            "depth",
            "latitude",
            "longitude",
            "clay_pct",
            "silt_pct",
            "sand_pct",
            "fine_fraction_pct",
            "water_pct",
            "d10",
            "d50",
            "d90",
            "valid_grain_order",
            "fe_ppm",
            "mn_ppm",
            "carbon_pct",
            "ph",
            "do_pct",
            "cond",
        ],
    )
    write_csv(
        args.staging_dir / "sediment_depositional_scores.csv",
        sediment_score_rows,
        [
            "site",
            "fine_depositional_score",
            "depth",
            "clay_pct",
            "silt_pct",
            "sand_pct",
            "water_pct",
            "d50",
            "fe_ppm",
            "carbon_pct",
        ],
    )
    write_csv(
        args.staging_dir / "sediment_pairwise_relations.csv",
        sediment_pairwise_rows,
        ["x_field", "y_field", "n", "slope", "intercept", "correlation", "direction"],
    )
    write_csv(
        args.staging_dir / "crosslayer_parameter_matrix.csv",
        parameter_overlap_rows,
        ["entity_group", "entity", "parameter_group", "years_available", "coverage_ratio", "first_year", "last_year", "result_count"],
    )
    write_csv(
        args.staging_dir / "context_source_inventory.csv",
        context_inventory_rows,
        [
            "run_id",
            "target_id",
            "source_name",
            "dataset_name",
            "collection_status",
            "thematic_axis",
            "analytical_role",
            "requested_window",
            "period_start",
            "period_end",
            "coverage_years",
            "target_years",
            "coverage_status",
            "requires_priority_followup",
            "priority_reason",
        ],
    )
    write_csv(
        args.staging_dir / "harvester_handoff_inventory.csv",
        handoff_inventory_rows,
        [
            "research_id",
            "handoff_generated_at",
            "river_scope",
            "rank",
            "source_slug",
            "source_name",
            "dataset_name",
            "source_family",
            "collection_method_hint",
            "access_type",
            "handoff_status",
            "target_window_years",
            "expected_period_start",
            "expected_period_end",
            "notes_on_asymmetry",
            "currently_matched",
            "current_run_id",
            "current_collection_status",
            "current_thematic_axis",
            "current_priority_reason",
        ],
    )

    write_csv(
        args.analytic_dir / "river_mainstem_layers.csv",
        analytic_river_rows,
        [
            "entity_group",
            "entity",
            "layer",
            "source",
            "reach",
            "first_year",
            "last_year",
            "returned_years",
            "target_years",
            "coverage_gap_years",
            "coverage_status",
            "record_count",
            "parameter_count",
        ],
    )
    write_csv(
        args.analytic_dir / "reservoir_annex_layers.csv",
        analytic_reservoir_rows,
        [
            "reservoir",
            "layer",
            "source",
            "first_year",
            "last_year",
            "returned_years",
            "target_years",
            "coverage_gap_years",
            "coverage_status",
            "record_count",
            "support_value_1",
            "support_value_2",
        ],
    )
    write_csv(
        args.analytic_dir / "pressure_source_inventory.csv",
        analytic_pressure_rows,
        [
            "source_stage",
            "scope",
            "dataset_name",
            "source_name",
            "status",
            "period_start",
            "period_end",
            "coverage_years",
            "target_years",
            "priority_reason",
        ],
    )
    write_csv(
        args.analytic_dir / "sediment_bridge_summary.csv",
        analytic_sediment_rows,
        [
            "record_type",
            "site",
            "metric",
            "value",
            "aux_1",
            "aux_2",
        ],
    )
    write_csv(
        args.analytic_dir / "river_behavior_monthly.csv",
        river_monthly_rows,
        [
            "site_label",
            "site_no",
            "site_name",
            "reach",
            "series_slug",
            "series_label",
            "parameter_group",
            "parameter_code",
            "variable_name",
            "statistic",
            "unit",
            "year",
            "month",
            "ano_mes",
            "monthly_mean",
            "monthly_median",
            "monthly_min",
            "monthly_max",
            "point_count",
        ],
    )
    write_csv(
        args.analytic_dir / "reservoir_operations_monthly.csv",
        reservoir_operation_monthly_rows,
        [
            "reservoir",
            "metric_slug",
            "metric_label",
            "parameter_group",
            "unit",
            "year",
            "month",
            "ano_mes",
            "monthly_mean",
            "monthly_median",
            "monthly_min",
            "monthly_max",
            "point_count",
        ],
    )
    write_csv(
        args.analytic_dir / "river_reservoir_bridge.csv",
        bridge_rows,
        [
            "ano_mes",
            "year",
            "month",
            "augusta_flow_cfs",
            "augusta_stage_ft",
            "dock_conductance_us_cm",
            "dock_do_mg_l",
            "dock_turbidity_fnu",
            "thurmond_outflow_cfs",
            "thurmond_inflow_cfs",
            "thurmond_storage_acft",
            "thurmond_pool_elevation_ft",
            "hartwell_outflow_cfs",
            "russell_outflow_cfs",
        ],
    )
    write_csv(
        args.analytic_dir / "savannah_main_treated_water_summary.csv",
        savannah_main_summary_rows,
        [
            "report_year",
            "data_year",
            "system_name",
            "system_number",
            "regulated_parameter_count",
            "unregulated_parameter_count",
            "parameters_meeting_standard_count",
            "parameters_not_meeting_standard_count",
            "violation_flag",
            "violation_parameter_count",
            "surface_water_share_pct",
            "groundwater_billion_gal",
            "surface_water_million_gal",
            "surface_water_billion_gal",
            "population_served",
            "tests_performed",
            "parameters_tested",
            "report_notice",
            "source_excerpt",
            "violation_summary",
            "corrective_action_summary",
        ],
    )
    write_csv(
        args.analytic_dir / "savannah_main_treated_water_bridge.csv",
        savannah_main_bridge_rows,
        [
            "report_year",
            "data_year",
            "violation_flag",
            "surface_water_share_pct",
            "groundwater_billion_gal",
            "surface_water_million_gal",
            "surface_water_billion_gal",
            "population_served",
            "tests_performed",
            "parameters_tested",
            "report_notice",
            "augusta_flow_cfs",
            "augusta_stage_ft",
            "dock_conductance_us_cm",
            "dock_do_mg_l",
            "dock_turbidity_fnu",
            "dock_water_temp_c",
            "chlorine_ppm",
            "fluoride_ppm",
            "tthms_ppb",
            "thaas_ppb",
            "nitrate_ppm",
            "lead_ppb",
            "copper_ppm",
            "arsenic_ppb",
            "manganese_ppb",
            "bromide_ppb",
            "haa5_ppb",
            "haa6br_ppb",
            "haa9_ppb",
        ],
    )
    write_csv(
        args.analytic_dir / "coverage_target_matrix.csv",
        analytic_coverage_rows,
        [
            "layer",
            "entity",
            "source",
            "returned_years",
            "target_years",
            "coverage_status",
            "first_year",
            "last_year",
            "coverage_kind",
            "coverage_gap_years",
        ],
    )
    write_csv(
        args.analytic_dir / "domain_registry.csv",
        domain_registry_rows,
        [
            "domain_id",
            "domain_label",
            "layer_name",
            "layer_stage",
            "layer_path",
            "grain",
            "entity_keys",
            "time_keys",
            "join_keys",
            "crossing_priority",
            "readiness",
            "first_year",
            "last_year",
            "record_count",
            "coverage_note",
        ],
    )
    write_csv(
        args.analytic_dir / "crosswalk_registry.csv",
        crosswalk_registry_rows,
        [
            "crosswalk_id",
            "left_domain_id",
            "right_domain_id",
            "left_layer",
            "right_layer",
            "output_layer",
            "join_grain",
            "join_keys",
            "crossing_status",
            "interpretation_rule",
            "caveat",
        ],
    )
    write_csv(
        args.analytic_dir / "collection_preflight_inventory.csv",
        handoff_inventory_rows,
        [
            "research_id",
            "handoff_generated_at",
            "river_scope",
            "rank",
            "source_slug",
            "source_name",
            "dataset_name",
            "source_family",
            "collection_method_hint",
            "access_type",
            "handoff_status",
            "target_window_years",
            "expected_period_start",
            "expected_period_end",
            "notes_on_asymmetry",
            "currently_matched",
            "current_run_id",
            "current_collection_status",
            "current_thematic_axis",
            "current_priority_reason",
        ],
    )

    report_context = build_report_context(
        river_manifest_path,
        reservoir_manifest_path,
        legacy_manifest_path,
        river_manifest,
        reservoir_manifest,
        legacy_manifest,
        usgs_site_summary,
        river_monthly_rows,
        river_climatology_rows,
        river_correlation_rows,
        river_wqp_summary,
        reservoir_wqp_summary,
        usace_rows,
        reservoir_operation_summary_rows,
        bridge_rows,
        coverage_rows,
        sediment_rows,
        sediment_score_rows,
        sediment_pairwise_rows,
        parameter_overlap_rows,
        context_inventory_rows,
        domain_registry_rows,
        crosswalk_registry_rows,
    )
    write_json(args.report_context, report_context)

    inventory_payload = {
        "study": "Savannah River river-first contextual EDA",
        "river_collection_run_id": river_manifest["run_id"],
        "reservoir_annex_run_id": reservoir_manifest["run_id"],
        "usgs_river_sites": usgs_site_summary,
        "river_behavior_series": river_monthly_rows[:48],
        "river_quality_correlations": river_correlation_rows,
        "reservoir_operation_summary": reservoir_operation_summary_rows,
        "river_wqp_summary": river_wqp_summary,
        "reservoir_wqp_summary": reservoir_wqp_summary,
        "context_source_inventory": context_inventory_rows,
        "sediment_site_count": len(sediment_rows),
        "sediment_top_score_sites": [row["site"] for row in sediment_score_rows[:5]],
        "key_caveats": [
            "USGS daily mainstem coverage meets the 20-year target and now drives the core river charts.",
            "Lower-river continuous sensor behavior is stronger than the discrete WQP exports for the current mainstem analysis.",
            "Reservoir operations are now monthly series, but Hartwell and Russell still return shorter windows than Thurmond.",
            "Sediment notebook crosswalk is now materialized in staging, but granulometric caveats such as D90 < D50 still require manual review.",
        ],
        "next_collection_priorities": [
            "Prioritize mainstem river water quality sites and pollutant-bearing WQP exports that extend the temporal window toward 20 years.",
            "Add mainstem gauges above, between, and below the cascade when they improve continuity of the Savannah River storyline.",
            "Materialize pollutant and pressure sources in structured tables rather than leaving them as PDF-only references.",
            "Deepen Hartwell and Russell operational continuity whenever the source allows it.",
        ],
        "harvester_handoff": "" if handoff_path is None else str(handoff_path.relative_to(ROOT)),
    }
    write_json(args.inventory_json, inventory_payload)
    args.inventory_md.write_text(
        build_inventory_markdown(
            river_manifest,
            reservoir_manifest,
            usgs_site_summary,
            river_wqp_summary,
            reservoir_wqp_summary,
            sediment_rows,
            sediment_score_rows,
            context_inventory_rows,
        ),
        encoding="utf-8",
    )

    print(f"Staging tables written to: {args.staging_dir}")
    print(f"Analytic tables written to: {args.analytic_dir}")
    print(f"Report context written to: {args.report_context}")
    print(f"Inventory written to: {args.inventory_json}")


if __name__ == "__main__":
    main()
