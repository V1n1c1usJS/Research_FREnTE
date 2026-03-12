# Research_FREnTE

Pipeline multiagente para descoberta, avaliação e documentação de bases de dados ambientais no contexto do projeto 100K.

## Objetivo científico

Identificar bases úteis para estudar impactos humanos em rios e reservatórios no corredor **São Paulo → Três Lagoas**, com foco no **Rio Tietê** e conexão com o **Reservatório de Jupiá**.

## Nova capacidade: pesquisa aberta na web

O `ResearchScoutAgent` está preparado para pesquisa aberta (web discovery) sem depender de lista fixa:

- usa conector abstrato (`WebResearchConnector`);
- suporta modo `mock` (`MockWebResearchConnector`) com achados realistas e auditáveis;
- possui modo real inicial (`DuckDuckGoWebResearchConnector`) e alias de compatibilidade (`PreparedWebResearchConnector`), sem acoplamento a um único portal;
- retorna resultados estruturados (`WebResearchResultRecord`) com URL, evidência, variáveis e confiança.

## Query expansion (novo)

O `QueryExpansionAgent` agora recebe `web_research_results` do `ResearchScoutAgent` e:

- extrai sinônimos, termos técnicos, aliases de variáveis e expressões metodológicas;
- gera novas consultas para descoberta de datasets e literatura;
- persiste saídas em `data/runs/<run_id>/02_query-expansion.json`.


## Normalização robusta (novo)

O `NormalizationAgent` consolida resultados do scout + discovery com:

- deduplicação por nome, aliases e URL canônica;
- separação explícita entre `dataset`, `portal`, `documentation` e `academic_source`;
- normalização de organização responsável, variáveis e temas;
- registro de evidências de origem com `provenance`;
- campo `confidence` para apoiar priorização posterior.



## Access evaluation (novo)

O `AccessAgent` classifica formas de acesso dos datasets priorizados e adiciona metadados de extração:

- classes: `api`, `download_manual`, `portal`, `documentation`, `ogc`, `unknown`;
- coleta de `access_links` e `documentation_links`;
- inferência de `requires_auth`;
- preservação de `formats`;
- `extraction_observations` para orientar ingestão futura e fallback mock quando necessário.

## Relevance scoring (novo)

O `RelevanceAgent` usa critérios explícitos e ponderados para o projeto 100K:

- `geographic_adherence` (peso `0.25`): aderência ao eixo São Paulo → Três Lagoas, Rio Tietê e Jupiá.
- `thematic_adherence` (peso `0.35`): cobertura de variáveis/temas de interesse.
- `data_readiness` (peso `0.15`): prontidão de uso (formato, frequência, tipo de entidade).
- `evidence_strength` (peso `0.15`): quantidade de evidências/proveniência no registro.
- `source_confidence` (peso `0.10`): confiança de origem herdada do scout/normalização.

Fórmula: `score = sum(weight_i * score_i)`.

Prioridade final:
- `critical` (`>= 0.85`)
- `high` (`>= 0.72`)
- `medium` (`>= 0.55`)
- `low` (`>= 0.35`)
- `discard` (`< 0.35`)

A saída é auditável em `relevance_breakdown`, incluindo:
- pesos usados,
- scores por critério,
- categorias: `anthropic_pressure`, `physical_context`, `environmental_response`.

## Arquitetura resumida (ordem de execução)

1. `ResearchScoutAgent`
2. `QueryExpansionAgent`
3. `DatasetDiscoveryAgent` (consolida e deduplica candidatos com evidências por fonte)
4. `NormalizationAgent`
5. `RelevanceAgent`
6. `AccessAgent`
7. `ExtractionPlanAgent`
8. `ReportAgent`
9. `OrchestratorAgent`

### Saída ampliada do DatasetDiscoveryAgent

Cada candidato agora inclui:
- relacionamento explícito dataset ↔ fontes (`source_mentions` e `source_ids`);
- distinção de acessibilidade (`direct_access`, `literature_citation`, `mixed`);
- status de verificabilidade (`verifiable`, `partially_verifiable`, `cited_not_directly_accessible`, etc.);
- consolidação por evidência com `evidence_count`, origem (`mention_origins`) e `confidence_hint`.

## Estrutura

```text
src/
  agents/
  connectors/
  schemas/
  pipelines/
  utils/
prompts/
data/
reports/
tests/
```

## Execução

### Dry-run

```bash
python -m src.main dry-run --query "impactos humanos no Rio Tietê" --limit 7
```

### Pipeline (modo run, mock por padrão)

```bash
python -m src.main run --query "qualidade da água" --limit 7 --web-mode mock
```

### Pipeline (modo run com conector real inicial)

```bash
python -m src.main run --query "qualidade da água" --limit 7 --web-mode real --web-timeout 8
```

### Exportação CSV

```bash
python -m src.main export --catalog data/runs/<run_id>/catalog.json --output reports/<run_id>.csv
```

## Artefatos

- `data/runs/<run_id>/01_research-scout.json`: achados de pesquisa aberta (`web_research_results` + `sources`) e `web_research_meta` (modo, timeout, fallback).
- `data/runs/<run_id>/02_query-expansion.json`: expansões de consulta e queries geradas.
- `data/runs/<run_id>/03_dataset-discovery.json`: candidatos consolidados (`dataset_candidates`), `preliminary_catalog` (origem/confiança/verificabilidade) e relatório simples de evidências.
- `data/runs/<run_id>/06_access.json`: catálogo com classificação de acesso, links e observações de extração.
- `data/runs/<run_id>/catalog.json`: catálogo consolidado.
- `reports/<run_id>.md`: relatório de execução.
- `reports/<run_id>.csv`: export tabular.

## Pontos de extensão

- Evoluir o conector real para múltiplos provedores e scraping controlado com compliance.
- Adicionar normalização de metadados por conector em `src/connectors/`.
- Evoluir o `QueryExpansionAgent` com ranking semântico de termos por domínio.

## Limitações atuais

- O conector real inicial é de triagem geral (DuckDuckGo Instant Answer), podendo retornar cobertura limitada para consultas especializadas.
- Em falha/timeout/resultado vazio no modo real, há fallback automático para mock para preservar execução.
- Dry-run sempre usa dados mock plausíveis; não representa consulta em tempo real.
