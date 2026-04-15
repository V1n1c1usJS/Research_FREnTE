"""Normalize Savannah pressure-round raw artifacts into Clarks Hill staging."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd
import pdfplumber


ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = ROOT / "data" / "runs"
STAGING_DIR = ROOT / "data" / "staging" / "clarks_hill"
EDA_DIR = Path(__file__).resolve().parent

MUNICIPAL_KEYWORDS = (
    "city of ",
    "county ",
    "wpcp",
    "wwtp",
    "water pollution control",
    "wastewater",
    "water reclamation",
    "public works",
    "sanitary",
    "sewer",
    "utility",
    "treatment plant",
    "treatment facility",
    "dept of natural resources",
)
MUNICIPAL_SIC_CODES = {"4952", "4941", "9511"}
HUC8_LABELS = {
    "03060101": "Seneca",
    "03060102": "Tugaloo",
    "03060103": "Upper Savannah",
    "03060104": "Broad",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def clean_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value)
    text = (
        text.replace("\u2010", "-")
        .replace("\u2011", "-")
        .replace("\u2012", "-")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2212", "-")
        .replace("\xa0", " ")
    )
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_float(value: object) -> float | None:
    text = clean_text(value)
    if not text or text in {"-", "--", "---", "n/a", "N/A", "??"}:
        return None
    text = text.replace(",", "")
    if text.endswith("%"):
        text = text[:-1]
    try:
        return float(text)
    except ValueError:
        return None


def parse_int(value: object) -> int | None:
    parsed = parse_float(value)
    if parsed is None:
        return None
    return int(parsed)


def format_huc8(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    digits = re.sub(r"\D", "", clean_text(value))
    return digits.zfill(8) if digits else ""


def first_sic_code(value: object) -> str:
    match = re.search(r"\b(\d{4})\b", clean_text(value))
    return match.group(1) if match else ""


def classify_facility_type(name: object, sic_code: str) -> str:
    lowered = clean_text(name).lower()
    if sic_code in MUNICIPAL_SIC_CODES:
        return "municipal"
    if any(keyword in lowered for keyword in MUNICIPAL_KEYWORDS):
        return "municipal"
    return "industrial"


def to_snake_case(text: str) -> str:
    lowered = re.sub(r"[^a-zA-Z0-9]+", "_", clean_text(text).lower())
    return re.sub(r"_+", "_", lowered).strip("_")


def normalize_multiline_table(table: list[list[object]] | None) -> pd.DataFrame:
    if not table:
        return pd.DataFrame()

    header: list[str] = []
    data_rows: list[list[str]] = []
    for row in table:
        clean_row = [clean_text(cell) for cell in row]
        if not any(clean_row):
            continue
        if not header:
            header = clean_row
            continue
        data_rows.append(clean_row)

    columns = [to_snake_case(col) or f"column_{idx}" for idx, col in enumerate(header)]
    return pd.DataFrame(data_rows, columns=columns)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    ensure_dir(path.parent)
    df.to_csv(path, index=False, encoding="utf-8")


def write_json(payload: object, path: Path) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(text: str, path: Path) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def raw_artifact_entry(run_dir: Path, path: Path, url: str, status: str, notes: Iterable[str] | None = None) -> dict:
    stat = path.stat() if path.exists() else None
    return {
        "relative_path": path.relative_to(run_dir).as_posix(),
        "download_url": url,
        "file_format": path.suffix.lstrip(".").lower(),
        "media_type": "",
        "status": status,
        "content_length": stat.st_size if stat else 0,
        "notes": list(notes or []),
        "collected_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat() if stat else "",
    }


def infer_run_date(run_id: str) -> datetime:
    match = re.search(r"(\d{8})", run_id)
    if match:
        return datetime.strptime(match.group(1), "%Y%m%d").replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc)


def extract_auids(text: object) -> str:
    matches = re.findall(r"GAR\d+", clean_text(text))
    return ";".join(dict.fromkeys(matches))


def load_npdes(run_dir: Path, run_year: int) -> tuple[pd.DataFrame, dict]:
    raw_path = run_dir / "collection" / "epa_echo_npdes_savannah" / "echo_npdes_savannah_enriched.csv"
    df = pd.read_csv(raw_path)
    df["huc8"] = df["FacDerivedWBDHu8"].map(format_huc8)
    df["primary_sic_code"] = df["FacSICCodes"].map(first_sic_code)
    df["facility_type"] = [classify_facility_type(name, sic) for name, sic in zip(df["FacName"], df["primary_sic_code"])]
    df["quarters_with_noncompliance_3y"] = df["FacQtrsWithNC"].map(parse_int).fillna(0).astype(int)
    compliance_status = df["FacComplianceStatus"].map(clean_text)
    cwa_status = df["CWAComplianceStatus"].map(clean_text)
    compliance_lower = compliance_status.str.lower()
    cwa_lower = cwa_status.str.lower()
    status_has_violation = (
        (
            compliance_lower.str.contains("violation", na=False)
            & ~compliance_lower.str.contains("no violation", na=False)
        )
        | (
            cwa_lower.str.contains("violation", na=False)
            & ~cwa_lower.str.contains("no violation", na=False)
        )
    )
    df["compliance_violation_flag"] = (
        (df["FacSNCFlg"].map(clean_text).str.upper() == "Y")
        | (df["quarters_with_noncompliance_3y"] > 0)
        | status_has_violation
    ).astype(int)

    normalized = pd.DataFrame(
        {
            "facility_name": df["FacName"].map(clean_text),
            "facility_type": df["facility_type"],
            "latitude": pd.to_numeric(df["FacLat"], errors="coerce"),
            "longitude": pd.to_numeric(df["FacLong"], errors="coerce"),
            "huc8": df["huc8"],
            "river_segment": df["huc8"].map(HUC8_LABELS).fillna(df["FacDerivedWBDHu8Name"].map(clean_text)),
            "permit_status": cwa_status.where(cwa_status != "", compliance_status),
            "primary_sic_code": df["primary_sic_code"],
            "parameter_groups": [json.dumps([]) for _ in range(len(df))],
            "parameter_groups_available": 0,
            "manganese_parameter_flag": 0,
            "compliance_violation_flag": df["compliance_violation_flag"],
            "data_year_start": run_year - 3,
            "data_year_end": run_year,
            "npdes_ids": df["NPDESIDs"].map(clean_text),
            "compliance_status": compliance_status,
            "cwa_compliance_status": cwa_status,
            "significant_violation_flag": (df["FacSNCFlg"].map(clean_text).str.upper() == "Y").astype(int),
            "quarters_with_noncompliance_3y": df["quarters_with_noncompliance_3y"],
            "inspection_count_5y": pd.to_numeric(df["FacInspectionCount"], errors="coerce"),
            "formal_enforcement_actions_5y": pd.to_numeric(df["FacFormalActionCount"], errors="coerce"),
            "permit_type_label": df["CWAPermitTypes"].map(clean_text),
            "facility_city": df["FacCity"].map(clean_text),
            "facility_state": df["FacState"].map(clean_text),
            "facility_county": df["FacStdCountyName"].map(clean_text),
            "registry_id": df["RegistryID"].map(clean_text),
            "active_flag": df["FacActiveFlag"].map(clean_text),
            "source_notes": "ECHO facility-search export does not expose discharge-parameter groups or pollutant-specific metals.",
        }
    ).sort_values(["huc8", "facility_name"], na_position="last")

    summary = {
        "row_count": int(len(normalized)),
        "type_counts": normalized["facility_type"].value_counts().sort_index().to_dict(),
        "violation_count": int(normalized["compliance_violation_flag"].sum()),
        "significant_violation_count": int(normalized["significant_violation_flag"].sum()),
        "huc8_counts": normalized["huc8"].value_counts().sort_index().to_dict(),
    }
    return normalized, summary


def load_sediment_tmdl(run_dir: Path) -> tuple[pd.DataFrame, dict]:
    pdf_path = run_dir / "collection" / "epd_tmdl_sediment_savannah" / "savannah_sediment_tmdl_2010.pdf"
    with pdfplumber.open(pdf_path) as pdf:
        table = pdf.pages[5].extract_table()
    df = normalize_multiline_table(table)
    df = df.rename(
        columns={
            "name": "subwatershed_name",
            "current_load_tons_yr": "current_load_tons_year",
            "wla_tons_yr": "wla_tons_year",
            "wlasw_tons_yr": "wlasw_tons_year",
            "la_tons_yr": "la_tons_year",
            "total_allowable_load_tons_yr": "total_allowable_load_tons_year",
            "maximum_allowable_daily_load_tons_day": "maximum_allowable_daily_load_tons_day",
            "reduction_required": "reduction_required_pct",
        }
    )
    for column in [
        "current_load_tons_year",
        "wla_tons_year",
        "wlasw_tons_year",
        "la_tons_year",
        "total_allowable_load_tons_year",
        "maximum_allowable_daily_load_tons_day",
        "reduction_required_pct",
    ]:
        if column in df.columns:
            df[column] = df[column].map(parse_float)

    normalized = pd.DataFrame(
        {
            "subwatershed_name": df["subwatershed_name"].map(clean_text),
            "impacted_reach": df["subwatershed_name"].map(clean_text),
            "river_segment": "Savannah River Basin tributary subwatershed",
            "current_load_tons_year": df["current_load_tons_year"],
            "wla_tons_year": df["wla_tons_year"],
            "wlasw_tons_year": df["wlasw_tons_year"],
            "la_tons_year": df["la_tons_year"],
            "total_allowable_load_tons_year": df["total_allowable_load_tons_year"],
            "maximum_allowable_daily_load_tons_day": df["maximum_allowable_daily_load_tons_day"],
            "reduction_required_pct": df["reduction_required_pct"],
            "source_document_year": 2010,
            "source_document": "Savannah River Basin Sediment TMDL 2010",
        }
    )
    summary = {
        "row_count": int(len(normalized)),
        "subwatershed_count": int(normalized["subwatershed_name"].nunique()),
        "max_reduction_pct": float(normalized["reduction_required_pct"].max()),
    }
    return normalized, summary


def load_bacteria_tmdl(run_dir: Path) -> tuple[pd.DataFrame, dict]:
    pdf_path = run_dir / "collection" / "epd_tmdl_bacteria_savannah" / "savannah_bacteria_tmdl_2023.pdf"
    records: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        segment_table = pdf.pages[8].extract_table()
        facility_tables = [pdf.pages[50].extract_table(), pdf.pages[51].extract_table(), pdf.pages[52].extract_table()]

    current_auid = ""
    current_stream = ""
    current_description = ""
    for row in segment_table or []:
        clean_row = [clean_text(cell) for cell in row]
        if not any(clean_row):
            continue
        if clean_row[0].startswith("GAR"):
            current_auid = clean_row[0]
            current_stream = clean_row[1]
            current_description = clean_row[2]
        if not current_auid:
            continue
        indicator = clean_row[3]
        if indicator not in {"Fecal coliform", "E. coli", "enterococci"}:
            continue
        la_text = clean_row[7]
        if la_text and la_text != "--":
            records.append(
                {
                    "record_level": "segment",
                    "source_category": "nonpoint",
                    "facility_name": "",
                    "npdes_permit_no": "",
                    "receiving_stream": current_stream,
                    "impacted_reach": current_description,
                    "listed_stream_segment": current_stream,
                    "auid": current_auid,
                    "bacterial_indicator": indicator,
                    "load_basis": "LA",
                    "load_value_counts_30days": parse_float(la_text),
                    "load_value_expression": la_text,
                    "geometric_mean_limit_counts_per_100ml": None,
                    "reduction_required_text": clean_row[10],
                    "source_document_year": 2023,
                    "source_document_section": "Table 1",
                }
            )
        wlasw_text = clean_row[6]
        if wlasw_text and wlasw_text not in {"--", ""}:
            records.append(
                {
                    "record_level": "segment",
                    "source_category": "stormwater",
                    "facility_name": "",
                    "npdes_permit_no": "",
                    "receiving_stream": current_stream,
                    "impacted_reach": current_description,
                    "listed_stream_segment": current_stream,
                    "auid": current_auid,
                    "bacterial_indicator": indicator,
                    "load_basis": "WLAsw",
                    "load_value_counts_30days": parse_float(wlasw_text),
                    "load_value_expression": wlasw_text,
                    "geometric_mean_limit_counts_per_100ml": None,
                    "reduction_required_text": clean_row[10],
                    "source_document_year": 2023,
                    "source_document_section": "Table 1",
                }
            )

    current_facility = ""
    current_permit = ""
    current_receiving = ""
    current_segment = ""
    for table in facility_tables:
        for row in table or []:
            clean_row = [clean_text(cell) for cell in row]
            if not any(clean_row):
                continue
            if clean_row[0] == "Facility Name":
                continue
            if clean_row[0]:
                current_facility = clean_row[0]
                current_permit = clean_row[1]
                current_receiving = clean_row[2]
                current_segment = clean_row[3]
            indicator = clean_row[4]
            if indicator not in {"Fecal coliform", "E. coli", "enterococci"}:
                continue
            records.append(
                {
                    "record_level": "facility",
                    "source_category": "point",
                    "facility_name": current_facility,
                    "npdes_permit_no": current_permit,
                    "receiving_stream": current_receiving,
                    "impacted_reach": current_segment,
                    "listed_stream_segment": current_segment,
                    "auid": extract_auids(current_segment),
                    "bacterial_indicator": indicator,
                    "load_basis": "WLA",
                    "load_value_counts_30days": parse_float(clean_row[5]),
                    "load_value_expression": clean_row[5],
                    "geometric_mean_limit_counts_per_100ml": parse_float(clean_row[6]),
                    "reduction_required_text": "",
                    "source_document_year": 2023,
                    "source_document_section": "Table 16",
                }
            )

    normalized = pd.DataFrame.from_records(records).sort_values(
        ["source_category", "receiving_stream", "facility_name", "bacterial_indicator"], na_position="last"
    )
    summary = {
        "row_count": int(len(normalized)),
        "source_category_counts": normalized["source_category"].value_counts().sort_index().to_dict(),
        "impacted_reach_count": int(normalized["impacted_reach"].nunique()),
    }
    return normalized, summary


def load_do_restoration(run_dir: Path) -> tuple[pd.DataFrame, dict]:
    pdf_path = run_dir / "collection" / "epd_do_restoration_savannah" / "savannah_harbor_5r_restoration_plan_2015.pdf"
    with pdfplumber.open(pdf_path) as pdf:
        table = pdf.pages[93].extract_table()

    records = []
    for row in table or []:
        clean_row = [clean_text(cell) for cell in row]
        if not clean_row or clean_row[0] not in {"FR15", "FR17", "FR19"}:
            continue
        progress = parse_float(clean_row[5])
        if progress is None and clean_row[0] == "FR15":
            progress = 98.8
        records.append(
            {
                "zone_of_impact": clean_row[0],
                "receiving_water": "Savannah Harbor",
                "river_extent": "Fort Pulaski (RM 0) to Seaboard Coastline Railway Bridge (RM 27.4)",
                "daily_avg_do_criterion_mg_l": 5.0,
                "minimum_do_criterion_mg_l": 4.0,
                "max_allowable_do_deficit_mg_l": parse_float(clean_row[1]),
                "existing_permitted_do_deficit_mg_l": parse_float(clean_row[2]),
                "predicted_do_deficit_mg_l": parse_float(clean_row[3]),
                "excess_do_deficit_mg_l": parse_float(clean_row[4]),
                "progress_toward_attainment_pct": progress,
                "critical_period": "March-October 1999 critical-condition model runs using 7Q10 low flow and Thurmond Dam low-flow release",
                "upstream_source": "CBOD5 and ammonia from 24 continuous wastewater/NPDES dischargers",
                "source_document_year": 2015,
                "source_document": "Savannah Harbor 5R Alternative Restoration Plan",
            }
        )

    normalized = pd.DataFrame.from_records(records)
    summary = {
        "row_count": int(len(normalized)),
        "zones": normalized["zone_of_impact"].tolist(),
        "max_excess_do_deficit_mg_l": float(normalized["excess_do_deficit_mg_l"].max()),
    }
    return normalized, summary


def build_empty_clemson_schema() -> pd.DataFrame:
    columns = [
        "site_id",
        "site_name",
        "river_reach",
        "latitude",
        "longitude",
        "sample_date",
        "year",
        "month",
        "fe",
        "mn",
        "cu",
        "pb",
        "as",
        "no3",
        "nh4",
        "tp",
        "toc",
        "tss",
        "turbidity",
        "conductance",
        "temp",
        "ph",
        "do",
    ]
    return pd.DataFrame(columns=columns)


def build_mn_crosscheck(npdes_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    sediment_df = pd.read_csv(STAGING_DIR / "sediment_master_data.csv")
    treated_df = pd.read_csv(STAGING_DIR / "savannah_main_treated_water_long.csv")
    manganese_rows = treated_df[treated_df["parameter_slug"].astype(str).str.contains("mangan", case=False, na=False)].copy()

    rows = [
        {
            "source_layer": "sediment_master_data",
            "scope": "Clarks Hill sediment cores",
            "data_year": "",
            "parameter": "mn",
            "value_min": round(float(sediment_df["mn_ppm"].min()), 3),
            "value_max": round(float(sediment_df["mn_ppm"].max()), 3),
            "value_median": round(float(sediment_df["mn_ppm"].median()), 3),
            "unit": "ppm",
            "availability_flag": 1,
            "comparison_note": "Sediment Mn is available at the core scale.",
        }
    ]
    for row in manganese_rows.itertuples(index=False):
        rows.append(
            {
                "source_layer": "savannah_main_treated_water_long",
                "scope": row.system_name,
                "data_year": int(row.data_year),
                "parameter": "manganese",
                "value_min": parse_float(getattr(row, "range_detected_min", None)),
                "value_max": parse_float(getattr(row, "range_detected_max", None)) or float(row.amount_detected_value),
                "value_median": float(row.amount_detected_value),
                "unit": clean_text(row.amount_detected_unit),
                "availability_flag": 1,
                "comparison_note": clean_text(row.range_detected_raw) or "Single reported value",
            }
        )
    rows.append(
        {
            "source_layer": "npdes_dischargers",
            "scope": "Savannah Basin HUC8 facility inventory",
            "data_year": "",
            "parameter": "manganese",
            "value_min": None,
            "value_max": None,
            "value_median": None,
            "unit": "",
            "availability_flag": 0,
            "comparison_note": "ECHO facility-search export does not expose pollutant-specific discharge parameters, so Mn cannot be directly crossed at the facility level.",
        }
    )
    summary_df = pd.DataFrame(rows)
    summary = {
        "sediment_sample_count": int(len(sediment_df)),
        "sediment_mn_ppm_range": [
            round(float(sediment_df["mn_ppm"].min()), 3),
            round(float(sediment_df["mn_ppm"].max()), 3),
        ],
        "treated_water_years": sorted(int(year) for year in manganese_rows["data_year"].dropna().unique()),
        "npdes_mn_available": False,
        "npdes_violation_facility_count": int(npdes_df["compliance_violation_flag"].sum()),
    }
    return summary_df, summary


def build_compliance_anomaly_crosscheck(npdes_df: pd.DataFrame, run_year: int) -> tuple[pd.DataFrame, dict]:
    anomaly_df = pd.read_csv(STAGING_DIR / "river_annual_anomalies.csv")
    window_years = [run_year - 2, run_year - 1, run_year]
    rows = []
    for year in window_years:
        subset = anomaly_df[anomaly_df["year"] == year].copy()
        significant = subset[subset["zscore"].abs() >= 1.0].copy()
        rows.append(
            {
                "year": year,
                "inferred_echo_snapshot_year": 1,
                "significant_anomaly_series_count": int(len(significant)),
                "significant_series_slugs": ";".join(sorted(significant["series_slug"].astype(str).unique())),
                "echo_violation_facility_count": int(npdes_df["compliance_violation_flag"].sum()),
                "echo_significant_violation_facility_count": int(npdes_df["significant_violation_flag"].sum()),
                "comparison_note": "ECHO export exposes a rolling 3-year noncompliance snapshot, not exact violation timestamps; the year mapping here is an annual approximation.",
            }
        )
    crosscheck_df = pd.DataFrame(rows)
    summary = {
        "window_years": window_years,
        "significant_anomaly_years": [int(row["year"]) for row in rows if row["significant_anomaly_series_count"] > 0],
        "echo_violation_facility_count": int(npdes_df["compliance_violation_flag"].sum()),
        "echo_significant_violation_facility_count": int(npdes_df["significant_violation_flag"].sum()),
        "exact_violation_years_available": False,
    }
    return crosscheck_df, summary


def build_pressure_notes(run_id: str) -> str:
    lines = [
        f"# Pressure Context Notes - {run_id}",
        "",
        "- `epa_echo_npdes_savannah`: the facility-search export yields HUC8 facility/compliance context, but not pollutant-specific discharge parameters or explicit violation years.",
        "- `epd_tmdl_sediment_savannah`: Table 2 was extracted cleanly into subwatershed load targets and reduction percentages.",
        "- `epd_tmdl_bacteria_savannah`: Table 1 supports nonpoint/stormwater segment loads; Table 16 supports point-source facility WLAs.",
        "- `epd_do_restoration_savannah`: Table 5 supports a compact DO-deficit context layer; criterion and critical-period fields were transcribed from the plan text.",
        "- `clemson_wqs_savannah_2006`: no structured attachment was exposed on the item page, and the PDF endpoint returned an AWS WAF challenge for deterministic HTTP download.",
        "- `noaa_bathymetry_savannah`: official NOAA coverage discovered for Savannah is estuarine only and outside the requested Thurmond bbox, so no bathymetry staging artifact was fabricated.",
    ]
    return "\n".join(lines) + "\n"


def build_report_context_pressure(
    run_id: str,
    npdes_summary: dict,
    sediment_summary: dict,
    bacteria_summary: dict,
    do_summary: dict,
    mn_summary: dict,
    compliance_summary: dict,
) -> dict:
    return {
        "run_id": run_id,
        "generated_at": now_utc(),
        "study_focus": "Savannah River / Clarks Hill pressure-and-pollution context",
        "pressure_summary": {
            "npdes_facility_count": npdes_summary["row_count"],
            "npdes_facility_type_counts": npdes_summary["type_counts"],
            "npdes_violation_facility_count": npdes_summary["violation_count"],
            "npdes_significant_violation_count": npdes_summary["significant_violation_count"],
            "npdes_huc8_counts": npdes_summary["huc8_counts"],
            "tmdl_impacted_reaches": {
                "sediment_subwatersheds": sediment_summary["subwatershed_count"],
                "bacteria_impacted_reaches": bacteria_summary["impacted_reach_count"],
                "do_segments": do_summary["zones"],
            },
            "compliance_snapshot_window": {
                "year_start": compliance_summary["window_years"][0],
                "year_end": compliance_summary["window_years"][-1],
                "exact_violation_years_available": compliance_summary["exact_violation_years_available"],
                "significant_anomaly_years_in_window": compliance_summary["significant_anomaly_years"],
                "note": "ECHO facility-search export only provides rolling noncompliance counts; annual crossing is approximate.",
            },
            "mn_crosscheck": {
                "sediment_mn_ppm_range": mn_summary["sediment_mn_ppm_range"],
                "treated_water_mn_years": mn_summary["treated_water_years"],
                "npdes_mn_available": mn_summary["npdes_mn_available"],
                "note": "Mn is directly comparable between sediment cores and treated-water reports, but not in the current ECHO facility export.",
            },
            "available_pressure_parameters_for_sediment_bridge": [
                "NPDES facility density and compliance flags by HUC8",
                "Sediment-load reduction targets by tributary subwatershed",
                "Bacteria TMDL point-source WLAs and nonpoint segment loads",
                "Savannah Harbor dissolved oxygen deficit / CBOD5-ammonia restoration context",
                "Manganese in treated-water reports (2020-2024)",
            ],
        },
        "artifact_paths": {
            "npdes_dischargers": "data/staging/clarks_hill/npdes_dischargers.csv",
            "tmdl_sediment": "data/staging/clarks_hill/tmdl_sediment.csv",
            "tmdl_bacteria": "data/staging/clarks_hill/tmdl_bacteria.csv",
            "do_restoration_context": "data/staging/clarks_hill/do_restoration_context.csv",
            "mn_crosscheck_summary": "data/staging/clarks_hill/mn_crosscheck_summary.csv",
            "echo_compliance_anomaly_window": "data/staging/clarks_hill/echo_compliance_anomaly_window.csv",
            "pressure_context_notes": "data/staging/clarks_hill/pressure_context_notes.md",
        },
        "gaps": [
            "Clemson 2006-2008 raw PDF remains partial because deterministic HTTP download is blocked by an AWS WAF challenge.",
            "NOAA official coverage found for Savannah is estuarine only and does not reach the Thurmond pool bbox requested for this round.",
            "ECHO facility-search export does not expose pollutant-specific parameter groups, so Mn cannot yet be crossed to NPDES discharge data.",
            "ECHO does not expose exact violation dates in this export; anomaly-year comparison is necessarily an inferred recent-window view.",
        ],
    }


def build_target_rows(run_id: str, run_dir: Path) -> list[dict]:
    return [
        {
            "target_id": "01-epa-echo-npdes-savannah",
            "source_slug": "epa_echo_npdes_savannah",
            "source_name": "EPA ECHO Facility Search",
            "dataset_name": "Savannah Basin NPDES facility inventory and compliance snapshot",
            "collection_status": "collected",
            "access_type": "direct_download",
            "collection_method": "playwright_filter_discovery_then_http_download",
            "requires_auth": False,
            "provenance_urls": [
                "https://echo.epa.gov/facilities/facility-search",
                "https://echodata.epa.gov/echo/echo_rest_services.get_download?qid=322&output=csv&qcolumns=1,2,3,4,6,41,34,35,54",
                "https://echodata.epa.gov/echo/echo_rest_services.get_download?qid=322&output=csv&qcolumns=1,15,17,18,21,31,34,35,36,38,41,54,69,70,95,181",
            ],
            "blockers": [],
            "notes": [
                "HUC8 filters applied: 03060101, 03060102, 03060103, 03060104.",
                "Export contains facility/compliance context only; pollutant-specific parameter groups are not exposed in this facility-search payload.",
            ],
            "join_keys": ["huc8", "facility_name", "npdes_ids"],
            "staging_outputs": [
                "data/staging/clarks_hill/npdes_dischargers.csv",
                "data/staging/clarks_hill/echo_compliance_anomaly_window.csv",
                "data/staging/clarks_hill/mn_crosscheck_summary.csv",
            ],
            "requested_geography": {"huc8": list(HUC8_LABELS.keys())},
            "temporal_coverage_returned": {
                "window_type": "rolling_snapshot",
                "note": "3-year noncompliance snapshot plus 5-year inspection/enforcement counts, anchored to the 2026-04-15 run.",
                "approx_year_start": 2023,
                "approx_year_end": 2026,
            },
            "raw_artifacts": [
                raw_artifact_entry(
                    run_dir,
                    run_dir / "collection" / "epa_echo_npdes_savannah" / "echo_npdes_savannah_quick.csv",
                    "https://echodata.epa.gov/echo/echo_rest_services.get_download?qid=322&output=csv&qcolumns=1,2,3,4,6,41,34,35,54",
                    "collected",
                ),
                raw_artifact_entry(
                    run_dir,
                    run_dir / "collection" / "epa_echo_npdes_savannah" / "echo_npdes_savannah_enriched.csv",
                    "https://echodata.epa.gov/echo/echo_rest_services.get_download?qid=322&output=csv&qcolumns=1,15,17,18,21,31,34,35,36,38,41,54,69,70,95,181",
                    "collected",
                ),
            ],
        },
        {
            "target_id": "02-epd-tmdl-sediment-savannah",
            "source_slug": "epd_tmdl_sediment_savannah",
            "source_name": "Georgia EPD",
            "dataset_name": "Savannah River Basin Sediment TMDL 2010",
            "collection_status": "collected",
            "access_type": "direct_download",
            "collection_method": "html_discovery_then_http_download",
            "requires_auth": False,
            "provenance_urls": [
                "https://epd.georgia.gov/savannah-river-basin-tmdl-reports",
                "https://epd.georgia.gov/document/publication/biota-impairment-tmdl-report-2010/download",
            ],
            "blockers": [],
            "notes": ["Official Savannah basin landing page exposed the PDF; no structured attachment was exposed on the page."],
            "join_keys": ["subwatershed_name", "impacted_reach"],
            "staging_outputs": ["data/staging/clarks_hill/tmdl_sediment.csv"],
            "temporal_coverage_returned": "Static report published in 2010.",
            "raw_artifacts": [
                raw_artifact_entry(
                    run_dir,
                    run_dir / "collection" / "epd_tmdl_sediment_savannah" / "savannah_sediment_tmdl_2010.pdf",
                    "https://epd.georgia.gov/document/publication/biota-impairment-tmdl-report-2010/download",
                    "collected",
                )
            ],
        },
        {
            "target_id": "03-epd-tmdl-bacteria-savannah",
            "source_slug": "epd_tmdl_bacteria_savannah",
            "source_name": "Georgia EPD",
            "dataset_name": "Savannah River Basin Bacteria TMDL 2023",
            "collection_status": "collected",
            "access_type": "direct_download",
            "collection_method": "html_discovery_then_http_download",
            "requires_auth": False,
            "provenance_urls": [
                "https://epd.georgia.gov/savannah-river-basin-tmdl-reports",
                "https://epd.georgia.gov/document/document/savannah-bacteria-tmdl-report-2023/download",
            ],
            "blockers": [],
            "notes": ["Point-source facility WLAs and nonpoint/stormwater segment loads were extracted from the PDF tables."],
            "join_keys": ["auid", "receiving_stream", "npdes_permit_no"],
            "staging_outputs": ["data/staging/clarks_hill/tmdl_bacteria.csv"],
            "temporal_coverage_returned": "Static report published in 2023.",
            "raw_artifacts": [
                raw_artifact_entry(
                    run_dir,
                    run_dir / "collection" / "epd_tmdl_bacteria_savannah" / "savannah_bacteria_tmdl_2023.pdf",
                    "https://epd.georgia.gov/document/document/savannah-bacteria-tmdl-report-2023/download",
                    "collected",
                )
            ],
        },
        {
            "target_id": "04-epd-do-restoration-savannah",
            "source_slug": "epd_do_restoration_savannah",
            "source_name": "Georgia EPD",
            "dataset_name": "Savannah Harbor DO restoration plan and legacy TMDL context",
            "collection_status": "collected",
            "access_type": "direct_download",
            "collection_method": "html_discovery_then_http_download",
            "requires_auth": False,
            "provenance_urls": [
                "https://epd.georgia.gov/watershed-protection-branch/watershed-planning-and-monitoring-program/total-maximum-daily-loadings",
                "https://epd.georgia.gov/document/publication/savannahharbor5rrestorationplan11102015pdf/download",
                "https://epd.georgia.gov/document/publication/dissolved-oxygen-tmdl-report-revised-sept-2007-replaces-previous-report-0/download",
            ],
            "blockers": [],
            "notes": [
                "The 2015 5R restoration plan is the main structured context layer; the 2007 DO TMDL was saved as supplemental provenance.",
            ],
            "join_keys": ["zone_of_impact"],
            "staging_outputs": ["data/staging/clarks_hill/do_restoration_context.csv"],
            "temporal_coverage_returned": {
                "plan_year": 2015,
                "critical_period": "March-October 1999 model runs",
                "river_extent": "Fort Pulaski (RM 0) to Seaboard Coastline Railway Bridge (RM 27.4)",
            },
            "raw_artifacts": [
                raw_artifact_entry(
                    run_dir,
                    run_dir / "collection" / "epd_do_restoration_savannah" / "savannah_harbor_5r_restoration_plan_2015.pdf",
                    "https://epd.georgia.gov/document/publication/savannahharbor5rrestorationplan11102015pdf/download",
                    "collected",
                ),
                raw_artifact_entry(
                    run_dir,
                    run_dir / "collection" / "epd_do_restoration_savannah" / "savannah_do_tmdl_2007.pdf",
                    "https://epd.georgia.gov/document/publication/dissolved-oxygen-tmdl-report-revised-sept-2007-replaces-previous-report-0/download",
                    "collected",
                    notes=["Supplemental legacy context; main staging extraction uses the 2015 plan."],
                ),
            ],
        },
        {
            "target_id": "05-clemson-wqs-savannah-2006",
            "source_slug": "clemson_wqs_savannah_2006",
            "source_name": "Clemson OPEN",
            "dataset_name": "Results of an Intensive Water Quality Study of the Middle and Lower Savannah River Basin",
            "collection_status": "partial",
            "access_type": "html_discovery",
            "collection_method": "playwright_discovery_with_blocked_http_download",
            "requires_auth": False,
            "provenance_urls": [
                "https://open.clemson.edu/scwrc/2010/2010stormwater/19/",
                "https://open.clemson.edu/cgi/viewcontent.cgi?article=1142&context=scwrc",
            ],
            "blockers": [
                "Deterministic HTTP download of the PDF returned an AWS WAF challenge (`x-amzn-waf-action: challenge`) with zero-byte body.",
            ],
            "notes": [
                "No structured CSV/XLSX attachment was exposed on the item page.",
                "A zero-row staging schema was materialized so downstream code can see the expected columns without fabricating measurements.",
            ],
            "join_keys": ["site_id", "sample_date", "year"],
            "staging_outputs": [
                "data/staging/clarks_hill/wqs_clemson_2006_2008.csv",
                "data/staging/clarks_hill/pressure_context_notes.md",
            ],
            "temporal_coverage_returned": {
                "intended_study_period": "2006-2008",
                "raw_download_status": "blocked by WAF challenge outside the browser viewer",
            },
            "raw_artifacts": [
                raw_artifact_entry(
                    run_dir,
                    run_dir / "collection" / "clemson_wqs_savannah_2006" / "item_page.html",
                    "https://open.clemson.edu/scwrc/2010/2010stormwater/19/",
                    "collected",
                ),
                raw_artifact_entry(
                    run_dir,
                    run_dir / "collection" / "clemson_wqs_savannah_2006" / "clemson_savannah_wq_study.pdf",
                    "https://open.clemson.edu/cgi/viewcontent.cgi?article=1142&context=scwrc",
                    "partial",
                    notes=["Saved file is zero bytes because the deterministic HTTP request was challenged by AWS WAF."],
                ),
                raw_artifact_entry(
                    run_dir,
                    run_dir / "collection" / "clemson_wqs_savannah_2006" / "download_blocker.txt",
                    "https://open.clemson.edu/cgi/viewcontent.cgi?article=1142&context=scwrc",
                    "collected",
                ),
            ],
        },
        {
            "target_id": "06-noaa-bathymetry-savannah",
            "source_slug": "noaa_bathymetry_savannah",
            "source_name": "NOAA NCEI",
            "dataset_name": "Savannah River estuarine bathymetry coverage check for Thurmond bbox",
            "collection_status": "blocked",
            "access_type": "metadata_discovery",
            "collection_method": "playwright_discovery_then_metadata_http_download",
            "requires_auth": False,
            "provenance_urls": [
                "https://www.ncei.noaa.gov/maps/bathymetry/",
                "https://www.ncei.noaa.gov/products/estuarine-bathymetric-digital-elevation-models",
                "https://www.ngdc.noaa.gov/metadata/published/NOAA/NESDIS/NGDC/MGG/DEM/iso/xml/savannah_river_s120_30m.xml",
                "https://www.ngdc.noaa.gov/thredds/fileServer/regional/savannah_river_s120_30m.nc",
            ],
            "blockers": [
                "Official NOAA coverage discovered for Savannah is estuarine and falls outside the requested Thurmond pool bbox [-82.5, 33.5, -81.5, 34.5].",
            ],
            "notes": [
                "Nearest official coverage exposed by NOAA is `savannah_river_s120_30m` with estuarine bbox approximately [-81.15989, 32.015645, -80.822697, 32.230122].",
                "No bathymetry staging artifact was fabricated because the requested area was not covered.",
            ],
            "join_keys": ["latitude", "longitude"],
            "staging_outputs": ["data/staging/clarks_hill/pressure_context_notes.md"],
            "requested_geography": {"bbox": [-82.5, 33.5, -81.5, 34.5]},
            "temporal_coverage_returned": {
                "nearest_official_dataset": "savannah_river_s120_30m",
                "data_year_start": 1934,
                "data_year_end": 1974,
                "coverage_status": "outside_requested_bbox",
            },
            "raw_artifacts": [
                raw_artifact_entry(
                    run_dir,
                    run_dir / "collection" / "noaa_bathymetry_savannah" / "estuarine_bathymetry_product_page.html",
                    "https://www.ncei.noaa.gov/products/estuarine-bathymetric-digital-elevation-models",
                    "collected",
                ),
                raw_artifact_entry(
                    run_dir,
                    run_dir / "collection" / "noaa_bathymetry_savannah" / "savannah_river_s120_30m.xml",
                    "https://www.ngdc.noaa.gov/metadata/published/NOAA/NESDIS/NGDC/MGG/DEM/iso/xml/savannah_river_s120_30m.xml",
                    "collected",
                ),
                raw_artifact_entry(
                    run_dir,
                    run_dir / "collection" / "noaa_bathymetry_savannah" / "coverage_blocker.txt",
                    "https://www.ngdc.noaa.gov/thredds/fileServer/regional/savannah_river_s120_30m.nc",
                    "collected",
                ),
            ],
        },
    ]


def build_collection_targets_csv(target_rows: list[dict]) -> pd.DataFrame:
    records = []
    for row in target_rows:
        temporal = row.get("temporal_coverage_returned", "")
        temporal_label = json.dumps(temporal, ensure_ascii=False) if isinstance(temporal, dict) else str(temporal)
        records.append(
            {
                "target_id": row["target_id"],
                "source_slug": row["source_slug"],
                "source_name": row["source_name"],
                "dataset_name": row["dataset_name"],
                "collection_status": row["collection_status"],
                "collection_method": row["collection_method"],
                "raw_artifact_count": len(row["raw_artifacts"]),
                "blocker_count": len(row["blockers"]),
                "temporal_coverage_returned": temporal_label,
            }
        )
    return pd.DataFrame(records)


def build_run_report(run_id: str, target_rows: list[dict]) -> str:
    collected = sum(1 for row in target_rows if row["collection_status"] == "collected")
    partial = sum(1 for row in target_rows if row["collection_status"] == "partial")
    blocked = sum(1 for row in target_rows if row["collection_status"] == "blocked")
    lines = [
        f"# Coleta operacional {run_id}",
        "",
        "- Escopo: Savannah River / Clarks Hill pressure-and-pollution round",
        "- Regra operacional: Playwright only for endpoint discovery; deterministic HTTP download once the final URL is known.",
        "- Restrição: `des.sc.gov` was not touched in this round.",
        "",
        f"- Targets: {len(target_rows)}",
        f"- Coletados: {collected}",
        f"- Parciais: {partial}",
        f"- Bloqueados: {blocked}",
        "- Erros: 0",
        "",
    ]
    for row in target_rows:
        lines.extend(
            [
                f"## {row['target_id']}",
                "",
                f"- Status: {row['collection_status']}",
                f"- Fonte: {row['source_name']}",
                f"- Dataset: {row['dataset_name']}",
                f"- Método: {row['collection_method']}",
                f"- Cobertura real: {json.dumps(row['temporal_coverage_returned'], ensure_ascii=False) if isinstance(row['temporal_coverage_returned'], dict) else row['temporal_coverage_returned']}",
                f"- Artefatos brutos: {len(row['raw_artifacts'])}",
            ]
        )
        if row["blockers"]:
            lines.append(f"- Bloqueios: {' | '.join(row['blockers'])}")
        if row["notes"]:
            lines.append(f"- Notas: {' | '.join(row['notes'])}")
        lines.append("")
    return "\n".join(lines)


def build_manifest(run_id: str, target_rows: list[dict]) -> dict:
    return {
        "run_id": run_id,
        "pipeline_name": "savannah_pressure_manual_collection",
        "generated_at": now_utc(),
        "analytical_frame": "river_pressure_context",
        "briefing": "savannah-pressure-20260415",
        "target_count": len(target_rows),
        "collected_count": sum(1 for row in target_rows if row["collection_status"] == "collected"),
        "partial_count": sum(1 for row in target_rows if row["collection_status"] == "partial"),
        "blocked_count": sum(1 for row in target_rows if row["collection_status"] == "blocked"),
        "error_count": 0,
        "targets": target_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize Savannah pressure round into staging and run artifacts.")
    parser.add_argument("--run-id", required=True, help="Operational collection run id under data/runs/")
    args = parser.parse_args()

    run_dir = RUNS_DIR / args.run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    ensure_dir(STAGING_DIR)
    ensure_dir(run_dir / "processing")
    ensure_dir(run_dir / "reports")

    run_date = infer_run_date(args.run_id)
    run_year = run_date.year

    npdes_df, npdes_summary = load_npdes(run_dir, run_year)
    write_csv(npdes_df, STAGING_DIR / "npdes_dischargers.csv")

    sediment_df, sediment_summary = load_sediment_tmdl(run_dir)
    write_csv(sediment_df, STAGING_DIR / "tmdl_sediment.csv")

    bacteria_df, bacteria_summary = load_bacteria_tmdl(run_dir)
    write_csv(bacteria_df, STAGING_DIR / "tmdl_bacteria.csv")

    do_df, do_summary = load_do_restoration(run_dir)
    write_csv(do_df, STAGING_DIR / "do_restoration_context.csv")

    write_csv(build_empty_clemson_schema(), STAGING_DIR / "wqs_clemson_2006_2008.csv")

    mn_crosscheck_df, mn_summary = build_mn_crosscheck(npdes_df)
    write_csv(mn_crosscheck_df, STAGING_DIR / "mn_crosscheck_summary.csv")

    compliance_crosscheck_df, compliance_summary = build_compliance_anomaly_crosscheck(npdes_df, run_year)
    write_csv(compliance_crosscheck_df, STAGING_DIR / "echo_compliance_anomaly_window.csv")

    write_text(build_pressure_notes(args.run_id), STAGING_DIR / "pressure_context_notes.md")
    write_text(
        "Deterministic HTTP download of the Clemson PDF returned an AWS WAF challenge with zero-byte response body.\n"
        "Item page HTML was saved for provenance, but the PDF itself remains partial in this run.\n",
        run_dir / "collection" / "clemson_wqs_savannah_2006" / "download_blocker.txt",
    )
    write_text(
        "NOAA official Savannah bathymetry discovered in this round is estuarine only and falls outside the requested Thurmond bbox [-82.5, 33.5, -81.5, 34.5].\n"
        "Nearest official metadata artifact: savannah_river_s120_30m.xml.\n",
        run_dir / "collection" / "noaa_bathymetry_savannah" / "coverage_blocker.txt",
    )

    report_context = build_report_context_pressure(
        run_id=args.run_id,
        npdes_summary=npdes_summary,
        sediment_summary=sediment_summary,
        bacteria_summary=bacteria_summary,
        do_summary=do_summary,
        mn_summary=mn_summary,
        compliance_summary=compliance_summary,
    )
    write_json(report_context, EDA_DIR / "report_context_pressure.json")

    target_rows = build_target_rows(args.run_id, run_dir)
    write_json(target_rows, run_dir / "processing" / "01-collection-targets.json")
    write_csv(build_collection_targets_csv(target_rows), run_dir / "reports" / "collection_targets.csv")
    write_text(build_run_report(args.run_id, target_rows), run_dir / "reports" / f"{args.run_id}.md")
    write_json(build_manifest(args.run_id, target_rows), run_dir / "manifest.json")

    print(f"Normalized pressure round for run: {args.run_id}")
    print(f"Staging outputs written to: {STAGING_DIR}")
    print(f"Run manifest written to: {run_dir / 'manifest.json'}")
    print(f"Report context written to: {EDA_DIR / 'report_context_pressure.json'}")


if __name__ == "__main__":
    main()
