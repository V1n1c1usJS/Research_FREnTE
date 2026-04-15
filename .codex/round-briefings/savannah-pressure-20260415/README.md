# Savannah Pressure Round — 2026-04-15

Objetivo desta rodada:
- coletar os dados de pressao ambiental e poluicao que estao ausentes no staging atual
- completar a narrativa river → pollutants → sediment com dados estruturados reais

Contexto:
- o staging atual tem hidrologia e operacao de reservatorio bem cobertos
- o eixo de pressao ambiental esta completamente vazio em dado estruturado
- os alvos foram identificados em context_source_inventory.csv com status `missing` e `requires_priority_followup = yes`
- esta rodada foca exclusivamente nesses alvos

Cadeia operacional:
1. `portal_data_collector` coleta os alvos de pressao listados no briefing
2. `eda_reservatorio` normaliza e integra ao staging existente
3. as figuras de pressao no relatorio (fig5_pressures_pollutants) serao atualizadas

Restricoes mantidas:
- `des.sc.gov` fora sem novo alinhamento
- sem login, captcha ou bypass de restricoes

Arquivos desta rodada:
- `portal_data_collector.md`  — briefing do Harvester com alvos de pressao
- `eda_reservatorio.md`        — briefing do Analyst para integracao ao staging
