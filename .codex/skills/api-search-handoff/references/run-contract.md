# Run Contract

The discovery round is considered complete only when the run folder contains the expected core artifacts.

## Expected files

Under `data/runs/{run-id}/`:

- `manifest.json`
- `collection/raw-sessions.json`
- `processing/01-filtered-sources.json`
- `processing/02-enriched-datasets.json`
- `processing/03-ranked-datasets.json`
- `reports/{run-id}.md`
- `reports/sources.csv`
- `reports/datasets.csv`

## Minimum manifest checks

Read at least:

- `research_id`
- `filtered_source_count`
- `enriched_dataset_count`
- `ranked_dataset_count`
- `filter_meta`
- `enrich_meta`
- `rank_meta`

## Failure signals

Common signals that the run should not be handed to the Harvester yet:

- missing `manifest.json`
- missing `03-ranked-datasets.json`
- `ranked_dataset_count = 0` when the run was expected to discover sources
- all sessions failed
- report artifacts missing

## Success result

If the run passes the checks, the next step is to convert `03-ranked-datasets.json` into a Harvester handoff package.
