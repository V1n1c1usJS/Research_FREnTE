# Prompts de sistema (YAML)

Todos os prompts de sistema dos agentes ficam neste diretório em **YAML**.

Arquivos atuais:
- `research_scout_agent.yaml`
- `query_expansion_agent.yaml`
- `dataset_discovery_agent.yaml`
- `normalization_agent.yaml`
- `relevance_agent.yaml`
- `access_agent.yaml`
- `extraction_plan_agent.yaml`
- `report_agent.yaml`
- `orchestrator_agent.yaml`

Estrutura YAML padrão esperada pelo loader:
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

O loader valida campos obrigatórios e monta o prompt textual consumível pela LLM.
