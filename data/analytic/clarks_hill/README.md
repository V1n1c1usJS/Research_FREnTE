Savannah River-first analytic tables for the Clarks Hill workspace.

This folder is the consolidated consumption layer for `EDA/clarks_hill/`.

Expected outputs from `EDA/clarks_hill/process_context_sources.py`:

- `river_mainstem_layers.csv`
  - long-horizon river hydrology and river WQP coverage by entity
- `reservoir_annex_layers.csv`
  - Hartwell, Russell, and Thurmond support layers: structure, operations, and forebay WQP
- `pressure_source_inventory.csv`
  - pollutant and environmental-pressure sources already collected plus pending discovery handoff targets
- `domain_registry.csv`
  - explicit analytical contract for each domain, layer, grain, and join key
- `crosswalk_registry.csv`
  - explicit registry of which domain crossings are already valid, partial, or still pending
- `coverage_target_matrix.csv`
  - 20-year target vs returned coverage with explicit coverage gaps
- `sediment_bridge_summary.csv`
  - top depositional sites and pairwise relations used for the sediment bridge
- `collection_preflight_inventory.csv`
  - normalized view of the current `04-harvester-handoff.json` for EDA readiness

Rules:

- Savannah River remains the protagonist.
- Reservoir layers are explanatory annexes inside the river narrative.
- Every layer must belong to an explicit domain before any crossing is interpreted.
- Keep the 20-year target explicit and preserve real gaps.
- Do not promote a layer to analytic parity when coverage is snapshot-only or sparse.
