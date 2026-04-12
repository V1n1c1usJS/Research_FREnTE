# Clarks Hill System Round - Agent Briefings

This package prepares the next Savannah River round with a river-first analytical core:

- Hartwell
- Russell
- Thurmond

Execution order:

1. `clarks-hill-system-round.runner.md`
2. `clarks-hill-system-round.harvester.md`
3. `clarks-hill-system-round.analyst.md`
4. `clarks-hill-system-round.narrator.md`

Shared analytical scope:

- Analytical core: mainstem Savannah River signal across the Hartwell -> Russell -> Thurmond cascade
- Environmental pressures and pollutant context are part of the analytical core, not optional annexes
- Reservoirs are supporting annexes for operations, regulation, and attribution inside the river narrative
- Final study target: sediment interpretation at Thurmond, informed by river-centric context
- Same framing as the Rio Tiete work: river behavior first, pressures and pollutants second, supporting structures third, sediment response last
- Temporal target: always search and collect with a 20-year historical target window whenever the source allows it
- If a source returns less than 20 years, keep the ask at 20 years and record the actual returned coverage explicitly
- Required river-first parity wherever data exist:
  - mainstem Savannah River gauges above, between, and below the reservoirs
  - flow and level context near Augusta and below the cascade
  - river-reach water-quality exports
  - suspended solids, sediment, or turbidity context for the mainstem
  - reservoir operations only where they explain the river signal

Hard restrictions:

- Do not touch `des.sc.gov` without new approval from the main chat
- Do not bypass login, captcha, email gates, or geoblocks
- If one river reach or supporting reservoir has weaker coverage than the others, record the asymmetry explicitly

Mandatory collection window rule:

- Always request or filter a target window of 20 years when the source allows it
- If the source returns less than 20 years, persist the real returned period
- Record the difference explicitly in both the run manifest and the run report
- Do not silently shorten the analytical window

Expected join keys:

- `river_reach_id`
- `river_segment`
- `reservoir_id`
- `reservoir_name`
- `date`
- `year`
- `month`
- `ano_mes`
- `station_id`
- `site_no`
- `gage_id`
