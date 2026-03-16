# Varredura web em escala (modo real) - Qualidade endurecida

- Arquivo consolidado JSON: `data/runs/scale_web_scan_real_mode_v2_quality_hardened.json`
- Total de lotes: `14`
- Status de recuperação: `{'low_recall': 14}`
- Totais (raw/descartados/mantidos): `826` / `724` / `78`
- Fontes únicas após deduplicação: `12`
- Failed quality gate runs: `2`

## Before vs After
- Before: `reports/scale_web_scan_real_mode.md` mostrou domínio de resultados irrelevantes e `analytical_data_source=0`.
- After: esta execução aplica hardening de consulta, tiers de domínio, filtro negativo forte e quality gates por lote.

## Analytical vs Scientific
- source_class_totals: `{'scientific_knowledge_source': 12, 'analytical_data_source': 66}`

## Top domínios
- sigrh.sp.gov.br: 12
- mapbiomas.org: 12
- plataforma.brasil.mapbiomas.org: 12
- brasil.mapbiomas.org: 12
- www3.inpe.br: 12
- weforum.org: 12
- turbotax.community.intuit.ca: 1
- freesolitaire.com: 1
- microsoft.com: 1
- microsoft-excel-preview.en.uptodown.com: 1
- gizmodo.com: 1
- healthcare.gov: 1

## Estatísticas por lote
- hidrologia | run=run-ae09554a | mode=real | status=low_recall | quality_gate=passed | raw=60 | discarded=52 | kept=8
- qualidade da água | run=run-6d34e621 | mode=real | status=low_recall | quality_gate=passed | raw=56 | discarded=50 | kept=6
- uso da terra | run=run-b41e5141 | mode=real | status=low_recall | quality_gate=passed | raw=60 | discarded=54 | kept=6
- desmatamento | run=run-1d81ba5d | mode=real | status=low_recall | quality_gate=passed | raw=60 | discarded=54 | kept=6
- queimadas | run=run-6551013a | mode=real | status=low_recall | quality_gate=passed | raw=53 | discarded=47 | kept=6
- saneamento e esgoto | run=run-90a7488d | mode=real | status=low_recall | quality_gate=passed | raw=60 | discarded=51 | kept=9
- resíduos e lixo | run=run-1caed848 | mode=real | status=low_recall | quality_gate=passed | raw=60 | discarded=54 | kept=6
- relevo | run=run-8f792da7 | mode=real | status=low_recall | quality_gate=failed_quality_gate | raw=60 | discarded=49 | kept=0
- reservatórios | run=run-4c5a2bc9 | mode=real | status=low_recall | quality_gate=passed | raw=60 | discarded=54 | kept=6
- limites hidrográficos | run=run-ee38c13a | mode=real | status=low_recall | quality_gate=passed | raw=60 | discarded=54 | kept=6
- sedimentos | run=run-ea1d0678 | mode=real | status=low_recall | quality_gate=passed | raw=61 | discarded=54 | kept=7
- material orgânico | run=run-cf094e0a | mode=real | status=low_recall | quality_gate=passed | raw=60 | discarded=54 | kept=6
- meteorologia | run=run-d9f6e369 | mode=real | status=low_recall | quality_gate=failed_quality_gate | raw=60 | discarded=47 | kept=0
- ocupação urbana | run=run-dec0f16c | mode=real | status=low_recall | quality_gate=passed | raw=56 | discarded=50 | kept=6

## JSON outputs gerados
- `data/runs/scale_web_scan_real_mode_v2_quality_hardened.json`
- `data/runs/<run_id>/01_research-scout.json` (raw/discarded/kept + quality gate por lote)
- `data/runs/<run_id>/02_query-expansion.json`
- `data/runs/<run_id>/03_dataset-discovery.json`
- `data/runs/<run_id>/04_normalization.json`
- `data/runs/<run_id>/05_relevance.json`
- `data/runs/<run_id>/06_access.json`
- `data/runs/<run_id>/07_extraction-plan.json`
- `data/runs/<run_id>/08_report.json`
- `data/runs/<run_id>/catalog.json`