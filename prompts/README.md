# Prompts de sistema (YAML)

Todos os prompts de sistema dos agentes ficam neste diretorio em YAML.

Arquivos atuais:
- `dataset_discovery_agent.yaml`
- `normalization_agent.yaml`
- `relevance_agent.yaml`
- `access_agent.yaml`
- `perplexity_source_categorization_agent.yaml`
- `source_validation_agent.yaml`
- `perplexity_intelligence_report_agent.yaml`

Estrutura YAML padrao esperada pelo loader:
- `agent.name`
- `agent.version`
- `agent.role`
- `objective`
- `context`
- `input`
- `output`
- `rules`
- `classification`
- `runtime`

O loader valida campos obrigatorios e monta o prompt textual consumivel pelos agentes.
