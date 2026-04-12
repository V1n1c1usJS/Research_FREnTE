# EDA/clarks_hill

Objetivo: caracterizar o comportamento do rio Savannah no mesmo frame analitico
adotado para o rio Tiete: o rio e o objeto principal da leitura, as pressoes
ambientais e os poluentes entram como parte do nucleo analitico, os reservatorios
Hartwell, Russell e Thurmond aparecem como estruturas e controles dentro do
proprio rio, e a interpretacao dos sedimentos vem ao final como camada-resposta
em J. Strom Thurmond Reservoir.

Esta frente nao substitui a analise laboratorial dos sedimentos apresentada em
`GSA Presentation Slide 2.pptx (1).pdf`. O foco aqui e montar a camada de contexto que
explica, em ordem narrativa:

- sinal do rio e sua variabilidade hidrologica e de qualidade da agua
- contexto de bacia, paisagem, poluentes e pressoes ambientais
- operacao coordenada de Hartwell -> Russell -> Thurmond como modulacao explicativa

Em outras palavras: o estudo principal da GSA e sedimentocentrico, e este workspace
de EDA existe para responder "que contexto fluvial, operacional e ambiental ajuda
a explicar os sedimentos observados em Clarks Hill?".

O interpretive anchor desta frente fica em:

- `analise_sedimentos/Analise_sedimentos_Clarks_Hill_Lake.ipynb`
- `analise_sedimentos/Most Corrected Master_Data Clarks Hill Lake (version 3).xlsb.xlsx`

Esse material deve ser tratado como a referencia independente para:

- dominancia de sedimentos finos
- enriquecimento de ferro em fracoes mais finas
- acoplamento Fe-C
- associacao entre maior profundidade e zonas deposicionais de menor energia

Referencias canonicas desta preparacao:

- `config/context_clarkshill.yaml`
- `config/tracks_clarkshill.yaml`
- `GSA Presentation Slide 2.pptx (1).pdf`
- `EDA/operacao_reservatorio/`

## Escopo analitico

O `context_clarkshill.yaml` define que esta EDA deve produzir o contexto fisico para
interpretar deposicao fina, enriquecimento em ferro e estabilizacao de carbono organico.

O slide 2 da apresentacao reforca a motivacao:

- sedimentos regulam armazenamento e mobilidade de nutrientes
- sedimentos controlam potencial de carga interna
- sedimentos influenciam a sustentabilidade do reservatorio
- Clarks Hill apresenta preocupacao com floracoes algais periodicas

Portanto, o nosso relatorio de apoio deve ser lido assim:

- nao e um relatorio "sobre operacao de reservatorios" em abstrato
- nao e uma reescrita da analise sedimentologica principal
- e uma camada de contexto externo para mostrar por que o sistema rio +
  reservatorios pode produzir o ambiente hidrodinamico e biogeoquimico descrito
  no estudo dos sedimentos

Portanto, esta EDA deve priorizar variaveis de contexto que ajudem a ligar
hidrodinamica, qualidade da agua, poluentes e pressoes ambientais a zonas de
baixa energia, sem fabricar dados de sedimento que pertencem a outra trilha do estudo.

O recorte correto para a proxima rodada e:

- Savannah River como storyline principal, tal como o Tiete foi na referencia canonica
- Hartwell -> Russell -> Thurmond como estruturas e controles operacionais secundarios inseridos no rio
- Thurmond como reservatorio-alvo da interpretacao sedimentologica
- comparacao entre os tres reservatorios apenas quando houver dado equivalente
- cruzamento entre sinal do rio e operacao dos reservatorios somente quando for analiticamente justificavel
- levantamento explicito de poluentes, fontes de pressao e indicadores de degradacao que influenciem o rio
- horizonte analitico alvo de 20 anos para series temporais
- exibicao obrigatoria da defasagem temporal por reservatorio, fonte e variavel quando a cobertura real ficar abaixo desse alvo

## Ordem narrativa canonica

Esta EDA deve seguir a estrutura narrativa inspirada no relatorio do Tiete, mas
adaptada para um frame `river-first`:

1. `river signal first`
- hidrologia, water quality, continuidade espacial e cobertura temporal do rio

2. `basin, pollutants, and pressures second`
- uso do solo, clima, paisagem, batimetria, documentos de bacia, poluentes, fontes de descarga e outras pressoes

3. `reservoir operations as explanatory modulation`
- Hartwell, Russell e Thurmond entram como controles operacionais do sinal do rio
- operacao nao deve ser tratada como protagonista quando o dado principal for de rio
- comparacoes multi-reservatorio so entram quando esclarecem o comportamento do rio

## Estrutura desta pasta

- `process_context_sources.py`
  - consolida o intake a partir dos manifests mais recentes do eixo Savannah, salvo quando um manifest explicito for passado por CLI
  - absorve gauges adicionais do mainstem e novos alvos WQP do rio sem depender de `target_id` fixo da rodada anterior
  - materializa `data/staging/clarks_hill/context_source_inventory.csv` para explicitar backlog de water quality, poluentes, pressoes e series operacionais longas
- `generate_figures.py`
  - gera as figuras finais a partir de tabelas harmonizadas, obedecendo o frame river-first
- `generate_presentation.py`
  - renderiza `docs/clarks-hill/index.html` a partir de `report_context.json`, preservando o visual canonico do projeto
- `report_context.template.json`
  - template inicial do contexto narrativo das figuras
- `handoff_contract.md`
  - contrato minimo esperado para a entrega do Harvester e do chat principal
- `agent_briefs/`
  - briefs persistentes por agent para a rodada sistemica `Hartwell -> Russell -> Thurmond`
- `initial_source_inventory.partial.json`
  - inventario parcial do que ja esta realmente aproveitavel
- `initial_source_inventory.partial.md`
  - leitura humana do inventario parcial
- `figures/`
  - destino das figuras finais

## Preflight da proxima passada

Discovery oficial desta passada:

- `data/runs/perplexity-intel-fcde4b9e/processing/04-harvester-handoff.json`

Preparacao analitica agora materializada:

- `data/staging/clarks_hill/harvester_handoff_inventory.csv`
- `data/staging/clarks_hill/domain_registry.csv`
- `data/analytic/clarks_hill/collection_preflight_inventory.csv`
- `data/analytic/clarks_hill/domain_registry.csv`
- `data/analytic/clarks_hill/crosswalk_registry.csv`
- `data/analytic/clarks_hill/river_mainstem_layers.csv`
- `data/analytic/clarks_hill/reservoir_annex_layers.csv`
- `data/analytic/clarks_hill/pressure_source_inventory.csv`
- `data/analytic/clarks_hill/coverage_target_matrix.csv`
- `data/analytic/clarks_hill/sediment_bridge_summary.csv`

Comando de integracao quando o Harvester concluir:

- `.\.venv310\Scripts\python.exe EDA/clarks_hill/process_context_sources.py --harvester-handoff data/runs/perplexity-intel-fcde4b9e/processing/04-harvester-handoff.json`

Regra operacional desta passada:

- convergir para `data/analytic/clarks_hill/`
- manter `Savannah River-first`
- tratar `Hartwell`, `Russell` e `Thurmond` como anexo explicativo
- preservar alvo de 20 anos e explicitar toda lacuna real de cobertura

## Estado atual do handoff

Busca concluida:

- `data/runs/perplexity-intel-5fdaad57/manifest.json`
- `data/runs/perplexity-intel-5fdaad57/processing/03-ranked-datasets.json`
- `data/runs/perplexity-intel-5fdaad57/processing/05-harvester-handoff-curated.json`

Coleta ativa materializada:

- `data/runs/operational-collect-savannah-system-20260408-222744/manifest.json`

Resumo atual:

- 13 alvos coletados na rodada sistemica ativa
- 0 alvos parciais
- 0 alvos bloqueados no escopo ativo
- staging sistemico inicial gerado em `data/staging/clarks_hill/`
- parser de intake preparado para reutilizar automaticamente a coleta Savannah River/Savannah System mais recente

Alerta de escopo:

- o frame analitico agora e `river-first`, nao `reservoir-first`
- Hartwell, Russell e Thurmond ja entram no contexto sistemico, mas a operacao deve funcionar como camada explicativa
- o HTML final nao deve transformar os reservatorios em narrativa principal quando o dado-ponte vier do rio

## O que ja e aproveitavel agora

### Usable now

1. `03-savannah-river-basin-landscape-analysis`
- arquivo local: `data/runs/operational-collect-clarkshill-20260401-225924/collection/03-savannah-river-basin-landscape-analysis/savannah_river_basin_landscape_analysis.pdf`
- valor para o EDA: contexto de bacia, indicadores de paisagem, drenagem, uso do solo, solos e limites hidrologicos
- limitacao: PDF semi-estruturado; ainda sem tabela harmonizada

2. `04-savannah-river-basin-restoration-data-2008`
- arquivo local: `data/runs/operational-collect-clarkshill-20260401-225924/collection/04-savannah-river-basin-restoration-data-2008/savannah_rbrp_2018.pdf`
- valor para o EDA: HUs/TLWs, prioridades de bacia, cobertura florestal, uso do solo e elevacao
- limitacao: PDF semi-estruturado; ainda sem tabela harmonizada

3. `waterqualitydata.us` nos tres forebays
- arquivos locais e staging sistemico em `data/staging/clarks_hill/wqp_system_summary.csv`, `wqp_system_yearly_counts.csv` e `wqp_parameter_coverage.csv`
- valor para o EDA: melhor camada comparavel atual para montar o sinal do rio e a cobertura temporal do sistema
- limitacao: forebays continuam sendo proximos aos reservatorios; nao equivalem sozinhos a um eixo fluvial completo

4. `water.usace` e `nid` nos tres reservatorios
- arquivos locais e staging sistemico em `data/staging/clarks_hill/usace_system_snapshot.csv` e `nid_system_summary.csv`
- valor para o EDA: camada explicativa da modulacao operacional da cascata sobre o sinal do rio
- limitacao: na rodada atual, a operacao ainda entrou mais como snapshot do que como serie historica harmonizada

5. `usgs-02193900-monitoring-location` e legado Thurmond detalhado
- arquivos locais: `endpoint_confirmed.json`, `iv_02193900.json`, `dv_02193900.json` e staging legado
- valor para o EDA: camada de detalhe de Thurmond que continua util como ponte para a interpretacao sedimentologica
- limitacao: nao deve rebaixar o frame river-first para uma narrativa Thurmond-only

### Criticos, mas pendentes por enquanto

- water quality fluvial harmonizada para o eixo principal do rio com alvo de 20 anos
  - impacto: o frame river-first ja esta definido, mas ainda depende de mais serie temporal e quimica fluvial harmonizada para amadurecer o protagonismo do rio

- gauges adicionais do `mainstem` acima, entre e abaixo da cascata
  - impacto: o workspace ja consegue absorver novos gauges, mas a rodada atual ainda nao cobre o eixo longitudinal no nivel desejado

- camada explicita de bacia/pressoes no mesmo grau de maturidade do WQP
  - impacto: a segunda perna narrativa existe como escopo, mas ainda nao e a camada mais forte do workspace atual

- `des.sc.gov`
  - fora do escopo por decisao do usuario

- historico operacional harmonizado para Hartwell, Russell e Thurmond com cobertura auditada contra o alvo de 20 anos
  - impacto: a operacao ainda funciona melhor como modulacao snapshot do que como serie comparativa longa

- poluentes, impairments, dischargers e demais pressoes ambientais em tabelas estruturadas
  - impacto: parte do contexto ja foi descoberta, mas ainda precisa sair do estado PDF-only para entrar de fato no cruzamento analitico do rio

## Proxima camada analitica esperada

O que ja pode ser feito sem fabricar dados:

1. inventario de fontes realmente disponiveis
2. camada river-first baseada em WQP e series fluviais quando existirem
3. camada de bacia, poluentes e pressoes com PDFs, paisagem, batimetria, uso do solo, impairment/discharger context e fontes ambientais
4. camada de modulacao operacional baseada em Hartwell, Russell e Thurmond
5. matriz de cobertura temporal contra o alvo de 20 anos
6. backlog estruturado da proxima coleta em `data/staging/clarks_hill/context_source_inventory.csv`

O que ainda NAO deve ser feito sem nova coleta:

- narrativa final do sistema sem serie fluvial mais madura
- leitura causal forte entre operacao e sinal do rio sem cruzamento analiticamente justificavel
- conclusoes sistemicas fechadas sobre tempo de residencia sem cobertura temporal auditada

## Contrato de dados esperado

O handoff de entrada nao precisa ter todos os datasets do estudo, mas precisa ter:

1. Um inventario consolidado do que foi coletado
- caminho do arquivo
- fonte
- formato
- periodo
- granularidade
- status de completude

2. Um resumo do recorte analitico
- janela temporal
- recorte espacial
- perguntas que o EDA precisa responder primeiro

3. Campos ou schema minimo por dataset
- nomes de colunas principais
- unidade de medida quando aplicavel
- chave temporal
- chave espacial ou de estacao quando aplicavel

4. Chaves de juncao disponiveis ou estrategia de conciliacao
- `date`, `year`, `month`
- `site_no`, `station_id`, `gage_id`
- `sample_site_id`
- `reservoir_id`, `basin_id`

Sem esse minimo, o EDA pode ser iniciado apenas ate a fase de triagem e validacao.

## Regra obrigatoria de cobertura temporal

Para esta frente, `20 anos` e o horizonte analitico alvo para operacao,
hidrologia, tempo de residencia, water quality e demais series temporais.

Quando a disponibilidade real ficar abaixo desse alvo, a defasagem deve aparecer:

- no `README`
- nas figuras
- no `report_context`

Granularidade minima da defasagem:

- por `reservatorio`
- por `fonte`
- por `variavel`

O EDA nao deve mascarar series curtas como se fossem historicos longos.
