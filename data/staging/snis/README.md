# staging/snis
Origem: raw/snis/
Arquivo principal: snis_municipios_serie.parquet
Schema mínimo: cod_ibge | municipio | ano | pop_total | pop_atendida_agua | pop_atendida_esgoto |
               indice_coleta_esgoto | indice_tratamento_esgoto | volume_esgoto_coletado_m3 |
               volume_esgoto_tratado_m3
Limpeza: remover linhas sem cod_ibge, padronizar cod_ibge para 7 dígitos, interpolar anos faltantes
Filtro espacial: manter apenas municípios com centroide dentro da bacia do Tietê (via spatial_ref/municipios_area_estudo/)
