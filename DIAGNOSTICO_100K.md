# Diagnóstico e Recomendações — Research_FREnTE × Projeto 100K

## Resumo executivo

A arquitetura do pipeline está sólida (11 etapas, JSONs intermediários, schemas Pydantic,
separação clara entre coleta e interpretação). O problema não é estrutural — é de
**configuração de entrada**. Os defaults internos são genéricos demais para o 100K.

Este documento mapeia 3 gaps críticos, 2 gaps parciais e 6 melhorias incrementais.

---

## GAP 1 (CRÍTICO): Contexto mestre genérico

### Situação atual
- `_build_master_context()` gera `geographic_scope: []` (vazio)
- `thematic_axes`: lista genérica ambiental
- `preferred_sources`: lista genérica sem URLs
- O `RelevanceAgent` depende de `geographic_scope` e `thematic_axes` para pontuar

### Impacto
Sem geographic_scope, o RelevanceAgent não consegue priorizar fontes da bacia do Tietê.
Sem thematic_axes específicos, todas as fontes recebem scores similares.
O pipeline coleta dados, mas não sabe *o que é relevante* para o 100K.

### Solução
Usar `config/context_100k.yaml` (entregue junto a este documento).
Contém: bounding box, 4 zonas funcionais, 6 UGRHIs, 15 eixos temáticos em 4 níveis,
19 fontes com URLs diretas, 7 tipos de output esperado, 6 exclusões e 9 notas operacionais.

### Comando
```bash
python -m src.main run \
  --query "impacto antropico materia organica reservatorios tiete" \
  --context-file config/context_100k.yaml \
  --tracks-file config/tracks_100k.yaml
```

---

## GAP 2 (CRÍTICO): Trilhas desconectadas do domínio

### Situação atual
5 trilhas default em `DEFAULT_RESEARCH_TRACKS`:
  1. official_data_portals
  2. monitoring_and_measurements
  3. pressure_and_drivers
  4. institutional_reports
  5. academic_knowledge

Essas trilhas são organizadas por *tipo de fonte*, não por *nível temático*.
Resultado: as buscas no Perplexity são genéricas e não mencionam ANA, CETESB,
MapBiomas, SNIS ou nenhuma fonte específica do domínio.

### Impacto
O Perplexity retorna resultados amplos demais. O SourceValidationAgent e o
DatasetDiscoveryAgent recebem material diluído. O consolidado final tem baixa
especificidade para o 100K.

### Solução
Usar `config/tracks_100k.yaml` (entregue junto a este documento).
Contém 12 trilhas organizadas pelos 4 níveis da knowledge base:
  - Nível 1 (macro): 3 trilhas — bacia/relevo, uso do solo, clima/hidrologia
  - Nível 2 (meso): 3 trilhas — saneamento, desmatamento/fogo, agro/resíduos/APP
  - Nível 3 (ponte): 3 trilhas — qualidade água, operação, batimetria
  - Nível 4 (micro): 3 trilhas — MOD/CDOM, sensoriamento remoto, tendências

Cada trilha traz:
  - `research_question` com escopo geográfico explícito
  - `task_prompt` com nomes de fontes, URLs-alvo e parâmetros específicos
  - `priority` alinhada à ordem de coleta do knowledge base

### Uso com --max-searches
```bash
# Execução completa (12 trilhas)
python -m src.main run --query "..." --tracks-file config/tracks_100k.yaml --max-searches 12

# Execução econômica (só high priority = 4 trilhas)
python -m src.main run --query "..." --tracks-file config/tracks_100k.yaml --max-searches 4
```

---

## GAP 3 (CRÍTICO): Keywords de busca ausentes nos prompts

### Situação atual
Os task_prompts das trilhas default não incluem palavras-chave específicas.
O Perplexity recebe perguntas genéricas como "Quais fontes trazem séries históricas
e monitoramento recorrente?" sem mencionar CETESB, QUALAR, HidroWeb, MapBiomas, etc.

### Impacto
A qualidade da coleta depende da capacidade do Perplexity de inferir o domínio.
Sem keywords, ele pode retornar fontes irrelevantes ou de outros países.

### Solução (já implementada nos tracks_100k.yaml)
Cada trilha agora inclui no task_prompt:
  - Nomes de fontes: "CETESB QUALAR", "ANA HidroWeb", "MapBiomas coleção 9"
  - URLs-alvo: "qualar.cetesb.sp.gov.br", "snirh.gov.br/hidroweb"
  - Parâmetros específicos: "IQA", "IET", "SUVA254", "IN046"
  - Queries de busca: "dissolved organic matter Tietê", "focos calor São Paulo INPE"

---

## GAP 4 (PARCIAL): RelevanceAgent sem lógica causal

### Situação atual
O RelevanceAgent pontua com base em `geographic_scope` e `thematic_axes`,
mas não tem noção de que a Zona A (RMSP) tem peso causal maior que a Zona D (Jupiá)
para entender a *origem* da carga orgânica.

### Solução sugerida (requer mudança em código)
Adicionar ao schema `PerplexityResearchContextRecord` um campo opcional:

```python
# src/schemas/records.py
zone_weights: dict[str, float] = Field(
    default_factory=dict,
    description="Peso relativo de cada zona geográfica no scoring de relevância"
)
```

Exemplo de uso no context_100k.yaml:
```yaml
zone_weights:
  Zona A - RMSP: 1.0
  Zona B - Medio Tiete: 0.8
  Zona C - Baixo Tiete: 0.6
  Zona D - Jupia: 0.7  # receptor final, peso alto apesar de pressão baixa
```

E no `RelevanceAgent`, usar zone_weights para ponderar o score quando uma fonte
é associada a uma zona específica.

**Prioridade: média.** Pode ser feito depois que o contexto e trilhas estiverem rodando.

---

## GAP 5 (PARCIAL): Validação cruzada não implementada

### Situação atual
O `SourceValidationAgent` valida consistência interna (URLs, snippets, metadata).
Não cruza dados entre fontes para verificar coerência.

### Onde a knowledge base exige cruzamento
O documento 100k_knowledge_base.md especifica 4 validações cruzadas:
  1. Dados de esgoto (SNIS) × DBO medida (CETESB)
  2. Desmatamento (INPE/MapBiomas) × turbidez/sólidos (CETESB)
  3. Clorofila-a in situ (CETESB) × clorofila-a por satélite (Sentinel/Landsat)
  4. Uso do solo (MapBiomas) × COT nos reservatórios

### Solução sugerida (requer novo agente ou extensão)
Criar um `CrossValidationAgent` ou estender o `SourceValidationAgent` para:
  - Receber pares de datasets descobertos
  - Verificar se cobrem a mesma região e período
  - Sinalizar quando um par de validação está incompleto (ex.: tem SNIS mas falta CETESB)

**Prioridade: baixa.** Isso é otimização de qualidade, não bloqueio funcional.

---

## MELHORIAS INCREMENTAIS (não são gaps, são otimizações)

### M1: Aumentar --limit default para 30-40
O pipeline usa `--limit 20` por default. Com 12 trilhas especializadas, cada uma pode
retornar 5-10 fontes relevantes. 20 é pouco — fontes serão cortadas prematuramente.
Sugestão: `--limit 40` para a execução do 100K.

### M2: Adicionar campo `level` ao schema de trilhas
O `PerplexityResearchTrackRecord` não tem um campo para indicar a qual nível
hierárquico a trilha pertence (1-macro, 2-meso, 3-ponte, 4-micro).
Adicionar isso permitiria ao RelevanceAgent e ao ReportAgent agrupar
resultados por nível automaticamente.

```python
# src/schemas/records.py — adicionar:
hierarchy_level: Literal["macro", "meso", "bridge", "micro"] = Field(
    default="macro",
    description="Nível hierárquico da trilha na arquitetura de dados"
)
```

### M3: Flag --dry-run para validar config antes de rodar
Antes de gastar créditos no Perplexity, rodar:
```bash
python -m src.main run --query "..." --context-file config/context_100k.yaml --dry-run
```
Que apenas valida os schemas, mostra o plano de busca e para.
Evita descobrir erros no YAML depois de 12 buscas.

### M4: Exportar knowledge base como JSON para ingestão direta
O 100k_knowledge_base.md é legível por humanos mas não por agentes.
Criar uma versão JSON estruturada que possa ser carregada como
`--knowledge-file config/kb_100k.json` e injetada nos prompts dos agentes.

### M5: Sinalizar formato de dado no DatasetDiscoveryAgent
Muitas fontes do 100K entregam dados em PDF (relatórios CETESB, fichas técnicas).
O DatasetDiscoveryAgent deveria ter um campo `data_format` nos candidatos:
  - "structured" → CSV, XLSX, Shapefile, GeoTIFF, API (pronto para uso)
  - "semi-structured" → tabelas em PDF, HTML scraping necessário
  - "unstructured" → texto corrido, precisa de NLP/OCR

Isso ajuda a priorizar datasets prontos para análise vs. os que precisam de ETL.

### M6: Cache de sessões Perplexity por trilha
Dado que as 12 trilhas são estáveis e a coleta custa tempo (~120s cada),
implementar cache: se uma trilha já foi executada nas últimas 72h, reutilizar
o JSON da sessão anterior em vez de rodar novamente.
Isso permite re-execuções parciais sem custo repetido.

---

## MATRIZ DE PRIORIDADE

| Item    | Tipo     | Esforço   | Impacto   | Prioridade |
|---------|----------|-----------|-----------|------------|
| GAP 1   | Config   | Pronto    | Altíssimo | Imediato   |
| GAP 2   | Config   | Pronto    | Altíssimo | Imediato   |
| GAP 3   | Config   | Pronto    | Alto      | Imediato   |
| GAP 4   | Código   | Médio     | Médio     | Sprint 2   |
| GAP 5   | Código   | Alto      | Médio     | Sprint 3   |
| M1      | Flag CLI | Trivial   | Médio     | Imediato   |
| M2      | Schema   | Baixo     | Médio     | Sprint 2   |
| M3      | CLI      | Baixo     | Alto      | Sprint 2   |
| M4      | Formato  | Médio     | Alto      | Sprint 2   |
| M5      | Schema   | Baixo     | Médio     | Sprint 3   |
| M6      | Infra    | Médio     | Médio     | Sprint 3   |

---

## COMO RODAR AGORA

Os 3 gaps críticos são resolvidos **sem nenhuma mudança de código** — apenas com os
dois arquivos de configuração entregues.

```bash
# 1. Copiar os arquivos para o repositório
cp config/context_100k.yaml <repo>/config/
cp config/tracks_100k.yaml <repo>/config/

# 2. Executar com configuração 100K
python -m src.main run \
  --query "impacto antropico materia organica reservatorios cascata tiete sao paulo tres lagoas" \
  --context-file config/context_100k.yaml \
  --tracks-file config/tracks_100k.yaml \
  --max-searches 12 \
  --limit 40 \
  --llm-mode auto

# 3. Verificar artefatos gerados
ls data/initializations/perplexity-intel-*/
# Conferir: 00_master-context.json deve conter geographic_scope preenchido
# Conferir: 01_search-plan.json deve ter 12 trilhas com task_prompts detalhados
```
