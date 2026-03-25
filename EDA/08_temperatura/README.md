# EDA/08_temperatura
Objetivo: caracterizar o regime térmico da região e identificar tendências de aquecimento.
Insumo principal: data/analytic/reservatorio_mes/
Insumo secundário: data/staging/temperatura/
Referência espacial: data/spatial_ref/pontos_monitoramento/

Análises recomendadas:
- Série temporal de temperatura média mensal por estação/região
- Tendência de longo prazo (Mann-Kendall)
- Correlação temperatura × vazão (impacto em evapotranspiração)
- Anomalias térmicas em anos de El Niño/La Niña

Chaves: id_ponto_monitoramento, ano_mes

Arquivos esperados:
- eda_overview.ipynb
- load_and_validate.py
- plots_temperatura.py
