# staging/uso_solo
Origem: raw/mapbiomas/
Arquivo principal: uso_solo_municipio_ano.parquet, uso_solo_subbacia_ano.parquet
Schema mínimo: cod_ibge | id_subbacia | ano | classe_mapbiomas | area_ha | proporcao_pct
Classes alvo: formação florestal, formação savânica, pastagem, agricultura anual, cana-de-açúcar,
              área urbanizada, corpos d'água, silvicultura
Limpeza: reclassificar para esquema simplificado de 8 classes, agregar por unidade espacial
