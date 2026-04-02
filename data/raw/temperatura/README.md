# raw/temperatura
Fontes: INMET, ANA HidroWeb, ERA5-Land (ECMWF)
Entradas: séries temporais diárias de temperatura do ar (máx, mín, média) por estação
Saídas para staging: staging/temperatura/temp_estacao_dia.parquet
Chaves: id_ponto_monitoramento, data, ano_mes
Próximos passos: baixar via INMET API (bdmep.inmet.gov.br) ou ERA5 via CDS API
