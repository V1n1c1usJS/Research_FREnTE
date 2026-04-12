"""
Generate behavior-first SVG figures for the Savannah River / Clarks Hill report.
12 figures total — expanded from 8 to include reservoir WQP activity, system structure,
full sediment geochemistry (Mn, water%), cross-layer coverage, and spatial sediment map.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[2]
STAGING_DIR = ROOT / "data" / "staging" / "clarks_hill"
EDA_FIG_DIR = Path(__file__).resolve().parent / "figures"
DOCS_FIG_DIR = ROOT / "docs" / "clarks-hill" / "figures"

BLUE = "#011E42"
GOLD = "#87714D"
GOLD_LIGHT = "#C4A86C"
TEAL = "#0F7B5F"
ORANGE = "#C27803"
RED = "#B91C1C"
SLATE = "#64748B"
SLATE_LIGHT = "#E2E8F0"
BACKGROUND = "#F8FAFC"
WHITE = "#FFFFFF"
RIVER_BLUE = "#0B5CAD"
RIVER_PALE = "#DBEAFE"
EMERALD_PALE = "#D1FAE5"
PURPLE = "#6D28D9"
CYAN = "#0891B2"
AMBER = "#D97706"
PINK = "#DB2777"
LIME = "#4D7C0F"

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
RESERVOIR_ORDER = ["Hartwell", "Russell", "Thurmond"]
RESERVOIR_COLORS = {"Hartwell": TEAL, "Russell": PURPLE, "Thurmond": ORANGE}


# ─── I/O helpers ──────────────────────────────────────────────────────────────

def ensure_dirs() -> None:
    EDA_FIG_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_FIG_DIR.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def save_svg(name: str, svg: str) -> None:
    for directory in (EDA_FIG_DIR, DOCS_FIG_DIR):
        (directory / name).write_text(svg, encoding="utf-8")


# ─── SVG primitives ───────────────────────────────────────────────────────────

def svg_header(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="Savannah River analytical figure">'
    )


def text(x: float, y: float, content: str, size: int = 14, weight: str = "400",
         fill: str = SLATE, anchor: str = "start") -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="Inter, Arial, sans-serif" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(str(content))}</text>'
    )


def rect(x: float, y: float, width: float, height: float, fill: str,
         stroke: str = "none", rx: int = 12) -> str:
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{rx}" fill="{fill}" stroke="{stroke}" />'


def line(x1: float, y1: float, x2: float, y2: float, stroke: str,
         width: int = 2, dash: str = "") -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{width}"{dash_attr} />'


def polyline(points: list[tuple[float, float]], stroke: str, width: int = 2,
             fill: str = "none", opacity: float = 1.0) -> str:
    serialized = " ".join(f"{x},{y}" for x, y in points)
    return f'<polyline points="{serialized}" stroke="{stroke}" stroke-width="{width}" fill="{fill}" opacity="{opacity}" />'


def polygon(points: list[tuple[float, float]], fill: str, opacity: float = 0.2) -> str:
    serialized = " ".join(f"{x},{y}" for x, y in points)
    return f'<polygon points="{serialized}" fill="{fill}" opacity="{opacity}" />'


def circle(cx: float, cy: float, radius: float, fill: str, stroke: str = "none",
           stroke_width: float = 0, opacity: float = 1.0) -> str:
    return (f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{stroke_width}" opacity="{opacity}" />')


# ─── Math helpers ─────────────────────────────────────────────────────────────

def scale(value: float, domain_min: float, domain_max: float,
          range_min: float, range_max: float) -> float:
    if domain_max == domain_min:
        return (range_min + range_max) / 2.0
    ratio = (value - domain_min) / (domain_max - domain_min)
    return range_min + ratio * (range_max - range_min)


def to_float(value: str) -> float | None:
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return None


def nice_domain(values: list[float], pad_ratio: float = 0.08) -> tuple[float, float]:
    if not values:
        return (0.0, 1.0)
    low = min(values)
    high = max(values)
    if low == high:
        pad = abs(low) * 0.05 or 1.0
        return (low - pad, high + pad)
    pad = (high - low) * pad_ratio
    return (low - pad, high + pad)


def format_number(value: float, decimals: int = 1) -> str:
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    return f"{value:.{decimals}f}"


def month_sort_key(value: str) -> tuple[int, int]:
    return (int(value[:4]), int(value[5:7]))


def pearson_r(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    dx = math.sqrt(sum((a - mx) ** 2 for a in xs))
    dy = math.sqrt(sum((b - my) ** 2 for b in ys))
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)


# ─── Data loaders ─────────────────────────────────────────────────────────────

def load_monthly_behavior() -> list[dict[str, str]]:
    return read_csv(STAGING_DIR / "river_monthly_behavior.csv")


def load_climatology() -> list[dict[str, str]]:
    return read_csv(STAGING_DIR / "river_monthly_climatology.csv")


def load_annual_anomalies() -> list[dict[str, str]]:
    return read_csv(STAGING_DIR / "river_annual_anomalies.csv")


def load_correlations() -> list[dict[str, str]]:
    return read_csv(STAGING_DIR / "river_quality_flow_correlations.csv")


def load_bridge() -> list[dict[str, str]]:
    return read_csv(STAGING_DIR / "river_reservoir_bridge.csv")


def load_sediment_master() -> list[dict[str, str]]:
    return read_csv(STAGING_DIR / "sediment_master_data.csv")


def load_sediment_scores() -> list[dict[str, str]]:
    return read_csv(STAGING_DIR / "sediment_depositional_scores.csv")


def load_sediment_pairwise() -> list[dict[str, str]]:
    return read_csv(STAGING_DIR / "sediment_pairwise_relations.csv")


def load_wqp_system_yearly() -> list[dict[str, str]]:
    return read_csv(STAGING_DIR / "wqp_system_yearly_counts.csv")


def load_wqp_system_summary() -> list[dict[str, str]]:
    return read_csv(STAGING_DIR / "wqp_system_summary.csv")


def load_nid_summary() -> list[dict[str, str]]:
    return read_csv(STAGING_DIR / "nid_system_summary.csv")


def load_usace_snapshot() -> list[dict[str, str]]:
    return read_csv(STAGING_DIR / "usace_system_snapshot.csv")


def load_coverage_matrix() -> list[dict[str, str]]:
    return read_csv(STAGING_DIR / "coverage_target_matrix.csv")


def load_crosslayer_matrix() -> list[dict[str, str]]:
    return read_csv(STAGING_DIR / "crosslayer_parameter_matrix.csv")


def load_reservoir_operations_monthly() -> list[dict[str, str]]:
    return read_csv(STAGING_DIR / "reservoir_operations_monthly.csv")


def load_reservoir_operation_summary() -> list[dict[str, str]]:
    return read_csv(STAGING_DIR / "reservoir_operations_summary.csv")


def load_savannah_main_summary() -> list[dict[str, str]]:
    return read_csv(STAGING_DIR / "savannah_main_treated_water_summary.csv")


def load_savannah_main_long() -> list[dict[str, str]]:
    return read_csv(STAGING_DIR / "savannah_main_treated_water_long.csv")


# ─── Series extractors ────────────────────────────────────────────────────────

def series_from_monthly(rows: list[dict[str, str]], series_slug: str) -> list[dict]:
    selected = [row for row in rows if row["series_slug"] == series_slug]
    selected.sort(key=lambda row: month_sort_key(row["ano_mes"]))
    return [
        {"ano_mes": row["ano_mes"], "year": int(row["year"]),
         "month": int(row["month"]), "value": float(row["monthly_mean"]),
         "unit": row["unit"], "series_label": row["series_label"]}
        for row in selected
    ]


def series_from_climatology(rows: list[dict[str, str]], series_slug: str) -> list[dict]:
    selected = [row for row in rows if row["series_slug"] == series_slug]
    selected.sort(key=lambda row: int(row["month"]))
    return [
        {"month": int(row["month"]), "value": float(row["climatology_mean"]),
         "unit": row["unit"], "series_label": row["series_label"]}
        for row in selected
    ]


def annual_series(rows: list[dict[str, str]], series_slug: str) -> list[dict]:
    selected = [row for row in rows if row["series_slug"] == series_slug]
    selected.sort(key=lambda row: int(row["year"]))
    return [
        {"year": int(row["year"]), "annual_mean": float(row["annual_mean"]),
         "zscore": float(row["zscore"])}
        for row in selected
    ]


def reservoir_series(rows: list[dict[str, str]], reservoir: str, metric_slug: str) -> list[dict]:
    selected = [row for row in rows if row["reservoir"] == reservoir and row["metric_slug"] == metric_slug]
    selected.sort(key=lambda row: month_sort_key(row["ano_mes"]))
    return [
        {
            "reservoir": row["reservoir"],
            "metric_slug": row["metric_slug"],
            "metric_label": row["metric_label"],
            "ano_mes": row["ano_mes"],
            "year": int(row["year"]),
            "month": int(row["month"]),
            "value": float(row["monthly_mean"]),
            "unit": row["unit"],
        }
        for row in selected
    ]


def rolling_mean(series: list[dict], window: int = 12, min_periods: int = 6) -> list[dict]:
    values = [float(item["value"]) for item in series]
    rolled: list[dict] = []
    for index, item in enumerate(series):
        start = max(0, index - window + 1)
        bucket = values[start:index + 1]
        if len(bucket) < min_periods:
            continue
        rolled.append({**item, "value": sum(bucket) / len(bucket)})
    return rolled


def series_year_window(series: list[dict]) -> str:
    if not series:
        return ""
    return f"{series[0]['ano_mes'][:4]}-{series[-1]['ano_mes'][:4]}"


# ─── Draw helpers ─────────────────────────────────────────────────────────────

def x_lookup_from_months(months: list[str], x0: float, width: float) -> dict[str, float]:
    if len(months) <= 1:
        return {months[0]: x0 + width / 2.0} if months else {}
    return {month: x0 + width * i / (len(months) - 1) for i, month in enumerate(months)}


def draw_time_axis(pieces: list[str], months: list[str], x_map: dict[str, float], y: float) -> None:
    pieces.append(line(min(x_map.values()), y, max(x_map.values()), y, SLATE_LIGHT, 2))
    seen_years: set[int] = set()
    for month in months:
        year = int(month[:4])
        current_month = int(month[5:7])
        if current_month == 1 or month == months[0] or month == months[-1]:
            if year in seen_years and month not in {months[0], months[-1]}:
                continue
            seen_years.add(year)
            x = x_map[month]
            pieces.append(line(x, y - 6, x, y + 6, SLATE_LIGHT, 1))
            pieces.append(text(x, y + 22, str(year), 11, "500", SLATE, "middle"))


def draw_y_guides(pieces: list[str], x0: float, width: float, y0: float,
                  height: float, minimum: float, maximum: float) -> None:
    for ratio in (0.0, 0.5, 1.0):
        y = y0 + height * ratio
        pieces.append(line(x0, y, x0 + width, y, SLATE_LIGHT, 1, "4 6"))
    pieces.append(text(x0 - 6, y0 + 6, format_number(maximum), 11, "500", SLATE, "end"))
    pieces.append(text(x0 - 6, y0 + height / 2 + 4, format_number((minimum + maximum) / 2.0), 11, "500", SLATE, "end"))
    pieces.append(text(x0 - 6, y0 + height + 4, format_number(minimum), 11, "500", SLATE, "end"))


def draw_series_line(pieces: list[str], series: list[dict], months: list[str],
                     x0: float, y0: float, width: float, height: float,
                     color: str, line_width: int = 3, fill_area: bool = False) -> tuple[float, float]:
    values = [float(item["value"]) for item in series]
    minimum, maximum = nice_domain(values)
    x_map = x_lookup_from_months(months, x0, width)
    points = [
        (x_map[item["ano_mes"]], scale(float(item["value"]), minimum, maximum, y0 + height, y0))
        for item in series if item["ano_mes"] in x_map
    ]
    draw_y_guides(pieces, x0, width, y0, height, minimum, maximum)
    if fill_area and points:
        pieces.append(polygon(
            [(points[0][0], y0 + height)] + points + [(points[-1][0], y0 + height)],
            color, 0.12,
        ))
    if points:
        pieces.append(polyline(points, color, line_width))
    draw_time_axis(pieces, months, x_map, y0 + height)
    return (minimum, maximum)


def draw_month_line(pieces: list[str], series: list[dict], x0: float, y0: float,
                    width: float, height: float, color: str) -> tuple[float, float]:
    values = [float(item["value"]) for item in series]
    minimum, maximum = nice_domain(values)
    points = [
        (x0 + width * (int(item["month"]) - 1) / 11.0,
         scale(float(item["value"]), minimum, maximum, y0 + height, y0))
        for item in series
    ]
    draw_y_guides(pieces, x0, width, y0, height, minimum, maximum)
    pieces.append(polyline(points, color, 3))
    for i, label in enumerate(MONTH_LABELS):
        x = x0 + width * i / 11.0
        pieces.append(line(x, y0 + height - 4, x, y0 + height + 4, SLATE_LIGHT, 1))
        pieces.append(text(x, y0 + height + 22, label, 11, "500", SLATE, "middle"))
    return (minimum, maximum)


def draw_badge(pieces: list[str], x: float, y: float, label: str,
               tone_fill: str, tone_text: str) -> None:
    pieces.append(rect(x, y, max(72, len(label) * 7.4), 24, tone_fill, "none", 12))
    pieces.append(text(x + 10, y + 17, label, 11, "700", tone_text))


def draw_line_legend(
    pieces: list[str],
    items: list[tuple[str, str, int, float]],
    x: float,
    y: float,
) -> None:
    current_x = x
    for label, color, width, opacity in items:
        pieces.append(line(current_x, y - 5, current_x + 24, y - 5, color, width))
        if opacity < 1:
            pieces[-1] = pieces[-1].replace("/>", f' opacity="{opacity}" />')
        pieces.append(text(current_x + 30, y, label, 11, "500", SLATE))
        current_x += 32 + len(label) * 6.8


def draw_series_with_trend(
    pieces: list[str],
    series: list[dict],
    x0: float,
    y0: float,
    width: float,
    height: float,
    color: str,
    trend_color: str | None = None,
    fill_area: bool = True,
) -> tuple[float, float]:
    if not series:
        return (0.0, 1.0)
    months = [item["ano_mes"] for item in series]
    trend = rolling_mean(series)
    values = [float(item["value"]) for item in series] + [float(item["value"]) for item in trend]
    minimum, maximum = nice_domain(values)
    x_map = x_lookup_from_months(months, x0, width)
    raw_points = [
        (x_map[item["ano_mes"]], scale(float(item["value"]), minimum, maximum, y0 + height, y0))
        for item in series if item["ano_mes"] in x_map
    ]
    trend_points = [
        (x_map[item["ano_mes"]], scale(float(item["value"]), minimum, maximum, y0 + height, y0))
        for item in trend if item["ano_mes"] in x_map
    ]
    draw_y_guides(pieces, x0, width, y0, height, minimum, maximum)
    if fill_area and raw_points:
        pieces.append(polygon(
            [(raw_points[0][0], y0 + height)] + raw_points + [(raw_points[-1][0], y0 + height)],
            color,
            0.10,
        ))
    if raw_points:
        pieces.append(polyline(raw_points, color, 2, opacity=0.40))
    if trend_points:
        pieces.append(polyline(trend_points, trend_color or color, 4))
    draw_time_axis(pieces, months, x_map, y0 + height)
    return (minimum, maximum)


def draw_stacked_bar_triplet(
    pieces: list[str],
    x: float,
    y: float,
    width: float,
    height: float,
    values: list[tuple[str, float, str]],
    label: str,
) -> None:
    total = max(sum(max(value, 0.0) for _, value, _ in values), 1.0)
    cursor_x = x
    for _, value, color in values:
        bar_width = width * max(value, 0.0) / total
        pieces.append(rect(cursor_x, y, bar_width, height, color, "none", 10))
        cursor_x += bar_width
    pieces.append(text(x, y - 8, label, 12, "600", SLATE))


def draw_scatter_panel(pieces: list[str], points: list[tuple[float, float]],
                       x0: float, y0: float, width: float, height: float,
                       point_color: str, line_color: str, x_label: str, y_label: str,
                       correlation: float | None = None) -> None:
    if not points:
        pieces.append(text(x0 + width / 2, y0 + height / 2, "No data", 14, "600", SLATE, "middle"))
        return
    x_values = [p[0] for p in points]
    y_values = [p[1] for p in points]
    min_x, max_x = nice_domain(x_values)
    min_y, max_y = nice_domain(y_values)
    draw_y_guides(pieces, x0, width, y0, height, min_y, max_y)
    pieces.append(line(x0, y0, x0, y0 + height, SLATE_LIGHT, 2))
    pieces.append(line(x0, y0 + height, x0 + width, y0 + height, SLATE_LIGHT, 2))
    for raw_x, raw_y in points:
        cx = scale(raw_x, min_x, max_x, x0, x0 + width)
        cy = scale(raw_y, min_y, max_y, y0 + height, y0)
        pieces.append(circle(cx, cy, 4.5, point_color, WHITE, 1, 0.75))
    mean_x = sum(x_values) / len(x_values)
    mean_y = sum(y_values) / len(y_values)
    sum_xx = sum((v - mean_x) ** 2 for v in x_values)
    sum_xy = sum((a - mean_x) * (b - mean_y) for a, b in points)
    if sum_xx:
        slope = sum_xy / sum_xx
        intercept = mean_y - slope * mean_x
        sx = scale(min_x, min_x, max_x, x0, x0 + width)
        ex = scale(max_x, min_x, max_x, x0, x0 + width)
        sy = scale(slope * min_x + intercept, min_y, max_y, y0 + height, y0)
        ey = scale(slope * max_x + intercept, min_y, max_y, y0 + height, y0)
        pieces.append(line(sx, sy, ex, ey, line_color, 2, "6 3"))
    r = correlation if correlation is not None else (pearson_r(x_values, y_values) if len(x_values) >= 2 else 0.0)
    pieces.append(text(x0 + width / 2, y0 + height + 42, x_label, 12, "600", SLATE, "middle"))
    pieces.append(text(x0 + 6, y0 - 14, y_label, 12, "600", SLATE))
    r_color = TEAL if r > 0 else RED
    pieces.append(text(x0 + width - 6, y0 + 18, f"r = {r:.2f}", 13, "700", r_color, "end"))
    pieces.append(text(x0 + 6, y0 + 18, f"n={len(points)}", 11, "500", SLATE))


# ─── Figure 1 — 20-year mainstem hydrograph ───────────────────────────────────

def fig1_river_mainstem_hydrograph(monthly_rows: list[dict], annual_rows: list[dict]) -> None:
    flow = series_from_monthly(monthly_rows, "augusta_flow_cfs")
    stage = series_from_monthly(monthly_rows, "augusta_stage_ft")
    annual = annual_series(annual_rows, "augusta_flow_cfs")
    months = [item["ano_mes"] for item in flow]
    width, height = 1400, 980
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 72, "Savannah River at Augusta: 20-year hydrograph and annual flow anomaly", 32, "700", BLUE))
    pieces.append(text(70, 102, "River-first anchor: monthly discharge and stage establish the mainstem signal before any reservoir or sediment interpretation.", 15, "400", SLATE))

    pieces.append(rect(70, 130, 1260, 760, WHITE, SLATE_LIGHT, 20))
    pieces.append(text(100, 166, "Monthly discharge (ft³/s)", 18, "700", BLUE))
    pieces.append(text(100, 438, "Monthly stage (ft)", 18, "700", BLUE))
    pieces.append(text(100, 710, "Annual discharge anomaly (z-score vs 2006–2026 mean)", 18, "700", BLUE))
    draw_badge(pieces, 1060, 138, f"{flow[0]['ano_mes'][:4]}–{flow[-1]['ano_mes'][:4]}", RIVER_PALE, BLUE)
    draw_badge(pieces, 1190, 138, f"{len(flow)} months", EMERALD_PALE, TEAL)

    draw_series_line(pieces, flow, months, 120, 190, 1170, 170, RIVER_BLUE, 3, True)
    draw_series_line(pieces, stage, months, 120, 462, 1170, 170, GOLD, 3, False)

    zscores = [item["zscore"] for item in annual]
    y0 = 734
    x0 = 120
    bar_w = 1170 / max(len(annual), 1)
    max_abs = max(max(abs(v) for v in zscores), 1.0)
    pieces.append(line(x0, y0 + 85, x0 + 1170, y0 + 85, SLATE_LIGHT, 2))
    for i, item in enumerate(annual):
        z = item["zscore"]
        x = x0 + i * bar_w + bar_w * 0.15
        bh = abs(z) / max_abs * 68
        y = y0 + 85 - bh if z >= 0 else y0 + 85
        color = TEAL if z >= 0 else RED
        pieces.append(rect(x, y, max(bar_w * 0.7, 3), bh, color, "none", 2))
        if i == 0 or i == len(annual) - 1 or item["year"] % 5 == 0:
            pieces.append(text(x + bar_w * 0.35, y0 + 110, str(item["year"]), 10, "500", SLATE, "middle"))

    wettest = max(annual, key=lambda r: r["zscore"])
    driest = min(annual, key=lambda r: r["zscore"])
    pieces.append(rect(1040, 646, 260, 220, "#EFF6FF", "#BFDBFE", 18))
    pieces.append(text(1062, 678, "What this panel says", 17, "700", BLUE))
    pieces.append(text(1062, 706, f"Wettest: {wettest['year']} (z={wettest['zscore']:.2f})", 13, "600", TEAL))
    pieces.append(text(1062, 728, f"Driest: {driest['year']} (z={driest['zscore']:.2f})", 13, "600", RED))
    flow_vals = [item["value"] for item in flow]
    pieces.append(text(1062, 760, f"Flow range: {format_number(min(flow_vals), 0)}–", 13, "500", SLATE))
    pieces.append(text(1062, 782, f"{format_number(max(flow_vals), 0)} ft³/s monthly", 13, "500", SLATE))
    pieces.append(text(1062, 818, "River-first backbone of the", 13, "600", BLUE))
    pieces.append(text(1062, 840, "Savannah narrative: the mainstem", 13, "600", BLUE))
    pieces.append(text(1062, 862, "pulses before any interpretation", 13, "600", BLUE))
    pieces.append(text(1062, 884, "of reservoir or sediment behavior.", 13, "600", BLUE))
    pieces.append("</svg>")
    save_svg("fig1_river_mainstem_hydrograph.svg", "".join(pieces))


# ─── Figure 2 — Lower-river quality timeseries (5 panels + pH) ────────────────

def fig2_lower_river_quality_timeseries(monthly_rows: list[dict], climatology_rows: list[dict]) -> None:
    config = [
        ("dock_water_temp_c", "Water temperature (°C)", TEAL),
        ("dock_do_mg_l", "Dissolved oxygen (mg/L)", BLUE),
        ("dock_conductance_us_cm", "Specific conductance (µS/cm)", ORANGE),
        ("dock_ph_su", "pH (standard units)", PURPLE),
        ("dock_turbidity_fnu", "Turbidity (FNU)", RED),
    ]
    width, height = 1400, 1080
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 72, "Lower-river quality behavior at USACE Dock: 2007–2026", 32, "700", BLUE))
    pieces.append(text(70, 102, "Continuous sensor series: temperature, DO, conductance, pH, and turbidity replace coverage-only chemistry with real 20-year behavior.", 15, "400", SLATE))

    layout = [(90, 170), (735, 170), (90, 430), (735, 430), (90, 700)]
    for i, (slug, title, color) in enumerate(config):
        series = series_from_monthly(monthly_rows, slug)
        if not series:
            continue
        x, y = layout[i]
        w = 555 if i < 4 else 1220
        h = 180
        pieces.append(rect(x - 20, y - 40, w + 40, h + 96, WHITE, SLATE_LIGHT, 18))
        pieces.append(text(x, y - 8, title, 17, "700", BLUE))
        draw_badge(pieces, x + w - 160, y - 30, f"{series[0]['ano_mes'][:4]}–{series[-1]['ano_mes'][:4]}", RIVER_PALE, BLUE)
        months = [item["ano_mes"] for item in series]
        draw_series_line(pieces, series, months, x, y + 14, w, h, color, 3, True)
        climatology = series_from_climatology(climatology_rows, slug)
        if climatology:
            summer = max(climatology, key=lambda r: r["value"])
            winter = min(climatology, key=lambda r: r["value"])
            pieces.append(text(x, y + h + 48, f"Peak: {MONTH_LABELS[int(summer['month']) - 1]} {format_number(float(summer['value']))}", 12, "600", color))
            pieces.append(text(x + 200, y + h + 48, f"Trough: {MONTH_LABELS[int(winter['month']) - 1]} {format_number(float(winter['value']))}", 12, "600", SLATE))

    pieces.append(rect(975, 792, 300, 216, "#F0FDF4", "#BBF7D0", 18))
    pieces.append(text(999, 820, "Analytical takeaways", 17, "700", TEAL))
    pieces.append(text(999, 852, "Summer thermal stress drives DO", 13, "600", SLATE))
    pieces.append(text(999, 874, "below seasonal baseline. Conductance", 13, "600", SLATE))
    pieces.append(text(999, 896, "peaks in late summer / fall, consistent", 13, "600", SLATE))
    pieces.append(text(999, 918, "with lower-river salinity intrusion.", 13, "600", SLATE))
    pieces.append(text(999, 950, "pH and turbidity reveal the mixing", 13, "600", SLATE))
    pieces.append(text(999, 972, "zone and runoff-driven turbidity", 13, "600", SLATE))
    pieces.append(text(999, 994, "signals not visible in discrete WQP.", 13, "600", SLATE))
    pieces.append("</svg>")
    save_svg("fig2_lower_river_quality_timeseries.svg", "".join(pieces))


# ─── Figure 3 — Seasonal climatology (6 panels) ───────────────────────────────

def fig3_river_seasonality(climatology_rows: list[dict]) -> None:
    config = [
        ("augusta_flow_cfs", "Augusta discharge (ft³/s)", RIVER_BLUE),
        ("dock_water_temp_c", "Dock temperature (°C)", TEAL),
        ("dock_do_mg_l", "Dock dissolved oxygen (mg/L)", BLUE),
        ("dock_conductance_us_cm", "Dock conductance (µS/cm)", ORANGE),
        ("dock_ph_su", "Dock pH", PURPLE),
        ("dock_turbidity_fnu", "Dock turbidity (FNU)", RED),
    ]
    width, height = 1400, 1060
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 72, "Savannah system seasonality: month-of-year climatology across all sensors", 32, "700", BLUE))
    pieces.append(text(70, 102, "Mean seasonal cycle from 20 years of data reveals the river's recurring behavioral structure across flow, chemistry, and quality.", 15, "400", SLATE))

    positions = [(90, 170), (735, 170), (90, 445), (735, 445), (90, 720), (735, 720)]
    for i, (slug, title, color) in enumerate(config):
        series = series_from_climatology(climatology_rows, slug)
        if not series:
            continue
        x, y = positions[i]
        w = 555
        h = 170
        pieces.append(rect(x - 20, y - 40, w + 40, h + 90, WHITE, SLATE_LIGHT, 18))
        pieces.append(text(x, y - 8, title, 16, "700", BLUE))
        draw_month_line(pieces, series, x, y + 14, w, h, color)

    pieces.append("</svg>")
    save_svg("fig3_river_seasonality.svg", "".join(pieces))


# ─── Figure 4 — Flow-quality coupling ─────────────────────────────────────────

def fig4_flow_quality_coupling(correlation_rows: list[dict], bridge_rows: list[dict]) -> None:
    pair_config = [
        ("dock_conductance_us_cm", "Conductance (µS/cm)", ORANGE),
        ("dock_do_mg_l", "Dissolved oxygen (mg/L)", BLUE),
        ("dock_turbidity_fnu", "Turbidity (FNU)", RED),
        ("dock_water_temp_c", "Water temperature (°C)", TEAL),
    ]
    width, height = 1400, 760
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 72, "Flow-quality coupling: Augusta discharge vs lower-river sensor behavior", 32, "700", BLUE))
    pieces.append(text(70, 102, "Monthly scatter reveals which responses move with hydrologic forcing and which oppose it — the core behavioral bridge inside the Savannah system.", 15, "400", SLATE))

    positions = [(80, 180), (430, 180), (780, 180), (80, 490)]
    for i, (target_slug, title, color) in enumerate(pair_config):
        x, y = positions[i]
        w = 300
        h = 260
        pieces.append(rect(x - 20, y - 40, w + 40, h + 104, WHITE, SLATE_LIGHT, 18))
        pieces.append(text(x, y - 8, f"Flow vs {title}", 16, "700", BLUE))
        points: list[tuple[float, float]] = []
        for row in bridge_rows:
            x_val = to_float(row.get("augusta_flow_cfs", ""))
            y_val = to_float(row.get(target_slug, ""))
            if x_val is not None and y_val is not None:
                points.append((x_val, y_val))
        r_val = None
        for row in correlation_rows:
            if row["source_series_slug"] == "augusta_flow_cfs" and row["target_series_slug"] == target_slug:
                r_val = float(row["correlation"])
                break
        draw_scatter_panel(pieces, points, x, y + 18, w, h, color, BLUE,
                           "Augusta discharge (ft³/s)", title, r_val)

    pieces.append(rect(1090, 490, 250, 270, "#EFF6FF", "#BFDBFE", 18))
    pieces.append(text(1114, 522, "Key couplings", 17, "700", BLUE))
    pieces.append(text(1114, 554, "Conductance: r = −0.79", 13, "700", ORANGE))
    pieces.append(text(1114, 576, "Strong negative — dilution", 13, "500", SLATE))
    pieces.append(text(1114, 608, "DO: r = +0.36", 13, "700", BLUE))
    pieces.append(text(1114, 630, "Moderate positive — reaeration", 13, "500", SLATE))
    pieces.append(text(1114, 662, "Turbidity: r = +0.40", 13, "700", RED))
    pieces.append(text(1114, 684, "Moderate positive — erosion load", 13, "500", SLATE))
    pieces.append(text(1114, 716, "Temperature: r = −0.33", 13, "700", TEAL))
    pieces.append(text(1114, 738, "Weak negative — seasonal lag", 13, "500", SLATE))
    pieces.append("</svg>")
    save_svg("fig4_flow_quality_coupling.svg", "".join(pieces))


# ─── Figure 5 — Reservoir WQP activity 1990–2025 (real data) ─────────────────

def fig5_reservoir_wqp_activity(yearly_rows: list[dict], summary_rows: list[dict]) -> None:
    """Replace empty cascade-operations figure with real WQP forebay activity data."""
    width, height = 1400, 800
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 72, "Reservoir forebay water-quality monitoring: 1990–2025", 32, "700", BLUE))
    pieces.append(text(70, 102, "WQP activity at Hartwell, Russell, and Thurmond dam forebays shows when each reservoir was monitored and how densely — the annex data foundation.", 15, "400", SLATE))

    card_w = 390
    for ci, reservoir in enumerate(RESERVOIR_ORDER):
        color = RESERVOIR_COLORS[reservoir]
        x = 70 + ci * 430
        y = 155
        pieces.append(rect(x, y, card_w, 560, WHITE, SLATE_LIGHT, 20))
        pieces.append(text(x + 24, y + 38, reservoir, 24, "700", BLUE))
        pieces.append(rect(x + 24, y + 56, 6, 6, color, "none", 3))

        # Summary metadata
        summary = next((r for r in summary_rows if r["reservoir"] == reservoir), None)
        if summary:
            pieces.append(text(x + 24, y + 80, f"Forebay: {summary['site_name'][:35]}", 11, "500", SLATE))
            pieces.append(text(x + 24, y + 98, f"{summary['first_year']}–{summary['last_year']}  |  {int(summary['years_with_data'])} active years  |  {int(summary['result_count']):,} results", 12, "700", BLUE))
            pieces.append(text(x + 24, y + 116, f"Lat {float(summary['latitude']):.4f}  Lon {float(summary['longitude']):.4f}", 11, "500", SLATE))

        # Bar chart: result_count by year
        res_rows = [r for r in yearly_rows if r["reservoir"] == reservoir]
        res_rows.sort(key=lambda r: int(r["year"]))
        if res_rows:
            years = [int(r["year"]) for r in res_rows]
            counts = [int(r["result_count"]) for r in res_rows]
            max_count = max(counts) or 1
            plot_x = x + 24
            plot_y = y + 140
            plot_w = 340
            plot_h = 280
            bar_gap = plot_w / len(years)
            pieces.append(line(plot_x, plot_y + plot_h, plot_x + plot_w, plot_y + plot_h, SLATE_LIGHT, 2))
            for bi, (yr, cnt) in enumerate(zip(years, counts)):
                bx = plot_x + bi * bar_gap + bar_gap * 0.1
                bh = cnt / max_count * plot_h
                by_ = plot_y + plot_h - bh
                bw = max(bar_gap * 0.8, 2)
                shade = color if cnt >= max_count * 0.5 else SLATE_LIGHT
                pieces.append(rect(bx, by_, bw, bh, shade, "none", 2))
                if yr % 5 == 0 or yr == years[0] or yr == years[-1]:
                    pieces.append(text(bx + bw / 2, plot_y + plot_h + 18, str(yr), 10, "500", SLATE, "middle"))
            pieces.append(text(plot_x, plot_y - 18, "Results per year", 12, "600", SLATE))
            pieces.append(text(plot_x + plot_w - 4, plot_y - 6, f"max {format_number(max_count, 0)}", 11, "600", color, "end"))

        # Total bar at bottom
        if summary:
            total_r = int(summary["result_count"])
            pieces.append(rect(x + 24, y + 448, 340, 22, SLATE_LIGHT, "none", 11))
            fill_w = min(340, 340 * total_r / 16_230)
            pieces.append(rect(x + 24, y + 448, fill_w, 22, color, "none", 11))
            pieces.append(text(x + 24 + 340 / 2, y + 464, f"{total_r:,} total results", 12, "700", WHITE, "middle"))

        pieces.append(text(x + 24, y + 496, f"Monitoring spans {summary['first_year'] if summary else '?'}–{summary['last_year'] if summary else '?'}", 12, "600", BLUE))
        pieces.append(text(x + 24, y + 518, "with forebay depth profiles and", 12, "500", SLATE))
        pieces.append(text(x + 24, y + 538, "multi-parameter chemical surveys.", 12, "500", SLATE))

    pieces.append(rect(70, 740, 1260, 44, "#F0F9FF", "#BAE6FD", 16))
    pieces.append(text(100, 769, "Combined: 44,644 WQP results across 3 dam forebays from 1990 to 2025 — the reservoir water-quality foundation that pairs with the river sensor layer.", 14, "600", BLUE))
    pieces.append("</svg>")
    save_svg("fig5_reservoir_wqp_activity.svg", "".join(pieces))


# ─── Figure 6 — Cascade system structure (NID + USACE snapshot) ──────────────

def fig6_cascade_system_structure(nid_rows: list[dict], usace_rows: list[dict]) -> None:
    """Replace empty bridge figure with real structural and operational snapshot data."""
    width, height = 1400, 780
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 72, "Cascade system structure: Hartwell → Russell → Thurmond", 32, "700", BLUE))
    pieces.append(text(70, 102, "NID structural metadata and current USACE operational snapshot for all three dams in the Savannah cascade regulation chain.", 15, "400", SLATE))

    # Storage capacity comparison bar
    nid_by_res = {r["reservoir"]: r for r in nid_rows}
    usace_by_res = {r["reservoir"]: r for r in usace_rows}
    max_storage = max(int(nid_by_res[r]["max_storage_acft"]) for r in RESERVOIR_ORDER if r in nid_by_res)

    # Cards
    card_w = 390
    for ci, reservoir in enumerate(RESERVOIR_ORDER):
        color = RESERVOIR_COLORS[reservoir]
        x = 70 + ci * 430
        y = 155
        pieces.append(rect(x, y, card_w, 520, WHITE, SLATE_LIGHT, 20))

        # Header
        pieces.append(text(x + 24, y + 38, reservoir, 24, "700", BLUE))
        nid = nid_by_res.get(reservoir, {})
        usace = usace_by_res.get(reservoir, {})

        if nid:
            pieces.append(text(x + 24, y + 64, f"Completed {nid.get('year_completed', '?')}  ·  NID {nid.get('nidid', '?')}", 12, "500", SLATE))
            pieces.append(text(x + 24, y + 86, f"Dam height: {nid.get('hydraulic_height_ft', '?')} ft  ·  Length: {int(nid.get('dam_length_ft', 0) or 0):,} ft", 12, "600", BLUE))
            pieces.append(text(x + 24, y + 108, f"Surface area: {int(nid.get('surface_area_acres', 0) or 0):,} acres  ·  Drainage: {int(nid.get('drainage_area_sqmi', 0) or 0):,} mi²", 12, "600", BLUE))

            # Max vs normal storage bar
            max_s = int(nid.get("max_storage_acft", 0) or 0)
            norm_s = int(nid.get("normal_storage_acft", 0) or 0)
            pieces.append(text(x + 24, y + 136, "Storage capacity", 13, "600", SLATE))
            pieces.append(rect(x + 24, y + 152, 340, 22, SLATE_LIGHT, "none", 11))
            if max_storage:
                pieces.append(rect(x + 24, y + 152, 340 * max_s / max_storage, 22, color, "none", 11))
                norm_w = 340 * norm_s / max_storage
                pieces.append(rect(x + 24, y + 152, norm_w, 22, color + "AA", "none", 11))
            pieces.append(text(x + 24, y + 174, f"Max: {format_number(max_s, 0)} ac·ft", 11, "600", SLATE))
            pieces.append(text(x + 24 + 340, y + 174, f"Normal: {format_number(norm_s, 0)}", 11, "600", SLATE, "end"))

        # USACE operational snapshot
        if usace:
            pieces.append(text(x + 24, y + 210, "Current USACE operational snapshot", 13, "600", BLUE))
            snap_items = [
                ("Pool elevation", usace.get("current_pool_elevation_ft", ""), "ft"),
                ("Rule curve", usace.get("rule_curve_ft", ""), "ft"),
                ("Δ to rule curve", usace.get("delta_to_rule_curve_ft", ""), "ft"),
                ("Storage", usace.get("current_storage_acft", ""), "ac·ft"),
                ("Storage %conservation", usace.get("storage_pct_conservation", ""), "%"),
                ("Inflow", usace.get("current_inflow_cfs", ""), "cfs"),
                ("Outflow", usace.get("current_outflow_cfs", ""), "cfs"),
                ("Tailwater elevation", usace.get("current_tailwater_ft", ""), "ft"),
            ]
            for si, (label, val, unit) in enumerate(snap_items):
                row_y = y + 236 + si * 28
                pieces.append(rect(x + 24, row_y, 340, 22, "#F8FAFC", SLATE_LIGHT, 6))
                pieces.append(text(x + 34, row_y + 16, label, 12, "500", SLATE))
                try:
                    fv = float(val)
                    val_str = f"{fv:,.1f} {unit}" if abs(fv) < 1e6 else f"{fv/1e6:.2f}M {unit}"
                    # Delta coloring
                    if "delta" in label.lower():
                        val_color = RED if fv < 0 else TEAL
                    else:
                        val_color = BLUE
                except (ValueError, TypeError):
                    val_str = val or "—"
                    val_color = SLATE
                pieces.append(text(x + 356, row_y + 16, val_str, 12, "700", val_color, "end"))

        pieces.append(text(x + 24, y + 498, usace.get("public_name", reservoir) if usace else reservoir, 11, "600", SLATE))

    # Cascade flow diagram at bottom
    arrow_y = 710
    pieces.append(text(70, arrow_y, "Cascade flow direction:", 13, "600", SLATE))
    for ci, reservoir in enumerate(RESERVOIR_ORDER):
        cx = 240 + ci * 350
        color = RESERVOIR_COLORS[reservoir]
        pieces.append(rect(cx, arrow_y - 18, 140, 30, color + "22", color, 8))
        pieces.append(text(cx + 70, arrow_y + 1, reservoir, 13, "700", color, "middle"))
        if ci < len(RESERVOIR_ORDER) - 1:
            pieces.append(line(cx + 140, arrow_y - 3, cx + 210, arrow_y - 3, SLATE, 2))
            pieces.append(text(cx + 185, arrow_y - 8, "→", 18, "700", SLATE, "middle"))
    pieces.append(text(1180, arrow_y + 1, "→  Augusta / river", 13, "600", SLATE))
    pieces.append("</svg>")
    save_svg("fig6_cascade_system_structure.svg", "".join(pieces))


# ─── Figure 7 — Sediment texture + depositional score (all 19 sites) ─────────

def fig7_sediment_texture_score(master_rows: list[dict], score_rows: list[dict]) -> None:
    width, height = 1400, 820
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 72, "Sediment texture and fine-depositional score — all 19 sites", 32, "700", BLUE))
    pieces.append(text(70, 102, "Stacked texture composition per site (left) and ranked composite score combining clay%, water%, Fe, carbon, D50, and sand% (right).", 15, "400", SLATE))

    # Left: stacked bar all 19 sites
    master_sorted = sorted(master_rows, key=lambda r: int(float(r["site"])))
    plot_x = 80
    plot_y = 180
    bar_w = 34
    gap = 6
    pieces.append(text(plot_x, 152, "Texture composition by site", 18, "700", BLUE))
    pieces.append(text(plot_x, 170, "Clay", 11, "700", TEAL))
    pieces.append(text(plot_x + 50, 170, "Silt", 11, "700", CYAN))
    pieces.append(text(plot_x + 94, 170, "Sand", 11, "700", ORANGE))

    for i, row in enumerate(master_sorted):
        site = int(float(row["site"]))
        x = plot_x + i * (bar_w + gap)
        clay = float(row.get("clay_pct") or 0)
        silt = float(row.get("silt_pct") or 0)
        sand = float(row.get("sand_pct") or 0)
        total = max(clay + silt + sand, 1.0)
        fracs = [("Clay", clay / total, TEAL), ("Silt", silt / total, CYAN), ("Sand", sand / total, ORANGE)]
        cur_y = plot_y + 380
        for _, frac, color in fracs:
            sh = 360 * frac
            pieces.append(rect(x, cur_y - sh, bar_w, sh, color, "none", 3))
            cur_y -= sh
        pieces.append(text(x + bar_w / 2, plot_y + 406, str(site), 10, "600", SLATE, "middle"))

    # Right: score bars (bilateral, all 19 sites)
    score_sorted = sorted(score_rows, key=lambda r: -float(r["fine_depositional_score"]))
    sx = 810
    pieces.append(text(sx, 152, "Fine-depositional score (ranked)", 18, "700", BLUE))
    max_s = max(abs(float(r["fine_depositional_score"])) for r in score_sorted)
    zero_x = sx + 200
    bar_scale = 360 / (max_s * 2) if max_s else 1

    for i, row in enumerate(score_sorted):
        s = float(row["fine_depositional_score"])
        y = 180 + i * 30
        site_n = row["site"]
        color = TEAL if s >= 0 else RED
        bw = abs(s) * bar_scale
        if s >= 0:
            bx = zero_x
        else:
            bx = zero_x - bw
        pieces.append(rect(sx, y + 2, 190, 22, "#F8FAFC", SLATE_LIGHT, 6))
        pieces.append(text(sx + 8, y + 17, f"Site {site_n}", 12, "600", SLATE))
        # background track
        pieces.append(rect(zero_x - 185, y + 2, 370, 22, "#F1F5F9", "none", 6))
        pieces.append(rect(bx, y + 2, max(bw, 2), 22, color, "none", 6))
        pieces.append(line(zero_x, y + 2, zero_x, y + 24, SLATE, 1))
        pieces.append(text(zero_x + 192, y + 17, f"{s:.2f}", 11, "700", color, "end"))

    # Zero line label
    pieces.append(line(zero_x, 175, zero_x, 175 + 19 * 30 + 10, SLATE_LIGHT, 1, "4 4"))
    pieces.append(text(zero_x, 168, "0", 10, "600", SLATE, "middle"))

    pieces.append(rect(70, 760, 1260, 44, "#F0FDF4", "#BBF7D0", 16))
    pieces.append(text(100, 789, "Sites 9, 3, 7, 5, 21 score highest: fine-grained, water-rich, Fe- and carbon-elevated — strongest depositional candidates in the Thurmond reservoir.", 14, "600", TEAL))
    pieces.append("</svg>")
    save_svg("fig7_sediment_texture_score.svg", "".join(pieces))


# ─── Figure 8 — Sediment geochemical relations (6 panels) ────────────────────

def fig8_sediment_relations(master_rows: list[dict], pairwise_rows: list[dict]) -> None:
    scatter_defs = [
        ("clay_pct", "fe_ppm", "Clay (%) vs Fe (ppm)", TEAL),
        ("d50", "fe_ppm", "D50 (µm) vs Fe (ppm)", ORANGE),
        ("fe_ppm", "carbon_pct", "Fe (ppm) vs Carbon (%)", BLUE),
        ("depth", "fe_ppm", "Depth (m) vs Fe (ppm)", PURPLE),
        ("mn_ppm", "fe_ppm", "Mn (ppm) vs Fe (ppm)", AMBER),
        ("water_pct", "carbon_pct", "Water content (%) vs Carbon (%)", CYAN),
    ]
    pairwise_lookup = {(r["x_field"], r["y_field"]): float(r["correlation"]) for r in pairwise_rows}
    width, height = 1400, 920
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 72, "Sediment geochemical relations: Fe, clay, carbon, Mn, depth, D50, and water content", 32, "700", BLUE))
    pieces.append(text(70, 102, "Six crossplots close the depositional interpretation loop — texture controls Fe enrichment, Fe couples to carbon, Mn co-varies with Fe, and water content mirrors organic preservation.", 15, "400", SLATE))

    positions = [(80, 170), (550, 170), (1020, 170), (80, 520), (550, 520), (1020, 520)]
    for i, (x_field, y_field, title, color) in enumerate(scatter_defs):
        x, y = positions[i]
        w, h = 320, 240
        pieces.append(rect(x - 20, y - 36, w + 40, h + 100, WHITE, SLATE_LIGHT, 18))
        pieces.append(text(x, y - 6, title, 15, "700", BLUE))
        points = []
        for row in master_rows:
            xv = to_float(row.get(x_field, ""))
            yv = to_float(row.get(y_field, ""))
            if xv is not None and yv is not None:
                points.append((xv, yv))
        r_val = pairwise_lookup.get((x_field, y_field))
        draw_scatter_panel(pieces, points, x, y + 18, w, h, color, BLUE,
                           x_field.replace("_", " "), y_field.replace("_", " "), r_val)

    pieces.append(rect(70, 860, 1260, 44, "#EFF6FF", "#BFDBFE", 16))
    pieces.append(text(100, 889, "Fe-clay (r=+0.69) and Fe-carbon (r=+0.75) are the clearest anchors. Mn-Fe co-enrichment (r~+0.6) signals redox-driven diagenesis. Water%-carbon coupling confirms organic preservation in wet fine sediment.", 14, "600", BLUE))
    pieces.append("</svg>")
    save_svg("fig8_sediment_relations.svg", "".join(pieces))


# ─── Figure 9 — Cross-layer data coverage matrix ─────────────────────────────

def fig9_coverage_matrix(coverage_rows: list[dict], crosslayer_rows: list[dict]) -> None:
    width, height = 1400, 860
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 72, "Data coverage across analytical layers: what is available and where gaps remain", 32, "700", BLUE))
    pieces.append(text(70, 102, "Coverage target matrix (left) and cross-layer parameter depth by entity (right) — the honest accounting of what the report can and cannot claim.", 15, "400", SLATE))

    # Left: coverage target matrix
    pieces.append(text(80, 150, "Coverage vs 20-year target by layer", 18, "700", BLUE))
    for i, row in enumerate(coverage_rows):
        y = 172 + i * 62
        ret = int(row.get("returned_years", 0) or 0)
        tgt = int(row.get("target_years", 20) or 20)
        status = row.get("coverage_status", "below_target")
        color = TEAL if status == "meets_target" else (AMBER if ret >= tgt * 0.5 else RED)
        pieces.append(rect(80, y, 580, 50, WHITE, SLATE_LIGHT, 10))
        layer_label = f"{row['layer']} — {row['entity']}"
        pieces.append(text(96, y + 18, layer_label[:48], 13, "700", BLUE))
        pieces.append(text(96, y + 36, f"{row.get('source', '')} · {row.get('first_year', '?')}–{row.get('last_year', '?')}", 11, "500", SLATE))
        # Progress bar
        bar_x = 360
        pieces.append(rect(bar_x, y + 10, 240, 18, SLATE_LIGHT, "none", 9))
        fill_w = min(240, 240 * ret / max(tgt, 1))
        pieces.append(rect(bar_x, y + 10, fill_w, 18, color, "none", 9))
        pieces.append(text(bar_x + 248, y + 24, f"{ret}/{tgt} yr", 11, "700", color, "start"))
        badge_text = "MEETS TARGET" if status == "meets_target" else "BELOW TARGET"
        draw_badge(pieces, 560, y + 10, badge_text, color + "22", color)

    # Right: cross-layer parameter depth heatmap
    pieces.append(text(720, 150, "Parameter coverage by entity and group", 18, "700", BLUE))
    entities = list(dict.fromkeys(r["entity"] for r in crosslayer_rows))[:8]
    param_groups = list(dict.fromkeys(r["parameter_group"] for r in crosslayer_rows))[:10]
    cell_w = 64
    cell_h = 34
    ox = 720
    oy = 175

    for pi, pg in enumerate(param_groups):
        pieces.append(text(ox + 170 + pi * cell_w + cell_w / 2, oy + 14,
                           pg[:10], 9, "600", SLATE, "middle"))

    for ei, entity in enumerate(entities):
        row_y = oy + 22 + ei * cell_h
        pieces.append(text(ox + 8, row_y + 22, entity[:18], 12, "600", BLUE))
        for pi, pg in enumerate(param_groups):
            match = next((r for r in crosslayer_rows if r["entity"] == entity and r["parameter_group"] == pg), None)
            cell_x = ox + 170 + pi * cell_w
            if match:
                ratio = float(match.get("coverage_ratio", 0) or 0)
                yrs = int(match.get("years_available", 0) or 0)
                cell_color = TEAL if ratio >= 0.8 else (AMBER if ratio >= 0.4 else RED)
                alpha = f"{int(40 + ratio * 160):02x}"
                pieces.append(rect(cell_x + 2, row_y + 4, cell_w - 4, cell_h - 6, cell_color + alpha, "none", 6))
                pieces.append(text(cell_x + cell_w / 2, row_y + 20, f"{yrs}yr", 9, "700", WHITE, "middle"))
            else:
                pieces.append(rect(cell_x + 2, row_y + 4, cell_w - 4, cell_h - 6, "#F1F5F9", "none", 6))
                pieces.append(text(cell_x + cell_w / 2, row_y + 20, "—", 9, "500", SLATE_LIGHT, "middle"))

    # Legend
    lx = 720
    ly = 720
    pieces.append(text(lx, ly, "Coverage ratio:", 12, "600", SLATE))
    for lbl, col in [("≥80%", TEAL), ("40–79%", AMBER), ("<40%", RED)]:
        pieces.append(rect(lx + 140, ly - 14, 16, 16, col, "none", 4))
        pieces.append(text(lx + 160, ly, lbl, 11, "500", SLATE))
        lx += 90

    pieces.append(rect(70, 800, 1260, 44, "#FFFBEB", "#FDE68A", 16))
    pieces.append(text(100, 829, "River hydrology and lower-river sensor layers meet the 20-year target. River chemistry and reservoir operations are the structural gaps — documented here, not papered over.", 14, "600", AMBER))
    pieces.append("</svg>")
    save_svg("fig9_coverage_matrix.svg", "".join(pieces))


# ─── Figure 10 — Spatial sediment map with Fe and clay gradients ──────────────

def fig10_sediment_spatial_map(master_rows: list[dict], score_rows: list[dict]) -> None:
    lats = [float(r["latitude"]) for r in master_rows]
    lons = [float(r["longitude"]) for r in master_rows]
    fe_vals = [float(r["fe_ppm"]) for r in master_rows]
    clay_vals = [float(r["clay_pct"]) for r in master_rows]
    score_lookup = {int(float(r["site"])): float(r["fine_depositional_score"]) for r in score_rows}

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    min_fe, max_fe = min(fe_vals), max(fe_vals)
    min_clay, max_clay = min(clay_vals), max(clay_vals)

    width, height = 1400, 860
    MAP_X, MAP_Y, MAP_W, MAP_H = 80, 155, 550, 500
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 72, "Spatial distribution of sediment properties across Clarks Hill Lake", 32, "700", BLUE))
    pieces.append(text(70, 102, "Site locations colored by Fe concentration (left) and clay content (right). Size encodes depositional score — larger circles are stronger depositional candidates.", 15, "400", SLATE))

    def map_x(lon: float) -> float:
        return scale(lon, min_lon - 0.01, max_lon + 0.01, MAP_X, MAP_X + MAP_W)

    def map_y(lat: float) -> float:
        return scale(lat, min_lat - 0.005, max_lat + 0.005, MAP_Y + MAP_H, MAP_Y)

    for panel_i, (field_vals, field_label, lo_color, hi_color) in enumerate([
        (fe_vals, "Fe concentration (ppm)", "#FEF3C7", "#92400E"),
        (clay_vals, "Clay content (%)", "#EFF6FF", "#1E3A5F"),
    ]):
        px = MAP_X + panel_i * 660
        py = MAP_Y

        pieces.append(rect(px - 10, py - 10, MAP_W + 20, MAP_H + 20, WHITE, SLATE_LIGHT, 16))
        pieces.append(text(px, py - 24, field_label, 17, "700", BLUE))

        min_v = min(field_vals)
        max_v = max(field_vals)

        for ri, row in enumerate(master_rows):
            site = int(float(row["site"]))
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            val = field_vals[ri]
            sc = score_lookup.get(site, 0)
            radius = 8 + max(sc, 0) * 2.5

            ratio = (val - min_v) / (max_v - min_v) if max_v > min_v else 0.5
            r_int = int(int(lo_color[1:3], 16) + ratio * (int(hi_color[1:3], 16) - int(lo_color[1:3], 16)))
            g_int = int(int(lo_color[3:5], 16) + ratio * (int(hi_color[3:5], 16) - int(lo_color[3:5], 16)))
            b_int = int(int(lo_color[5:7], 16) + ratio * (int(hi_color[5:7], 16) - int(lo_color[5:7], 16)))
            fill_color = f"#{max(0, min(255, r_int)):02x}{max(0, min(255, g_int)):02x}{max(0, min(255, b_int)):02x}"

            cx = map_x(lon) + panel_i * 660
            cy = map_y(lat)
            pieces.append(circle(cx, cy, radius, fill_color, WHITE, 1.2, 0.85))
            pieces.append(text(cx, cy + 4, str(site), 9, "700", WHITE if ratio > 0.5 else BLUE, "middle"))

        # Color legend
        leg_x = px
        leg_y = py + MAP_H + 28
        pieces.append(text(leg_x, leg_y, f"Low ({format_number(min_v, 0)})", 11, "500", SLATE))
        for step in range(12):
            ratio = step / 11
            r_int = int(int(lo_color[1:3], 16) + ratio * (int(hi_color[1:3], 16) - int(lo_color[1:3], 16)))
            g_int = int(int(lo_color[3:5], 16) + ratio * (int(hi_color[3:5], 16) - int(lo_color[3:5], 16)))
            b_int = int(int(lo_color[5:7], 16) + ratio * (int(hi_color[5:7], 16) - int(lo_color[5:7], 16)))
            fill_c = f"#{max(0, min(255, r_int)):02x}{max(0, min(255, g_int)):02x}{max(0, min(255, b_int)):02x}"
            pieces.append(rect(leg_x + 100 + step * 22, leg_y - 14, 22, 14, fill_c, "none", 3))
        pieces.append(text(leg_x + 100 + 12 * 22 + 6, leg_y, f"High ({format_number(max_v, 0)})", 11, "500", SLATE))

    # Size legend
    pieces.append(text(80, MAP_Y + MAP_H + 82, "Circle size = depositional score (larger = stronger candidate)", 12, "500", SLATE))

    pieces.append(rect(70, 790, 1260, 44, "#F0FDF4", "#BBF7D0", 16))
    pieces.append(text(100, 819, "Deep-water southern sites (9, 3, 7) cluster as high-Fe, high-clay depositional zones. Shallow nearshore sites (2, 13, 14, 20) show coarser texture and lower Fe — consistent with higher-energy conditions.", 14, "600", TEAL))
    pieces.append("</svg>")
    save_svg("fig10_sediment_spatial_map.svg", "".join(pieces))


# ─── Figure 11 — pH and DO monthly series + scatter ──────────────────────────

def fig11_ph_do_series(monthly_rows: list[dict], climatology_rows: list[dict]) -> None:
    ph_series = series_from_monthly(monthly_rows, "dock_ph_su")
    do_series = series_from_monthly(monthly_rows, "dock_do_mg_l")
    temp_series = series_from_monthly(monthly_rows, "dock_water_temp_c")

    # Build scatter: temp vs DO and pH
    temp_map = {item["ano_mes"]: item["value"] for item in temp_series}
    do_scatter: list[tuple[float, float]] = []
    ph_scatter: list[tuple[float, float]] = []
    for item in do_series:
        t = temp_map.get(item["ano_mes"])
        if t is not None:
            do_scatter.append((t, item["value"]))
    ph_map = {item["ano_mes"]: item["value"] for item in ph_series}
    for item in do_series:
        p = ph_map.get(item["ano_mes"])
        if p is not None:
            do_scatter_ph: list[tuple[float, float]] = []
    for item in ph_series:
        d = next((x["value"] for x in do_series if x["ano_mes"] == item["ano_mes"]), None)
        if d is not None:
            ph_scatter.append((d, item["value"]))

    width, height = 1400, 860
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 72, "pH and dissolved oxygen at USACE Dock: seasonal dynamics and thermal coupling", 32, "700", BLUE))
    pieces.append(text(70, 102, "pH and DO timeseries (top) paired with temperature-DO and DO-pH scatter to expose the photosynthesis-respiration and thermal-stratification signals in the lower Savannah.", 15, "400", SLATE))

    # pH timeseries
    pieces.append(rect(70, 140, 615, 280, WHITE, SLATE_LIGHT, 18))
    pieces.append(text(96, 170, "Dock pH (standard units) — 2007–2026", 17, "700", BLUE))
    if ph_series:
        months = [item["ano_mes"] for item in ph_series]
        draw_series_line(pieces, ph_series, months, 96, 190, 558, 168, PURPLE, 3, True)

    # DO timeseries
    pieces.append(rect(715, 140, 615, 280, WHITE, SLATE_LIGHT, 18))
    pieces.append(text(741, 170, "Dock dissolved oxygen (mg/L) — 2007–2026", 17, "700", BLUE))
    if do_series:
        months_do = [item["ano_mes"] for item in do_series]
        draw_series_line(pieces, do_series, months_do, 741, 190, 558, 168, BLUE, 3, True)

    # Scatter: temperature vs DO
    pieces.append(rect(70, 450, 400, 340, WHITE, SLATE_LIGHT, 18))
    pieces.append(text(96, 480, "Temperature vs DO", 17, "700", BLUE))
    if do_scatter:
        r_temp_do = pearson_r([p[0] for p in do_scatter], [p[1] for p in do_scatter])
        draw_scatter_panel(pieces, do_scatter, 96, 500, 348, 230, BLUE, TEAL,
                           "Temperature (°C)", "DO (mg/L)", r_temp_do)
    pieces.append(text(96, 798, "As temperature rises, DO drops — thermal stratification suppresses reaeration.", 12, "500", SLATE))

    # Scatter: DO vs pH
    pieces.append(rect(500, 450, 400, 340, WHITE, SLATE_LIGHT, 18))
    pieces.append(text(526, 480, "DO vs pH", 17, "700", BLUE))
    if ph_scatter:
        r_do_ph = pearson_r([p[0] for p in ph_scatter], [p[1] for p in ph_scatter])
        draw_scatter_panel(pieces, ph_scatter, 526, 500, 348, 230, PURPLE, BLUE,
                           "DO (mg/L)", "pH", r_do_ph)
    pieces.append(text(526, 798, "DO and pH co-vary — photosynthesis produces both O₂ and alkalinity.", 12, "500", SLATE))

    # Climatology comparison
    pieces.append(rect(930, 450, 400, 340, WHITE, SLATE_LIGHT, 18))
    pieces.append(text(956, 480, "Seasonal cycle: pH and DO", 17, "700", BLUE))
    ph_clim = series_from_climatology(climatology_rows, "dock_ph_su")
    do_clim = series_from_climatology(climatology_rows, "dock_do_mg_l")
    if ph_clim:
        draw_month_line(pieces, ph_clim, 956, 510, 348, 100, PURPLE)
    if do_clim:
        draw_month_line(pieces, do_clim, 956, 636, 348, 100, BLUE)
    pieces.append(text(956, 628, "pH seasonal cycle", 11, "600", PURPLE))
    pieces.append(text(956, 756, "DO seasonal cycle", 11, "600", BLUE))

    pieces.append(rect(70, 804, 1260, 44, "#F5F3FF", "#DDD6FE", 16))
    pieces.append(text(100, 833, "Summer pH rises with photosynthesis; DO falls with thermal stratification. The anti-phase between pH and DO in summer confirms a biologically active lower-river environment.", 14, "600", PURPLE))
    pieces.append("</svg>")
    save_svg("fig11_ph_do_series.svg", "".join(pieces))


# ─── Figure 12 — Sediment Mn-Fe and water content deep-dive ──────────────────

def fig12_sediment_mn_water(master_rows: list[dict], score_rows: list[dict]) -> None:
    score_lookup = {int(float(r["site"])): float(r["fine_depositional_score"]) for r in score_rows}

    # Build series for bar/scatter plots
    sites = [int(float(r["site"])) for r in master_rows]
    fe = [float(r.get("fe_ppm") or 0) for r in master_rows]
    mn = [float(r.get("mn_ppm") or 0) for r in master_rows]
    water = [float(r.get("water_pct") or 0) for r in master_rows]
    carbon = [float(r.get("carbon_pct") or 0) for r in master_rows]
    clay = [float(r.get("clay_pct") or 0) for r in master_rows]
    depth = [float(r.get("depth") or 0) for r in master_rows]

    fe_mn_scatter = list(zip(mn, fe))
    water_carbon_scatter = list(zip(water, carbon))
    clay_mn_scatter = list(zip(clay, mn))
    depth_water_scatter = list(zip(depth, water))

    width, height = 1400, 900
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 72, "Sediment Mn–Fe co-enrichment and water content as diagenetic indicators", 32, "700", BLUE))
    pieces.append(text(70, 102, "Mn and Fe are redox-sensitive elements that co-enrich under reducing conditions. High water content in fine sediments promotes organic-matter preservation.", 15, "400", SLATE))

    # Mn per site bar chart
    pieces.append(rect(70, 148, 620, 280, WHITE, SLATE_LIGHT, 18))
    pieces.append(text(96, 178, "Mn concentration per site (ppm)", 17, "700", BLUE))
    max_mn = max(mn) or 1
    mn_bar_w = 560 / len(sites)
    for i, (s, m) in enumerate(zip(sites, mn)):
        bx = 96 + i * mn_bar_w + mn_bar_w * 0.1
        bh = m / max_mn * 170
        by = 148 + 272 - bh
        score_s = score_lookup.get(s, 0)
        color = AMBER if score_s >= 1.0 else SLATE_LIGHT
        pieces.append(rect(bx, by, max(mn_bar_w * 0.8, 3), bh, color, "none", 2))
        pieces.append(text(bx + mn_bar_w * 0.4, 148 + 284, str(s), 9, "500", SLATE, "middle"))
    pieces.append(text(96, 148 + 298, f"Max: {format_number(max_mn, 0)} ppm (Site 6)", 11, "600", AMBER))

    # Water content per site bar chart
    pieces.append(rect(710, 148, 620, 280, WHITE, SLATE_LIGHT, 18))
    pieces.append(text(736, 178, "Water content per site (%)", 17, "700", BLUE))
    max_w = max(water) or 1
    w_bar_w = 560 / len(sites)
    for i, (s, w_) in enumerate(zip(sites, water)):
        bx = 736 + i * w_bar_w + w_bar_w * 0.1
        bh = w_ / max_w * 170
        by = 148 + 272 - bh
        score_s = score_lookup.get(s, 0)
        color = CYAN if score_s >= 1.0 else SLATE_LIGHT
        pieces.append(rect(bx, by, max(w_bar_w * 0.8, 3), bh, color, "none", 2))
        pieces.append(text(bx + w_bar_w * 0.4, 148 + 284, str(s), 9, "500", SLATE, "middle"))
    pieces.append(text(736, 148 + 298, f"Max: {format_number(max_w, 1)}% (highest-score sites)", 11, "600", CYAN))

    # Four scatters
    scatter_defs = [
        (fe_mn_scatter, "Mn (ppm)", "Fe (ppm)", "Mn vs Fe co-enrichment", AMBER, ORANGE),
        (water_carbon_scatter, "Water content (%)", "Carbon (%)", "Water content vs Carbon", CYAN, BLUE),
        (clay_mn_scatter, "Clay (%)", "Mn (ppm)", "Clay vs Mn", TEAL, AMBER),
        (depth_water_scatter, "Depth (m)", "Water content (%)", "Depth vs Water content", PURPLE, CYAN),
    ]
    positions = [(80, 480), (430, 480), (780, 480), (1130, 480)]
    for i, (pts, xl, yl, title, pc, lc) in enumerate(scatter_defs):
        x, y = positions[i]
        w, h = 260, 220
        pieces.append(rect(x - 14, y - 36, w + 28, h + 100, WHITE, SLATE_LIGHT, 18))
        pieces.append(text(x, y - 6, title, 14, "700", BLUE))
        r_val = pearson_r([p[0] for p in pts], [p[1] for p in pts]) if len(pts) >= 2 else 0.0
        draw_scatter_panel(pieces, pts, x, y + 14, w, h, pc, lc, xl, yl, r_val)

    pieces.append(rect(70, 840, 1260, 44, "#FFFBEB", "#FDE68A", 16))
    pieces.append(text(100, 869, "Mn–Fe co-enrichment under reducing conditions confirms diagenetic mobilization in fine depositional zones. Clay drives both Mn and Fe accumulation via surface sorption and redox trapping.", 14, "600", AMBER))
    pieces.append("</svg>")
    save_svg("fig12_sediment_mn_water.svg", "".join(pieces))


# ─── Main ─────────────────────────────────────────────────────────────────────

def clean_fig1_river_mainstem_hydrograph(monthly_rows: list[dict]) -> None:
    flow = series_from_monthly(monthly_rows, "augusta_flow_cfs")
    stage = series_from_monthly(monthly_rows, "augusta_stage_ft")
    width, height = 1400, 860
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 70, "Savannah River behavior near Augusta (2006-2026)", 30, "700", BLUE))
    pieces.append(text(70, 98, "Monthly behavior with a 12-month moving mean. The river comes first; the rest of the report tries to explain this signal.", 14, "400", SLATE))
    draw_line_legend(pieces, [("Monthly", RIVER_BLUE, 2, 0.40), ("12-month mean", BLUE, 4, 1.0)], 70, 128)

    for series, title, x, y, w, h, color in [
        (flow, "Augusta discharge (ft³/s)", 80, 170, 1240, 250, RIVER_BLUE),
        (stage, "Augusta stage (ft)", 80, 500, 1240, 220, GOLD),
    ]:
        pieces.append(rect(x - 18, y - 36, w + 36, h + 94, WHITE, SLATE_LIGHT, 18))
        pieces.append(text(x, y - 8, title, 17, "700", BLUE))
        draw_badge(pieces, x + w - 110, y - 30, series_year_window(series), RIVER_PALE, BLUE)
        draw_series_with_trend(pieces, series, x, y + 16, w, h, color, BLUE if color == RIVER_BLUE else color)

    pieces.append("</svg>")
    save_svg("fig1_river_mainstem_hydrograph.svg", "".join(pieces))


def clean_fig2_cascade_operations(monthly_rows: list[dict], summary_rows: list[dict]) -> None:
    width, height = 1400, 980
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 70, "Reservoir behavior upstream of Augusta: cascade outflow", 30, "700", BLUE))
    pieces.append(text(70, 98, "Hartwell, Russell, and Thurmond appear here as operational context for the river. Each panel shows monthly outflow plus a 12-month mean.", 14, "400", SLATE))
    draw_line_legend(pieces, [("Monthly", SLATE, 2, 0.35), ("12-month mean", BLUE, 4, 1.0)], 70, 128)

    for index, reservoir in enumerate(RESERVOIR_ORDER):
        series = reservoir_series(monthly_rows, reservoir, "outflow_cfs")
        color = RESERVOIR_COLORS[reservoir]
        x = 80
        y = 170 + index * 255
        w = 1240
        h = 165
        pieces.append(rect(x - 18, y - 34, w + 36, h + 84, WHITE, SLATE_LIGHT, 18))
        pieces.append(text(x, y - 8, reservoir, 17, "700", BLUE))
        summary = next((row for row in summary_rows if row["reservoir"] == reservoir and row["metric_slug"] == "outflow_cfs"), None)
        if summary:
            draw_badge(pieces, x + w - 150, y - 28, f"{summary['first_year']}-{summary['last_year']}", RIVER_PALE, BLUE)
        draw_series_with_trend(pieces, series, x, y + 14, w, h, color, color)

    pieces.append("</svg>")
    save_svg("fig2_cascade_operations.svg", "".join(pieces))


def clean_fig3_thurmond_augusta_bridge(bridge_rows: list[dict]) -> None:
    width, height = 1400, 900
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 70, "Thurmond to Augusta: release, storage, and downstream response", 30, "700", BLUE))
    pieces.append(text(70, 98, "This is the clearest operational bridge in the workspace: Thurmond release behavior aligns with the river response observed near Augusta.", 14, "400", SLATE))
    draw_line_legend(pieces, [("Augusta discharge", RIVER_BLUE, 4, 1.0), ("Thurmond outflow", ORANGE, 4, 1.0)], 70, 128)

    flow_series = [{"ano_mes": row["ano_mes"], "value": float(row["augusta_flow_cfs"])} for row in bridge_rows if to_float(row.get("augusta_flow_cfs")) is not None and to_float(row.get("thurmond_outflow_cfs")) is not None]
    thurmond_outflow = [{"ano_mes": row["ano_mes"], "value": float(row["thurmond_outflow_cfs"])} for row in bridge_rows if to_float(row.get("augusta_flow_cfs")) is not None and to_float(row.get("thurmond_outflow_cfs")) is not None]
    storage_series = [{"ano_mes": row["ano_mes"], "value": float(row["thurmond_storage_acft"])} for row in bridge_rows if to_float(row.get("thurmond_storage_acft")) is not None]

    x, y, w, h = 80, 170, 1240, 250
    pieces.append(rect(x - 18, y - 36, w + 36, h + 88, WHITE, SLATE_LIGHT, 18))
    pieces.append(text(x, y - 8, "Augusta discharge vs Thurmond outflow (ft³/s)", 17, "700", BLUE))
    months = [item["ano_mes"] for item in flow_series]
    values = [item["value"] for item in flow_series] + [item["value"] for item in thurmond_outflow]
    minimum, maximum = nice_domain(values)
    x_map = x_lookup_from_months(months, x, w)
    draw_y_guides(pieces, x, w, y + 16, h, minimum, maximum)
    pieces.append(polyline([(x_map[item["ano_mes"]], scale(item["value"], minimum, maximum, y + 16 + h, y + 16)) for item in flow_series], RIVER_BLUE, 2, opacity=0.30))
    pieces.append(polyline([(x_map[item["ano_mes"]], scale(item["value"], minimum, maximum, y + 16 + h, y + 16)) for item in rolling_mean(flow_series)], RIVER_BLUE, 4))
    pieces.append(polyline([(x_map[item["ano_mes"]], scale(item["value"], minimum, maximum, y + 16 + h, y + 16)) for item in thurmond_outflow], ORANGE, 2, opacity=0.30))
    pieces.append(polyline([(x_map[item["ano_mes"]], scale(item["value"], minimum, maximum, y + 16 + h, y + 16)) for item in rolling_mean(thurmond_outflow)], ORANGE, 4))
    draw_time_axis(pieces, months, x_map, y + 16 + h)

    x2, y2, w2, h2 = 80, 510, 1240, 210
    pieces.append(rect(x2 - 18, y2 - 36, w2 + 36, h2 + 88, WHITE, SLATE_LIGHT, 18))
    pieces.append(text(x2, y2 - 8, "Thurmond storage context (ac·ft)", 17, "700", BLUE))
    draw_series_with_trend(pieces, storage_series, x2, y2 + 16, w2, h2, GOLD, GOLD)

    pieces.append("</svg>")
    save_svg("fig3_thurmond_augusta_bridge.svg", "".join(pieces))


def clean_fig4_lower_river_quality(monthly_rows: list[dict]) -> None:
    config = [
        ("dock_water_temp_c", "Water temperature (°C)", TEAL),
        ("dock_do_mg_l", "Dissolved oxygen (mg/L)", BLUE),
        ("dock_conductance_us_cm", "Specific conductance (µS/cm)", ORANGE),
        ("dock_turbidity_fnu", "Turbidity (FNU)", RED),
    ]
    width, height = 1400, 980
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 70, "Lower-river water-quality behavior at USACE Dock", 30, "700", BLUE))
    pieces.append(text(70, 98, "These continuous sensor records are still the strongest quality-behavior layer currently available in the Savannah workspace.", 14, "400", SLATE))
    draw_line_legend(pieces, [("Monthly", SLATE, 2, 0.35), ("12-month mean", BLUE, 4, 1.0)], 70, 128)

    positions = [(80, 170), (720, 170), (80, 520), (720, 520)]
    for index, (slug, title, color) in enumerate(config):
        series = series_from_monthly(monthly_rows, slug)
        x, y = positions[index]
        w, h = 560, 210
        pieces.append(rect(x - 18, y - 36, w + 36, h + 90, WHITE, SLATE_LIGHT, 18))
        pieces.append(text(x, y - 8, title, 16, "700", BLUE))
        draw_badge(pieces, x + w - 110, y - 30, series_year_window(series), RIVER_PALE, BLUE)
        draw_series_with_trend(pieces, series, x, y + 16, w, h, color, color)

    pieces.append("</svg>")
    save_svg("fig4_lower_river_quality_timeseries.svg", "".join(pieces))


def clean_fig5_pressures_pollutants(summary_rows: list[dict], detail_rows: list[dict]) -> None:
    years = [int(row["data_year"]) for row in summary_rows]
    source_share = [float(row["surface_water_share_pct"] or 0) for row in summary_rows]
    width, height = 1400, 940
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 70, "Pollutants and pressure indicators in the lower basin", 30, "700", BLUE))
    pieces.append(text(70, 98, "Savannah Main annual reports provide the clearest modern pollutant-like slice currently available in the lower basin.", 14, "400", SLATE))

    band_x, band_y, band_w = 80, 150, 1240
    pieces.append(rect(band_x, band_y, band_w, 120, WHITE, SLATE_LIGHT, 18))
    pieces.append(text(band_x + 20, band_y + 30, "Source-water share from the Savannah River (%)", 16, "700", BLUE))
    max_share = max(source_share) if source_share else 1.0
    for index, row in enumerate(summary_rows):
        year = int(row["data_year"])
        share = float(row["surface_water_share_pct"] or 0)
        vx = band_x + 24 + index * 230
        pieces.append(text(vx + 60, band_y + 58, str(year), 11, "600", SLATE, "middle"))
        pieces.append(rect(vx, band_y + 72, 120, 16, SLATE_LIGHT, "none", 8))
        pieces.append(rect(vx, band_y + 72, 120 * share / max_share, 16, BLUE, "none", 8))
        pieces.append(text(vx + 130, band_y + 85, f"{share:.1f}%", 11, "700", BLUE))
        if int(row.get("violation_flag") or 0) == 1:
            draw_badge(pieces, vx, band_y + 96, "Violation", "#FEE2E2", RED)

    for index, (slug, title, color) in enumerate([("tthms", "TTHMs (ppb)", ORANGE), ("thaas", "THAAs (ppb)", PINK), ("nitrate", "Nitrate (ppm)", TEAL), ("lead", "Lead (ppb)", PURPLE)]):
        x, y = [(80, 330), (720, 330), (80, 620), (720, 620)][index]
        w, h = 560, 180
        pieces.append(rect(x - 18, y - 34, w + 36, h + 82, WHITE, SLATE_LIGHT, 18))
        pieces.append(text(x, y - 8, title, 16, "700", BLUE))
        series_rows, values = [], []
        for year in years:
            row = next((item for item in detail_rows if int(item["data_year"]) == year and item["parameter_slug"] == slug), None)
            value = None if row is None else to_float(row.get("amount_detected_value") or row.get("range_detected_max") or row.get("range_detected_min"))
            if value is not None:
                series_rows.append((year, value))
                values.append(value)
        top = max(values) if values else 1.0
        pieces.append(line(x, y + h, x + w, y + h, SLATE_LIGHT, 2))
        for i, year in enumerate(years):
            bx = x + 26 + i * 100
            pieces.append(text(bx + 22, y + h + 24, str(year), 11, "500", SLATE, "middle"))
            match = next((value for current_year, value in series_rows if current_year == year), None)
            if match is None:
                pieces.append(rect(bx, y + h - 6, 44, 6, SLATE_LIGHT, "none", 4))
                continue
            bar_h = max(10.0, (match / top) * (h - 26))
            by = y + h - bar_h
            pieces.append(rect(bx, by, 44, bar_h, color, "none", 8))
            pieces.append(text(bx + 22, by - 8, format_number(match, 1), 11, "700", color, "middle"))

    pieces.append("</svg>")
    save_svg("fig5_pressures_pollutants.svg", "".join(pieces))


def clean_fig6_flow_quality_coupling(correlation_rows: list[dict], bridge_rows: list[dict]) -> None:
    width, height = 1400, 620
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 70, "Flow-quality coupling inside the river", 30, "700", BLUE))
    pieces.append(text(70, 98, "These scatterplots summarize how lower-river quality responds when the mainstem at Augusta strengthens or weakens.", 14, "400", SLATE))

    for index, (target_slug, title, color) in enumerate([("dock_conductance_us_cm", "Flow vs conductance", ORANGE), ("dock_turbidity_fnu", "Flow vs turbidity", RED), ("dock_do_mg_l", "Flow vs dissolved oxygen", BLUE)]):
        x, y = [(80, 170), (480, 170), (880, 170)][index]
        w, h = 360, 280
        pieces.append(rect(x - 18, y - 36, w + 36, h + 92, WHITE, SLATE_LIGHT, 18))
        pieces.append(text(x, y - 8, title, 16, "700", BLUE))
        points = []
        for row in bridge_rows:
            x_val = to_float(row.get("augusta_flow_cfs", ""))
            y_val = to_float(row.get(target_slug, ""))
            if x_val is not None and y_val is not None:
                points.append((x_val, y_val))
        r_val = None
        for row in correlation_rows:
            if row["source_series_slug"] == "augusta_flow_cfs" and row["target_series_slug"] == target_slug:
                r_val = float(row["correlation"])
                break
        draw_scatter_panel(pieces, points, x, y + 18, w, h, color, BLUE, "Augusta discharge (ft³/s)", title.replace("Flow vs ", ""), r_val)

    pieces.append("</svg>")
    save_svg("fig6_flow_quality_coupling.svg", "".join(pieces))


def clean_fig7_sediment_texture_score(master_rows: list[dict], score_rows: list[dict]) -> None:
    width, height = 1400, 800
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 70, "Sediment texture and depositional score", 30, "700", BLUE))
    pieces.append(text(70, 98, "Once the river context is clear, the report closes on the site-level sediment response at Thurmond.", 14, "400", SLATE))
    master_sorted = sorted(master_rows, key=lambda r: int(float(r["site"])))
    plot_x, plot_y, bar_w, gap = 80, 180, 34, 6
    pieces.append(text(plot_x, 152, "Texture composition by site", 17, "700", BLUE))
    pieces.append(text(plot_x, 170, "Clay", 11, "700", TEAL))
    pieces.append(text(plot_x + 50, 170, "Silt", 11, "700", CYAN))
    pieces.append(text(plot_x + 94, 170, "Sand", 11, "700", ORANGE))
    for i, row in enumerate(master_sorted):
        site = int(float(row["site"]))
        x = plot_x + i * (bar_w + gap)
        clay = float(row.get("clay_pct") or 0)
        silt = float(row.get("silt_pct") or 0)
        sand = float(row.get("sand_pct") or 0)
        total = max(clay + silt + sand, 1.0)
        current_y = plot_y + 360
        for fraction, color in [(clay / total, TEAL), (silt / total, CYAN), (sand / total, ORANGE)]:
            sh = 340 * fraction
            pieces.append(rect(x, current_y - sh, bar_w, sh, color, "none", 3))
            current_y -= sh
        pieces.append(text(x + bar_w / 2, plot_y + 386, str(site), 10, "600", SLATE, "middle"))
    score_sorted = sorted(score_rows, key=lambda r: -float(r["fine_depositional_score"]))
    sx = 810
    pieces.append(text(sx, 152, "Fine-depositional score (ranked)", 17, "700", BLUE))
    max_score = max(abs(float(r["fine_depositional_score"])) for r in score_sorted) if score_sorted else 1.0
    zero_x = sx + 210
    scale_factor = 340 / (max_score * 2 if max_score else 1.0)
    for i, row in enumerate(score_sorted):
        score = float(row["fine_depositional_score"])
        y = 180 + i * 28
        width_bar = abs(score) * scale_factor
        bx = zero_x if score >= 0 else zero_x - width_bar
        pieces.append(text(sx, y + 16, f"Site {row['site']}", 11, "600", SLATE))
        pieces.append(rect(zero_x - 170, y + 2, 340, 18, "#F1F5F9", "none", 6))
        pieces.append(rect(bx, y + 2, max(width_bar, 2), 18, TEAL if score >= 0 else RED, "none", 6))
        pieces.append(text(zero_x + 176, y + 16, f"{score:.2f}", 11, "700", TEAL if score >= 0 else RED, "end"))
    pieces.append(line(zero_x, 175, zero_x, 175 + 19 * 28, SLATE_LIGHT, 1, "4 4"))
    pieces.append("</svg>")
    save_svg("fig7_sediment_texture_score.svg", "".join(pieces))


def clean_fig8_sediment_relations(master_rows: list[dict], pairwise_rows: list[dict]) -> None:
    pairwise_lookup = {(r["x_field"], r["y_field"]): float(r["correlation"]) for r in pairwise_rows}
    width, height = 1400, 760
    pieces = [svg_header(width, height), rect(0, 0, width, height, BACKGROUND)]
    pieces.append(text(70, 70, "Sediment geochemical relations that anchor the interpretation", 30, "700", BLUE))
    pieces.append(text(70, 98, "These are the cleanest sediment relations currently supporting the depositional reading at Thurmond.", 14, "400", SLATE))
    for index, (x_field, y_field, title, color) in enumerate([("clay_pct", "fe_ppm", "Clay vs Fe", TEAL), ("fe_ppm", "carbon_pct", "Fe vs carbon", BLUE), ("depth", "fe_ppm", "Depth vs Fe", PURPLE), ("d50", "fe_ppm", "D50 vs Fe", ORANGE)]):
        x, y = [(80, 170), (720, 170), (80, 470), (720, 470)][index]
        w, h = 560, 200
        pieces.append(rect(x - 18, y - 34, w + 36, h + 84, WHITE, SLATE_LIGHT, 18))
        pieces.append(text(x, y - 8, title, 16, "700", BLUE))
        points = []
        for row in master_rows:
            xv = to_float(row.get(x_field, ""))
            yv = to_float(row.get(y_field, ""))
            if xv is not None and yv is not None:
                points.append((xv, yv))
        draw_scatter_panel(pieces, points, x, y + 14, w, h, color, BLUE, x_field.replace("_", " "), y_field.replace("_", " "), pairwise_lookup.get((x_field, y_field)))
    pieces.append("</svg>")
    save_svg("fig8_sediment_relations.svg", "".join(pieces))


def main() -> None:
    ensure_dirs()

    monthly_rows = load_monthly_behavior()
    correlation_rows = load_correlations()
    bridge_rows = load_bridge()
    sediment_rows = load_sediment_master()
    score_rows = load_sediment_scores()
    pairwise_rows = load_sediment_pairwise()
    reservoir_monthly_rows = load_reservoir_operations_monthly()
    reservoir_summary_rows = load_reservoir_operation_summary()
    savannah_main_summary_rows = load_savannah_main_summary()
    savannah_main_long_rows = load_savannah_main_long()

    clean_fig1_river_mainstem_hydrograph(monthly_rows)
    print("fig1 done")
    clean_fig2_cascade_operations(reservoir_monthly_rows, reservoir_summary_rows)
    print("fig2 done")
    clean_fig3_thurmond_augusta_bridge(bridge_rows)
    print("fig3 done")
    clean_fig4_lower_river_quality(monthly_rows)
    print("fig4 done")
    clean_fig5_pressures_pollutants(savannah_main_summary_rows, savannah_main_long_rows)
    print("fig5 done")
    clean_fig6_flow_quality_coupling(correlation_rows, bridge_rows)
    print("fig6 done")
    clean_fig7_sediment_texture_score(sediment_rows, score_rows)
    print("fig7 done")
    clean_fig8_sediment_relations(sediment_rows, pairwise_rows)
    print("fig8 done")
    print(f"\nActive report figures written to {DOCS_FIG_DIR}")


if __name__ == "__main__":
    main()
