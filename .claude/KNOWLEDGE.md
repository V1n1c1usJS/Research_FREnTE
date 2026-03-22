# KNOWLEDGE.md

> Este arquivo é lido automaticamente pelo Claude Code em cada sessão.
> Ele contém o conhecimento de domínio do **Projeto 100K** e as orientações
> para evolução do pipeline **Research_FREnTE**.
>
> Última atualização: 2026-03-21

---

## 1) O que é o Projeto 100K

Projeto de pesquisa ambiental que investiga como atividades humanas na bacia
do Rio Tietê (São Paulo → Três Lagoas) influenciam o comportamento do material
orgânico em reservatórios ao longo do tempo.

**Pergunta central:** como as pressões antrópicas na bacia afetam a dinâmica
do material orgânico nos reservatórios em cascata do Tietê?

**Princípio fundamental:** tudo que está a montante de Jupiá influencia Jupiá.
A área de coleta não é uma faixa estreita ao longo do rio, mas toda a bacia
de drenagem do Tietê.

---

## 2) Delimitação geográfica

### Bounding box (SIRGAS 2000 / EPSG:4674)

```
Norte (lat max):  -20.50
Sul   (lat min):  -24.00
Oeste (lon min):  -52.20
Leste (lon max):  -45.80
Área aproximada:  ~72.000 km²
```

### Zonas funcionais

| Zona | Nome | Papel | UGRHIs | Pressão | Municípios-chave |
|------|------|-------|--------|---------|------------------|
| A | RMSP | Fonte de carga | 06 | Máxima | São Paulo, Guarulhos, Osasco, Barueri, Pirapora do Bom Jesus |
| B | Médio Tietê | Transição agro | 10, 13 | Alta | Sorocaba, Piracicaba, Bauru, Barra Bonita, Jaú, Ibitinga |
| C | Baixo Tietê | Diluição | 16, 19 | Moderada | Lins, Penápolis, Araçatuba, Promissão, Buritama |
| D | Confluência | Receptor final | — | Acumulada | Pereira Barreto, Ilha Solteira, Castilho, Três Lagoas (MS) |

### Reservatórios em cascata (montante → jusante)

Ponte Nova → **Barra Bonita** → Bariri → Ibitinga → **Promissão** → Nova Avanhandava → Três Irmãos → **Jupiá**

Tempos de residência de referência: Barra Bonita ~30-60 dias, Três Irmãos ~120-200 dias.

### Afluentes urbanos críticos (Zona A)

Rios Pinheiros, Tamanduateí, córregos Aricanduva, Cabuçu de Baixo, Pirajussara, Ribeirão dos Meninos.

---

## 3) Arquitetura de dados — 4 níveis hierárquicos

A coleta de dados segue uma hierarquia causal: o nível 1 define o cenário,
o nível 2 identifica as forças, o nível 3 mostra onde elas se acumulam,
e o nível 4 mede a resposta do sistema.

### Nível 1 — Contexto regional (macro)

| Variável | Fonte primária | URL | Formato | Resolução |
|----------|---------------|-----|---------|-----------|
| Limites da bacia | ANA (ottobacias) | metadados.snirh.gov.br/geonetwork | SHP, GPKG | Vetorial |
| Relevo (MDE) | SRTM / ALOS PALSAR | earthexplorer.usgs.gov / search.asf.alaska.edu | GeoTIFF | 12.5-30m |
| Geologia | CPRM | geosgb.sgb.gov.br | SHP, PDF | 1:250k |
| Solos | EMBRAPA | embrapa.br/solos | SHP, PDF | 1:250k-1M |
| Precipitação | ANA HidroWeb / CHIRPS | snirh.gov.br/hidroweb / data.chc.ucsb.edu/products/CHIRPS-2.0 | CSV, GeoTIFF | Pontual / ~5km |
| Temperatura | INMET / ERA5 | bdmep.inmet.gov.br / cds.climate.copernicus.eu | CSV, NetCDF | Pontual / ~30km |
| Uso e cobertura | MapBiomas col. 9 | brasil.mapbiomas.org | GeoTIFF, GEE | 30m, anual 1985-2023 |
| Demografia | IBGE Censo/SIDRA | sidra.ibge.gov.br | CSV, XLSX, API | Municipal/setor censitário |
| Vazão | ANA HidroWeb | snirh.gov.br/hidroweb | CSV, TXT | Diária |

### Nível 2 — Pressões antrópicas (meso)

| Variável | Fonte primária | URL | Formato | Indicadores-chave |
|----------|---------------|-----|---------|-------------------|
| Saneamento/esgoto | SNIS | app4.mdr.gov.br/serieHistorica | XLSX, CSV | IN046, IN056, ES005, ES006 |
| Qualidade água SP | CETESB QUALAR | qualar.cetesb.sp.gov.br | CSV, PDF | IQA, IET, DBO, OD |
| Desmatamento | INPE PRODES/DETER | terrabrasilis.dpi.inpe.br | SHP, GeoTIFF | Incremento anual |
| Desmat. Mata Atlântica | SOS MA / MapBiomas Alerta | alerta.mapbiomas.org | SHP, GeoJSON | Alertas por bioma |
| Queimadas | INPE BDQueimadas | terrabrasilis.dpi.inpe.br/queimadas | CSV, SHP | Focos de calor (AQUA_M-T) |
| Queimadas global | NASA FIRMS | firms.modaps.eosdis.nasa.gov | CSV | MODIS ~1km, VIIRS ~375m |
| Agropecuária | IBGE PAM/PPM | sidra.ibge.gov.br (tabelas 1612, 5457) | CSV | Área plantada, produção cana |
| Resíduos sólidos | SNIS mod. RS / CETESB IQR | cetesb.sp.gov.br/residuossolidos | XLSX, PDF | IQR, geração per capita |
| APP/ocupação | SICAR/CAR | car.gov.br/publico/municipios/downloads | SHP, CSV | Sobreposição uso × APP |

### Nível 3 — Reservatórios e qualidade da água (ponte)

| Variável | Fonte primária | URL | Formato | Parâmetros |
|----------|---------------|-----|---------|------------|
| Qualidade água | CETESB QUALAR | qualar.cetesb.sp.gov.br | CSV, PDF | IQA, IET, OD, DBO, DQO, Chl-a, PT, NT, turbidez, COT |
| Qualidade água | ANA SNIRH | snirh.gov.br/hidroweb | CSV | Estações de qualidade |
| Operação | ONS | ons.org.br / sintegre.ons.org.br | CSV, API | Vazão afluente/defluente |
| Nível/volume | SAR/ANA | ana.gov.br/sar | CSV | Nível, volume, % útil |
| Batimetria | Artigos, EIA/RIMA | Google Scholar | PDF | Área, profundidade, volume por cota |

Operadoras: AES Tietê (Barra Bonita→Nova Avanhandava), CTG Brasil (Jupiá, Três Irmãos).

### Nível 4 — Material orgânico e séries temporais (micro)

| Variável | Fonte | Estratégia de busca | Parâmetros |
|----------|-------|-------------------|------------|
| MOD/MOP/CDOM | Artigos científicos | Scholar: "CDOM" "Tietê" OR "Barra Bonita" | a(254), a(355), SUVA254, E2:E3, PARAFAC |
| COT/COD/COP | CETESB + artigos | QUALAR + Scholar: "DOC" "reservoir" "Tietê" | Carbono orgânico total, dissolvido, particulado |
| Biogeoquímica | CETESB | qualar.cetesb.sp.gov.br | Chl-a, PT, NT, OD, DBO, DQO |
| Sensoriamento remoto | Sentinel-2, Landsat | GEE: S2_SR_HARMONIZED, LC08/C02/T1_L2 | NDCI, turbidez, CDOM, Secchi, TSW |
| Séries temporais | Compilação dos acima | Mann-Kendall, Sen's slope, change-point | Tendência, sazonalidade, pontos de inflexão |
| Índices integrativos | CETESB | cetesb.sp.gov.br/aguas-interiores | IET, IQA, IVA, razão DBO/DQO |

---

## 4) Tabela consolidada de fontes

| Sigla | URL principal | Tipo de dado |
|-------|--------------|-------------|
| ANA | snirh.gov.br/hidroweb | Hidrologia, qualidade água |
| CETESB | cetesb.sp.gov.br/aguas-interiores | Qualidade água SP |
| QUALAR | qualar.cetesb.sp.gov.br | Dados brutos qualidade |
| INPE | terrabrasilis.dpi.inpe.br | Desmatamento, queimadas |
| MapBiomas | brasil.mapbiomas.org | Uso e cobertura do solo |
| IBGE | sidra.ibge.gov.br | Demografia, agropecuária |
| SNIS | app4.mdr.gov.br/serieHistorica | Esgoto, resíduos |
| ONS | ons.org.br | Operação reservatórios |
| SAR/ANA | ana.gov.br/sar | Nível, volume reservatórios |
| INMET | bdmep.inmet.gov.br | Clima |
| CHIRPS | data.chc.ucsb.edu/products/CHIRPS-2.0 | Precipitação raster |
| ERA5 | cds.climate.copernicus.eu | Clima global |
| USGS | earthexplorer.usgs.gov | SRTM, Landsat |
| ESA | dataspace.copernicus.eu | Sentinel-2 |
| GEE | earthengine.google.com | Processamento SR |
| CPRM | geosgb.sgb.gov.br | Geologia |
| SICAR | car.gov.br | APP, imóveis rurais |
| SINIR | sinir.gov.br | Resíduos sólidos |
| FIRMS | firms.modaps.eosdis.nasa.gov | Focos de calor |

---

## 5) Diagnóstico do pipeline Research_FREnTE

### O que está bom (não mexer)

- Arquitetura de 11 etapas (coleta → categorização → validação → discovery → normalização → relevância → acesso → relatório)
- JSONs intermediários entre etapas
- Schemas Pydantic com validação
- Separação coleta (Perplexity) vs. interpretação (agentes)
- CLI flexível com flags de override

### Gaps resolvidos por configuração (sem mudança de código)

| Gap | Problema | Solução |
|-----|----------|---------|
| Contexto genérico | `geographic_scope: []` vazio, thematic_axes genéricos | Usar `config/context_100k.yaml` |
| Trilhas desconectadas | 5 trilhas por tipo de fonte, sem foco temático | Usar `config/tracks_100k.yaml` (12 trilhas por nível) |
| Keywords ausentes | task_prompts sem nomes de fontes/URLs | Trilhas 100K incluem fontes, URLs e parâmetros por nome |

### Gaps que requerem código (sprints futuros)

| Gap | O que falta | Sugestão |
|-----|-------------|----------|
| Relevância sem lógica causal | RelevanceAgent não sabe que Zona A > Zona C em peso causal | Adicionar `zone_weights: dict[str, float]` ao context schema |
| Sem validação cruzada | SourceValidationAgent não cruza fontes (SNIS×CETESB, SR×campo) | Criar CrossValidationAgent ou estender o existente |

### Melhorias incrementais sugeridas

| Melhoria | Esforço | Onde mexer |
|----------|---------|-----------|
| `--limit 40` para 100K | Trivial | Flag CLI |
| Campo `hierarchy_level` nas trilhas | Baixo | `src/schemas/records.py` |
| `--dry-run` para validar config | Baixo | `src/main.py` |
| Knowledge base em JSON para ingestão | Médio | Novo arquivo + flag `--knowledge-file` |
| Campo `data_format` nos datasets | Baixo | `DatasetDiscoveryAgent` |
| Cache de sessões Perplexity | Médio | `PerplexityPlaywrightCollector` |

---

## 6) Instruções para o Claude Code

### Ao modificar configuração

- Sempre validar YAMLs contra os schemas em `src/schemas/records.py`
- `context_100k.yaml` segue `PerplexityResearchContextRecord`
- `tracks_100k.yaml` segue lista de `PerplexityResearchTrackRecord`
- Se adicionar campos novos, atualizar o schema Pydantic primeiro

### Ao modificar agentes

- Prompts vivem em `prompts/*.yaml` — editar lá, não inline no código
- O `RelevanceAgent` usa `geographic_scope` e `thematic_axes` do contexto — qualquer enriquecimento desses campos melhora o scoring
- O `SourceValidationAgent` roda ANTES do discovery — mudanças nele afetam toda a cadeia downstream
- Preservar JSONs intermediários — são a trilha de auditoria

### Ao adicionar funcionalidade

- Seguir padrão incremental: mudanças pequenas e rastreáveis
- Novos agentes herdam de `src/agents/base.py` e usam `load_prompt()`
- Novos schemas vão em `src/schemas/records.py` ou `src/schemas/settings.py`
- Testes obrigatórios para coleta, categorização, consolidação e CLI

### Prioridade de coleta de dados (ordem sugerida)

1. Delimitação da bacia (sem isso não se recorta nada)
2. Uso e cobertura do solo (MapBiomas — série longa, alta resolução)
3. Qualidade da água (CETESB — dado mais direto sobre reservatórios)
4. Saneamento/esgoto (SNIS — maior pressão antrópica na RMSP)
5. Dados operacionais dos reservatórios (ONS/SAR)
6. Clima (precipitação — driver de transporte)
7. Demais variáveis em paralelo

### Validações cruzadas que o pipeline deveria fazer

1. Esgoto (SNIS) × DBO medida (CETESB) → verifica consistência
2. Desmatamento (INPE/MapBiomas) × turbidez (CETESB) → verifica causa-efeito
3. Clorofila-a in situ (CETESB) × clorofila-a satélite (Sentinel) → calibra SR
4. Uso do solo (MapBiomas) × COT nos reservatórios → testa hipótese central

### Comando de referência para execução 100K

```bash
python -m src.main run \
  --query "impacto antropico materia organica reservatorios cascata tiete sao paulo tres lagoas" \
  --context-file config/context_100k.yaml \
  --tracks-file config/tracks_100k.yaml \
  --max-searches 12 \
  --limit 40 \
  --llm-mode auto
```

### Formatos mais comuns encontrados nas fontes

- **SHP** (.shp+.dbf+.shx+.prj) → dados vetoriais
- **GeoTIFF** (.tif) → dados raster (MDE, uso do solo, satélite)
- **CSV/XLSX** → dados tabulares (estações, indicadores municipais)
- **NetCDF** (.nc) → dados climáticos gridados
- **PDF** → relatórios CETESB (requer parsing/OCR — sinalizar no pipeline)

### Cuidados técnicos

- Sistema de coordenadas padrão brasileiro: SIRGAS 2000
- Dados CETESB frequentemente vêm em PDF — considerar ferramentas de extração
- MapBiomas é melhor acessado via Google Earth Engine para grandes áreas
- SNIS pode ter lacunas municipais — sinalizar municípios sem dados
- Sensoriamento remoto: máscara de nuvens é obrigatória antes de análise
- Separar contribuição Tietê vs. Paraná ao analisar dados de Jupiá
