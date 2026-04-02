# Output Contract

The default EDA contract for this repository is:

## EDA workspace

```text
EDA/{slug}/
|-- README.md
|-- figures/
|-- generate_figures.py
|-- process_context_sources.py
|-- generate_presentation.py
`-- report_context.json
```

## Data layer outputs

Only create the layers that are supported by real data:

- `data/staging/{domain}/...`
  - cleaned, typed, harmonized tables

- `data/analytic/{grain}/...`
  - consolidated tables used directly by the EDA figures

Common grains in this repository:
- `reservatorio_mes`
- `reservatorio_ano`
- `municipio_ano`
- `subbacia_ano`
- site-level or sample-level tables when the study is not reservoir-aggregated

## Figure outputs

Figures should normally be written to:

- `EDA/{slug}/figures/*.png`

Default expectations:
- stable filenames
- readable titles and labels
- source note or source trace in code comments or chart footer
- 300 dpi export when the output is presentation-facing

## Documentation outputs

`README.md` should capture:
- objective
- input data paths
- join keys
- generated outputs
- known gaps

`report_context.json` should capture:
- report title
- summary of the study context
- list of figures with narrative text
- metrics or highlights used by the HTML report layer
