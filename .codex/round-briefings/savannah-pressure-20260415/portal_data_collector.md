# Briefing: portal_data_collector — Savannah Pressure Round

Objetivo:
- coletar os seis alvos de pressao ambiental identificados como `missing` no context_source_inventory.csv
- organizar o bruto em `data/runs/{run-id}/collection/` com manifesto e proveniencia

Sistema alvo:
- Savannah River — trecho Hartwell → Russell → Thurmond → Augusta

---

## Alvos prioritarios — coletar nesta ordem

### 1. EPA ECHO — Discarregadores NPDES na bacia do Savannah
- URL de entrada: https://echo.epa.gov/facilities/facility-search
- source_slug: `epa_echo_npdes_savannah`
- O que coletar:
  - lista de instalacoes com permissao NPDES ativa ou historica na bacia do Savannah (HUC 03060101, 03060102, 03060103, 03060104)
  - para cada instalacao: nome, tipo (industrial/municipal), parametros de descarga, status de compliance, coordenadas
  - download CSV via botao "Download" na pagina de resultados apos aplicar filtros
- Fluxo Playwright esperado:
  - abrir pagina de busca
  - aplicar filtro HUC ou estado GA + SC com keyword "Savannah"
  - interceptar request de download ou copiar URL do CSV gerado
  - baixar por HTTP direto
- Formato esperado: CSV
- Janela temporal alvo: 2006-2026 (compliance history)
- Nota: se o portal exigir selecao de watershed, usar HUC8 codes: 03060101, 03060102, 03060103, 03060104

### 2. EPD Georgia — Sediment TMDL 2010
- URL de entrada: https://epd.georgia.gov/watershed-protection-branch/tmdls
- source_slug: `epd_tmdl_sediment_savannah`
- O que coletar:
  - documento "Savannah River Basin Sediment TMDL Evaluation" (2010)
  - se houver tabelas estruturadas: carga de sedimento por sub-bacia, trechos impactados, metas de reducao
  - baixar PDF completo e qualquer anexo de dados (XLSX, CSV)
- Fluxo Playwright esperado:
  - navegar para pagina de TMDLs
  - localizar secao Savannah River Basin
  - identificar link do documento de sedimento
  - baixar por HTTP direto apos descoberta do URL real
- Formato esperado: PDF + eventual XLSX/CSV de suporte

### 3. EPD Georgia — Bacteria TMDL 2023
- URL de entrada: https://epd.georgia.gov/watershed-protection-branch/tmdls
- source_slug: `epd_tmdl_bacteria_savannah`
- O que coletar:
  - documento "Savannah River Basin Bacteria TMDL" (2023)
  - lista de trechos impactados (stream segments), classificacao de fonte (point/nonpoint), estimativas de carga coliform
- Fluxo Playwright: mesmo fluxo do TMDL sedimento, localizar documento bacteria/coliform no Savannah Basin
- Formato esperado: PDF

### 4. EPD Georgia — DO Restoration Plan
- URL de entrada: https://epd.georgia.gov/watershed-protection-branch
- source_slug: `epd_do_restoration_savannah`
- O que coletar:
  - "Savannah River Basin dissolved oxygen restoration plan" ou equivalente
  - zonas de impacto de OD, limiares sazonais, fontes a montante identificadas
- Nota: pode estar em subpagina diferente da TMDL — explorar navegacao do site EPD
- Formato esperado: PDF

### 5. Clemson — Water Quality Study 2006-2008
- URL de entrada: https://open.clemson.edu
- source_slug: `clemson_wqs_savannah_2006`
- O que coletar:
  - "Water Quality Study of Savannah River Basin (2006-2008)" ou equivalente
  - dados de metais, nutrientes, OC, TSS por estacao/trecho
  - preferir dataset estruturado (CSV, XLSX) ao PDF se existir no repositorio
- Fluxo Playwright:
  - buscar no repositorio open.clemson.edu por "Savannah River water quality"
  - localizar bitstream ou link de download do dataset ou relatorio
  - baixar por HTTP direto
- Formato esperado: CSV/XLSX ou PDF com tabelas

### 6. NOAA — Bathymetry Savannah River
- URL de entrada: https://www.ncei.noaa.gov/maps/bathymetry/
- source_slug: `noaa_bathymetry_savannah`
- O que coletar:
  - modelo batimetrico ou dataset de pontos de profundidade para o trecho Thurmond → Augusta
  - preferir formato raster (GeoTIFF) ou CSV de pontos com lat/lon/depth
- Fluxo Playwright:
  - abrir visualizador NCEI
  - filtrar area geografica: bbox aproximado [-82.5, 33.5, -81.5, 34.5]
  - identificar dataset disponivel e URL de download
- Formato esperado: GeoTIFF, CSV ou NetCDF
- Nota: se nao houver cobertura especifica para Thurmond, registrar como blocked e documentar qual e a cobertura mais proxima disponivel

---

## Regras operacionais

- Usar Playwright apenas para descobrir o endpoint real — depois baixar por HTTP deterministico
- Registrar bloqueios sem tentar bypass de login, CAPTCHA ou aprovacao manual
- Para cada alvo: salvar em `data/runs/{run-id}/collection/{source_slug}/`
- Registrar no manifest: URL exata usada, metodo de coleta, status (collected / partial / blocked), periodo retornado
- `des.sc.gov` fora desta rodada

## Criterio de qualidade

- Manifesto com status explicito por alvo
- Para alvos PDF: confirmar que o download chegou completo (tamanho > 0, paginas visiveis)
- Para alvos CSV: registrar numero de linhas e colunas no manifest
- Declarar explicitamente se algum alvo ficou blocked e o motivo exato

## Entregavel esperado

- Bruto auditavel em `data/runs/{run-id}/collection/`
- `manifest.json` com cobertura por alvo
- Resumo curto (max 10 linhas) para o Analyst: o que chegou, o que bloqueou, o que precisara de extracao manual de PDF
