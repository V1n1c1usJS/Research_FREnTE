# Harvester Scope

Agent alvo:
- `portal_data_collector`
- nickname esperado: `Harvester`

Objetivo desta rodada:
- coletar os dados brutos do rio Savannah e, dentro dele, das estruturas `Hartwell -> Russell -> Thurmond`
- organizar a coleta para EDA do rio, nao apenas de Thurmond ou dos reservatorios

Escopo individual:
- receber o handoff gerado pelo `Runner`
- entrar nas paginas ou portais quando necessario
- usar Playwright apenas para descobrir o fluxo real, endpoints ou links finais
- preferir download HTTP deterministico depois que a URL real estiver clara
- coletar primeiro artefatos do canal principal do rio e das pressoes ambientais que o afetam
- coletar depois artefatos para os tres reservatorios quando eles ajudarem a explicar o comportamento do rio
- salvar tudo em `data/runs/{run-id}/collection/{source_slug}/`
- manter manifesto, reports e trilha auditavel completos
- registrar cobertura temporal efetivamente observada em cada artefato coletado

Prioridades obrigatorias:
- USGS/NWIS e WQP associados ao rio Savannah
- EPA ECHO, ATTAINS e outras fontes de poluentes e pressoes ambientais
- NWS/NOAA para suporte hidrologico e forecast
- USACE `water.usace.army.mil` para operacao dos tres reservatorios
- NID para Hartwell, Russell e Thurmond
- outras fontes oficiais ranqueadas pelo `Runner`
- City of Savannah / Savannah Water Quality para PFAS e relatorios anuais recentes
- Savannah Riverkeeper para dashboards, ArcGIS e alertas recentes
- SRNS / DOE / SRS para tritio, radionuclideos e tributarios com potencial influencia no mainstem
- ScienceBase / USGS 2020 e Clemson 2006-2008 como campanhas institucionais de quimica

Chaves e estrutura de handoff para o EDA:
- preservar ou declarar:
  - `reservoir_id`
  - `reservoir_name`
  - `river_segment`
  - `river_reach_id`
  - `date`
  - `year`
  - `year_month`
  - `site_no`
  - `station_id`
  - `gage_id`
  - `basin_id`
- sempre registrar:
  - url exata
  - formato
  - janela alvo do estudo
  - janela temporal observada
  - grain temporal
  - grain espacial
  - status de coleta

Entregavel esperado:
- `data/runs/{run-id}/collection/...`
- `data/runs/{run-id}/processing/01-collection-targets.json`
- `data/runs/{run-id}/manifest.json`
- `data/runs/{run-id}/reports/{run-id}.md`

Restricoes:
- nao misturar bruto com `data/staging/` ou `data/analytic/`
- nao tocar em `des.sc.gov` nesta rodada
- nao burlar bloqueios de login, captcha, e-mail ou geoblock
- se uma fonte cair em bloqueio, registrar `blocked` e seguir para as demais
- nao reduzir a coleta a reservatorios se houver caminho oficial melhor para o canal principal do rio
- nao fazer EDA
- nao montar HTML
- nao tratar cobertura parcial como se atendesse a janela alvo de 20 anos
- nao considerar dashboard moderno de poluicao como resolvido sem verificar se existe export util ou endpoint coletavel

Condicao de parada:
- parar quando a coleta auditavel do rio estiver consolidada e as camadas de reservatorio suficientes para suporte explicativo estiverem registradas
- se o rio ficar sem bloco hidrologico, water quality ou pressao ambiental aproveitavel, escalar ao chat principal
