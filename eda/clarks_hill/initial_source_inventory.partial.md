# Savannah River Inventory

- River collection run: `operational-collect-savannah-river-20260410-204518`
- River targets collected: `13/13`
- Reservoir annex run: `operational-collect-savannah-system-20260409-013209`
- Reservoir annex targets collected: `11/16`
- Analytical frame: `river-first`
- Target coverage rule: `always request 20 years when the source allows it`

## Mainstem hydrology integrated now

- `Augusta` | 2006 to 2026 | 21 returned years | 2 parameter codes | 34,406 daily points
- `USACE Dock` | 2007 to 2026 | 20 returned years | 7 parameter codes | 122,866 daily points

## River chemistry integrated now

- `Calhoun Falls` | 1956 to 1974 | 11 years with data | 63 activities | 954 results
- `Augusta Intake` | 1970 to 1970 | 1 years with data | 1 activities | 7 results
- `US 1 Augusta` | 1997 to 1998 | 2 years with data | 18 activities | 340 results

## Reservoir annex integrated now


## Sediment notebook materialized now

- `Master Data` parsed to `19` valid sediment sites using the same notebook filter (`Site` and `Fe_ppm` present, `1 <= Site <= 30`).
- Top fine-depositional-score sites in the current staging pass: `9, 3, 7, 5, 21`.

## Analytical caveats

- The 20-year target is satisfied by `2` mainstem USGS endpoints in the current staging pass, but river WQP chemistry remains below that target at most sites.
- River chemistry is now real and explicit, but it remains patchier and older than the daily hydrology layer.
- Reservoir operations remain necessary as explanatory modulation, not as the protagonist of the report.
- Thurmond stays the sediment-study target, but the causal path should now start from the river signal.

## Next collection priorities

- River-first gaps still active: `8` priority targets or layers need stronger mainstem coverage.
- Pressure and pollutant gaps still active: `17` contextual targets still need structured ingestion.
- Operational long-series gaps still active: `4` reservoir-operation layers remain snapshot-only or short.
