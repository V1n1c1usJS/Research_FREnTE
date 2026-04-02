# Output Layout

Use this project layout for every browser-first collection run:

```text
data/runs/{run-id}/
|-- config/
|   `-- collection-options.json
|-- collection/
|   `-- {source_slug}/
|       |-- raw files discovered or downloaded from the portal
|       `-- blocked notes when applicable
|-- processing/
|   `-- 01-collection-targets.json
|-- reports/
|   |-- {run-id}.md
|   `-- collection_targets.csv
`-- manifest.json
```

## This repository's expected downstream outputs

Declare these in the manifest when relevant. Do not create them unless the task explicitly includes normalization.

- Qualidade da agua
  - `data/staging/qualidade_agua/qualidade_agua_ponto_amostra.parquet`
  - `data/staging/qualidade_agua/pontos_monitoramento_tiete.parquet`
  - `data/analytic/reservatorio_mes/qualidade_agua_reservatorio_mes.parquet`
  - `data/analytic/reservatorio_ano/qualidade_agua_reservatorio_ano.parquet`

- Queimadas
  - `data/staging/queimadas/focos_calor_evento.parquet`
  - `data/analytic/subbacia_ano/queimadas_subbacia_ano.parquet`
  - `data/analytic/reservatorio_ano/queimadas_reservatorio_ano.parquet`

- SNIS
  - `data/staging/snis/snis_municipios_serie.parquet`
  - `data/analytic/municipio_ano/snis_municipio_ano.parquet`
  - `data/analytic/reservatorio_ano/snis_reservatorio_ano.parquet`

- Residuos
  - `data/staging/residuos/residuos_municipio_ano.parquet`
  - `data/analytic/municipio_ano/residuos_municipio_ano.parquet`
  - `data/analytic/reservatorio_ano/residuos_reservatorio_ano.parquet`

## Join keys to preserve

- `id_reservatorio`
- `ano_mes`
- `ano`
- `cod_ibge`
- `id_subbacia`
- `cod_ponto`
