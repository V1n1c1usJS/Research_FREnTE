# staging/precipitacao
Origem: raw/precipitacao/
Arquivos: precip_estacao_dia.parquet, precip_subbacia_mes.parquet
Schema mínimo estação: id_ponto_monitoramento | data | precip_mm | flag_qualidade
Schema mínimo subbacia: id_subbacia | ano_mes | precip_media_mm | n_estacoes
Limpeza: remover outliers (> 500mm/dia), interpolar falhas curtas (< 7 dias)
