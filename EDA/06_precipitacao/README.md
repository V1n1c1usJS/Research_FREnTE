# EDA/06_precipitacao
Objetivo: caracterizar o regime pluviométrico da bacia e identificar tendências e anomalias.
Insumo principal: data/analytic/subbacia_ano/ e data/analytic/reservatorio_mes/
Insumo secundário: data/staging/precipitacao/
Referência espacial: data/spatial_ref/pontos_monitoramento/, data/spatial_ref/subbacias/

Análises recomendadas:
- Série temporal mensal de precipitação média na bacia (1980–presente)
- Distribuição espacial da precipitação por sub-bacia
- Identificação de anos secos e úmidos (anomalia em relação à média histórica)
- Sazonalidade: precipitação média por mês do ano

Chaves: id_subbacia, id_ponto_monitoramento, ano_mes

Arquivos esperados:
- eda_overview.ipynb
- load_and_validate.py
- plots_precipitacao.py
