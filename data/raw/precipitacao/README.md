# raw/precipitacao
Fontes: ANA HidroWeb (snirh.gov.br), CHIRPS (chc.ucsb.edu), INMET
Entradas: séries temporais diárias/mensais por estação pluviométrica
Saídas para staging: staging/precipitacao/precip_estacao_dia.parquet, precip_subbacia_mes.parquet
Chaves: id_ponto_monitoramento, id_subbacia, data, ano_mes
Próximos passos: baixar via ANA HidroWeb API ou CHIRPS NetCDF por bbox da bacia
