# Auditoria de lacunas de dados do projeto ambiental

## Resumo executivo

Foi feita uma auditoria do repositorio inteiro com foco em evidencia real ja produzida pelas runs, e nao apenas no que o pipeline sugeriu por heuristica ou automaticamente. O resultado e que o repo ja localizou com boa forca as bases de `SNIS/esgoto`, `uso do solo`, `limites de bacia`, `precipitacao`, `vazao`, `operacao de reservatorio`, `agropecuaria`, `desmatamento` e parte importante do bloco de `materia organica/optica` via literatura e PDFs aderentes ao sistema Tiete.

Ao mesmo tempo, varias variaveis criticas ainda nao estao realmente consolidadas como dataset pronto, mesmo quando aparecem em relatorios ou rankings internos. Os casos mais sensiveis sao `DBO/DQO`, `clorofila-a`, `indices opticos avancados`, `queimadas`, `MDE`, `sensoriamento remoto operacional de qualidade da agua`, `residuos solidos` e `batimetria`. Nessas frentes, o repo tem pistas e fontes provaveis, mas ainda nao entregou localizacao robusta de dados utilizaveis.

O pipeline downstream ainda contem heuristicas, mocks e classificacao por dominio/extensao. Por isso, nesta auditoria, um item so foi considerado `FOUND_REPO` quando havia pelo menos nome de fonte, URL ou recurso claramente identificavel e alguma indicacao pratica de acesso. Resultados ruidosos, paginas genericas e resumos narrativos foram rebaixados para `PARTIAL_LEAD`.

## Metodologia usada na auditoria

1. Foi inspecionado o workspace inteiro, incluindo arquivos locais presentes fora do Git, com leitura de `data/runs/`, `reports/`, `output/`, `prompts/` e `src/`.
2. Foram procurados explicitamente `catalog.json`, `01_research-scout.json`, `02_query-expansion.json`, `03_dataset-discovery.json` e `06_access.json`. Esses arquivos nao existem no estado atual do repo.
3. A auditoria percorreu todas as runs encontradas em `data/runs/`, com foco principal em:
   - `collection/raw-sessions.json`
   - `processing/02-enriched-datasets.json`
   - `processing/03-ranked-datasets.json`
   - relatorios em `reports/`
4. O codigo dos agentes e schemas foi lido para entender a confiabilidade dos campos:
   - `FilterValidateAgent` remove ruido basico, mas nao prova qualidade cientifica da fonte.
   - `EnrichAgent` infere parte dos metadados via LLM/heuristica.
   - `RankAccessAgent` classifica acesso principalmente por dominio e extensao.
   - Portanto, score, ranking e `access_type` foram tratados como apoio, nao como evidencia final.
5. O arquivo `output/current_search_queries.md` foi usado para entender intencao de coleta e fontes-alvo, mas intencao sozinha nao contou como dado encontrado.
6. Criterio conservador:
   - `FOUND_REPO`: fonte/dataset claramente localizado com evidencia concreta de acesso.
   - `PARTIAL_LEAD`: portal, artigo, documentacao ou pista relevante sem dataset claramente pronto.
   - `NEEDS_COLLECTION`: nada util ou aderente encontrado.
   - `DERIVED`: variavel nao precisa de coleta direta se puder ser derivada de bases ja localizadas.

## Tabela consolidada

| Variavel | Prioridade | Status | Evidencia encontrada | Arquivo origem no repo | Run ID | Fonte identificada | Tipo de acesso | Prontidao analitica | Observacao |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COT / COD / COP | critical | FOUND_REPO | Evidencia concreta de COD/CDOM em Barra Bonita e mencao de COT em material CETESB | `data/runs/perplexity-intel-67b872c1/processing/02-enriched-datasets.json` | `perplexity-intel-67b872c1` | UNESP Barra Bonita; CETESB aguas interiores | pdf_table | baixa | Encontrado, mas ainda em PDF/artigo; COP nao apareceu de forma clara |
| CDOM / FDOM | critical | FOUND_REPO | Estudo aderente ao Tiete com CDOM; FDOM so em pistas genericas | `data/runs/perplexity-intel-67b872c1/processing/02-enriched-datasets.json` | `perplexity-intel-67b872c1` | UNESP; LABISA/INPE | pdf_table | baixa | CDOM efetivamente localizado; FDOM ainda fraco |
| DBO / DQO | critical | PARTIAL_LEAD | Mencao de DBO no Tiete e referencias secundarias; DQO sem dataset aderente | `data/runs/perplexity-intel-6a79327f/collection/raw-sessions.json` | `perplexity-intel-6a79327f` | USP Noticias e materiais secundarios | portal | baixa | Boa pista, mas nao base pronta |
| Clorofila-a | critical | PARTIAL_LEAD | Artigos e paginas INPE/OBT sobre clorofila em reservatorios paulistas | `data/runs/perplexity-intel-c88076ac/processing/03-ranked-datasets.json` | `perplexity-intel-c88076ac` | INPE/OBT; artigo RSD | pdf_table | baixa | Falta dataset operacional claramente localizado |
| IET (estado trofico) | critical | FOUND_REPO | Estudo de Barra Bonita e material CETESB/CBH-AT com IET | `data/runs/perplexity-intel-6a79327f/collection/raw-sessions.json` | `perplexity-intel-6a79327f` | SciELO Ambi-Agua; CETESB/CBH-AT | pdf_table | baixa | Encontrado como PDF/tabela, nao como base tabular pronta |
| Esgoto (SNIS) | critical | FOUND_REPO | SNIS oficial, recurso CSV e planilha CETESB de saneamento paulista | `data/runs/perplexity-intel-67b872c1/processing/03-ranked-datasets.json` | `perplexity-intel-67b872c1` | SNIS; portal CKAN; CETESB | download_manual | alta | Uma das evidencias mais fortes do repo |
| Uso do solo | critical | FOUND_REPO | MapBiomas downloads, GEE e links de GeoTIFF ja identificados | `data/runs/perplexity-intel-8b5a5553/reports/relatorio_100k.html` | `perplexity-intel-8b5a5553` | MapBiomas; GEE | download_manual | alta | Falta consolidar recorte espacial, nao descobrir a fonte |
| Precipitacao | critical | FOUND_REPO | BDMEP/INMET e Rede Hidrometeorologica ANA/Hidroweb localizados | `data/runs/perplexity-intel-67b872c1/processing/02-enriched-datasets.json` | `perplexity-intel-67b872c1` | INMET; ANA SNIRH/Hidroweb | portal | media | Base oficial localizada, mas ainda sem extracao consolidada |
| Vazao | critical | FOUND_REPO | ANA/Hidroweb/telemetria e ONS hidrologia de reservatorios | `data/runs/perplexity-intel-67b872c1/processing/02-enriched-datasets.json` | `perplexity-intel-67b872c1` | ANA; ONS | portal | media | Ja ha base forte localizada |
| Tempo de residencia | critical | DERIVED | Pode ser derivado de vazao e cota-area-volume/operacao | `data/runs/perplexity-intel-67b872c1/processing/03-ranked-datasets.json` | `perplexity-intel-67b872c1` | ONS; ANA SAR; SNIRH CAV | portal | media | Nao exige coleta direta prioritaria |
| Limites da bacia | critical | FOUND_REPO | Shapefiles/catalogos claros de ANA, ONS e CBH-AT | `data/runs/perplexity-intel-1a6c8db8/processing/03-ranked-datasets.json` | `perplexity-intel-1a6c8db8` | ANA SNIRH; ONS; CBH-AT | download_manual | alta | Variavel ja efetivamente localizada |
| Indices opticos (SUVA254, E2:E3, PARAFAC) | important | PARTIAL_LEAD | Artigos metodologicos e literatura, sem base aderente pronta | `data/runs/perplexity-intel-c88076ac/processing/02-enriched-datasets.json` | `perplexity-intel-c88076ac` | Literatura academica DOM/fluorescencia | pdf_table | baixa | Serve mais para revisao e desenho de coleta |
| Queimadas | important | PARTIAL_LEAD | TerraBrasilis e mencoes a monitoramento de fogo, sem dataset explicito ja localizado | `data/runs/perplexity-intel-67b872c1/collection/raw-sessions.json` | `perplexity-intel-67b872c1` | TerraBrasilis/INPE | portal | baixa | Falta localizar de forma limpa a base operacional |
| Agropecuaria | important | FOUND_REPO | PAM/IBGE, serie historica e API SIDRA ja apontadas | `data/runs/perplexity-intel-67b872c1/collection/raw-sessions.json` | `perplexity-intel-67b872c1` | IBGE PAM; SIDRA | api | alta | Fonte oficial robusta ja localizada |
| Desmatamento | important | FOUND_REPO | PRODES, TerraBrasilis e MapBiomas Alerta | `data/runs/perplexity-intel-67b872c1/processing/03-ranked-datasets.json` | `perplexity-intel-67b872c1` | INPE; MapBiomas Alerta | portal | media | Falta baixar/consolidar o recorte do projeto |
| Temperatura | important | FOUND_REPO | Bases meteorologicas oficiais localizadas | `data/runs/perplexity-intel-67b872c1/processing/02-enriched-datasets.json` | `perplexity-intel-67b872c1` | INMET; ANA | portal | media | Encontrado para temperatura do ar; temperatura da agua segue fraca |
| Operacao do reservatorio | important | FOUND_REPO | ONS, ANA SAR e cota-area-volume localizados | `data/runs/perplexity-intel-67b872c1/processing/03-ranked-datasets.json` | `perplexity-intel-67b872c1` | ONS; ANA SAR; SNIRH | portal | media | Ja ha base para consolidacao por reservatorio |
| MDE (relevo) | important | PARTIAL_LEAD | Intencao clara nos prompts, mas evidencia salva ficou majoritariamente ruidosa/secundaria | `output/current_search_queries.md` | `n/a` | Pistas para SRTM/ALOS/TOPODATA/Brasil em Relevo | unknown | baixa | Ainda nao foi localizado de forma convincente nas runs |
| Sensoriamento remoto de qualidade da agua (Sentinel-2 / Landsat / GEE) | important | PARTIAL_LEAD | Estudos e metodologia localizados, mas nao colecao operacional pronta | `data/runs/perplexity-intel-c88076ac/processing/03-ranked-datasets.json` | `perplexity-intel-c88076ac` | INPE/OBT; artigos academicos | pdf_table | baixa | Aderente como pista, insuficiente como dataset encontrado |
| Residuos solidos | complementary | PARTIAL_LEAD | Materiais genericos/municipais e saneamento, sem base estruturada clara | `data/runs/perplexity-intel-67b872c1/collection/raw-sessions.json` | `perplexity-intel-67b872c1` | Materiais municipais/estaduais | portal | baixa | Ainda nao ha dataset real localizado |
| Batimetria | complementary | PARTIAL_LEAD | PDFs/metadados genericos e cota-area-volume, sem batimetria clara para Tiete/Jupia | `data/runs/perplexity-intel-67b872c1/collection/raw-sessions.json` | `perplexity-intel-67b872c1` | SNIRH/ANA; documentos genericos | pdf_table | baixa | Requer coleta direcionada adicional |

## Ja temos no repo

As variaveis abaixo ja tem evidencia concreta de fonte ou dataset localizado dentro das runs/artefatos atuais:

- COT / COD / COP
- CDOM / FDOM
- IET (estado trofico)
- Esgoto (SNIS)
- Uso do solo
- Precipitacao
- Vazao
- Limites da bacia
- Agropecuaria
- Desmatamento
- Temperatura
- Operacao do reservatorio

Leitura critica importante:

- Nem todas essas variaveis estao em formato tabular pronto.
- `SNIS`, `uso do solo`, `limites da bacia` e `agropecuaria` sao os casos mais maduros.
- `COT/COD/COP`, `CDOM/FDOM` e `IET` foram encontrados principalmente em PDFs/artigos aderentes, entao contam como localizacao de fonte util, mas ainda pedem extracao manual ou semiautomatica.

## Temos pistas, mas falta consolidar

As variaveis abaixo ja tem fontes provaveis ou mencoes relevantes, porem ainda nao ha dataset claramente localizado e pronto:

- DBO / DQO
- Clorofila-a
- Indices opticos (SUVA254, E2:E3, PARAFAC)
- Queimadas
- MDE (relevo)
- Sensoriamento remoto de qualidade da agua (Sentinel-2 / Landsat / GEE)
- Residuos solidos
- Batimetria

Padrao observado:

- Boa parte dessas variaveis aparece em artigos, paginas institucionais, relatorios ou pistas genericas.
- Falta, porem, o passo que separa "ha um portal ou paper promissor" de "ha um arquivo, colecao, endpoint ou tabela efetivamente utilizavel para analise".

## Precisa coletar

Nenhuma variavel foi classificada como `NEEDS_COLLECTION` absoluta porque o repo ja contem ao menos alguma pista relevante para quase todos os temas. Ainda assim, na pratica, estas frentes exigem nova coleta direcionada e provavelmente devem ser tratadas como coleta prioritaria:

- DBO / DQO
- Clorofila-a
- Indices opticos (SUVA254, E2:E3, PARAFAC)
- Queimadas
- MDE (relevo)
- Sensoriamento remoto de qualidade da agua (Sentinel-2 / Landsat / GEE)
- Residuos solidos
- Batimetria

## Proximos passos por ordem de prioridade

### 1. Coleta imediata

- DBO / DQO: refazer busca focada em CETESB/QUALAR, ANA, SABESP e series laboratoriais ou monitoramentos oficiais diretamente aplicaveis ao Tiete e reservatorios conectados.
- Clorofila-a: buscar bases operacionais em CETESB, SABESP, ANA ou produtos academicos com tabela/suplemento reutilizavel.
- Queimadas: localizar explicitamente a base operacional do INPE para focos/area queimada, em vez de manter so a referencia ao portal TerraBrasilis.
- MDE (relevo): localizar fonte primaria limpa e oficial para SRTM/ALOS/TOPODATA com recorte do corredor.
- Batimetria: buscar especificamente levantamentos de Jupia, Barra Bonita, Ibitinga, Promissao, Nova Avanhandava e Tres Irmaos, alem de verificar concessionarias e ANA/ONS.

### 2. Consolidacao ou extracao de fontes ja localizadas

- SNIS/esgoto: baixar e harmonizar municipios do corredor.
- Uso do solo: consolidar MapBiomas em recorte espacial do projeto.
- Limites da bacia: fechar camada base de bacias/sub-bacias e trechos de interesse.
- Precipitacao e vazao: definir estacoes-chave e automatizar extracao.
- Operacao do reservatorio: consolidar series ONS/ANA por reservatorio relevante.
- Agropecuaria e desmatamento: recortar espacialmente e integrar com pressao antropica.
- COT/COD/CDOM/IET: extrair manualmente as tabelas e variaveis localizadas em PDFs/artigos aderentes.

### 3. Derivacao a partir de bases existentes

- Tempo de residencia: derivar a partir de volume armazenado/cota-area-volume e vazoes afluente/defluente.
- Desmatamento como componente de mudanca de cobertura: em alguns usos analiticos pode ser derivado ou checado contra series de uso do solo do MapBiomas.
- Indicadores compostos de pressao antropica: combinar uso do solo, agropecuaria, esgoto, residuos solidos e queimadas quando as bases faltantes forem consolidadas.

## Ranking final em ordem de acao pratica

### Coleta imediata

1. DBO / DQO
2. Clorofila-a
3. Queimadas
4. MDE (relevo)
5. Batimetria
6. Indices opticos (SUVA254, E2:E3, PARAFAC)
7. Sensoriamento remoto de qualidade da agua (Sentinel-2 / Landsat / GEE)
8. Residuos solidos

### Consolidacao/extracao de fontes ja localizadas

1. Esgoto (SNIS)
2. Uso do solo
3. Limites da bacia
4. Vazao
5. Precipitacao
6. Operacao do reservatorio
7. Agropecuaria
8. Desmatamento
9. COT / COD / COP
10. CDOM / FDOM
11. IET (estado trofico)
12. Temperatura

### Derivacao a partir de bases existentes

1. Tempo de residencia
2. Metricas integradas de pressao antropica
3. Parte das leituras de mudanca de cobertura/desmatamento a partir das series de uso do solo
