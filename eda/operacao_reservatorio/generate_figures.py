"""
EDA — Operação dos Reservatórios do Tietê em Cascata (ONS, 2000-2025)
Fonte: dados.ons.org.br/dataset/dados-hidrologicos-res
Figuras para artigo científico (300 dpi)
"""

from __future__ import annotations

import io
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import requests

warnings.filterwarnings("ignore")

# ── Configuração ──────────────────────────────────────────────────────────────
RAW_DIR    = Path(__file__).resolve().parents[2] / "data" / "raw" / "operacao_reservatorio"
STAGING    = Path(__file__).resolve().parents[2] / "data" / "staging" / "operacao_reservatorio"
FIG_DIR    = Path(__file__).resolve().parent / "figures"

RAW_DIR.mkdir(parents=True, exist_ok=True)
STAGING.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

RESERVATORIOS_TIETE = {
    "B. BONITA":      "Barra Bonita",
    "BARIRI":         "Bariri",
    "IBITINGA":       "Ibitinga",
    "PROMISSÃO":      "Promissão",
    "N. AVANHANDAVA": "Nova Avanhandava",
    "TRÊS IRMÃOS":    "Três Irmãos",
}

CASCADE_ORDER = ["B. BONITA", "BARIRI", "IBITINGA", "PROMISSÃO", "N. AVANHANDAVA", "TRÊS IRMÃOS"]

COLORS = {
    "B. BONITA":      "#011E42",
    "BARIRI":         "#1B4F8A",
    "IBITINGA":       "#2E7FC4",
    "PROMISSÃO":      "#5BA0D0",
    "N. AVANHANDAVA": "#87714D",
    "TRÊS IRMÃOS":    "#C4A86C",
}

ANOS = range(2000, 2026)

ONS_BASE = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/dados_hidrologicos_di/DADOS_HIDROLOGICOS_RES_{year}.parquet"

plt.rcParams.update({
    "font.family":    "DejaVu Sans",
    "font.size":      10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8,
    "figure.dpi":     150,
    "axes.spines.top":   False,
    "axes.spines.right": False,
})


# ── 1. Download ───────────────────────────────────────────────────────────────
def download_ons() -> pd.DataFrame:
    frames = []
    for year in ANOS:
        cache = RAW_DIR / f"ons_hidro_{year}.parquet"
        if cache.exists():
            df = pd.read_parquet(cache)
        else:
            url = ONS_BASE.format(year=year)
            print(f"  Baixando {year}...", end=" ", flush=True)
            try:
                r = requests.get(url, timeout=60)
                r.raise_for_status()
                df = pd.read_parquet(io.BytesIO(r.content))
                df.to_parquet(cache)
                print("ok")
            except Exception as e:
                print(f"erro: {e}")
                continue
        frames.append(df)

    return pd.concat(frames, ignore_index=True)


# ── 2. Staging ────────────────────────────────────────────────────────────────
def prepare_staging(df: pd.DataFrame) -> pd.DataFrame:
    tiete = df[df["nom_bacia"].str.upper().str.contains("TIET", na=False)].copy()
    tiete = tiete[tiete["nom_reservatorio"].isin(RESERVATORIOS_TIETE.keys())]

    tiete["data"] = pd.to_datetime(tiete["din_instante"])
    tiete["ano"]  = tiete["data"].dt.year
    tiete["mes"]  = tiete["data"].dt.month
    tiete["ano_mes"] = tiete["data"].dt.to_period("M")

    # Volume útil disponível em hm³ (usar nivelmontante como proxy de cota quando volumeutilcon falhar)
    tiete["vol_util_pct"] = pd.to_numeric(tiete["val_volumeutilcon"], errors="coerce")

    # Tempo de residência (dias) = Volume_armazenado / Defluente
    # ONS fornece vazão em m³/s; vol_util_pct é %, convertemos com capacidade máx aproximada por UHE
    cap_max_hm3 = {
        "B. BONITA": 3622, "BARIRI": 591, "IBITINGA": 1028,
        "PROMISSÃO": 7408, "N. AVANHANDAVA": 4950, "TRÊS IRMÃOS": 17029,
    }
    tiete["cap_max_hm3"] = pd.to_numeric(tiete["nom_reservatorio"].map(cap_max_hm3), errors="coerce")
    tiete["vol_armazenado_hm3"] = pd.to_numeric(tiete["vol_util_pct"], errors="coerce") / 100.0 * tiete["cap_max_hm3"]
    tiete["def_m3s"] = pd.to_numeric(tiete["val_vazaodefluente"], errors="coerce").replace(0, np.nan)
    tiete["val_vazaoafluente"] = pd.to_numeric(tiete["val_vazaoafluente"], errors="coerce")
    tiete["tempo_residencia_dias"] = (
        (tiete["vol_armazenado_hm3"] * 1e6) / (tiete["def_m3s"] * 86400)
    )

    # Forçar tipos numéricos em todas as colunas val_*
    for col in tiete.columns:
        if col.startswith("val_") or col in ("num_ordemcs", "cod_usina"):
            tiete[col] = pd.to_numeric(tiete[col], errors="coerce")

    path = STAGING / "operacao_reservatorio_dia.parquet"
    tiete.to_parquet(path)
    print(f"  Staging salvo: {path}")
    return tiete


# ── 3. Figuras ────────────────────────────────────────────────────────────────

def fig1_volume_cascata(df: pd.DataFrame) -> None:
    """Fig 1 — Volume útil (%) em cascata, série mensal 2000-2025"""
    mensal = (
        df.groupby(["nom_reservatorio", "ano_mes"])["vol_util_pct"]
        .mean()
        .reset_index()
    )
    mensal["data"] = mensal["ano_mes"].dt.to_timestamp()

    fig, axes = plt.subplots(6, 1, figsize=(12, 14), sharex=True)
    fig.suptitle(
        "Volume Útil dos Reservatórios do Rio Tietê — Cascata (2000–2025)\nFonte: ONS Dados Abertos",
        fontsize=12, fontweight="bold", y=0.98,
    )

    for ax, res in zip(axes, CASCADE_ORDER):
        sub = mensal[mensal["nom_reservatorio"] == res].sort_values("data")
        if sub.empty:
            ax.set_visible(False)
            continue
        ax.fill_between(sub["data"], sub["vol_util_pct"], alpha=0.3, color=COLORS[res])
        ax.plot(sub["data"], sub["vol_util_pct"], color=COLORS[res], linewidth=0.9)
        ax.axhline(20, color="red", linewidth=0.7, linestyle="--", alpha=0.6, label="Crítico 20%")
        ax.set_ylabel("%", fontsize=8)
        ax.set_ylim(0, 110)
        ax.yaxis.set_major_locator(mticker.MultipleLocator(25))
        ax.set_title(RESERVATORIOS_TIETE.get(res, res), loc="left", fontsize=9, fontweight="bold")

        # Destaque 2014-2015 (crise hídrica)
        ax.axvspan(pd.Timestamp("2014-01-01"), pd.Timestamp("2016-01-01"),
                   alpha=0.08, color="orange", label="Crise hídrica 2014-15")
        if ax == axes[0]:
            ax.legend(loc="upper right", fontsize=7)

    axes[-1].xaxis.set_major_locator(plt.matplotlib.dates.YearLocator(2))
    axes[-1].xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%Y"))
    plt.setp(axes[-1].xaxis.get_majorticklabels(), rotation=45, ha="right")
    fig.text(0.5, 0.01, "Ano", ha="center", fontsize=10)

    fig.tight_layout(rect=[0, 0.02, 1, 0.97])
    path = FIG_DIR / "fig1_volume_cascata.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    print(f"  Fig 1 salva: {path}")
    plt.close(fig)


def fig2_vazao_cabeceira_foz(df: pd.DataFrame) -> None:
    """Fig 2 — Vazão afluente: cabeceira (Barra Bonita) vs foz (Três Irmãos)"""
    mensal = (
        df.groupby(["nom_reservatorio", "ano_mes"])["val_vazaoafluente"]
        .mean()
        .reset_index()
    )
    mensal["data"] = mensal["ano_mes"].dt.to_timestamp()

    pares = [("B. BONITA", "Barra Bonita"), ("TRÊS IRMÃOS", "Três Irmãos")]
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    fig.suptitle(
        "Vazão Afluente — Cabeceira vs Foz da Cascata do Rio Tietê (2000–2025)\nFonte: ONS Dados Abertos",
        fontsize=12, fontweight="bold",
    )

    for ax, (res, label) in zip(axes, pares):
        sub = mensal[mensal["nom_reservatorio"] == res].sort_values("data")
        if sub.empty:
            ax.set_visible(False)
            continue
        # Média móvel 12 meses
        sub = sub.set_index("data")
        sub["ma12"] = sub["val_vazaoafluente"].rolling(12, min_periods=6).mean()
        ax.fill_between(sub.index, sub["val_vazaoafluente"], alpha=0.2, color=COLORS[res])
        ax.plot(sub.index, sub["val_vazaoafluente"], color=COLORS[res], linewidth=0.7, alpha=0.5, label="Mensal")
        ax.plot(sub.index, sub["ma12"], color=COLORS[res], linewidth=2.0, label="Média móvel 12 meses")
        ax.set_ylabel("Vazão (m³/s)", fontsize=9)
        ax.set_title(label, loc="left", fontsize=10, fontweight="bold")
        ax.legend(loc="upper right", fontsize=8)
        ax.axvspan(pd.Timestamp("2014-01-01"), pd.Timestamp("2016-01-01"),
                   alpha=0.08, color="orange")

    axes[-1].xaxis.set_major_locator(plt.matplotlib.dates.YearLocator(2))
    axes[-1].xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%Y"))
    plt.setp(axes[-1].xaxis.get_majorticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    path = FIG_DIR / "fig2_vazao_cabeceira_foz.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    print(f"  Fig 2 salva: {path}")
    plt.close(fig)


def fig3_tempo_residencia(df: pd.DataFrame) -> None:
    """Fig 3 — Tempo de residência estimado por reservatório (mensal, 2000-2025)"""
    mensal = (
        df.groupby(["nom_reservatorio", "ano_mes"])["tempo_residencia_dias"]
        .median()
        .reset_index()
    )
    mensal["data"] = mensal["ano_mes"].dt.to_timestamp()
    mensal = mensal[mensal["tempo_residencia_dias"].between(1, 1000)]

    fig, axes = plt.subplots(3, 2, figsize=(14, 10), sharex=True)
    axes_flat = axes.flatten()
    fig.suptitle(
        "Tempo de Residência Estimado — Reservatórios do Tietê (2000–2025)\n"
        "TR = Volume armazenado / Vazão defluente   |   Fonte: ONS Dados Abertos",
        fontsize=11, fontweight="bold",
    )

    for ax, res in zip(axes_flat, CASCADE_ORDER):
        sub = mensal[mensal["nom_reservatorio"] == res].sort_values("data")
        if sub.empty:
            ax.set_visible(False)
            continue
        ax.fill_between(sub["data"], sub["tempo_residencia_dias"], alpha=0.25, color=COLORS[res])
        ax.plot(sub["data"], sub["tempo_residencia_dias"], color=COLORS[res], linewidth=0.9)
        ax.axhline(180, color="red", linewidth=0.8, linestyle="--", alpha=0.7, label="TR 180 dias")
        ax.set_ylabel("TR (dias)", fontsize=8)
        ax.set_title(RESERVATORIOS_TIETE.get(res, res), loc="left", fontsize=9, fontweight="bold")
        ax.set_ylim(bottom=0)
        ax.legend(loc="upper right", fontsize=7)

    for ax in axes_flat:
        ax.xaxis.set_major_locator(plt.matplotlib.dates.YearLocator(4))
        ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%Y"))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    fig.tight_layout()
    path = FIG_DIR / "fig3_tempo_residencia.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    print(f"  Fig 3 salva: {path}")
    plt.close(fig)


def fig4_correlacao_volume_tr(df: pd.DataFrame) -> None:
    """Fig 4 — Correlação Volume Útil (%) × Tempo de Residência por reservatório"""
    sub = df[
        df["tempo_residencia_dias"].between(1, 1000) &
        df["vol_util_pct"].between(0, 100)
    ].copy()

    fig, axes = plt.subplots(2, 3, figsize=(13, 8))
    axes_flat = axes.flatten()
    fig.suptitle(
        "Correlação Volume Útil × Tempo de Residência — Reservatórios do Tietê\nFonte: ONS Dados Abertos",
        fontsize=11, fontweight="bold",
    )

    for ax, res in zip(axes_flat, CASCADE_ORDER):
        s = sub[sub["nom_reservatorio"] == res]
        if s.empty:
            ax.set_visible(False)
            continue
        ax.scatter(s["vol_util_pct"], s["tempo_residencia_dias"],
                   alpha=0.12, s=4, color=COLORS[res])
        # Linha de regressão
        m, b = np.polyfit(s["vol_util_pct"].fillna(0), s["tempo_residencia_dias"].fillna(0), 1)
        x_line = np.linspace(0, 100, 100)
        ax.plot(x_line, m * x_line + b, color=COLORS[res], linewidth=2)
        r = s[["vol_util_pct", "tempo_residencia_dias"]].dropna().corr().iloc[0, 1]
        ax.set_title(f"{RESERVATORIOS_TIETE.get(res, res)}\nr = {r:.2f}", fontsize=9, fontweight="bold")
        ax.set_xlabel("Volume útil (%)", fontsize=8)
        ax.set_ylabel("TR (dias)", fontsize=8)
        ax.set_xlim(0, 105)
        ax.set_ylim(bottom=0)

    fig.tight_layout()
    path = FIG_DIR / "fig4_correlacao_vol_tr.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    print(f"  Fig 4 salva: {path}")
    plt.close(fig)


def fig5_anomalia_anual(df: pd.DataFrame) -> None:
    """Fig 5 — Anomalia anual de volume em relação à média histórica (2000-2025)"""
    anual = (
        df.groupby(["nom_reservatorio", "ano"])["vol_util_pct"]
        .mean()
        .reset_index()
    )
    media_hist = anual.groupby("nom_reservatorio")["vol_util_pct"].mean()
    anual["anomalia"] = anual.apply(
        lambda row: row["vol_util_pct"] - media_hist[row["nom_reservatorio"]], axis=1
    )

    fig, ax = plt.subplots(figsize=(13, 6))
    fig.suptitle(
        "Anomalia Anual de Volume Útil — Reservatórios do Tietê (2000–2025)\n"
        "Referência: média histórica do período   |   Fonte: ONS Dados Abertos",
        fontsize=11, fontweight="bold",
    )

    x = np.arange(len(anual["ano"].unique()))
    anos = sorted(anual["ano"].unique())
    width = 0.14

    for i, res in enumerate(CASCADE_ORDER):
        sub = anual[anual["nom_reservatorio"] == res].set_index("ano").reindex(anos)
        bars = ax.bar(x + i * width, sub["anomalia"].values,
                      width=width, color=COLORS[res], label=RESERVATORIOS_TIETE.get(res, res), alpha=0.85)

    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x + width * 2.5)
    ax.set_xticklabels(anos, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Anomalia de volume útil (p.p.)", fontsize=9)
    ax.legend(ncol=3, fontsize=8, loc="upper right")

    fig.tight_layout()
    path = FIG_DIR / "fig5_anomalia_anual.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    print(f"  Fig 5 salva: {path}")
    plt.close(fig)


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Download ONS 2000-2025 ===")
    raw = download_ons()
    print(f"  Total linhas brutas: {len(raw):,}")

    print("\n=== Staging ===")
    df = prepare_staging(raw)
    print(f"  Tietê — linhas: {len(df):,} | reservatórios: {df['nom_reservatorio'].nunique()}")
    print(f"  Reservatórios: {df['nom_reservatorio'].unique().tolist()}")
    print(f"  Periodo: {df['data'].min().date()} a {df['data'].max().date()}")

    print("\n=== Gerando figuras ===")
    fig1_volume_cascata(df)
    fig2_vazao_cabeceira_foz(df)
    fig3_tempo_residencia(df)
    fig4_correlacao_volume_tr(df)
    fig5_anomalia_anual(df)

    print(f"\nFiguras salvas em: {FIG_DIR}")
