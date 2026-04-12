# Clarks Hill System Round - Agent Handoffs

Este pacote prepara a proxima rodada para o sistema `Hartwell -> Russell -> Thurmond`.

Objetivo geral:
- coletar, normalizar, analisar e apresentar o contexto do rio Savannah e do sistema Hartwell-Russell-Thurmond
- manter `J. Strom Thurmond` como foco sedimentologico
- incorporar `Hartwell` e `Russell` como controles operacionais a montante
- tratar o rio como objeto principal de analise e os reservatorios como estrutura explicativa de suporte

Sequencia esperada:
1. `Runner` executa a rodada geral de descoberta via API sem Firecrawl e monta o handoff para o Harvester
2. `Harvester` coleta os dados brutos e organiza os artefatos em `data/runs/{run-id}/`
3. `Analyst` transforma a coleta em `data/staging/`, `data/analytic/`, `EDA/clarks_hill/` e figuras reais
4. `Narrator` atualiza `docs/clarks-hill/index.html` a partir do contexto estruturado e das figuras produzidas

Reservatorios obrigatorios desta rodada:
- `Hartwell`
- `Richard B. Russell`
- `J. Strom Thurmond`

Regra editorial:
- o relatorio final deve ser `river-first`
- hero, figuras centrais e interpretacao principal devem priorizar o rio
- os reservatorios devem aparecer como anexos analiticos ou blocos explicativos de suporte
- quando a integracao ainda estiver parcial, o HTML deve explicitar quais reservatorios ja entraram e quais continuam pendentes
- o HTML deve distinguir explicitamente a janela alvo de 20 anos da cobertura efetivamente retornada por cada fonte, reservatorio, metrica e figura
- nenhuma cobertura parcial pode ser apresentada como se fosse serie completa

Arquivos deste pacote:
- `runner_scope.md`
- `harvester_scope.md`
- `analyst_scope.md`
- `narrator_scope.md`
