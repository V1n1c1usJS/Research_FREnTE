# EDA/clarks_hill

Objetivo: caracterizar o contexto regional, hidrologico e ambiental de Clarks Hill Lake
(J. Strom Thurmond Reservoir) para apoiar a interpretacao espacial dos sedimentos do lago.

Esta frente nao substitui a analise laboratorial dos sedimentos apresentada em
`GSA Presentation Slide 2.pptx.pdf`. O foco aqui e montar a camada de contexto que
explica:

- operacao do reservatorio
- hidrologia de entrada e saida
- tempo de residencia e energia deposicional
- qualidade da agua e sinais de eutrofizacao
- uso e cobertura da terra na bacia
- pressao hidroclimatica sobre o sistema

Referencias canonicas desta preparacao:

- `config/context_clarkshill.yaml`
- `GSA Presentation Slide 2.pptx.pdf`
- `EDA/operacao_reservatorio/`

## Escopo analitico

O `context_clarkshill.yaml` define que esta EDA deve produzir o contexto fisico para
interpretar deposicao fina, enriquecimento em ferro e estabilizacao de carbono organico.

O slide 2 da apresentacao reforca a motivacao:

- sedimentos regulam armazenamento e mobilidade de nutrientes
- sedimentos controlam potencial de carga interna
- sedimentos influenciam a sustentabilidade do reservatorio
- Clarks Hill apresenta preocupacao com floracoes algais periodicas

Portanto, esta EDA deve priorizar variaveis de contexto que ajudem a ligar
hidrodinamica e qualidade da agua a zonas de baixa energia, sem fabricar dados
de sedimento que pertencem a outra trilha do estudo.

## Estrutura desta pasta

- `process_context_sources.py`
  - consolida o intake inicial a partir dos manifests de busca e coleta
  - classifica fontes em `usable_now`, `blocked`, `discovered_only`
  - prepara inventario parcial sem gerar `data/staging/` ou `data/analytic/`
- `generate_figures.py`
  - sera responsavel por gerar as figuras finais a partir de tabelas harmonizadas
- `generate_presentation.py`
  - prepara o contexto estruturado que depois sera consumido pelo agent de relatorio HTML
- `report_context.template.json`
  - template inicial do contexto narrativo das figuras
- `handoff_contract.md`
  - contrato minimo esperado para a entrega do Harvester e do chat principal
- `initial_source_inventory.partial.json`
  - inventario inicial do que ja esta realmente aproveitavel
- `initial_source_inventory.partial.md`
  - leitura humana do inventario parcial
- `figures/`
  - destino das figuras finais

## Estado atual do handoff parcial

Busca concluida:

- `data/runs/perplexity-intel-8ba66531/manifest.json`
- `data/runs/perplexity-intel-8ba66531/processing/03-ranked-datasets.json`
- `data/runs/perplexity-intel-8ba66531/processing/04-harvester-handoff.json`

Coleta em andamento:

- `data/runs/operational-collect-clarkshill-20260401-225924/manifest.json`

Resumo atual:

- 30 datasets ranqueados na busca
- 6 alvos priorizados pelo Harvester nesta rodada
- 2 alvos com artefato local coletado
- 4 alvos bloqueados por timeout, redirect ou restricao de acesso

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

### Criticos, mas bloqueados por enquanto

- `01-savannah-river-augusta-intake-data`
  - bloqueio: redirect em vez de exportacao de dados WQP
  - impacto: sem serie estruturada inicial de qualidade da agua nesse ponto

- `08-clark-hill-dam-inflows-and-forecasts`
  - bloqueio: timeout na navegacao inicial
  - impacto: sem serie de inflow/forecast para abrir camada operacional/hidrologica

- `14-savannah-and-salkehatchie-surface-water-data`
  - bloqueio: 403 CloudFront geoblock
  - impacto: sem documento de apoio amplo para hidrologia/regra operacional

- `sas-usace-thurmond-basin-dam`
  - bloqueio: access denied via Akamai/edgesuite
  - impacto: sem documento institucional adicional do USACE nesta rodada

## Proxima camada analitica esperada

O que ja pode ser feito sem fabricar dados:

1. inventario de fontes realmente disponiveis
2. plano de extracao dos dois PDFs ja coletados
3. definicao das variaveis de contexto por tema
4. preparacao dos contratos de entrada para quando chegarem dados estruturados

O que ainda NAO deve ser feito sem nova coleta:

- staging de operacao do reservatorio
- analytic de series temporais
- calculo de tempo de residencia
- figuras hidrologicas reais
- figuras de qualidade da agua reais

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
