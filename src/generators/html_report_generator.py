"""Gerador de dashboard HTML interativo para resultados do pipeline."""

from __future__ import annotations

import json
from typing import Any

_GSU_SEAL = "https://upload.wikimedia.org/wikipedia/en/thumb/0/07/Georgia_Southern_University_seal.svg/150px-Georgia_Southern_University_seal.svg.png"
_100K_LOGO = "https://i0.wp.com/www.100kstrongamericas.org/wp-content/uploads/2017/03/cropped-100k-Strong-Logo_Whitney_blue.fw_.png"


def generate_html_report(
    datasets: list[Any],
    master_context: Any,
    search_plan: list[Any],
    metadata: dict[str, Any],
) -> str:
    """Gera dashboard HTML completo com dados injetados como JSON inline."""
    datasets_data = [
        d.model_dump(mode="json") if hasattr(d, "model_dump") else d
        for d in datasets
    ]
    plan_data = [
        s.model_dump(mode="json") if hasattr(s, "model_dump") else s
        for s in search_plan
    ]

    if hasattr(master_context, "article_goal"):
        article_goal = master_context.article_goal or ""
    elif isinstance(master_context, dict):
        article_goal = master_context.get("article_goal", "")
    else:
        article_goal = ""

    def _safe_json(obj: Any) -> str:
        return json.dumps(obj, ensure_ascii=False).replace("</script>", "<\\/script>")

    html = _HTML_TEMPLATE
    html = html.replace("__DATASETS_JSON__", _safe_json(datasets_data))
    html = html.replace("__METADATA_JSON__", _safe_json(metadata))
    html = html.replace("__SEARCH_PLAN_JSON__", _safe_json(plan_data))
    html = html.replace("__ARTICLE_GOAL__", _esc(article_goal))
    html = html.replace("__GSU_SEAL__", _GSU_SEAL)
    html = html.replace("__100K_LOGO__", _100K_LOGO)
    return html


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Projeto 100K \u2014 Relat\u00f3rio de Descoberta</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Bitter:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {
  --gsu-blue: #011E42;
  --gsu-gold: #87714D;
  --gsu-gray: #A3AAAE;
  --gsu-blue-light: #1A3A5C;
  --gsu-blue-pale: #E8EDF2;
  --gsu-gold-light: #C4A86C;
  --gsu-gold-pale: #F5F0E6;
  --100k-blue: #1B75BB;
  --100k-blue-light: #4A9AD4;
  --100k-blue-pale: #E3F0FA;
  --bg-primary: #FFFFFF;
  --bg-secondary: #F7F8FA;
  --bg-page: #F0F2F5;
  --text-primary: #1A1A2E;
  --text-secondary: #5A6070;
  --text-muted: #8E95A5;
  --border: #E2E5EB;
  --border-hover: #C8CDD5;
  --fmt-structured: #0F7B5F;
  --fmt-semi: #1B75BB;
  --fmt-geo: #6B48A8;
  --fmt-paper: #87714D;
  --fmt-pdf: #C75D2C;
  --fmt-unknown: #8E95A5;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Inter', sans-serif; background: var(--bg-page); color: var(--text-primary); font-size: 13px; line-height: 1.5; }
.container { max-width: 1200px; margin: 24px auto; padding: 0 16px; }

/* HEADER */
.header { background: var(--gsu-blue); color: #fff; padding: 20px 24px 16px; border-radius: 12px 12px 0 0; }
.header-logos { display: flex; align-items: center; gap: 16px; margin: 0 0 12px; }
.header-sep { color: var(--gsu-gold); font-size: 20px; }
.header h1 { font-size: 18px; font-weight: 600; margin: 0 0 4px; }
.header-subtitle { font-family: 'Bitter', serif; font-size: 13px; color: var(--gsu-gray); }
.header-meta { font-size: 11px; color: var(--gsu-gold); margin: 6px 0 0; }
.gold-bar { height: 3px; background: linear-gradient(90deg, #87714D, #C4A86C, #87714D); }

/* METRICS */
.metrics-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 16px 0; }
.metric-card { background: var(--bg-primary); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; border-top: 3px solid var(--border); }
.metric-card.blue   { border-top-color: var(--gsu-blue); }
.metric-card.green  { border-top-color: var(--fmt-structured); }
.metric-card.orange { border-top-color: var(--fmt-pdf); }
.metric-card.sky    { border-top-color: var(--100k-blue); }
.metric-value { font-size: 28px; font-weight: 600; color: var(--text-primary); line-height: 1.1; }
.metric-label { font-size: 11px; color: var(--text-muted); margin-top: 4px; text-transform: uppercase; letter-spacing: 0.05em; }

/* FILTERS */
.filters { background: var(--bg-primary); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px; margin: 0 0 12px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.filter-select, .filter-search { border: 1px solid var(--border); border-radius: 6px; padding: 6px 10px; font-size: 12px; font-family: 'Inter', sans-serif; color: var(--text-primary); background: var(--bg-secondary); outline: none; }
.filter-select { cursor: pointer; }
.filter-search { flex: 1; min-width: 160px; }
.filter-select:focus, .filter-search:focus { border-color: var(--100k-blue); }
.filter-count { font-size: 11px; color: var(--text-muted); margin-left: auto; }
.btn-clear { font-size: 11px; font-family: 'Inter', sans-serif; color: var(--text-muted); background: none; border: 1px solid var(--border); border-radius: 6px; padding: 5px 10px; cursor: pointer; }
.btn-clear:hover { border-color: var(--border-hover); color: var(--text-primary); }

/* TABLE */
.table-wrap { background: var(--bg-primary); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; margin: 0 0 16px; overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
thead tr { background: var(--bg-secondary); border-bottom: 1px solid var(--border); }
th { padding: 10px 12px; font-size: 11px; font-weight: 600; color: var(--text-secondary); text-align: left; white-space: nowrap; text-transform: uppercase; letter-spacing: 0.04em; }
th.sortable { cursor: pointer; user-select: none; }
th.sortable:hover { color: var(--text-primary); }
th .sort-icon { margin-left: 4px; font-size: 10px; opacity: 0.4; }
th .sort-icon::after { content: '\21C5'; }
th.sort-asc  .sort-icon { opacity: 1; }
th.sort-asc  .sort-icon::after { content: '\2191'; }
th.sort-desc .sort-icon { opacity: 1; }
th.sort-desc .sort-icon::after { content: '\2193'; }
tbody tr.data-row { cursor: pointer; border-bottom: 1px solid var(--border); transition: background 0.1s; }
tbody tr.data-row:last-child { border-bottom: none; }
tbody tr.data-row:hover { background: var(--gsu-blue-pale); }
tbody tr.data-row.expanded { background: var(--gsu-gold-pale); }
td { padding: 9px 12px; vertical-align: top; }
td.rank { color: var(--text-muted); font-size: 11px; width: 40px; }
td.col-name { max-width: 280px; }
td.col-name .ds-name { font-weight: 500; font-size: 13px; color: var(--text-primary); display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
td.col-name .ds-desc { font-size: 11px; color: var(--text-muted); display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
td.col-link a { color: var(--100k-blue); font-size: 15px; text-decoration: none; }
td.col-link a:hover { opacity: 0.7; }

/* BADGES */
.badge { display: inline-block; font-size: 10px; font-weight: 500; padding: 2px 8px; border-radius: 4px; white-space: nowrap; }
.lv-macro  { background: rgba(1,30,66,0.08);  color: #011E42; }
.lv-meso   { background: rgba(1,30,66,0.18);  color: #011E42; }
.lv-bridge { background: rgba(1,30,66,0.40);  color: #fff; }
.lv-micro  { background: #011E42;             color: #fff; }
.fmt-structured         { background: rgba(15,123,95,0.12);  color: var(--fmt-structured); }
.fmt-semi_structured    { background: rgba(27,117,187,0.12); color: var(--fmt-semi); }
.fmt-geospatial_platform{ background: rgba(107,72,168,0.12); color: var(--fmt-geo); }
.fmt-academic_paper     { background: rgba(135,113,77,0.12); color: var(--fmt-paper); }
.fmt-pdf_report         { background: rgba(199,93,44,0.12);  color: var(--fmt-pdf); }
.fmt-unknown            { background: rgba(142,149,165,0.12);color: var(--fmt-unknown); }
.acc-direct_download    { background: rgba(15,123,95,0.12);  color: var(--fmt-structured); }
.acc-api_access         { background: rgba(27,117,187,0.12); color: var(--fmt-semi); }
.acc-web_portal         { background: rgba(135,113,77,0.12); color: var(--fmt-paper); }
.acc-geospatial_platform{ background: rgba(107,72,168,0.12); color: var(--fmt-geo); }
.acc-pdf_extraction     { background: rgba(199,93,44,0.12);  color: var(--fmt-pdf); }
.acc-restricted         { background: rgba(199,93,44,0.20);  color: #8B1A00; }
.acc-unknown            { background: rgba(142,149,165,0.12);color: var(--fmt-unknown); }
.pri-high   { background: rgba(1,30,66,0.12);  color: var(--gsu-blue); }
.pri-medium { background: rgba(135,113,77,0.12);color: var(--gsu-gold); }
.pri-low    { background: rgba(142,149,165,0.12);color: var(--fmt-unknown); }

/* DETAIL ROW */
tr.detail-row td { padding: 0; background: var(--gsu-gold-pale); border-bottom: 1px solid var(--border); }
.detail-panel { padding: 14px 16px 16px; }
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 20px; }
.detail-full { grid-column: 1 / -1; }
.field-label { font-weight: 500; font-size: 10px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; display: block; margin-bottom: 2px; }
.field-value { font-size: 12px; color: var(--text-primary); }
.field-value a { color: var(--100k-blue); word-break: break-all; }
.cg-card { margin: 12px 0 0; padding: 12px 14px; background: var(--bg-primary); border: 1px solid var(--border); border-radius: 8px; }
.cg-title { font-size: 11px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; margin: 0 0 10px; }
.cg-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 20px; }
.cg-list { margin: 6px 0 0 16px; color: var(--text-primary); font-size: 12px; }
.cg-list li { margin: 0 0 4px; }
.cg-downloads a { display: block; margin: 0 0 4px; font-size: 12px; color: var(--100k-blue); word-break: break-all; }
.cg-unavailable { font-size: 12px; color: var(--text-muted); padding: 10px 14px; background: var(--bg-secondary); border-radius: 8px; margin: 12px 0 0; text-align: center; border: 1px dashed var(--border); }

/* SECTION */
.section { margin: 0 0 16px; }
.section-header { font-size: 13px; font-weight: 600; color: var(--text-primary); margin: 0 0 10px; display: flex; align-items: center; gap: 8px; }
.section-header::before { content: ''; display: block; width: 3px; height: 16px; background: var(--gsu-gold); border-radius: 2px; }

/* COVERAGE */
.coverage-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.coverage-card { background: var(--bg-primary); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
.card-title { font-size: 11px; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.06em; margin: 0 0 14px; }
.bar-row { margin: 0 0 10px; }
.bar-label { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 4px; }
.bar-name { font-size: 12px; color: var(--text-primary); font-weight: 500; }
.bar-count { font-size: 11px; color: var(--text-muted); }
.bar-track { background: var(--bg-secondary); border-radius: 4px; height: 8px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; }

/* GAPS */
.gaps-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.gap-card { background: var(--bg-primary); border-radius: 8px; padding: 12px 14px; font-size: 12px; border-left: 3px solid var(--border); border: 1px solid var(--border); border-left-width: 3px; }
.gap-card.found   { border-left-color: var(--fmt-structured); }
.gap-card.missing { border-left-color: var(--fmt-pdf); }
.gap-name { font-weight: 500; margin-bottom: 4px; color: var(--text-primary); }
.gap-status { font-size: 11px; }
.gap-card.found   .gap-status { color: var(--fmt-structured); }
.gap-card.missing .gap-status { color: var(--fmt-pdf); }

/* NEXT STEPS */
.steps-card { background: var(--bg-primary); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
.step-item { display: flex; gap: 10px; padding: 10px 16px; border-bottom: 1px solid var(--border); align-items: flex-start; }
.step-item:last-child { border-bottom: none; }
.step-icon { flex-shrink: 0; width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; margin-top: 1px; }
.step-icon.search  { background: rgba(199,93,44,0.12); color: var(--fmt-pdf); }
.step-icon.extract { background: rgba(135,113,77,0.12); color: var(--fmt-paper); }
.step-icon.cross   { background: rgba(15,123,95,0.12);  color: var(--fmt-structured); }
.step-body { font-size: 12px; line-height: 1.5; }
.step-body .step-sub { display: block; font-size: 11px; color: var(--text-muted); margin-top: 2px; }

/* FOOTER */
.footer { background: var(--gsu-blue); color: var(--gsu-gray); padding: 14px 24px; border-radius: 0 0 12px 12px; font-size: 11px; text-align: center; }
.footer-gold { color: var(--gsu-gold); }

/* EMPTY */
.empty-state { text-align: center; padding: 40px; color: var(--text-muted); font-size: 13px; }

/* RESPONSIVE */
@media (max-width: 1200px) { .metrics-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 768px) {
  .coverage-grid { grid-template-columns: 1fr; }
  .gaps-grid     { grid-template-columns: 1fr 1fr; }
  .detail-grid   { grid-template-columns: 1fr; }
}
@media (max-width: 480px) { .gaps-grid { grid-template-columns: 1fr; } }

/* PRINT */
@media print {
  .filters { display: none; }
  tbody tr.data-row { break-inside: avoid; }
  tr.detail-row { display: table-row !important; }
}
</style>
</head>
<body>
<div class="container">

<!-- HEADER -->
<div class="header">
  <div class="header-logos">
    <img src="__GSU_SEAL__" alt="Georgia Southern" height="36" style="opacity:0.9" onerror="this.style.display='none'">
    <span class="header-sep">/</span>
    <img src="__100K_LOGO__" alt="100K Strong" height="28" style="filter:brightness(0) invert(1)" onerror="this.style.display='none'">
  </div>
  <h1>Projeto 100K &mdash; Relat&oacute;rio de Descoberta</h1>
  <p class="header-subtitle">__ARTICLE_GOAL__</p>
  <p class="header-meta" id="header-meta">Carregando&hellip;</p>
</div>
<div class="gold-bar"></div>

<!-- METRICS -->
<div class="metrics-grid">
  <div class="metric-card blue">  <div class="metric-value" id="m-total">—</div>  <div class="metric-label">Total datasets</div></div>
  <div class="metric-card green"> <div class="metric-value" id="m-direct">—</div> <div class="metric-label">Download direto</div></div>
  <div class="metric-card orange"><div class="metric-value" id="m-gaps">—</div>   <div class="metric-label">Lacunas cr&iacute;ticas</div></div>
  <div class="metric-card sky">   <div class="metric-value" id="m-tracks">—</div> <div class="metric-label">Trilhas executadas</div></div>
</div>

<!-- FILTERS -->
<div class="filters">
  <select class="filter-select" id="f-level"    onchange="applyFilters()">
    <option value="">N&iacute;vel &#x25BE;</option>
    <option value="macro">Macro</option>
    <option value="meso">Meso</option>
    <option value="bridge">Bridge</option>
    <option value="micro">Micro</option>
  </select>
  <select class="filter-select" id="f-format"   onchange="applyFilters()">
    <option value="">Formato &#x25BE;</option>
    <option value="structured">Estruturado</option>
    <option value="semi_structured">Semi-estruturado</option>
    <option value="geospatial_platform">Geoespacial</option>
    <option value="academic_paper">Artigo</option>
    <option value="pdf_report">PDF</option>
    <option value="unknown">Desconhecido</option>
  </select>
  <select class="filter-select" id="f-access"   onchange="applyFilters()">
    <option value="">Acesso &#x25BE;</option>
    <option value="direct_download">Download direto</option>
    <option value="api_access">API</option>
    <option value="web_portal">Portal web</option>
    <option value="geospatial_platform">Plataforma geo</option>
    <option value="pdf_extraction">PDF</option>
    <option value="restricted">Restrito</option>
    <option value="unknown">Desconhecido</option>
  </select>
  <select class="filter-select" id="f-priority" onchange="applyFilters()">
    <option value="">Prioridade &#x25BE;</option>
    <option value="high">Alta</option>
    <option value="medium">M&eacute;dia</option>
    <option value="low">Baixa</option>
  </select>
  <input class="filter-search" id="f-search" type="text"
         placeholder="&#x1F50D; Dataset, URL, par&acirc;metro&hellip;" oninput="applyFilters()">
  <span class="filter-count" id="filter-count"></span>
  <button class="btn-clear" onclick="clearFilters()">Limpar filtros</button>
</div>

<!-- TABLE -->
<div class="section">
  <div class="section-header">Datasets descobertos</div>
  <div class="table-wrap">
    <table id="main-table">
      <thead>
        <tr>
          <th style="width:40px">#</th>
          <th class="sortable" data-col="dataset_name"    style="min-width:200px">Dataset <span class="sort-icon"></span></th>
          <th class="sortable" data-col="hierarchy_level" style="width:80px">N&iacute;vel <span class="sort-icon"></span></th>
          <th class="sortable" data-col="data_format"     style="width:120px">Formato <span class="sort-icon"></span></th>
          <th class="sortable" data-col="access_type"     style="width:120px">Acesso <span class="sort-icon"></span></th>
          <th class="sortable" data-col="temporal_coverage" style="width:100px">Per&iacute;odo <span class="sort-icon"></span></th>
          <th class="sortable" data-col="track_priority"  style="width:80px">Prior. <span class="sort-icon"></span></th>
          <th style="width:40px">URL</th>
        </tr>
      </thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>
</div>

<!-- COVERAGE -->
<div class="section">
  <div class="section-header">Cobertura</div>
  <div class="coverage-grid">
    <div class="coverage-card">
      <div class="card-title">Por n&iacute;vel hier&aacute;rquico</div>
      <div id="coverage-level"></div>
    </div>
    <div class="coverage-card">
      <div class="card-title">Por formato de dados</div>
      <div id="coverage-format"></div>
    </div>
  </div>
</div>

<!-- GAPS -->
<div class="section">
  <div class="section-header">Fontes esperadas vs. encontradas</div>
  <div class="gaps-grid" id="gaps-grid"></div>
</div>

<!-- NEXT STEPS -->
<div class="section">
  <div class="section-header">Pr&oacute;ximos passos</div>
  <div class="steps-card" id="next-steps"></div>
</div>

<!-- FOOTER -->
<div class="footer">
  <span class="footer-gold">Georgia Southern University</span> &middot; Dept. of Geology and Geography
  <span class="footer-gold"> / </span>
  <span class="footer-gold">100K Strong in the Americas</span> &middot; Innovation Fund<br>
  Pipeline Research_FREnTE v2 &middot; <span id="footer-ts"></span>
</div>

</div><!-- /container -->

<script>
// ── DATA ──────────────────────────────────────────────────────────────
const DATASETS    = __DATASETS_JSON__;
const METADATA    = __METADATA_JSON__;
const SEARCH_PLAN = __SEARCH_PLAN_JSON__;

// ── EXPECTED SOURCES (gap detection) ─────────────────────────────────
const EXPECTED_SOURCES = [
  { name: "ANA HidroWeb",         domain: "snirh.gov.br",             level: "macro"  },
  { name: "CETESB QUALAR",        domain: "qualar.cetesb.sp.gov.br",  level: "bridge" },
  { name: "SNIS saneamento",      domain: "app4.mdr.gov.br",          level: "meso"   },
  { name: "MapBiomas",            domain: "mapbiomas.org",             level: "macro"  },
  { name: "INPE PRODES/DETER",    domain: "terrabrasilis.dpi.inpe.br",level: "meso"   },
  { name: "INPE BDQueimadas",     domain: "queimadas.dgi.inpe.br",    level: "meso"   },
  { name: "ONS opera\u00e7\u00e3o", domain: "ons.org.br",             level: "bridge" },
  { name: "IBGE SIDRA",           domain: "sidra.ibge.gov.br",        level: "macro"  },
  { name: "Sentinel-2 / Landsat", domain: "copernicus.eu",            level: "micro"  },
  { name: "CDOM/MOD artigos",     keywords: ["cdom","organic matter","tiet\u00ea","tiete"], level: "micro" },
  { name: "SRTM / ALOS DEM",      domain: "earthexplorer.usgs.gov",   level: "macro"  },
  { name: "CHIRPS precipita\u00e7\u00e3o", domain: "chc.ucsb.edu",   level: "macro"  },
  { name: "SICAR/CAR APP",        domain: "car.gov.br",               level: "meso"   },
  { name: "IBGE PAM agro",        keywords: ["PAM","produ\u00e7\u00e3o agr\u00edcola","producao agricola"], level: "meso" },
];

// ── STATE ─────────────────────────────────────────────────────────────
let filteredData = [];
let sortCol = "rank";
let sortAsc  = true;
let expandedIdx = -1;

const PRIORITY_ORDER  = { high: 0, medium: 1, low: 2 };
const LEVEL_LABELS    = { macro: "Macro", meso: "Meso", bridge: "Bridge", micro: "Micro" };
const FORMAT_LABELS   = { structured: "Estruturado", semi_structured: "Semi-estrut.", geospatial_platform: "Geoespacial", academic_paper: "Artigo", pdf_report: "PDF", unknown: "?" };
const ACCESS_LABELS   = { direct_download: "Download", api_access: "API", web_portal: "Portal", geospatial_platform: "Plataforma", pdf_extraction: "PDF", restricted: "Restrito", unknown: "?" };
const PRIORITY_LABELS = { high: "Alta", medium: "M\u00e9dia", low: "Baixa" };

// ── HELPERS ───────────────────────────────────────────────────────────
function esc(s) {
  if (s == null) return "";
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
function badge(cls, label) {
  return '<span class="badge ' + cls + '">' + esc(label) + '</span>';
}
function badgeLevel(v)    { return badge("lv-"   + (v||"unknown"), LEVEL_LABELS[v]    || v || "?"); }
function badgeFormat(v)   { return badge("fmt-"  + (v||"unknown"), FORMAT_LABELS[v]   || v || "?"); }
function badgeAccess(v)   { return badge("acc-"  + (v||"unknown"), ACCESS_LABELS[v]   || v || "?"); }
function badgePriority(v) { return badge("pri-"  + (v||"low"),     PRIORITY_LABELS[v] || v || "?"); }

// ── GAP DETECTION ─────────────────────────────────────────────────────
function isFound(exp) {
  return DATASETS.some(function(d) {
    var url  = (d.url || "").toLowerCase();
    var text = [d.dataset_name, d.dataset_description, d.title].join(" ").toLowerCase();
    if (exp.domain   && url.includes(exp.domain.toLowerCase()))  return true;
    if (exp.keywords) return exp.keywords.some(function(k) { return text.includes(k.toLowerCase()); });
    return false;
  });
}
function foundVia(exp) {
  var d = DATASETS.find(function(d) {
    var url  = (d.url || "").toLowerCase();
    var text = [d.dataset_name, d.dataset_description, d.title].join(" ").toLowerCase();
    if (exp.domain   && url.includes(exp.domain.toLowerCase()))  return true;
    if (exp.keywords) return exp.keywords.some(function(k) { return text.includes(k.toLowerCase()); });
    return false;
  });
  return d ? d.track_origin : null;
}

// ── METRICS ───────────────────────────────────────────────────────────
function renderMetrics() {
  var total  = DATASETS.length;
  var direct = DATASETS.filter(function(d) { return d.access_type === "direct_download"; }).length;
  var gaps   = EXPECTED_SOURCES.filter(function(e) { return !isFound(e); }).length;
  var tracks = SEARCH_PLAN.length || new Set(DATASETS.map(function(d) { return d.track_origin; })).size;
  var ts     = (METADATA.timestamp || "").slice(0,10);

  document.getElementById("m-total").textContent  = total;
  document.getElementById("m-direct").textContent = direct;
  document.getElementById("m-gaps").textContent   = gaps;
  document.getElementById("m-tracks").textContent = tracks;
  document.getElementById("header-meta").textContent =
    "Execu\u00e7\u00e3o: " + ts + " \u00b7 " + tracks + " trilhas \u00b7 " + total + " datasets";
  document.getElementById("footer-ts").textContent = (METADATA.timestamp || "").slice(0,16).replace("T"," ");
}

// ── FILTERS ───────────────────────────────────────────────────────────
function applyFilters() {
  var level    = document.getElementById("f-level").value;
  var format   = document.getElementById("f-format").value;
  var access   = document.getElementById("f-access").value;
  var priority = document.getElementById("f-priority").value;
  var search   = document.getElementById("f-search").value.toLowerCase();

  filteredData = DATASETS.filter(function(d) {
    if (level    && d.hierarchy_level !== level)   return false;
    if (format   && d.data_format     !== format)  return false;
    if (access   && d.access_type     !== access)  return false;
    if (priority && d.track_priority  !== priority)return false;
    if (search) {
      var hay = [d.dataset_name, d.dataset_description, d.url,
                 (d.key_parameters || []).join(" "),
                 d.thematic_axis, d.source_domain].join(" ").toLowerCase();
      if (!hay.includes(search)) return false;
    }
    return true;
  });

  document.getElementById("filter-count").textContent =
    filteredData.length + " de " + DATASETS.length + " datasets";
  expandedIdx = -1;
  renderTable();
}

function clearFilters() {
  ["f-level","f-format","f-access","f-priority"].forEach(function(id) {
    document.getElementById(id).value = "";
  });
  document.getElementById("f-search").value = "";
  applyFilters();
}

// ── SORT ──────────────────────────────────────────────────────────────
function sortData(col) {
  if (sortCol === col) { sortAsc = !sortAsc; } else { sortCol = col; sortAsc = true; }
  document.querySelectorAll("th.sortable").forEach(function(th) {
    th.classList.remove("sort-asc","sort-desc");
    if (th.dataset.col === sortCol) th.classList.add(sortAsc ? "sort-asc" : "sort-desc");
  });
  filteredData.sort(function(a, b) {
    var va = a[sortCol], vb = b[sortCol];
    if (sortCol === "track_priority") { va = PRIORITY_ORDER[va] != null ? PRIORITY_ORDER[va] : 99; vb = PRIORITY_ORDER[vb] != null ? PRIORITY_ORDER[vb] : 99; }
    if (typeof va === "number" && typeof vb === "number") return sortAsc ? va - vb : vb - va;
    va = String(va || "").toLowerCase(); vb = String(vb || "").toLowerCase();
    return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
  });
  expandedIdx = -1;
  renderTable();
}

// ── TABLE ─────────────────────────────────────────────────────────────
function renderTable() {
  var tbody = document.getElementById("table-body");
  if (!filteredData.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="empty-state">Nenhum dataset encontrado com os filtros selecionados.</td></tr>';
    return;
  }
  var html = "";
  filteredData.forEach(function(d, i) {
    var isExp = expandedIdx === i;
    var name  = esc(d.dataset_name || d.title || "Sem t\u00edtulo");
    var desc  = esc(d.dataset_description || d.snippet || "");
    var period = esc(d.temporal_coverage || "\u2014");

    html += '<tr class="data-row' + (isExp ? " expanded" : "") + '" onclick="toggleDetail(' + i + ')">';
    html += '<td class="rank">'   + (d.rank || (i+1)) + '</td>';
    html += '<td class="col-name"><span class="ds-name">' + name + '</span><span class="ds-desc">' + desc + '</span></td>';
    html += '<td>' + badgeLevel(d.hierarchy_level) + '</td>';
    html += '<td>' + badgeFormat(d.data_format)    + '</td>';
    html += '<td>' + badgeAccess(d.access_type)    + '</td>';
    html += '<td style="font-size:11px;color:var(--text-secondary)">' + period + '</td>';
    html += '<td>' + badgePriority(d.track_priority) + '</td>';
    html += '<td class="col-link"><a href="' + esc(d.url) + '" target="_blank" onclick="event.stopPropagation()" title="' + esc(d.url) + '">\u2197</a></td>';
    html += '</tr>';

    if (isExp) {
      html += '<tr class="detail-row"><td colspan="8">' + renderDetail(d) + '</td></tr>';
    }
  });
  tbody.innerHTML = html;
}

function renderDetail(d) {
  var params   = (d.key_parameters || []).join(", ") || "\u2014";
  var spatial  = d.spatial_coverage  || "\u2014";
  var temporal = d.temporal_coverage || "\u2014";
  var notes    = d.access_notes      || "\u2014";
  var desc     = d.dataset_description || d.snippet || "Sem descri\u00e7\u00e3o dispon\u00edvel.";
  var guide    = d.collection_guide || null;

  var h = '<div class="detail-panel"><div class="detail-grid">';
  h += field("Descri\u00e7\u00e3o",       desc,          true);
  h += field("Par\u00e2metros",            params,        false);
  h += field("Cobertura temporal",         temporal,      false);
  h += field("Cobertura espacial",         spatial,       false);
  h += field("Eixo tem\u00e1tico",         d.thematic_axis    || "\u2014", false);
  h += field("Categoria",                  d.source_category  || "\u2014", false);
  h += field("Trilha de origem",           d.track_origin     || "\u2014", false);
  h += field("Dom\u00ednio",              d.source_domain    || "\u2014", false);
  h += '<div class="detail-field detail-full"><span class="field-label">URL</span>'
    +  '<span class="field-value"><a href="' + esc(d.url) + '" target="_blank">' + esc(d.url) + '</a></span></div>';
  h += field("Notas de acesso", notes, true);
  h += '</div>';
  h += renderCollectionGuide(guide);
  h += '</div>';
  return h;
}

function field(label, value, full) {
  return '<div class="detail-field' + (full ? " detail-full" : "") + '">'
    + '<span class="field-label">' + esc(label) + '</span>'
    + '<span class="field-value">' + esc(value) + '</span>'
    + '</div>';
}

function renderCollectionGuide(guide) {
  if (!guide) {
    return '<div class="cg-unavailable">Guia de coleta nao disponivel. Rode com Firecrawl ativado ou navegue manualmente pelo portal.</div>';
  }

  var steps = (guide.steps || []).map(function(step) { return '<li>' + esc(step) + '</li>'; }).join("");
  var caveats = (guide.caveats || []).map(function(note) { return '<li>' + esc(note) + '</li>'; }).join("");
  var filterEntries = Object.entries(guide.filters_available || {});
  var filters = filterEntries.length
    ? '<ul class="cg-list">' + filterEntries.map(function(entry) {
        return '<li><strong>' + esc(entry[0]) + ':</strong> ' + esc(entry[1]) + '</li>';
      }).join("") + '</ul>'
    : '<div class="field-value">\u2014</div>';
  var directDownloads = (guide.direct_download_urls || []).length
    ? '<div class="cg-downloads">' + guide.direct_download_urls.map(function(url) {
        return '<a href="' + esc(url) + '" target="_blank">' + esc(url) + '</a>';
      }).join("") + '</div>'
    : '<div class="field-value">\u2014</div>';

  var h = '<div class="cg-card">';
  h += '<div class="cg-title">Guia de coleta</div>';
  h += '<div class="cg-grid">';
  h += field("Esforco estimado", guide.estimated_effort || "\u2014", false);
  h += field("Requer login", guide.requires_login ? "Sim" : "Nao", false);
  h += field("Formato de download", guide.download_format || "\u2014", false);
  h += '<div class="detail-field"><span class="field-label">Downloads diretos</span>' + directDownloads + '</div>';
  h += '<div class="detail-field detail-full"><span class="field-label">Passos</span>' + (steps ? '<ol class="cg-list">' + steps + '</ol>' : '<div class="field-value">\u2014</div>') + '</div>';
  h += '<div class="detail-field detail-full"><span class="field-label">Filtros identificados</span>' + filters + '</div>';
  h += '<div class="detail-field detail-full"><span class="field-label">Alertas</span>' + (caveats ? '<ul class="cg-list">' + caveats + '</ul>' : '<div class="field-value">\u2014</div>') + '</div>';
  h += '</div></div>';
  return h;
}

function toggleDetail(i) {
  expandedIdx = expandedIdx === i ? -1 : i;
  renderTable();
}

// ── COVERAGE ──────────────────────────────────────────────────────────
function renderCoverage() {
  var levels = ["macro","meso","bridge","micro"];
  var levelColors = { macro:"rgba(1,30,66,0.18)", meso:"rgba(1,30,66,0.38)", bridge:"rgba(1,30,66,0.65)", micro:"rgba(1,30,66,0.90)" };
  var levelCount = {}; levels.forEach(function(l) { levelCount[l] = DATASETS.filter(function(d) { return d.hierarchy_level === l; }).length; });
  var maxL = Math.max.apply(null, levels.map(function(l) { return levelCount[l] || 0; }).concat([1]));
  var lHtml = "";
  levels.forEach(function(l) {
    var n = levelCount[l] || 0;
    lHtml += '<div class="bar-row"><div class="bar-label"><span class="bar-name">' + (LEVEL_LABELS[l]||l) + '</span><span class="bar-count">' + n + '</span></div>'
      + '<div class="bar-track"><div class="bar-fill" style="width:' + Math.round(n/maxL*100) + '%;background:' + levelColors[l] + '"></div></div></div>';
  });
  document.getElementById("coverage-level").innerHTML = lHtml;

  var formats = ["structured","semi_structured","geospatial_platform","academic_paper","pdf_report","unknown"];
  var fmtColors = { structured:"var(--fmt-structured)", semi_structured:"var(--fmt-semi)", geospatial_platform:"var(--fmt-geo)", academic_paper:"var(--fmt-paper)", pdf_report:"var(--fmt-pdf)", unknown:"var(--fmt-unknown)" };
  var fmtCount = {}; formats.forEach(function(f) { fmtCount[f] = DATASETS.filter(function(d) { return d.data_format === f; }).length; });
  var maxF = Math.max.apply(null, formats.map(function(f) { return fmtCount[f] || 0; }).concat([1]));
  var fHtml = "";
  formats.filter(function(f) { return fmtCount[f] > 0; }).forEach(function(f) {
    var n = fmtCount[f];
    fHtml += '<div class="bar-row"><div class="bar-label"><span class="bar-name">' + (FORMAT_LABELS[f]||f) + '</span><span class="bar-count">' + n + '</span></div>'
      + '<div class="bar-track"><div class="bar-fill" style="width:' + Math.round(n/maxF*100) + '%;background:' + fmtColors[f] + '"></div></div></div>';
  });
  document.getElementById("coverage-format").innerHTML = fHtml;
}

// ── GAPS ──────────────────────────────────────────────────────────────
function renderGaps() {
  var html = "";
  EXPECTED_SOURCES.forEach(function(e) {
    var found = isFound(e);
    var via   = foundVia(e);
    html += '<div class="gap-card ' + (found ? "found" : "missing") + '">';
    html += '<div class="gap-name">' + esc(e.name) + '</div>';
    html += '<div class="gap-status">' + (found ? "\u2713 encontrada via " + esc(via||"trilha") : "\u2717 buscar manualmente") + '</div>';
    html += '</div>';
  });
  document.getElementById("gaps-grid").innerHTML = html;
}

// ── NEXT STEPS ────────────────────────────────────────────────────────
function renderNextSteps() {
  var steps = [];

  EXPECTED_SOURCES.filter(function(e) { return !isFound(e); }).forEach(function(e) {
    var url = e.domain ? "https://" + e.domain : "";
    steps.push({ icon: "search", main: "Buscar manualmente: <strong>" + esc(e.name) + "</strong>", sub: url ? "Acessar: " + esc(url) : "" });
  });

  DATASETS.filter(function(d) { return d.data_format === "pdf_report"; }).forEach(function(d) {
    steps.push({ icon: "extract", main: "Extrair tabelas de: <strong>" + esc(d.dataset_name || d.title) + "</strong>", sub: "Requer OCR/parsing de PDF" });
  });

  var cross = [
    { main: "SNIS \u00d7 CETESB DBO",             sub: "Verificar consist\u00eancia entre dados de esgoto e qualidade da \u00e1gua" },
    { main: "MapBiomas \u00d7 CETESB turbidez",    sub: "Correlacionar desmatamento com eros\u00e3o e turbidez nos reservat\u00f3rios" },
    { main: "Clorofila in situ \u00d7 sat\u00e9lite", sub: "Calibrar sensoriamento remoto com medi\u00e7\u00f5es de campo" },
    { main: "Uso do solo \u00d7 COT reservat\u00f3rios", sub: "Testar hip\u00f3tese central sobre carbono org\u00e2nico e uso do solo" },
  ];
  cross.forEach(function(c) { steps.push({ icon: "cross", main: c.main, sub: c.sub }); });

  if (!steps.length) {
    document.getElementById("next-steps").innerHTML = '<div class="empty-state">Todas as fontes esperadas foram encontradas.</div>';
    return;
  }
  var icons = { search: "!", extract: "P", cross: "\u00d7" };
  var html = "";
  steps.forEach(function(s) {
    html += '<div class="step-item"><div class="step-icon ' + s.icon + '">' + (icons[s.icon]||"") + '</div>';
    html += '<div class="step-body">' + s.main + (s.sub ? '<span class="step-sub">' + esc(s.sub) + '</span>' : '') + '</div></div>';
  });
  document.getElementById("next-steps").innerHTML = html;
}

// ── SORT HEADERS ──────────────────────────────────────────────────────
document.querySelectorAll("th.sortable").forEach(function(th) {
  th.addEventListener("click", function() { sortData(th.dataset.col); });
});

// ── INIT ──────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", function() {
  renderMetrics();
  filteredData = DATASETS.slice();
  applyFilters();
  renderCoverage();
  renderGaps();
  renderNextSteps();
});
</script>
</body>
</html>"""
