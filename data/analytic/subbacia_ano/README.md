# analytic/subbacia_ano
Granularidade: sub-bacia × ano
Variáveis mínimas:
  id_subbacia | ano |
  area_desmatada_ha | proporcao_desmatamento_pct | (← desmatamento)
  area_pastagem_pct | area_cana_pct |               (← uso_solo)
  precip_media_mm | precip_total_mm |               (← precipitacao)
  vazao_media_m3s | vazao_especifica_ls_km2         (← vazao)
Fontes: staging/desmatamento, staging/uso_solo, staging/precipitacao, staging/vazao
Dependências espaciais: spatial_ref/subbacias/, spatial_ref/pontos_monitoramento/
