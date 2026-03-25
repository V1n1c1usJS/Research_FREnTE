# EDA/99_integracao
Objetivo: cruzar as frentes prontas e identificar relações entre pressões antrópicas e dinâmica dos reservatórios.

PRÉ-REQUISITO: todas as frentes 01–09 devem estar com staging e analytic prontos.

Integrações planejadas:
1. SNIS × municípios × bacia
   → déficit de saneamento espacializado por sub-bacia contribuinte a cada reservatório

2. uso do solo × desmatamento × sub-bacias
   → índice de degradação da cobertura por sub-bacia ao longo do tempo

3. precipitação × vazão × operação do reservatório
   → eficiência hídrica: quanto da chuva chega como afluência útil

4. temperatura × vazão × precipitação
   → balanço hídrico simplificado e tendência de deficit hídrico

5. tempo de residência × uso do solo × SNIS
   → hipótese central: reservatórios com maior TR e maior déficit de saneamento têm maior risco de eutrofização

Painéis finais produzidos aqui:
- painel_pressao_antrópica_subbacia.parquet (integra SNIS + uso_solo + desmatamento + agro)
- painel_hidrologico_reservatorio.parquet (integra vazao + precipitacao + temperatura + operacao)
- painel_risco_eutrofizacao.parquet (integra TR + pressao_antrópica)

Arquivos esperados:
- integracao_pressao_hidro.ipynb
- integracao_risco_eutrofizacao.ipynb
- summary_dashboard.py
