# Clarks Hill Initial Source Inventory

- Search run: `perplexity-intel-8ba66531`
- Collection run: `operational-collect-clarkshill-20260401-225924`
- Ranked datasets: `30`
- Collected now: `3`
- Blocked now: `3`

## Usable Now

- `03-savannah-river-basin-landscape-analysis` | Savannah River Basin Landscape Analysis
  local: `collection/03-savannah-river-basin-landscape-analysis/savannah_river_basin_landscape_analysis.pdf`
  note: Direct PDF download succeeded.
- `04-savannah-river-basin-restoration-data-2008` | Savannah River Basin Restoration Data 2008
  local: `collection/04-savannah-river-basin-restoration-data-2008/savannah_rbrp_2018.pdf`
  note: Direct download endpoint returned a PDF successfully.
- `usgs-02193900-monitoring-location` | USGS 02193900 THURMOND LAKE NEAR PLUM BRANCH, SC
  local: `collection/usgs-02193900-monitoring-location/endpoint_confirmed.json`
  local: `collection/usgs-02193900-monitoring-location/iv_02193900.json`
  local: `collection/usgs-02193900-monitoring-location/dv_02193900.json`
  note: Official USGS Water Services endpoints confirmed for site 02193900 and iv/dv JSON artifacts were downloaded.
  note: Site inventory shows 00062 elevation and water-quality/climate variables, not 00060/00065 for this location.

## Blocked

- `08-clark-hill-dam-inflows-and-forecasts` | Clark Hill Dam Inflows and Forecasts
  blocker: Initial Playwright navigation timed out and was aborted after 328.1 seconds.
- `14-savannah-and-salkehatchie-surface-water-data` | Savannah and Salkehatchie Surface Water Data
  blocker: 403 CloudFront geoblock: The Amazon CloudFront distribution is configured to block access from your country.
- `sas-usace-thurmond-basin-dam` | Thurmond Basin Dam Brochure
  blocker: Access Denied from Akamai/edgesuite when requesting the PDF directly.

## Next Analytic Layer

- extract watershed and land-cover context from the two collected PDFs
- wait for structured operational and water-quality endpoints before creating staging or analytic tables
- define join strategy once station ids, basin ids, or time keys arrive from collection

## Not Ready For Figures

- no structured reservoir operations time series collected yet
- no structured inflow or outflow time series collected yet
- no structured water-quality table collected yet
