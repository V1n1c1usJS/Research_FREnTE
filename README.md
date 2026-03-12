# Research_FREnTE

Pipeline multiagente em Python para descoberta, avaliação e documentação de bases de dados ambientais, com foco em desenvolvimento orientado por **Codex**.

## Visão geral do projeto

O repositório implementa uma arquitetura modular para executar um fluxo completo de pesquisa de dados ambientais com rastreabilidade por etapa (`JSON` intermediário, relatório `Markdown` e catálogo `CSV`).

O modo atual prioriza **dry-run com mocks estruturais realistas** para validar contrato de dados, orquestração e CLI antes de integrar conectores reais.

## Objetivo científico

Apoiar o projeto **100K** na identificação e priorização de bases úteis para estudar impactos humanos em rios e reservatórios no corredor **São Paulo → Três Lagoas**, com foco no **Rio Tietê** e conexão com o **Reservatório de Jupiá**.

## Arquitetura dos agentes

Ordem atual de execução:

1. `ResearchScoutAgent` — mapeia fontes de pesquisa (mock inspirado em ANA/Hidroweb/MapBiomas/INPE/IBGE/SNIS/literatura).
2. `QueryExpansionAgent` — expande consultas e separa trilhas de descoberta de datasets vs. literatura.
3. `DatasetDiscoveryAgent` — gera registros de descoberta simulados por fonte/tipo.
4. `NormalizationAgent` — normaliza para schemas Pydantic.
5. `RelevanceAgent` — atribui score e prioridade simulados.
6. `AccessAgent` — classifica acesso/licença de forma simulada.
7. `ExtractionPlanAgent` — gera plano de extração com ordem de execução.
8. `ReportAgent` — consolida relatório técnico e catálogo final.
9. `OrchestratorAgent` — coordena etapas e persistência de artefatos.

## Estrutura de diretórios

```text
src/
  agents/        # agentes e orquestração
  schemas/       # contratos Pydantic
  pipelines/     # pipeline(s) de execução
  utils/         # IO, logging, prompts
  main.py        # CLI
prompts/         # prompts versionados por agente
data/            # artefatos intermediários por execução
reports/         # relatórios Markdown + exportações CSV
tests/           # testes automatizados
config/          # exemplos de configuração
```

## Execução via CLI

### Dry-run (recomendado para desenvolvimento)

```bash
python -m src.main dry-run --query "impactos humanos no Rio Tietê" --limit 7
```

### Pipeline (modo `run`, ainda mock)

```bash
python -m src.main run --query "qualidade da água" --limit 7
```

### Exportar resultados

```bash
python -m src.main export \
  --catalog data/runs/<run_id>/catalog.json \
  --output reports/<run_id>.csv
```

## Como editar prompts

- Cada agente possui um arquivo em `prompts/*.txt`.
- Edite o prompt do agente alvo mantendo:
  - foco geográfico (São Paulo → Três Lagoas / Tietê / Jupiá),
  - proibição de invenção de dados,
  - exigência de saída estruturada.
- Carregamento centralizado em `src/utils/prompts.py` (`load_prompt`).

## Como adicionar novos conectores (futuro)

1. Criar módulo em `src/connectors/` (ex.: `ana_connector.py`).
2. Definir schema de entrada/saída em `src/schemas/`.
3. Integrar no agente apropriado (`ResearchScout`, `DatasetDiscovery` ou `Access`) mantendo fallback dry-run.
4. Preservar rastreabilidade (`evidence_origin`, URLs, timestamps).
5. Adicionar testes unitários/integrados cobrindo modo mock e modo real.

## Como interpretar artefatos gerados

### `data/runs/<run_id>/`

- `01_*.json ... 08_*.json`: saída de cada etapa.
- `catalog.json`: catálogo consolidado de datasets/sources.
- `run_metadata.json`: metadados da execução (status, timestamps, arquivos).

### `reports/`

- `<run_id>.md`: relatório técnico consolidado.
- `<run_id>.csv`: exportação tabular do catálogo para inspeção externa.

## Limitações atuais do modo mock

- Não há chamadas a APIs reais nesta fase.
- Scores, prioridades e classificações de acesso são simulados.
- URLs/fontes são usadas como inspiração estrutural, não como evidência de consulta em tempo real.

## Roadmap curto

1. Introduzir conectores reais (com feature flags) mantendo dry-run estável.
2. Evoluir scoring com critérios explícitos por domínio e validação estatística.
3. Enriquecer relatório com seções comparativas e matriz de lacunas de dados.
