# Analyst Scope

Agent:

- `eda_reservatorio`

Mission:

- Convert the collected Savannah River data into a river-first EDA workspace
- Keep the Tiete EDA structure, but apply it to the Savannah River with Hartwell -> Russell -> Thurmond as supporting controls
- Generate reproducible scripts, analytical tables, figures, and report context

Reservoir scope:

- Hartwell
- Russell
- Thurmond

Analytical framing:

- The Savannah River is the main object of analysis
- Final sediment interpretation target remains Thurmond
- Hartwell and Russell are operational controls inside the river narrative, not optional context
- The EDA must show what is comparable across the river and across the three reservoirs and what remains Thurmond-only
- The EDA must preserve the distinction between the 20-year target window and any shorter real period returned by collection

Required work products:

- `EDA/clarks_hill/process_context_sources.py`
- `EDA/clarks_hill/generate_figures.py`
- `EDA/clarks_hill/generate_presentation.py`
- `EDA/clarks_hill/figures/*.png`
- `EDA/clarks_hill/report_context.json`
- `data/staging/clarks_hill/...`
- `data/analytic/clarks_hill/...` when real derivations exist

Primary analysis goals:

1. Harmonize the mainstem river signal across available reaches and sources
2. Add pollutant-pressure and environmental context that helps explain the river behavior
3. Harmonize operational metrics across Hartwell, Russell, and Thurmond where they explain the river
4. Build Thurmond-focused residence-time and operational context even if the other two reservoirs are still incomplete
5. Make gaps explicit in the figures, README, and report context
6. Treat 20 years as the target analytical horizon and show when actual availability is shorter

Expected analytical outputs:

- river hydrology and river water-quality series where coverage exists
- pollutant-pressure context tied to the river corridor
- comparative elevation and storage series where they help explain the river
- comparative inflow and outflow series
- release or discharge context where available
- Thurmond-focused residence-time estimates with upstream regulation context
- water-quality coverage map or inventory for the river first and the three reservoirs second
- data completeness matrix by river reach, reservoir, and variable
- temporal completeness matrix against the 20-year target window

Do not:

- Do not invent missing Hartwell or Russell values
- Do not collapse three-reservoir scope into a Thurmond-only narrative without labeling it as partial
- Do not treat short records as if they represented the requested 20-year window

Escalate if:

- no reliable reservoir mapping can be established from the collected raw files
- variable definitions differ enough across reservoirs to break comparison without a decision
