# Validação de qualidade da busca web real (ResearchScoutAgent)

- Execução anterior (antes): `run-58f79177`.
- Nova execução (depois): `run-69a620c5`.
- Teste controlado adicional: `run-control-dbd991d1`.

## Resultado geral

- Busca web real funcionou no modo atual: **mock-fallback**.
- Resultados retornados no teste controlado: `7`.
- Resultados descartados por irrelevância (teste controlado): `20`.
- Falha registrada: `all_results_filtered_as_irrelevant`.

## Comparação antes vs depois (qualidade)

- Antes: domínios prioritários (gov/inst/acadêmico) em top evidences: `0` de `4`.
- Antes: domínios não-prioritários em top evidences: `4` de `4`.
- Depois: domínios prioritários (gov/inst/acadêmico) em top evidences: `7` de `7`.
- Depois: domínios não-prioritários em top evidences: `0` de `7`.
- Depois: descartes explícitos por irrelevância no meta: `20`.

## Fontes reais acessadas no teste controlado

- **Título:** ANA - Agência Nacional de Águas e Saneamento Básico
  - URL: https://www.gov.br/ana
  - Tipo: institutional_documentation
  - Organização: ANA
  - Datasets mencionados: ['Painéis de recursos hídricos', 'Documentos técnicos de gestão']
  - Variáveis mencionadas: ['hidrologia', 'qualidade da água', 'uso da água']
- **Título:** Portal Hidroweb (SNIRH)
  - URL: https://www.snirh.gov.br/hidroweb
  - Tipo: primary_data_portal
  - Organização: Hidroweb
  - Datasets mencionados: ['Séries históricas hidrológicas', 'Estações fluviométricas']
  - Variáveis mencionadas: ['vazão', 'nível', 'chuva']
- **Título:** MapBiomas - Coleções de uso e cobertura da terra
  - URL: https://mapbiomas.org
  - Tipo: primary_data_portal
  - Organização: MapBiomas
  - Datasets mencionados: ['Coleção de Uso e Cobertura da Terra']
  - Variáveis mencionadas: ['uso da terra', 'desmatamento', 'ocupação urbana']
- **Título:** Programa Queimadas (INPE)
  - URL: https://terrabrasilis.dpi.inpe.br/queimadas/portal/
  - Tipo: primary_data_portal
  - Organização: INPE
  - Datasets mencionados: ['Focos de queimadas', 'Risco de fogo']
  - Variáveis mencionadas: ['queimadas', 'focos de calor', 'meteorologia']
- **Título:** IBGE SIDRA - Banco de tabelas estatísticas
  - URL: https://sidra.ibge.gov.br/
  - Tipo: primary_data_portal
  - Organização: IBGE
  - Datasets mencionados: ['Tabelas municipais', 'Indicadores territoriais']
  - Variáveis mencionadas: ['ocupação urbana', 'demografia', 'indicadores socioeconômicos']
- **Título:** SNIS - Painel de Saneamento
  - URL: https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/snis
  - Tipo: primary_data_portal
  - Organização: SNIS
  - Datasets mencionados: ['Indicadores de água e esgoto', 'Cobertura de coleta e tratamento']
  - Variáveis mencionadas: ['esgoto', 'resíduos', 'infraestrutura urbana']
- **Título:** SciELO e Portal CAPES - literatura sobre Tietê/Jupiá
  - URL: https://www.scielo.br/
  - Tipo: academic_literature
  - Organização: Bases Acadêmicas e Relatórios Técnicos
  - Datasets mencionados: ['Bases ambientais citadas em artigos', 'Relatórios técnicos e teses']
  - Variáveis mencionadas: ['sedimentos', 'material orgânico', 'qualidade da água']

## Falhas de rede / timeout / bloqueio

- Não houve exceção fatal nesta validação.
- O conector real ainda encontra ruído em motores genéricos; com o novo filtro, resultados fora do contexto são descartados e, quando necessário, ocorre fallback seguro para mock.

## Partes ainda em mock

- `DatasetDiscoveryAgent`, `NormalizationAgent`, `RelevanceAgent`, `AccessAgent`, `ExtractionPlanAgent` e `ReportAgent` ainda usam heurísticas/mock.
- O `MockWebResearchConnector` continua ativo como fallback de segurança.