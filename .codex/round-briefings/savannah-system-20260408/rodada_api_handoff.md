# Briefing: rodada_api_handoff

Objetivo:
- executar a proxima busca geral por API sem Firecrawl quando o chat principal liberar

Escopo funcional:
- trabalhar com o sistema completo `Hartwell -> Russell -> Thurmond`
- tratar o canal principal do rio Savannah como nucleo analitico
- buscar paridade entre trechos do rio em:
  - hidrologia
  - level and flow context
  - water quality
  - sedimento em suspensao / turbidez
- usar operacao de reservatorios como suporte explicativo

Prioridades de fonte:
- `USGS NWIS`
- `Water Quality Portal`
- `water.usace`
- `NID / USACE`
- `NWS SERFC`
- `NOAA`
- `PRISM`
- `Daymet`
- `NLCD`
- literatura tecnica oficial ou academica

Regras:
- usar rodada API-first sem Firecrawl
- nao fazer raspagem portal-first
- nao montar EDA
- nao construir HTML
- sempre buscar uma janela historica alvo de 20 anos quando a fonte permitir
- se a fonte devolver menos de 20 anos, registrar a cobertura real como limitacao no handoff
- `des.sc.gov` fica fora da rodada

Criterio de qualidade do handoff:
- targets agrupados por trecho do rio, reservatorio de suporte e familia de fonte
- destaque explicito das lacunas por trecho do rio
- destaque explicito das limitacoes de cobertura temporal por trecho e por fonte
- evitar um handoff concentrado apenas em Thurmond ou apenas em operacao de barragem

Entregavel esperado:
- pacote de handoff para o `Harvester`
- resumo curto para o chat principal
