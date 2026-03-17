# Consolidado de Pesquisa Manual - real-init-2653813e

Este consolidado prioriza o caminho para chegar ao dado no portal, com foco em navegacao, filtros e estrategia de pesquisa.

Nota de validacao: a confirmacao pratica desta rodada foi feita em navegador real via Playwright CLI Skill.
Por isso, `validated_via_browser` pode ser `true` mesmo quando `validated_via_mcp` for `false`.

## Dados Analiticos

### Hidroweb

- Tipo: `dados_analiticos`
- Entrada principal: `https://www.snirh.gov.br/hidroweb`
- Link direto util: `https://www.snirh.gov.br/hidroweb`
- Modo de acesso: `portal`
- Validado via MCP: `False`
- Validado em browser real: `True`
- Metodo de validacao: `playwright_cli_skill`
- Exige autenticacao: `False`

Passo a passo:
- Abrir o Hidroweb.
- Entrar em Series Historicas.
- Filtrar por estacao, rio, estado ou municipio.
- Executar a consulta e baixar os arquivos da estacao ou do lote selecionado.

Passo a passo validado:
- Abrir `https://www.snirh.gov.br/hidroweb`.
- Clicar em `Series Historicas`.
- Preencher `Estado`, `Municipio`, `Rio`, `Bacia` ou `Tipo Estacao`.
- Clicar em `Consultar`.
- No grid, usar `baixar txt`, `baixar csv` ou `baixar mdb` por estacao.
- Para lote, marcar estacoes, escolher `Texto (.txt)` ou `Excel (.csv)` e clicar em `Baixar Arquivo`.

Labels visiveis na interface:
- Series Historicas
- Tipo Estacao
- Bacia
- SubBacia
- Rio (Selecione Bacia)
- Estado
- Municipio
- Consultar
- baixar txt
- baixar csv
- baixar mdb
- Download para as estacoes selecionadas
- Texto (.txt)
- Excel (.csv)
- Baixar Arquivo
- Solicite Acesso API
- Acesso Restrito

Filtros do portal:
- Tipo Estacao.
- Codigo da Estacao.
- Nome Estacao.
- Bacia.
- SubBacia.
- Rio.
- Estado.
- Municipio.
- Operando.
- Responsavel (Sigla).
- Operadora (Sigla).

Filtros do estudo:
- Priorizar recortes do corredor Sao Paulo -> Tres Lagoas.
- Quando o portal exigir territorio administrativo, priorizar SP, MS e municipios associados ao Tiete/Jupia.
- Favorecer series historicas, indicadores anuais ou mensais e tabelas exportaveis.
- Para hidrologia do corredor, priorizar vazao, nivel e chuva.
- Para Jupia, incluir Castilho, Tiete, Parana e estacoes proximas ao reservatorio.

Valores recomendados para o estudo 100K:
- estado: Sao Paulo, Mato Grosso do Sul
- municipio: Castilho, Tres Lagoas
- rio: Rio Tiete, Rio Parana
- tipo_estacao: Fluviometrica, Pluviometrica
- variavel_operacional: Vazao, Nivel, Chuva

Caminho de download ou exportacao:
- Resumo: O download publico aparece diretamente na grade de Series Historicas, por estacao ou em lote.
- Abrir a consulta em `Series Historicas`.
- Filtrar o recorte desejado.
- Clicar em `Consultar`.
- Baixar por linha ou em lote no rodape do grid.
- Controle observado: baixar txt
- Controle observado: baixar csv
- Controle observado: baixar mdb
- Controle observado: Texto (.txt)
- Controle observado: Excel (.csv)
- Controle observado: Baixar Arquivo
- URL observada: `https://www.snirh.gov.br/hidroweb`
- URL observada: `https://www.snirh.gov.br/hidroweb/serieshistoricas`

Formatos observados:
- TXT
- CSV
- MDB

Termos de busca recomendados:
- `rio tiete`
- `reservatorio de jupia`
- `castilho`
- `tres lagoas`
- `vazao`
- `nivel`
- `chuva`

Saidas esperadas:
- Series historicas por estacao.
- Metadados da estacao.
- Arquivos TXT, CSV e MDB.

Referencias oficiais:
- `https://www.snirh.gov.br/hidroweb`

Bloqueios:
- Nenhum bloqueio publico relevante observado nesta rodada.

Observacoes:
- A navegacao real confirmou o menu Series Historicas e os botoes de download por linha e por lote.
- A API aparece como fluxo separado em Solicite Acesso API e nao foi seguida nesta rodada.

### MapBiomas

- Tipo: `dados_analiticos`
- Entrada principal: `https://plataforma.brasil.mapbiomas.org/`
- Link direto util: `https://plataforma.brasil.mapbiomas.org/`
- Modo de acesso: `portal`
- Validado via MCP: `False`
- Validado em browser real: `True`
- Metodo de validacao: `playwright_cli_skill`
- Exige autenticacao: `False`

Passo a passo:
- Abrir a plataforma.
- Selecionar tema, territorio e periodo.
- Entrar em Downloads.
- Baixar o GeoTIFF rapido por territorio ou gerar um mapa personalizado.

Passo a passo validado:
- Abrir `https://plataforma.brasil.mapbiomas.org/`.
- Fechar os modais informativos com `Continuar`.
- Clicar em `Downloads`.
- Escolher `Territorio` para o download rapido ou usar `Gerar mapa personalizado (GeoTiff)`.
- Acionar `Download (.TIFF)` quando o territorio estiver definido.

Labels visiveis na interface:
- Temas
- Cobertura
- Transicoes
- Agua
- Fogo
- Downloads
- Pesquise um ou mais territorios
- Minha geometria
- Download de Mapas (GeoTiffs)
- Territorio
- Download (.TIFF)
- Gerar mapa personalizado (GeoTiff)

Filtros do portal:
- Tema.
- Colecao.
- Territorio.
- Minha geometria.
- Ano.

Filtros do estudo:
- Priorizar recortes do corredor Sao Paulo -> Tres Lagoas.
- Quando o portal exigir territorio administrativo, priorizar SP, MS e municipios associados ao Tiete/Jupia.
- Favorecer series historicas, indicadores anuais ou mensais e tabelas exportaveis.
- Para o projeto 100K, priorizar uso e cobertura da terra, transicoes, agua e fogo.
- Para recorte fino, preferir geometria propria cobrindo Tiete e Jupia.

Valores recomendados para o estudo 100K:
- tema: Cobertura, Transicoes, Agua, Fogo
- territorio: Municipios do corredor Sao Paulo -> Tres Lagoas
- geometria: Bacia/trecho cobrindo Rio Tiete e Reservatorio de Jupia
- ano: 2019, 2020, 2021, 2022, 2023, 2024

Caminho de download ou exportacao:
- Resumo: O download publico fica no painel `Downloads`, com GeoTIFF rapido por territorio ou geracao personalizada.
- Abrir a plataforma.
- Entrar em `Downloads`.
- Selecionar um `Territorio` ou optar por `Gerar mapa personalizado (GeoTiff)`.
- Clicar em `Download (.TIFF)`.
- Controle observado: Downloads
- Controle observado: Territorio
- Controle observado: Download (.TIFF)
- Controle observado: Gerar mapa personalizado (GeoTiff)
- URL observada: `https://plataforma.brasil.mapbiomas.org/`

Formatos observados:
- GeoTIFF

Termos de busca recomendados:
- `rio tiete`
- `uso da terra`
- `cobertura do solo`
- `transicoes`
- `fogo`
- `tres lagoas`

Saidas esperadas:
- Mapas GeoTIFF.
- Estatisticas por territorio.
- Recorte personalizado por geometria.

Referencias oficiais:
- `https://plataforma.brasil.mapbiomas.org/`

Bloqueios:
- Nenhum bloqueio publico relevante observado nesta rodada.

Observacoes:
- A navegacao real confirmou o painel `Downloads` e o card `Gerar mapa personalizado (GeoTiff)`.
- A plataforma exibiu modais informativos antes de liberar o painel de download.

### Programa Queimadas - INPE

- Tipo: `dados_analiticos`
- Entrada principal: `https://terrabrasilis.dpi.inpe.br/queimadas/portal/`
- Link direto util: `https://terrabrasilis.dpi.inpe.br/queimadas/portal/`
- Modo de acesso: `portal`
- Validado via MCP: `False`
- Validado em browser real: `True`
- Metodo de validacao: `playwright_cli_skill`
- Exige autenticacao: `False`

Passo a passo:
- Abrir o portal do Programa Queimadas.
- Entrar em Download > Dados Abertos para acesso direto aos arquivos.
- Usar Estatisticas quando precisar de recorte por estado, regiao ou bioma.
- Baixar os arquivos do dataserver ou usar Geoservicos OGC.

Passo a passo validado:
- Abrir `https://terrabrasilis.dpi.inpe.br/queimadas/portal/`.
- Entrar em `Download` > `Dados Abertos`.
- Na secao `Focos de Queimadas e Incendios`, escolher CSV (`10 min`, `Diarios`, `Mensais`, `Anuais`) ou KML.
- Na secao `Area Queimada`, escolher `Mensais` em `Tiff` ou `Shapefile`.
- Na secao `Risco de Fogo e Meteorologia`, escolher observado diario ou previsto para os proximos 3 dias.

Labels visiveis na interface:
- Download
- Dados Abertos
- Focos de Queimadas e Incendios
- Arquivos CSV
- 10 min
- Diarios
- Mensais
- Anuais
- Arquivos KML
- Area Queimada
- AQ 1km
- Tiff
- Shapefile
- Risco de Fogo e Meteorologia
- Risco de Fogo Observado
- Risco de Fogo Previsto
- Geoservicos OGC

Filtros do portal:
- Estado.
- Regiao.
- Bioma.
- Periodicidade do arquivo.
- Tipo de dado.

Filtros do estudo:
- Priorizar recortes do corredor Sao Paulo -> Tres Lagoas.
- Quando o portal exigir territorio administrativo, priorizar SP, MS e municipios associados ao Tiete/Jupia.
- Favorecer series historicas, indicadores anuais ou mensais e tabelas exportaveis.
- Priorizar Sao Paulo e Mato Grosso do Sul.
- Cruzar foco de calor com recorte mensal, diario ou anual conforme a analise.

Valores recomendados para o estudo 100K:
- estado: Sao Paulo, Mato Grosso do Sul
- regiao: Sudeste, Centro-Oeste
- bioma: Mata Atlantica, Cerrado
- periodicidade: Diario, Mensal, Anual
- tipo_dado: Focos, Area Queimada, Risco de Fogo, Precipitacao, Temperatura, Umidade relativa

Caminho de download ou exportacao:
- Resumo: O portal expoe links publicos diretos para o dataserver do INPE por tipo de dado e periodicidade.
- Abrir a pagina `Dados Abertos`.
- Escolher a secao do dado.
- Clicar no card de periodicidade ou formato desejado.
- Baixar diretamente do dataserver do INPE.
- Controle observado: 10 min
- Controle observado: Diarios
- Controle observado: Mensais
- Controle observado: Anuais
- Controle observado: Focos diarios web
- Controle observado: Mensais Tiff
- Controle observado: Mensais Shapefile
- Controle observado: Risco de Fogo Observado
- Controle observado: Risco de Fogo Previsto
- URL observada: `https://terrabrasilis.dpi.inpe.br/queimadas/portal/pages/secao_downloads/dados-abertos/#da-focos`
- URL observada: `https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/diario/`
- URL observada: `https://dataserver-coids.inpe.br/queimadas/queimadas/area_queimada/colecao2/tif/`
- URL observada: `https://dataserver-coids.inpe.br/queimadas/queimadas/area_queimada/colecao2/shp/`
- URL observada: `https://terrabrasilis.dpi.inpe.br/queimadas/geoserver/ows?SERVICE=WMS&VERSION=1.3.0&REQUEST=Getcapabilities`

Formatos observados:
- CSV
- KML
- TIFF
- Shapefile
- WMS
- WFS

Termos de busca recomendados:
- `sao paulo`
- `mato grosso do sul`
- `focos ativos`
- `csv`
- `risco de fogo`
- `precipitacao`

Saidas esperadas:
- Arquivos CSV e KML de focos.
- TIFF e Shapefile de area queimada.
- Arquivos diarios observados e previstos de risco de fogo e meteorologia.
- Servicos WMS/WFS.

Referencias oficiais:
- `https://terrabrasilis.dpi.inpe.br/queimadas/portal/`
- `https://terrabrasilis.dpi.inpe.br/queimadas/portal/pages/secao_downloads/dados-abertos/#da-focos`

Bloqueios:
- Nenhum bloqueio publico relevante observado nesta rodada.

Observacoes:
- A navegacao real confirmou a pagina `Dados Abertos` com links publicos diretos do dataserver do INPE.
- Para comparativos territoriais, o portal principal tambem exibe `Estatisticas: Estados, Regioes e Biomas`.

### SIDRA - IBGE

- Tipo: `dados_analiticos`
- Entrada principal: `https://sidra.ibge.gov.br/`
- Link direto util: `https://sidra.ibge.gov.br/`
- Modo de acesso: `portal`
- Validado via MCP: `False`
- Validado em browser real: `True`
- Metodo de validacao: `playwright_cli_skill`
- Exige autenticacao: `False`

Passo a passo:
- Abrir o SIDRA.
- Entrar em Acervo.
- Filtrar pesquisa, assunto e tabela.
- Abrir a tabela, ajustar os editores e usar Download.

Passo a passo validado:
- Abrir `https://sidra.ibge.gov.br/`.
- Clicar em `Acervo`.
- Selecionar a pesquisa `C4 - Contas Economicas Ambientais da Agua`.
- Selecionar o assunto `274 - Meio ambiente`.
- Abrir a tabela `9688` pelo icone de tabela.
- Ajustar os editores `Variavel`, `Atividades economicas e familias`, `Ano` e `Unidade Territorial`.
- Clicar em `Download` e escolher o formato.

Labels visiveis na interface:
- Acervo
- Filtros ativos
- Pesquisa
- Assunto
- Tabela de dados agregados
- Contas Economicas Ambientais da Agua
- Variavel
- Atividades economicas e familias
- Ano
- Unidade Territorial
- Visualizar
- Download
- Salvar Quadro

Filtros do portal:
- Pesquisa.
- Assunto.
- Tabela de dados agregados.
- Variavel.
- Atividades economicas e familias.
- Ano.
- Unidade Territorial.

Filtros do estudo:
- Priorizar recortes do corredor Sao Paulo -> Tres Lagoas.
- Quando o portal exigir territorio administrativo, priorizar SP, MS e municipios associados ao Tiete/Jupia.
- Favorecer series historicas, indicadores anuais ou mensais e tabelas exportaveis.
- Priorizar recortes de meio ambiente, agua e indicadores territoriais.
- Cruzar o corredor via municipio, UF ou agregados nacionais quando a tabela nao descer ao nivel local.

Valores recomendados para o estudo 100K:
- pesquisa: C4 - Contas Economicas Ambientais da Agua, IU - Indicadores de Desenvolvimento Sustentavel, DU - uso da terra nos biomas brasileiros
- assunto: 274 - Meio ambiente
- tabelas_uteis: 9688, 9687, 9692, 9693
- unidade_territorial: Brasil, Sao Paulo, Mato Grosso do Sul, Municipios do corredor quando a tabela permitir
- ano: 2018, 2019, 2020

Caminho de download ou exportacao:
- Resumo: O download publico aparece diretamente dentro da pagina da tabela selecionada.
- Abrir a tabela desejada.
- Configurar os editores da tabela.
- Clicar em `Download`.
- Definir nome do arquivo e formato.
- Usar o link final de download gerado pela propria tabela.
- Controle observado: Download
- Controle observado: Nome do arquivo
- Controle observado: Formato
- Controle observado: XLSX
- Controle observado: ODS
- Controle observado: HTML
- Controle observado: CSV (BR)
- Controle observado: CSV (US)
- Controle observado: TSV (BR)
- Controle observado: TSV (US)
- URL observada: `https://sidra.ibge.gov.br/acervo#/S/C4/A/274/T/Q`
- URL observada: `https://sidra.ibge.gov.br/Tabela/9688`

Formatos observados:
- XLSX
- ODS
- HTML
- CSV (BR)
- CSV (US)
- TSV (BR)
- TSV (US)

Termos de busca recomendados:
- `contas economicas ambientais da agua`
- `meio ambiente`
- `indicadores de desenvolvimento sustentavel`
- `sao paulo`
- `tres lagoas`

Saidas esperadas:
- Tabelas agregadas com URL persistida.
- Download tabular em formatos multiplos.
- Quadro salvo para reproducao da consulta.

Referencias oficiais:
- `https://sidra.ibge.gov.br/`
- `https://sidra.ibge.gov.br/acervo`
- `https://sidra.ibge.gov.br/Tabela/9688`

Bloqueios:
- Nenhum bloqueio publico relevante observado nesta rodada.

Observacoes:
- A navegacao real confirmou o fluxo `Acervo -> Assunto -> Tabela de dados agregados -> Tabela -> Download`.
- Na validacao real, a tabela 9688 exibiu apenas `Brasil` em Unidade Territorial no recorte testado.

### SNIS

- Tipo: `dados_analiticos`
- Entrada principal: `https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/snis`
- Link direto util: `https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/snis`
- Modo de acesso: `portal`
- Validado via MCP: `False`
- Validado em browser real: `True`
- Metodo de validacao: `playwright_cli_skill`
- Exige autenticacao: `False`

Passo a passo:
- Abrir a pagina principal do SNIS.
- Escolher entre Painel ou Serie Historica.
- Para consulta reproduzivel, entrar em Serie Historica > Municipios.
- Preencher filtros territoriais e de ano e seguir para o relatorio.

Passo a passo validado:
- Abrir a pagina principal do SNIS.
- Entrar em `Serie Historica` pelo card `bt_serie_historica.png`.
- Na aplicacao `SNIS - Serie Historica`, abrir `Municipios`.
- Entrar em `Informacoes e indicadores municipais consolidados`.
- Preencher `Ano de Referencia`, `Estado` e `Municipios (*)` e clicar em `Continuar`.
- Se precisar de leitura agregada rapida, usar o `Painel` e filtrar o `Ano` no Power BI.

Labels visiveis na interface:
- Painel
- Serie Historica
- Diagnosticos
- Abastecimento de Agua
- Esgotamento Sanitario
- Manejo dos Residuos Solidos Urbanos
- Drenagem e Manejo das Aguas Pluviais Urbanas
- Filtros
- Tipo Informacao
- Ano de Referencia
- Regiao
- Estado
- Municipios (*)
- Continuar
- Relatorio do Power BI
- Ano

Filtros do portal:
- Componente.
- Tipo Informacao.
- Ano de Referencia.
- Regiao.
- Estado.
- Municipios.
- Prestador de servico.
- Familia de informacoes e indicadores.
- Informacoes e Indicadores.

Filtros do estudo:
- Priorizar recortes do corredor Sao Paulo -> Tres Lagoas.
- Quando o portal exigir territorio administrativo, priorizar SP, MS e municipios associados ao Tiete/Jupia.
- Favorecer series historicas, indicadores anuais ou mensais e tabelas exportaveis.
- Priorizar Agua e Esgotos e, quando fizer sentido, Aguas Pluviais.
- Usar Castilho, Panorama, Tres Lagoas e outros municipios do eixo Tiete/Jupia como primeiro recorte.

Valores recomendados para o estudo 100K:
- componente: Agua e Esgotos, Aguas Pluviais
- estado: Sao Paulo, Mato Grosso do Sul
- municipios: Castilho/SP, Panorama/SP, Tres Lagoas/MS
- ano: 2022
- familias: Operacionais - agua, Operacionais - esgotos, Qualidade, Informacoes sobre PMSB

Caminho de download ou exportacao:
- Resumo: O melhor caminho operacional e `Serie Historica`; a tela de filtros foi validada, mas o passo final da exportacao nao foi concluido na automacao desta rodada.
- Abrir `Serie Historica`.
- Entrar em `Municipios`.
- Abrir `Informacoes e indicadores municipais consolidados`.
- Selecionar `Ano de Referencia`, `Estado` e `Municipios (*)`.
- Clicar em `Continuar` para gerar o relatorio e a exportacao.
- Controle observado: Filtros
- Controle observado: Tipo Informacao
- Controle observado: Ano de Referencia
- Controle observado: Estado
- Controle observado: Municipios (*)
- Controle observado: Continuar
- Controle observado: Relatorio do Power BI
- Controle observado: Ano
- URL observada: `https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/snis`
- URL observada: `https://app4.cidades.gov.br/serieHistorica/`
- URL observada: `https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/snis/painel/ab`

Formatos observados:
- Excel (declarado pela aplicacao)
- Planilhas eletronicas (declarado pela aplicacao)

Termos de busca recomendados:
- `agua e esgotos`
- `serie historica`
- `castilho`
- `panorama`
- `tres lagoas`
- `prestador`

Saidas esperadas:
- Indicadores consolidados em painel.
- Series historicas por municipio ou prestador.
- Planilhas exportaveis e glossarios de apoio.

Referencias oficiais:
- `https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/snis`
- `https://app4.cidades.gov.br/serieHistorica/`
- `https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/snis/painel/ab`

Bloqueios:
- Na automacao Playwright da Serie Historica, o app exibiu o alerta `E necessario selecionar ao menos um(a) Municipio.` mesmo com municipio marcado na interface.
- O caminho ate a tela final de exportacao ficou parcialmente validado, mas o clique final no relatorio nao foi concluido de ponta a ponta nesta rodada.

Observacoes:
- A navegacao real confirmou a pagina principal, o `Painel` com Power BI e a tela de filtros da `Serie Historica`.
- O aplicativo da Serie Historica declara no proprio texto que permite exportacao para Excel e planilhas eletronicas.

## Literatura e Documentacao

### SciELO

- Tipo: `literatura_documentacao`
- Entrada principal: `https://search.scielo.org/?lang=pt`
- Link direto util: `https://www.scielo.br/`
- Modo de acesso: `documentation`
- Validado via MCP: `False`
- Validado em browser real: `True`
- Metodo de validacao: `playwright_cli_skill`
- Exige autenticacao: `False`

Passo a passo:
- Abrir a busca da SciELO.
- Executar a consulta por rio, reservatorio ou variavel.
- Usar filtros de colecao, periodico, idioma e ano.
- Abrir texto e PDF para rastrear fontes citadas.

Passo a passo validado:
- Abrir `https://search.scielo.org/?lang=pt`.
- A navegacao automatizada encontrou `403 Forbidden` antes de expor os filtros da busca.
- Usar `https://www.scielo.br/` manualmente se precisar continuar a pesquisa bibliografica fora da automacao.

Labels visiveis na interface:
- 403 Forbidden

Filtros do portal:
- Colecoes.
- Periodico.
- Idioma.
- Ano.
- Area tematica.
- Tipo de literatura.

Filtros do estudo:
- Priorizar recortes do corredor Sao Paulo -> Tres Lagoas.
- Quando o portal exigir territorio administrativo, priorizar SP, MS e municipios associados ao Tiete/Jupia.
- Favorecer series historicas, indicadores anuais ou mensais e tabelas exportaveis.
- Priorizar ciencias ambientais, recursos hidricos, saneamento e geografia.
- Fechar por anos recentes para rastrear bases ainda ativas.

Valores recomendados para o estudo 100K:
- consulta: "rio tiete", "reservatorio de jupia", "qualidade da agua"
- uso: Literatura, Metodologia, Referencias de datasets

Caminho de download ou exportacao:
- Resumo: Nao houve caminho de download validado nesta rodada porque a busca automatizada retornou `403 Forbidden`.
- Abrir a busca publica.
- Registrar o bloqueio HTTP.
- Tratar a fonte como apoio bibliografico, nao como fonte operacional nesta rodada.
- Controle observado: 403 Forbidden
- URL observada: `https://search.scielo.org/?lang=pt`

Formatos observados:

Termos de busca recomendados:
- `"rio tiete"`
- `"reservatorio de jupia"`
- `"qualidade da agua"`
- `sedimentos`
- `uso da terra`
- `saneamento`

Saidas esperadas:
- Artigos e revisoes.
- PDFs e textos completos.
- Referencias de datasets e metodos.

Referencias oficiais:
- `https://search.scielo.org/?lang=pt`
- `https://www.scielo.br/`

Bloqueios:
- A busca automatizada em `https://search.scielo.org/?lang=pt` retornou `403 Forbidden` no navegador real.

Observacoes:
- SciELO segue sendo uma trilha de descoberta metodologica e bibliografica, nao um dataset operacional direto.
- Nesta rodada, a validacao real detectou bloqueio HTTP na busca publica automatizada.
