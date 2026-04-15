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

### Savannah River / Clarks Hill system

- River hydrology
  - `data/staging/clarks_hill/usgs_river_daily_long.csv`
  - `data/staging/clarks_hill/river_monthly_behavior.csv`
  - `data/staging/clarks_hill/river_annual_anomalies.csv`
  - `data/staging/clarks_hill/river_monthly_climatology.csv`

- River water quality
  - `data/staging/clarks_hill/river_quality_flow_correlations.csv`
  - `data/staging/clarks_hill/river_reservoir_bridge.csv`
  - `data/staging/clarks_hill/wqp_river_parameter_coverage.csv`
  - `data/staging/clarks_hill/wqp_river_yearly_counts.csv`

- Environmental pressure and pollutants
  - `data/staging/clarks_hill/npdes_dischargers.csv`         — EPA ECHO point-source dischargers in Savannah watershed
  - `data/staging/clarks_hill/tmdl_sediment.csv`             — EPD Georgia Sediment TMDL load estimates by sub-basin
  - `data/staging/clarks_hill/tmdl_bacteria.csv`             — EPD Georgia Bacteria TMDL impairment context
  - `data/staging/clarks_hill/do_restoration_context.csv`    — Savannah Harbor DO restoration plan parameters
  - `data/staging/clarks_hill/savannah_main_treated_water_long.csv`  — City of Savannah drinking-water compliance

- Reservoir operations
  - `data/staging/clarks_hill/reservoir_operations_monthly.csv`
  - `data/staging/clarks_hill/reservoir_operations_summary.csv`
  - `data/staging/clarks_hill/usace_system_snapshot.csv`
  - `data/staging/clarks_hill/nid_system_summary.csv`

- Sediment
  - `data/staging/clarks_hill/sediment_master_data.csv`
  - `data/staging/clarks_hill/sediment_depositional_scores.csv`
  - `data/staging/clarks_hill/sediment_pairwise_relations.csv`

## Join keys to preserve

- `station_id`
- `site_no`
- `gage_id`
- `river_reach_id`
- `river_segment`
- `reservoir_id`
- `reservoir_name`
- `date`
- `year`
- `month`
- `ano_mes`
