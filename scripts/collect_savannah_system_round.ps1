param(
    [string]$SearchRunId = "perplexity-intel-5fdaad57",
    [string]$HandoffPath = "data/runs/perplexity-intel-5fdaad57/processing/05-harvester-handoff-curated.json",
    [string]$RunId,
    [string]$TargetBegin = "2006-01-01T00:00:00Z",
    [string]$TargetEnd = "2026-04-09T00:00:00Z"
)

$ErrorActionPreference = "Stop"

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
        [int]$Depth = 10
    )
    $Object | ConvertTo-Json -Depth $Depth | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Download-File {
    param(
        [string]$Uri,
        [string]$OutFile
    )
    Invoke-WebRequest -Uri $Uri -UseBasicParsing -OutFile $OutFile
}

function Download-Json {
    param(
        [string]$Uri,
        [string]$OutFile
    )
    $response = Invoke-WebRequest -Uri $Uri -UseBasicParsing
    $response.Content | Set-Content -LiteralPath $OutFile -Encoding UTF8
    return (Get-Content -LiteralPath $OutFile -Raw | ConvertFrom-Json)
}

function Normalize-Artifact {
    param(
        [string]$RelativePath,
        [string]$DownloadUrl,
        [string]$FileFormat,
        [string]$Status = "collected",
        [string]$MediaType = "",
        [string[]]$Notes = @()
    )
    $fullPath = Join-Path $script:RunDir $RelativePath
    $size = if (Test-Path -LiteralPath $fullPath) { (Get-Item -LiteralPath $fullPath).Length } else { 0 }
    return [ordered]@{
        relative_path = $RelativePath
        download_url = $DownloadUrl
        file_format = $FileFormat
        media_type = $MediaType
        status = $Status
        content_length = $size
        notes = $Notes
        collected_at = (Get-Date).ToUniversalTime().ToString("o")
    }
}

function Get-TimeSeriesCoverage {
    param([string]$Path)
    try {
        $payload = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
        $values = @($payload.values)
        if ($values.Count -eq 0) {
            return [ordered]@{ point_count = 0; first_time = $null; last_time = $null }
        }
        return [ordered]@{
            point_count = $values.Count
            first_time = $values[0][0]
            last_time = $values[$values.Count - 1][0]
        }
    } catch {
        return [ordered]@{ point_count = 0; first_time = $null; last_time = $null }
    }
}

function Collect-WaterUsaceLocation {
    param(
        [string]$ReservoirSlug,
        [string]$ReservoirName,
        [string]$LocationUrl,
        [string]$TargetId
    )

    $targetDirRel = "collection/$TargetId"
    $targetDir = Join-Path $script:RunDir $targetDirRel
    Ensure-Dir $targetDir

    $locationFileRel = "$targetDirRel/location_$ReservoirSlug.json"
    $locationFile = Join-Path $script:RunDir $locationFileRel
    $locationPayload = Download-Json -Uri $LocationUrl -OutFile $locationFile

    $timeSeries = @()
    if ($locationPayload -is [array] -and $locationPayload.Count -gt 0) {
        $timeSeries = $locationPayload[0].timeseries
    }

    $selectors = @(
        @{ key = "pool_elevation"; labels = @("Elevation"); parameter = "Elev-Pool" },
        @{ key = "inflow"; labels = @("Inflow"); parameter = "Flow-In" },
        @{ key = "outflow"; labels = @("Outflow"); parameter = "Flow" },
        @{ key = "storage"; labels = @("Conservation Storage"); parameter = "Stor" },
        @{ key = "tailwater"; labels = @("Elevation Tailwater"); parameter = "Elev-Tail" },
        @{ key = "rule_curve"; labels = @("Elevation Rule Curve"); parameter = "Elev-GC" },
        @{ key = "power_generation"; labels = @("Power Generation"); parameter = "Energy" },
        @{ key = "precipitation"; labels = @("Precipitation"); parameter = "Precip-Inc" }
    )

    $artifacts = @(
        (Normalize-Artifact -RelativePath $locationFileRel -DownloadUrl $LocationUrl -FileFormat "json" -MediaType "application/json" -Notes @("Official water.usace location payload collected."))
    )
    $notes = @("Requested 20-year target window ($TargetBegin to $TargetEnd) for historical timeseries whenever the endpoint allowed it.")
    $coverage = @{}

    foreach ($selector in $selectors) {
        $match = $timeSeries | Where-Object {
            ($_.label -in $selector.labels) -or ($_.parameter -eq $selector.parameter)
        } | Select-Object -First 1
        if (-not $match) {
            continue
        }

        $encodedName = [System.Uri]::EscapeDataString([string]$match.tsid)
        $tsUrl = "https://water.usace.army.mil/cda/reporting/providers/sas/timeseries?begin=$TargetBegin&end=$TargetEnd&name=$encodedName"
        $tsFileRel = "$targetDirRel/timeseries_${ReservoirSlug}_$($selector.key).json"
        $tsFile = Join-Path $script:RunDir $tsFileRel

        try {
            Download-Json -Uri $tsUrl -OutFile $tsFile | Out-Null
            $seriesCoverage = Get-TimeSeriesCoverage -Path $tsFile
            $coverage[$selector.key] = $seriesCoverage
            $artifacts += Normalize-Artifact -RelativePath $tsFileRel -DownloadUrl $tsUrl -FileFormat "json" -MediaType "application/json" -Notes @("TSID $($match.tsid)")
        } catch {
            $notes += "Timeseries $($selector.key) failed for ${ReservoirName}: $($_.Exception.Message)"
        }
    }

    return [ordered]@{
        target_id = $TargetId
        source_name = "water.usace.army.mil"
        dataset_name = "$ReservoirName operational data"
        collection_status = "collected"
        access_type = "api_access"
        collection_method = "direct_api_from_location_endpoint"
        requires_auth = $false
        provenance_urls = @($LocationUrl)
        blockers = @()
        notes = $notes
        join_keys = @("id_reservatorio", "ano_mes", "ano")
        staging_outputs = @("data/staging/clarks_hill/usace_$ReservoirSlug_long.csv")
        analytic_outputs = @("data/analytic/clarks_hill/usace_$ReservoirSlug_daily.csv")
        requested_year_start = 2006
        requested_year_end = 2026
        temporal_coverage_requested = "2006-2026"
        temporal_coverage_returned = $coverage
        raw_artifacts = $artifacts
    }
}

function Collect-Nid {
    param(
        [string]$NidId,
        [string]$ReservoirName,
        [string]$TargetId
    )
    $targetDirRel = "collection/$TargetId"
    $targetDir = Join-Path $script:RunDir $targetDirRel
    Ensure-Dir $targetDir

    $inventoryUrl = "https://nid.sec.usace.army.mil/api/dams/$NidId/inventory"
    $dataSourceUrl = "https://nid.sec.usace.army.mil/api/dams/$NidId/data-source"
    $inventoryRel = "$targetDirRel/inventory_$NidId.json"
    $dataSourceRel = "$targetDirRel/data_source_$NidId.json"
    Download-Json -Uri $inventoryUrl -OutFile (Join-Path $script:RunDir $inventoryRel) | Out-Null
    Download-Json -Uri $dataSourceUrl -OutFile (Join-Path $script:RunDir $dataSourceRel) | Out-Null

    return [ordered]@{
        target_id = $TargetId
        source_name = "nid.sec.usace.army.mil"
        dataset_name = "NID structural metadata for $ReservoirName"
        collection_status = "collected"
        access_type = "api_access"
        collection_method = "direct_api"
        requires_auth = $false
        provenance_urls = @($inventoryUrl, $dataSourceUrl)
        blockers = @()
        notes = @("Official NID inventory and data-source payloads collected.")
        join_keys = @("id_reservatorio")
        staging_outputs = @()
        analytic_outputs = @()
        requested_year_start = 2006
        requested_year_end = 2026
        temporal_coverage_requested = "2006-2026"
        temporal_coverage_returned = "Structural metadata"
        raw_artifacts = @(
            (Normalize-Artifact -RelativePath $inventoryRel -DownloadUrl $inventoryUrl -FileFormat "json" -MediaType "application/json"),
            (Normalize-Artifact -RelativePath $dataSourceRel -DownloadUrl $dataSourceUrl -FileFormat "json" -MediaType "application/json")
        )
    }
}

function Collect-WqpSite {
    param(
        [string]$SiteId,
        [string]$ReservoirSlug,
        [string]$ReservoirName,
        [string]$TargetId
    )
    $targetDirRel = "collection/$TargetId"
    $targetDir = Join-Path $script:RunDir $targetDirRel
    Ensure-Dir $targetDir

    $providerPage = "https://www.waterqualitydata.us/provider/STORET/21GAEPD_WQX/$SiteId/"
    $stationUrl = "https://www.waterqualitydata.us/data/Station/search?siteid=$SiteId&mimeType=csv&zip=no&providers=STORET"
    $resultUrl = "https://www.waterqualitydata.us/data/Result/search?siteid=$SiteId&mimeType=csv&zip=no&providers=STORET"
    $stationRel = "$targetDirRel/station_$SiteId.csv"
    $resultRel = "$targetDirRel/result_$SiteId.csv"

    Download-File -Uri $stationUrl -OutFile (Join-Path $script:RunDir $stationRel)
    Download-File -Uri $resultUrl -OutFile (Join-Path $script:RunDir $resultRel)

    return [ordered]@{
        target_id = $TargetId
        source_name = "waterqualitydata.us"
        dataset_name = "WQP station and results for $ReservoirName"
        collection_status = "collected"
        access_type = "direct_download"
        collection_method = "official_export_discovery"
        requires_auth = $false
        provenance_urls = @($providerPage, $stationUrl, $resultUrl)
        blockers = @()
        notes = @("Official WQP station and result exports collected for 20-year-target review.")
        join_keys = @("cod_ponto", "ano_mes", "ano", "id_reservatorio")
        staging_outputs = @("data/staging/clarks_hill/wqp_$ReservoirSlug`_results.csv")
        analytic_outputs = @("data/analytic/clarks_hill/wqp_$ReservoirSlug`_annual.csv")
        requested_year_start = 2006
        requested_year_end = 2026
        temporal_coverage_requested = "2006-2026"
        temporal_coverage_returned = "From WQP export; to be profiled in EDA."
        raw_artifacts = @(
            (Normalize-Artifact -RelativePath $stationRel -DownloadUrl $stationUrl -FileFormat "csv" -MediaType "text/csv"),
            (Normalize-Artifact -RelativePath $resultRel -DownloadUrl $resultUrl -FileFormat "csv" -MediaType "text/csv")
        )
    }
}

function Collect-StaticAsset {
    param(
        [string]$TargetId,
        [string]$SourceName,
        [string]$DatasetName,
        [string]$Url,
        [string]$FileName,
        [string]$FileFormat,
        [string[]]$Notes = @()
    )
    $targetDirRel = "collection/$TargetId"
    $targetDir = Join-Path $script:RunDir $targetDirRel
    Ensure-Dir $targetDir
    $fileRel = "$targetDirRel/$FileName"
    Download-File -Uri $Url -OutFile (Join-Path $script:RunDir $fileRel)
    return [ordered]@{
        target_id = $TargetId
        source_name = $SourceName
        dataset_name = $DatasetName
        collection_status = "collected"
        access_type = "direct_download"
        collection_method = "direct_download"
        requires_auth = $false
        provenance_urls = @($Url)
        blockers = @()
        notes = $Notes
        join_keys = @()
        staging_outputs = @()
        analytic_outputs = @()
        requested_year_start = 2006
        requested_year_end = 2026
        temporal_coverage_requested = "2006-2026"
        temporal_coverage_returned = "Static contextual reference"
        raw_artifacts = @(
            (Normalize-Artifact -RelativePath $fileRel -DownloadUrl $Url -FileFormat $FileFormat)
        )
    }
}

if (-not $RunId) {
    $RunId = "operational-collect-savannah-system-" + (Get-Date -Format "yyyyMMdd-HHmmss")
}

$script:RunDir = Join-Path "data/runs" $RunId
Ensure-Dir $script:RunDir
Ensure-Dir (Join-Path $script:RunDir "config")
Ensure-Dir (Join-Path $script:RunDir "collection")
Ensure-Dir (Join-Path $script:RunDir "processing")
Ensure-Dir (Join-Path $script:RunDir "reports")

$options = [ordered]@{
    source_manifest = "data/runs/$SearchRunId/manifest.json"
    source_ranked_datasets = "data/runs/$SearchRunId/processing/03-ranked-datasets.json"
    source_handoff = $HandoffPath
    context_file = "config/context_clarkshill.yaml"
    target_begin = $TargetBegin
    target_end = $TargetEnd
    target_window_years = 20
    excluded_sources = @("des.sc.gov")
}
Write-JsonFile -Path (Join-Path $script:RunDir "config/collection-options.json") -Object $options

$targets = @()
$targets += Collect-WaterUsaceLocation -ReservoirSlug "hartwell" -ReservoirName "Hartwell Dam" -LocationUrl "https://water.usace.army.mil/cda/reporting/providers/sas/locations/hartwell" -TargetId "01-water-usace-hartwell-location"
$targets += Collect-WaterUsaceLocation -ReservoirSlug "russell" -ReservoirName "Richard B. Russell Dam" -LocationUrl "https://water.usace.army.mil/cda/reporting/providers/sas/locations/russell" -TargetId "02-water-usace-russell-location"
$targets += Collect-WaterUsaceLocation -ReservoirSlug "thurmond" -ReservoirName "J. Strom Thurmond Dam" -LocationUrl "https://water.usace.army.mil/cda/reporting/providers/sas/locations/thurmond" -TargetId "03-water-usace-thurmond-location"
$targets += Collect-Nid -NidId "GA01702" -ReservoirName "Hartwell Dam" -TargetId "04-nid-usace-ga01702"
$targets += Collect-Nid -NidId "GA01705" -ReservoirName "Richard B. Russell Dam" -TargetId "05-nid-usace-ga01705"
$targets += Collect-Nid -NidId "GA01701" -ReservoirName "J. Strom Thurmond Dam" -TargetId "06-nid-usace-ga01701"
$targets += Collect-WqpSite -SiteId "21GAEPD_WQX-LK_01_22" -ReservoirSlug "hartwell" -ReservoirName "Lake Hartwell - Dam Forebay" -TargetId "07-wqp-hartwell-dam-forebay"
$targets += Collect-WqpSite -SiteId "21GAEPD_WQX-LK_01_29" -ReservoirSlug "russell" -ReservoirName "Lake Richard B. Russell - Dam Forebay" -TargetId "08-wqp-russell-dam-forebay"
$targets += Collect-WqpSite -SiteId "21GAEPD_WQX-LK_01_40" -ReservoirSlug "thurmond" -ReservoirName "Clarks Hill Lake - Dam Forebay" -TargetId "09-wqp-thurmond-dam-forebay"
$targets += Collect-StaticAsset -TargetId "10-nws-rvf-cae-text" -SourceName "forecast.weather.gov" -DatasetName "NWS River Forecast Text Product CAE RVF" -Url "https://forecast.weather.gov/product.php?site=ERH&issuedby=CAE&product=RVF&format=txt&version=1&glossary=0" -FileName "rvf_cae_v1.txt" -FileFormat "txt" -Notes @("Forecast-support artifact; may remain HTML-wrapped.")
$targets += Collect-StaticAsset -TargetId "11-savannah-bathymetry-noaa" -SourceName "ncei.noaa.gov" -DatasetName "Savannah River Bathymetric Digital Elevation Model" -Url "https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ngdc.mgg.dem:981" -FileName "noaa_bathymetry_landing.html" -FileFormat "html" -Notes @("Metadata landing page collected as morphometry context seed.")
$targets += Collect-StaticAsset -TargetId "12-savannah-landscape-analysis-epa" -SourceName "epa.gov" -DatasetName "Savannah River Basin Landscape Analysis" -Url "https://19january2021snapshot.epa.gov/sites/static/files/2015-06/documents/app-f_text.pdf" -FileName "savannah_river_basin_landscape_analysis.pdf" -FileFormat "pdf"
$targets += Collect-StaticAsset -TargetId "13-savannah-rbrp-deq" -SourceName "deq.nc.gov" -DatasetName "Savannah River Basin Restoration Data" -Url "https://www.deq.nc.gov/mitigation-services/publicfolder/learn-about/core-processes/watershed-planning/savannah-river-basin/savannah-rbrp-2018/download" -FileName "savannah_rbrp_2018.pdf" -FileFormat "pdf"

Write-JsonFile -Path (Join-Path $script:RunDir "processing/01-collection-targets.json") -Object $targets

$manifest = [ordered]@{
    run_id = $RunId
    pipeline_name = "savannah_system_manual_collection"
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    source_research_id = $SearchRunId
    source_handoff = $HandoffPath
    target_count = $targets.Count
    target_ids = @($targets | ForEach-Object { $_.target_id })
    collected_count = @($targets | Where-Object collection_status -eq "collected").Count
    partial_count = @($targets | Where-Object collection_status -eq "partial").Count
    blocked_count = @($targets | Where-Object collection_status -like "blocked*").Count
    error_count = @($targets | Where-Object collection_status -eq "error").Count
    targets = $targets
}
Write-JsonFile -Path (Join-Path $script:RunDir "manifest.json") -Object $manifest

$reportLines = @(
    "# Coleta operacional $RunId",
    "",
    "- Janela-alvo solicitada: 20 anos ($TargetBegin a $TargetEnd) quando a fonte permitiu.",
    "- Pesquisa base: $SearchRunId",
    "- Targets: $($manifest.target_count)",
    "- Coletados: $($manifest.collected_count)",
    "- Parciais: $($manifest.partial_count)",
    "- Bloqueados: $($manifest.blocked_count)",
    ""
)
foreach ($target in $targets) {
    $reportLines += "## $($target.target_id)"
    $reportLines += ""
    $reportLines += "- Fonte: $($target.source_name)"
    $reportLines += "- Dataset: $($target.dataset_name)"
    $reportLines += "- Status: $($target.collection_status)"
    $reportLines += "- Join keys: $([string]::Join(', ', $target.join_keys))"
    foreach ($note in $target.notes) {
        $reportLines += "- Nota: $note"
    }
    $reportLines += ""
}
$reportLines -join "`n" | Set-Content -LiteralPath (Join-Path $script:RunDir "reports/$RunId.md") -Encoding UTF8

$targets | Select-Object target_id, source_name, dataset_name, collection_status, access_type, requested_year_start, requested_year_end | Export-Csv (Join-Path $script:RunDir "reports/collection_targets.csv") -NoTypeInformation -Encoding UTF8

Write-Output "Run directory: $script:RunDir"
Write-Output "Manifest: $(Join-Path $script:RunDir 'manifest.json')"
Write-Output "Collected targets: $($manifest.collected_count)"
