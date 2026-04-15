# Briefing: portal_data_collector

Objetivo:
- coletar os targets recebidos da rodada geral e organizar o bruto em `data/runs/...`

Escopo funcional:
- operar no sistema `Hartwell -> Russell -> Thurmond`
- coletar com foco em equivalencia entre reservatorios
- preservar proveniencia e chaves de juncao para EDA posterior

Prioridades de coleta:

1. Pressao ambiental e poluicao — alvos com `missing` no context_source_inventory.csv:
   - EPA ECHO: discarregadores NPDES na bacia do Savannah (echo.epa.gov)
     - filtrar por HUC ou estado GA/SC + Savannah River
     - baixar lista de instalacoes com grupos de parametros e status de permissao
   - EPD Georgia — Sediment TMDL 2010 (epd.georgia.gov)
     - estimativas de carga por sub-bacia, trechos impactados, metas de reducao
   - EPD Georgia — Bacteria TMDL 2023 (epd.georgia.gov)
     - lista de trechos impactados, atribuicao de fonte, estimativas de carga coliform
   - EPD Georgia — DO Restoration Plan (epd.georgia.gov)
     - zonas de impacto de OD, limiares sazonais, atribuicao de fontes a montante
   - Clemson Water Quality Study 2006-2008 (open.clemson.edu)
     - metais, nutrientes, OC, TSS por trecho no medio e baixo Savannah
   - NOAA Bathymetry (ncei.noaa.gov)
     - modelo batimetrico do pool de Thurmond

2. Operacao por reservatorio (completar paridade onde ainda ha lacuna):
   - elevacao, storage, inflow, outflow, releases
   - power generation — Hartwell, Russell, Thurmond (ja existe em reservoir_operations_monthly mas nao esta sendo usado na EDA)

3. Hidrologia e qualidade do rio:
   - gauges NWIS acima, entre e abaixo dos reservatorios
   - WQP mainstem — qualquer resultado pos-1998 que nao esteja em staging

4. Contexto:
   - metadados NID
   - NWS quando houver endpoint reutilizavel

Regras:
- usar Playwright apenas quando necessario para descobrir endpoint real
- depois preferir download HTTP deterministico
- organizar por `source_slug` em `data/runs/{run-id}/collection/...`
- registrar bloqueios sem tentar burlar login, captcha ou restricoes de aprovacao
- tentar coletar ate 20 anos de historico quando a fonte permitir
- se a coleta real trouxer menos de 20 anos, registrar a cobertura retornada no manifest e no report como limitacao da fonte
- `des.sc.gov` nao deve ser reexplorado

Criterio de qualidade:
- alvos de pressao ambiental tem prioridade igual ou maior que operacao de reservatorio nesta rodada
- declarar lacunas por dominio (pressao, hidrologia, operacao) no manifest e no report do run
- registrar explicitamente se algum alvo TMDL ou ECHO ficou bloqueado e o motivo

Entregavel esperado:
- bruto auditavel por fonte
- manifest com cobertura por dominio analitico (pressao / hidrologia / operacao / sedimento)
- resumo curto das lacunas para o `Analyst`
