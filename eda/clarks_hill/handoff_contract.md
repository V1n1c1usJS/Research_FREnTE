# Handoff Contract for Clarks Hill EDA

Este EDA entra em acao somente apos o handoff consolidado do chat principal.

## Minimo obrigatorio

### 1. Manifesto de handoff

Um arquivo `json`, `yaml` ou `md` com:

- objetivo analitico resumido
- janela temporal prioritaria
- recorte espacial
- lista dos datasets entregues
- lacunas conhecidas

### 2. Inventario de arquivos

Para cada arquivo entregue:

- `path`
- `source_name`
- `dataset_name`
- `format`
- `time_grain`
- `spatial_grain`
- `period_start`
- `period_end`
- `status`

### 3. Schema minimo ou amostra de colunas

Para cada dataset:

- chave temporal
- chave espacial ou identificador de estacao
- colunas numericas principais
- unidade de medida quando aplicavel

### 4. Chaves de juncao

Pelo menos uma estrategia clara de ligacao entre datasets:

- `date`
- `year` ou `year_month`
- `site_no`
- `station_id`
- `gage_id`
- `sample_site_id`
- `reservoir_id`
- `basin_id`

Se a juncao depender de tabela auxiliar, essa tabela tambem deve vir no handoff.

## Blocos de dados esperados

Nem todos sao obrigatorios na primeira rodada, mas este e o contrato-alvo:

### Operacao e hidrologia

Exemplos de campos esperados:

- `date`
- `pool_elevation_ft`
- `storage_acft`
- `inflow_cfs`
- `outflow_cfs`
- `release_cfs`
- `station_id`

### Streamflow ou gauges

Exemplos:

- `site_no`
- `date`
- `parameter_code`
- `discharge_cfs`
- `stage_ft`

### Qualidade da agua

Exemplos:

- `site_id`
- `sample_date`
- `parameter_code` ou `characteristic_name`
- `result_value`
- `result_unit`
- `latitude`
- `longitude`

### Clima

Exemplos:

- `station_id`
- `date`
- `precip_mm`
- `tmax_c`
- `tmin_c`
- `spi` ou outro indice de seca, quando houver

### Uso do solo e bacia

Exemplos:

- `basin_id`
- `year`
- `land_cover_class`
- `area_km2`
- `pct_area`

## Itens que precisam de escalacao imediata ao chat principal

Escalar imediatamente se faltar:

- caminho real dos arquivos coletados
- qualquer chave temporal valida
- qualquer chave espacial ou de estacao
- definicao do periodo prioritario
- indicacao de qual dataset e canonico quando houver duplicidade

Sem esses itens, o EDA nao deve avancar para staging ou analytic.
