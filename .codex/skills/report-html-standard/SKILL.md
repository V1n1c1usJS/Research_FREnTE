---
name: report-html-standard
description: Use when the task is to generate or update an HTML report that must keep the project's established visual pattern and only change images, metrics, sections, and narrative from provided analytical context.
---

# Report HTML Standard

Use this skill when the user wants an HTML report or presentation with stable project branding and changing analytical content.

## Canonical visual references

Treat these files as the canonical family for report styling:

- `EDA/operacao_reservatorio/apresentacao_reservatorios.html`
- `EDA/operacao_reservatorio/generate_presentation.py`
- `src/generators/html_report_generator.py`

The visual language to preserve includes:

- `Bitter` for titles and `Inter` for body text
- Tailwind-based layout
- project blues and gold accents
- white cards on light slate background
- icon + badge + title composition
- narrative blocks with:
  - what the figure shows
  - analytical interpretation
  - highlighted takeaway

## Main rule

Do not redesign the page unless the user explicitly asks for a new visual direction.

Default behavior:
- keep layout
- keep typography
- keep hierarchy
- keep card structure
- keep spacing rhythm
- replace only:
  - images
  - metrics
  - section labels
  - narratives
  - contextual metadata

## Inputs to establish

- `report_title`
- `report_subtitle`
- `context_summary`
- `sections`
- `figures`
- `metrics`
- `output_path`

If the user only gives raw analytical data, synthesize these inputs before rendering.

## Recommended content shape

For figure-driven reports, prefer each analytical card to contain:

- `id`
- `title`
- `tag`
- `tag_color`
- `icon`
- `image_path` or image source
- `summary`
- `interpretation`
- `highlight`

For dashboard-style reports, prefer:

- top-level metrics
- filters or navigation only if already part of the pattern
- one or more analytical sections
- a concise closing block with implications or next steps

## Rendering workflow

1. Read the canonical references.
Focus first on:
- `EDA/operacao_reservatorio/generate_presentation.py`
- `src/generators/html_report_generator.py`

2. Identify the closest existing pattern.
Choose one of:
- presentation-like figure narrative
- dashboard-like discovery report

3. Build or normalize the content context.
Use structured dictionaries or JSON-like payloads before touching the HTML.

4. Render by adaptation, not reinvention.
Copy the existing structure and swap content blocks.

5. Preserve missing-data grace.
If an image or metric is unavailable, keep the card and show a clean placeholder or note.

6. Write the final HTML to the requested destination.

## Editorial guidance

The tone should sound analytical, precise, and presentation-ready.

Prefer:
- short descriptive summaries
- one interpretive paragraph with analytical meaning
- one strong takeaway line

Avoid:
- raw dump of notebook text
- generic filler
- speculative conclusions unsupported by the data

## File organization

Put final outputs in:
- `reports/` for project reports
- or the exact destination requested by the user

If a report depends on multiple local figures, preserve the source file references in the script or generator that assembles the HTML.

## What not to do

- Do not introduce a new design system by default.
- Do not silently change the project's fonts or palette.
- Do not flatten the report into a generic AI-looking layout.
- Do not remove analytical interpretation from figure cards.

Read `references/visual-contract.md` for the frozen visual contract and `references/content-contract.md` for the expected report payload shape.
