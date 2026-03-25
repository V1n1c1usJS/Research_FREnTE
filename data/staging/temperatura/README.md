# staging/temperatura
Origem: raw/temperatura/
Arquivo principal: temp_estacao_dia.parquet
Schema mínimo: id_ponto_monitoramento | data | temp_max_c | temp_min_c | temp_media_c
Limpeza: remover outliers físicos (< -5°C ou > 45°C para SP), interpolar falhas curtas
