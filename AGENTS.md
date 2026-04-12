# AGENTS.md

## 1) Objetivo do projeto
Este repositorio implementa um pipeline multi-agente para:
- descoberta de fontes ambientais via Perplexity Search API
- enriquecimento semantico por LLM
- ranking de acesso
- coleta operacional de fontes selecionadas
- producao de relatorios HTML e EDA para apresentacoes

O trabalho esta alinhado ao Projeto 100K e hoje possui dois eixos geograficos:
- Brasil - Bacia do Rio Tiete: Sao Paulo -> Tres Lagoas / Jupia
- EUA - Clarks Hill Lake / J. Strom Thurmond

No eixo EUA, o trabalho atual deve ser lido como suporte contextual ao estudo
sedimentologico apresentado em `GSA Presentation Slide 2.pptx (1).pdf`.
A pergunta cientifica principal desse eixo nao e "como operam os reservatorios"
isoladamente, mas "que contexto hidrologico, ambiental e de pressao explica os
padroes sedimentares observados em Clarks Hill / J. Strom Thurmond".

Em termos praticos, isso significa:
- o estudo principal e sedimentocentrico
- o rio Savannah e o eixo contextual principal, no mesmo espirito em que o Tiete
  foi tratado no caso Brasil
- Hartwell, Russell e Thurmond entram como estruturas explicativas dentro do sistema
  fluvial
- os relatorios HTML e EDA deste eixo devem apoiar a interpretacao dos sedimentos,
  especialmente para nutrientes, carga interna, sustentabilidade do reservatorio e
  preocupacao com floracoes algais periodicas

No eixo Brasil, as prioridades praticas do repositorio continuam sendo:
- corredor entre Sao Paulo e Tres Lagoas
- Rio Tiete
- reservatorio de Jupia

---

## 2) Camadas do repositorio
O projeto tem quatro camadas principais:

1. `src/`
- pipeline principal de descoberta, enriquecimento e relatorio
- conectores para Perplexity, LLM, Firecrawl e coleta operacional
- geradores HTML

2. `eda/` e `EDA/`
- analises exploratorias e apresentacoes
- referencia principal atual: `EDA/operacao_reservatorio/`

3. `data/`
- staging, analytic e artefatos por execucao em `data/runs/`

4. `.codex/`
- configuracao local do Codex para este repositorio
- agents especializados
- skills locais reutilizaveis

---

## 3) Arquitetura funcional atual

### 3.1 Pipeline principal de descoberta
O fluxo principal continua Perplexity Search API-first:

```text
FilterValidate [heuristica] -> Enrich [Fase A + Fase B + Firecrawl opcional] -> RankAccess [heuristica] -> Report [LLM]
```

Etapas:
1. montar contexto mestre
2. montar plano de buscas tematicas
3. coletar respostas via `PerplexityAPICollector`
4. armazenar coleta crua em `collection/raw-sessions.json`
5. `FilterValidateAgent` limpar duplicatas, URLs invalidas e snippets curtos
6. `EnrichAgent / Fase A` herdar `hierarchy_level`, `thematic_axis` e `source_category` do track
7. `EnrichAgent / Fase B` extrair `dataset_name`, `data_format`, `temporal_coverage`, `spatial_coverage` e `key_parameters` via LLM
8. `EnrichAgent / Fase C` opcionalmente gerar `collection_guide` via Firecrawl
9. `RankAccessAgent` ordenar por prioridade e formato e classificar `access_type`
10. `ReportAgent` gerar relatorio analitico final

### 3.2 Coleta operacional
O repositorio tambem possui uma trilha de coleta operacional para baixar artefatos brutos de fontes especificas e organizar tudo em `data/runs/{run-id}/`.

Uso por CLI:
- `python -m src.main run`
- `python -m src.main perplexity-intel`
- `python -m src.main collect-operational`
- `python -m src.main export`

Regras da coleta operacional:
- usar navegador ou Playwright para descobrir endpoints reais quando necessario
- preferir download HTTP deterministico depois que a URL real for descoberta
- salvar bruto em `data/runs/{run-id}/collection/{source_slug}/`
- nunca misturar bruto com `data/staging/` ou `data/analytic/`
- registrar bloqueios de login, captcha, e-mail ou aprovacao manual em manifesto

### 3.3 EDA e apresentacao
A linha mais madura de EDA esta em:
- `EDA/operacao_reservatorio/generate_figures.py`
- `EDA/operacao_reservatorio/process_pressoes_ambientais.py`
- `EDA/operacao_reservatorio/generate_presentation.py`
- `EDA/operacao_reservatorio/apresentacao_reservatorios.html`

O padrao visual dessa apresentacao e da familia de relatorios HTML do projeto deve ser preservado em novas entregas HTML.

Para o eixo `Clarks Hill / Savannah River`, a EDA e o HTML devem funcionar como
camada de contexto para o estudo sedimentologico da GSA:
- mostrar comportamento do rio
- mostrar pressoes ambientais e poluentes que atuam sobre o rio
- mostrar modulacao operacional dos reservatorios apenas como explicacao secundaria
- fechar a ponte interpretativa com os sedimentos, sem substituir a analise
  laboratorial e geocientifica do deck principal

### 3.4 Publicacao
O repositorio tambem entrega HTML para `docs/`, incluindo:
- `docs/index.html`
- `docs/clarks-hill/`

---

## 4) Arquitetura local do Codex
Esta pasta concentra a infraestrutura local do Codex usada por este projeto:

### 4.1 `.codex/config.toml`
Responsavel por:
- habilitar recursos locais do Codex
- configurar colaboracao entre agents
- registrar MCPs necessarios ao repositorio

Hoje ele configura:
- `multi_agent = true`
- limites de subagents em `[agents]`
- MCP local do Playwright
- registro de skills locais do projeto

### 4.2 `.codex/agents/`
Contem subagents no formato `.toml`.

Agents locais atuais:
- `portal-data-collector.toml`
  - entra em portais, descobre links reais, bitstreams ou APIs e organiza coleta em `data/runs/`
- `relatorio-html.toml`
  - gera relatorios HTML com padrao visual fixo do projeto, trocando apenas conteudo, imagens e narrativa
- `eda-reservatorio.toml`
  - monta workspaces EDA no padrao do Tiete, cria scripts Python reproduziveis, gera figuras e prepara contexto para relatorio
- `rodada-api-handoff.toml`
  - roda a descoberta geral por API sem Firecrawl, valida o fim da rodada e monta o pacote de handoff para o Harvester

### 4.3 `.codex/skills/`
Contem skills locais reutilizaveis.

Skills locais atuais:
- `portal-data-collector/`
  - fluxo portal-first com Playwright + output auditavel em `data/runs/`
- `report-html-standard/`
  - contrato visual e editorial para relatorios HTML baseados no padrao do projeto
- `reservoir-eda-pipeline/`
  - playbook para transformar dados recebidos em EDA contextual com scripts Python, figuras e handoff para HTML
- `api-search-handoff/`
  - playbook para rodar a busca geral sem Firecrawl, verificar o run e gerar o handoff de coleta para o Harvester

### 4.4 Relacao entre as camadas
Fluxo esperado:
1. `AGENTS.md` explica o projeto e suas restricoes
2. `.codex/config.toml` configura o ambiente local do Codex
3. `.codex/agents/*.toml` define quem faz o trabalho
4. `.codex/skills/*/SKILL.md` define como esse trabalho deve ser feito

Precedencia local:
1. `.codex/config.toml`
2. `~/.codex/config.toml`

Para skills:
1. `.codex/skills/`
2. `~/.codex/skills/`

---

## 5) Regras de desenvolvimento
- Sempre preferir mudancas pequenas, incrementais e rastreaveis.
- Manter JSONs intermediarios entre etapas do pipeline.
- Validar schemas em cada etapa antes de avancar.
- Nao inventar metadados nao verificados.
- Preservar URLs, snippets, trilhas de pesquisa e origem das informacoes coletadas.
- Priorizar fontes oficiais, institucionais e academicas.
- Separar claramente descoberta, filtragem, enriquecimento, guia de coleta, ranking e relatorio.
- Quando houver padrao visual existente, adaptar o conteudo em vez de redesenhar.

---

## 6) Regras de implementacao
- Usar Pydantic para definicao e validacao de schemas.
- Organizar prompts em YAML no diretorio `prompts/`.
- Garantir execucao por CLI via `python -m src.main`.
- Incluir testes para coleta, filtragem, enriquecimento, Firecrawl opcional, coleta operacional e CLI.
- O conector principal de descoberta externa e o `PerplexityAPICollector`.
- O guia de coleta contextual e opcional e usa `FirecrawlCollector` quando `FIRECRAWL_API_KEY` estiver configurada.
- A coleta deve ser armazenada antes de qualquer interpretacao posterior dos agentes.
- `hierarchy_level` e `thematic_axis` devem vir do prefixo do track, nunca da LLM.
- `relevance_score` nao existe neste fluxo; relevancia e codificada no desenho das trilhas, no ranking da Search API e em `track_priority`.
- A LLM foca exclusivamente em extracao de metadados que o track nao carrega.
- Para coleta operacional, usar navegador apenas para descoberta do endpoint real quando necessario; preferir download HTTP depois disso.
- Para HTML de relatorio, usar como referencias principais:
  - `EDA/operacao_reservatorio/apresentacao_reservatorios.html`
  - `EDA/operacao_reservatorio/generate_presentation.py`
  - `src/generators/html_report_generator.py`

---

## 7) Convencoes de saida
- Coleta crua e artefatos intermediarios: JSON
- Relatorios analiticos: Markdown
- Dashboard humano e apresentacoes: HTML
- Exportacoes tabulares: CSV
- Timestamps e rastreabilidade: obrigatorios

### 7.1 Estrutura por execucao do pipeline principal
Cada execucao do pipeline principal grava artefatos em `data/runs/{run-id}/`:

```text
data/runs/{run-id}/
|-- config/
|   |-- context.json
|   `-- tracks.json
|-- master-context.json
|-- search-plan.json
|-- collection/
|   `-- raw-sessions.json
|-- processing/
|   |-- 01-filtered-sources.json
|   |-- 02-enriched-datasets.json
|   `-- 03-ranked-datasets.json
|-- reports/
|   |-- {run-id}.md
|   |-- relatorio_100k.html
|   |-- sources.csv
|   `-- datasets.csv
`-- manifest.json
```

### 7.2 Estrutura por execucao da coleta operacional
Cada execucao de coleta operacional grava artefatos em `data/runs/{run-id}/`:

```text
data/runs/{run-id}/
|-- config/
|   `-- collection-options.json
|-- collection/
|   `-- {source_slug}/
|       |-- arquivos brutos
|       `-- notas de bloqueio, quando existirem
|-- processing/
|   `-- 01-collection-targets.json
|-- reports/
|   |-- {run-id}.md
|   `-- collection_targets.csv
`-- manifest.json
```

### 7.3 Camadas analiticas
Camadas de consumo:
- `data/staging/`
- `data/analytic/`

Nunca gravar coleta bruta diretamente nessas pastas.

---

## 8) Formatos de comunicacao
- Artefatos intermediarios: JSON
- Relatorio final humano: Markdown
- Dashboard final e apresentacoes: HTML
- Prompts dos agentes: YAML em `prompts/`
- Skills locais do Codex: `SKILL.md` + `references/` + `scripts/` + `agents/openai.yaml`
