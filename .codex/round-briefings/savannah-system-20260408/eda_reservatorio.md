# Briefing: eda_reservatorio

Objetivo:
- transformar os dados coletados do sistema Savannah em EDA reproduzivel e figuras para relatorio

Escopo funcional:
- trabalhar com `Hartwell`, `Russell` e `Thurmond`
- manter `Thurmond` como foco final da interpretacao sedimentologica
- tratar `Hartwell` e `Russell` como condicionantes de operacao e tempo de residencia a jusante

Entregas analiticas esperadas:
- normalizacao em `data/staging/...`
- derivacoes analiticas em `data/analytic/...` quando necessario
- workspace em `EDA/clarks_hill/` ou equivalente alinhado ao sistema
- figuras comparativas e figuras focadas em Thurmond
- `report_context.json` pronto para o `Narrator`

Prioridades de analise:
- paridade operacional entre os tres reservatorios
- cascata hidrologica e condicionamento a montante
- water quality por reservatorio quando os dados existirem
- tempo de residencia e contexto hidrodinamico de Thurmond
- explicitar lacunas sem fabricar metricas

Regras:
- seguir o padrao canonico de `EDA/operacao_reservatorio/`
- nao inventar comparacao se um reservatorio nao tiver dados suficientes
- quando a cobertura for desigual, separar:
  - `system-wide comparison`
  - `Thurmond-focused interpretation`

Entregavel esperado:
- scripts Python reproduziveis
- figuras PNG para relatorio
- contexto estruturado para HTML com cobertura e lacunas por reservatorio
