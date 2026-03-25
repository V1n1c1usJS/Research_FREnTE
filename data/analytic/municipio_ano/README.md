# analytic/municipio_ano
Granularidade: município × ano
Variáveis mínimas:
  cod_ibge | municipio | ano |
  indice_coleta_esgoto | indice_tratamento_esgoto |  (← snis)
  area_pastagem_ha | area_cana_ha | area_floresta_ha | (← uso_solo)
  area_desmatada_ha |                                 (← desmatamento)
  producao_cana_t | area_cana_colhida_ha |            (← agropecuaria)
  precip_media_mm |                                   (← precipitacao)
  temp_media_c                                        (← temperatura)
Fontes: staging/snis, staging/uso_solo, staging/agropecuaria, staging/desmatamento,
        staging/precipitacao, staging/temperatura
Dependências espaciais: spatial_ref/municipios_area_estudo/
