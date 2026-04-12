# Runner Scope

Agent alvo:

- `rodada_api_handoff`
- arquivo: `.codex/agents/rodada-api-handoff.toml`

Missao desta rodada:

- rodar a descoberta geral via API sem Firecrawl
- produzir um handoff de coleta orientado ao rio Savannah com eixo `river-first`
- priorizar fontes que descrevam o sinal do rio, seus poluentes e suas pressoes, e depois cruzar isso com a operacao dos tres reservatorios

Escopo obrigatorio de busca:

- monitoramento do canal principal do rio Savannah acima, entre e abaixo de `Hartwell`, `Russell` e `Thurmond`
- gauges USGS/NWS com sinal de vazao, nivel, stage, downstream context e Augusta reach
- water quality historica em trechos de rio e pontos que capturem a resposta do mainstem
- sedimento em suspensao, turbidez, TSS e contexto de sedimento fluvial quando houver
- fontes de poluentes e pressoes ambientais: NPDES/ECHO, ATTAINS, TMDL, impairments, uso do solo, agricultura, urbanizacao, e outros vetores que influenciem o rio
- operacao USACE e metadados de barragem apenas como anexos interpretativos
- clima, uso do solo e contexto de bacia apenas quando ajudarem a explicar o sinal do rio

Hipoteses de contaminacao a verificar na rodada:

- usar o recorte vindo da descoberta como contexto de busca, nao como fato confirmado
- organizar a procura por periodo historico e por familia de contaminante
- procurar evidencias oficiais e queryaveis para as seguintes janelas:
  - `1940s-1970s`: metais pesados, PAHs, PCBs, pesticidas organoclorados, butyltins em sedimento, agua ou biota
  - `1980s-1990s`: residuos de DDT/DDE, PCBs, mirex, hidrocarbonetos de petroleo e metais em agua, sedimento ou biota
  - `2000-2026`: PFAS/PFOA/PFOS, radionuclideos ligados ao SRS, E. coli, metais em sedimentos recentes, plasticos/particulados industriais
- priorizar datasets ou relatorios com serie, tabela, dashboard, export oficial ou mapa queryavel
- sempre separar:
  - `evidencia direta`: dado tabular, serie, inventario ou endpoint
  - `evidencia indireta`: PDF tecnico, artigo, dashboard sem export claro

Fontes prioritarias para essas hipoteses:

- `USGS NWIS` e `WQP` para agua e sedimento
- `EPA ECHO`, `ATTAINS`, `303(d)` e `TMDL` para pressoes, impairments e cargas
- `NOAA` para historicos de contaminantes em sedimento e biota
- `Savannah Riverkeeper` para dashboards e alertas recentes
- `Savannah River Site / DOE / state oversight` para radionuclideos e remediacao
- `City of Savannah / Savannah Water Quality` para PFAS e relatorios anuais recentes
- `ScienceBase / USGS data releases` para campanhas quimicas modernas no baixo Savannah
- `open.clemson.edu` para o estudo 2006-2008 no medio e baixo Savannah

Prioridades de descoberta:

1. gauges e endpoints oficiais para o canal principal do Savannah River
2. fontes queryaveis de water quality e sedimento em suspensao no rio, incluindo estacoes adicionais como `021973269`
3. fontes oficiais de poluentes, impairments e pressoes ambientais sobre o rio
4. fontes recentes sobre PFAS, radionuclideos, E. coli, metais e descargas no corredor do rio
5. fontes oficiais ou institucionais sobre contaminantes historicos em sedimento, agua e biota
6. contexto de operacao dos reservatorios para explicar mudancas no sinal do rio
7. documentos tecnicos sobre propagacao hidrologica, controle de vazao e efeitos da cascata no mainstem

Regra temporal:

- sempre buscar uma janela historica alvo de 20 anos quando a fonte permitir
- nao reduzir a busca para um periodo menor so porque o snippet inicial mostra menos tempo
- se a fonte devolver menos de 20 anos, registrar explicitamente a cobertura real no handoff

Handoff exigido ao Harvester:

- `start_url`
- `source_name`
- `dataset_name`
- `source_slug`
- `access_type`
- `data_format`
- `collection_method_hint`
- `priority`
- `river_targets`
- `supporting_reservoir_targets`
- `coverage_note`
- `handoff_status`

Regras:

- nao fazer raspagem portal-first
- nao fazer EDA
- nao fechar o HTML
- nao aceitar handoff centrado so em reservatorio se existir opcao melhor no canal principal
- nao aceitar handoff que ignore poluentes e pressoes ambientais quando houver fonte oficial para o rio
- escalar ao chat principal se a rodada terminar sem alvos comparaveis para os principais trechos do rio

Observacao de escopo:

- `des.sc.gov` nao entra nesta rodada
- quando houver lacuna moderna de poluicao no mainstem, o Runner deve tentar buscas guiadas por parametro e por estacao:
  - `PFAS`, `PFOA`, `PFOS`
  - `E. coli`, `fecal coliform`
  - `metals`, `aluminum`, `chromium`, `zinc`, `mercury`, `arsenic`, `cadmium`
  - `total suspended solids`, `suspended sediment`, `turbidity`
  - `nitrogen`, `phosphorus`, `BOD`, `COD`
- o handoff deve distinguir entre:
  - fonte moderna do mainstem com potencial de serie temporal
  - fonte regulatoria de descarga ou violacao
  - relatorio anual ou dashboard que precisa Playwright para achar export
