# Tiete Pattern

Use `EDA/operacao_reservatorio/` as the canonical decomposition for new contextual EDA work.

## Canonical file roles

- `README.md`
  - explains the analytical objective
  - lists the expected inputs, keys, and outputs

- `generate_figures.py`
  - loads the prepared tables
  - applies the plotting style
  - saves stable PNG outputs under `figures/`

- `process_pressoes_ambientais.py`
  - ingests multiple contextual sources
  - normalizes and aggregates them
  - writes `data/staging/` and `data/analytic/` outputs
  - generates pressure-oriented figures when needed

- `generate_presentation.py`
  - assembles the final HTML or figure narrative layer
  - keeps the project visual pattern stable

## What should be copied

- the separation between data preparation, figure generation, and presentation assembly
- stable file naming
- explicit `Path` handling
- high-resolution PNG output
- narrative framing for each figure

## What should adapt to the new study

- variables and metrics
- join keys
- time grain
- spatial grain
- the order of the figures
- the analytical bridge to the scientific question

## Suggested sequence for non-Tiete studies

1. Build or validate the harmonized tables in `data/staging/`.
2. Build EDA-ready tables in `data/analytic/`.
3. Implement `generate_figures.py`.
4. Export figures to `EDA/{slug}/figures/`.
5. Build `report_context.json`.
6. Only then assemble HTML or presentation artifacts.
