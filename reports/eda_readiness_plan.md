# Plano de Prontidão para EDA — Projeto FREnTE / Rio Tietê

## Resumo Executivo

Este documento consolida o estado atual de prontidão das frentes analíticas do projeto FREnTE para análise exploratória de dados (EDA) sobre a dinâmica ambiental do Rio Tietê (SP).

O pipeline é organizado em camadas (raw → staging → spatial_ref + analytic → EDA) e o diagnóstico identifica três categorias de prontidão:

- **READY_FOR_EDA**: 9 frentes com dados identificados e pipeline definido
- **DERIVE_AFTER_BASES**: 1 frente derivável após as bases hidro-operacionais estarem prontas
- **NEEDS_COLLECTION_BEFORE_EDA**: 8 frentes que requerem coleta de dados antes de qualquer análise

A hipótese central do projeto é que reservatórios com maior tempo de residência e maior déficit de saneamento têm maior risco de eutrofização — o que demanda a integração de frentes hidrológicas, operacionais e antrópicas.

---

## Arquitetura em Camadas

```
data/raw/          → dados brutos, imutáveis, exatamente como vieram da fonte
     ↓
data/staging/      → dados limpos, padronizados, por fonte/domínio (.parquet / .csv.gz)
     ↓
data/spatial_ref/  → camadas geográficas de referência (EPSG:4674 SIRGAS 2000)
data/analytic/     → painéis integrados (municipio_ano, subbacia_ano, reservatorio_mes, reservatorio_ano)
     ↓
EDA/               → notebooks e scripts de análise (NUNCA consome raw/ diretamente)
```

### Chaves de Integração

| Tipo     | Chaves                                                                 |
|----------|------------------------------------------------------------------------|
| Espacial | id_bacia, id_subbacia, id_reservatorio, cod_ibge, id_ponto_monitoramento |
| Temporal | ano, mes, data, ano_mes                                                |

---

## Matriz de Prontidão

### READY_FOR_EDA (9 frentes)

| # | Frente              | Fonte Principal         | Staging Alvo                        | Painel Analítico       | Chaves            |
|---|---------------------|-------------------------|-------------------------------------|------------------------|-------------------|
| 01 | SNIS/esgoto        | SNIS MDR                | staging/snis/                       | municipio_ano          | cod_ibge, ano     |
| 02 | Uso do solo        | MapBiomas Col. 9        | staging/uso_solo/                   | municipio_ano, subbacia_ano | cod_ibge, id_subbacia, ano |
| 03 | Limites da bacia   | ANA SNIRH, CBH-AT       | staging/limites_bacia/ → spatial_ref | —                     | id_bacia, id_subbacia |
| 04 | Agropecuária       | IBGE PAM (SIDRA)        | staging/agropecuaria/               | municipio_ano          | cod_ibge, ano     |
| 05 | Desmatamento       | MapBiomas Alerta, PRODES | staging/desmatamento/              | subbacia_ano           | id_subbacia, ano  |
| 06 | Precipitação       | ANA HidroWeb, CHIRPS    | staging/precipitacao/               | subbacia_ano, reservatorio_mes | id_ponto_monitoramento, ano_mes |
| 07 | Vazão              | ANA HidroWeb, ONS       | staging/vazao/                      | subbacia_ano, reservatorio_mes | id_reservatorio, data |
| 08 | Temperatura        | INMET, ERA5-Land        | staging/temperatura/                | reservatorio_mes       | id_ponto_monitoramento, ano_mes |
| 09 | Operação reservatório | ONS dados abertos    | staging/operacao_reservatorio/      | reservatorio_mes, reservatorio_ano | id_reservatorio, data |

### DERIVE_AFTER_BASES (1 frente)

| # | Frente             | Fórmula                                             | Dependências              | Painel Alvo         |
|---|--------------------|-----------------------------------------------------|---------------------------|---------------------|
| 10 | Tempo de residência | TR (dias) = Volume_armazenado (m³) / Vazao_defluente (m³/s) / 86400 | EDA/07 + EDA/09 prontos | reservatorio_mes (nova coluna) |

### NEEDS_COLLECTION_BEFORE_EDA (8 frentes)

| Frente                        | Motivo                        | Fonte Potencial                        |
|-------------------------------|-------------------------------|----------------------------------------|
| DBO/DQO                       | Sem dados coletados           | CETESB Infoáguas, ANA SNIRH            |
| Clorofila-a                   | Sem dados coletados           | CETESB, imagens Sentinel-2             |
| Índices ópticos (CDOM, turbidez) | Sem dados coletados        | Sensoriamento remoto, CETESB           |
| Queimadas                     | Sem dados coletados           | INPE BDQueimadas, MapBiomas Fogo       |
| MDE (modelo digital de elevação) | Sem dados coletados       | SRTM 30m, ALOS PALSAR, Copernicus DEM  |
| SR qualidade da água          | Sem dados coletados           | Sentinel-2 MSI, Landsat Collection 2   |
| Resíduos sólidos              | Sem dados coletados           | SNIS RSU, CETESB inventário            |
| Batimetria                    | Sem dados / dado restrito     | ANA, SABESP, estudos acadêmicos        |

---

## Estrutura data/raw/

```
data/raw/
├── README.md
├── snis/               ← CSV/XLSX anuais SNIS (2000–2022)
├── mapbiomas/          ← GeoTIFF + CSV MapBiomas Col. 9 (1985–2023)
├── ibge_pam/           ← tabelas SIDRA PAM por município/ano
├── precipitacao/       ← séries diárias ANA HidroWeb / CHIRPS
├── vazao/              ← séries diárias ANA HidroWeb / ONS
├── temperatura/        ← séries diárias INMET / ERA5-Land
├── operacao_reservatorio/ ← séries ONS: volume, cota, vazões
├── limites_bacia/      ← shapefiles ANA SNIRH ottobacias, BHO
├── desmatamento/       ← shapefiles PRODES / MapBiomas Alerta
└── artigos_pdf/        ← referência bibliográfica (não entra no EDA)
```

---

## Estrutura data/staging/

```
data/staging/
├── README.md
├── snis/
│   └── snis_municipios_serie.parquet
│       Schema: cod_ibge | municipio | ano | pop_total | pop_atendida_agua | pop_atendida_esgoto |
│               indice_coleta_esgoto | indice_tratamento_esgoto | volume_esgoto_coletado_m3 | volume_esgoto_tratado_m3
├── uso_solo/
│   ├── uso_solo_municipio_ano.parquet
│   └── uso_solo_subbacia_ano.parquet
│       Schema: cod_ibge | id_subbacia | ano | classe_mapbiomas | area_ha | proporcao_pct
├── agropecuaria/
│   └── pam_municipio_ano.parquet
│       Schema: cod_ibge | ano | cultura | area_colhida_ha | producao_t | rendimento_kgha
├── desmatamento/
│   └── desmatamento_subbacia_ano.parquet
│       Schema: id_subbacia | ano | area_desmatada_ha | fonte
├── precipitacao/
│   ├── precip_estacao_dia.parquet
│   └── precip_subbacia_mes.parquet
├── vazao/
│   ├── vazao_estacao_dia.parquet
│   └── vazao_reservatorio_mes.parquet
├── temperatura/
│   └── temp_estacao_dia.parquet
│       Schema: id_ponto_monitoramento | data | temp_max_c | temp_min_c | temp_media_c
├── operacao_reservatorio/
│   └── operacao_reservatorio_dia.parquet
│       Schema: id_reservatorio | nome_reservatorio | data | volume_util_pct | cota_m |
│               vazao_afluente_m3s | vazao_defluente_m3s | volume_armazenado_hm3
└── limites_bacia/
    └── [GeoPackages intermediários antes de ir para spatial_ref/]
```

---

## Estrutura data/spatial_ref/

```
data/spatial_ref/                        ← todas em EPSG:4674 (SIRGAS 2000)
├── README.md
├── bacia/
│   └── bacia_tiete.gpkg                 ← polígono único da bacia
├── subbacias/
│   └── subbacias_tiete.gpkg             ← sub-bacias Otto nível 6/7
├── reservatorios/
│   └── reservatorios_tiete.gpkg         ← 7 reservatórios em cascata
├── municipios_area_estudo/
│   └── municipios_tiete.gpkg            ← municípios com >= 10% na bacia
├── hidrografia/
│   └── hidrografia_tiete.gpkg           ← rede de drenagem BHO
└── pontos_monitoramento/
    └── estacoes_monitoramento.gpkg      ← estações ANA HidroWeb
```

---

## Estrutura data/analytic/

```
data/analytic/
├── README.md
├── municipio_ano/
│   └── municipio_ano.parquet
│       Chaves: cod_ibge | municipio | ano
│       Fontes: snis + uso_solo + agropecuaria + desmatamento + precipitacao + temperatura
├── subbacia_ano/
│   └── subbacia_ano.parquet
│       Chaves: id_subbacia | ano
│       Fontes: desmatamento + uso_solo + precipitacao + vazao
├── reservatorio_mes/
│   └── reservatorio_mes.parquet
│       Chaves: id_reservatorio | nome_reservatorio | ano_mes
│       Fontes: operacao_reservatorio + vazao + precipitacao + temperatura
│       Derivada: tempo_residencia_dias
└── reservatorio_ano/
    └── reservatorio_ano.parquet
        Chaves: id_reservatorio | nome_reservatorio | ano
        Origem: agregação de reservatorio_mes
```

---

## Estrutura EDA/

```
EDA/
├── README.md                    ← ordem de execução e regras de consumo
├── 01_snis_esgoto/              ← READY — cobertura de saneamento por município
├── 02_uso_do_solo/              ← READY — evolução MapBiomas 1985–2023
├── 03_limites_bacia/            ← READY — base geográfica (EXECUTAR PRIMEIRO)
├── 04_agropecuaria/             ← READY — IBGE PAM cana e outras culturas
├── 05_desmatamento/             ← READY — PRODES/MapBiomas Alerta por sub-bacia
├── 06_precipitacao/             ← READY — regime pluviométrico ANA/CHIRPS
├── 07_vazao/                    ← READY — hidrologia ANA HidroWeb / ONS
├── 08_temperatura/              ← READY — regime térmico INMET / ERA5
├── 09_operacao_reservatorio/    ← READY — operação dos 7 reservatórios ONS
├── 10_tempo_residencia/         ← DERIVE — após 07 + 09 prontos
└── 99_integracao/               ← INTEGRAÇÃO — após todas as frentes 01–09
```

---

## Plano de Integração entre Frentes

### Integração 1 — Pressão Antrópica por Sub-bacia
- **Entradas**: staging/snis + staging/uso_solo + staging/agropecuaria + staging/desmatamento
- **Saída**: `analytic/subbacia_ano` + `painel_pressao_antrópica_subbacia.parquet`
- **Cola espacial**: spatial_ref/subbacias + spatial_ref/municipios_area_estudo

### Integração 2 — Balanço Hídrico dos Reservatórios
- **Entradas**: staging/precipitacao + staging/vazao + staging/temperatura + staging/operacao_reservatorio
- **Saída**: `analytic/reservatorio_mes` + `painel_hidrologico_reservatorio.parquet`
- **Cola espacial**: spatial_ref/reservatorios + spatial_ref/pontos_monitoramento

### Integração 3 — Risco de Eutrofização (Hipótese Central)
- **Entradas**: analytic/reservatorio_mes (TR) + painel_pressao_antrópica_subbacia
- **Saída**: `painel_risco_eutrofizacao.parquet`
- **Lógica**: reservatórios com TR elevado + alta carga de esgoto sem tratamento + alta área agrícola = maior risco

---

## Backlog de Coleta

### Prioridade Alta (bloqueiam hipóteses centrais)
| Frente           | Ação Necessária                              | Prazo Estimado |
|------------------|----------------------------------------------|----------------|
| DBO/DQO          | Acessar CETESB Infoáguas para séries históricas | 2–4 semanas  |
| Clorofila-a      | Acessar CETESB + explorar Sentinel-2 GEE     | 3–6 semanas    |
| Queimadas        | Download INPE BDQueimadas por bbox da bacia  | 1–2 semanas    |

### Prioridade Média
| Frente           | Ação Necessária                              |
|------------------|----------------------------------------------|
| Índices ópticos  | Buscar literatura + dados CETESB disponíveis |
| SR qualidade água | Script GEE para Sentinel-2 + Landsat        |
| Resíduos sólidos | SNIS RSU módulo municipal                    |

### Prioridade Baixa / Dado Restrito
| Frente     | Nota                                             |
|------------|--------------------------------------------------|
| MDE        | SRTM disponível — priorizar se análise morfológica for necessária |
| Batimetria | Dado restrito — negociar com ANA / SABESP        |

---

## Ordem de Execução Recomendada

```
FASE 1 — Base Geográfica (pré-requisito de tudo)
  └── EDA/03_limites_bacia → gera spatial_ref/ completo

FASE 2 — Pressões Antrópicas (paralelo)
  ├── EDA/01_snis_esgoto
  ├── EDA/02_uso_do_solo
  ├── EDA/04_agropecuaria
  └── EDA/05_desmatamento

FASE 3 — Climatologia e Hidrologia (paralelo)
  ├── EDA/06_precipitacao
  ├── EDA/07_vazao
  └── EDA/08_temperatura

FASE 4 — Operação do Sistema
  └── EDA/09_operacao_reservatorio

FASE 5 — Variável Derivada (depende de FASE 3 + FASE 4)
  └── EDA/10_tempo_residencia

FASE 6 — Integração Final (depende de todas as fases anteriores)
  └── EDA/99_integracao
```

---

## Checklist de Aderência à Arquitetura

- [ ] Nenhum notebook em EDA/ lê arquivos de data/raw/ diretamente
- [ ] Todos os arquivos em staging/ têm schema documentado no README da subpasta
- [ ] Todas as camadas em spatial_ref/ estão em EPSG:4674 (SIRGAS 2000)
- [ ] Todos os panéis em analytic/ têm as chaves de integração definidas
- [ ] cod_ibge sempre com 7 dígitos
- [ ] Datas sempre no formato YYYY-MM-DD
- [ ] ano_mes sempre no formato YYYY-MM
- [ ] id_reservatorio usa lista fechada: {BARRA_BONITA, BARIRI, IBITINGA, PROMISSAO, NOVA_AVANHANDAVA, TRES_IRMAOS, JUPIA}
- [ ] EDA/10 só é iniciada após EDA/07 e EDA/09 completamente prontos
- [ ] EDA/99 só é iniciada após todas as frentes 01–09 com staging e analytic prontos
- [ ] Frentes NEEDS_COLLECTION_BEFORE_EDA não têm notebooks criados ainda (evitar estrutura vazia)
