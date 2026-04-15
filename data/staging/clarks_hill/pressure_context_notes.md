# Pressure Context Notes - operational-collect-savannah-pressure-20260415-001840

- `epa_echo_npdes_savannah`: the facility-search export yields HUC8 facility/compliance context, but not pollutant-specific discharge parameters or explicit violation years.
- `epd_tmdl_sediment_savannah`: Table 2 was extracted cleanly into subwatershed load targets and reduction percentages.
- `epd_tmdl_bacteria_savannah`: Table 1 supports nonpoint/stormwater segment loads; Table 16 supports point-source facility WLAs.
- `epd_do_restoration_savannah`: Table 5 supports a compact DO-deficit context layer; criterion and critical-period fields were transcribed from the plan text.
- `clemson_wqs_savannah_2006`: no structured attachment was exposed on the item page, and the PDF endpoint returned an AWS WAF challenge for deterministic HTTP download.
- `noaa_bathymetry_savannah`: official NOAA coverage discovered for Savannah is estuarine only and outside the requested Thurmond bbox, so no bathymetry staging artifact was fabricated.
