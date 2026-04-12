# Narrator Scope

Agent alvo:
- `relatorio_html`
- nickname esperado: `Narrator`

Objetivo desta rodada:
- construir o HTML final preservando o padrao visual do projeto
- representar o rio Savannah como objeto principal de analise

Escopo individual:
- construir o HTML final preservando o padrao visual do projeto
- o relatorio final deve ser `river-first`
- hero, figuras centrais e interpretacao principal devem centrar o rio Savannah
- Hartwell, Russell e Thurmond devem entrar como anexos analiticos ou blocos explicativos de suporte ao comportamento do rio
- Thurmond continua como foco sedimentologico, mas o HTML precisa mostrar com honestidade o papel de Hartwell e Russell como controles de operacao a montante
- quando o EDA ainda estiver parcial, manter o layout e sinalizar claramente quais reservatorios estao integrados e quais ainda estao pendentes
- consumir somente contexto estruturado e figuras reais entregues pelo `Analyst`
- nao inventar metricas ou comparacoes ausentes
- deixar clara, em texto e legendas quando necessario, a diferenca entre a janela alvo de 20 anos e a cobertura efetivamente retornada por cada fonte, reservatorio ou figura

Entregavel esperado quando liberado:
- `docs/clarks-hill/index.html` atualizado com narrativa `river-first`, usando os reservatorios como suporte explicativo e com honestidade sobre integracao parcial ou completa dos tres reservatorios

Restricoes:
- nao redesenhar o padrao visual do projeto
- nao usar placeholders que parecam dado real
- nao promover comparacoes entre reservatorios sem figura ou tabela real
- nao puxar dados brutos diretamente; consumir somente o handoff do `Analyst`
- nao apresentar cobertura parcial como se fosse serie completa

Condicao atual:
- por enquanto, apenas absorver o escopo, confirmar dominio e aguardar o handoff do `Analyst` ou do chat principal
