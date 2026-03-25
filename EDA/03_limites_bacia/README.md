# EDA/03_limites_bacia
Objetivo: estabelecer e validar a base geográfica do projeto — polígonos, sub-bacias, reservatórios.
Insumo: data/staging/limites_bacia/
Saídas para spatial_ref: bacia_tiete.gpkg, subbacias_tiete.gpkg, hidrografia_tiete.gpkg

Análises recomendadas:
- Visualização do mapa base da bacia completa
- Validação dos polígonos de sub-bacias (sem gaps, sem sobreposição)
- Conferência dos limites dos 7 reservatórios em cascata
- Tabela de áreas por sub-bacia (km²)

DEVE SER EXECUTADA PRIMEIRO — é pré-requisito para todas as outras frentes.

Arquivos esperados:
- setup_spatial_ref.ipynb  (gera os arquivos em spatial_ref/)
- validate_geometry.py
- map_overview.py
