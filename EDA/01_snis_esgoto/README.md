# EDA/01_snis_esgoto
Objetivo: caracterizar a cobertura e qualidade do saneamento nos municípios da bacia do Tietê.
Insumo principal: data/analytic/municipio_ano/ (colunas SNIS)
Insumo secundário: data/staging/snis/snis_municipios_serie.parquet
Referência espacial: data/spatial_ref/municipios_area_estudo/

Análises recomendadas:
- Série temporal 2000–2022: índice de coleta e tratamento de esgoto por município
- Mapa de cobertura de esgoto (gradiente por município na bacia)
- Distribuição do déficit de saneamento por sub-bacia
- Comparação entre municípios urbanos vs rurais da bacia

Chaves: cod_ibge, ano

Arquivos esperados:
- eda_overview.ipynb
- load_and_validate.py
- quality_checks.py
- plots_saneamento.py

Riscos: dados SNIS têm auto-declaração municipal — inconsistências frequentes em municípios pequenos.
