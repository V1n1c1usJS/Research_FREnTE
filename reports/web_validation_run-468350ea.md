# Validação de busca web real (ResearchScoutAgent)

- Pipeline em modo real executado: `run-468350ea`.
- Teste controlado do `ResearchScoutAgent` executado: `run-control-1f1cf06e`.

## Resultado da busca web

- Busca web funcionou: **sim**.
- Modo solicitado: `real`.
- Modo efetivamente usado: `real`.
- Falha registrada: `nenhuma`.

## Fontes reais acessadas (amostra)

- **Título:** Rio de Janeiro - Wikipedia
  - URL: https://en.wikipedia.org/wiki/Rio_de_Janeiro
  - Tipo: web_result
  - Organização: Bing HTML
  - Datasets mencionados: []
  - Variáveis mencionadas: ['hidrologia', 'qualidade da água', 'uso da terra', 'bacia hidrográfica', 'rio tietê']
- **Título:** Cafe Rio: Mexican Grill | Online Ordering | Midvale
  - URL: https://www.caferio.com/order/midvale
  - Tipo: web_result
  - Organização: Bing HTML
  - Datasets mencionados: []
  - Variáveis mencionadas: ['hidrologia', 'qualidade da água', 'uso da terra', 'bacia hidrográfica', 'rio tietê']
- **Título:** Rio (2011) - IMDb
  - URL: https://www.imdb.com/title/tt1436562/
  - Tipo: web_result
  - Organização: Bing HTML
  - Datasets mencionados: []
  - Variáveis mencionadas: ['hidrologia', 'qualidade da água', 'uso da terra', 'bacia hidrográfica', 'rio tietê']
- **Título:** Rio Salado - Online Community College
  - URL: https://www.riosalado.edu/
  - Tipo: web_result
  - Organização: Bing HTML
  - Datasets mencionados: []
  - Variáveis mencionadas: ['hidrologia', 'qualidade da água', 'uso da terra', 'bacia hidrográfica', 'rio tietê']
- **Título:** Rio de Janeiro | History, Population, Map, Climate, &amp; Facts | Britannica
  - URL: https://www.britannica.com/place/Rio-de-Janeiro-Brazil
  - Tipo: web_result
  - Organização: Bing HTML
  - Datasets mencionados: []
  - Variáveis mencionadas: ['hidrologia', 'qualidade da água', 'uso da terra', 'bacia hidrográfica', 'rio tietê']

## Falhas de rede / timeout / bloqueio

- Não houve exceção fatal no teste controlado.
- O endpoint DuckDuckGo Instant Answer retornou baixa cobertura para este tema; o conector usou fallback de busca HTML (Bing) para obter resultados reais.
- Não houve timeout fatal na execução desta validação.

## Partes que ainda estão em mock

- `DatasetDiscoveryAgent`, `NormalizationAgent`, `RelevanceAgent`, `AccessAgent`, `ExtractionPlanAgent` e `ReportAgent` continuam operando com heurísticas/mock.
- O `MockWebResearchConnector` continua sendo o fallback oficial quando o modo real falha ou retorna vazio.