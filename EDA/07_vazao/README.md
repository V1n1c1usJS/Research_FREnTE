# EDA/07_vazao
Objetivo: caracterizar o regime hidrológico da bacia — vazões afluentes, efluentes e tendências.
Insumo principal: data/analytic/subbacia_ano/ e data/analytic/reservatorio_mes/
Insumo secundário: data/staging/vazao/
Referência espacial: data/spatial_ref/pontos_monitoramento/, data/spatial_ref/reservatorios/

Análises recomendadas:
- Série temporal de vazão afluente para cada reservatório
- Curva de permanência de vazões
- Correlação precipitação × vazão (com defasagem)
- Identificação de períodos de estiagem crítica

Chaves: id_reservatorio, id_ponto_monitoramento, data, ano_mes

Arquivos esperados:
- eda_overview.ipynb
- load_and_validate.py
- plots_vazao.py

Nota: pré-requisito para EDA/10_tempo_residencia/
