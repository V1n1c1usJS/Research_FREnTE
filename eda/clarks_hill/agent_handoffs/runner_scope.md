# Runner Scope

Agent alvo:
- `rodada_api_handoff`
- nickname esperado: `Runner` ou `RoundLead`

Objetivo desta rodada:
- executar a busca geral por API para o sistema `Hartwell -> Russell -> Thurmond`
- preparar um handoff de coleta explicitamente sistemico para o `Harvester`

Escopo individual:
- rodar a descoberta geral do projeto sem Firecrawl
- usar o contexto oficial em `config/context_clarkshill.yaml`
- usar as trilhas oficiais em `config/tracks_clarkshill.yaml`
- buscar datasets, endpoints e paginas-fonte para os tres reservatorios
- priorizar fontes oficiais e dados operacionais, hidrologicos e de qualidade da agua
- verificar se o run finalizou corretamente antes de liberar qualquer handoff
- gerar o pacote `04-harvester-handoff.json` com prioridades, urls iniciais, formato esperado e observacoes de risco
- registrar, sempre que possivel, a janela temporal alvo de 20 anos versus a cobertura declarada ou observada de cada alvo

Temas obrigatorios de busca:
- operacao coordenada USACE para Hartwell, Russell e Thurmond
- metadados estruturais NID para os tres reservatorios
- hidrologia e gauges USGS associados ao sistema
- forecast e suporte operacional NWS/NOAA quando relevante
- water quality para Thurmond e, quando houver, Hartwell e Russell
- morfometria, watershed context, land cover e literatura tecnica sobre a cascata

Entregavel esperado:
- `data/runs/{run-id}/processing/04-harvester-handoff.json`
- `data/runs/{run-id}/reports/harvester_targets.csv`
- resumo curto com:
  - contagem de alvos
  - cobertura por reservatorio
  - lacunas por tema
  - riscos de acesso
  - diferenca entre janela alvo e cobertura retornada

Restricoes:
- nao usar Firecrawl
- nao fazer raspagem portal-first
- nao fazer EDA
- nao construir HTML
- se um reservatorio nao tiver cobertura minima de operacao, isso deve aparecer explicitamente no handoff
- nao marcar fonte como historica completa sem evidencia de cobertura observada

Condicao de parada:
- parar quando o handoff estiver pronto para alimentar o `Harvester`
- se o run terminar sem cobertura utilizavel para qualquer um dos tres reservatorios, escalar ao chat principal
