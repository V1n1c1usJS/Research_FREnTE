# staging/vazao
Origem: raw/vazao/
Arquivos: vazao_estacao_dia.parquet, vazao_reservatorio_mes.parquet
Schema mínimo: id_ponto_monitoramento | data | vazao_m3s | flag_qualidade
Limpeza: remover valores negativos, marcar períodos de operação especial (cheias/estiagens extremas)
