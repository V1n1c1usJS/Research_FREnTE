# EDA/
Análises exploratórias do projeto FREnTE — Rio Tietê.
IMPORTANTE: Esta pasta consome dados de data/staging/, data/spatial_ref/ e data/analytic/.
NÃO usar dados de data/raw/ diretamente em notebooks ou scripts daqui.

Frentes prontas: 01–09
Frente derivada: 10 (tempo de residência — depende de 07 + 09 prontos)
Integração: 99

Ordem de execução recomendada:
1. 03_limites_bacia (base geográfica)
2. 01_snis_esgoto + 02_uso_do_solo + 04_agropecuaria (pressões antrópicas)
3. 05_desmatamento (pressão sobre cobertura)
4. 06_precipitacao + 07_vazao + 08_temperatura (climatologia)
5. 09_operacao_reservatorio (estado do sistema)
6. 10_tempo_residencia (derivado de 07+09)
7. 99_integracao (cruzamento final)
