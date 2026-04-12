# Briefing: portal_data_collector

Objetivo:
- coletar os targets recebidos da rodada geral e organizar o bruto em `data/runs/...`

Escopo funcional:
- operar no sistema `Hartwell -> Russell -> Thurmond`
- coletar com foco em equivalencia entre reservatorios
- preservar proveniencia e chaves de juncao para EDA posterior

Prioridades de coleta:
- operacao por reservatorio:
  - elevacao
  - storage
  - inflow
  - outflow
  - releases quando existirem
- hidrologia:
  - gauges e series NWIS
  - forecasts NWS quando houver endpoint reutilizavel
- water quality:
  - station metadata
  - result exports
- contexto:
  - metadados NID
  - clima e bacia quando a rodada entregar alvo operacionalizavel

Regras:
- usar Playwright apenas quando necessario para descobrir endpoint real
- depois preferir download HTTP deterministico
- organizar por `source_slug` em `data/runs/{run-id}/collection/...`
- registrar bloqueios sem tentar burlar login, captcha ou restricoes de aprovacao
- tentar coletar ate 20 anos de historico quando a fonte permitir
- se a coleta real trouxer menos de 20 anos, registrar a cobertura retornada no manifest e no report como limitacao da fonte
- `des.sc.gov` nao deve ser reexplorado

Criterio de qualidade:
- evitar profundidade extra em Thurmond se Hartwell ou Russell ainda estiverem sem alvo equivalente
- declarar lacunas por reservatorio no manifest e no report do run

Entregavel esperado:
- bruto auditavel por fonte
- manifest com cobertura por reservatorio
- resumo curto das lacunas para o `Analyst`
