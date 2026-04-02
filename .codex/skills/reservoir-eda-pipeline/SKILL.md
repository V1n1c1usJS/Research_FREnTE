---
name: reservoir-eda-pipeline
description: Use when the task is to build or update a reservoir-focused EDA workspace from incoming data, creating Python analysis scripts, report-ready figures, and structured context for the project's HTML reports.
---

# Reservoir EDA Pipeline

Use this skill when new contextual data arrives and the repository needs a reproducible EDA workspace, not just an ad hoc notebook.

## Canonical repository pattern

Treat `EDA/operacao_reservatorio/` as the main reference for structure and tone:

- `EDA/operacao_reservatorio/README.md`
- `EDA/operacao_reservatorio/generate_figures.py`
- `EDA/operacao_reservatorio/process_pressoes_ambientais.py`
- `EDA/operacao_reservatorio/generate_presentation.py`
- `EDA/operacao_reservatorio/apresentacao_reservatorios.html`

The default rule is:
- adapt from the Tiete pattern
- keep the workflow reproducible
- let the figures and narratives change according to the received data

## Inputs to establish

- `eda_slug`
- `study_title`
- `context_summary`
- `data_paths`
- `target_outputs`
- `join_keys`
- `time_grain`
- `report_destination` when HTML is expected

If some fields are missing, infer the minimum safe set and state the assumption in the EDA README or report context.

## Expected workspace shape

Prefer this layout:

```text
EDA/{slug}/
|-- README.md
|-- figures/
|-- generate_figures.py
|-- process_context_sources.py
|-- generate_presentation.py
`-- report_context.json
```

Not every file is mandatory in every run, but this is the default target.

## Workflow

1. Inspect the incoming context and data.
Determine the real analytical question, the available grains, and the keys that connect the datasets.

2. Map the layers.
Keep raw data in `data/runs/`.
Write cleaned or harmonized tables to `data/staging/`.
Write consolidated tables used by the figures to `data/analytic/`.

3. Scaffold or update the EDA workspace.
Use `scripts/bootstrap_eda_workspace.ps1` when you want deterministic scaffolding for `EDA/{slug}/`.

4. Implement the Python analysis files.
Prefer these responsibilities:
- `process_context_sources.py`: clean, merge, aggregate, and validate contextual sources
- `generate_figures.py`: produce the report-ready PNG files
- `generate_presentation.py`: assemble HTML or figure-driven presentation artifacts when requested

5. Generate report-ready figures.
Prefer:
- stable file names
- 300 dpi exports when presentation use is likely
- source notes and readable labels
- figures that explain the context, not just raw metrics

6. Prepare the report handoff.
Write a structured `report_context.json` or equivalent payload compatible with the project's HTML report flow.

7. Record gaps honestly.
If expected datasets are missing or partial, keep the scripts reproducible and document the gap instead of inventing fallback values.

## Figure design guidance

Use the Tiete EDA as the narrative model:

- start with hydrology or operations
- then show watershed or environmental pressures
- then add water quality or environmental response
- finish with the interpretation bridge to the scientific question

For sediment studies like Clarks Hill, the bridge should connect:
- hydrodynamics
- depositional energy
- fine-sediment accumulation
- water quality or eutrophication context

without replacing the lab sediment analysis itself.

## Output rules for this repository

- `data/runs/` remains raw only
- `data/staging/` stores harmonized tables
- `data/analytic/` stores EDA-ready tables
- `EDA/{slug}/figures/` stores final PNGs used by the report
- the HTML layer should consume structured context rather than re-deriving analytics inside the template

## What not to do

- Do not keep the logic only in notebooks if the workflow needs to run again.
- Do not mix raw collection with staging or analytic layers.
- Do not create generic charts without analytical framing.
- Do not assume the Tiete variables are the same as the next study; keep the structure, not the exact metrics.
- Do not generate HTML before the figure set and report context are stable.

Read `references/tiete-pattern.md` for the canonical decomposition of the Tiete EDA.
Read `references/output-contract.md` for the expected file and data outputs.
Read `references/report-context-contract.md` for the payload shape to hand off to the HTML report layer.
