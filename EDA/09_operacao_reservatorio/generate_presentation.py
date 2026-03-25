"""
Gera apresentação HTML das figuras EDA — cascata Tietê
Mesmo estilo visual do relatorio_100k.html (Tailwind + Bitter/Inter + GSU colors)
"""

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = Path(__file__).resolve().parent / "figures"
IMG_DIR = ROOT / "src" / "img"
OUT = Path(__file__).resolve().parent / "apresentacao_reservatorios.html"


def b64(path: Path) -> str:
    ext = path.suffix.lower()
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp", ".svg": "image/svg+xml"}
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime.get(ext, 'image/png')};base64,{data}"


# ── figuras com contexto analítico ──────────────────────────────────────────
FIGURES = [
    {
        "id": "fig1",
        "file": "fig1_volume_cascata.png",
        "title": "Volume Útil Armazenado na Cascata do Tietê (2000–2025)",
        "icon": "water",
        "tag": "Armazenamento",
        "tag_color": "blue",
        "summary": (
            "Evolução temporal do volume útil armazenado (% da capacidade máxima) nos seis "
            "reservatórios da cascata do Tietê: Barra Bonita, Bariri, Ibitinga, Promissão, "
            "Nova Avanhandava e Três Irmãos."
        ),
        "interpretation": (
            "A crise hídrica de 2014–2015 é o evento mais expressivo do período, com todos os "
            "reservatórios atingindo volumes criticamente baixos de forma simultânea — evidenciando "
            "o comportamento em cascata da bacia. Três Irmãos, o maior reservatório (17.029 hm³), "
            "apresenta maior inércia e amortece melhor as oscilações interanuais. Barra Bonita e "
            "Bariri, localizados na cabeceira, respondem mais rapidamente a eventos extremos de "
            "seca ou cheia. O padrão sazonal (baixa no fim do período seco, recarga entre novembro "
            "e março) é consistente em todos os reservatórios ao longo dos 25 anos."
        ),
        "highlight": "Crise de 2014–2015 reduziu o volume de Barra Bonita a menos de 5% da capacidade.",
    },
    {
        "id": "fig2",
        "file": "fig2_vazao_cabeceira_foz.png",
        "title": "Vazão Afluente: Cabeceira (Barra Bonita) vs Foz (Três Irmãos)",
        "icon": "waves",
        "tag": "Hidrologia",
        "tag_color": "green",
        "summary": (
            "Comparação da vazão afluente diária (m³/s) entre o primeiro reservatório da cascata "
            "(Barra Bonita, cabeceira) e o último (Três Irmãos, foz), com média móvel de 12 meses "
            "sobreposta para evidenciar tendências de longo prazo."
        ),
        "interpretation": (
            "A foz (Três Irmãos) concentra toda a descarga acumulada da bacia, operando com "
            "vazões médias substancialmente maiores que a cabeceira. A média móvel de 12 meses "
            "revela ciclos plurianuais associados ao ENOS: anos La Niña tendem a reduzir as "
            "afluências no sudeste brasileiro, enquanto El Niño provoca anomalias positivas. "
            "A amplitude das cheias em Barra Bonita é proporcionalmente maior, refletindo a "
            "menor área de amortecimento na cabeceira. A convergência de tendências entre as "
            "duas séries confirma que eventos climáticos de grande escala afetam toda a bacia "
            "de forma homogênea."
        ),
        "highlight": "A amplitude sazonal na foz é ~4× maior que na cabeceira, evidenciando o efeito acumulativo da bacia.",
    },
    {
        "id": "fig3",
        "file": "fig3_tempo_residencia.png",
        "title": "Tempo de Residência Estimado por Reservatório (2000–2025)",
        "icon": "hourglass_empty",
        "tag": "Qualidade de Água",
        "tag_color": "purple",
        "summary": (
            "Tempo de residência hidráulica estimado (dias) para cada reservatório, calculado como "
            "a razão entre o volume armazenado (hm³) e a vazão defluente (m³/s × 86.400 s/dia). "
            "A linha tracejada marca o limiar crítico de 180 dias."
        ),
        "interpretation": (
            "O tempo de residência é um indicador-chave da qualidade da água: valores elevados "
            "favorecem estratificação térmica, consumo de oxigênio e proliferação de cianobactérias "
            "(eutrofização). Três Irmãos e Promissão apresentam os maiores tempos de residência "
            "médios, ultrapassando frequentemente 180 dias no período seco. Durante a crise de "
            "2014–2015, os tempos de residência dispararam em todos os reservatórios, amplificando "
            "os riscos para o abastecimento e os ecossistemas aquáticos. A variabilidade "
            "interanual é maior nos reservatórios intermediários (Ibitinga, Bariri), que dependem "
            "fortemente das decisões de operação dos reservatórios a montante."
        ),
        "highlight": "Limiar de 180 dias frequentemente ultrapassado em Três Irmãos e Promissão no período seco.",
    },
    {
        "id": "fig4",
        "file": "fig4_correlacao_vol_tr.png",
        "title": "Correlação entre Volume Armazenado e Tempo de Residência",
        "icon": "scatter_plot",
        "tag": "Correlação",
        "tag_color": "orange",
        "summary": (
            "Diagrama de dispersão (volume útil % × tempo de residência em dias) para cada "
            "reservatório, com linha de regressão linear e coeficiente de correlação de Pearson (r). "
            "Cada ponto representa um dia de operação ao longo de 25 anos."
        ),
        "interpretation": (
            "A correlação positiva entre volume armazenado e tempo de residência — contraintuitiva "
            "à primeira vista — reflete a dinâmica operacional: reservatórios mais cheios tendem a "
            "ter maiores volumes absolutos que, divididos por vazões defluentes controladas, "
            "resultam em maiores residências. A dispersão elevada em todos os reservatórios indica "
            "que a operação (turbinamento, vertimento) é o fator dominante sobre a hidrodinâmica "
            "natural. Coeficientes r mais próximos de 1 em Três Irmãos e Promissão sugerem que, "
            "nesses reservatórios maiores, o volume disponível tem papel mais determinante no "
            "tempo de residência do que em reservatórios menores com maior variabilidade operacional."
        ),
        "highlight": "Dispersão elevada evidencia que decisões operacionais superam a sazonalidade natural na determinação da residência.",
    },
    {
        "id": "fig5",
        "file": "fig5_anomalia_anual.png",
        "title": "Anomalia Anual de Volume Armazenado vs Média Histórica (2000–2025)",
        "icon": "bar_chart",
        "tag": "Anomalia Climática",
        "tag_color": "red",
        "summary": (
            "Anomalia do volume útil médio anual em relação à média histórica do período (2000–2025) "
            "para cada reservatório, expressa em pontos percentuais. Barras positivas indicam anos "
            "mais úmidos; barras negativas, anos mais secos que a média."
        ),
        "interpretation": (
            "O gráfico revela que 2014 e 2015 foram os anos com maior desvio negativo em "
            "praticamente todos os reservatórios, confirmando a magnitude da crise hídrica como "
            "evento sem precedentes no período analisado. Os anos de 2009–2010 e 2019–2020 "
            "apresentaram anomalias positivas pronunciadas, associadas a eventos La Niña fortes. "
            "A sincronização das anomalias entre os seis reservatórios confirma que a variabilidade "
            "interanual é predominantemente climática (precipitação na bacia) e não operacional. "
            "A tendência de anos mais secos após 2019 — exceto 2020 — é consistente com "
            "projeções de mudanças climáticas para a Bacia do Alto Tietê."
        ),
        "highlight": "2014–2015: único biênio com anomalia negativa simultânea em todos os reservatórios da cascata.",
    },
    # ── PRESSÕES AMBIENTAIS ──────────────────────────────────────────────────
    {
        "id": "fig6",
        "file": "fig6_queimadas_corredor.png",
        "title": "Focos de Calor no Corredor do Rio Tietê (2000–2024)",
        "icon": "local_fire_department",
        "tag": "Queimadas",
        "tag_color": "red",
        "summary": (
            "Contagem anual de focos de calor detectados por satélite (todos os satélites ativos) "
            "no corredor do Rio Tietê (bbox: lon -52.2° a -45.8°, lat -24.0° a -20.5°), com "
            "decomposição por bioma (Cerrado vs Mata Atlântica). Fonte: INPE BDQueimadas, 2000–2024, "
            "totalizando 1.116.805 detecções no período."
        ),
        "interpretation": (
            "Os anos 2019–2021 concentram os maiores volumes de focos de calor da série histórica, "
            "coincidindo com o período de seca severa pós-2019 e com políticas ambientais que "
            "resultaram em menor fiscalização. O Cerrado domina as detecções no corredor médio "
            "e baixo do Tietê (UGRHI 16, 19), enquanto fragmentos de Mata Atlântica concentram "
            "focos na cabeceira (UGRHI 5, 10). A correlação temporal entre picos de queimadas "
            "e baixos volumes nos reservatórios sugere sinergia entre déficit hídrico e pressão "
            "de fogo na bacia. A média móvel de 3 anos evidencia uma escalada estrutural a partir "
            "de 2017, interrompida apenas em 2022–2023."
        ),
        "highlight": "2020–2021: maior sequência bianual de focos desde o início da série; ~60% acima da média histórica.",
        "section": "pressoes",
    },
    {
        "id": "fig7",
        "file": "fig7_snis_esgoto.png",
        "title": "Cobertura de Coleta e Tratamento de Esgoto — Municípios SP (2010–2020)",
        "icon": "plumbing",
        "tag": "Saneamento",
        "tag_color": "blue",
        "summary": (
            "Evolução dos índices medianos de coleta de esgoto (IN015) e de esgoto tratado "
            "referido à água consumida (IN046) para municípios do Estado de São Paulo com "
            "prestadores locais públicos. Fonte: SNIS — Sistema Nacional de Informações sobre "
            "Saneamento, 2010–2020 (210–232 municípios/ano)."
        ),
        "interpretation": (
            "O gap estrutural entre coleta (IN015 ≈ 85%) e tratamento efetivo (IN046 ≈ 80%) "
            "persiste ao longo de toda a série. Isso significa que, mesmo onde existe rede "
            "coletora, cerca de 5–8 p.p. do esgoto coletado não recebe tratamento antes do "
            "lançamento — uma carga orgânica direta sobre os tributários que deságuam na cascata "
            "do Tietê. O avanço dos índices de 2010 a 2019 (+6 p.p. em coleta, +6 p.p. em "
            "tratamento) reflete investimentos do PAC Saneamento, mas o ritmo desacelerou em "
            "2020, ano com dados preliminares. A persistência do gap coleta-tratamento é um "
            "indicador-chave do aporte de DBO nos reservatórios, especialmente nos de menor "
            "tempo de residência (Barra Bonita, Bariri)."
        ),
        "highlight": "Gap coleta–tratamento persistente: ~5 p.p. em 2020 representam esgoto coletado mas não tratado antes do lançamento.",
        "section": "pressoes",
    },
    {
        "id": "fig8",
        "file": "fig8_residuos_iqr.png",
        "title": "Índice de Qualidade de Aterros (IQR) — Municípios da Bacia do Tietê (2017–2021)",
        "icon": "delete_sweep",
        "tag": "Resíduos Sólidos",
        "tag_color": "purple",
        "summary": (
            "Evolução do IQR mediano (Índice de Qualidade de Aterros de Resíduos) para municípios "
            "da bacia do Tietê (UGRHIs 5, 10, 13, 16, 19) e para o Estado de São Paulo como "
            "referência. Fonte: CETESB — Inventário Estadual de Resíduos Sólidos Urbanos, 2017–2021. "
            "Escala CETESB: Inadequado < 6.0 | Controlado 6.0–8.0 | Adequado > 8.0."
        ),
        "interpretation": (
            "Os municípios da bacia do Tietê apresentam IQR mediano de 9.2 (2019–2020), acima "
            "da mediana estadual de 9.0, indicando que o corredor conta com aterros em condições "
            "predominantemente adequadas. A melhoria da qualidade de aterros entre 2017 (mediana "
            "8.5) e 2019 (9.0–9.2) reflete o programa paulista de encerramento de lixões. No "
            "entanto, o IQR mede condições de operação dos aterros, não o potencial de lixiviação "
            "ou a distância dos corpos d'água. Municípios com IQR controlado ou inadequado "
            "localizados na faixa ripária representam risco de contaminação de lençóis e tributários "
            "que drenam diretamente para os reservatórios. A leve queda de 2021 (9.2 → 8.9 na bacia) "
            "merece monitoramento continuado."
        ),
        "highlight": "Municípios da bacia Tietê superam a média estadual no IQR — porém 2021 registra primeira queda no período.",
        "section": "pressoes",
    },
]

TAG_COLORS = {
    "blue":   ("rgba(27,117,187,.10)", "#1B75BB"),
    "green":  ("rgba(15,123,95,.10)",  "#0F7B5F"),
    "purple": ("rgba(107,72,168,.10)", "#6B48A8"),
    "orange": ("rgba(199,93,44,.10)",  "#C75D2C"),
    "red":    ("rgba(180,30,30,.10)",  "#B41E1E"),
}

# ── imagens ──────────────────────────────────────────────────────────────────
logo_100k  = b64(IMG_DIR / "100K.webp")
logo_gsu   = b64(IMG_DIR / "Georgia.png")
logo_senai = b64(IMG_DIR / "SENAI.svg")

fig_srcs = {}
for f in FIGURES:
    p = FIG_DIR / f["file"]
    if p.exists():
        fig_srcs[f["id"]] = b64(p)
    else:
        fig_srcs[f["id"]] = ""
        print(f"  AVISO: {p} não encontrado")


# ── card HTML ────────────────────────────────────────────────────────────────
def figure_card(fig: dict) -> str:
    bg, color = TAG_COLORS[fig["tag_color"]]
    src = fig_srcs[fig["id"]]
    img_html = (
        f'<img src="{src}" alt="{fig["title"]}" '
        f'class="w-full rounded-lg border border-slate-200 shadow-sm">'
        if src else
        '<div class="w-full h-64 rounded-lg border border-dashed border-slate-300 '
        'flex items-center justify-center text-slate-400 text-sm">Imagem não encontrada</div>'
    )
    return f"""
<section class="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden mb-10">
  <!-- cabeçalho do card -->
  <div class="px-8 pt-7 pb-4 flex items-start gap-4">
    <div class="mt-0.5 flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center"
         style="background:{bg}">
      <span class="material-symbols-outlined text-xl" style="color:{color}">{fig["icon"]}</span>
    </div>
    <div class="flex-1">
      <div class="flex flex-wrap items-center gap-2 mb-1">
        <span class="badge" style="background:{bg};color:{color}">{fig["tag"]}</span>
        <span class="text-xs text-slate-400 font-mono">{fig["id"].upper()}</span>
      </div>
      <h2 class="text-xl font-bold text-slate-800" style="font-family:'Bitter',serif">{fig["title"]}</h2>
    </div>
  </div>
  <div class="px-8 pb-2"><div class="gold-bar"></div></div>

  <!-- figura -->
  <div class="px-8 py-5">
    {img_html}
  </div>

  <!-- resumo + interpretação -->
  <div class="px-8 pb-8 grid lg:grid-cols-2 gap-6">
    <!-- O que é -->
    <div>
      <p class="field-label mb-2">
        <span class="material-symbols-outlined text-sm mr-1" style="color:#64748b">description</span>
        O QUE MOSTRA
      </p>
      <p class="text-sm text-slate-600 leading-relaxed">{fig["summary"]}</p>
    </div>
    <!-- Interpretação -->
    <div>
      <p class="field-label mb-2">
        <span class="material-symbols-outlined text-sm mr-1" style="color:#64748b">lightbulb</span>
        INTERPRETAÇÃO ANALÍTICA
      </p>
      <p class="text-sm text-slate-600 leading-relaxed">{fig["interpretation"]}</p>
    </div>
    <!-- destaque -->
    <div class="lg:col-span-2 rounded-lg px-5 py-3 flex items-start gap-3"
         style="background:{bg};border-left:3px solid {color}">
      <span class="material-symbols-outlined text-base flex-shrink-0 mt-0.5" style="color:{color}">star</span>
      <p class="text-sm font-semibold" style="color:{color}">{fig["highlight"]}</p>
    </div>
  </div>
</section>
"""


SECTION_DIVIDER = """
<div class="my-12">
  <div class="gold-bar mb-6"></div>
  <div class="flex items-center gap-4 mb-6">
    <div class="flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center"
         style="background:#011E42">
      <span class="material-symbols-outlined text-2xl text-white">warning</span>
    </div>
    <div>
      <p class="text-xs font-semibold tracking-widest mb-0.5" style="color:#87714D">
        PRESSÕES ANTRÓPICAS NA BACIA
      </p>
      <h2 class="text-2xl font-bold" style="color:#011E42;font-family:'Bitter',serif">
        Queimadas, Saneamento e Resíduos Sólidos
      </h2>
    </div>
  </div>
  <p class="text-sm text-slate-500 max-w-3xl leading-relaxed">
    Além das variáveis hidrológicas e operacionais, a qualidade da água nos reservatórios
    é influenciada diretamente por pressões antrópicas na bacia de drenagem. As três análises
    a seguir quantificam o aporte de queimadas, carga orgânica de esgoto e resíduos sólidos
    ao longo do corredor do Tietê.
  </p>
</div>
"""

cards_html_parts = []
for f in FIGURES:
    if f.get("section") == "pressoes" and not any(
        prev.get("section") == "pressoes" for prev in FIGURES[:FIGURES.index(f)]
    ):
        cards_html_parts.append(SECTION_DIVIDER)
    cards_html_parts.append(figure_card(f))

cards_html = "\n".join(cards_html_parts)

HTML = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Análise EDA — Operação de Reservatórios do Tietê</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Bitter:wght@400;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
<style>
:root {{
  --gsu-blue: #011E42;
  --gsu-gold: #87714D;
}}
body {{ font-family: 'Inter', sans-serif; background:#f8fafc; }}
h1,h2,h3 {{ font-family: 'Bitter', serif; }}
.material-symbols-outlined {{
  font-variation-settings: 'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;
  vertical-align: middle;
}}
.gold-bar {{
  height: 3px;
  background: linear-gradient(90deg, #87714D, #C4A86C, #87714D);
  border-radius: 2px;
}}
.badge {{ display:inline-flex; align-items:center; font-size:10px; font-weight:600;
          padding:2px 8px; border-radius:4px; white-space:nowrap;
          text-transform:uppercase; letter-spacing:.04em; }}
.field-label {{ font-weight:600; font-size:10px; color:#64748b;
               text-transform:uppercase; letter-spacing:.05em;
               display:flex; align-items:center; }}
</style>
</head>
<body class="min-h-screen">

<!-- ── TOP BAR ── -->
<header style="background:var(--gsu-blue)" class="sticky top-0 z-50 shadow-lg">
  <div class="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
    <div class="flex items-center gap-4">
      <img src="{logo_100k}"  alt="Projeto 100K" class="h-9 object-contain">
      <div class="w-px h-7 bg-white/20"></div>
      <img src="{logo_gsu}"   alt="Georgia State University" class="h-8 object-contain brightness-0 invert">
      <img src="{logo_senai}" alt="SENAI" class="h-7 object-contain brightness-0 invert">
    </div>
    <div class="text-right hidden sm:block">
      <p class="text-white/50 text-xs">Projeto FREnTE</p>
      <p class="text-white text-sm font-semibold">EDA · Operação de Reservatórios</p>
    </div>
  </div>
</header>

<!-- ── HERO ── -->
<div style="background:var(--gsu-blue)" class="pb-10 pt-8">
  <div class="max-w-6xl mx-auto px-6">
    <p class="text-xs font-semibold tracking-widest mb-2" style="color:#87714D">
      ANÁLISE EXPLORATÓRIA DE DADOS · BACIA HIDROGRÁFICA DO RIO TIETÊ
    </p>
    <h1 class="text-3xl font-bold text-white leading-tight mb-3">
      Dinâmica Operacional da Cascata de Reservatórios<br>
      <span style="color:#C4A86C">Rio Tietê · 2000–2025</span>
    </h1>
    <p class="text-white/70 text-sm max-w-3xl leading-relaxed mb-6">
      Análise comparativa de variáveis hidrológicas e operacionais nos seis reservatórios
      da cascata do Tietê (Barra Bonita, Bariri, Ibitinga, Promissão, Nova Avanhandava e
      Três Irmãos) com base nos dados abertos do Operador Nacional do Sistema Elétrico (ONS).
      O período de 25 anos (2000–2025) permite contextualizar a crise hídrica de 2014–2015
      e avaliar tendências de longo prazo relevantes para qualidade de água e gestão de
      recursos hídricos.
    </p>
    <!-- meta cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div class="rounded-xl px-4 py-3" style="background:rgba(255,255,255,.07)">
        <span class="material-symbols-outlined text-2xl" style="color:#C4A86C">calendar_month</span>
        <p class="text-white font-bold text-lg mt-1">25 anos</p>
        <p class="text-white/50 text-xs">2000–2025</p>
      </div>
      <div class="rounded-xl px-4 py-3" style="background:rgba(255,255,255,.07)">
        <span class="material-symbols-outlined text-2xl" style="color:#C4A86C">water_dam</span>
        <p class="text-white font-bold text-lg mt-1">6 reservatórios</p>
        <p class="text-white/50 text-xs">Cascata completa</p>
      </div>
      <div class="rounded-xl px-4 py-3" style="background:rgba(255,255,255,.07)">
        <span class="material-symbols-outlined text-2xl" style="color:#C4A86C">table_rows</span>
        <p class="text-white font-bold text-lg mt-1">56.982 registros</p>
        <p class="text-white/50 text-xs">Série diária ONS</p>
      </div>
      <div class="rounded-xl px-4 py-3" style="background:rgba(255,255,255,.07)">
        <span class="material-symbols-outlined text-2xl" style="color:#C4A86C">analytics</span>
        <p class="text-white font-bold text-lg mt-1">8 figuras</p>
        <p class="text-white/50 text-xs">Análises integradas</p>
      </div>
    </div>
  </div>
</div>

<!-- ── GOLD DIVIDER ── -->
<div class="max-w-6xl mx-auto px-6 py-4">
  <div class="gold-bar"></div>
</div>

<!-- ── FONTE ── -->
<div class="max-w-6xl mx-auto px-6 mb-6">
  <div class="rounded-xl border border-slate-200 bg-white px-6 py-4 grid md:grid-cols-3 gap-5">
    <div class="flex items-start gap-3">
      <span class="material-symbols-outlined text-xl flex-shrink-0 mt-0.5" style="color:#1B75BB">water_dam</span>
      <div>
        <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Operação de Reservatórios</p>
        <p class="text-sm text-slate-700"><strong>ONS Dados Abertos</strong> — série diária 2000–2025, 56.982 registros Tietê.
        <span class="font-mono text-xs text-blue-600">dados.ons.org.br</span></p>
      </div>
    </div>
    <div class="flex items-start gap-3">
      <span class="material-symbols-outlined text-xl flex-shrink-0 mt-0.5" style="color:#B41E1E">local_fire_department</span>
      <div>
        <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Queimadas</p>
        <p class="text-sm text-slate-700"><strong>INPE BDQueimadas</strong> — focos 2000–2024, 1.116.805 registros (bbox Tietê).
        <span class="font-mono text-xs text-blue-600">queimadas.dgi.inpe.br</span></p>
      </div>
    </div>
    <div class="flex items-start gap-3">
      <span class="material-symbols-outlined text-xl flex-shrink-0 mt-0.5" style="color:#0F7B5F">plumbing</span>
      <div>
        <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Saneamento &amp; Resíduos</p>
        <p class="text-sm text-slate-700"><strong>SNIS</strong> 2010–2020 (SP, 210–232 mun.) + <strong>CETESB IQR</strong> 2017–2021.
        <span class="font-mono text-xs text-blue-600">app4.mdr.gov.br · cetesb.sp.gov.br</span></p>
      </div>
    </div>
  </div>
</div>

<!-- ── FIGURES ── -->
<main class="max-w-6xl mx-auto px-6 pb-16">
  {cards_html}
</main>

<!-- ── FOOTER ── -->
<footer style="background:var(--gsu-blue)" class="py-8">
  <div class="max-w-6xl mx-auto px-6 text-center">
    <p class="text-white/40 text-xs">
      Projeto FREnTE · Análise Exploratória de Dados · Bacia do Rio Tietê
      &nbsp;·&nbsp; Dados: ONS Dados Abertos &nbsp;·&nbsp; Gerado automaticamente
    </p>
  </div>
</footer>

</body>
</html>
"""

OUT.write_text(HTML, encoding="utf-8")
print(f"HTML salvo: {OUT}")
