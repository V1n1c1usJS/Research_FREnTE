# Briefing: portal_data_collector - Savannah Pressure Round 2

Objetivo:
- executar uma rodada complementar de pressao focada em tres gaps de alto valor
- organizar o bruto em `data/runs/{run-id}/collection/` com manifesto rastreavel

Sistema alvo:
- Savannah River - HUC8 `03060101`, `03060102`, `03060103`, `03060104`
- foco sedimentologico continua em Clarks Hill / J. Strom Thurmond

Reuso explicito da rodada anterior:
- consultar `data/runs/operational-collect-savannah-pressure-20260415-001840/manifest.json`
- consultar `data/staging/clarks_hill/npdes_dischargers.csv`
- consultar `data/staging/clarks_hill/mn_crosscheck_summary.csv`
- nao recolher os PDFs de TMDL / DO da rodada anterior, salvo se forem necessarios para validar join keys

---

## Alvos prioritarios - coletar nesta ordem

### 1. EPA ECHO - DMR de manganes por instalacao
- source_slug: `epa_echo_dmr_mn_savannah`
- endpoint-alvo: `https://echo.epa.gov/trends/loading-tool/get-data/dmr-data`
- fallback de descoberta, se necessario: interface do ECHO Loading Tool / Trends
- o que coletar:
  - registros DMR de manganes por instalacao e, se disponivel, por outfall / periodo de monitoramento
  - campos desejados: `npdes_id`, `facility_name`, `outfall_id`, `huc8`, `parameter_name`, `monitoring_year`, `monitoring_period`, `reported_value`, `unit`, `limit_value`, `exceedance_flag`
  - capturar tambem o request real, incluindo parametros de filtro aplicados
- filtros obrigatorios:
  - HUC8: `03060101`, `03060102`, `03060103`, `03060104`
  - parametro: `manganese`
- regras de filtro:
  - se o endpoint aceitar apenas filtros por texto / pollutant label, tentar variantes como `manganese`, `Mn`, `manganese compounds`
  - se nao houver filtro de HUC8 no endpoint direto, usar Playwright so para descobrir a chamada de rede equivalente na UI e depois repetir por HTTP
  - se o endpoint retornar um payload amplo sem filtro final de Mn, salvar o bruto completo e registrar um subset de Mn no mesmo `source_slug`
- metodo esperado:
  - preferir HTTP direto no endpoint `dmr-data`
  - usar Playwright apenas para descobrir parametros ocultos ou validar a chamada correta
- formato esperado:
  - resposta bruta exatamente como vier do endpoint (`json`, `csv` ou `xlsx`)
  - se houver opcao de export tabular, salvar tambem uma versao tabular crua
- nota:
  - este alvo existe para fechar o gap que a rodada anterior nao cobriu: Mn por instalacao em vez de apenas compliance geral

### 2. Clemson - PDF 2006-2008 via browser download
- source_slug: `clemson_wqs_savannah_2006`
- pagina-alvo descoberta na rodada anterior: `https://open.clemson.edu/scwrc/2010/2010stormwater/19/`
- download-alvo conhecido: `https://open.clemson.edu/cgi/viewcontent.cgi?article=1142&context=scwrc`
- o que coletar:
  - PDF completo do estudo `Results of an Intensive Water Quality Study of the Middle and Lower Savannah River Basin`
  - qualquer anexo estruturado (`csv`, `xlsx`, `zip`) que apareca no fluxo de download ou na pagina
- mudanca operacional obrigatoria:
  - nesta rodada, NAO usar HTTP direto como metodo principal para o PDF
  - usar Playwright com evento real de download do navegador
  - salvar o arquivo recebido pelo navegador com o nome sugerido pelo portal ou um nome rastreavel no `source_slug`
- fluxo esperado:
  - abrir a item page
  - clicar no botao / link `Download`
  - capturar o evento de arquivo do navegador
  - salvar o arquivo bruto em `collection/{source_slug}/`
  - registrar a URL final do download, o comportamento observado e o nome do arquivo salvo
- criterio de status:
  - `collected` se o browser efetivamente salvar um PDF nao vazio
  - `partial` se a item page for confirmada mas nenhum arquivo real for emitido pelo navegador
  - `blocked` apenas se surgir gate explicito de acesso manual
- nota:
  - o desafio WAF do HTTP direto ja foi observado na rodada anterior e deve ser mencionado no manifest como contexto, nao como surpresa

### 3. USACE / HEC-RAS - bathymetria de Thurmond
- source_slug: `usace_bathymetry_thurmond`
- alvo geografico: Thurmond pool area / bbox aproximado `[-82.5, 33.5, -81.5, 34.5]`
- estrategia:
  - priorizar fontes publicas do USACE / HEC-RAS / Savannah District
  - NAO usar NOAA como fonte principal nesta rodada
- tipos de fonte aceitaveis:
  - terrain / bathymetry rasters
  - grids de profundidade
  - levantamentos batimetricos em `xyz`, `csv`, `tif`, `hdf`, `zip`, `ras` ou formatos equivalentes claramente publicos
  - geometry / terrain bundles do HEC-RAS quando o conteudo espacial for claro e reaproveitavel
  - paginas publicas do Savannah District que exponham survey download ou o caminho oficial de solicitacao
- o que coletar:
  - preferencialmente um dataset espacial publico utilizavel para o pool de Thurmond
  - alternativamente, uma pagina oficial que documente com precisao o caminho publico ou o contato oficial do distrito para a obtencao
- metodo esperado:
  - usar Playwright para localizar o arquivo / bundle / link real
  - depois baixar por HTTP quando houver URL estavel
  - se o arquivo espacial so existir via pacote zip ou download protegido por click-through, registrar exatamente o fluxo
- criterio de status:
  - `collected` se houver arquivo espacial publico baixavel
  - `partial` se houver apenas metadados tecnicos claros, mas nao o arquivo espacial final
  - `blocked` se o acesso depender de contato manual com o distrito ou canal nao automatizavel
- regra importante:
  - se o unico caminho restante for contato humano com Savannah District, salvar as paginas / metadados publicos e marcar `blocked` com motivo `manual_contact_required`

---

## Regras operacionais

- usar Playwright apenas para descoberta de endpoint e para o caso especial do browser download da Clemson
- para `ECHO DMR`, o objetivo e HTTP direto no endpoint real
- para `Clemson`, o objetivo e o evento de download do navegador; esta e a excecao explicita da rodada
- para `USACE bathymetry`, tentar primeiro arquivos espaciais publicos; se nao houver, documentar o caminho oficial e parar
- salvar todos os brutos em `data/runs/{run-id}/collection/{source_slug}/`
- registrar no manifest:
  - URLs exatas usadas
  - metodo de coleta
  - status (`collected`, `partial`, `blocked`)
  - cobertura temporal real quando aplicavel
  - cobertura espacial real quando aplicavel
- registrar artefatos auxiliares quando relevantes:
  - HTML da pagina fonte
  - notas de bloqueio
  - screenshots so se ajudarem a explicar gate ou fluxo especial

## Criterio de qualidade

- `ECHO DMR` deve resultar em uma camada bruta que permita isolar Mn por instalacao
- `Clemson` so conta como resolvido se houver arquivo salvo pelo browser com tamanho maior que zero
- `USACE bathymetry` so conta como resolvido se houver arquivo espacial publico real; metadado sozinho nao equivale a bathymetria entregue
- declarar explicitamente se o round 2 melhora ou nao os gaps deixados por `savannah-pressure-20260415`

## Entregavel esperado

- bruto auditavel em `data/runs/{run-id}/collection/`
- `manifest.json` com status por alvo
- `reports/{run-id}.md` com resumo curto da rodada
- nota curta para o Analyst:
  - DMR Mn chegou ou nao chegou
  - Clemson browser download funcionou ou nao
  - USACE bathymetry entregou arquivo espacial ou ficou em caminho de contato manual
