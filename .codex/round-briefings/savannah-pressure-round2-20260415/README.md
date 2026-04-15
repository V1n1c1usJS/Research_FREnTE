# Savannah Pressure Round 2 - 2026-04-15

Objetivo desta rodada:
- abrir uma rodada complementar apos `savannah-pressure-20260415`
- fechar tres lacunas de maior valor que ficaram fora ou bloqueadas na rodada anterior
- transformar a camada de pressao em algo mais util para a ponte `river -> pressure -> sediment`

Motivacao:
- `ECHO DMR` nunca entrou no escopo anterior, entao ainda nao existe camada de Mn por instalacao
- `Clemson 2006-2008` ficou apenas como descoberta de item page; o metodo de HTTP direto falhou por desafio WAF
- `NOAA bathymetry` so encontrou cobertura estuarina, fora do bbox de Thurmond

Escopo desta rodada:
1. `epa_echo_dmr_mn_savannah` - DMR de manganes por instalacao / ano
2. `clemson_wqs_savannah_2006` - retry via Playwright browser download event
3. `usace_bathymetry_thurmond` - bathymetria / terrain publico via USACE ou HEC-RAS; sem NOAA como alvo principal

Relacao com a rodada anterior:
- esta rodada complementa `savannah-pressure-20260415`; nao a substitui
- manter os artefatos ja coletados em `data/runs/operational-collect-savannah-pressure-20260415-001840/`
- reutilizar os HUC8, manifest e tabelas de staging ja produzidos quando isso reduzir ambiguidade

Cadeia operacional:
1. `portal_data_collector` coleta os tres alvos desta extensao de escopo
2. `eda_reservatorio` integra os novos artefatos ao staging existente
3. `report_context_pressure.json` e atualizado com a nova cobertura de Mn, Clemson e bathymetria

Restricoes mantidas:
- `des.sc.gov` continua fora sem novo alinhamento
- sem bypass de login, captcha, registro ou aprovacao manual
- `NOAA` nao e o alvo principal desta rodada; so manter como contexto do bloqueio anterior
- `Clemson` muda de metodo: o download deve usar evento de arquivo do navegador quando o HTTP direto falhar

Arquivos desta rodada:
- `portal_data_collector.md` - briefing do Harvester para a coleta round 2
- `eda_reservatorio.md` - briefing do Analyst para integracao round 2
