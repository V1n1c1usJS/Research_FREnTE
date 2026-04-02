param(
    [Parameter(Mandatory = $true)]
    [string]$Slug,

    [string]$StudyTitle = "Reservoir EDA",

    [string]$WorkspaceRoot = (Get-Location).Path
)

$edaDir = Join-Path $WorkspaceRoot ("EDA\" + $Slug)
$figDir = Join-Path $edaDir "figures"

New-Item -ItemType Directory -Force -Path $edaDir | Out-Null
New-Item -ItemType Directory -Force -Path $figDir | Out-Null

$readmePath = Join-Path $edaDir "README.md"
$processPath = Join-Path $edaDir "process_context_sources.py"
$figuresPath = Join-Path $edaDir "generate_figures.py"
$presentationPath = Join-Path $edaDir "generate_presentation.py"
$contextPath = Join-Path $edaDir "report_context.template.json"

if (-not (Test-Path $readmePath)) {
    @"
# $StudyTitle

Objetivo: EDA contextual para o estudo.
Insumos principais: definir caminhos reais quando os dados chegarem.
Saidas principais: figuras em `figures/`, scripts Python reproduziveis e contexto estruturado para relatorio.

Arquivos esperados:
- process_context_sources.py
- generate_figures.py
- generate_presentation.py
- report_context.json
"@ | Set-Content -LiteralPath $readmePath -Encoding UTF8
}

if (-not (Test-Path $processPath)) {
    @"
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGING = ROOT / "data" / "staging"
ANALYTIC = ROOT / "data" / "analytic"


def main() -> None:
    print("TODO: normalize and aggregate context sources for this study")


if __name__ == "__main__":
    main()
"@ | Set-Content -LiteralPath $processPath -Encoding UTF8
}

if (-not (Test-Path $figuresPath)) {
    @"
from pathlib import Path

FIG_DIR = Path(__file__).resolve().parent / "figures"


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    print("TODO: generate report-ready figures for this study")


if __name__ == "__main__":
    main()
"@ | Set-Content -LiteralPath $figuresPath -Encoding UTF8
}

if (-not (Test-Path $presentationPath)) {
    @"
from pathlib import Path

OUT = Path(__file__).resolve().parent / "apresentacao.html"


def main() -> None:
    print(f"TODO: build HTML presentation at {OUT}")


if __name__ == "__main__":
    main()
"@ | Set-Content -LiteralPath $presentationPath -Encoding UTF8
}

if (-not (Test-Path $contextPath)) {
    @"
{
  "report_title": "$StudyTitle",
  "report_subtitle": "Contextual EDA",
  "context_summary": "Fill this file with analytical context after the figures are generated.",
  "metrics": [],
  "sections": [],
  "figures": [],
  "output_path": "EDA/$Slug/apresentacao.html"
}
"@ | Set-Content -LiteralPath $contextPath -Encoding UTF8
}

Write-Output "EDA scaffold ready at: $edaDir"
