# EDA/10_tempo_residencia
VARIÁVEL DERIVADA — depende de EDA/07_vazao/ e EDA/09_operacao_reservatorio/ prontos.

Objetivo: estimar o tempo de residência da água em cada reservatório e sua variação temporal.
Fórmula base: TR (dias) = Volume_armazenado (m³) / Vazao_defluente (m³/s) / 86400

Insumo: data/analytic/reservatorio_mes/ (colunas: volume_armazenado_hm3, vazao_defluente_media_m3s)
Saída: adicionar coluna tempo_residencia_dias ao painel reservatorio_mes

Análises recomendadas:
- Série temporal de TR por reservatório (1990–presente)
- Correlação TR × volume útil (%)
- Identificação de períodos de TR extremo (> 200 dias = risco de eutrofização)
- Comparação TR entre reservatórios (cascata: cabeceira vs foz)

Chaves: id_reservatorio, ano_mes

PRÉ-REQUISITOS OBRIGATÓRIOS:
- data/analytic/reservatorio_mes/ completo (07 + 09 prontos)

Arquivos esperados:
- derive_tempo_residencia.ipynb
- plots_tempo_residencia.py
