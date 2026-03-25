# EDA/02_uso_do_solo
Objetivo: mapear e quantificar as classes de uso e cobertura do solo na bacia, 1985–2023.
Insumo principal: data/analytic/subbacia_ano/ (colunas uso_solo)
Insumo secundário: data/staging/uso_solo/uso_solo_subbacia_ano.parquet
Referência espacial: data/spatial_ref/subbacias/

Análises recomendadas:
- Evolução temporal das classes (pastagem, cana, floresta, urbano) por sub-bacia
- Proporção atual de cada classe na área total da bacia
- Identificação de sub-bacias com maior conversão de floresta para agro
- Mapa de uso atual (ano mais recente disponível)

Chaves: id_subbacia, ano

Arquivos esperados:
- eda_overview.ipynb
- load_and_validate.py
- plots_uso_solo.py

Riscos: MapBiomas tem erros de classificação em áreas de transição — validar com imagens Sentinel quando possível.
