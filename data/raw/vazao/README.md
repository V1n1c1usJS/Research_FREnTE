# raw/vazao
Fonte: ANA HidroWeb (snirh.gov.br), ONS dados abertos (dados.ons.org.br)
Entradas: séries temporais diárias de vazão afluente e defluente por estação fluviométrica/reservatório
Saídas para staging: staging/vazao/vazao_estacao_dia.parquet, vazao_reservatorio_mes.parquet
Chaves: id_ponto_monitoramento, id_reservatorio, data, ano_mes
Próximos passos: baixar via HidroWeb API (método GetSerie) para estações na bacia do Tietê
