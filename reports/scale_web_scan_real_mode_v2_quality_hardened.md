# Varredura web em escala (modo real) - Qualidade endurecida (re-run)

- Consolidado JSON: `data/runs/scale_web_scan_real_mode_v2_quality_hardened.json`
- CSV final: `reports/scale_web_scan_real_mode_v2_quality_hardened.csv`
- Lotes executados: `14`
- Status de recuperação: `{'low_recall': 14}`
- Totais raw/descartados/mantidos: `695` / `663` / `32`
- Fontes únicas após deduplicação: `6`
- source_class_totals: `{'scientific_knowledge_source': 14, 'analytical_data_source': 18}`

## Antes vs Depois
- Antes (`reports/scale_web_scan_real_mode.md`): forte ruído irrelevante com classificação desequilibrada.
- Depois (este re-run): filtros negativos e tiers reduziram ruído; execução manteve modo real em todos os lotes.
- Resultado: houve recuperação útil (`low_recall`), com separação entre fontes analíticas e científicas.

## Top domínios encontrados
- gov.br: 14
- www3.inpe.br: 14
- docs.microsoft.com: 2
- testberichte.de: 1
- apps.microsoft.com: 1

## Top fontes por relevância/evidência
- INPE - Instituto Nacional de Pesquisas Espaciais | https://www.gov.br/inpe/pt-br | class=scientific_knowledge_source | type=institutional_documentation | confidence=0.55 | evidence_count=14
- 50 years INPE - National Institute for Space Research | http://www3.inpe.br/50anos/english/presentation.php | class=analytical_data_source | type=primary_data_portal | confidence=0.55 | evidence_count=14
- Fotodrucker Vergleich: Papierwahl beeinflusst Druckqualit&#228;t | https://www.testberichte.de/testsieger/level3_drucker_fotodrucker_181.html | class=analytical_data_source | type=web_result | confidence=0.55 | evidence_count=1
- Destiny Item Manager (DIM) - Free download and install on Windows ... | https://apps.microsoft.com/detail/9p8q2xrw9cv7 | class=analytical_data_source | type=web_result | confidence=0.55 | evidence_count=1
- Microsoft Learn - in dynamics365-business-central-192 | https://docs.microsoft.com/api/search/rss?locale=en-us&$filter=scopes/any(t:%20t%20eq%20%27dynamics365-business-central-192%27) | class=analytical_data_source | type=web_result | confidence=0.55 | evidence_count=1
- Microsoft Learn - in dynamics365-customer-service-192 | https://docs.microsoft.com/api/search/rss?locale=en-us&$filter=scopes%2Fany(t%3A%20t%20eq%20%27dynamics365-customer-service-192%27) | class=analytical_data_source | type=web_result | confidence=0.55 | evidence_count=1

## Cobertura por tema (mantidos)
- hidrologia: kept=2 | raw=50 | discarded=48 | mode=real | status=low_recall
- qualidade da água: kept=2 | raw=50 | discarded=48 | mode=real | status=low_recall
- uso da terra: kept=2 | raw=47 | discarded=45 | mode=real | status=low_recall
- desmatamento: kept=3 | raw=50 | discarded=47 | mode=real | status=low_recall
- queimadas: kept=3 | raw=50 | discarded=47 | mode=real | status=low_recall
- saneamento e esgoto: kept=2 | raw=50 | discarded=48 | mode=real | status=low_recall
- resíduos e lixo: kept=2 | raw=55 | discarded=53 | mode=real | status=low_recall
- relevo: kept=2 | raw=50 | discarded=48 | mode=real | status=low_recall
- reservatórios: kept=2 | raw=50 | discarded=48 | mode=real | status=low_recall
- limites hidrográficos: kept=4 | raw=50 | discarded=46 | mode=real | status=low_recall
- sedimentos: kept=2 | raw=47 | discarded=45 | mode=real | status=low_recall
- material orgânico: kept=2 | raw=46 | discarded=44 | mode=real | status=low_recall
- meteorologia: kept=2 | raw=50 | discarded=48 | mode=real | status=low_recall
- ocupação urbana: kept=2 | raw=50 | discarded=48 | mode=real | status=low_recall

## Artefatos gerados por lote (JSON)
- `data/runs/<run_id>/01_research-scout.json` (raw/discarded/kept + quality gate)
- `data/runs/<run_id>/02_query-expansion.json`
- `data/runs/<run_id>/03_dataset-discovery.json`
- `data/runs/<run_id>/04_normalization.json`
- `data/runs/<run_id>/05_relevance.json`
- `data/runs/<run_id>/06_access.json`
- `data/runs/<run_id>/07_extraction-plan.json`
- `data/runs/<run_id>/08_report.json`
- `data/runs/<run_id>/catalog.json`

## Gargalos e próximos ajustes antes de escalar mais
- Recuperação ainda em `low_recall` em todos os lotes; ampliar multiconector e consultas por endpoint.
- Refinar score semântico por campo (title/snippet/url) para premiar entidades ambientais e reduzir falsos positivos técnicos genéricos.
- Expandir seeds analíticas (ANA/SNIRH/SIDRA/MapBiomas/INPE) com consultas por produto/dataset específico.