# analytic/reservatorio_mes
Granularidade: reservatório × mês
Variáveis mínimas:
  id_reservatorio | nome_reservatorio | ano_mes |
  volume_util_pct | cota_m |                              (← operacao_reservatorio)
  vazao_afluente_media_m3s | vazao_defluente_media_m3s | (← operacao_reservatorio + vazao)
  precip_media_mm |                                       (← precipitacao)
  temp_media_c |                                          (← temperatura)
  tempo_residencia_dias                                   (← DERIVADO: volume/vazao_defluente)
Fontes: staging/operacao_reservatorio, staging/vazao, staging/precipitacao, staging/temperatura
Dependências espaciais: spatial_ref/reservatorios/
Nota: tempo_residencia_dias é variável derivada — não existe em nenhuma fonte primária
