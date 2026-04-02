"""
EDA — J. Strom Thurmond Dam (Clarks Hill Lake) Operations
Sources: USACE SAS water portal (timeseries JSON), NID GA01701
Figures: 300 dpi PNGs for HTML report
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
COLLECTION = ROOT / "data" / "runs" / "operational-collect-clarkshill-20260401-225924" / "collection"
USACE_DIR = COLLECTION / "water-usace-thurmond-location"
NID_FILE = COLLECTION / "nid-usace-ga01701" / "inventory_GA01701.json"
FIG_DIR = Path(__file__).resolve().parent / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# ── Project palette ───────────────────────────────────────────────────────────
GSU_BLUE = "#011E42"
GSU_GOLD = "#87714D"
GSU_GOLD_LIGHT = "#C4A86C"
ACCENT_TEAL = "#0F7B5F"
ACCENT_RED = "#B91C1C"
SLATE = "#64748b"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})


# ── Loaders ───────────────────────────────────────────────────────────────────
_SENTINEL = -9.0e18  # USACE uses INT64_MIN as missing marker


def load_ts(filename: str) -> pd.Series:
    path = USACE_DIR / filename
    d = json.loads(path.read_text(encoding="utf-8"))
    rows = d.get("values", [])
    unit = d.get("unit", "")
    s = pd.Series(
        {pd.Timestamp(ts): val for ts, val in rows if val is not None and val > _SENTINEL},
        name=unit,
    )
    s.index = pd.to_datetime(s.index, utc=True).tz_convert("America/New_York")
    return s


def load_nid() -> dict:
    return json.loads(NID_FILE.read_text(encoding="utf-8"))


# ── Helpers ───────────────────────────────────────────────────────────────────
def date_fmt(ax, freq="W"):
    locator = mdates.WeekdayLocator(byweekday=mdates.MO) if freq == "W" else mdates.DayLocator(interval=3)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")


def add_watermark(fig):
    fig.text(
        0.99, 0.01, "Project FREnTE · GSU / SENAI · 2026",
        ha="right", va="bottom", fontsize=7, color="#94a3b8",
    )


def save(fig, name: str):
    path = FIG_DIR / name
    fig.savefig(path)
    print(f"  saved: {path.name}")
    plt.close(fig)


# ── FIG 1 — Pool elevation + storage ─────────────────────────────────────────
def fig1_elevation_storage():
    elev = load_ts("timeseries_pool_elevation_02193900.json").resample("1h").mean()
    stor = load_ts("timeseries_storage_thurmond.json")

    # align to common daily index
    df = pd.DataFrame({"elev_ft": elev, "storage_kac_ft": stor / 1_000}).resample("1D").mean().dropna()

    fig, ax1 = plt.subplots(figsize=(11, 4))
    ax2 = ax1.twinx()

    ax1.fill_between(df.index, df["elev_ft"], alpha=0.15, color=GSU_BLUE)
    ax1.plot(df.index, df["elev_ft"], color=GSU_BLUE, lw=1.8, label="Pool elevation (ft)")
    ax2.plot(df.index, df["storage_kac_ft"], color=GSU_GOLD, lw=1.5, ls="--", label="Storage (k ac-ft)")

    # reference lines
    full_pool_ft = 330.0
    ax1.axhline(full_pool_ft, color=ACCENT_TEAL, lw=0.9, ls=":", alpha=0.7)
    ax1.text(df.index[2], full_pool_ft + 0.3, "Full pool 330 ft", fontsize=7.5, color=ACCENT_TEAL)

    ax1.set_ylabel("Pool elevation (ft NGVD)", color=GSU_BLUE)
    ax2.set_ylabel("Storage (× 1,000 ac-ft)", color=GSU_GOLD)
    ax1.tick_params(axis="y", colors=GSU_BLUE)
    ax2.tick_params(axis="y", colors=GSU_GOLD)

    date_fmt(ax1)
    ax1.set_title("J. Strom Thurmond Lake — Pool Elevation & Storage\nMarch 2026", fontweight="bold", color=GSU_BLUE)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc="upper right")

    ax1.grid(axis="y", ls="--", lw=0.5, alpha=0.4)
    add_watermark(fig)
    save(fig, "fig1_elevation_storage.png")


# ── FIG 2 — Inflow vs outflow hydrograph ─────────────────────────────────────
def fig2_inflow_outflow():
    inflow = load_ts("timeseries_inflow_thurmond.json")
    outflow = load_ts("timeseries_outflow_thurmond.json")

    df = pd.DataFrame({"inflow": inflow, "outflow": outflow}).resample("6h").mean().dropna()
    df["net"] = df["inflow"] - df["outflow"]

    fig, axes = plt.subplots(2, 1, figsize=(11, 6), sharex=True, gridspec_kw={"height_ratios": [3, 1.2]})

    ax = axes[0]
    ax.plot(df.index, df["inflow"], color=ACCENT_TEAL, lw=1.6, label="Inflow")
    ax.plot(df.index, df["outflow"], color=GSU_BLUE, lw=1.6, label="Outflow")
    ax.fill_between(df.index, df["inflow"], df["outflow"],
                    where=df["inflow"] >= df["outflow"], alpha=0.12, color=ACCENT_TEAL, label="Net gain")
    ax.fill_between(df.index, df["inflow"], df["outflow"],
                    where=df["inflow"] < df["outflow"], alpha=0.12, color=ACCENT_RED, label="Net release")
    ax.set_ylabel("Flow (cfs)")
    ax.legend(fontsize=8, ncols=4, loc="upper right")
    ax.set_title("Inflow vs. Outflow — J. Strom Thurmond Dam\nMarch 1 – April 1, 2026 (6-h means)", fontweight="bold", color=GSU_BLUE)
    ax.grid(axis="y", ls="--", lw=0.5, alpha=0.4)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

    ax2 = axes[1]
    colors_net = [ACCENT_TEAL if v >= 0 else ACCENT_RED for v in df["net"]]
    ax2.bar(df.index, df["net"], width=0.22, color=colors_net, alpha=0.75)
    ax2.axhline(0, color=SLATE, lw=0.8)
    ax2.set_ylabel("Net (cfs)")
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax2.grid(axis="y", ls="--", lw=0.5, alpha=0.4)
    date_fmt(ax2)

    add_watermark(fig)
    fig.tight_layout()
    save(fig, "fig2_inflow_outflow.png")


# ── FIG 3 — Estimated residence time ─────────────────────────────────────────
def fig3_residence_time():
    stor = load_ts("timeseries_storage_thurmond.json")
    outflow = load_ts("timeseries_outflow_thurmond.json")

    # daily means; outflow in cfs → ac-ft/day (1 cfs = 1.9835 ac-ft/day)
    df = pd.DataFrame({"storage_ac_ft": stor, "outflow_cfs": outflow}).resample("1D").mean().dropna()
    df["outflow_ac_ft_day"] = df["outflow_cfs"] * 1.9835
    df["residence_days"] = df["storage_ac_ft"] / df["outflow_ac_ft_day"]
    df = df[df["residence_days"].between(1, 2000)]  # sanity clip

    fig, ax = plt.subplots(figsize=(11, 4))
    ax.fill_between(df.index, df["residence_days"], alpha=0.15, color=GSU_GOLD)
    ax.plot(df.index, df["residence_days"], color=GSU_GOLD, lw=2)

    median_rt = df["residence_days"].median()
    ax.axhline(median_rt, color=GSU_BLUE, lw=0.9, ls="--")
    ax.text(df.index[2], median_rt + 8, f"Median {median_rt:.0f} d", fontsize=8, color=GSU_BLUE)

    ax.set_ylabel("Estimated residence time (days)")
    ax.set_title("Estimated Residence Time — J. Strom Thurmond Lake\n(Storage ÷ Daily outflow, March 2026)", fontweight="bold", color=GSU_BLUE)
    ax.grid(axis="y", ls="--", lw=0.5, alpha=0.4)
    date_fmt(ax)

    add_watermark(fig)
    save(fig, "fig3_residence_time.png")


# ── FIG 4 — Tailwater & dam context ──────────────────────────────────────────
def fig4_tailwater_context():
    pool = load_ts("timeseries_pool_elevation_02193900.json").resample("1h").mean()
    tail = load_ts("timeseries_tailwater_thurmond.json")

    df = pd.DataFrame({"pool_ft": pool, "tailwater_ft": tail}).resample("6h").mean().dropna()
    df["head_ft"] = df["pool_ft"] - df["tailwater_ft"]

    nid = load_nid()
    dam_height = nid.get("hydraulicHeight", 170)

    fig, axes = plt.subplots(2, 1, figsize=(11, 6), sharex=True, gridspec_kw={"height_ratios": [2, 1.5]})

    ax = axes[0]
    ax.plot(df.index, df["pool_ft"], color=GSU_BLUE, lw=1.8, label="Pool elevation")
    ax.plot(df.index, df["tailwater_ft"], color=ACCENT_TEAL, lw=1.4, ls="--", label="Tailwater elevation")
    ax.fill_between(df.index, df["tailwater_ft"], df["pool_ft"], alpha=0.1, color=GSU_BLUE)
    ax.set_ylabel("Elevation (ft NGVD)")
    ax.legend(fontsize=8)
    ax.set_title(
        f"Pool vs. Tailwater Elevation — J. Strom Thurmond Dam\n"
        f"NID: hydraulic height {dam_height} ft, max storage 3,820,000 ac-ft",
        fontweight="bold", color=GSU_BLUE,
    )
    ax.grid(axis="y", ls="--", lw=0.5, alpha=0.4)

    ax2 = axes[1]
    ax2.fill_between(df.index, df["head_ft"], alpha=0.18, color=GSU_GOLD)
    ax2.plot(df.index, df["head_ft"], color=GSU_GOLD, lw=1.6)
    ax2.set_ylabel("Hydraulic head (ft)")
    ax2.set_title("Operating head across dam", fontsize=9, color=SLATE)
    ax2.grid(axis="y", ls="--", lw=0.5, alpha=0.4)
    date_fmt(ax2)

    add_watermark(fig)
    fig.tight_layout()
    save(fig, "fig4_tailwater_context.png")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating Clarks Hill EDA figures...")
    fig1_elevation_storage()
    fig2_inflow_outflow()
    fig3_residence_time()
    fig4_tailwater_context()
    print(f"Done. Figures saved to: {FIG_DIR}")
