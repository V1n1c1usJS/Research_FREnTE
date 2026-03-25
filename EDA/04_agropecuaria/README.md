# EDA/04_agropecuaria
Objetivo: quantificar a intensidade e a evolução da atividade agropecuária na bacia.
Insumo principal: data/analytic/municipio_ano/ (colunas agropecuaria)
Insumo secundário: data/staging/agropecuaria/pam_municipio_ano.parquet
Referência espacial: data/spatial_ref/municipios_area_estudo/

Análises recomendadas:
- Série temporal de área colhida de cana-de-açúcar por município (principal cultura da bacia)
- Intensificação agrícola: área colhida total / área municipal
- Mapa de concentração de cana por sub-bacia
- Correlação entre área de cana e índice de tratamento de esgoto (integração com SNIS)

Chaves: cod_ibge, ano

Arquivos esperados:
- eda_overview.ipynb
- load_and_validate.py
- plots_agropecuaria.py
