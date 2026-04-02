param(
    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [Parameter(Mandatory = $false)]
    [string]$ReportTitle = "Relatorio HTML",

    [Parameter(Mandatory = $false)]
    [string]$ReportSubtitle = "",

    [Parameter(Mandatory = $false)]
    [string]$ContextSummary = ""
)

$payload = @{
    report_title = $ReportTitle
    report_subtitle = $ReportSubtitle
    context_summary = $ContextSummary
    metadata = @{
        date_label = ""
        source_note = ""
    }
    metrics = @()
    sections = @()
    figures = @()
    output_path = $OutputPath
} | ConvertTo-Json -Depth 8

$parent = Split-Path -Parent $OutputPath
if ($parent -and -not (Test-Path $parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
}

$contextPath = [System.IO.Path]::ChangeExtension($OutputPath, ".context.json")
$payload | Set-Content -Path $contextPath -Encoding UTF8

Write-Output "context_path=$contextPath"
