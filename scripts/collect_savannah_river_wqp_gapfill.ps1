param(
    [string]$SearchRunId = "perplexity-intel-0cd96ccc",
    [string]$HandoffPath = "data/runs/perplexity-intel-0cd96ccc/processing/04-harvester-handoff.json",
    [string]$RunId,
    [string]$RequestedPeriodStart = "2006-01-01",
    [string]$RequestedPeriodEnd = "2026-04-09"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Write-JsonFile {
    param(
        [string]$Path,
        [object]$Object,
        [int]$Depth = 12
    )
    $Object | ConvertTo-Json -Depth $Depth | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Get-Checksum {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-WqpResultCoverage {
    param(
        [string]$CsvPath,
        [datetime]$RequestedStart,
        [datetime]$RequestedEnd
    )

    $rows = Import-Csv -LiteralPath $CsvPath
    $allDates = New-Object System.Collections.Generic.List[datetime]
    $windowDates = New-Object System.Collections.Generic.List[datetime]

    foreach ($row in $rows) {
        $dateText = [string]$row.ActivityStartDate
        if (-not [string]::IsNullOrWhiteSpace($dateText)) {
            try {
                $parsed = [datetime]::Parse($dateText)
                $allDates.Add($parsed)
                if ($parsed -ge $RequestedStart -and $parsed -le $RequestedEnd) {
                    $windowDates.Add($parsed)
                }
            } catch {
            }
        }
    }

    $orderedAll = @($allDates | Sort-Object)
    $orderedWindow = @($windowDates | Sort-Object)
    $allYears = @($orderedAll | ForEach-Object { $_.Year } | Sort-Object -Unique)
    $windowYears = @($orderedWindow | ForEach-Object { $_.Year } | Sort-Object -Unique)

    $status = if ($orderedWindow.Count -eq 0) {
        "outside_target_window"
    } elseif ($orderedWindow[0] -le $RequestedStart -and $orderedWindow[$orderedWindow.Count - 1] -ge $RequestedEnd) {
        "met_or_exceeded"
    } else {
        "partial_within_target"
    }

    return [ordered]@{
        result_count_total = $rows.Count
        result_count_in_target_window = $orderedWindow.Count
        first_activity_date = if ($orderedAll.Count -gt 0) { $orderedAll[0].ToString("yyyy-MM-dd") } else { $null }
        last_activity_date = if ($orderedAll.Count -gt 0) { $orderedAll[$orderedAll.Count - 1].ToString("yyyy-MM-dd") } else { $null }
        first_activity_date_in_target_window = if ($orderedWindow.Count -gt 0) { $orderedWindow[0].ToString("yyyy-MM-dd") } else { $null }
        last_activity_date_in_target_window = if ($orderedWindow.Count -gt 0) { $orderedWindow[$orderedWindow.Count - 1].ToString("yyyy-MM-dd") } else { $null }
        years_with_data_total = $allYears.Count
        years_with_data_in_target_window = $windowYears.Count
        coverage_window_status = $status
    }
}

function Get-CoverageNote {
    param(
        [object]$Coverage,
        [string]$RequestedStart,
        [string]$RequestedEnd
    )

    if (-not $Coverage.first_activity_date) {
        return "20-year target window requested from $RequestedStart to $RequestedEnd, but the returned CSV did not expose a parseable ActivityStartDate."
    }

    if ($Coverage.coverage_window_status -eq "met_or_exceeded") {
        return "20-year target window requested from $RequestedStart to $RequestedEnd; returned CSV contains records inside that full window, with overall export coverage from $($Coverage.first_activity_date) to $($Coverage.last_activity_date)."
    }

    if ($Coverage.coverage_window_status -eq "outside_target_window") {
        return "20-year target window requested from $RequestedStart to $RequestedEnd, but the returned CSV contains no records inside that window. Overall export coverage is $($Coverage.first_activity_date) to $($Coverage.last_activity_date)."
    }

    return "20-year target window requested from $RequestedStart to $RequestedEnd, but the returned CSV only partially covers that window. Records inside the target window run from $($Coverage.first_activity_date_in_target_window) to $($Coverage.last_activity_date_in_target_window), while the overall export spans $($Coverage.first_activity_date) to $($Coverage.last_activity_date)."
}

function Normalize-Artifact {
    param(
        [string]$RelativePath,
        [string]$DownloadUrl,
        [string]$FileFormat,
        [string]$MediaType,
        [string[]]$Notes = @()
    )

    $fullPath = Join-Path $script:RunDir $RelativePath
    return [ordered]@{
        relative_path = $RelativePath
        download_url = $DownloadUrl
        media_type = $MediaType
        file_format = $FileFormat
        content_length = if (Test-Path -LiteralPath $fullPath) { (Get-Item -LiteralPath $fullPath).Length } else { 0 }
        checksum_sha256 = Get-Checksum -Path $fullPath
        status = "collected"
        notes = $Notes
        collected_at = (Get-Date).ToUniversalTime().ToString("o")
    }
}

function Collect-WqpResultTarget {
    param(
        [string]$TargetId,
        [string]$SiteId,
        [string]$DatasetName,
        [string]$RiverScope,
        [string]$ProviderPage,
        [string]$ResultUrl,
        [datetime]$RequestedStart,
        [datetime]$RequestedEnd
    )

    $targetDirRel = "collection/$TargetId"
    $targetDir = Join-Path $script:RunDir $targetDirRel
    Ensure-Dir $targetDir

    $csvRel = "$targetDirRel/result_$SiteId.csv"
    $csvFull = Join-Path $script:RunDir $csvRel
    Invoke-WebRequest -Uri $ResultUrl -UseBasicParsing -OutFile $csvFull

    $coverage = Get-WqpResultCoverage -CsvPath $csvFull -RequestedStart $RequestedStart -RequestedEnd $RequestedEnd
    $coverageNote = Get-CoverageNote -Coverage $coverage -RequestedStart $RequestedStart.ToString("yyyy-MM-dd") -RequestedEnd $RequestedEnd.ToString("yyyy-MM-dd")

    return [ordered]@{
        target_id = $TargetId
        source_name = "waterqualitydata.us"
        dataset_name = $DatasetName
        collection_status = "collected"
        access_type = "direct_download"
        collection_method = "portal_confirmed_result_search_export"
        requires_auth = $false
        provenance_urls = @($ProviderPage, $ResultUrl)
        blockers = @()
        notes = @(
            "The functional WQP Result/search endpoint was confirmed through a portal-first Playwright step before deterministic download.",
            "No extra query parameter was required beyond siteid, mimeType, zip, and providers=NWIS.",
            $coverageNote
        )
        join_keys = @("MonitoringLocationIdentifier", "ActivityStartDate", "year", "month", "ano_mes")
        staging_outputs = @()
        analytic_outputs = @()
        requested_period_start = $RequestedStart.ToString("yyyy-MM-dd")
        requested_period_end = $RequestedEnd.ToString("yyyy-MM-dd")
        actual_period_start = $coverage.first_activity_date
        actual_period_end = $coverage.last_activity_date
        coverage_window_status = $coverage.coverage_window_status
        coverage_note = $coverageNote
        requested_target_window_years = 20
        result_count_total = $coverage.result_count_total
        result_count_in_target_window = $coverage.result_count_in_target_window
        years_with_data_total = $coverage.years_with_data_total
        years_with_data_in_target_window = $coverage.years_with_data_in_target_window
        site_id = $SiteId
        river_scope = $RiverScope
        raw_artifacts = @(
            (Normalize-Artifact -RelativePath $csvRel -DownloadUrl $ResultUrl -FileFormat "csv" -MediaType "text/csv" -Notes @("Raw WQP result export collected from confirmed endpoint."))
        )
    }
}

if (-not $RunId) {
    $RunId = "operational-collect-savannah-river-gapfill-" + (Get-Date -Format "yyyyMMdd-HHmmss")
}

$requestedStart = [datetime]::Parse($RequestedPeriodStart)
$requestedEnd = [datetime]::Parse($RequestedPeriodEnd)

$script:RunDir = Join-Path "data/runs" $RunId
Ensure-Dir $script:RunDir
Ensure-Dir (Join-Path $script:RunDir "config")
Ensure-Dir (Join-Path $script:RunDir "collection")
Ensure-Dir (Join-Path $script:RunDir "processing")
Ensure-Dir (Join-Path $script:RunDir "reports")

$collectionOptions = [ordered]@{
    source_research_id = $SearchRunId
    source_handoff = $HandoffPath
    analytical_frame = "river-first gapfill"
    focus_priorities = @(
        "WQP mainstem result exports for Savannah River",
        "20-year target window reporting versus real coverage",
        "No des.sc.gov access"
    )
    requested_period_start = $RequestedPeriodStart
    requested_period_end = $RequestedPeriodEnd
    target_window_years = 20
    confirmed_result_search_endpoints = @(
        "https://www.waterqualitydata.us/data/Result/search?siteid=USGS-02189000&mimeType=csv&zip=no&providers=NWIS",
        "https://www.waterqualitydata.us/data/Result/search?siteid=USGS-02196671&mimeType=csv&zip=no&providers=NWIS",
        "https://www.waterqualitydata.us/data/Result/search?siteid=USGS-02196560&mimeType=csv&zip=no&providers=NWIS"
    )
    excluded_sources = @("des.sc.gov")
    declared_gaps = @(
        "Pollutant-pressure targets remain unspecified in the provisional handoff; no generic pressure collection was invented in this run."
    )
}
Write-JsonFile -Path (Join-Path $script:RunDir "config/collection-options.json") -Object $collectionOptions

$targets = @()
$targets += Collect-WqpResultTarget -TargetId "01-wqp-savannah-river-calhoun-falls-results" -SiteId "USGS-02189000" -DatasetName "WQP Savannah River near Calhoun Falls, SC result export" -RiverScope "mainstem_above_hartwell" -ProviderPage "https://www.waterqualitydata.us/provider/NWIS/USGS-SC/USGS-02189000" -ResultUrl "https://www.waterqualitydata.us/data/Result/search?siteid=USGS-02189000&mimeType=csv&zip=no&providers=NWIS" -RequestedStart $requestedStart -RequestedEnd $requestedEnd
$targets += Collect-WqpResultTarget -TargetId "02-wqp-savannah-river-us1-augusta-results" -SiteId "USGS-02196671" -DatasetName "WQP Savannah River at US 1, Augusta, GA result export" -RiverScope "mainstem_below_thurmond_augusta" -ProviderPage "https://www.waterqualitydata.us/provider/NWIS/USGS-GA/USGS-02196671" -ResultUrl "https://www.waterqualitydata.us/data/Result/search?siteid=USGS-02196671&mimeType=csv&zip=no&providers=NWIS" -RequestedStart $requestedStart -RequestedEnd $requestedEnd
$targets += Collect-WqpResultTarget -TargetId "03-wqp-savannah-river-augusta-intake-results" -SiteId "USGS-02196560" -DatasetName "WQP Savannah River Augusta intake result export" -RiverScope "mainstem_below_thurmond_augusta" -ProviderPage "https://www.waterqualitydata.us/provider/NWIS/USGS-GA/USGS-02196560" -ResultUrl "https://www.waterqualitydata.us/data/Result/search?siteid=USGS-02196560&mimeType=csv&zip=no&providers=NWIS" -RequestedStart $requestedStart -RequestedEnd $requestedEnd

Write-JsonFile -Path (Join-Path $script:RunDir "processing/01-collection-targets.json") -Object $targets

$manifest = [ordered]@{
    run_id = $RunId
    pipeline_name = "savannah_river_wqp_gapfill"
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    source_research_id = $SearchRunId
    source_handoff = $HandoffPath
    target_count = $targets.Count
    target_ids = @($targets | ForEach-Object { $_.target_id })
    collected_count = @($targets | Where-Object collection_status -eq "collected").Count
    partial_count = @($targets | Where-Object collection_status -eq "partial").Count
    blocked_count = @($targets | Where-Object collection_status -like "blocked*").Count
    error_count = @($targets | Where-Object collection_status -eq "error").Count
    target_window_years = 20
    requested_period_start = $RequestedPeriodStart
    requested_period_end = $RequestedPeriodEnd
    excluded_sources = @("des.sc.gov")
    declared_gaps = @(
        "Pollutant-pressure targets remain unspecified in the provisional handoff; no generic pressure collection was invented in this run."
    )
    targets = $targets
}
Write-JsonFile -Path (Join-Path $script:RunDir "manifest.json") -Object $manifest

$reportLines = @(
    "# Coleta operacional $RunId",
    "",
    "- Handoff provisório: $HandoffPath",
    "- Foco: gapfill WQP mainstem Savannah River.",
    "- Janela-alvo operacional: $RequestedPeriodStart a $RequestedPeriodEnd (20 anos, alinhada ao calendario das rodadas anteriores).",
    "- Regra aplicada: endpoint confirmado via portal-first/Playwright e download deterministico em seguida.",
    "- Restricao respeitada: des.sc.gov nao foi tocado.",
    "- Targets: $($manifest.target_count)",
    "- Coletados: $($manifest.collected_count)",
    "- Parciais: $($manifest.partial_count)",
    "- Bloqueados: $($manifest.blocked_count)",
    "- Erros: $($manifest.error_count)",
    "",
    "## Lacuna declarada",
    "",
    "- Pollutant pressures continuam sem alvo especifico neste handoff provisório; nenhuma coleta generica foi inventada.",
    ""
)

foreach ($target in $targets) {
    $reportLines += "## $($target.target_id)"
    $reportLines += ""
    $reportLines += "- Fonte: $($target.source_name)"
    $reportLines += "- Dataset: $($target.dataset_name)"
    $reportLines += "- Status: $($target.collection_status)"
    $reportLines += "- Endpoint funcional: $($target.provenance_urls[1])"
    $reportLines += "- Janela-alvo: $($target.requested_period_start) -> $($target.requested_period_end)"
    $reportLines += "- Cobertura real do export: $($target.actual_period_start) -> $($target.actual_period_end)"
    $reportLines += "- Registros totais no CSV: $($target.result_count_total)"
    $reportLines += "- Registros dentro da janela-alvo: $($target.result_count_in_target_window)"
    $reportLines += "- Anos com dados no CSV: $($target.years_with_data_total)"
    $reportLines += "- Anos com dados dentro da janela-alvo: $($target.years_with_data_in_target_window)"
    $reportLines += "- Avaliacao da cobertura: $($target.coverage_window_status)"
    foreach ($note in $target.notes) {
        $reportLines += "- Nota: $note"
    }
    $reportLines += ""
}

$reportPath = Join-Path $script:RunDir "reports/$RunId.md"
$reportLines -join "`n" | Set-Content -LiteralPath $reportPath -Encoding UTF8

$targets |
    Select-Object target_id, site_id, river_scope, collection_status, requested_period_start, requested_period_end, actual_period_start, actual_period_end, result_count_total, result_count_in_target_window, years_with_data_total, years_with_data_in_target_window, coverage_window_status |
    Export-Csv (Join-Path $script:RunDir "reports/collection_targets.csv") -NoTypeInformation -Encoding UTF8

Write-Output "run_id=$RunId"
Write-Output "run_dir=$script:RunDir"
Write-Output "manifest=$(Join-Path $script:RunDir 'manifest.json')"
Write-Output "report=$reportPath"
