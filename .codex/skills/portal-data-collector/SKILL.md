---
name: portal-data-collector
description: Use when the task requires entering a web portal, discovering the real download links or hidden API endpoints with Playwright, scraping raw files, and organizing outputs under data/runs with provenance and reservoir-EDA-friendly join keys.
---

# Portal Data Collector

Use this skill for browser-first collection work where the UI hides the real file URL or API.

## What this skill does

- Opens and inspects web portals with Playwright or browser tooling.
- Reconstructs the real collection path behind buttons, forms, filters, dynamic tables, and embedded viewers.
- Switches to direct HTTP download once the real endpoint is known.
- Saves raw artifacts and manifests in the project run structure.

## Inputs you should establish first

- `source_name`: human label for the source
- `source_slug`: filesystem-safe folder name
- `dataset_name`
- `year_start` / `year_end` when temporal filtering matters
- `bbox` or geographic filter when the portal supports it
- expected target grain for later EDA use, such as `reservatorio_mes`, `reservatorio_ano`, `municipio_ano`, or `subbacia_ano`

If the user did not provide all of them, infer the minimum safe set and record the assumption in the manifest or report.

## Workflow

1. Create the run skeleton first.
Use the project layout in `references/output-layout.md`.
If you are in PowerShell, prefer `scripts/bootstrap_run.ps1`.

2. Inspect the portal in the browser.
Use Playwright or browser tools to:
- open the page
- inspect dynamic UI state
- reveal hidden links
- verify whether login, email gates, or tokenized downloads exist
- inspect network behavior when buttons trigger downloads or API requests

3. Discover the real data source.
Look for:
- direct file links such as CSV, XLSX, ZIP, PDF
- WFS/WMS/GeoServer endpoints
- API calls made after applying filters
- DSpace or repository bitstream URLs
- paginated year pages that expose attachment links

4. Prefer deterministic download after discovery.
Once the real URL or endpoint is known, download by HTTP rather than relying on browser download state. Keep the browser for discovery and validation.

5. Store raw outputs in the run folder.
Save every file under:
- `data/runs/{run-id}/collection/{source_slug}/`

Also save:
- `config/collection-options.json`
- `processing/01-collection-targets.json`
- `manifest.json`
- `reports/{run-id}.md`
- `reports/collection_targets.csv`

6. Preserve provenance.
Record:
- exact URLs used
- collection method such as `wfs`, `html_discovery`, `direct_download`, `portal_login`
- collection status such as `collected`, `partial`, `blocked`, `error`
- blockers and notes

7. Prepare for downstream EDA without fabricating derived data.
Do not write fake staging or analytic tables. Instead, declare intended outputs and join keys in the manifest.

## Blocked portal policy

If a portal requires login, CAPTCHA, registration, email approval, or other manual gate:

- do not try to bypass it
- save a note in the raw collection folder
- mark the target as `blocked`
- include the blocker and the portal URL in the manifest

## Output rules for this repository

- Raw downloads always go to `data/runs/{run-id}/collection/...`
- Do not drop raw files into `data/staging` or `data/analytic`
- For reservoir presentation work, preserve or declare the intended keys:
  - `id_reservatorio`
  - `ano_mes`
  - `ano`
  - `cod_ibge`
  - `id_subbacia`
  - `cod_ponto`

## When to keep using the browser

Stay in the browser when:
- the page is highly dynamic
- a filter changes the request payload
- the UI reveals a hidden endpoint only after interaction
- you need screenshots, console evidence, or network traces

Switch to HTTP download when:
- the final URL is stable
- the endpoint is directly callable
- the artifact is a normal file response

## What not to do

- Do not invent metadata that the portal did not expose.
- Do not merge raw and cleaned layers.
- Do not silently drop failed years or blocked pages; record them.
- Do not treat the visible portal URL as the final artifact URL if a deeper endpoint exists.

Read `references/output-layout.md` when you need the exact run and EDA storage conventions.
Use `scripts/bootstrap_run.ps1` when you want deterministic scaffolding for the run folder.
