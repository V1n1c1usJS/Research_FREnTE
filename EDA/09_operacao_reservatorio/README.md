# EDA/09_operacao_reservatorio
Objetivo: caracterizar o comportamento operacional dos 7 reservatórios em cascata do Tietê.
Insumo principal: data/analytic/reservatorio_mes/ e data/analytic/reservatorio_ano/
Insumo secundário: data/staging/operacao_reservatorio/
Referência espacial: data/spatial_ref/reservatorios/

Reservatórios: Barra Bonita | Bariri | Ibitinga | Promissão | Nova Avanhandava | Três Irmãos | Jupiá

Análises recomendadas:
- Série temporal de volume útil (%) por reservatório
- Frequência de eventos críticos (volume < 20%)
- Padrão operacional sazonal (ondas de enchimento/esvaziamento em cascata)
- Comparação entre reservatório de cabeceira (Barra Bonita) e foz (Jupiá)

Chaves: id_reservatorio, ano_mes

Arquivos esperados:
- eda_overview.ipynb
- load_and_validate.py
- plots_operacao.py

Nota: pré-requisito para EDA/10_tempo_residencia/
