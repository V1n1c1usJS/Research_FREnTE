param(
    [Parameter(Mandatory = $true)]
    [string]$RunId,

    [Parameter(Mandatory = $false)]
    [string]$SourceSlug = "",

    [Parameter(Mandatory = $false)]
    [string]$CollectionOptionsJson = "{}"
)

$runRoot = Join-Path "data/runs" $RunId
$subdirs = @(
    "config",
    "collection",
    "processing",
    "reports"
)

foreach ($subdir in $subdirs) {
    $target = Join-Path $runRoot $subdir
    New-Item -ItemType Directory -Path $target -Force | Out-Null
}

if ($SourceSlug -ne "") {
    New-Item -ItemType Directory -Path (Join-Path $runRoot "collection/$SourceSlug") -Force | Out-Null
}

$optionsPath = Join-Path $runRoot "config/collection-options.json"
$CollectionOptionsJson | Set-Content -Path $optionsPath -Encoding UTF8

Write-Output "run_root=$runRoot"
Write-Output "options_path=$optionsPath"
