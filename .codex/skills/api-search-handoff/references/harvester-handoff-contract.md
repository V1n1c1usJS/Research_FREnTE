# Harvester Handoff Contract

The handoff package should make the portal collector's work explicit and low-friction.

## Output files

- `data/runs/{run-id}/processing/04-harvester-handoff.json`
- `data/runs/{run-id}/reports/harvester_targets.csv`

## Per-target fields

- `rank`
- `source_name`
- `source_slug`
- `dataset_name`
- `title`
- `start_url`
- `source_domain`
- `track_origin`
- `track_priority`
- `track_intent`
- `data_format`
- `access_type`
- `access_notes`
- `temporal_coverage`
- `spatial_coverage`
- `key_parameters`
- `needs_review`
- `collection_method_hint`
- `handoff_status`

## Handoff status guidance

- `ready`
  - clear URL and plausible collection path

- `needs_review`
  - ambiguous access type
  - missing key metadata
  - source flagged with `needs_review`

- `blocked`
  - missing URL or obviously unusable target

## Collection method hint guidance

Suggested mapping:

- `pdf_extraction` -> `direct_download_or_pdf`
- `web_portal` -> `portal_first`
- `api` -> `api`
- `unknown` -> `manual_triage`

This package is not the final collection output. It is only the operational input for the Harvester.
