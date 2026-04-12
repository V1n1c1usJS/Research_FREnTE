# Runner Scope

Agent:

- `rodada_api_handoff`

Mission:

- Run the general discovery round for the Savannah system with a river-first scope
- Prepare a clean collection handoff for the Harvester
- Stop before portal scraping

Reservoir scope:

- Hartwell
- Russell
- Thurmond

What to search for:

- Mainstem Savannah River monitoring across the cascade
- USGS gauges above, between, and below Hartwell, Russell, and Thurmond
- Flow and level context near Augusta and below the cascade
- River-reach water-quality export endpoints
- Suspended sediment, suspended solids, turbidity, and related river-signal datasets
- Tributary context only when it materially explains the mainstem signal
- Reservoir operations, NID records, and NWS products only as supporting annexes to interpret the river signal

Priority rules:

1. Prefer sources that provide equivalent metrics across mainstem river reaches and can be crossed with reservoir operations
2. Prefer official and queryable sources over PDFs
3. Prefer sources with historical daily or sub-daily coverage
4. Prefer sources that expose stable URLs or APIs

Temporal rule:

- Always search for a 20-year historical window when the source allows it
- Include the source's known or expected period of record when available
- Do not narrow the ask just because the first result snippet shows a shorter period
- If early inspection suggests or confirms less than 20 years, pass the actual returned coverage in the handoff as a documented limitation

Required handoff fields to Harvester:

- `source_name`
- `dataset_name`
- `source_slug`
- `start_url`
- `river_scope`
- `data_format`
- `access_type`
- `collection_method_hint`
- `priority`
- `notes_on_asymmetry`
- `target_window_years`
- `expected_period_start`
- `expected_period_end`

Do not:

- Do not scrape dynamic portals yourself
- Do not generate EDA outputs
- Do not build the HTML report

Completion condition:

- `04-harvester-handoff.json` is present and explicitly organized by river reach, supporting reservoir, and source family
