# Handoff Contract for Clarks Hill EDA

Este EDA entra em acao somente apos o handoff consolidado do chat principal.

## Minimo obrigatorio

Horizonte analitico alvo:

- `20 anos` para as series temporais do sistema
- quando a disponibilidade real ficar abaixo disso, o handoff deve explicitar a defasagem por `reservatorio`, `fonte` e `variavel`
- essa defasagem deve ser preservada pelo EDA em README, figuras e `report_context`

Prioridades obrigatorias da proxima coleta de lacunas:

- water quality do eixo principal do rio Savannah antes de expandir anexos reservatorio-centricos
- poluentes, impairments, dischargers e demais pressoes ambientais que expliquem o comportamento do rio
- gauges adicionais do `mainstem`, inclusive acima, entre e abaixo da cascata quando existirem
- series operacionais longas de Hartwell, Russell e Thurmond apenas como suporte explicativo ao rio

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
- `coverage_years`
- `status`

### 3. Schema minimo ou amostra de colunas

Para cada dataset:

- chave temporal
- chave espacial ou identificador de estacao
- colunas numericas principais
- unidade de medida quando aplicavel
- variaveis analiticas que contam para o horizonte alvo de 20 anos

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

### 5. Matriz de cobertura temporal

O handoff deve trazer, quando possivel, uma matriz simples com:

- `reservoir`
- `source_name`
- `variable`
- `period_start`
- `period_end`
- `coverage_years`
- `target_years`
- `coverage_gap_years`
- `coverage_status`

## Blocos de dados esperados

Nem todos sao obrigatorios na primeira rodada, mas este e o contrato-alvo:

### Sinal do rio e camada de pressoes

Para Savannah / Clarks Hill, o handoff deve deixar claro o que pertence ao:

- `river_core`
- `pressure_core`
- `reservoir_annex`

Sempre que houver dados reais, a camada `pressure_core` deve tentar materializar:

- poluentes ou grupos de parametros no rio principal
- proxies de sedimento ou turbidez
- impairments, dischargers, TMDLs, wastewater ou outras fontes de pressao
- contexto de uso do solo, paisagem, bacia ou restauracao que ajude a explicar o sinal do rio

Se essa camada vier parcial, o handoff precisa marcar isso explicitamente; o HTML nao deve esconder a lacuna.

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
- `gage_id`
- `river_segment`

### Qualidade da agua

Exemplos:

- `site_id`
- `sample_date`
- `parameter_code` ou `characteristic_name`
- `result_value`
- `result_unit`
- `latitude`
- `longitude`
- `characteristic_group`
- `river_reach_id`

### Poluentes e pressoes ambientais

Exemplos:

- `river_reach_id`
- `source_name`
- `pressure_type`
- `pollutant_name`
- `facility_or_program`
- `latitude`
- `longitude`
- `period_start`
- `period_end`

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
- indicacao clara de cobertura temporal frente ao alvo de 20 anos
- indicacao de qual dataset e canonico quando houver duplicidade
- classificacao do dataset como `river_core`, `pressure_core` ou `reservoir_annex` quando ele entrar na narrativa principal

Sem esses itens, o EDA nao deve avancar para staging ou analytic.
