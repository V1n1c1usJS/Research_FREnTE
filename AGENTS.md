# AGENTS.md

## 1) Objetivo do projeto
Este repositorio implementa um pipeline para **descoberta, categorizacao e consolidacao de fontes e datasets ambientais** com foco em um artigo cientifico.

O trabalho segue alinhado ao **projeto 100K**, com prioridade para:
- corredor entre **Sao Paulo e Tres Lagoas**
- **Rio Tiete**
- **Reservatorio de Jupia**

---

## 2) Arquitetura atual
O fluxo principal agora e **Perplexity-first**.

Etapas do pipeline:
1. montar um **contexto mestre** da pesquisa
2. gerar **chats tematicos** especializados
3. coletar respostas e links no **Perplexity** via **Playwright CLI**
4. armazenar a coleta crua em JSON
5. categorizar fontes com o **PerplexitySourceCategorizationAgent**
6. validar consistencia e sinalizar evidencias fracas com o **SourceValidationAgent**
7. consolidar candidatos com o **DatasetDiscoveryAgent**
8. normalizar registros com o **NormalizationAgent**
9. priorizar com o **RelevanceAgent**
10. organizar acesso com o **AccessAgent**
11. gerar consolidado final com o **PerplexityIntelligenceReportAgent**

---

## 3) Regras de desenvolvimento
- Sempre preferir mudancas pequenas, incrementais e rastreaveis.
- Manter JSONs intermediarios entre etapas do pipeline.
- Validar schemas em cada etapa antes de avancar.
- Nao inventar metadados nao verificados.
- Preservar URLs, snippets, trilhas de pesquisa e origem das informacoes coletadas.
- Priorizar fontes oficiais, institucionais e academicas.
- Separar claramente:
  descoberta no Perplexity,
  categorizacao de fontes,
  validacao das fontes,
  consolidacao de datasets,
  relatorio final.

---

## 4) Regras de implementacao
- Usar **Pydantic** para definicao e validacao de schemas.
- Organizar prompts em YAML no diretorio `prompts/`.
- Garantir execucao por CLI via `python -m src.main`.
- Incluir testes para coleta, categorizacao, consolidacao e CLI.
- O conector principal de descoberta externa e o `PerplexityPlaywrightCollector`.
- A coleta deve ser armazenada antes de qualquer interpretacao posterior dos agentes.

---

## 5) Convencoes de saida
- Coleta crua, fontes categorizadas e catalogos em **JSON**
- Relatorios analiticos em **Markdown**
- Exportacoes tabulares em **CSV**
- Timestamps e rastreabilidade obrigatorios entre entradas e saidas

---

## 6) Formatos de comunicacao
- Artefatos intermediarios: **JSON**
- Relatorio final humano: **Markdown**
- Prompts dos agentes: **YAML** em `prompts/`
