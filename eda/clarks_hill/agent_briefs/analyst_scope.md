# Analyst Scope

Agent alvo:

- `eda_reservatorio`
- arquivo: `.codex/agents/eda-reservatorio.toml`

Missao desta rodada:

- trabalhar no padrao do Tiete, mas para o rio Savannah com frame `river-first`
- tratar o rio como storyline principal e como objeto central da interpretacao
- tratar `Thurmond` como reservatorio-alvo da interpretacao sedimentologica
- tratar `Hartwell` e `Russell` como controles operacionais a montante
- montar comparacao entre os tres reservatorios apenas quando isso ajudar a explicar o sinal do rio
- incorporar poluentes e pressoes ambientais como camada central do EDA, nao como anexo opcional
- na proxima coleta, priorizar water quality do rio, poluentes, pressoes ambientais, gauges adicionais do `mainstem` e series operacionais longas de suporte
- lembrar que o deck cientifico principal e sedimentocentrico: esta EDA existe para explicar o contexto externo dos sedimentos, nao para substituir a pergunta da apresentacao por uma historia puramente hidrologica

Entregaveis quando os dados chegarem:

- `EDA/clarks_hill/` atualizado para escopo sistemico
- scripts Python reproduziveis
- `data/staging/...` e `data/analytic/...` apenas quando houver derivacao real
- figuras comparativas entre reservatorios quando possivel
- figuras e tabelas que mostrem o rio, suas pressoes e seus poluentes como eixo principal
- `report_context.json` consistente para o Narrator

Camadas analiticas esperadas:

- sinal do rio: hidrologia, water quality, continuidade espacial e cobertura temporal
- bacia e pressoes: clima, uso do solo, paisagem, batimetria, poluentes, dischargers, impairments e contexto de bacia
- operacao: pool elevation, storage, inflow, outflow, releases como modulacao explicativa
- tempo de residencia: Thurmond condicionado por Hartwell e Russell
- water quality: comparavel entre reservatorios quando houver equivalencia real
- bacia e morfometria: suporte para interpretar zonas deposicionais

Regras:

- nao fabricar equivalencia entre reservatorios
- nao deixar operacao de reservatorios virar protagonista quando a camada principal for de rio
- nao deixar os reservatorios reconfigurarem o estudo como se o objeto principal nao fosse o rio
- nao deixar o frame `river-first` apagar a motivacao sedimentologica principal do estudo
- se `Hartwell` ou `Russell` ainda nao tiverem dado comparavel, explicitar isso no README, nas figuras e no `report_context`
- nao inventar conclusoes sistemicas so com Thurmond
- preservar separacao entre bruto, staging, analytic e assets de EDA
- priorizar scripts Python claros e reproduziveis
- tratar 20 anos como horizonte analitico alvo e mostrar quando a disponibilidade real ficar abaixo disso
- explicitar a defasagem temporal por `reservatorio`, `fonte` e `variavel`
- materializar uma matriz de cobertura temporal para alimentar README, figuras e `report_context`

Definicao de sucesso desta rodada:

- pipeline analitico pronto para receber a coleta sistemica
- comparacao real entre reservatorios quando a coleta permitir
- lacunas explicitadas quando a equivalencia ainda nao existir
- matriz de completude temporal comparada ao alvo de 20 anos

## Benchmark visual e backlog minimo

Benchmark usado:

- `https://v1n1c1usjs.github.io/Research_FREnTE/`
- referencia canonica local: `EDA/operacao_reservatorio/apresentacao_reservatorios.html`

Leitura do benchmark:

- o Tiete trabalha com mais figuras e mais tipos de leitura visual
- cada figura cruza camadas diferentes e fecha com takeaway forte
- o HTML nao para em cobertura de fonte; ele mostra comportamento, relacao e implicacao

Portanto, para Clarks Hill, a proxima passada do Analyst deve elevar a densidade analitica do relatorio.

Obrigacoes adicionais desta rodada:

- usar `analise_sedimentos/Analise_sedimentos_Clarks_Hill_Lake.ipynb` e a planilha Master Data como insumos formais do EDA
- extrair ou recriar em Python figuras sedimentologicas relevantes, em vez de deixar esse material apenas como texto-resumo
- entregar mais graficos cruzando informacoes, nao apenas paineis de cobertura e status

Backlog minimo de figuras a priorizar:

- uma figura longitudinal do sistema, cruzando alto rio, reservatorios e baixo rio com as estacoes realmente disponiveis
- uma figura temporal cruzando hidrologia do rio com variaveis de qualidade da agua mais fortes no eixo Savannah
- uma figura de cruzamento entre operacao dos reservatorios e proxies de baixa energia ou deposicao
- uma figura sedimentologica reproduzida do notebook, mostrando textura por sitio ou score deposicional
- uma figura de relacao entre `Fe`, `%Clay`, `D50`, `%Carbon` e profundidade, mesmo que em forma de painel de dispersao
- uma figura final de sintese que una `rio -> regulacao -> resposta sedimentologica`

Regras editoriais adicionais:

- cada figura nova precisa ter `o que mostra`, `interpretacao analitica` e `takeaway`
- sempre preferir graficos de relacao real entre variaveis a cards descritivos quando houver dado suficiente
- nao usar o notebook de sedimentos apenas como conclusao textual; ele precisa aparecer tambem em imagens relevantes para o relatorio
- o backlog visual precisa mostrar o rio e as pressoes sobre o rio com a mesma centralidade que o Tiete teve na referencia canonica
- o backlog visual tambem precisa deixar claro por que os sedimentos importam: nutrientes, carga interna, sustentabilidade do reservatorio e preocupacao com blooms periodicos
