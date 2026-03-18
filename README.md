# Research_FREnTE

Pipeline multiagente para descoberta, avaliacao e documentacao de bases de dados ambientais no contexto do projeto 100K.

## Objetivo cientifico

Identificar bases uteis para estudar impactos humanos em rios e reservatorios no corredor **Sao Paulo -> Tres Lagoas**, com foco no **Rio Tiete** e conexao com o **Reservatorio de Jupia**.

## Capacidades atuais

- `ResearchScoutAgent` usa conector abstrato de pesquisa web, com modo `mock` e modo `real`, e pode usar LLM para triagem e enriquecimento de links/fontes.
- `QueryExpansionAgent` pode usar LLM real para ampliar queries a partir dos achados do scout, mantendo fallback heuristico.
- `ReportAgent` permanece deterministico para reduzir deriva narrativa.
- Os demais agentes seguem deterministicos e auditaveis.

## Classificacao de fontes

O pipeline distingue duas classes principais:

- `analytical_data_source`: fonte com dados utilizaveis diretamente em analise.
- `scientific_knowledge_source`: fonte de conhecimento cientifico/metodologico.

Campos relevantes preservados no scout, normalizacao e catalogo:

- `source_class`
- `source_roles`
- `data_extractability`
- `historical_records_available`
- `structured_export_available`
- `scientific_value`
- `recommended_pipeline_use`

## Configuracao de LLM

O projeto esta preparado para usar a API da OpenAI com o modelo `gpt-4.1-nano`.
Tambem existe um modo de teste com Groq usando `groq/compound-mini`.

1. Instale as dependencias do projeto.
2. Copie `.env.example` para `.env`.
3. Preencha `OPENAI_API_KEY` no `.env`.

Exemplo de `.env`:

```env
OPENAI_API_KEY=...
GROQ_API_KEY=
RESEARCH_FRENTE_LLM_MODE=auto
RESEARCH_FRENTE_LLM_MODEL=gpt-4.1-nano
RESEARCH_FRENTE_GROQ_TEST_MODEL=groq/compound-mini
```

Com `RESEARCH_FRENTE_LLM_MODE=auto`, o pipeline:

- usa OpenAI quando `OPENAI_API_KEY` estiver presente;
- usa Groq quando nao houver `OPENAI_API_KEY` mas existir `GROQ_API_KEY`;
- cai para fallback heuristico quando nenhuma chave estiver definida;
- desabilita LLM automaticamente em `dry-run`.

## Configuracao YAML de referencia

O arquivo [config/settings.example.yaml](d:/Projetos/Github_ViniciusJ/Research_FREnTE/config/settings.example.yaml) documenta a configuracao recomendada:

```yaml
pipeline:
  query: "impactos humanos no Rio Tiete reservatorios Sao Paulo Tres Lagoas qualidade agua"
  limit: 10
  dry_run: false
  web_research_mode: "real"
  web_timeout_seconds: 5

llm:
  mode: "auto"
  model: "gpt-4.1-nano"
  timeout_seconds: 60
  temperature: 0.2
  max_output_tokens: 1800
  fail_on_error: false
```

## Arquitetura resumida

1. `ResearchScoutAgent`
2. `QueryExpansionAgent`
3. `DatasetDiscoveryAgent`
4. `NormalizationAgent`
5. `RelevanceAgent`
6. `AccessAgent`
7. `ExtractionPlanAgent`
8. `ReportAgent`
9. `OrchestratorAgent`

## Execucao

### Dry-run

```bash
python -m src.main dry-run --query "impactos humanos no Rio Tiete" --limit 7
```

### Run com fallback automatico para OpenAI

```bash
python -m src.main run --query "impactos humanos no Rio Tiete reservatorios Sao Paulo Tres Lagoas qualidade agua" --limit 10 --web-mode real
```

### Run forcando OpenAI

```bash
python -m src.main run --query "impactos humanos no Rio Tiete" --limit 10 --web-mode real --llm-mode openai --llm-model gpt-4.1-nano
```

### Run de teste com Groq

```bash
python -m src.main run --query "impactos humanos no Rio Tiete" --limit 10 --web-mode real --llm-mode groq --llm-model groq/compound-mini
```

### Inicializacao real em larga escala

```bash
python -m src.main real-init --limit-per-run 10 --max-queries 8 --web-timeout 5 --llm-mode auto
```

### Exportacao CSV

```bash
python -m src.main export --catalog data/runs/<run_id>/catalog.json --output reports/<run_id>.csv
```

## Artefatos

- `data/runs/<run_id>/01_research-scout.json`: achados de pesquisa aberta (`web_research_results`, `web_research_results_raw`, `web_research_results_discarded`, `web_research_results_kept`, `sources`) e `web_research_meta`.
- `data/runs/<run_id>/02_query-expansion.json`: expansoes de consulta e queries geradas.
- `data/runs/<run_id>/03_dataset-discovery.json`: candidatos consolidados e catalogo preliminar.
- `data/runs/<run_id>/04_normalization.json`: datasets normalizados e evidencias consolidadas.
- `data/runs/<run_id>/05_relevance.json`: scoring e justificativas de relevancia.
- `data/runs/<run_id>/06_access.json`: classificacao de acesso, links e observacoes de extracao.
- `data/runs/<run_id>/07_extraction-plan.json`: plano de extracao priorizado.
- `data/runs/<run_id>/08_report.json`: metadados do relatorio final.
- `data/runs/<run_id>/catalog.json`: catalogo consolidado.
- `data/runs/<run_id>/run_metadata.json`: metadados da execucao.
- `reports/<run_id>.md`: relatorio de execucao.
- `reports/<run_id>.csv`: exportacao tabular do catalogo.

`run_metadata.json` registra:

- `llm_mode_requested`
- `llm_provider_used`
- `llm_model_used`
- `llm_enabled_agents`
- `llm_setup_error`

## Status de recuperacao no `ResearchScoutAgent`

- `no_results`: o conector real nao retornou resultados uteis ou houve erro de rede/timeout.
- `all_filtered`: houve resultados reais, mas todos foram descartados por irrelevancia.
- `low_recall`: houve resultados reais validos, mas em quantidade baixa apos filtragem.
- `mock_fallback`: uso de dados mock em `dry-run` ou com `--web-mode mock`.

## Dependencias principais

- `pydantic`
- `httpx`
- `PyYAML`
- `openai`
- `python-dotenv`
