# Report Context Contract

Prefer a compact JSON payload that the HTML report layer can consume without recomputing the analytics.

## Top-level fields

- `report_title`
- `report_subtitle`
- `context_summary`
- `metrics`
- `sections`
- `figures`
- `output_path`

## Figure card shape

Each figure should preferably expose:

- `id`
- `title`
- `tag`
- `tag_color`
- `icon`
- `image_path`
- `summary`
- `interpretation`
- `highlight`

## Notes

- `image_path` should point to a file already generated under `EDA/{slug}/figures/`
- `summary` explains what the figure shows
- `interpretation` explains the analytical meaning
- `highlight` is the one-line takeaway

This payload should stay compatible with the report pattern already used by:

- `EDA/operacao_reservatorio/generate_presentation.py`
- `.codex/skills/report-html-standard/`
