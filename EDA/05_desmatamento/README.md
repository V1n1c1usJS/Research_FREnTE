# EDA/05_desmatamento
Objetivo: quantificar e localizar a perda de cobertura vegetal na bacia ao longo do tempo.
Insumo principal: data/analytic/subbacia_ano/ (colunas desmatamento)
Insumo secundário: data/staging/desmatamento/desmatamento_subbacia_ano.parquet
Referência espacial: data/spatial_ref/subbacias/

Análises recomendadas:
- Taxa anual de desmatamento por sub-bacia (1985–2023)
- Sub-bacias com maior acumulado de perda florestal
- Mapa de hotspots de desmatamento
- Correlação espacial entre desmatamento e área de pastagem/agro (integração com uso do solo)

Chaves: id_subbacia, ano

Arquivos esperados:
- eda_overview.ipynb
- load_and_validate.py
- plots_desmatamento.py

Riscos: PRODES foca em Amazônia — para Cerrado/Mata Atlântica usar MapBiomas Alerta.
