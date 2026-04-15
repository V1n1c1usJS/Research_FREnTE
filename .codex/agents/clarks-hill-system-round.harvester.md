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
2. Pollutant and environmental-pressure datasets affecting the river corridor — see explicit target list below
3. `water.usace` operational series for all three reservoirs
4. NID structural metadata for all three dams
5. Supporting documents that explain the interaction between the river and the regulated system

River-first target:

- mainstem hydrology
- river water quality
- suspended sediment / turbidity / TSS proxies
- pollutant-pressure sources and impairment context

Environmental pressure targets (priority collect — all marked `missing` in context_source_inventory.csv):

- **EPA ECHO** (echo.epa.gov)
  - NPDES point-source dischargers with permits on the Savannah River watershed
  - Target: facility list, discharge parameter groups, permit status, SIC codes
  - Collection hint: ECHO Facility Search → CSV download, filter by HUC or state GA/SC + Savannah River
  - Expected format: CSV via direct download after filter
  - Why: only structured dataset of direct industrial and municipal discharge into the river corridor

- **EPD Georgia — Sediment TMDL 2010** (epd.georgia.gov)
  - Savannah River Basin Sediment TMDL Evaluation
  - Target: load estimates by sub-basin, impaired reaches, reduction targets
  - Collection hint: PDF or structured table download from EPD site
  - Why: directly validates the depositional scores in the sediment cores

- **EPD Georgia — Bacteria TMDL 2023** (epd.georgia.gov)
  - Savannah River Basin Bacteria TMDL Report
  - Target: impaired reach list, source attribution, coliform load estimates
  - Collection hint: PDF download
  - Why: complements microbiological data already in treated-water layer

- **EPD Georgia — DO Restoration Plan** (epd.georgia.gov)
  - Savannah Harbor dissolved oxygen restoration plan
  - Target: DO impairment zones, seasonal thresholds, upstream source attribution
  - Collection hint: PDF download
  - Why: mechanistic explanation for low-DO episodes at USACE Dock that drive Fe/Mn mobilization in sediments

- **Clemson Water Quality Study 2006–2008** (open.clemson.edu)
  - Middle and lower Savannah River water quality chemistry
  - Target: metals, nutrients, OC, TSS measurements by reach
  - Collection hint: repository bitstream or direct PDF/dataset link
  - Why: only known raw-river chemistry dataset in the 2006–2008 window

- **NOAA Bathymetry** (ncei.noaa.gov)
  - Savannah River bathymetric digital elevation model
  - Target: depth grid or point dataset for Thurmond pool area
  - Collection hint: NCEI search → direct raster or point download
  - Why: needed to weight sediment core locations by depth and volume

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
