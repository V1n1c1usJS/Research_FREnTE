# AGENTS.md

## 1) Objetivo do projeto
Este repositório implementa um pipeline multiagente para **descoberta, avaliação e documentação de bases de dados ambientais**.

O trabalho está alinhado ao **projeto 100K**, com foco em identificar fontes úteis para estudar impactos humanos em sistemas aquáticos.

Área de interesse prioritária:
- corredor entre **São Paulo e Três Lagoas**;
- foco no **Rio Tietê**;
- conexão com o **Reservatório de Jupiá**.

---

## 2) Arquitetura planejada
Agentes planejados (modulares e evolutivos):

1. **ResearchScoutAgent** (pesquisa aberta na web via conector abstrato)
2. **QueryExpansionAgent**
3. **DatasetDiscoveryAgent**
4. **NormalizationAgent**
5. **RelevanceAgent**
6. **AccessAgent**
7. **ExtractionPlanAgent**
8. **ReportAgent**
9. **OrchestratorAgent**

---

## 3) Regras de desenvolvimento
- Sempre preferir mudanças pequenas, incrementais e rastreáveis.
- Manter JSONs intermediários entre etapas do pipeline.
- Validar schemas em cada etapa antes de avançar.
- Não inventar metadados não verificados.
- Preservar URLs, citações e origem das informações coletadas.
- Priorizar fontes oficiais, institucionais e acadêmicas.
- Manter separação clara entre descoberta, normalização, avaliação e relatório.

---

## 4) Regras de implementação
- Usar **Pydantic** para definição e validação de schemas.
- Organizar prompts em arquivos YAML no diretório `prompts/` (`*.yaml`).
- Garantir execução por CLI (ex.: `python -m src.main`).
- Incluir testes básicos para cada etapa principal.
- Preparar e manter modo **dry-run** com mocks/stubs para integrações externas.
- Conectores externos devem implementar interface abstrata (evitar acoplamento por portal único).

---

## 5) Convenções de saída
- Catálogos de datasets em **JSON**.
- Relatórios analíticos em **Markdown**.
- Exportações tabulares em **CSV**.
- Logs de execução por etapa.
- Uso obrigatório de timestamps e rastreabilidade entre entradas/saídas de cada estágio.

---

## 6) Próximas fases
1. Implementar conectores reais de busca web e scraping controlado.
2. Integrar descoberta web com expansão avançada de consultas.
3. Evoluir scoring de relevância e qualidade dos relatórios.

## 7) Estado atual de conectores de pesquisa web
- Interface base disponível em `src/connectors/web_research.py` (`WebResearchConnector`).
- Modo mock obrigatório para dry-run (`MockWebResearchConnector`).
- Conector real inicial desacoplado (`DuckDuckGoWebResearchConnector`), com timeout e fallback para mock no `ResearchScoutAgent`.
- Persistir evidências de execução (`web_research_meta`) nos artefatos do run para auditoria.


## 8) Formatos de comunicação
- Comunicação entre agentes e artefatos intermediários: **JSON**.
- Relatório final para humanos: **Markdown**.
- System prompts dos agentes: **YAML** em `prompts/`.
