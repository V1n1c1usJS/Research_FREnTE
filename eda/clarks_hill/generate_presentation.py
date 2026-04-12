"""
Render the Clarks Hill / Savannah River HTML report from structured context.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import defaultdict
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EDA_DIR = Path(__file__).resolve().parent
DEFAULT_CONTEXT = EDA_DIR / "report_context.json"
DEFAULT_OUTPUT = ROOT / "docs" / "clarks-hill" / "index.html"
DOCS_ASSETS = ROOT / "docs" / "assets"

TAG_STYLES = {
    "blue": {
        "badge_bg": "rgba(1,30,66,.10)",
        "badge_color": "#011E42",
        "callout_bg": "rgba(1,30,66,.08)",
        "callout_border": "#011E42",
    },
    "green": {
        "badge_bg": "rgba(15,123,95,.10)",
        "badge_color": "#0F7B5F",
        "callout_bg": "rgba(16,185,129,.10)",
        "callout_border": "#065f46",
    },
    "purple": {
        "badge_bg": "rgba(107,72,168,.10)",
        "badge_color": "#6B48A8",
        "callout_bg": "rgba(167,139,250,.12)",
        "callout_border": "#6D28D9",
    },
    "orange": {
        "badge_bg": "rgba(199,93,44,.10)",
        "badge_color": "#C75D2C",
        "callout_bg": "rgba(251,146,60,.12)",
        "callout_border": "#C2410C",
    },
    "red": {
        "badge_bg": "rgba(185,28,28,.10)",
        "badge_color": "#B91C1C",
        "callout_bg": "rgba(254,226,226,1)",
        "callout_border": "#9F1239",
    },
    "stone": {
        "badge_bg": "rgba(120,113,108,.12)",
        "badge_color": "#57534E",
        "callout_bg": "rgba(245,245,244,1)",
        "callout_border": "#44403C",
    },
}

METRIC_STYLES = {
    "blue": {"bg": "rgba(255,255,255,.07)", "color": "#C4A86C"},
    "green": {"bg": "rgba(255,255,255,.07)", "color": "#86C53F"},
    "gold": {"bg": "rgba(255,255,255,.07)", "color": "#C4A86C"},
    "red": {"bg": "rgba(255,255,255,.07)", "color": "#FCA5A5"},
    "dark": {"bg": "rgba(255,255,255,.07)", "color": "#E2E8F0"},
}

SECTION_DEFAULTS = {
    "river-first-frame": {"icon": "waves", "eyebrow": "River Frame"},
    "river-pressures-pollutants": {"icon": "science", "eyebrow": "Pressures And Pollutants"},
    "coverage-status": {"icon": "grid_view", "eyebrow": "Coverage Status"},
    "reservoir-modulation": {"icon": "water", "eyebrow": "Reservoir Annex"},
    "thurmond-bridge": {"icon": "hub", "eyebrow": "Sediment Bridge"},
    "methods-and-gaps": {"icon": "rule", "eyebrow": "Methods And Gaps"},
}

STATUS_LABELS = {
    "ready": "Ready",
    "partial": "Partial",
    "placeholder": "Pending",
    "meets_target": "Meets target",
    "below_target": "Below target",
    "snapshot": "Snapshot only",
}

STATUS_TONES = {
    "ready": ("#DCFCE7", "#166534"),
    "partial": ("#FEF3C7", "#92400E"),
    "placeholder": ("#E2E8F0", "#475569"),
    "meets_target": ("#DCFCE7", "#166534"),
    "below_target": ("#FEE2E2", "#991B1B"),
    "snapshot": ("#E0F2FE", "#075985"),
}

TAG_COLOR_BY_NAME = {
    "river signal": "blue",
    "river chemistry": "green",
    "operations": "orange",
    "interpretation": "green",
    "coverage": "red",
    "overlap": "blue",
    "sediment texture": "green",
    "sediment relations": "stone",
    "basin pressures": "green",
    "data availability": "blue",
}

ICON_BY_TAG = {
    "river signal": "show_chart",
    "river chemistry": "science",
    "operations": "water",
    "interpretation": "hub",
    "coverage": "grid_view",
    "overlap": "table_chart",
    "sediment texture": "stacked_bar_chart",
    "sediment relations": "scatter_plot",
    "basin pressures": "warning",
    "data availability": "inventory_2",
}

DOMAIN_STYLES = {
    "river_core": {"icon": "waves", "accent": "#1D4ED8", "bg": "rgba(29,78,216,.08)", "eyebrow": "River core"},
    "pressure_core": {"icon": "science", "accent": "#0F7B5F", "bg": "rgba(15,123,95,.08)", "eyebrow": "Pressure core"},
    "reservoir_support": {"icon": "water", "accent": "#C75D2C", "bg": "rgba(199,93,44,.08)", "eyebrow": "Reservoir annex"},
    "sediment_response": {"icon": "experiment", "accent": "#6B48A8", "bg": "rgba(107,72,168,.08)", "eyebrow": "Sediment response"},
    "supporting_context": {"icon": "inventory_2", "accent": "#57534E", "bg": "rgba(120,113,108,.08)", "eyebrow": "Support context"},
}

PREFERRED_SOURCES = {
    "river_core": ["waterservices.usgs.gov", "waterdata.usgs.gov", "waterqualitydata.us"],
    "pressure_core": ["City of Savannah Water Quality Reports", "epd.georgia.gov", "echo.epa.gov", "hec.usace.army.mil"],
    "reservoir_support": ["water.usace.army.mil", "nid.sec.usace.army.mil", "waterqualitydata.us"],
    "sediment_response": ["Analise_sedimentos notebook", "Master Data Clarks Hill Lake"],
}

LAYER_LABELS = {
    "river_annual_anomalies": "Annual river anomalies",
    "river_monthly_behavior": "Monthly river behavior",
    "usgs_river_daily_long": "USGS daily mainstem series",
    "wqp_river_sites_summary": "WQP river chemistry summary",
    "pressure_source_inventory": "Pressure source inventory",
    "savannah_main_treated_water_long": "Savannah Main compliance by parameter",
    "savannah_main_treated_water_summary": "Savannah Main annual compliance",
    "savannah_main_violation_details": "Savannah Main violation detail",
    "nid_system_summary": "NID structural metadata",
    "reservoir_operations_monthly": "Reservoir operations monthly",
    "usace_system_snapshot": "USACE reservoir snapshots",
    "sediment_bridge_summary": "Sediment bridge summary",
    "sediment_depositional_scores": "Depositional scores",
    "sediment_master_data": "Sediment master data",
    "collection_preflight_inventory": "Collection preflight inventory",
    "coverage_target_matrix": "Coverage target matrix",
    "context_source_inventory": "Context source inventory",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render the Savannah River HTML report from JSON context.")
    parser.add_argument("--context", type=Path, default=DEFAULT_CONTEXT, help="Structured report context JSON.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Destination HTML path.")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def esc(value: Any) -> str:
    return escape(str(value if value is not None else ""), quote=True)


def clip_text(value: Any, limit: int) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    clipped = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:")
    if not clipped:
        clipped = text[:limit].rstrip(" ,;:")
    return f"{clipped}..."


def relpath(from_dir: Path, to_path: Path) -> str:
    return os.path.relpath(to_path, from_dir).replace("\\", "/")


def csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def resolve_workspace_path(path_str: str) -> Path:
    return ROOT / Path(path_str.replace("\\", "/"))


def asset_src(output_dir: Path, filename: str) -> str:
    return relpath(output_dir, DOCS_ASSETS / filename)


def figure_exists(output_dir: Path, image_path: str) -> bool:
    candidate = Path(image_path)
    if candidate.is_absolute():
        return candidate.exists()
    return (output_dir / candidate).exists()


def infer_metric_tone(metric: dict[str, Any]) -> str:
    if metric.get("tone") in METRIC_STYLES:
        return str(metric["tone"])
    label = str(metric.get("label", "")).lower()
    if "coverage" in label or "target" in label:
        return "blue"
    if "sediment" in label or "support" in label:
        return "green"
    if "chemistry" in label or "gap" in label:
        return "red"
    return "gold"


def infer_metric_icon(metric: dict[str, Any]) -> str:
    if metric.get("icon"):
        return str(metric["icon"])
    label = str(metric.get("label", "")).lower()
    if "target" in label or "coverage" in label:
        return "show_chart"
    if "sediment" in label:
        return "experiment"
    if "chemistry" in label:
        return "science"
    if "reservoir" in label or "annex" in label:
        return "water"
    if "overlap" in label:
        return "table_chart"
    return "hub"


def render_metric_card(metric: dict[str, Any]) -> str:
    tone = infer_metric_tone(metric)
    icon = infer_metric_icon(metric)
    style = METRIC_STYLES[tone]
    note = metric.get("note", "")
    return f"""
      <div class="rounded-xl px-4 py-3" style="background: {style['bg']};">
        <span class="material-symbols-outlined text-2xl" style="color: {style['color']};">{esc(icon)}</span>
        <p class="text-white font-bold text-lg mt-1">{esc(metric.get('value', 'n/a'))}</p>
        <p class="text-white/55 text-xs">{esc(note)}</p>
      </div>
    """


def render_status_badge(status: str) -> str:
    bg, color = STATUS_TONES.get(status, STATUS_TONES["placeholder"])
    label = STATUS_LABELS.get(status, status.replace("_", " ").title())
    return (
        f'<span class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold" '
        f'style="background: {bg}; color: {color};">{esc(label)}</span>'
    )


def render_section_overview(sections: list[dict[str, Any]]) -> str:
    if not sections:
        return ""
    cards = []
    for section in sections:
        section_id = str(section.get("id", ""))
        defaults = SECTION_DEFAULTS.get(section_id, {"icon": "article", "eyebrow": "Section"})
        cards.append(
            f"""
            <article class="metric-card p-5">
              <div class="flex items-start justify-between gap-3 mb-3">
                <p class="field-label">
                  <span class="material-symbols-outlined text-sm">{esc(defaults['icon'])}</span>
                  {esc(defaults['eyebrow'])}
                </p>
                {render_status_badge(str(section.get('status', 'placeholder')))}
              </div>
              <h3 class="text-lg font-bold text-slate-800 mb-2">{esc(section.get('title', 'Untitled section'))}</h3>
              <p class="text-sm text-slate-600 leading-6">{esc(section.get('body', section.get('intro', '')))}</p>
            </article>
            """
        )
    return f"""
    <section class="mb-10">
      <div class="flex items-center justify-between gap-4 mb-4">
        <div>
          <p class="text-xs font-semibold tracking-[0.24em] uppercase mb-1" style="color: var(--gsu-gold);">Narrative contract</p>
          <h2 class="text-2xl font-bold" style="color: var(--gsu-blue);">River-first section order for the next EDA pass</h2>
        </div>
        <span class="text-xs text-slate-500">Prepared from structured context, not handwritten HTML</span>
      </div>
      <div class="gold-bar mb-6"></div>
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {''.join(cards)}
      </div>
    </section>
    """


def render_coverage_grid(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    cards = []
    for row in rows:
        status = str(row.get("coverage_status", "placeholder"))
        bg, color = STATUS_TONES.get(status, STATUS_TONES["placeholder"])
        actual_period = row.get("actual_period", "")
        gap_years = row.get("coverage_gap_years")
        gap_text = f"Gap {gap_years}y" if isinstance(gap_years, (int, float)) and gap_years > 0 else "Gap 0y"
        cards.append(
            f"""
            <article class="metric-card p-5">
              <div class="flex items-start justify-between gap-3 mb-3">
                <div>
                  <p class="field-label mb-1">
                    <span class="material-symbols-outlined text-sm">timeline</span>
                    {esc(row.get('layer', 'Coverage layer'))}
                  </p>
                  <h3 class="text-base font-bold text-slate-800">{esc(row.get('entity', 'n/a'))}</h3>
                </div>
                <span class="badge" style="background: {bg}; color: {color};">{esc(STATUS_LABELS.get(status, status))}</span>
              </div>
              <p class="text-sm text-slate-600 mb-2">{esc(row.get('source', 'Source not provided'))}</p>
              <div class="grid grid-cols-2 gap-3 text-sm">
                <div class="rounded-xl bg-slate-50 border border-slate-200 px-3 py-2">
                  <p class="field-label mb-1">Actual period</p>
                  <p class="font-semibold text-slate-800">{esc(actual_period or 'n/a')}</p>
                </div>
                <div class="rounded-xl bg-slate-50 border border-slate-200 px-3 py-2">
                  <p class="field-label mb-1">Returned vs target</p>
                  <p class="font-semibold text-slate-800">{esc(row.get('returned_years', '0'))} / {esc(row.get('target_years', '20'))} years</p>
                </div>
              </div>
              <p class="mt-3 text-xs text-slate-500">{esc(gap_text)} | {esc(row.get('coverage_kind', 'series'))}</p>
            </article>
            """
        )
    return f"""
    <section class="mb-10">
      <div class="flex items-center justify-between gap-4 mb-4">
        <div>
          <p class="text-xs font-semibold tracking-[0.24em] uppercase mb-1" style="color: var(--gsu-gold);">Coverage detail</p>
          <h2 class="text-2xl font-bold" style="color: var(--gsu-blue);">Target horizon versus returned coverage</h2>
        </div>
        <span class="text-xs text-slate-500">The 20-year target stays explicit by layer, source, and entity</span>
      </div>
      <div class="gold-bar mb-6"></div>
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {''.join(cards)}
      </div>
    </section>
    """


def figure_style(figure: dict[str, Any]) -> dict[str, str]:
    tag_name = str(figure.get("tag", "")).lower()
    tag_color = str(figure.get("tag_color", "")).lower()
    if tag_color not in TAG_STYLES:
        tag_color = TAG_COLOR_BY_NAME.get(tag_name, "blue")
    style = dict(TAG_STYLES[tag_color])
    style["icon"] = str(figure.get("icon") or ICON_BY_TAG.get(tag_name, "insights"))
    return style


def render_figure_provenance(figure: dict[str, Any], image_exists_flag: bool) -> str:
    entries = []
    image_path = figure.get("image_path", "")
    if image_path:
        entries.append(f"Image: {image_path}")
    entries.extend(str(entry) for entry in figure.get("source_refs", []) if entry)
    if not entries:
        return ""
    status_text = "Image ready" if image_exists_flag else "Image missing"
    return f"""
      <div class="px-8 pb-6">
        <p class="text-[11px] text-slate-400">
          {esc(status_text)} - {esc(str(len(entries)))} source reference(s)
        </p>
      </div>
    """


def render_figure_card(figure: dict[str, Any], output_dir: Path, reverse: bool = False) -> str:
    style = figure_style(figure)
    image_path = str(figure.get("image_path", "")).strip()
    image_ready = bool(image_path) and figure_exists(output_dir, image_path)
    if image_ready:
        image_html = f'<img src="{esc(image_path)}" alt="{esc(figure.get("title", "Figure"))}" class="fig-img">'
    else:
        image_html = (
            '<div class="placeholder-box">Missing figure image. Keep the card and update the context when the EDA exports arrive.</div>'
        )
    image_block = f"""
        <div class="{ 'lg:order-2' if reverse else '' }">
          {image_html}
        </div>
    """
    explanation_block = f"""
        <div class="space-y-5 { 'lg:order-1' if reverse else '' }">
          <div>
            <p class="field-label mb-2"><span class="material-symbols-outlined text-sm">description</span>What it shows</p>
            <p class="text-sm text-slate-600 leading-7">{esc(clip_text(figure.get('summary', 'Summary pending from the analyst handoff.'), 220))}</p>
          </div>
          <div>
            <p class="field-label mb-2"><span class="material-symbols-outlined text-sm">lightbulb</span>Why it matters</p>
            <p class="text-sm text-slate-600 leading-7">{esc(clip_text(figure.get('interpretation', 'Interpretation pending from the analyst handoff.'), 300))}</p>
          </div>
          <div class="rounded-2xl px-5 py-4" style="background: {style['callout_bg']}; border: 1px solid {style['callout_border']}33;">
            <p class="field-label mb-2" style="color: {style['callout_border']};">
              <span class="material-symbols-outlined text-sm">flag</span>
              Main takeaway
            </p>
            <p class="text-sm leading-6" style="color: {style['callout_border']};">{esc(clip_text(figure.get('highlight', 'Takeaway pending.'), 150))}</p>
          </div>
        </div>
    """
    return f"""
    <section class="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden mb-10">
      <div class="px-8 pt-7 pb-4 flex items-start gap-4">
        <div class="mt-0.5 flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center" style="background: {style['badge_bg']};">
          <span class="material-symbols-outlined text-xl" style="color: {style['badge_color']};">{esc(style['icon'])}</span>
        </div>
        <div class="flex-1">
          <div class="flex flex-wrap items-center gap-2 mb-1">
            <span class="badge" style="background: {style['badge_bg']}; color: {style['badge_color']};">{esc(figure.get('tag', 'Figure'))}</span>
            <span class="text-xs text-slate-400 font-mono">{esc(str(figure.get('id', 'FIG')).upper())}</span>
          </div>
          <h2 class="text-xl font-bold text-slate-800">{esc(figure.get('title', 'Untitled figure'))}</h2>
        </div>
      </div>
      <div class="px-8 pb-2"><div class="gold-bar"></div></div>
      <div class="px-8 py-6 grid gap-6 lg:grid-cols-[minmax(0,1.75fr)_minmax(18rem,1fr)] items-start">
        {image_block}
        {explanation_block}
      </div>
      {render_figure_provenance(figure, image_ready)}
    </section>
    """


def render_grouped_figures(figures: list[dict[str, Any]], sections: list[dict[str, Any]], output_dir: Path) -> str:
    if not figures:
        return ""
    cards = []
    previous_section = ""
    for index, figure in enumerate(figures):
        section_id = str(figure.get("section", "")).strip()
        if section_id and section_id != previous_section:
            defaults = SECTION_DEFAULTS.get(section_id, {"eyebrow": "Figures"})
            cards.append(
                f"""
                <div class="mb-5">
                  <p class="text-xs font-semibold tracking-[0.24em] uppercase mb-2" style="color: var(--gsu-gold);">{esc(defaults['eyebrow'])}</p>
                  <div class="gold-bar"></div>
                </div>
                """
            )
            previous_section = section_id
        cards.append(render_figure_card(figure, output_dir, reverse=bool(index % 2)))
    return "".join(cards)


def summarize_domain_cards(payload: dict[str, Any]) -> list[dict[str, Any]]:
    contract = payload.get("domain_contract", {})
    domain_labels = {
        str(item.get("domain_id")): str(item.get("domain_label"))
        for item in contract.get("domains", [])
        if item.get("domain_id")
    }
    registry_path = ROOT / "data" / "analytic" / "clarks_hill" / "domain_registry.csv"
    for artifact in contract.get("artifacts", []):
        artifact_path = resolve_workspace_path(str(artifact))
        if artifact_path.name == "domain_registry.csv" and "analytic" in artifact_path.parts:
            registry_path = artifact_path
            break
    source_inventory_path = ROOT / "data" / "staging" / "clarks_hill" / "context_source_inventory.csv"
    registry_rows = csv_rows(registry_path)
    source_rows = csv_rows(source_inventory_path)
    rows_by_domain: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in registry_rows:
        rows_by_domain[str(row.get("domain_id", ""))].append(row)
    sources_by_domain: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in source_rows:
        sources_by_domain[str(row.get("analytical_role", ""))].append(row)

    sediment_sources = [
        "Analise_sedimentos notebook",
        "Master Data Clarks Hill Lake",
    ]
    card_order = ["river_core", "pressure_core", "reservoir_support", "sediment_response"]
    cards: list[dict[str, Any]] = []

    for domain_id in card_order:
        style = DOMAIN_STYLES.get(domain_id, DOMAIN_STYLES["supporting_context"])
        domain_rows = rows_by_domain.get(domain_id, [])
        if not domain_rows:
            continue
        domain_rows.sort(
            key=lambda row: (
                0 if row.get("readiness") == "ready" else 1,
                0 if row.get("crossing_priority") == "primary" else 1,
                str(row.get("layer_name", "")),
            )
        )
        available = []
        for row in domain_rows[:3]:
            period_bits = []
            if row.get("first_year") and row.get("last_year"):
                period_bits.append(f"{row['first_year']}-{row['last_year']}")
            elif row.get("record_count"):
                period_bits.append("snapshot")
            count_bit = ""
            if row.get("record_count"):
                count_bit = f"{row['record_count']} rows"
            detail = " - ".join(bit for bit in [*period_bits, count_bit] if bit)
            layer_label = LAYER_LABELS.get(str(row.get("layer_name", "")), str(row.get("layer_name", "")).replace("_", " ").title())
            if detail:
                available.append(f"{layer_label}: {detail}")
            else:
                available.append(layer_label)

        ready_rows = [row for row in domain_rows if row.get("readiness") == "ready"]
        numeric_years = []
        for row in ready_rows or domain_rows:
            try:
                if row.get("first_year"):
                    numeric_years.append(int(float(row["first_year"])))
                if row.get("last_year"):
                    numeric_years.append(int(float(row["last_year"])))
            except ValueError:
                continue
        if numeric_years:
            coverage = f"{min(numeric_years)}-{max(numeric_years)}"
        else:
            coverage = "Local campaign / snapshot"

        preferred_sources = list(PREFERRED_SOURCES.get(domain_id, []))
        source_names = []
        seen = set()
        for source_name in preferred_sources:
            if source_name and source_name not in seen:
                source_names.append(source_name)
                seen.add(source_name)
        for row in sources_by_domain.get(domain_id, []):
            source_name = str(row.get("source_name", "")).strip()
            if not source_name or source_name in seen:
                continue
            seen.add(source_name)
            source_names.append(source_name)
            if len(source_names) >= 4:
                break
        note = ""
        for row in domain_rows:
            note = str(row.get("coverage_note", "")).strip()
            if note:
                break
        cards.append(
            {
                "domain_id": domain_id,
                "label": domain_labels.get(domain_id, domain_id.replace("_", " ").title()),
                "coverage": coverage,
                "available": available,
                "sources": source_names,
                "note": clip_text(note, 150),
                "icon": style["icon"],
                "accent": style["accent"],
                "bg": style["bg"],
                "eyebrow": style["eyebrow"],
            }
        )
    return cards


def render_domain_intro(cards: list[dict[str, Any]]) -> str:
    if not cards:
        return ""
    rendered = []
    for card in cards:
        rendered.append(
            f"""
            <article class="metric-card p-5">
              <div class="flex items-start gap-3 mb-3">
                <div class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" style="background: {card['bg']};">
                  <span class="material-symbols-outlined text-xl" style="color: {card['accent']};">{esc(card['icon'])}</span>
                </div>
                <div>
                  <p class="text-[11px] font-semibold tracking-[0.20em] uppercase mb-1" style="color: {card['accent']};">{esc(card['eyebrow'])}</p>
                  <h3 class="text-lg font-bold text-slate-800">{esc(card['label'])}</h3>
                  <p class="text-xs text-slate-500 mt-1">Available window: {esc(card['coverage'])}</p>
                </div>
              </div>
              <div class="space-y-3">
                <div>
                  <p class="field-label mb-2"><span class="material-symbols-outlined text-sm">dataset</span>Available data</p>
                  <ul class="space-y-1.5 text-sm text-slate-600 leading-6">
                    {''.join(f'<li>{esc(item)}</li>' for item in card['available'])}
                  </ul>
                </div>
                <div>
                  <p class="field-label mb-2"><span class="material-symbols-outlined text-sm">link</span>Sources</p>
                  <p class="text-sm text-slate-600 leading-6">{esc(', '.join(card['sources']) if card['sources'] else 'Local structured layer')}</p>
                </div>
                <p class="text-xs text-slate-500 leading-6">{esc(card['note'])}</p>
              </div>
            </article>
            """
        )
    return f"""
    <section class="mb-10">
      <div class="flex items-center justify-between gap-4 mb-4">
        <div>
          <p class="text-xs font-semibold tracking-[0.24em] uppercase mb-1" style="color: var(--gsu-gold);">Available data</p>
          <h2 class="text-2xl font-bold" style="color: var(--gsu-blue);">What is already available by analytical domain</h2>
        </div>
        <span class="text-xs text-slate-500">Compact source map before the figure sequence starts</span>
      </div>
      <div class="gold-bar mb-6"></div>
      <div class="grid gap-4 md:grid-cols-2">
        {''.join(rendered)}
      </div>
    </section>
    """


def render_list_block(title: str, icon: str, items: list[str], tone: str = "#0F7B5F") -> str:
    if not items:
        return ""
    return f"""
      <div class="rounded-2xl border border-slate-200 bg-white px-5 py-4">
        <p class="field-label mb-3" style="color: {tone};">
          <span class="material-symbols-outlined text-sm">{esc(icon)}</span>
          {esc(title)}
        </p>
        <ul class="space-y-2 text-sm text-slate-600 leading-6">
          {''.join(f'<li>{esc(item)}</li>' for item in items)}
        </ul>
      </div>
    """


def render_sources_block(payload: dict[str, Any]) -> str:
    sources = payload.get("sources", {})
    source_note = payload.get("source_note", {})
    artifacts = [str(item) for item in source_note.get("artifacts", []) if item]
    narrative_rules = [str(item) for item in payload.get("narrative_rules", []) if item]
    source_lines = []
    for key, value in sources.items():
        if value:
            source_lines.append(f"{key}: {value}")
    if not artifacts and not source_lines and not narrative_rules and not source_note.get("text"):
        return ""
    return f"""
    <section class="metric-card p-8 mb-10">
      <div class="flex items-start gap-4">
        <div class="w-12 h-12 rounded-full flex items-center justify-center text-white flex-shrink-0" style="background: var(--gsu-blue);">
          <span class="material-symbols-outlined text-2xl">link</span>
        </div>
        <div class="flex-1">
          <p class="text-xs font-semibold tracking-[0.24em] uppercase mb-1" style="color: var(--gsu-gold);">Methods and provenance</p>
          <h2 class="text-2xl font-bold mb-3" style="color: var(--gsu-blue);">Where images, metrics, and synthesized text come from</h2>
          <p class="text-sm text-slate-700 leading-7 mb-4">{esc(source_note.get('text', 'This report should only synthesize structured context and local figure exports with traceable file paths.'))}</p>
          <div class="grid gap-4 lg:grid-cols-2">
            {render_list_block('Narrative rules', 'policy', narrative_rules)}
            {render_list_block('Structured sources', 'dataset', source_lines, '#075985')}
            {render_list_block('Artifact references', 'folder_open', artifacts, '#57534E')}
          </div>
        </div>
      </div>
    </section>
    """


def render_caveats(payload: dict[str, Any]) -> str:
    caveats = [str(item) for item in payload.get("current_caveats", []) if item]
    sediment_summary = payload.get("sediment_summary", {})
    sediment_caveat = sediment_summary.get("caveat")
    if sediment_caveat:
        caveats.append(str(sediment_caveat))
    coverage_notes = [
        str(item) for item in payload.get("coverage_summary", {}).get("notes", []) if item
    ]
    for note in coverage_notes:
        if note not in caveats:
            caveats.append(note)
    if not caveats:
        return ""
    return f"""
    <section class="metric-card p-8">
      <div class="flex items-start gap-4">
        <div class="w-12 h-12 rounded-full flex items-center justify-center text-white flex-shrink-0" style="background: var(--gsu-blue);">
          <span class="material-symbols-outlined text-2xl">pending</span>
        </div>
        <div class="flex-1">
          <p class="text-xs font-semibold tracking-[0.24em] uppercase mb-1" style="color: var(--gsu-gold);">Current caveats</p>
          <h2 class="text-2xl font-bold mb-3" style="color: var(--gsu-blue);">What the next EDA pass still needs to keep explicit</h2>
          <ul class="space-y-2 text-sm text-slate-600 leading-6">
            {''.join(f'<li>- {esc(item)}</li>' for item in caveats)}
          </ul>
        </div>
      </div>
    </section>
    """


def build_html(payload: dict[str, Any], output_path: Path) -> str:
    output_dir = output_path.parent
    metrics = payload.get("metrics", [])
    sections = payload.get("sections", [])
    figures = payload.get("figures", [])
    coverage_layers = payload.get("coverage_layers", [])
    metadata = payload.get("metadata", {})
    coverage_summary = payload.get("coverage_summary", {})
    sources = payload.get("sources", {})
    sediment_summary = payload.get("sediment_summary", {})

    hero_metrics = metrics[:4]
    metrics_html = "".join(render_metric_card(metric) for metric in hero_metrics)
    domain_intro_html = render_domain_intro(summarize_domain_cards(payload))
    figures_html = render_grouped_figures(figures, sections, output_dir)

    logo_100k = asset_src(output_dir, "100K.webp")
    logo_gsu = asset_src(output_dir, "Georgia.png")
    logo_senai = asset_src(output_dir, "SENAI.svg")
    date_label = metadata.get("date_label") or datetime.now().strftime("%B %Y")
    status_badge = metadata.get("status_badge") or "River-first + coverage-explicit"
    run_summary = []
    if sources.get("river_collection_run"):
        run_summary.append(f"River: {sources['river_collection_run']}")
    if sources.get("reservoir_annex_run"):
        run_summary.append(f"Annex: {sources['reservoir_annex_run']}")

    summary_text = clip_text(
        payload.get("context_summary", "Structured context pending from the next EDA handoff."),
        300,
    )
    focus_text = clip_text(
        "The page is organized as a visual reading of river behavior first, then lower-river quality, reservoir regulation, and the sediment response that Thurmond still needs to explain.",
        220,
    )
    coverage_rule = clip_text(
        coverage_summary.get("rule", "Always keep the target horizon and the real returned coverage separate."),
        180,
    )
    coverage_actual = clip_text(
        coverage_summary.get("actual_summary", "Coverage detail will be filled when the analyst exports the next structured context."),
        180,
    )
    figure_count = len(figures)
    run_line = " | ".join(run_summary) if run_summary else "Runs pending"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(payload.get('report_title', 'Savannah River Mainstem'))} - EDA Report</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Bitter:wght@400;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
<style>
:root {{
  --gsu-blue: #011E42;
  --gsu-gold: #87714D;
  --gsu-gold-light: #C4A86C;
  --slate-bg: #f8fafc;
}}
body {{ font-family: 'Inter', sans-serif; background: var(--slate-bg); color: #0f172a; }}
h1, h2, h3 {{ font-family: 'Bitter', serif; }}
.material-symbols-outlined {{
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  vertical-align: middle;
}}
.gold-bar {{
  height: 3px;
  background: linear-gradient(90deg, var(--gsu-gold), var(--gsu-gold-light), var(--gsu-gold));
  border-radius: 999px;
}}
.badge {{
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}}
.field-label {{
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}}
.metric-card {{
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  background: white;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
}}
.logo-chip {{
  background: white;
  border-radius: 0.75rem;
  padding: 0.35rem 0.6rem;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
}}
.fig-img {{
  width: 100%;
  border-radius: 0.75rem;
  border: 1px solid #e2e8f0;
  background: white;
}}
.placeholder-box {{
  width: 100%;
  min-height: 16rem;
  border-radius: 0.75rem;
  border: 1px dashed #cbd5e1;
  background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%);
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 2rem;
  font-size: 0.95rem;
  line-height: 1.7;
}}
</style>
</head>
<body class="min-h-screen">

<header class="sticky top-0 z-50 shadow-lg" style="background: var(--gsu-blue);">
  <div class="max-w-6xl mx-auto px-6 py-3 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
    <div class="flex flex-wrap items-center gap-3">
      <img src="{esc(logo_100k)}" alt="Project 100K" class="h-9 object-contain">
      <div class="w-px h-7 bg-white/20 hidden sm:block"></div>
      <div class="logo-chip">
        <img src="{esc(logo_gsu)}" alt="Georgia university logo" class="h-7 object-contain">
      </div>
      <div class="logo-chip">
        <img src="{esc(logo_senai)}" alt="SENAI logo" class="h-6 object-contain">
      </div>
    </div>
    <div class="flex items-center gap-3 text-xs">
      <span class="hidden sm:inline-block text-white/40">Project FREnTE - EDA</span>
      <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full font-semibold"
            style="background: rgba(134,197,63,.15); color: #86C53F; border: 1px solid rgba(134,197,63,.25);">
        <span class="w-1.5 h-1.5 rounded-full inline-block" style="background: #86C53F;"></span>
        {esc(status_badge)} - {esc(date_label)}
      </span>
    </div>
  </div>
</header>

<section style="background: var(--gsu-blue);" class="pb-10 pt-8">
  <div class="max-w-6xl mx-auto px-6">
    <p class="text-xs font-semibold tracking-[0.24em] uppercase mb-2" style="color: var(--gsu-gold);">
      Exploratory Data Report - Savannah River Mainstem
    </p>
    <h1 class="text-3xl lg:text-4xl font-bold text-white leading-tight mb-3">
      {esc(payload.get('report_title', 'Savannah River Mainstem'))}
      <span class="block mt-1" style="color: var(--gsu-gold-light);">{esc(payload.get('report_subtitle', 'River-first contextual EDA'))}</span>
    </h1>
    <p class="text-white/75 text-sm lg:text-base max-w-4xl leading-relaxed mb-5">
      {esc(summary_text)}
    </p>
    <div class="flex flex-wrap gap-2 mb-5 text-[11px]">
      <span class="badge" style="background: rgba(255,255,255,.10); color: #E2E8F0;">{esc(str(figure_count))} figures</span>
      <span class="badge" style="background: rgba(255,255,255,.10); color: #E2E8F0;">River-first reading</span>
      <span class="badge" style="background: rgba(255,255,255,.10); color: #E2E8F0;">Reservoirs as annex</span>
      <span class="badge" style="background: rgba(255,255,255,.10); color: #E2E8F0;">Sediment bridge at the end</span>
    </div>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      {metrics_html}
    </div>
  </div>
</section>

<div class="max-w-6xl mx-auto px-6 py-4">
  <div class="gold-bar"></div>
</div>

<main class="max-w-6xl mx-auto px-6 py-6">

  <section class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(18rem,22rem)] mb-8">
    <article class="metric-card p-6">
      <p class="field-label mb-2">
        <span class="material-symbols-outlined text-sm">visibility</span>
        How to read this page
      </p>
      <p class="text-sm text-slate-700 leading-7">{esc(focus_text)}</p>
    </article>
    <article class="metric-card p-6">
      <p class="field-label mb-2">
        <span class="material-symbols-outlined text-sm">timeline</span>
        Coverage note
      </p>
      <p class="text-sm text-slate-700 leading-7">{esc(coverage_rule)}</p>
      <p class="text-xs text-slate-500 leading-6 mt-2">{esc(coverage_actual)}</p>
      <p class="text-[11px] text-slate-400 font-mono mt-3">{esc(run_line)}</p>
    </article>
  </section>

  {domain_intro_html}

  {figures_html}

</main>

<footer class="mt-12 border-t border-slate-200 py-6">
  <div class="max-w-6xl mx-auto px-6 text-xs text-slate-400 flex flex-col sm:flex-row gap-2 sm:items-center sm:justify-between">
    <span>Project FREnTE - GSU / SENAI - 2026</span>
    <span>{esc(' | '.join(run_summary) if run_summary else 'Awaiting next Savannah River EDA handoff')}</span>
  </div>
</footer>

</body>
</html>
"""


def main() -> None:
    args = parse_args()
    payload = load_json(args.context)
    ensure_parent(args.output)
    html = build_html(payload, args.output)
    args.output.write_text(html, encoding="utf-8")
    print(f"Context loaded from: {args.context}")
    print(f"HTML written to: {args.output}")


if __name__ == "__main__":
    main()
