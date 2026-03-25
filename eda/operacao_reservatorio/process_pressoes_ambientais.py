"""
Processa dados de pressões ambientais na bacia do Tietê:
  - BDQueimadas → focos de calor 2000-2024
  - SNIS        → cobertura de coleta e tratamento de esgoto 2010-2021
  - Resíduos CETESB → IQR médio SP 2017-2021

Gera figuras para apresentacao_reservatorios.html
"""

import io
import re
import zipfile
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import pdfplumber
import xlrd

# ── caminhos ────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).resolve().parents[2]
RUNS      = ROOT / "data" / "runs"
STAGING   = ROOT / "data" / "staging"
ANALYTIC  = ROOT / "data" / "analytic" / "reservatorio_ano"
FIG_DIR   = Path(__file__).resolve().parent / "figures"

QUEIMADAS_RUN = RUNS / "operational-collect-b02cd324" / "collection" / "queimadas"
SNIS_RUN      = RUNS / "operational-collect-3c21e5fc"  / "collection" / "snis" / "attachments"
RESIDUOS_RUN  = RUNS / "operational-collect-4ccc1200"  / "collection" / "residuos" / "downloads"

for d in [STAGING / "queimadas", STAGING / "snis", STAGING / "residuos", ANALYTIC, FIG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── estilo visual idêntico ao relatorio_100k ─────────────────────────────────
GSU_BLUE  = "#011E42"
GSU_GOLD  = "#87714D"
GOLD_LITE = "#C4A86C"
RED_CRISE = "#C75D2C"
BLUE_ACC  = "#1B75BB"
GREEN_ACC = "#0F7B5F"
PURPLE    = "#6B48A8"

plt.rcParams.update({
    "font.family":       "serif",
    "font.serif":        ["Georgia", "Times New Roman", "DejaVu Serif"],
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.color":        "#e2e8f0",
    "grid.linewidth":    0.6,
    "figure.dpi":        150,
    "savefig.dpi":       300,
    "savefig.bbox":      "tight",
})


# ═══════════════════════════════════════════════════════════════════════════
# 1. BDQUEIMADAS
# ═══════════════════════════════════════════════════════════════════════════
print("\n=== BDQueimadas ===")

dfs = []
for csv_file in sorted(QUEIMADAS_RUN.glob("focos_*.csv")):
    try:
        df = pd.read_csv(csv_file, encoding="latin-1", low_memory=False)
        # normaliza coluna de data
        date_col = next((c for c in df.columns if "data" in c.lower()), None)
        if date_col:
            df["data"] = pd.to_datetime(df[date_col], errors="coerce")
        dfs.append(df)
    except Exception as e:
        print(f"  AVISO {csv_file.name}: {e}")

queimadas_raw = pd.concat(dfs, ignore_index=True)
queimadas_raw["ano"] = queimadas_raw["data"].dt.year
print(f"  Total focos: {len(queimadas_raw):,} | anos: {queimadas_raw['ano'].min()}-{queimadas_raw['ano'].max()}")

# staging
queimadas_staging = queimadas_raw[["data", "ano", "municipio", "estado", "bioma",
                                    "latitude", "longitude",
                                    "frp", "numero_dias_sem_chuva", "risco_fogo"]].copy()
queimadas_staging.to_parquet(STAGING / "queimadas" / "focos_calor_evento.parquet", index=False)

# analytic: por ano
q_ano = (
    queimadas_raw.groupby("ano")
    .agg(n_focos=("data", "count"),
         frp_medio=("frp", "mean"),
         dias_sem_chuva_medio=("numero_dias_sem_chuva", "mean"))
    .reset_index()
)
# por ano × bioma
q_bioma = (
    queimadas_raw.groupby(["ano", "bioma"])
    .size().reset_index(name="n_focos")
)
q_ano.to_parquet(ANALYTIC / "queimadas_reservatorio_ano.parquet", index=False)
print(f"  Analytic salvo: {ANALYTIC / 'queimadas_reservatorio_ano.parquet'}")


# ═══════════════════════════════════════════════════════════════════════════
# 2. SNIS
# ═══════════════════════════════════════════════════════════════════════════
print("\n=== SNIS ===")

YEARS_SNIS = list(range(2010, 2022))


def _extract_from_wb(wb: "xlrd.Book", year: int) -> list:
    """Extrai IN015 e IN046 para municípios SP de um workbook xlrd."""
    rows = []
    for sh in [wb.sheets()[0]] if wb.nsheets == 1 else wb.sheets():
        if sh.nrows < 12:
            continue
        # Detecta formato: row 8 = códigos (multi-sheet) ou row 7 = nomes (flat)
        row8 = [str(sh.cell(8, j).value) for j in range(sh.ncols)]
        row7 = [str(sh.cell(7, j).value).lower() for j in range(sh.ncols)]

        # Formato multi-sheet: códigos IN015/IN046 na row 8
        if any("IN015" in v for v in row8):
            col_in015 = next((j for j, v in enumerate(row8) if "IN015" in v), None)
            col_in046 = next((j for j, v in enumerate(row8) if "IN046" in v), None)
            data_start = 9
        # Formato flat: nomes longos na row 7
        elif any("coleta de esgoto" in h for h in row7):
            col_in015 = next((j for j, h in enumerate(row7) if "coleta de esgoto" in h), None)
            col_in046 = next((j for j, h in enumerate(row7) if "tratado referido" in h), None)
            data_start = 10
        else:
            continue

        for i in range(data_start, sh.nrows):
            v_uf = str(sh.cell(i, 2).value).strip()
            if v_uf != "SP":
                continue
            def _val(j):
                if j is None:
                    return np.nan
                v = sh.cell(i, j).value
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return np.nan
            cod_raw = sh.cell(i, 0).value
            try:
                cod = str(int(float(cod_raw)))
            except (TypeError, ValueError):
                cod = str(cod_raw)
            rows.append({
                "cod_ibge":  cod,
                "municipio": str(sh.cell(i, 1).value),
                "uf":        v_uf,
                "in015":     _val(col_in015),
                "in046":     _val(col_in046),
                "ano":       year,
            })
        if rows:
            break  # achou no primeiro sheet com dados
    return rows


def _read_snis_year(year: int):
    """Retorna DataFrame com colunas [cod_municipio, municipio, uf, in015, in046] para o ano."""
    year_dir = SNIS_RUN / str(year)
    if not year_dir.exists():
        return None

    # --- formato 2010-2019: zip individual ---
    zip_old = year_dir / f"Planilhas_AE{year}_Completa_LPU.zip"
    if zip_old.exists():
        try:
            with zipfile.ZipFile(zip_old) as z:
                # busca case-insensitive pelo arquivo de indicadores
                xls_name = next(
                    n for n in z.namelist()
                    if "indicadores" in n.lower() and n.lower().endswith(".xls")
                )
                with z.open(xls_name) as f:
                    wb = xlrd.open_workbook(file_contents=f.read())
                    rows = _extract_from_wb(wb, year)
                    return pd.DataFrame(rows) if rows else None
        except Exception as e:
            print(f"  AVISO {year} (old fmt): {e}")

    # --- formato 2020-2021: bundle zip ---
    zip_bundle = year_dir / f"Planilhas_AE{year}.zip"
    if zip_bundle.exists():
        try:
            with zipfile.ZipFile(zip_bundle) as z1:
                inner_name = next(n for n in z1.namelist() if "LPU" in n and n.endswith(".zip"))
                with z1.open(inner_name) as ib:
                    with zipfile.ZipFile(io.BytesIO(ib.read())) as z2:
                        xls_name = next(
                            n for n in z2.namelist()
                            if "indicadores" in n.lower() and n.lower().endswith(".xls")
                        )
                        with z2.open(xls_name) as f:
                            wb = xlrd.open_workbook(file_contents=f.read())
                            rows = _extract_from_wb(wb, year)
                            return pd.DataFrame(rows) if rows else None
        except Exception as e:
            print(f"  AVISO {year} (bundle fmt): {e}")

    return None


snis_dfs = []
for yr in YEARS_SNIS:
    df_yr = _read_snis_year(yr)
    if df_yr is not None and len(df_yr) > 0:
        snis_dfs.append(df_yr)
        print(f"  {yr}: {len(df_yr)} municípios SP | "
              f"IN015 med={df_yr['in015'].median():.1f}% | "
              f"IN046 med={df_yr['in046'].median():.1f}%")
    else:
        print(f"  {yr}: sem dados")

if snis_dfs:
    snis_staging = pd.concat(snis_dfs, ignore_index=True)
    snis_staging.to_parquet(STAGING / "snis" / "snis_municipios_serie.parquet", index=False)

    snis_ano = (
        snis_staging.groupby("ano")
        .agg(
            in015_mediana=("in015", "median"),
            in015_media=("in015", "mean"),
            in046_mediana=("in046", "median"),
            in046_media=("in046", "mean"),
            n_municipios=("cod_ibge", "count"),
        )
        .reset_index()
    )
    snis_ano.to_parquet(ANALYTIC / "snis_reservatorio_ano.parquet", index=False)
    print(f"  Analytic salvo")
else:
    snis_ano = pd.DataFrame()
    print("  Nenhum dado SNIS extraído")


# ═══════════════════════════════════════════════════════════════════════════
# 3. RESÍDUOS CETESB
# ═══════════════════════════════════════════════════════════════════════════
print("\n=== Resíduos CETESB ===")

# UGRHIs da bacia do Tietê: 5 (PCJ), 10 (Sorocaba/Médio Tietê),
#   13 (Tietê/Jacaré), 16 (Tietê/Batalha), 17 (Médio Paranapanema),
#   19 (Baixo Tietê)
TIETE_UGRHIS = {"5", "10", "13", "16", "19"}


def _extract_iqr_pdf(pdf_path: Path, year: int) -> pd.DataFrame:
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row or len(row) < 5:
                        continue
                    # colunas: ENQUADRAMENTO, #, MUNICIPIO, AGENCIA, UGRHI, IQR, DISPÕE_EM
                    municipio = row[2] if len(row) > 2 else None
                    ugrhi_raw = row[4] if len(row) > 4 else None
                    iqr_raw   = row[5] if len(row) > 5 else None
                    if not municipio or municipio in ("MUNICÍPIO", "Munic\xedpio", None):
                        continue
                    # limpa IQR
                    iqr_str = str(iqr_raw or "").replace(",", ".").strip()
                    try:
                        iqr = float(iqr_str)
                    except ValueError:
                        continue
                    ugrhi = str(ugrhi_raw or "").strip()
                    rows.append({
                        "municipio": str(municipio).strip(),
                        "ugrhi":     ugrhi,
                        "iqr":       iqr,
                        "ano":       year,
                        "tiete":     ugrhi in TIETE_UGRHIS,
                    })
    return pd.DataFrame(rows)


residuos_dfs = []
for pdf_file in sorted(RESIDUOS_RUN.glob("inventario_residuos_*.pdf")):
    m = re.search(r"(\d{4})", pdf_file.name)
    if not m:
        continue
    year = int(m.group(1))
    df_r = _extract_iqr_pdf(pdf_file, year)
    if len(df_r):
        n_tiete = df_r["tiete"].sum()
        med_all   = df_r["iqr"].median()
        med_tiete = df_r[df_r["tiete"]]["iqr"].median() if n_tiete else np.nan
        print(f"  {year}: {len(df_r)} municípios SP | IQR med(todos)={med_all:.2f} | "
              f"IQR med(Tietê UGRHI={n_tiete})={med_tiete:.2f}")
        residuos_dfs.append(df_r)
    else:
        print(f"  {year}: sem tabelas extraídas")

if residuos_dfs:
    residuos_staging = pd.concat(residuos_dfs, ignore_index=True)
    residuos_staging.to_parquet(STAGING / "residuos" / "residuos_municipio_ano.parquet", index=False)

    residuos_ano = (
        residuos_staging.groupby(["ano", "tiete"])
        .agg(
            iqr_mediana=("iqr", "median"),
            iqr_media=("iqr", "mean"),
            n_municipios=("municipio", "count"),
        )
        .reset_index()
    )
    residuos_ano.to_parquet(ANALYTIC / "residuos_reservatorio_ano.parquet", index=False)
    print("  Analytic salvo")
else:
    residuos_ano = pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════════════
# 4. FIGURAS
# ═══════════════════════════════════════════════════════════════════════════
print("\n=== Gerando figuras ===")

# ── FIG 6: Queimadas ─────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={"height_ratios": [2, 1]})
fig.suptitle("Focos de Calor no Corredor do Rio Tietê · 2000–2024\n(BDQueimadas/INPE — satélites ativos)",
             fontsize=13, color=GSU_BLUE, fontweight="bold", y=1.01)

ax1, ax2 = axes

# painel superior: contagem anual com barras coloridas
anos_q = q_ano["ano"].values
n_focos = q_ano["n_focos"].values
colors = [RED_CRISE if (y >= 2019 and y <= 2021) else BLUE_ACC for y in anos_q]
bars = ax1.bar(anos_q, n_focos, color=colors, width=0.75, alpha=0.85, zorder=3)

# destaca anos críticos
for yr, n, c in zip(anos_q, n_focos, colors):
    if c == RED_CRISE:
        ax1.text(yr, n + max(n_focos) * 0.015, f"{n:,}", ha="center", va="bottom",
                 fontsize=7.5, color=RED_CRISE, fontweight="bold")

# linha de tendência (média móvel 3 anos)
ma3 = pd.Series(n_focos).rolling(3, center=True).mean()
ax1.plot(anos_q, ma3, color=GSU_GOLD, linewidth=2, zorder=4, label="Média móvel 3 anos")
ax1.set_ylabel("Focos de calor (contagem)", fontsize=10, color=GSU_BLUE)
ax1.set_ylim(0, max(n_focos) * 1.15)
ax1.legend(fontsize=9, framealpha=0.7)
ax1.set_title("Contagem anual de focos detectados (todos satélites)", fontsize=10, color="#475569")

# anotação de pico
peak_yr = anos_q[np.argmax(n_focos)]
peak_n  = max(n_focos)
ax1.annotate(f"Pico: {peak_yr}\n{peak_n:,} focos",
             xy=(peak_yr, peak_n), xytext=(peak_yr - 4, peak_n * 0.92),
             fontsize=8, color=RED_CRISE,
             arrowprops=dict(arrowstyle="->", color=RED_CRISE, lw=1.2))

# painel inferior: bioma breakdown (Cerrado vs Mata Atlântica)
biomas_relevantes = ["Cerrado", "Mata Atl\u00e2ntica"]
bioma_colors      = {biomas_relevantes[0]: GSU_GOLD, biomas_relevantes[1]: GREEN_ACC}
bottom = np.zeros(len(anos_q))
for bioma in biomas_relevantes:
    sub = q_bioma[q_bioma["bioma"] == bioma].set_index("ano")["n_focos"].reindex(anos_q, fill_value=0)
    ax2.bar(anos_q, sub.values, bottom=bottom, width=0.75, alpha=0.85,
            color=bioma_colors[bioma], label=bioma, zorder=3)
    bottom += sub.values
ax2.set_ylabel("Focos por bioma", fontsize=9, color=GSU_BLUE)
ax2.set_xlabel("Ano", fontsize=10, color=GSU_BLUE)
ax2.set_xticks(anos_q)
ax2.set_xticklabels(anos_q, rotation=45, ha="right", fontsize=8)
ax2.legend(fontsize=9, framealpha=0.7, loc="upper left")
ax2.set_title("Distribuição por bioma", fontsize=10, color="#475569")

# linha dourada decorativa no topo
for ax in axes:
    ax.tick_params(colors="#475569")
    for spine in ax.spines.values():
        spine.set_edgecolor("#e2e8f0")

plt.tight_layout()
out6 = FIG_DIR / "fig6_queimadas_corredor.png"
fig.savefig(out6)
plt.close()
print(f"  Fig 6 salva: {out6}")


# ── FIG 7: SNIS ──────────────────────────────────────────────────────────
if not snis_ano.empty:
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.suptitle("Cobertura de Esgoto nos Municípios do Estado de São Paulo · 2010–2021\n(SNIS — Prestadores Locais Públicos)",
                 fontsize=13, color=GSU_BLUE, fontweight="bold")

    anos_s = snis_ano["ano"].values
    ax.fill_between(anos_s, snis_ano["in015_mediana"], alpha=0.15, color=BLUE_ACC)
    ax.fill_between(anos_s, snis_ano["in046_mediana"], alpha=0.15, color=GREEN_ACC)
    ax.plot(anos_s, snis_ano["in015_mediana"], color=BLUE_ACC, linewidth=2.2,
            marker="o", markersize=5, label="IN015 — Índice de coleta de esgoto (%)")
    ax.plot(anos_s, snis_ano["in046_mediana"], color=GREEN_ACC, linewidth=2.2,
            marker="s", markersize=5, label="IN046 — Esgoto tratado / água consumida (%)")

    # valores no último ponto
    last_yr = anos_s[-1]
    for col, color, col_name in [("in015_mediana", BLUE_ACC, "IN015"),
                                  ("in046_mediana", GREEN_ACC, "IN046")]:
        v = snis_ano[snis_ano["ano"] == last_yr][col].values[0]
        ax.annotate(f"{v:.0f}%", xy=(last_yr, v), xytext=(last_yr + 0.3, v),
                    fontsize=9, color=color, fontweight="bold", va="center")

    ax.set_xlabel("Ano", fontsize=10, color=GSU_BLUE)
    ax.set_ylabel("Mediana (%)", fontsize=10, color=GSU_BLUE)
    ax.set_ylim(0, 105)
    ax.set_xticks(anos_s)
    ax.set_xticklabels(anos_s, rotation=45, ha="right")
    ax.legend(fontsize=9, framealpha=0.7)
    ax.axhline(100, color="#e2e8f0", linewidth=1, linestyle="--")

    # gap de tratamento
    gap_col  = snis_ano["in015_mediana"] - snis_ano["in046_mediana"]
    gap_last = gap_col.values[-1]
    ax.annotate(f"Gap coleta–tratamento\n{gap_last:.0f} p.p. em {last_yr}",
                xy=(last_yr, snis_ano["in046_mediana"].values[-1] + gap_last / 2),
                xytext=(last_yr - 3.5, snis_ano["in046_mediana"].values[-1] + gap_last / 2 + 8),
                fontsize=8.5, color=GSU_GOLD,
                arrowprops=dict(arrowstyle="->", color=GSU_GOLD, lw=1))

    ax.tick_params(colors="#475569")
    for spine in ax.spines.values():
        spine.set_edgecolor("#e2e8f0")

    plt.tight_layout()
    out7 = FIG_DIR / "fig7_snis_esgoto.png"
    fig.savefig(out7)
    plt.close()
    print(f"  Fig 7 salva: {out7}")
else:
    print("  Fig 7 pulada (sem dados SNIS)")
    out7 = None


# ── FIG 8: Resíduos ──────────────────────────────────────────────────────
if not residuos_ano.empty:
    fig, ax = plt.subplots(figsize=(9, 5))
    fig.suptitle("Índice de Qualidade de Aterros (IQR) — São Paulo · 2017–2021\n(CETESB — Inventário Estadual de Resíduos Sólidos Urbanos)",
                 fontsize=13, color=GSU_BLUE, fontweight="bold")

    # IQR: 0 (péssimo) → 10 (ótimo); categorias CETESB
    # Adequado ≥ 8.1; Controlado 6.1-8.0; Inadequado ≤ 6.0
    ax.axhspan(0, 6.0,  alpha=0.07, color=RED_CRISE,  label="Inadequado (< 6.0)")
    ax.axhspan(6.0, 8.0, alpha=0.07, color=GSU_GOLD,   label="Controlado (6.0–8.0)")
    ax.axhspan(8.0, 10,  alpha=0.07, color=GREEN_ACC,  label="Adequado (> 8.0)")

    for is_tiete, label, color, ls, ms in [
        (True,  "Municípios Bacia Tietê",   GSU_BLUE,  "-",  8),
        (False, "Demais municípios SP",      "#94a3b8", "--", 5),
    ]:
        sub = residuos_ano[residuos_ano["tiete"] == is_tiete].sort_values("ano")
        if len(sub):
            ax.plot(sub["ano"], sub["iqr_mediana"], color=color, linewidth=2.2,
                    marker="o", markersize=ms, linestyle=ls, label=label, zorder=4)
            ax.fill_between(sub["ano"], sub["iqr_mediana"], alpha=0.12, color=color)

    ax.set_xlabel("Ano", fontsize=10, color=GSU_BLUE)
    ax.set_ylabel("IQR Mediana", fontsize=10, color=GSU_BLUE)
    ax.set_ylim(0, 10.5)
    ax.set_xticks(residuos_ano["ano"].unique())
    ax.legend(fontsize=9, framealpha=0.7)
    ax.tick_params(colors="#475569")
    for spine in ax.spines.values():
        spine.set_edgecolor("#e2e8f0")

    plt.tight_layout()
    out8 = FIG_DIR / "fig8_residuos_iqr.png"
    fig.savefig(out8)
    plt.close()
    print(f"  Fig 8 salva: {out8}")
else:
    print("  Fig 8 pulada (sem dados resíduos)")
    out8 = None

print("\nDone.")
