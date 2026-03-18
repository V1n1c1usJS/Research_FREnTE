# Comparativo: fallback mock vs permanência em modo real

- Referência anterior (histórica): `reports/web_validation_relevance_run-69a620c5.md`.
- Nova execução controlada: `run-a21beccc`.
- Arquivo de evidências: `data/runs/run-a21beccc/01_research-scout.json`.

## Antes (com fallback para mock)

Na validação histórica, o relatório registrava que a busca em modo real terminava com **mock-fallback** quando a recuperação era ruim.

- modo final: `mock-fallback`
- falha registrada: `all_results_filtered_as_irrelevant`

## Depois (sem fallback silencioso para mock)

Na nova execução, o `ResearchScoutAgent` permaneceu em modo real mesmo com baixa recuperação:

- `requested_mode = real`
- `connector_mode_used = real`
- `retrieval_status = low_recall`
- `raw_result_count = 30`
- `kept_result_count = 10`
- `discarded_irrelevant_count = 20`

Isso confirma que o pipeline **não substituiu** resultados reais por mock.

## Evidências reais coletadas (amostra bruta)

Fontes efetivamente acessadas na web durante a execução real (extraídas do bloco `web_research_results_raw`):

- Rio de Janeiro - Wikipedia — https://en.wikipedia.org/wiki/Rio_de_Janeiro
- Rio (2011 film) - Wikipedia — https://en.wikipedia.org/wiki/Rio_(2011_film)
- Rio Salado - Online Community College — https://www.riosalado.edu/
- Rio (2011) - IMDb — https://www.imdb.com/title/tt1436562/
- Rio de Janeiro | Britannica — https://www.britannica.com/place/Rio-de-Janeiro-Brazil

## Diagnóstico curto

- Busca web real: **funcionou** (requisições HTTP e resultados brutos foram persistidos).
- Timeout/bloqueio fatal: **não houve** nesta execução.
- Qualidade dos resultados: ainda baixa para o domínio 100K (muito ruído genérico sobre “Rio”).
- Partes ainda mock no pipeline: etapas downstream continuam heurísticas/simuladas conforme arquitetura atual.
