# Briefing: eda_reservatorio — Savannah Pressure Round

Objetivo:
- integrar os dados de pressao ambiental coletados nesta rodada ao staging existente em `data/staging/clarks_hill/`
- produzir tabelas normalizadas e atualizar o contexto analitico para as figuras de pressao

---

## Inputs esperados do Harvester

O Harvester desta rodada entregara arquivos brutos em `data/runs/{run-id}/collection/`:

| source_slug | Conteudo esperado |
|---|---|
| `epa_echo_npdes_savannah` | CSV de instalacoes NPDES com parametros de descarga |
| `epd_tmdl_sediment_savannah` | PDF do Sediment TMDL 2010 (+ eventual CSV de carga) |
| `epd_tmdl_bacteria_savannah` | PDF do Bacteria TMDL 2023 |
| `epd_do_restoration_savannah` | PDF do DO Restoration Plan |
| `clemson_wqs_savannah_2006` | CSV/XLSX ou PDF com quimica do rio 2006-2008 |
| `noaa_bathymetry_savannah` | Raster ou CSV de profundidade |

---

## Normalizacao esperada por alvo

### EPA ECHO — NPDES
Arquivo de saida: `data/staging/clarks_hill/npdes_dischargers.csv`
Colunas minimas:
- `facility_name`, `facility_type` (industrial/municipal), `latitude`, `longitude`
- `huc8`, `river_segment` (trecho mais proximo no Savannah)
- `permit_status`, `primary_sic_code`, `parameter_groups` (lista de grupos de parametros da descarga)
- `compliance_violation_flag` (1/0 se houve violacao no periodo)
- `data_year_start`, `data_year_end`

### EPD TMDLs e DO Plan — PDFs
Se o PDF vier com tabelas estruturadas extraiveis:
- `data/staging/clarks_hill/tmdl_sediment.csv` — carga por sub-bacia (ton/ano), trecho impactado, meta de reducao
- `data/staging/clarks_hill/tmdl_bacteria.csv` — trecho impactado, fonte (point/nonpoint), carga coliform
- `data/staging/clarks_hill/do_restoration_context.csv` — zona de impacto, limiar DO (mg/L), periodo critico, fonte a montante

Se o PDF nao permitir extracao estruturada:
- salvar resumo textual em `data/staging/clarks_hill/pressure_context_notes.md` com os valores-chave extraidos manualmente
- declarar no manifest que a tabela completa requer extracao manual

### Clemson WQS 2006-2008
Arquivo de saida: `data/staging/clarks_hill/wqs_clemson_2006_2008.csv`
Colunas minimas:
- `site_id`, `site_name`, `river_reach`, `latitude`, `longitude`
- `sample_date`, `year`, `month`
- colunas por parametro detectado (metais: Fe, Mn, Cu, Pb, As; nutrientes: NO3, NH4, TP; organicos: TOC; fisicos: TSS, turbidity, conductance, temp, pH, DO)

### NOAA Bathymetry
Se formato raster: salvar GeoTIFF em `data/staging/clarks_hill/bathymetry_thurmond.tif`
Se formato CSV: `data/staging/clarks_hill/bathymetry_thurmond_points.csv` com `latitude`, `longitude`, `depth_m`
Se indisponivel: registrar em manifest como blocked, sem fabricar dados

---

## Integracao com staging existente

Apos normalizacao, verificar joins possiveis com:
- `sediment_master_data.csv` — cruzar coordenadas dos cores com instalacoes NPDES proximas e com batimetria
- `river_annual_anomalies.csv` — cruzar anos anomalos com anos de violacao de compliance (ECHO)
- `savannah_main_treated_water_long.csv` — Mn na agua tratada (8-11 ppb) vs instalacoes NPDES com Mn na descarga

---

## Regras

- Nao inventar dados que o PDF nao expoe
- Se a extracao de PDF for parcial, declarar o que foi extraido e o que ficou por extrair
- Manter join keys: `year`, `month`, `river_segment`, `reservoir_name` onde aplicavel
- Nao misturar camada bruta (runs/) com camada normalizada (staging/)

## Entregavel esperado

- Arquivos CSV normalizados em `data/staging/clarks_hill/`
- `report_context_pressure.json` com resumo dos dados de pressao para uso no HTML:
  - contagem de instalacoes NPDES por tipo
  - trechos impactados por TMDL
  - anos com violacao de compliance
  - parametros de pressao disponiveis para cruzamento com sedimento
- Nota de lacunas: o que ainda nao tem dado estruturado e precisa de coleta futura
