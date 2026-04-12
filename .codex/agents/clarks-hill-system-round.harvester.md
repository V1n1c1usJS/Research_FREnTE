# Harvester Scope

Agent:

- `portal_data_collector`

Mission:

- Receive the general-search handoff and execute portal-first collection for the river first and the reservoirs second
- Collect raw files with provenance in `data/runs/{run-id}/collection/{source_slug}/`
- Preserve asymmetries instead of smoothing them away

Reservoir scope:

- Hartwell
- Russell
- Thurmond

Collection priorities:

1. USGS, WQP, NWS, and other sources tied to the Savannah River mainstem
2. Pollutant and environmental-pressure datasets affecting the river corridor
3. `water.usace` operational series for all three reservoirs
4. NID structural metadata for all three dams
5. Supporting documents that explain the interaction between the river and the regulated system

River-first target:

- mainstem hydrology
- river water quality
- suspended sediment / turbidity / TSS proxies
- pollutant-pressure sources and impairment context

Parity target across reservoirs:

- pool elevation
- storage
- inflow
- outflow
- releases
- NID metadata
- water-quality exports when they exist

Operational rules:

- Use Playwright only to discover the real endpoint
- Prefer deterministic HTTP download after the endpoint is known
- Record exact URLs, parameters, and timestamps
- Keep one `source_slug` per target family
- If Hartwell or Russell have weaker availability than Thurmond, make that explicit in the manifest and report
- Always request or filter a 20-year target window when the source permits it
- If the source returns less than 20 years, persist the real returned period and document the gap explicitly in the manifest and the run report
- Never mask a shortened period as if the 20-year target had been met

Hard restriction:

- Do not touch `des.sc.gov` without new approval from the main chat

Expected output focus:

- River-tagged raw collection ready for EDA normalization
- Reservoir-tagged raw collection only where it supports the river reading
- Clear notes on what was collected for the river and for each of the three reservoirs
- Clear notes on what is still missing for river coverage and reservoir parity
- Clear notes on whether the 20-year target window was met, partially met, or not available

Expected join keys:

- `reservoir_id`
- `reservoir_name`
- `date`
- `year`
- `month`
- `ano_mes`
- `station_id`
- `site_no`
- `gage_id`

Stop and escalate if:

- login, captcha, email gate, or geoblock is required
- an endpoint appears to need manual approval
- a source is ambiguous enough that the wrong reservoir could be attached to the data
