# Savannah System Round Prep

Escopo desta preparacao:
- sistema `Hartwell -> Russell -> Thurmond`
- eixo analitico `river-first`
- rodada ainda nao executada
- objetivo: deixar cada agent com dominio individual claro antes da liberacao do chat principal

Reservatorios alvo:
- `Hartwell`
- `Russell`
- `Thurmond`

Regra obrigatoria do usuario:
- `des.sc.gov` nao deve ser reexplorado sem novo alinhamento

Cadeia operacional esperada:
1. `rodada_api_handoff` roda a busca geral por API sem Firecrawl e prepara o handoff
2. `portal_data_collector` coleta os alvos priorizados e organiza o bruto em `data/runs/...`
3. `eda_reservatorio` transforma os dados recebidos em tabelas, figuras e contexto analitico
4. `relatorio_html` monta o HTML final a partir do contexto estruturado e das figuras

Principio de escopo:
- prioridade para o sinal do canal principal do rio Savannah
- usar `Hartwell`, `Russell` e `Thurmond` como anexos de operacao e atribuicao
- evitar aprofundar Thurmond sozinho se existir lacuna material no sinal do rio
- manter Thurmond como foco final da interpretacao sedimentologica

Arquivos desta preparacao:
- `rodada_api_handoff.md`
- `portal_data_collector.md`
- `eda_reservatorio.md`
- `relatorio_html.md`
