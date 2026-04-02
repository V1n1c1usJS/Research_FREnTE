# raw/ibge_pam
Fonte: IBGE PAM — Produção Agrícola Municipal (sidra.ibge.gov.br)
Entradas: tabelas SIDRA com área colhida, produção e rendimento por cultura/município/ano
Saídas para staging: staging/agropecuaria/pam_municipio_ano.parquet
Chaves: cod_ibge, ano
Próximos passos: baixar via SIDRA API ou download manual (tabelas 1612, 5457)
