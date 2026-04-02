# raw/operacao_reservatorio
Fonte: ONS dados abertos (dados.ons.org.br), ANA HidroWeb
Entradas: séries temporais de volume armazenado (%), cota, vazão afluente/defluente por reservatório
Saídas para staging: staging/operacao_reservatorio/operacao_reservatorio_dia.parquet
Chaves: id_reservatorio, data, ano_mes
Reservatórios alvo: Barra Bonita, Bariri, Ibitinga, Promissão, Nova Avanhandava, Três Irmãos, Jupiá
Próximos passos: baixar série histórica via ONS dados.ons.org.br/dataset/
