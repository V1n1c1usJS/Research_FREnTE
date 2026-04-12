from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

from src.utils.io import ensure_dir, write_bytes, write_catalog_csv, write_json, write_markdown


TARGET_WINDOW_YEARS = 20
TARGET_START = "2006-01-01"
USACE_BEGIN = "2006-01-01T00:00:00Z"
USGS_BEGIN = "2006-01-01"
WQP_BEGIN = "2006-01-01"
USGS_PARAMETER_CODES = "00062,00010,00021,00035,00036,00045,00052"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fetch(url: str, timeout: float = 180.0) -> tuple[bytes, str, str]:
    request = Request(
        url,
        headers={
            "User-Agent": "Research-FREnTE/savannah-system-collector",
            "Accept": "*/*",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        payload = response.read()
        media_type = response.headers.get("Content-Type", "")
        final_url = response.geturl()
    return payload, media_type, final_url


def _artifact(
    *,
    run_dir: Path,
    path: Path,
    target_id: str,
    source_name: str,
    download_url: str,
    media_type: str,
    status: str,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    payload = path.read_bytes()
    return {
        "artifact_id": f"{target_id}-{path.stem}",
        "target_id": target_id,
        "source_name": source_name,
        "status": status,
        "relative_path": path.relative_to(run_dir).as_posix(),
        "download_url": download_url,
        "media_type": media_type,
        "file_format": path.suffix.lstrip(".") or "bin",
        "content_length": len(payload),
        "checksum_sha256": hashlib.sha256(payload).hexdigest(),
        "notes": notes or [],
        "collected_at": _utcnow().isoformat().replace("+00:00", "Z"),
    }


def _iso_end() -> tuple[str, str]:
    now = _utcnow()
    usace_end = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    usgs_end = now.date().isoformat()
    return usace_end, usgs_end


def _requested_period(target: dict[str, Any]) -> tuple[str, str]:
    year_start = target.get("requested_year_start", 2006)
    _, usgs_end = _iso_end()
    return f"{year_start}-01-01", usgs_end


def _gap_note(
    *,
    applicable: bool,
    actual_start: str | None,
    actual_end: str | None,
) -> tuple[str | None, str | None]:
    if not applicable:
        return None, "20-year target window not applicable for this endpoint."
    if not actual_start or not actual_end:
        return None, "20-year target window requested, but actual returned period could not be confirmed from the payload."
    actual_start_date = actual_start[:10]
    actual_end_date = actual_end[:10]
    if actual_start_date <= TARGET_START:
        return "met_or_exceeded", f"20-year target window requested from {TARGET_START}; payload returned coverage from {actual_start_date} to {actual_end_date}."
    return "shorter_than_target", (
        f"20-year target window requested from {TARGET_START}, but payload returned only {actual_start_date} to {actual_end_date}."
    )


def _extract_dates_from_water_usace(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    values = payload.get("values") or []
    if not values:
        return None, None
    start = values[0][0] if isinstance(values[0], list) and values[0] else None
    end = values[-1][0] if isinstance(values[-1], list) and values[-1] else None
    return start, end


def _extract_dates_from_usgs(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    series = (((payload.get("value") or {}).get("timeSeries")) or [])
    dates: list[str] = []
    for item in series:
        blocks = item.get("values") or []
        for block in blocks:
            for value in block.get("value") or []:
                dt = value.get("dateTime")
                if dt:
                    dates.append(dt)
    if not dates:
        return None, None
    dates.sort()
    return dates[0], dates[-1]


def _extract_dates_from_csv(path: Path) -> tuple[str | None, str | None]:
    dates: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            for key, value in row.items():
                if value and ("Date" in key or key == "AnalysisStartDate"):
                    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                        dates.append(value)
    if not dates:
        return None, None
    dates.sort()
    return dates[0], dates[-1]


def _extract_direct_links(html_text: str, base_url: str) -> list[str]:
    hrefs = re.findall(r"""href=["']([^"']+)["']""", html_text, flags=re.IGNORECASE)
    links: list[str] = []
    seen: set[str] = set()
    for href in hrefs:
        resolved = urljoin(base_url, unescape(href))
        lower = resolved.lower()
        if not any(ext in lower for ext in (".pdf", ".zip", ".tif", ".tiff", ".csv", ".xml")):
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        links.append(resolved)
    return links


def _extract_json_links(payload: Any) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()

    def _walk(value: Any) -> None:
        if isinstance(value, dict):
            for nested in value.values():
                _walk(nested)
            return
        if isinstance(value, list):
            for nested in value:
                _walk(nested)
            return
        if not isinstance(value, str):
            return
        lowered = value.lower()
        if not lowered.startswith(("http://", "https://")):
            return
        if not any(token in lowered for token in (".csv", ".zip", ".pdf", ".xml", ".xlsx", "/download")):
            return
        if value in seen:
            return
        seen.add(value)
        links.append(value)

    _walk(payload)
    return links


def _build_target_base(target: dict[str, Any]) -> dict[str, Any]:
    requested_start, requested_end = _requested_period(target)
    return {
        "target_id": target["source_slug"],
        "source_name": target["source_name"],
        "dataset_name": target["dataset_name"],
        "collection_status": "not_attempted",
        "access_type": target.get("access_type", "unknown"),
        "collection_method": target.get("collection_method_hint", "direct_download"),
        "requires_auth": False,
        "provenance_urls": [target["start_url"]],
        "blockers": [],
        "notes": [],
        "join_keys": ["reservoir_id", "reservoir_name", "date", "year", "month", "ano_mes", "station_id", "site_no", "gage_id"],
        "staging_outputs": [],
        "analytic_outputs": [],
        "raw_artifacts": [],
        "target_window_years": target.get("target_window_years", TARGET_WINDOW_YEARS),
        "requested_period_start": requested_start,
        "requested_period_end": requested_end,
        "actual_period_start": None,
        "actual_period_end": None,
        "coverage_window_status": None,
        "coverage_note": None,
        "track_origin": target.get("track_origin"),
        "track_priority": target.get("track_priority"),
        "reservoir_scope": target.get("spatial_coverage"),
        "source_domain": target.get("source_domain"),
        "requested_parameters": target.get("key_parameters", []),
    }


def _collect_water_usace(target: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    target_dir = run_dir / "collection" / target["source_slug"]
    ensure_dir(target_dir)
    payload = _build_target_base(target)
    slug = urlparse(target["start_url"]).path.rstrip("/").split("/")[-1]
    artifacts = payload["raw_artifacts"]
    usace_end, _ = _iso_end()

    location_bytes, media_type, final_url = _fetch(target["start_url"])
    location_path = target_dir / f"location_{slug}.json"
    write_bytes(location_path, location_bytes)
    artifacts.append(
        _artifact(
            run_dir=run_dir,
            path=location_path,
            target_id=payload["target_id"],
            source_name=payload["source_name"],
            download_url=final_url,
            media_type=media_type or "application/json",
            status="collected",
            notes=["Official water.usace location payload collected."],
        )
    )
    location_payload = json.loads(location_bytes.decode("utf-8"))
    timeseries = location_payload[0]["timeseries"]
    tsid_map: dict[str, dict[str, str]] = {}
    for item in timeseries:
        label = (item.get("label") or "").strip().lower()
        tsid = item.get("tsid")
        if not tsid:
            continue
        if label == "elevation" and "elevation" not in tsid_map:
            tsid_map["elevation"] = {"tsid": tsid, "label": item.get("label", "")}
        elif "conservation storage" in label and "storage" not in tsid_map:
            tsid_map["storage"] = {"tsid": tsid, "label": item.get("label", "")}
        elif label == "inflow" and "inflow" not in tsid_map:
            tsid_map["inflow"] = {"tsid": tsid, "label": item.get("label", "")}
        elif label == "outflow" and "outflow" not in tsid_map:
            tsid_map["outflow"] = {"tsid": tsid, "label": item.get("label", "")}
        elif "tailwater" in label and "tailwater" not in tsid_map:
            tsid_map["tailwater"] = {"tsid": tsid, "label": item.get("label", "")}
        elif "release" in label and "release" not in tsid_map:
            tsid_map["release"] = {"tsid": tsid, "label": item.get("label", "")}
        elif "power generation" in label and "power_generation" not in tsid_map:
            tsid_map["power_generation"] = {"tsid": tsid, "label": item.get("label", "")}

    pattern_note = [
        "Confirmed history pattern for water.usace operational series:",
        f"https://water.usace.army.mil/cda/reporting/providers/sas/timeseries?begin={USACE_BEGIN}&end={usace_end}&name=<urlencoded_tsid>",
        "",
        "Collected series in this pass:",
    ]
    actual_starts: list[str] = []
    actual_ends: list[str] = []
    failures = 0
    for metric, ts_meta in tsid_map.items():
        params = {"begin": USACE_BEGIN, "end": usace_end, "name": ts_meta["tsid"]}
        ts_url = f"https://water.usace.army.mil/cda/reporting/providers/sas/timeseries?{urlencode(params)}"
        try:
            ts_bytes, ts_media, ts_final_url = _fetch(ts_url, timeout=300.0)
            ts_path = target_dir / f"timeseries_{metric}.json"
            write_bytes(ts_path, ts_bytes)
            artifacts.append(
                _artifact(
                    run_dir=run_dir,
                    path=ts_path,
                    target_id=payload["target_id"],
                    source_name=payload["source_name"],
                    download_url=ts_final_url,
                    media_type=ts_media or "application/json",
                    status="collected",
                    notes=[f"{ts_meta['label']} timeseries collected with a 20-year target window."],
                )
            )
            ts_payload = json.loads(ts_bytes.decode("utf-8"))
            start, end = _extract_dates_from_water_usace(ts_payload)
            if start:
                actual_starts.append(start)
            if end:
                actual_ends.append(end)
            pattern_note.append(f"- {ts_meta['tsid']}")
        except Exception as exc:
            failures += 1
            payload["blockers"].append(f"Failed to collect water.usace timeseries {metric}: {exc}")

    pattern_path = target_dir / "history_pattern_confirmed.txt"
    write_markdown(pattern_path, "\n".join(pattern_note).rstrip() + "\n")
    artifacts.append(
        _artifact(
            run_dir=run_dir,
            path=pattern_path,
            target_id=payload["target_id"],
            source_name=payload["source_name"],
            download_url=target["start_url"],
            media_type="text/plain",
            status="endpoint_confirmed",
            notes=["Confirmed reusable history endpoint pattern and selected tsids."],
        )
    )

    if actual_starts and actual_ends:
        payload["actual_period_start"] = min(actual_starts)
        payload["actual_period_end"] = max(actual_ends)
    payload["coverage_window_status"], payload["coverage_note"] = _gap_note(
        applicable=True,
        actual_start=payload["actual_period_start"],
        actual_end=payload["actual_period_end"],
    )
    if payload["coverage_note"]:
        payload["notes"].append(payload["coverage_note"])
    payload["notes"].append("No Thurmond-only bias applied; same collection logic used for Hartwell, Russell, and Thurmond water.usace locations.")
    payload["collection_status"] = "collected" if failures == 0 and len(artifacts) > 2 else "partial"
    return payload


def _collect_nid(target: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    target_dir = run_dir / "collection" / target["source_slug"]
    ensure_dir(target_dir)
    payload = _build_target_base(target)
    inventory_url = target["start_url"]
    dam_id = inventory_url.rstrip("/").split("/")[-2]
    data_source_url = inventory_url.rsplit("/", 1)[0] + "/data-source"
    artifacts = payload["raw_artifacts"]
    for url, filename, note in (
        (inventory_url, f"inventory_{dam_id}.json", "Official NID inventory JSON collected."),
        (data_source_url, f"data_source_{dam_id}.json", "Official NID data-source JSON collected."),
    ):
        try:
            content, media_type, final_url = _fetch(url)
            path = target_dir / filename
            write_bytes(path, content)
            artifacts.append(
                _artifact(
                    run_dir=run_dir,
                    path=path,
                    target_id=payload["target_id"],
                    source_name=payload["source_name"],
                    download_url=final_url,
                    media_type=media_type or "application/json",
                    status="collected",
                    notes=[note],
                )
            )
            payload["provenance_urls"].append(final_url)
        except Exception as exc:
            payload["blockers"].append(f"Failed to collect NID endpoint {url}: {exc}")
    payload["coverage_window_status"], payload["coverage_note"] = _gap_note(applicable=False, actual_start=None, actual_end=None)
    if payload["coverage_note"]:
        payload["notes"].append(payload["coverage_note"])
    payload["collection_status"] = "collected" if len(artifacts) == 2 else "partial"
    return payload


def _collect_usgs(target: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    target_dir = run_dir / "collection" / target["source_slug"]
    ensure_dir(target_dir)
    payload = _build_target_base(target)
    start_url = target["start_url"]
    parsed_start = urlparse(start_url)
    query = parse_qs(parsed_start.query)
    site_no_match = re.search(r"(\d{8,9})", start_url)
    site_no = site_no_match.group(1) if site_no_match else target["source_slug"].split("-")[2]
    _, usgs_end = _iso_end()
    artifacts = payload["raw_artifacts"]
    actual_starts: list[str] = []
    actual_ends: list[str] = []
    requested_parameter_codes = ",".join(query.get("parameterCd", [])) or USGS_PARAMETER_CODES

    try:
        content, media_type, final_url = _fetch(start_url, timeout=300.0)
        requested_name = "requested_endpoint.json" if "format=json" in start_url else f"start_{site_no}.html"
        requested_path = target_dir / requested_name
        write_bytes(requested_path, content)
        artifacts.append(
            _artifact(
                run_dir=run_dir,
                path=requested_path,
                target_id=payload["target_id"],
                source_name=payload["source_name"],
                download_url=final_url,
                media_type=media_type or "application/json",
                status="collected",
                notes=["USGS requested endpoint captured for provenance."],
            )
        )
        if requested_name.endswith(".json"):
            parsed = json.loads(content.decode("utf-8"))
            start, end = _extract_dates_from_usgs(parsed)
            if start:
                actual_starts.append(start)
            if end:
                actual_ends.append(end)
    except Exception as exc:
        payload["blockers"].append(f"Failed to collect primary USGS endpoint for {site_no}: {exc}")

    for url, filename, note in (
        (f"https://waterdata.usgs.gov/nwis/inventory?agency_code=USGS&site_no={site_no}", f"inventory_{site_no}.html", "USGS inventory page captured."),
        (f"https://waterservices.usgs.gov/nwis/site/?format=rdb&sites={site_no}&siteOutput=expanded", f"site_{site_no}.rdb", "USGS site metadata collected."),
    ):
        try:
            content, media_type, final_url = _fetch(url)
            path = target_dir / filename
            write_bytes(path, content)
            artifacts.append(
                _artifact(
                    run_dir=run_dir,
                    path=path,
                    target_id=payload["target_id"],
                    source_name=payload["source_name"],
                    download_url=final_url,
                    media_type=media_type or "text/html",
                    status="collected",
                    notes=[note],
                )
            )
            if final_url not in payload["provenance_urls"]:
                payload["provenance_urls"].append(final_url)
        except Exception as exc:
            payload["blockers"].append(f"Failed to collect USGS provenance endpoint {url}: {exc}")

    for service, filename in (("iv", f"iv_{site_no}.json"), ("dv", f"dv_{site_no}.json")):
        params = {
            "format": "json",
            "sites": site_no,
            "parameterCd": requested_parameter_codes,
            "siteStatus": "all",
            "startDT": USGS_BEGIN,
            "endDT": usgs_end,
        }
        url = f"https://waterservices.usgs.gov/nwis/{service}/?{urlencode(params)}"
        try:
            content, media_type, final_url = _fetch(url, timeout=300.0)
            path = target_dir / filename
            write_bytes(path, content)
            artifacts.append(
                _artifact(
                    run_dir=run_dir,
                    path=path,
                    target_id=payload["target_id"],
                    source_name=payload["source_name"],
                    download_url=final_url,
                    media_type=media_type or "application/json",
                    status="collected",
                    notes=[f"USGS {service.upper()} service collected with a 20-year target window."],
                )
            )
            parsed = json.loads(content.decode("utf-8"))
            start, end = _extract_dates_from_usgs(parsed)
            if start:
                actual_starts.append(start)
            if end:
                actual_ends.append(end)
        except Exception as exc:
            payload["blockers"].append(f"Failed to collect USGS {service.upper()} endpoint for {site_no}: {exc}")

    if actual_starts and actual_ends:
        payload["actual_period_start"] = min(actual_starts)
        payload["actual_period_end"] = max(actual_ends)
    payload["coverage_window_status"], payload["coverage_note"] = _gap_note(
        applicable=True,
        actual_start=payload["actual_period_start"],
        actual_end=payload["actual_period_end"],
    )
    if payload["coverage_note"]:
        payload["notes"].append(payload["coverage_note"])
    payload["collection_status"] = "collected" if len(artifacts) >= 5 and not payload["blockers"] else "partial"
    return payload


def _collect_wqp(target: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    target_dir = run_dir / "collection" / target["source_slug"]
    ensure_dir(target_dir)
    payload = _build_target_base(target)
    artifacts = payload["raw_artifacts"]
    parsed = urlparse(target["start_url"])
    query = parse_qs(parsed.query)
    site_id = query.get("siteid", [None])[0]
    if not site_id:
        site_match = re.search(r"(USGS-\d{8,9}|USGS-[A-Z]{2}|[A-Z]+-\d+)", target["start_url"])
        site_id = site_match.group(1) if site_match else target["start_url"].rstrip("/").split("/")[-1]
    provider_match = re.search(r"/provider/([^/]+)/", target["start_url"])
    provider_code = query.get("providers", [None])[0] or (provider_match.group(1) if provider_match else "NWIS")
    result_end = payload["requested_period_end"]
    start_is_provider = "/provider/" in parsed.path

    if start_is_provider:
        try:
            provider_bytes, provider_media, provider_url = _fetch(target["start_url"])
            provider_path = target_dir / f"provider_{site_id}.html"
            write_bytes(provider_path, provider_bytes)
            artifacts.append(
                _artifact(
                    run_dir=run_dir,
                    path=provider_path,
                    target_id=payload["target_id"],
                    source_name=payload["source_name"],
                    download_url=provider_url,
                    media_type=provider_media or "text/html",
                    status="collected",
                    notes=["Provider page captured for provenance."],
                )
            )
        except Exception as exc:
            payload["blockers"].append(f"Failed to collect WQP provider page for {site_id}: {exc}")

    station_url = (
        "https://www.waterqualitydata.us/data/Station/search?"
        + urlencode({"siteid": site_id, "mimeType": "csv", "zip": "no", "providers": provider_code})
    )
    result_url = (
        "https://www.waterqualitydata.us/data/Result/search?"
        + urlencode(
            {
                "siteid": site_id,
                "mimeType": "csv",
                "zip": "no",
                "providers": provider_code,
                "startDateLo": WQP_BEGIN,
                "startDateHi": result_end,
            }
        )
    )
    actual_start = None
    actual_end = None
    for url, filename, note in (
        (station_url, f"station_{site_id}.csv", "WQP station export collected."),
        (result_url, f"result_{site_id}.csv", "WQP result export collected with a 20-year target window."),
    ):
        try:
            content, media_type, final_url = _fetch(url, timeout=300.0)
            path = target_dir / filename
            write_bytes(path, content)
            artifacts.append(
                _artifact(
                    run_dir=run_dir,
                    path=path,
                    target_id=payload["target_id"],
                    source_name=payload["source_name"],
                    download_url=final_url,
                    media_type=media_type or "text/csv",
                    status="collected",
                    notes=[note],
                )
            )
            if "result_" in filename:
                actual_start, actual_end = _extract_dates_from_csv(path)
        except Exception as exc:
            payload["blockers"].append(f"Failed to collect WQP export {filename} for {site_id}: {exc}")

    payload["actual_period_start"] = actual_start
    payload["actual_period_end"] = actual_end
    payload["coverage_window_status"], payload["coverage_note"] = _gap_note(
        applicable=True,
        actual_start=actual_start,
        actual_end=actual_end,
    )
    if payload["coverage_note"]:
        payload["notes"].append(payload["coverage_note"])
    payload["collection_status"] = "collected" if len(artifacts) >= 3 and not payload["blockers"] else "partial"
    return payload


def _collect_sciencebase(target: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    target_dir = run_dir / "collection" / target["source_slug"]
    ensure_dir(target_dir)
    payload = _build_target_base(target)
    artifacts = payload["raw_artifacts"]

    try:
        content, media_type, final_url = _fetch(target["start_url"], timeout=300.0)
        meta_path = target_dir / "sciencebase_metadata.json"
        write_bytes(meta_path, content)
        artifacts.append(
            _artifact(
                run_dir=run_dir,
                path=meta_path,
                target_id=payload["target_id"],
                source_name=payload["source_name"],
                download_url=final_url,
                media_type=media_type or "application/json",
                status="collected",
                notes=["ScienceBase metadata JSON collected."],
            )
        )
        payload_json = json.loads(content.decode("utf-8"))
        for index, link in enumerate(_extract_json_links(payload_json)[:8], start=1):
            try:
                asset_bytes, asset_media, asset_url = _fetch(link, timeout=300.0)
                asset_name = Path(urlparse(asset_url).path).name or f"sciencebase_asset_{index}.bin"
                if "." not in asset_name:
                    if "csv" in (asset_media or "").lower():
                        asset_name = f"{asset_name}.csv"
                    elif "zip" in (asset_media or "").lower():
                        asset_name = f"{asset_name}.zip"
                    elif "pdf" in (asset_media or "").lower():
                        asset_name = f"{asset_name}.pdf"
                asset_path = target_dir / asset_name
                write_bytes(asset_path, asset_bytes)
                artifacts.append(
                    _artifact(
                        run_dir=run_dir,
                        path=asset_path,
                        target_id=payload["target_id"],
                        source_name=payload["source_name"],
                        download_url=asset_url,
                        media_type=asset_media or "application/octet-stream",
                        status="collected",
                        notes=["Artifact discovered from ScienceBase metadata."],
                    )
                )
            except Exception as exc:
                payload["blockers"].append(f"Failed to collect ScienceBase asset {link}: {exc}")
    except Exception as exc:
        payload["blockers"].append(f"Failed to collect ScienceBase metadata: {exc}")

    payload["coverage_window_status"], payload["coverage_note"] = _gap_note(applicable=False, actual_start=None, actual_end=None)
    if payload["coverage_note"]:
        payload["notes"].append(payload["coverage_note"])
    payload["collection_status"] = "collected" if len(artifacts) > 1 and not payload["blockers"] else ("partial" if artifacts else "error")
    return payload


def _extract_text_from_html(html_bytes: bytes) -> str | None:
    text = html_bytes.decode("utf-8", errors="replace")
    pre_match = re.search(r"<pre[^>]*>(.*?)</pre>", text, flags=re.IGNORECASE | re.DOTALL)
    if pre_match:
        body = unescape(pre_match.group(1))
        body = re.sub(r"<[^>]+>", "", body)
        return body.strip() or None
    return None


def _collect_nws(target: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    target_dir = run_dir / "collection" / target["source_slug"]
    ensure_dir(target_dir)
    payload = _build_target_base(target)
    artifacts = payload["raw_artifacts"]
    content, media_type, final_url = _fetch(target["start_url"], timeout=180.0)
    raw_path = target_dir / "rvf_cae_v1.txt"
    write_bytes(raw_path, content)
    artifacts.append(
        _artifact(
            run_dir=run_dir,
            path=raw_path,
            target_id=payload["target_id"],
            source_name=payload["source_name"],
            download_url=final_url,
            media_type=media_type or "text/plain",
            status="partial",
            notes=["Raw NWS RVF response captured."],
        )
    )
    normalized = _extract_text_from_html(content)
    if normalized:
        normalized_path = target_dir / "rvf_cae_v1.normalized.txt"
        write_markdown(normalized_path, normalized + "\n")
        artifacts.append(
            _artifact(
                run_dir=run_dir,
                path=normalized_path,
                target_id=payload["target_id"],
                source_name=payload["source_name"],
                download_url=final_url,
                media_type="text/plain",
                status="collected",
                notes=["Normalized plain-text bulletin extracted from HTML-wrapped response."],
            )
        )
        payload["collection_status"] = "collected"
        payload["notes"].append("Current bulletin collected; 20-year target window not applicable to the RVF product.")
    else:
        payload["collection_status"] = "partial"
        payload["blockers"].append("RVF endpoint responded without extractable plain-text bulletin content.")
    payload["coverage_window_status"], payload["coverage_note"] = _gap_note(applicable=False, actual_start=None, actual_end=None)
    return payload


def _collect_direct_context(target: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    target_dir = run_dir / "collection" / target["source_slug"]
    ensure_dir(target_dir)
    payload = _build_target_base(target)
    artifacts = payload["raw_artifacts"]
    content, media_type, final_url = _fetch(target["start_url"], timeout=180.0)
    parsed = urlparse(final_url)
    suffix = Path(parsed.path).suffix.lower()
    inferred_suffix = suffix
    media_type_lower = (media_type or "").lower()
    if not inferred_suffix:
        if "pdf" in media_type_lower:
            inferred_suffix = ".pdf"
        elif "zip" in media_type_lower:
            inferred_suffix = ".zip"
        elif "xml" in media_type_lower:
            inferred_suffix = ".xml"
    if inferred_suffix in {".pdf", ".zip", ".tif", ".tiff", ".xml"}:
        filename = Path(parsed.path).name or f"{target['source_slug']}{inferred_suffix or '.bin'}"
        if "." not in filename:
            filename = f"{filename}{inferred_suffix}"
        path = target_dir / filename
        write_bytes(path, content)
        artifacts.append(
            _artifact(
                run_dir=run_dir,
                path=path,
                target_id=payload["target_id"],
                source_name=payload["source_name"],
                download_url=final_url,
                media_type=media_type,
                status="collected",
                notes=["Direct contextual artifact downloaded."],
            )
        )
        payload["collection_status"] = "collected"
    else:
        landing_path = target_dir / "landing.html"
        write_bytes(landing_path, content)
        artifacts.append(
            _artifact(
                run_dir=run_dir,
                path=landing_path,
                target_id=payload["target_id"],
                source_name=payload["source_name"],
                download_url=final_url,
                media_type=media_type or "text/html",
                status="collected",
                notes=["Landing page captured for provenance and artifact discovery."],
            )
        )
        extracted = _extract_direct_links(content.decode("utf-8", errors="replace"), final_url)
        for index, link in enumerate(extracted[:5], start=1):
            try:
                asset_bytes, asset_media, asset_url = _fetch(link, timeout=180.0)
                asset_name = Path(urlparse(asset_url).path).name or f"asset_{index}.bin"
                asset_path = target_dir / asset_name
                write_bytes(asset_path, asset_bytes)
                artifacts.append(
                    _artifact(
                        run_dir=run_dir,
                        path=asset_path,
                        target_id=payload["target_id"],
                        source_name=payload["source_name"],
                        download_url=asset_url,
                        media_type=asset_media or "application/octet-stream",
                        status="collected",
                        notes=["Direct artifact discovered from landing page."],
                    )
                )
            except Exception as exc:
                payload["blockers"].append(f"Failed to collect contextual asset {link}: {exc}")
        payload["collection_status"] = "collected" if len(artifacts) > 1 else "partial"
    payload["coverage_window_status"], payload["coverage_note"] = _gap_note(applicable=False, actual_start=None, actual_end=None)
    if payload["coverage_note"]:
        payload["notes"].append(payload["coverage_note"])
    return payload


def _collect_local_reference(target: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    target_dir = run_dir / "collection" / target["source_slug"]
    ensure_dir(target_dir)
    payload = _build_target_base(target)
    artifacts = payload["raw_artifacts"]
    ref_path = Path(target["start_url"])
    if not ref_path.exists():
        payload["collection_status"] = "blocked"
        payload["blockers"].append(f"Local annex reference not found: {ref_path.as_posix()}")
        return payload

    dest_path = target_dir / ref_path.name
    write_bytes(dest_path, ref_path.read_bytes())
    artifacts.append(
        _artifact(
            run_dir=run_dir,
            path=dest_path,
            target_id=payload["target_id"],
            source_name=payload["source_name"],
            download_url=ref_path.as_posix(),
            media_type="application/json",
            status="collected",
            notes=["Existing reservoir operations annex manifest copied into the river-first run as a provenance reference."],
        )
    )
    payload["collection_status"] = "collected"
    payload["notes"].append("Reservoir operations annex reused from existing run; no recollection performed in this river-first pass.")
    payload["coverage_window_status"], payload["coverage_note"] = _gap_note(applicable=False, actual_start=None, actual_end=None)
    if payload["coverage_note"]:
        payload["notes"].append(payload["coverage_note"])
    return payload


def _collect_target(target: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    if "des.sc.gov" in target["start_url"]:
        payload = _build_target_base(target)
        payload["collection_status"] = "blocked"
        payload["blockers"].append("Target skipped by policy: des.sc.gov cannot be touched without new alignment from the main chat.")
        return payload
    if "sciencebase.gov" in target["start_url"]:
        return _collect_sciencebase(target, run_dir)
    domain = target.get("source_domain", "")
    if domain == "water.usace.army.mil":
        return _collect_water_usace(target, run_dir)
    if domain == "nid.sec.usace.army.mil":
        return _collect_nid(target, run_dir)
    if domain in {"waterdata.usgs.gov", "waterservices.usgs.gov"}:
        return _collect_usgs(target, run_dir)
    if domain == "waterqualitydata.us":
        return _collect_wqp(target, run_dir)
    if domain == "forecast.weather.gov":
        return _collect_nws(target, run_dir)
    if domain == "local_workspace":
        return _collect_local_reference(target, run_dir)
    return _collect_direct_context(target, run_dir)


def _build_report(run_id: str, targets: list[dict[str, Any]], handoff_path: Path) -> str:
    collected = sum(1 for item in targets if item["collection_status"] == "collected")
    partial = sum(1 for item in targets if item["collection_status"] == "partial")
    blocked = sum(1 for item in targets if item["collection_status"] == "blocked")
    error = sum(1 for item in targets if item["collection_status"] == "error")
    lines = [
        f"# Coleta operacional {run_id}",
        "",
        f"- Handoff de origem: {handoff_path.as_posix()}",
        "- Escopo: Savannah River como objeto principal; Hartwell, Russell e Thurmond apenas como anexo operacional de referencia.",
        "- Regra temporal: sempre solicitar janela-alvo de 20 anos quando a fonte permitir; persistir e documentar cobertura real retornada.",
        "- Restricao: des.sc.gov nao foi tocado nesta rodada.",
        "",
        f"- Targets: {len(targets)}",
        f"- Coletados: {collected}",
        f"- Parciais: {partial}",
        f"- Bloqueados: {blocked}",
        f"- Erros: {error}",
        "",
    ]
    for target in targets:
        lines.extend(
            [
                f"## {target['target_id']}",
                "",
                f"- Status: {target['collection_status']}",
                f"- Fonte: {target['source_name']}",
                f"- Dataset: {target['dataset_name']}",
                f"- Janela-alvo: {target['requested_period_start']} -> {target['requested_period_end']}",
                f"- Cobertura real: {target['actual_period_start'] or 'n/a'} -> {target['actual_period_end'] or 'n/a'}",
                f"- Regra de cobertura: {target['coverage_note'] or 'n/a'}",
                f"- Artefatos brutos: {len(target['raw_artifacts'])}",
            ]
        )
        if target["blockers"]:
            lines.append(f"- Bloqueios: {' | '.join(target['blockers'])}")
        if target["notes"]:
            lines.append(f"- Notas: {' | '.join(target['notes'])}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--handoff", required=True)
    args = parser.parse_args()

    handoff_path = Path(args.handoff)
    handoff = json.loads(handoff_path.read_text(encoding="utf-8-sig"))
    timestamp = _utcnow().strftime("%Y%m%d-%H%M%S")
    run_prefix = "operational-collect-savannah-river" if "river" in handoff_path.name.lower() else "operational-collect-savannah-system"
    run_id = f"{run_prefix}-{timestamp}"
    run_dir = Path("data") / "runs" / run_id
    for subdir in ("config", "collection", "processing", "reports"):
        ensure_dir(run_dir / subdir)

    options = {
        "source_handoff": handoff_path.as_posix(),
        "source_research_id": handoff.get("research_id"),
        "target_window_years": TARGET_WINDOW_YEARS,
        "requested_year_start": 2006,
        "requested_year_end": _utcnow().year,
        "river_scope": ["Savannah River"],
        "reservoir_scope": ["Hartwell", "Russell", "Thurmond"],
        "do_not_touch_domains": ["des.sc.gov"],
        "priorities": [
            "WQP and USGS Savannah River sites",
            "NWS RVF text product",
            "existing Hartwell/Russell/Thurmond operational annex reference",
            "NWS RVF text product",
            "NOAA/EPA/DEQ/Clemson contextual artifacts",
        ],
    }
    write_json(run_dir / "config" / "collection-options.json", options)

    results: list[dict[str, Any]] = []
    for target in handoff["targets"]:
        try:
            results.append(_collect_target(target, run_dir))
        except Exception as exc:
            failed = _build_target_base(target)
            failed["collection_status"] = "error"
            failed["blockers"].append(f"Unhandled collection error: {exc}")
            results.append(failed)

    write_json(run_dir / "processing" / "01-collection-targets.json", results)

    manifest = {
        "run_id": run_id,
        "pipeline_name": "curated_harvester_collection",
        "generated_at": _utcnow().isoformat().replace("+00:00", "Z"),
        "source_research_id": handoff.get("research_id"),
        "source_handoff": handoff_path.as_posix(),
        "target_count": len(results),
        "target_ids": [item["target_id"] for item in results],
        "collected_count": sum(1 for item in results if item["collection_status"] == "collected"),
        "partial_count": sum(1 for item in results if item["collection_status"] == "partial"),
        "blocked_count": sum(1 for item in results if item["collection_status"] == "blocked"),
        "error_count": sum(1 for item in results if item["collection_status"] == "error"),
        "primary_analytical_object": "Savannah River",
        "reservoir_annex_scope": ["Hartwell", "Russell", "Thurmond"],
        "sediment_target": "Thurmond",
        "target_window_years": TARGET_WINDOW_YEARS,
        "targets": results,
    }
    manifest_path = run_dir / "manifest.json"
    write_json(manifest_path, manifest)

    report_text = _build_report(run_id, results, handoff_path)
    report_path = run_dir / "reports" / f"{run_id}.md"
    write_markdown(report_path, report_text)

    csv_rows = [
        {
            "target_id": item["target_id"],
            "source_name": item["source_name"],
            "dataset_name": item["dataset_name"],
            "collection_status": item["collection_status"],
            "actual_period_start": item["actual_period_start"] or "",
            "actual_period_end": item["actual_period_end"] or "",
            "coverage_window_status": item["coverage_window_status"] or "",
            "raw_artifact_count": len(item["raw_artifacts"]),
            "blockers": " | ".join(item["blockers"]),
        }
        for item in results
    ]
    write_catalog_csv(
        run_dir / "reports" / "collection_targets.csv",
        csv_rows,
        fieldnames=[
            "target_id",
            "source_name",
            "dataset_name",
            "collection_status",
            "actual_period_start",
            "actual_period_end",
            "coverage_window_status",
            "raw_artifact_count",
            "blockers",
        ],
    )

    print(json.dumps({"run_id": run_id, "run_dir": run_dir.as_posix(), "manifest_path": manifest_path.as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
