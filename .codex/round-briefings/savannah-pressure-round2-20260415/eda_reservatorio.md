# Briefing: eda_reservatorio - Savannah Pressure Round 2

Objetivo:
- integrar os artefatos da rodada complementar de pressao ao staging existente em `data/staging/clarks_hill/`
- elevar a camada de Mn / Clemson / bathymetria para um estado mais util na ponte com os sedimentos

Contexto de partida:
- a rodada `savannah-pressure-20260415` ja produziu:
  - `npdes_dischargers.csv`
  - `tmdl_sediment.csv`
  - `tmdl_bacteria.csv`
  - `do_restoration_context.csv`
  - `mn_crosscheck_summary.csv`
  - `report_context_pressure.json`
- esta rodada nao deve apagar esses outputs; deve complementar e melhorar o que ja existe

---

## Inputs esperados do Harvester

| source_slug | Conteudo esperado |
|---|---|
| `epa_echo_dmr_mn_savannah` | payload bruto DMR com Mn por instalacao / periodo |
| `clemson_wqs_savannah_2006` | PDF baixado pelo browser e, se existirem, anexos estruturados |
| `usace_bathymetry_thurmond` | raster, pontos, bundle spatial ou metadado oficial do caminho USACE |

---

## Normalizacao esperada por alvo

### 1. ECHO DMR - manganes por instalacao
Arquivo de saida principal:
- `data/staging/clarks_hill/echo_dmr_manganese_savannah.csv`

Colunas minimas:
- `npdes_id`, `facility_name`, `outfall_id`
- `huc8`, `river_segment`
- `parameter_name`, `parameter_code`
- `monitoring_year`, `monitoring_period`
- `result_value_raw`, `result_value`, `result_unit`
- `result_value_ug_l` quando a unidade permitir conversao robusta
- `limit_value`, `limit_unit`, `exceedance_flag`
- `source_url`

Arquivo agregado recomendado:
- `data/staging/clarks_hill/echo_dmr_manganese_annual_summary.csv`

Colunas minimas do agregado:
- `npdes_id`, `facility_name`, `huc8`
- `year`
- `mn_result_count`
- `mn_result_min_ug_l`, `mn_result_max_ug_l`, `mn_result_median_ug_l`
- `mn_exceedance_any_flag`

Notas:
- se a unidade nao permitir conversao segura, manter o valor bruto e declarar a lacuna
- usar `npdes_dischargers.csv` como crosswalk principal de instalacao / HUC

### 2. Clemson WQS 2006-2008
Arquivo de saida:
- `data/staging/clarks_hill/wqs_clemson_2006_2008.csv`

Regra principal:
- NAO sobrescrever este arquivo com schema vazio se o browser download falhar de novo
- so atualizar o CSV se houver dados reais extraidos do PDF ou de anexo estruturado

Colunas minimas:
- `site_id`, `site_name`, `river_reach`, `latitude`, `longitude`
- `sample_date`, `year`, `month`
- parametros detectados: `fe`, `mn`, `cu`, `pb`, `as`, `no3`, `nh4`, `tp`, `toc`, `tss`, `turbidity`, `conductance`, `temp`, `ph`, `do`

Se o PDF vier mas a extracao for parcial:
- manter o melhor CSV parcial possivel
- escrever `data/staging/clarks_hill/wqs_clemson_2006_2008_extraction_notes.md`
- declarar quais tabelas ainda exigem extracao manual

### 3. USACE Bathymetria Thurmond
Se raster publico:
- `data/staging/clarks_hill/bathymetry_thurmond_usace.tif`

Se pontos / xyz / csv:
- `data/staging/clarks_hill/bathymetry_thurmond_usace_points.csv`
  - colunas minimas: `latitude`, `longitude`, `depth_m`

Se bundle / geometry HEC-RAS sem ponto ou raster simples:
- `data/staging/clarks_hill/bathymetry_thurmond_usace_metadata.json`
  - registrar formato, conteudo e por que ainda nao virou superficie usavel

Se indisponivel:
- manter status `blocked` no manifest
- NAO fabricar dado espacial

Arquivo derivado recomendado, se houver bathymetria espacial real:
- `data/staging/clarks_hill/sediment_bathymetry_nearest.csv`
  - colunas minimas: `site`, `latitude`, `longitude`, `bathymetry_depth_m`, `distance_to_nearest_bathy_m`, `source_slug`

---

## Integracao com staging existente

Cruzes prioritarios desta rodada:

1. `echo_dmr_manganese_savannah.csv` x `npdes_dischargers.csv`
- chave principal: `npdes_id`
- objetivo: sair de compliance geral para Mn por instalacao / ano

2. `echo_dmr_manganese_annual_summary.csv` x `river_annual_anomalies.csv`
- chave: `year`
- objetivo: verificar se anos com atividade / excedencia de Mn aparecem perto de anos anomalos do rio
- deixar claro quando a comparacao for apenas anual e nao evento-a-evento

3. `echo_dmr_manganese_annual_summary.csv` x `savannah_main_treated_water_long.csv`
- foco: Mn em agua tratada (`8-11 ppb`) versus Mn em descargas DMR
- declarar unidade e dominio de comparacao; nao misturar ppb, ug/L e mg/L sem conversao clara

4. `echo_dmr_manganese_annual_summary.csv` x `sediment_master_data.csv`
- comparacao conceitual, nao causal:
  - `mn_ppm` no sedimento
  - Mn em descargas por instalacao / ano
- registrar os limites da comparacao de escala e unidade

5. `wqs_clemson_2006_2008.csv` x `mn_crosscheck_summary.csv`
- se a Clemson trouxer Mn, Fe ou outros metais relevantes, anexar essas linhas ao resumo de cross-check

6. `bathymetry_thurmond_usace.*` x `sediment_master_data.csv`
- se houver superficie espacial real, cruzar cada core com a bathymetria mais proxima

---

## Regras

- nao apagar ou degradar os CSVs uteis ja criados na rodada anterior
- atualizar `mn_crosscheck_summary.csv` apenas se a nova rodada realmente acrescentar informacao
- preservar a distincao entre:
  - dado bruto em `data/runs/`
  - dado harmonizado em `data/staging/`
- se Clemson ou USACE continuarem incompletos, registrar o melhor estado atingido sem criar placeholders enganosos
- se a bathymetria ficar apenas em caminho de contato manual, manter isso como `blocked`
- preferir atualizar `EDA/clarks_hill/report_context_pressure.json`; se precisar de payload intermediario de rodada, salvar tambem um `report_context_pressure_round2.json`

## Entregavel esperado

- novos CSVs de Mn DMR em `data/staging/clarks_hill/`
- atualizacao do `wqs_clemson_2006_2008.csv` somente se houver dado real
- bathymetria USACE materializada ou bloqueio documentado com precisao
- `report_context_pressure.json` atualizado com:
  - contagem de instalacoes com Mn DMR
  - anos com cobertura DMR de Mn
  - status Clemson via browser download
  - status bathymetria USACE
- nota curta de lacunas restantes para o HTML e para o runner principal
