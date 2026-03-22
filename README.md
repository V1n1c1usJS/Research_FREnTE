# Research_FREnTE

Pipeline para pesquisa de artigo com descoberta de fontes via **Perplexity Search API**, seguido de categorizacao, consolidacao de inteligencia e estruturacao de candidatos a dataset.

## Objetivo

Identificar fontes, datasets e conhecimento academico para um problema de pesquisa ambiental, a partir de um **contexto mestre configuravel** e de **chats tematicos especificos**.

O repositorio continua alinhado ao projeto 100K e ao caso Sao Paulo -> Tres Lagoas / Rio Tiete / Jupia.

## Fluxo atual

O projeto hoje funciona assim:

1. [src/main.py](src/main.py) recebe a configuracao de execucao pela CLI
2. [src/pipelines/perplexity_intelligence_pipeline.py](src/pipelines/perplexity_intelligence_pipeline.py) monta o contexto mestre e o plano de chats
3. [src/connectors/perplexity_api.py](src/connectors/perplexity_api.py) executa as buscas via Perplexity Search API e armazena a coleta crua
4. [src/agents/filter_validate_agent.py](src/agents/filter_validate_agent.py) remove duplicatas e URLs invalidas; herda track_origin, track_priority e track_intent de cada sessao
5. [src/agents/enrich_agent.py](src/agents/enrich_agent.py) deriva hierarchy_level/thematic_axis/source_category do track (Fase A); usa LLM para extrair dataset_name, data_format, cobertura temporal/espacial e parametros-chave (Fase B); opcionalmente usa Firecrawl para gerar collection_guide contextual (Fase C)
6. [src/agents/rank_access_agent.py](src/agents/rank_access_agent.py) ordena por track_priority → data_format e classifica access_type por dominio/extensao
7. [src/agents/report_agent.py](src/agents/report_agent.py) gera relatorio analitico com cobertura por nivel, formatos, lacunas e proximos passos

### Conector de coleta

O conector principal e o [src/connectors/perplexity_api.py](src/connectors/perplexity_api.py) (`PerplexityAPICollector`).

Ele e responsavel por:

- iterar sobre o plano de buscas
- chamar `POST https://api.perplexity.ai/search` para cada trilha tematica
- receber resultados rankeados com `title`, `url` e `snippet` por item
- montar os `PerplexitySearchSessionRecord` para consumo pelos agentes

## Onde a configuracao do projeto existe

Hoje a configuracao do projeto esta distribuida em 6 camadas:

1. **CLI**
   Definida em [src/main.py](src/main.py).
   E a configuracao principal de runtime.
2. **Arquivo de contexto mestre**
   Opcional.
   Estrutura definida por [PerplexityResearchContextRecord](src/schemas/records.py) em [src/schemas/records.py](src/schemas/records.py).
3. **Arquivo de trilhas/chats tematicos**
   Opcional.
   Estrutura definida por [PerplexityResearchTrackRecord](src/schemas/records.py) em [src/schemas/records.py](src/schemas/records.py).
4. **Variaveis de ambiente**
   Carregadas em [src/main.py](src/main.py) via `python-dotenv`, quando disponivel.
   No fluxo atual, `PERPLEXITY_API_KEY` e obrigatoria para a coleta, `OPENAI_API_KEY` e opcional para inferencia estrutural e `FIRECRAWL_API_KEY` e opcional para o guia de coleta.
5. **Defaults internos da pipeline**
   Definidos em [src/pipelines/perplexity_intelligence_pipeline.py](src/pipelines/perplexity_intelligence_pipeline.py).
   Entram em acao quando voce nao passa arquivos ou flags especificas.
6. **Schemas de validacao**
   Definidos em [src/schemas/settings.py](src/schemas/settings.py) e [src/schemas/records.py](src/schemas/records.py).
   Eles nao sao “config” do usuario, mas controlam quais valores sao aceitos e como os dados sao validados.

## Ordem de precedencia

Quando ha mais de uma fonte de configuracao, pense na ordem abaixo:

1. **Flags da CLI**
   Sempre vencem, porque sao passadas diretamente para a pipeline.
2. **`context-file` e `tracks-file`**
   Sobrescrevem os defaults internos da pipeline para contexto e trilhas.
   Se nao forem passados e os arquivos `config/context_100k.yaml` e `config/tracks_100k.yaml` existirem, eles viram o preset padrao do projeto.
3. **`.env`**
   Hoje entra para autenticar a Perplexity Search API via `PERPLEXITY_API_KEY`, a OpenAI via `OPENAI_API_KEY` e, opcionalmente, o Firecrawl via `FIRECRAWL_API_KEY`.
4. **Defaults internos**
   Sao usados quando voce nao informa alguma configuracao.

## Configuracoes da CLI

As configuracoes principais estao em [src/main.py](src/main.py), dentro de `_add_perplexity_args()`.

### Comandos disponiveis

- `run`
  Executa o fluxo principal.
- `perplexity-intel`
  Alias explicito do mesmo fluxo principal.
- `export`
  Exporta um catalogo JSON para CSV.

### Flags de `run` e `perplexity-intel`

| Flag                     | Default                  | Onde definida           | Como funciona                                                                                                                                   |
| ------------------------ | ------------------------ | ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `--query`              | sem default, obrigatoria | [src/main.py](src/main.py) | Tema base da pesquisa. Alimenta o contexto mestre default, o plano de chats e os artefatos finais.                                              |
| `--limit`              | `20`                   | [src/main.py](src/main.py) | Limite de datasets/fontes normalizadas usados no pipeline. Tambem e validado por[PipelineSettings](src/schemas/settings.py).                       |
| `--max-searches`       | `5`                    | [src/main.py](src/main.py) | Numero maximo de chats tematicos usados apenas quando o pipeline recorre aos defaults internos. Quando um `tracks-file` e fornecido, o projeto respeita todas as trilhas do arquivo.        |
| `--perplexity-max-results` | `20`               | [src/main.py](src/main.py) | Numero maximo de resultados por busca na Search API (1-20).                                                                                     |
| `--perplexity-timeout` | `60.0`                 | [src/main.py](src/main.py) | Timeout em segundos das chamadas a Search API do Perplexity.                                                                                    |
| `--context-file`       | `None`                 | [src/main.py](src/main.py) | Caminho para um JSON ou YAML com o contexto mestre da pesquisa. Se presente, substitui o contexto default gerado pela pipeline. Se ausente, o projeto tenta carregar `config/context_100k.yaml` automaticamente.          |
| `--tracks-file`        | `None`                 | [src/main.py](src/main.py) | Caminho para um JSON ou YAML com as trilhas/chats tematicos. Se presente, substitui as trilhas default da pipeline. Se ausente, o projeto tenta carregar `config/tracks_100k.yaml` automaticamente.                      |
| `--track-limit`       | `None`                 | [src/main.py](src/main.py) | Limita quantas trilhas do arquivo de tracks serao executadas na rodada atual. E util para depurar a coleta uma busca por vez.                   |
| `--llm-mode`           | `auto`                 | [src/main.py](src/main.py) | Controla se a categorizacao de fontes usa LLM. Valores aceitos:`auto`, `off`, `openai`.                                                   |
| `--llm-model`          | `gpt-4.1-nano`         | [src/main.py](src/main.py) | Modelo OpenAI usado na inferencia estrutural das fontes.                                                                                        |
| `--llm-timeout`        | `60.0`                 | [src/main.py](src/main.py) | Timeout das chamadas de inferencia por LLM.                                                                                                     |
| `--llm-fail-on-error`  | `False`                | [src/main.py](src/main.py) | Se ativado, falhas da LLM interrompem a execucao. Se nao, o fluxo cai para heuristica.                                                          |
| `--skip-collection-guides` | `False`            | [src/main.py](src/main.py) | Pula a Fase C do EnrichAgent e nao chama o Firecrawl, mesmo se `FIRECRAWL_API_KEY` estiver configurada.                                        |

### Flags de `export`

| Flag          | Default                  | Onde definida           | Como funciona                                    |
| ------------- | ------------------------ | ----------------------- | ------------------------------------------------ |
| `--catalog` | sem default, obrigatoria | [src/main.py](src/main.py) | Caminho para o JSON de catalogo a ser exportado. |
| `--output`  | sem default, obrigatoria | [src/main.py](src/main.py) | Caminho do CSV de saida.                         |

## Configuracao por arquivo

### 1. Contexto mestre

O contexto mestre define o enquadramento conceitual da pesquisa.

Ele e validado por [PerplexityResearchContextRecord](src/schemas/records.py), com os campos:

| Campo                 | Onde definido                                 | Como funciona                                                                                          |
| --------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `context_id`        | [src/schemas/records.py](src/schemas/records.py) | Identificador do contexto. Vai para os artefatos, mas nao muda a logica sozinho.                       |
| `article_goal`      | [src/schemas/records.py](src/schemas/records.py) | Objetivo principal da pesquisa. Entra na montagem dos prompts de busca.                                |
| `geographic_scope`  | [src/schemas/records.py](src/schemas/records.py) | Lista de recortes geograficos. E usada nos prompts e no `RelevanceAgent`.                            |
| `thematic_axes`     | [src/schemas/records.py](src/schemas/records.py) | Lista de eixos tematicos. E usada nos prompts, no `RelevanceAgent` e refletida no consolidado final. |
| `preferred_sources` | [src/schemas/records.py](src/schemas/records.py) | Tipos de fonte que devem ser priorizados na busca.                                                     |
| `expected_outputs`  | [src/schemas/records.py](src/schemas/records.py) | Ajuda a orientar o que os chats devem procurar.                                                        |
| `exclusions`        | [src/schemas/records.py](src/schemas/records.py) | Ruido ou tipos de conteudo a evitar conceitualmente.                                                   |
| `notes`             | [src/schemas/records.py](src/schemas/records.py) | Observacoes livres para orientar o contexto.                                                           |

Exemplo:

```yaml
context_id: ctx-artigo-001
article_goal: Investigar impactos antropicos em sistema aquatico costeiro
geographic_scope:
  - Costa norte
  - Estuario principal
thematic_axes:
  - monitoramento ambiental
  - qualidade da agua
  - vetores de pressao antropica
preferred_sources:
  - portais institucionais
  - repositorios academicos
expected_outputs:
  - links diretos para fontes
  - datasets e programas de monitoramento
exclusions:
  - conteudo promocional
notes:
  - priorizar fontes com dados recorrentes
```

### 2. Trilhas ou chats tematicos

As trilhas dizem como a pesquisa sera quebrada em conversas menores no Perplexity.

Elas sao validadas por [PerplexityResearchTrackRecord](src/schemas/records.py), com os campos:

| Campo                 | Onde definido                                 | Como funciona                                                                                                                  |
| --------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `research_track`    | [src/schemas/records.py](src/schemas/records.py) | Nome interno da trilha. Vai para o plano de busca, artefatos e consolidado.                                                    |
| `chat_label`        | [src/schemas/records.py](src/schemas/records.py) | Rotulo humano do chat.                                                                                                         |
| `search_profile`    | [src/schemas/records.py](src/schemas/records.py) | Perfil de busca associado a essa trilha. Hoje ele e mais semantico do que comportamental, mas e preservado em todo o pipeline. |
| `target_intent`     | [src/schemas/records.py](src/schemas/records.py) | Intencao da trilha, por exemplo `dataset_discovery`, `academic_knowledge` ou `contextual_intelligence`.                  |
| `research_question` | [src/schemas/records.py](src/schemas/records.py) | Pergunta central daquela trilha. Vai para a montagem do prompt do Perplexity.                                                  |
| `task_prompt`       | [src/schemas/records.py](src/schemas/records.py) | Instrucao operacional do que procurar naquela trilha.                                                                          |
| `priority`          | [src/schemas/records.py](src/schemas/records.py) | Prioridade descritiva da trilha. E carregada para o plano de busca e artefatos.                                                |

Exemplo:

```yaml
- research_track: monitoring_sources
  chat_label: chat-monitoramento
  search_profile: monitoring_sources
  target_intent: dataset_discovery
  research_question: Quais fontes trazem series historicas e monitoramento recorrente?
  task_prompt: Busque programas de monitoramento, paineis, catalogos e datasets recorrentes ligados ao tema.
  priority: high
- research_track: academic_knowledge
  chat_label: chat-academico
  search_profile: academic_knowledge
  target_intent: academic_knowledge
  research_question: Quais estudos citam bases de dados ou metodologias reutilizaveis?
  task_prompt: Busque artigos, teses e repositorios que referenciem dados ou protocolos metodologicos.
  priority: medium
```

Uso com arquivos:

```bash
python -m src.main run --query "monitoramento ambiental costeiro" --context-file config/context.yaml --tracks-file config/tracks.yaml
```

## Defaults internos da pipeline

Quando voce nao passa `context-file` nem `tracks-file`, a CLI tenta primeiro carregar os presets [config/context_100k.yaml](config/context_100k.yaml) e [config/tracks_100k.yaml](config/tracks_100k.yaml). So na ausencia deles a pipeline recorre aos defaults internos em [src/pipelines/perplexity_intelligence_pipeline.py](src/pipelines/perplexity_intelligence_pipeline.py).

### Defaults do contexto mestre

Definidos em `_build_master_context()`.

Comportamento atual:

- `context_id` default: `ctx-article-001`
- `article_goal`: construido dinamicamente a partir de `base_query`
- `geographic_scope`: vazio por default
- `thematic_axes`: lista generica ambiental
- `preferred_sources`: lista generica de fontes institucionais, academicas e de dados
- `expected_outputs`, `exclusions` e `notes`: preenchidos com defaults genericos

### Defaults das trilhas

Definidos em `DEFAULT_RESEARCH_TRACKS`.

As 5 trilhas default sao:

- `official_data_portals`
- `monitoring_and_measurements`
- `pressure_and_drivers`
- `institutional_reports`
- `academic_knowledge`

Cada uma ja traz `chat_label`, `search_profile`, `target_intent`, `research_question`, `task_prompt` e `priority`.

### Defaults do coletor Search API

Definidos em [src/connectors/perplexity_api.py](src/connectors/perplexity_api.py):

- `max_results=20`
- `timeout_seconds=60.0`

Esses valores sao usados quando a CLI nao passa overrides.

### Defaults da LLM

Definidos na pipeline e no conector OpenAI:

- `llm_mode="auto"`
- `llm_model="gpt-4.1-nano"`
- `llm_timeout_seconds=60.0`
- `llm_fail_on_error=False`

No conector [src/connectors/llm.py](src/connectors/llm.py), o `OpenAIResponsesConnector` ainda tem defaults internos:

- `max_output_tokens=1800`
- `temperature=0.1`

Esses dois valores hoje **nao sao configurados pela CLI**.

## Variaveis de ambiente

As variaveis de ambiente sao carregadas em [src/main.py](src/main.py), na funcao `_load_dotenv_if_available()`.

### Variaveis ativas no fluxo atual

- `PERPLEXITY_API_KEY`
  Onde usada: [src/main.py](src/main.py), antes de instanciar a pipeline, e em [src/connectors/perplexity_api.py](src/connectors/perplexity_api.py).
  Como funciona:
  - e obrigatoria para qualquer execucao de `run` ou `perplexity-intel`
  - sem ela a CLI encerra com erro antes de iniciar a coleta
- `OPENAI_API_KEY`
  Onde usada: [src/pipelines/perplexity_intelligence_pipeline.py](src/pipelines/perplexity_intelligence_pipeline.py), em `_build_llm_connector()`.
  Como funciona:
  - se `--llm-mode off`, a chave e ignorada
  - se `--llm-mode auto`, a LLM so e habilitada se a chave existir
  - se `--llm-mode openai`, a ausencia da chave gera erro
- `FIRECRAWL_API_KEY`
  Onde usada: [src/agents/enrich_agent.py](src/agents/enrich_agent.py) e [src/connectors/firecrawl_collector.py](src/connectors/firecrawl_collector.py).
  Como funciona:
  - e opcional
  - se existir e `--skip-collection-guides` nao for usado, a Fase C tenta gerar `collection_guide`
  - se nao existir, o pipeline continua normalmente com `collection_guide = null`

Exemplo minimo de `.env` util hoje:

```env
PERPLEXITY_API_KEY=...
OPENAI_API_KEY=...
FIRECRAWL_API_KEY=...
```

### Variaveis que existem no `.env.example`, mas hoje sao legadas

O arquivo [.env.example](.env.example) ainda contem:

- `GROQ_API_KEY`
- `RESEARCH_FRENTE_LLM_MODE`
- `RESEARCH_FRENTE_LLM_MODEL`
- `RESEARCH_FRENTE_GROQ_TEST_MODEL`
- `RESEARCH_FRENTE_LLM_TIMEOUT_SECONDS`
- `RESEARCH_FRENTE_LLM_TEMPERATURE`
- `RESEARCH_FRENTE_LLM_MAX_OUTPUT_TOKENS`
- `RESEARCH_FRENTE_LLM_FAIL_ON_ERROR`

Essas variaveis **nao sao lidas pelo fluxo principal atual**.
Hoje a configuracao de runtime e dirigida pela CLI, e nao por essas variaveis.

## Schema de configuracao leve do pipeline

O arquivo [src/schemas/settings.py](src/schemas/settings.py) define [PipelineSettings](src/schemas/settings.py), com:

| Campo     | Default no schema | Como funciona                                                                                                                                   |
| --------- | ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `query` | sem default       | Tema principal da pesquisa. E obrigatorio.                                                                                                      |
| `limit` | `10`            | Limite maximo por etapa. No fluxo normal, a CLI passa `20` como default, entao o schema fica mais como validacao do que como origem do valor. |

Observacao importante:

- a CLI usa `--limit` com default `20`
- o schema `PipelineSettings` usa default `10`

Na execucao normal pela CLI, **vale o valor da CLI**.
O default `10` do schema so entra se `PipelineSettings` for instanciado em outro lugar sem `limit`.

## Como cada configuracao afeta os agentes

### `FilterValidateAgent`

Usa:

- `perplexity_sessions`
- `perplexity_search_plan` (para herdar `priority` por query_id)

Impacto da configuracao:

- nao usa LLM — puramente heuristico
- herda `track_origin`, `track_priority`, `track_intent` de cada sessao para uso downstream

### `EnrichAgent`

Usa:

- `filtered_sources`
- `llm_connector` opcional

Impacto da configuracao:

- **Fase A** (deterministica): `hierarchy_level` e `thematic_axis` vem do prefixo do track (n1\_, n2\_, n3\_, n4\_); `source_category` vem do dominio ou do `track_intent`
- **Fase B** (LLM): `llm-mode`, `llm-model` e `OPENAI_API_KEY` definem se a extracao de metadados usa LLM ou heuristica de fallback
- **Fase C** (Firecrawl opcional): `FIRECRAWL_API_KEY` ativa a extracao de `collection_guide`; `--skip-collection-guides` desliga essa fase mesmo com chave presente
- Com `--llm-mode off`, o agente usa heuristicas baseadas em palavras-chave no titulo/snippet

### `RankAccessAgent`

Usa:

- `enriched_datasets`
- `limit` (via pipeline)

Impacto da configuracao:

- `--limit` controla quantos datasets seguem para o relatorio
- ordena por: track_priority (high primeiro) → data_format (structured primeiro)
- classifica `access_type` por extensao de arquivo e dominio conhecido

### `ReportAgent`

Usa:

- `ranked_datasets`
- `perplexity_search_plan`
- `perplexity_sessions`
- `llm_connector` opcional

Impacto da configuracao:

- `llm-mode` define se o relatorio e gerado por LLM (com analise de lacunas) ou por template heuristico
- `query`, `context-file`, `tracks-file` e `max-searches` mudam o escopo do relatorio final

## Estrutura de saida por execucao

Cada execucao gera um diretorio isolado em `data/runs/{run-id}/`:

```
data/runs/{run-id}/
├── config/
│   ├── context.json          snapshot do contexto mestre usado
│   └── tracks.json           snapshot das trilhas usadas
├── master-context.json       contexto mestre da pesquisa
├── search-plan.json          plano de buscas gerado
├── collection/
│   └── raw-sessions.json     coleta bruta da Perplexity Search API
├── processing/
│   ├── 01-categorized-sources.json
│   ├── 02-source-validation.json
│   ├── 03-dataset-candidates.json
│   ├── 04-normalized-datasets.json
│   ├── 05-relevance-scored.json
│   └── 06-access-organized.json
├── reports/
│   ├── {run-id}.md           relatorio final em Markdown
│   ├── sources.csv           catalogo de fontes
│   └── datasets.csv          catalogo de datasets
└── manifest.json             metadados e resumo da execucao
```

## Como inspecionar a configuracao realmente usada em uma execucao

Os artefatos mais importantes para auditoria sao:

- `data/runs/perplexity-intel-*/master-context.json`
  Mostra o contexto mestre efetivamente usado.
- `data/runs/perplexity-intel-*/search-plan.json`
  Mostra os chats/trilhas realmente gerados.
- `data/runs/perplexity-intel-*/collection/raw-sessions.json`
  Mostra o que voltou da Perplexity Search API para cada busca.
- `data/runs/perplexity-intel-*/processing/02-source-validation.json`
  Mostra os ajustes e alertas aplicados antes do discovery.
- `data/runs/perplexity-intel-*/manifest.json`
  Resume `perplexity_max_results`, `llm_mode`, `llm_provider`, `llm_model`, contagens da execucao e metadados de validacao.

## Arquivos de configuracao legados

O repositorio ainda possui [config/settings.example.yaml](config/settings.example.yaml), mas ele pertence ao desenho anterior do projeto e **nao e lido pela CLI atual**.

Ele pode servir como referencia historica, mas nao controla o fluxo `Perplexity-first`.

## Prompts

Os arquivos em `prompts/` funcionam como configuracao semantica dos agentes.

Hoje eles sao carregados por [src/agents/base.py](src/agents/base.py), via `load_prompt()`, e ajudam a documentar o papel de cada agente. Eles nao substituem a configuracao de runtime da CLI, mas fazem parte da configuracao comportamental do projeto.

Prompts principais do fluxo atual:

- `prompts/perplexity_source_categorization_agent.yaml`
- `prompts/source_validation_agent.yaml`
- `prompts/dataset_discovery_agent.yaml`
- `prompts/normalization_agent.yaml`
- `prompts/relevance_agent.yaml`
- `prompts/access_agent.yaml`
- `prompts/perplexity_intelligence_report_agent.yaml`

## Exemplos de uso

### Execucao minima

```bash
python -m src.main run --query "monitoramento ambiental costeiro"
```

Se os arquivos `config/context_100k.yaml` e `config/tracks_100k.yaml` estiverem presentes, essa execucao ja usa automaticamente o preset 100K.

### Execucao com contexto e trilhas customizadas

```bash
python -m src.main run \
  --query "monitoramento ambiental costeiro" \
  --context-file config/context.yaml \
  --tracks-file config/tracks.yaml
```

### Execucao usando explicitamente o preset 100K

```bash
python -m src.main run \
  --query "projeto 100k rio tiete jupia" \
  --context-file config/context_100k.yaml \
  --tracks-file config/tracks_100k.yaml
```

### Execucao com OpenAI obrigatoria na categorizacao

```bash
python -m src.main run \
  --query "monitoramento ambiental costeiro" \
  --llm-mode openai \
  --llm-model gpt-4.1-nano
```

### Exportacao de catalogo

O comando `export` continua disponivel em [src/main.py](src/main.py), mas ele espera um JSON compativel com a estrutura antiga de catalogo, com `datasets` na raiz.

No fluxo principal atual, voce normalmente **nao precisa** usar esse comando, porque a pipeline ja gera:

- `data/runs/perplexity-intel-*/reports/sources.csv`
- `data/runs/perplexity-intel-*/reports/datasets.csv`

## Dependencias principais

- `pydantic`
- `httpx`
- `PyYAML`
- `python-dotenv`
- `openai`

## Resumo pratico

Se voce quiser lembrar rapidamente onde mexer:

- **mudar parametros de execucao**: [src/main.py](src/main.py)
- **mudar defaults do fluxo**: [src/pipelines/perplexity_intelligence_pipeline.py](src/pipelines/perplexity_intelligence_pipeline.py)
- **mudar estrutura valida de contexto/trilhas**: [src/schemas/records.py](src/schemas/records.py)
- **mudar validacao simples de query/limit**: [src/schemas/settings.py](src/schemas/settings.py)
- **mudar chave Perplexity**: `.env` com `PERPLEXITY_API_KEY`
- **mudar autenticacao LLM**: `.env` com `OPENAI_API_KEY`
- **mudar orientacao semantica dos agentes**: `prompts/*.yaml`
