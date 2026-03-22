# AGENTS.md

## 1) Objetivo do projeto
Este repositorio implementa um pipeline para descoberta, enriquecimento, priorizacao e consolidacao de fontes e datasets ambientais com foco em um artigo cientifico.

O trabalho segue alinhado ao projeto 100K, com prioridade para:
- corredor entre Sao Paulo e Tres Lagoas
- Rio Tiete
- Reservatorio de Jupia

---

## 2) Arquitetura atual
O fluxo principal e Perplexity Search API-first, com 4 etapas principais e uma Fase C opcional dentro do EnrichAgent.

```
FilterValidate [heuristica] -> Enrich [Fase A + Fase B + Firecrawl opcional] -> RankAccess [heuristica] -> Report [LLM]
```

Etapas do pipeline:
1. montar um contexto mestre da pesquisa
2. gerar chats tematicos especializados
3. executar buscas via Perplexity Search API com o PerplexityAPICollector
4. armazenar a coleta crua em `collection/raw-sessions.json`
5. `FilterValidateAgent` - limpar duplicatas, URLs invalidas e snippets curtos; herdar `track_origin`, `track_priority`, `track_intent`
6. `EnrichAgent / Fase A` - herdar `hierarchy_level`, `thematic_axis` e `source_category` do track
7. `EnrichAgent / Fase B` - extrair `dataset_name`, `data_format`, `temporal_coverage`, `spatial_coverage` e `key_parameters` via LLM
8. `EnrichAgent / Fase C` - opcionalmente gerar `collection_guide` contextual via Firecrawl usando os campos das fases A e B
9. `RankAccessAgent` - ordenar por `track_priority -> data_format`; classificar `access_type` por dominio/extensao; aplicar `--limit`
10. `ReportAgent` - gerar relatorio analitico com cobertura por nivel, formatos, lacunas e proximos passos

---

## 3) Regras de desenvolvimento
- Sempre preferir mudancas pequenas, incrementais e rastreaveis.
- Manter JSONs intermediarios entre etapas do pipeline.
- Validar schemas em cada etapa antes de avancar.
- Nao inventar metadados nao verificados.
- Preservar URLs, snippets, trilhas de pesquisa e origem das informacoes coletadas.
- Priorizar fontes oficiais, institucionais e academicas.
- Separar claramente descoberta no Perplexity, filtragem, enriquecimento, guia de coleta, ranking de acesso e relatorio final.

---

## 4) Regras de implementacao
- Usar Pydantic para definicao e validacao de schemas.
- Organizar prompts em YAML no diretorio `prompts/`.
- Garantir execucao por CLI via `python -m src.main`.
- Incluir testes para coleta, filtragem, enriquecimento, Firecrawl opcional e CLI.
- O conector principal de descoberta externa e o `PerplexityAPICollector` (Search API).
- O guia de coleta contextual e opcional e usa `FirecrawlCollector` quando `FIRECRAWL_API_KEY` estiver configurada.
- A coleta deve ser armazenada antes de qualquer interpretacao posterior dos agentes.
- `hierarchy_level` e `thematic_axis` devem vir do prefixo do track, nunca da LLM.
- `relevance_score` nao existe neste fluxo; relevancia e codificada no desenho das trilhas, no ranking da Search API e em `track_priority`.
- A LLM foca exclusivamente em extracao de metadados que o track nao carrega.

---

## 5) Convencoes de saida
- Coleta crua e artefatos intermediarios em JSON
- Relatorios analiticos em Markdown
- Dashboard humano em HTML
- Exportacoes tabulares em CSV
- Timestamps e rastreabilidade obrigatorios entre entradas e saidas

### Estrutura de diretorios por execucao

Cada execucao grava todos os artefatos dentro de `data/runs/{run-id}/`:

```
data/runs/{run-id}/
|-- config/                       snapshot da configuracao usada (context.json, tracks.json)
|-- master-context.json           contexto mestre da pesquisa
|-- search-plan.json              plano de buscas tematicas
|-- collection/
|   `-- raw-sessions.json         coleta bruta da Perplexity Search API, intocavel
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

---

## 6) Formatos de comunicacao
- Artefatos intermediarios: JSON
- Relatorio final humano: Markdown
- Dashboard final: HTML
- Prompts dos agentes: YAML em `prompts/`
