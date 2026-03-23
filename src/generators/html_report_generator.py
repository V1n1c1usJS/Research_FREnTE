"""Gerador de dashboard HTML interativo para resultados do pipeline."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

_IMG_DIR = Path(__file__).resolve().parent.parent / "img"

_MIME = {
    ".webp": "image/webp",
    ".png":  "image/png",
    ".svg":  "image/svg+xml",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
}

# Mapeamento: placeholder → nome real do arquivo em src/img/
_IMAGES = {
    "__100K_LOGO__":  "100K.webp",
    "__GSU_LOGO__":   "Georgia.png",
    "__SENAI_LOGO__": "SENAI.svg",
}


def _img_src(filename: str) -> str:
    """Retorna data URI base64 se o arquivo existir, senão caminho relativo."""
    path = _IMG_DIR / filename
    if path.exists():
        mime = _MIME.get(path.suffix.lower(), "image/png")
        data = base64.b64encode(path.read_bytes()).decode()
        return f"data:{mime};base64,{data}"
    return f"img/{filename}"


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
    html = html.replace("__DATASETS_JSON__",    _safe_json(datasets_data))
    html = html.replace("__METADATA_JSON__",    _safe_json(metadata))
    html = html.replace("__SEARCH_PLAN_JSON__", _safe_json(plan_data))
    html = html.replace("__ARTICLE_GOAL__",     _esc(article_goal))
    for placeholder, filename in _IMAGES.items():
        html = html.replace(placeholder, _img_src(filename))
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
<title>Projeto FREnTE &mdash; Relat&oacute;rio de Descoberta</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Bitter:wght@400;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
<style>
:root {
  --gsu-blue: #011E42;
  --gsu-gold: #87714D;
  --fmt-structured: #0F7B5F;
  --fmt-semi:       #1B75BB;
  --fmt-geo:        #6B48A8;
  --fmt-paper:      #87714D;
  --fmt-pdf:        #C75D2C;
  --fmt-unknown:    #8E95A5;
}
body { font-family: 'Inter', sans-serif; }
h1,h2,h3 { font-family: 'Bitter', serif; }
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;
  vertical-align: middle;
}
.gold-bar {
  height: 3px;
  background: linear-gradient(90deg, #87714D, #C4A86C, #87714D);
  border-radius: 2px;
}
/* ── Badges ── */
.badge { display:inline-flex; align-items:center; font-size:10px; font-weight:600; padding:2px 8px; border-radius:4px; white-space:nowrap; text-transform:uppercase; letter-spacing:.04em; }
.lv-macro   { background:rgba(1,30,66,.08);  color:#011E42; }
.lv-meso    { background:rgba(1,30,66,.18);  color:#011E42; }
.lv-bridge  { background:rgba(1,30,66,.45);  color:#fff; }
.lv-micro   { background:#011E42;            color:#fff; }
.fmt-structured          { background:rgba(15,123,95,.12);  color:var(--fmt-structured); }
.fmt-semi_structured     { background:rgba(27,117,187,.12); color:var(--fmt-semi); }
.fmt-geospatial_platform { background:rgba(107,72,168,.12); color:var(--fmt-geo); }
.fmt-academic_paper      { background:rgba(135,113,77,.12); color:var(--fmt-paper); }
.fmt-pdf_report          { background:rgba(199,93,44,.12);  color:var(--fmt-pdf); }
.fmt-unknown             { background:rgba(142,149,165,.12);color:var(--fmt-unknown); }
.acc-direct_download     { background:rgba(15,123,95,.12);  color:var(--fmt-structured); }
.acc-api_access          { background:rgba(27,117,187,.12); color:var(--fmt-semi); }
.acc-web_portal          { background:rgba(135,113,77,.12); color:var(--fmt-paper); }
.acc-geospatial_platform { background:rgba(107,72,168,.12); color:var(--fmt-geo); }
.acc-pdf_extraction      { background:rgba(199,93,44,.12);  color:var(--fmt-pdf); }
.acc-restricted          { background:rgba(199,93,44,.20);  color:#8B1A00; }
.acc-unknown             { background:rgba(142,149,165,.12);color:var(--fmt-unknown); }
.pri-high   { background:rgba(1,30,66,.12);   color:#011E42; }
.pri-medium { background:rgba(135,113,77,.12);color:#87714D; }
.pri-low    { background:rgba(142,149,165,.12);color:#8E95A5; }
/* ── Sort headers ── */
th.sortable { cursor:pointer; user-select:none; }
th.sort-asc  .sort-icon::after { content:' \u2191'; }
th.sort-desc .sort-icon::after { content:' \u2193'; }
th .sort-icon::after           { content:' \u21C5'; opacity:.4; font-size:10px; }
/* ── Table rows ── */
.data-row { cursor:pointer; transition:background .1s; }
.data-row.expanded { background:#fef9ee !important; }
/* ── Detail panel ── */
.detail-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px 20px; }
.detail-full { grid-column:1/-1; }
.field-label { font-weight:600; font-size:10px; color:#64748b; text-transform:uppercase; letter-spacing:.05em; display:block; margin-bottom:3px; }
.field-value { font-size:12px; color:#1e293b; }
.field-value a { color:#1B75BB; word-break:break-all; }
.cg-grid  { display:grid; grid-template-columns:1fr 1fr; gap:10px 20px; }
.cg-list  { margin:4px 0 0 14px; }
.cg-list li { font-size:12px; margin:0 0 3px; color:#1e293b; }
.cg-downloads a { display:block; font-size:11px; color:#1B75BB; word-break:break-all; margin:2px 0; }
.cg-unavailable { font-size:12px; color:#94a3b8; padding:12px; background:#f8fafc; border-radius:8px; margin-top:12px; text-align:center; border:1px dashed #e2e8f0; }
/* ── Scrollbar ── */
.custom-scrollbar::-webkit-scrollbar { width:5px; height:5px; }
.custom-scrollbar::-webkit-scrollbar-track { background:#f1f5f9; }
.custom-scrollbar::-webkit-scrollbar-thumb { background:#cbd5e1; border-radius:10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background:#94a3b8; }
</style>
</head>
<body class="min-h-screen py-8 px-4 md:px-8 bg-[#F8FAFC] text-slate-800">
<div class="max-w-7xl mx-auto space-y-8">

<!-- ── HEADER ──────────────────────────────────────────────────────── -->
<header class="space-y-4">
  <div class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
    <div class="flex items-center gap-8">
      <img src="__100K_LOGO__"  alt="100K Strong in the Americas" class="h-10 object-contain" onerror="this.style.display='none'">
      <img src="__GSU_LOGO__"   alt="Georgia Southern University" class="h-10 object-contain opacity-90" onerror="this.style.display='none'">
      <img src="__SENAI_LOGO__" alt="SENAI"                       class="h-8  object-contain opacity-90" onerror="this.style.display='none'">
    </div>
    <div class="flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm">
      <span class="material-symbols-outlined text-[#87714D] text-[18px]">calendar_today</span>
      <span class="text-sm font-semibold text-slate-700" id="currentDate"></span>
    </div>
  </div>
  <div class="flex flex-col md:flex-row md:items-start justify-between gap-4">
    <div class="space-y-2 max-w-4xl">
      <h1 class="text-3xl font-bold text-[#011E42] tracking-tight">Projeto FREnTE &mdash; Relat&oacute;rio de Descoberta</h1>
      <p class="text-[11px] font-bold text-[#87714D] uppercase tracking-wider">Fundo de Resili&ecirc;ncia e Ecossistemas nas Trilhas de Estudo</p>
      <p class="text-sm text-slate-500 font-medium leading-relaxed border-l-2 border-[#87714D]/30 pl-4">__ARTICLE_GOAL__</p>
    </div>
    <p class="text-[11px] font-bold text-[#87714D] uppercase tracking-wider text-right shrink-0" id="header-meta">Carregando&hellip;</p>
  </div>
  <div class="gold-bar w-full"></div>
</header>

<!-- ── METRICS ─────────────────────────────────────────────────────── -->
<div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
  <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5 flex items-start gap-4 hover:-translate-y-0.5 hover:shadow-md transition-all">
    <div class="p-2.5 bg-blue-50 rounded-lg">
      <span class="material-symbols-outlined text-[#011E42] text-2xl">database</span>
    </div>
    <div>
      <p class="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Datasets</p>
      <p class="text-3xl font-bold text-slate-900 mt-1 leading-none" id="m-total">&mdash;</p>
    </div>
  </div>
  <div class="bg-white rounded-xl border border-slate-100 shadow-sm p-5 flex items-start gap-4 hover:-translate-y-0.5 hover:shadow-md transition-all">
    <div class="p-2.5 bg-emerald-50 rounded-lg">
      <span class="material-symbols-outlined text-emerald-600 text-2xl">download_for_offline</span>
    </div>
    <div>
      <p class="text-xs font-bold text-slate-400 uppercase tracking-wider">Download Direto</p>
      <p class="text-3xl font-bold text-slate-900 mt-1 leading-none" id="m-direct">&mdash;</p>
    </div>
  </div>
  <div class="bg-white rounded-xl border border-slate-100 border-b-2 border-b-red-200 shadow-sm p-5 flex items-start gap-4 hover:-translate-y-0.5 hover:shadow-md transition-all">
    <div class="p-2.5 bg-red-50 rounded-lg">
      <span class="material-symbols-outlined text-red-400 text-2xl">error</span>
    </div>
    <div>
      <p class="text-xs font-bold text-slate-400 uppercase tracking-wider">Lacunas Cr&iacute;ticas</p>
      <p class="text-3xl font-bold text-slate-900 mt-1 leading-none" id="m-gaps">&mdash;</p>
    </div>
  </div>
  <div class="bg-[#011E42] rounded-xl shadow-lg p-5 flex items-start gap-4 hover:-translate-y-0.5 hover:shadow-xl transition-all">
    <div class="p-2.5 bg-white/10 rounded-lg">
      <span class="material-symbols-outlined text-white text-2xl">route</span>
    </div>
    <div>
      <p class="text-xs font-bold text-slate-300 uppercase tracking-wider">Trilhas Executadas</p>
      <p class="text-3xl font-bold text-white mt-1 leading-none" id="m-tracks">&mdash;</p>
    </div>
  </div>
</div>

<!-- ── FILTERS ─────────────────────────────────────────────────────── -->
<div class="bg-white rounded-xl border border-slate-200 shadow-sm px-5 py-3 flex flex-wrap gap-2 items-center">
  <select id="f-level"    onchange="applyFilters()" class="text-xs border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 text-slate-700 focus:outline-none focus:border-[#1B75BB] cursor-pointer">
    <option value="">N&iacute;vel &#x25BE;</option>
    <option value="macro">Macro</option>
    <option value="meso">Meso</option>
    <option value="bridge">Bridge</option>
    <option value="micro">Micro</option>
  </select>
  <select id="f-format"   onchange="applyFilters()" class="text-xs border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 text-slate-700 focus:outline-none focus:border-[#1B75BB] cursor-pointer">
    <option value="">Formato &#x25BE;</option>
    <option value="structured">Estruturado</option>
    <option value="semi_structured">Semi-estruturado</option>
    <option value="geospatial_platform">Geoespacial</option>
    <option value="academic_paper">Artigo</option>
    <option value="pdf_report">PDF</option>
    <option value="unknown">Desconhecido</option>
  </select>
  <select id="f-access"   onchange="applyFilters()" class="text-xs border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 text-slate-700 focus:outline-none focus:border-[#1B75BB] cursor-pointer">
    <option value="">Acesso &#x25BE;</option>
    <option value="direct_download">Download direto</option>
    <option value="api_access">API</option>
    <option value="web_portal">Portal web</option>
    <option value="geospatial_platform">Plataforma geo</option>
    <option value="pdf_extraction">PDF</option>
    <option value="restricted">Restrito</option>
    <option value="unknown">Desconhecido</option>
  </select>
  <select id="f-priority" onchange="applyFilters()" class="text-xs border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 text-slate-700 focus:outline-none focus:border-[#1B75BB] cursor-pointer">
    <option value="">Prioridade &#x25BE;</option>
    <option value="high">Alta</option>
    <option value="medium">M&eacute;dia</option>
    <option value="low">Baixa</option>
  </select>
  <input id="f-search" type="text" placeholder="&#x1F50D; Dataset, URL, par&acirc;metro&hellip;"
    oninput="applyFilters()"
    class="flex-1 min-w-40 text-xs border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 text-slate-700 focus:outline-none focus:border-[#1B75BB]">
  <span class="text-xs text-slate-400 ml-auto" id="filter-count"></span>
  <button onclick="clearFilters()" class="text-xs text-slate-400 border border-slate-200 rounded-lg px-3 py-2 hover:text-slate-700 hover:border-slate-300 transition-colors">Limpar filtros</button>
</div>

<!-- ── MAIN 2-COL GRID ──────────────────────────────────────────────── -->
<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">

  <!-- LEFT: Table + Coverage -->
  <div class="lg:col-span-2 space-y-6">

    <!-- Table card -->
    <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div class="px-6 py-4 border-b border-slate-100">
        <h2 class="text-xl font-bold text-[#011E42]">Datasets Descobertos</h2>
      </div>
      <div class="overflow-x-auto custom-scrollbar">
        <table class="w-full text-left">
          <thead>
            <tr class="bg-slate-50 border-b border-slate-100">
              <th class="px-5 py-3 text-xs font-bold text-slate-400 uppercase tracking-wider w-10">#</th>
              <th class="px-5 py-3 text-xs font-bold text-slate-400 uppercase tracking-wider sortable" data-col="dataset_name">Dataset <span class="sort-icon"></span></th>
              <th class="px-5 py-3 text-xs font-bold text-slate-400 uppercase tracking-wider w-24 sortable" data-col="hierarchy_level">N&iacute;vel <span class="sort-icon"></span></th>
              <th class="px-5 py-3 text-xs font-bold text-slate-400 uppercase tracking-wider w-32 sortable" data-col="data_format">Formato <span class="sort-icon"></span></th>
              <th class="px-5 py-3 text-xs font-bold text-slate-400 uppercase tracking-wider w-28 sortable" data-col="access_type">Acesso <span class="sort-icon"></span></th>
              <th class="px-5 py-3 text-xs font-bold text-slate-400 uppercase tracking-wider w-12">URL</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100" id="table-body"></tbody>
        </table>
      </div>
    </div>

    <!-- Coverage card -->
    <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
      <h2 class="text-xl font-bold text-[#011E42] mb-6">Cobertura</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <p class="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-4">Por n&iacute;vel hier&aacute;rquico</p>
          <div class="space-y-4" id="coverage-level"></div>
        </div>
        <div>
          <p class="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-4">Por formato de dados</p>
          <div class="space-y-4" id="coverage-format"></div>
        </div>
      </div>
    </div>

  </div><!-- /left col -->

  <!-- RIGHT: Gaps + Steps + Logos -->
  <div class="space-y-6">

    <!-- Gaps card -->
    <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div class="px-5 py-4 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
        <span class="material-symbols-outlined text-[#87714D] text-[18px]">warning</span>
        <h2 class="text-xs font-bold text-slate-600 uppercase tracking-widest">Fontes Esperadas vs. Encontradas</h2>
      </div>
      <div class="p-4 space-y-2" id="gaps-grid"></div>
    </div>

    <!-- Next steps card -->
    <div class="bg-[#011E42] rounded-xl shadow-lg overflow-hidden text-white">
      <div class="px-5 py-4 bg-white/5 border-b border-white/10 flex items-center gap-2">
        <span class="material-symbols-outlined text-[#87714D] text-[18px]">assignment_turned_in</span>
        <h2 class="text-xs font-bold text-white/80 uppercase tracking-widest">Pr&oacute;ximos Passos</h2>
      </div>
      <div class="p-5 space-y-3" id="next-steps"></div>
    </div>


  </div><!-- /right col -->

</div><!-- /main grid -->
</div><!-- /max-w-7xl -->

<script>
// ── DATA ──────────────────────────────────────────────────────────────
const DATASETS    = __DATASETS_JSON__;
const METADATA    = __METADATA_JSON__;
const SEARCH_PLAN = __SEARCH_PLAN_JSON__;

// ── EXPECTED SOURCES (gap detection) ─────────────────────────────────
const EXPECTED_SOURCES = [
  { name: "ANA HidroWeb",               domain: "snirh.gov.br",              level: "macro"  },
  { name: "CETESB QUALAR",              domain: "qualar.cetesb.sp.gov.br",   level: "bridge" },
  { name: "SNIS saneamento",            domain: "app4.mdr.gov.br",           level: "meso"   },
  { name: "MapBiomas",                  domain: "mapbiomas.org",              level: "macro"  },
  { name: "INPE PRODES/DETER",          domain: "terrabrasilis.dpi.inpe.br", level: "meso"   },
  { name: "INPE BDQueimadas",           domain: "queimadas.dgi.inpe.br",     level: "meso"   },
  { name: "ONS opera\u00e7\u00e3o",    domain: "ons.org.br",                level: "bridge" },
  { name: "IBGE SIDRA",                 domain: "sidra.ibge.gov.br",         level: "macro"  },
  { name: "Sentinel-2 / Landsat",       domain: "copernicus.eu",             level: "micro"  },
  { name: "CDOM/MOD artigos",           keywords: ["cdom","organic matter","tiet\u00ea","tiete"], level: "micro" },
  { name: "SRTM / ALOS DEM",           domain: "earthexplorer.usgs.gov",    level: "macro"  },
  { name: "CHIRPS precipita\u00e7\u00e3o", domain: "chc.ucsb.edu",         level: "macro"  },
  { name: "SICAR/CAR APP",              domain: "car.gov.br",                level: "meso"   },
  { name: "IBGE PAM agro",              keywords: ["PAM","produ\u00e7\u00e3o agr\u00edcola","producao agricola"], level: "meso" },
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
function badgeLevel(v)    { return badge("lv-"  + (v||"unknown"), LEVEL_LABELS[v]    || v || "?"); }
function badgeFormat(v)   { return badge("fmt-" + (v||"unknown"), FORMAT_LABELS[v]   || v || "?"); }
function badgeAccess(v)   { return badge("acc-" + (v||"unknown"), ACCESS_LABELS[v]   || v || "?"); }
function badgePriority(v) { return badge("pri-" + (v||"low"),     PRIORITY_LABELS[v] || v || "?"); }

// ── GAP DETECTION ─────────────────────────────────────────────────────
function isFound(exp) {
  return DATASETS.some(function(d) {
    var url  = (d.url || "").toLowerCase();
    var text = [d.dataset_name, d.dataset_description, d.title].join(" ").toLowerCase();
    if (exp.domain)   return url.includes(exp.domain.toLowerCase());
    if (exp.keywords) return exp.keywords.some(function(k) { return text.includes(k.toLowerCase()); });
    return false;
  });
}
function foundVia(exp) {
  var d = DATASETS.find(function(d) {
    var url  = (d.url || "").toLowerCase();
    var text = [d.dataset_name, d.dataset_description, d.title].join(" ").toLowerCase();
    if (exp.domain)   return url.includes(exp.domain.toLowerCase());
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
  document.getElementById("currentDate").textContent =
    new Date().toLocaleDateString("pt-BR", { day:"numeric", month:"long", year:"numeric" });
}

// ── FILTERS ───────────────────────────────────────────────────────────
function applyFilters() {
  var level    = document.getElementById("f-level").value;
  var format   = document.getElementById("f-format").value;
  var access   = document.getElementById("f-access").value;
  var priority = document.getElementById("f-priority").value;
  var search   = document.getElementById("f-search").value.toLowerCase();

  filteredData = DATASETS.filter(function(d) {
    if (level    && d.hierarchy_level !== level)    return false;
    if (format   && d.data_format     !== format)   return false;
    if (access   && d.access_type     !== access)   return false;
    if (priority && d.track_priority  !== priority) return false;
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
    if (sortCol === "track_priority") {
      va = PRIORITY_ORDER[va] != null ? PRIORITY_ORDER[va] : 99;
      vb = PRIORITY_ORDER[vb] != null ? PRIORITY_ORDER[vb] : 99;
    }
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
    tbody.innerHTML = '<tr><td colspan="6" class="px-6 py-14 text-center text-sm text-slate-400">Nenhum dataset encontrado com os filtros selecionados.</td></tr>';
    return;
  }
  var html = "";
  filteredData.forEach(function(d, i) {
    var isExp = expandedIdx === i;
    var name  = esc(d.dataset_name || d.title || "Sem t\u00edtulo");
    var desc  = esc(d.dataset_description || d.snippet || "");

    html += '<tr class="data-row hover:bg-slate-50 transition-colors' + (isExp ? " expanded" : "") + '" onclick="toggleDetail(' + i + ')">';
    html += '<td class="px-5 py-3.5 text-xs font-bold text-slate-400">' + (d.rank || (i+1)) + '</td>';
    html += '<td class="px-5 py-3.5 max-w-xs">'
          + '<span class="block text-sm font-semibold text-[#011E42] truncate">' + name + '</span>'
          + (desc ? '<span class="block text-xs text-slate-400 truncate mt-0.5">' + desc + '</span>' : '')
          + '</td>';
    html += '<td class="px-5 py-3.5">' + badgeLevel(d.hierarchy_level)  + '</td>';
    html += '<td class="px-5 py-3.5">' + badgeFormat(d.data_format)     + '</td>';
    html += '<td class="px-5 py-3.5">' + badgeAccess(d.access_type)     + '</td>';
    html += '<td class="px-5 py-3.5 text-center">'
          + '<a href="' + esc(d.url) + '" target="_blank" onclick="event.stopPropagation()" '
          + 'class="text-slate-400 hover:text-[#87714D] transition-colors">'
          + '<span class="material-symbols-outlined text-[18px]">open_in_new</span></a></td>';
    html += '</tr>';

    if (isExp) {
      html += '<tr><td colspan="6" class="bg-amber-50/40 border-t border-amber-100">' + renderDetail(d) + '</td></tr>';
    }
  });
  tbody.innerHTML = html;
}

function renderDetail(d) {
  var params   = (d.key_parameters || []).join(", ") || "\u2014";
  var spatial  = d.spatial_coverage   || "\u2014";
  var temporal = d.temporal_coverage  || "\u2014";
  var notes    = d.access_notes       || "\u2014";
  var desc     = d.dataset_description || d.snippet || "Sem descri\u00e7\u00e3o dispon\u00edvel.";
  var guide    = d.collection_guide || null;

  var h = '<div class="p-5"><div class="detail-grid">';
  h += field("Descri\u00e7\u00e3o",     desc,              true);
  h += field("Par\u00e2metros",          params,            false);
  h += field("Cobertura temporal",       temporal,          false);
  h += field("Cobertura espacial",       spatial,           false);
  h += field("Eixo tem\u00e1tico",       d.thematic_axis   || "\u2014", false);
  h += field("Categoria",                d.source_category || "\u2014", false);
  h += field("Trilha de origem",         d.track_origin    || "\u2014", false);
  h += field("Dom\u00ednio",            d.source_domain   || "\u2014", false);
  h += '<div class="detail-field detail-full">'
    +  '<span class="field-label">URL</span>'
    +  '<span class="field-value"><a href="' + esc(d.url) + '" target="_blank">' + esc(d.url) + '</a></span>'
    +  '</div>';
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
    return '<div class="cg-unavailable">Guia de coleta n\u00e3o dispon\u00edvel &mdash; rode com Firecrawl ativado ou navegue manualmente pelo portal.</div>';
  }

  var steps = (guide.steps || []).map(function(step, i) {
    return '<li class="flex gap-2 text-xs text-slate-700 mb-1.5">'
      + '<span class="shrink-0 font-bold text-[#87714D]">' + (i+1) + '.</span>'
      + esc(step) + '</li>';
  }).join("");
  var caveats = (guide.caveats || []).map(function(note) { return '<li>' + esc(note) + '</li>'; }).join("");
  var filterEntries = Object.entries(guide.filters_available || {});
  var filters = filterEntries.length
    ? '<ul class="cg-list">' + filterEntries.map(function(e) {
        return '<li><strong>' + esc(e[0]) + ':</strong> ' + esc(e[1]) + '</li>';
      }).join("") + '</ul>'
    : '<span class="field-value">\u2014</span>';
  var directDownloads = (guide.direct_download_urls || []).length
    ? '<div class="cg-downloads">' + guide.direct_download_urls.map(function(url) {
        return '<a href="' + esc(url) + '" target="_blank">\u25BE ' + esc(url) + '</a>';
      }).join("") + '</div>'
    : '<span class="field-value">\u2014</span>';

  var effortIcon = { minutes:"bolt", hours:"schedule", days:"event", requires_contact:"mail" };
  var effort = guide.estimated_effort || "hours";

  var h = '<div class="mt-4 p-4 bg-white rounded-xl border border-slate-200">';
  h += '<div class="flex items-center gap-2 mb-4">'
    +  '<span class="material-symbols-outlined text-[#87714D] text-[16px]">map</span>'
    +  '<span class="text-xs font-bold text-slate-600 uppercase tracking-wider">Guia de coleta</span>'
    +  '</div>';
  h += '<div class="cg-grid">';
  h += '<div><span class="field-label">Esfor\u00e7o estimado</span>'
    +  '<span class="field-value flex items-center gap-1">'
    +  '<span class="material-symbols-outlined text-[13px] text-[#87714D]">' + (effortIcon[effort]||"schedule") + '</span>'
    +  esc(effort) + '</span></div>';
  h += '<div><span class="field-label">Requer login</span><span class="field-value">'
    +  (guide.requires_login ? "\u26a0\ufe0f Sim" : "\u2713 N\u00e3o") + '</span></div>';
  h += '<div><span class="field-label">Formato de download</span><span class="field-value">'
    +  esc(guide.download_format || "\u2014") + '</span></div>';
  h += '<div><span class="field-label">Downloads diretos</span>' + directDownloads + '</div>';
  h += '<div style="grid-column:1/-1"><span class="field-label">Passos</span>'
    +  (steps ? '<ol class="mt-1 space-y-0.5">' + steps + '</ol>' : '<span class="field-value">\u2014</span>') + '</div>';
  h += '<div style="grid-column:1/-1"><span class="field-label">Filtros identificados</span>' + filters + '</div>';
  h += '<div style="grid-column:1/-1"><span class="field-label">Alertas</span>'
    +  (caveats ? '<ul class="cg-list">' + caveats + '</ul>' : '<span class="field-value">\u2014</span>') + '</div>';
  h += '</div></div>';
  return h;
}

function toggleDetail(i) {
  expandedIdx = expandedIdx === i ? -1 : i;
  renderTable();
}

// ── COVERAGE ──────────────────────────────────────────────────────────
function renderCoverage() {
  var levels      = ["macro","meso","bridge","micro"];
  var levelColors = { macro:"rgba(1,30,66,.18)", meso:"rgba(1,30,66,.38)", bridge:"rgba(1,30,66,.65)", micro:"rgba(1,30,66,.90)" };
  var levelCount  = {};
  levels.forEach(function(l) { levelCount[l] = DATASETS.filter(function(d) { return d.hierarchy_level === l; }).length; });
  var maxL = Math.max.apply(null, levels.map(function(l) { return levelCount[l]||0; }).concat([1]));
  document.getElementById("coverage-level").innerHTML = levels.map(function(l) {
    var n = levelCount[l] || 0;
    return '<div class="space-y-1.5">'
      + '<div class="flex justify-between items-baseline">'
      + '<span class="text-sm font-semibold text-slate-700">' + (LEVEL_LABELS[l]||l) + '</span>'
      + '<span class="text-sm font-bold text-[#87714D]">' + n + '</span>'
      + '</div>'
      + '<div class="h-2 w-full bg-slate-100 rounded-full overflow-hidden">'
      + '<div class="h-full rounded-full transition-all duration-700" style="width:' + Math.round(n/maxL*100) + '%;background:' + levelColors[l] + '"></div>'
      + '</div></div>';
  }).join("");

  var formats    = ["structured","semi_structured","geospatial_platform","academic_paper","pdf_report","unknown"];
  var fmtColors  = { structured:"var(--fmt-structured)", semi_structured:"var(--fmt-semi)", geospatial_platform:"var(--fmt-geo)", academic_paper:"var(--fmt-paper)", pdf_report:"var(--fmt-pdf)", unknown:"var(--fmt-unknown)" };
  var fmtCount   = {};
  formats.forEach(function(f) { fmtCount[f] = DATASETS.filter(function(d) { return d.data_format === f; }).length; });
  var maxF = Math.max.apply(null, formats.map(function(f) { return fmtCount[f]||0; }).concat([1]));
  document.getElementById("coverage-format").innerHTML = formats
    .filter(function(f) { return fmtCount[f] > 0; })
    .map(function(f) {
      var n = fmtCount[f];
      return '<div class="space-y-1.5">'
        + '<div class="flex justify-between items-baseline">'
        + '<span class="text-sm font-semibold text-slate-700">' + (FORMAT_LABELS[f]||f) + '</span>'
        + '<span class="text-sm font-bold text-[#87714D]">' + n + '</span>'
        + '</div>'
        + '<div class="h-2 w-full bg-slate-100 rounded-full overflow-hidden">'
        + '<div class="h-full rounded-full transition-all duration-700" style="width:' + Math.round(n/maxF*100) + '%;background:' + fmtColors[f] + '"></div>'
        + '</div></div>';
    }).join("");
}

// ── GAPS ──────────────────────────────────────────────────────────────
function renderGaps() {
  document.getElementById("gaps-grid").innerHTML = EXPECTED_SOURCES.map(function(e) {
    var found = isFound(e);
    var via   = foundVia(e);
    return '<div class="flex items-start gap-3 p-3 rounded-lg border transition-opacity hover:opacity-75 '
      + (found ? 'bg-emerald-50/50 border-emerald-100' : 'bg-red-50/20 border-red-100/60') + '">'
      + '<span class="material-symbols-outlined text-[18px] mt-0.5 shrink-0 '
      + (found ? 'text-emerald-500' : 'text-red-400') + '">'
      + (found ? 'check_circle' : 'cancel') + '</span>'
      + '<div>'
      + '<p class="text-sm font-bold text-slate-700">' + esc(e.name) + '</p>'
      + '<p class="text-[10px] font-bold uppercase tracking-wider '
      + (found ? 'text-emerald-600' : 'text-slate-400') + '">'
      + (found ? 'encontrada' + (via ? ' \u00b7 ' + esc(via) : '') : 'buscar manualmente')
      + '</p></div></div>';
  }).join("");
}

// ── NEXT STEPS ────────────────────────────────────────────────────────
function renderNextSteps() {
  var steps = [];

  EXPECTED_SOURCES.filter(function(e) { return !isFound(e); }).forEach(function(e) {
    var url = e.domain ? "https://" + e.domain : "";
    steps.push({ main: "Buscar manualmente: <strong class='text-white'>" + esc(e.name) + "</strong>", sub: url });
  });

  DATASETS.filter(function(d) { return d.data_format === "pdf_report"; }).forEach(function(d) {
    steps.push({ main: "Extrair tabelas: <strong class='text-white'>" + esc(d.dataset_name || d.title) + "</strong>", sub: "Requer OCR/parsing de PDF" });
  });

  [
    { main: "SNIS \u00d7 CETESB DBO",                 sub: "Consist\u00eancia esgoto vs. qualidade da \u00e1gua" },
    { main: "MapBiomas \u00d7 turbidez CETESB",        sub: "Correlacionar desmatamento e turbidez" },
    { main: "Clorofila in situ \u00d7 sat\u00e9lite",  sub: "Calibrar sensoriamento remoto" },
    { main: "Uso do solo \u00d7 COT reservat\u00f3rios", sub: "Hip\u00f3tese central: carbono org\u00e2nico" },
  ].forEach(function(c) { steps.push(c); });

  if (!steps.length) {
    document.getElementById("next-steps").innerHTML =
      '<p class="text-sm text-white/60 text-center py-4">Todas as fontes esperadas foram encontradas.</p>';
    return;
  }

  document.getElementById("next-steps").innerHTML = steps.map(function(s, i) {
    return '<div class="flex items-start gap-3 group">'
      + '<div class="shrink-0 w-6 h-6 rounded-full bg-white/10 border border-white/20 flex items-center justify-center text-[10px] font-bold text-[#C4A86C] group-hover:bg-[#87714D] group-hover:text-white transition-colors">' + (i+1) + '</div>'
      + '<div><p class="text-sm font-medium text-white/80 group-hover:text-white transition-colors">' + s.main + '</p>'
      + (s.sub ? '<p class="text-[10px] text-white/40 mt-0.5">' + esc(s.sub) + '</p>' : '')
      + '</div></div>';
  }).join("");
}

// ── SORT HEADER CLICKS ────────────────────────────────────────────────
document.querySelectorAll("th.sortable").forEach(function(th) {
  th.addEventListener("click", function() { sortData(th.dataset.col); });
});

// ── INIT ──────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", function() {
  renderMetrics();
  applyFilters();
  renderCoverage();
  renderGaps();
  renderNextSteps();
});
</script>
</body>
</html>"""
