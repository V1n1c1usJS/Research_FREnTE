# Varredura web em escala (modo real) - Qualidade endurecida

- Arquivo consolidado JSON: `data/runs/scale_web_scan_real_mode_v2_quality_hardened.json`
- Total de lotes: `14`
- Status de recuperação: `{'all_filtered': 14}`
- Totais (raw/descartados/mantidos): `420` / `420` / `0`
- Fontes únicas após deduplicação: `0`
- Failed quality gate runs: `0`

## Before vs After
- Before: `reports/scale_web_scan_real_mode.md` mostrou domínio de resultados irrelevantes e `analytical_data_source=0`.
- After: esta execução aplica hardening de consulta, tiers de domínio, filtro negativo forte e quality gates por lote.

## Analytical vs Scientific
- source_class_totals: `{}`

## Top domínios

## Estatísticas por lote
- hidrologia | run=run-71cdd839 | mode=real | status=all_filtered | quality_gate=passed | raw=30 | discarded=30 | kept=0
- qualidade da água | run=run-6a39c304 | mode=real | status=all_filtered | quality_gate=passed | raw=30 | discarded=30 | kept=0
- uso da terra | run=run-5292f0de | mode=real | status=all_filtered | quality_gate=passed | raw=30 | discarded=30 | kept=0
- desmatamento | run=run-1f3b80ac | mode=real | status=all_filtered | quality_gate=passed | raw=30 | discarded=30 | kept=0
- queimadas | run=run-b1373693 | mode=real | status=all_filtered | quality_gate=passed | raw=30 | discarded=30 | kept=0
- saneamento e esgoto | run=run-53874d51 | mode=real | status=all_filtered | quality_gate=passed | raw=30 | discarded=30 | kept=0
- resíduos e lixo | run=run-3db0ec19 | mode=real | status=all_filtered | quality_gate=passed | raw=30 | discarded=30 | kept=0
- relevo | run=run-dd87587a | mode=real | status=all_filtered | quality_gate=passed | raw=30 | discarded=30 | kept=0
- reservatórios | run=run-fb95452e | mode=real | status=all_filtered | quality_gate=passed | raw=30 | discarded=30 | kept=0
- limites hidrográficos | run=run-a28ffa79 | mode=real | status=all_filtered | quality_gate=passed | raw=30 | discarded=30 | kept=0
- sedimentos | run=run-37823669 | mode=real | status=all_filtered | quality_gate=passed | raw=30 | discarded=30 | kept=0
- material orgânico | run=run-f997e692 | mode=real | status=all_filtered | quality_gate=passed | raw=30 | discarded=30 | kept=0
- meteorologia | run=run-908d1044 | mode=real | status=all_filtered | quality_gate=passed | raw=30 | discarded=30 | kept=0
- ocupação urbana | run=run-30dd15c5 | mode=real | status=all_filtered | quality_gate=passed | raw=30 | discarded=30 | kept=0

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