# eda/

Analises exploratorias do projeto FREnTE.

Esta pasta consome dados de `data/staging/` e `data/analytic/`.

## Frentes ativas

| Pasta | Descricao |
|-------|-----------|
| `operacao_reservatorio/` | Operacao dos reservatorios em cascata (ONS, 2000-2025) |
| `clarks_hill/` | Scaffold preparatorio para o EDA contextual de Clarks Hill Lake |

## Como gerar figuras

```bash
python eda/operacao_reservatorio/generate_figures.py
python EDA/clarks_hill/generate_figures.py
```

## Como gerar a apresentacao HTML

```bash
python eda/operacao_reservatorio/generate_presentation.py
python EDA/clarks_hill/generate_presentation.py
```

A apresentacao usa as figuras de `eda/operacao_reservatorio/figures/` e os logos de `src/assets/`.
