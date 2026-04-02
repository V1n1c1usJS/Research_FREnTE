---
name: api-search-handoff
description: Use when the task is to run the general API-based discovery round without Firecrawl, verify the run completed correctly, and prepare a clean handoff package for the portal data collector.
---

# API Search Handoff

Use this skill when the repository needs an agent to run the main discovery round, confirm that the run finished correctly, and convert the ranked output into a collection-ready handoff for the Harvester.

## Canonical command path

The main discovery round in this repository is:

- `python -m src.main run`
- or `python -m src.main perplexity-intel`

For this skill, default to:

- no Firecrawl
- `--skip-collection-guides`

## Inputs to establish

- `query`
- `context_file`
- `tracks_file`
- `max_searches`
- `limit`
- `track_limit` when needed
- `perplexity_max_results` when needed
- confirmation of whether zero-result runs should be treated as failure or just reported

If a run already exists and the user wants to reuse it, establish:

- `run_dir`
- whether the handoff should be rebuilt from the existing run

## Workflow

1. Run the discovery round.
Use the API-first pipeline and explicitly skip collection guides.

2. Verify completion.
Read `manifest.json` and confirm the core artifacts exist:
- `processing/03-ranked-datasets.json`
- `reports/sources.csv`
- `reports/datasets.csv`

3. Check whether the run is usable.
At minimum, inspect:
- `filtered_source_count`
- `enriched_dataset_count`
- `ranked_dataset_count`
- track coverage or error counts when available

4. Build the Harvester handoff.
Use `scripts/build_harvester_handoff.py` to generate:
- `processing/04-harvester-handoff.json`
- `reports/harvester_targets.csv`

5. Summarize the handoff.
Report:
- run id
- ranked dataset count
- how many targets are `ready`
- how many need review
- obvious blockers such as login risk, unknown access type, or missing URLs

6. Hand off to Harvester.
If direct agent-to-agent integration is available, pass the generated handoff package.
If not, provide the exact output paths and a concise payload summary to the chat principal for forwarding.

## Harvester handoff shape

The handoff should expose, at minimum:

- `rank`
- `source_name`
- `source_slug`
- `dataset_name`
- `start_url`
- `source_domain`
- `track_origin`
- `track_priority`
- `data_format`
- `access_type`
- `temporal_coverage`
- `spatial_coverage`
- `key_parameters`
- `needs_review`
- `collection_method_hint`
- `handoff_status`

## Completion policy

Treat the run as incomplete or blocked when:
- `manifest.json` is missing
- `03-ranked-datasets.json` is missing
- the run crashes before the report artifacts exist
- all sessions fail
- the ranked output is empty when the user expected discoverable sources

In those cases:
- do not fabricate a handoff
- report the failure cleanly
- ask the chat principal for help

## What not to do

- Do not scrape the sources yourself.
- Do not enrich the sources with browser-only assumptions.
- Do not mix run validation with EDA work.
- Do not silently pass unusable targets to the Harvester.
- Do not enable Firecrawl by default for this flow.

Read `references/run-contract.md` for the run-completion checklist.
Read `references/harvester-handoff-contract.md` for the expected output package.
Use `scripts/build_harvester_handoff.py` for deterministic handoff generation.
