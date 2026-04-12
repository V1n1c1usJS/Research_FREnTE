# Analyst Scope

Agent alvo:
- `eda_reservatorio`
- nickname esperado: `Analyst`

Objetivo desta rodada:
- transformar a coleta do rio Savannah e de suas estruturas `Hartwell -> Russell -> Thurmond` em EDA reproduzivel
- preparar figuras e contexto estruturado para o `Narrator`
- estruturar a leitura principal como `river-first`, usando os reservatorios como mecanismo explicativo dentro do proprio rio

Escopo individual:
- receber apenas dados reais entregues pelo `Harvester`
- atualizar `EDA/clarks_hill/` no padrao canonico do repositorio
- tratar Hartwell, Russell e Thurmond como estruturas do sistema fluvial, nao como protagonistas independentes
- manter Thurmond como foco sedimentologico
- organizar o contexto para que o rio Savannah seja o objeto principal da interpretacao, no mesmo espirito do Tiete
- produzir tabelas e figuras que mostrem com honestidade:
  - leitura principal do rio e de sua variabilidade ao longo da cascata
  - poluentes, pressoes ambientais e sinais de degradacao que influenciem o rio
  - operacao individual por reservatorio
  - comparacao entre reservatorios quando os dados existirem
  - condicionamento de Thurmond pela regulacao a montante
- gerar `report_context.json` pronto para o HTML
- carregar no contexto a diferenca entre janela alvo de 20 anos e cobertura efetivamente disponivel por fonte, reservatorio, metrica e figura

Saidas esperadas:
- `EDA/clarks_hill/process_context_sources.py`
- `EDA/clarks_hill/generate_figures.py`
- `EDA/clarks_hill/generate_presentation.py` quando aplicavel
- `EDA/clarks_hill/figures/*.png`
- `EDA/clarks_hill/report_context.json`
- derivacoes reais em `data/staging/clarks_hill/` e `data/analytic/clarks_hill/`

Escopo analitico minimo:
- series e figuras que sustentem uma narrativa principal do rio Savannah
- series e figuras que sustentem uma narrativa de pressoes ambientais e poluentes sobre o rio
- series operacionais de Hartwell, Russell e Thurmond
- comparacao de pool elevation, storage, inflow e outflow quando houver
- tempo de residencia e contexto hidrodinamico de Thurmond condicionado pelo sistema
- contexto de qualidade da agua disponivel, priorizando Thurmond
- inventario explicito das lacunas por reservatorio e por tema
- inventario explicito da cobertura real de cada serie frente a janela alvo do estudo

Restricoes:
- nao inventar metricas, comparacoes ou cobertura onde faltarem dados
- nao promover um reservatorio como integrado sem tabela ou figura real correspondente
- nao trocar a pergunta principal do estudo de "como o rio se comporta" para "como os reservatorios se comportam"
- nao misturar bruto com staging ou analytic
- nao fechar o HTML final
- nao rotular figura ou serie como historica completa se a cobertura efetiva for parcial

Condicao de parada:
- parar quando houver figuras reais e `report_context.json` utilizavel pelo `Narrator`
- se Hartwell ou Russell continuarem sem integracao minima, isso deve aparecer de forma explicita no contexto entregue

## Reforco apos benchmark visual

Comparar sempre com o benchmark do Tiete:

- `https://v1n1c1usjs.github.io/Research_FREnTE/`
- `EDA/operacao_reservatorio/apresentacao_reservatorios.html`

Nao entregar Clarks Hill com menos densidade analitica do que esse benchmark sem justificar a lacuna.

Na proxima passada, priorizar:

- mais figuras de relacao entre variaveis do rio e da cascata
- figuras sedimentologicas reproduzidas de `analise_sedimentos`
- paineis visuais que fechem a ponte `rio -> operacao -> deposicao`
- imagens relevantes extraidas ou recriadas do notebook de sedimentos para o HTML final
