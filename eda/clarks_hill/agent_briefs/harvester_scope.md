# Harvester Scope

Agent alvo:

- `portal_data_collector`
- arquivo: `.codex/agents/portal-data-collector.toml`

Missao desta rodada:

- receber o handoff do Runner
- coletar os dados brutos do rio Savannah e, dentro dele, das estruturas `Hartwell -> Russell -> Thurmond`
- organizar o output em `data/runs/{run-id}/...` com proveniencia completa

Escopo obrigatorio de coleta:

- gauges e endpoints hidrologicos do canal principal do rio Savannah acima, entre e abaixo de `Hartwell`, `Russell` e `Thurmond`
- water quality historica em trechos de rio e pontos que capturem o mainstem
- sedimento em suspensao, turbidez, TSS e proxies que ajudem a explicar o comportamento do rio
- fontes de poluentes e pressoes ambientais sobre o rio: NPDES/ECHO, ATTAINS, TMDL, impairments, uso do solo e documentos de bacia
- fontes modernas de poluicao e descarga no mainstem:
  - `savannahwaterquality.com/archive`
  - `savannahwaterquality.com/pfas`
  - `savannahriverkeeper.org/program-overview`
  - `savannahriverkeeper.org/forever-chemicals`
  - dashboards ArcGIS ou exports oficiais associados
  - `srns.doe.gov/ars` e relatorios ambientais anuais do SRS
  - `sciencebase.gov` Savannah River 2020
  - `open.clemson.edu` 2006-2008
- operacao USACE ou equivalente para `Hartwell`, `Russell` e `Thurmond` como camada explicativa secundaria
- metadados estruturais dos tres reservatorios como anexo interpretativo

Prioridade operacional:

1. dados do rio Savannah antes de dados exclusivos de reservatorio
2. poluentes, pressoes e water quality do rio antes de detalhes documentais
3. operacao e hidrologia dos reservatorios apenas quando ajudarem a explicar o sinal do rio
4. dados queryaveis e historicos antes de PDFs de apoio
5. equivalencia minima entre reservatorios antes de aprofundar Thurmond sozinho
6. quando a quimica moderna do mainstem estiver fraca, priorizar:
  - fontes locais de PFAS
  - dashboards e exports Riverkeeper
  - WQP guiado por parametro
  - SRS / DOE para radionuclideos e tributarios relevantes

Output esperado:

- `data/runs/{run-id}/config/collection-options.json`
- `data/runs/{run-id}/collection/{source_slug}/...`
- `data/runs/{run-id}/processing/01-collection-targets.json`
- `data/runs/{run-id}/reports/{run-id}.md`
- `data/runs/{run-id}/reports/collection_targets.csv`
- `data/runs/{run-id}/manifest.json`

Chaves e metadados a preservar:

- `reservoir_id`
- `reservoir_name`
- `river_segment`
- `river_reach_id`
- `station_id`
- `site_no`
- `date`
- `year`
- `year_month`
- unidade de medida e timezone quando houver

Regras:

- usar Playwright so para descobrir endpoint real
- depois preferir download HTTP deterministico
- nao misturar bruto com `data/staging/` ou `data/analytic/`
- nao deixar a coleta escorregar para reservatorio-first quando existir fonte melhor no canal principal do rio
- registrar claramente quando um reservatorio tiver cobertura inferior aos outros
- registrar claramente quando um trecho do rio tiver cobertura inferior aos demais
- nao tocar em `des.sc.gov` nesta rodada
- se um portal estiver bloqueado por login, CAPTCHA, aprovacao manual ou geoblock, registrar e parar
- sempre solicitar ou filtrar uma janela alvo de 20 anos quando a fonte permitir
- se a fonte devolver menos de 20 anos, persistir o periodo real retornado e documentar a diferenca
- se uma fonte moderna de poluicao for dashboard ou pagina de arquivos, registrar se havia:
  - CSV/XLSX direto
  - PDF anual
  - ArcGIS FeatureServer ou REST endpoint
  - tabela dinamica exportavel
  - ausencia total de export util

Definicao de sucesso desta rodada:

- ao menos um bloco auditavel do rio Savannah com hidrologia, water quality ou pressao ambiental utilizavel no EDA
- e, quando possivel, um bloco operacional comparavel entre `Hartwell`, `Russell` e `Thurmond`
- ou evidencia clara, auditavel, de por que essa cobertura nao foi possivel
