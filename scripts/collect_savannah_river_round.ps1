param(
    [string]$SearchRunId = "perplexity-intel-0cd96ccc",
    [string]$HandoffPath = "data/runs/perplexity-intel-0cd96ccc/processing/05-harvester-handoff-river-curated.json",
    [string]$ReservoirAnnexManifest = "data/runs/operational-collect-savannah-system-20260408-222744/manifest.json",
    [string]$RunId,
    [string]$TargetBeginDate = "2006-01-01",
    [string]$TargetEndDate = "2026-04-09"
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
        [int]$Depth = 12
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

function New-TargetFailure {
    param(
        [string]$TargetId,
        [string]$SourceName,
        [string]$DatasetName,
        [string]$StartUrl,
        [string]$CollectionMethod,
        [string]$Message
    )
    return [ordered]@{
        target_id = $TargetId
        source_name = $SourceName
        dataset_name = $DatasetName
        collection_status = "error"
        access_type = "mixed"
        collection_method = $CollectionMethod
        requires_auth = $false
        provenance_urls = @($StartUrl)
        blockers = @($Message)
        notes = @()
        join_keys = @()
        staging_outputs = @()
        analytic_outputs = @()
        requested_year_start = 2006
        requested_year_end = 2026
        temporal_coverage_requested = "2006-2026"
        temporal_coverage_returned = $null
        raw_artifacts = @()
    }
}

function Get-WqpCoverage {
    param([string]$CsvPath)
    $rows = Import-Csv -LiteralPath $CsvPath
    $years = @(
        $rows |
        ForEach-Object {
            $dateText = $_.ActivityStartDate
            if ($dateText -and $dateText.Length -ge 4) { [int]$dateText.Substring(0, 4) }
        } |
        Where-Object { $_ } |
        Sort-Object -Unique
    )
    if ($years.Count -eq 0) {
        return [ordered]@{
            first_year = $null
            last_year = $null
            years_with_data = 0
            result_count = $rows.Count
        }
    }
    return [ordered]@{
        first_year = $years[0]
        last_year = $years[$years.Count - 1]
        years_with_data = $years.Count
        result_count = $rows.Count
    }
}

function Get-UsgsDvCoverage {
    param([string]$JsonPath)
    $payload = Get-Content -LiteralPath $JsonPath -Raw | ConvertFrom-Json
    $series = @($payload.value.timeSeries)
    $allDates = New-Object System.Collections.Generic.List[string]
    foreach ($item in $series) {
        foreach ($entry in @($item.values[0].value)) {
            if ($entry.dateTime) {
                $allDates.Add([string]$entry.dateTime)
            }
        }
    }
    $orderedDates = $allDates | Sort-Object
    return [ordered]@{
        site_name = if ($series.Count -gt 0) { $series[0].sourceInfo.siteName } else { "" }
        time_series_count = $series.Count
        first_date = if ($orderedDates.Count -gt 0) { $orderedDates[0] } else { $null }
        last_date = if ($orderedDates.Count -gt 0) { $orderedDates[$orderedDates.Count - 1] } else { $null }
        point_count = $orderedDates.Count
        variables = @($series | ForEach-Object { $_.variable.variableCode[0].value } | Sort-Object -Unique)
    }
}

function Collect-WqpRiverSite {
    param(
        [string]$TargetId,
        [string]$SiteId,
        [string]$SiteLabel,
        [string]$ProviderPage,
        [string[]]$JoinKeys
    )
    try {
        $targetDirRel = "collection/$TargetId"
        $targetDir = Join-Path $script:RunDir $targetDirRel
        Ensure-Dir $targetDir

        $stationUrl = "https://www.waterqualitydata.us/data/Station/search?siteid=$SiteId&mimeType=csv&zip=no&providers=NWIS"
        $resultUrl = "https://www.waterqualitydata.us/data/Result/search?siteid=$SiteId&mimeType=csv&zip=no&providers=NWIS"
        $stationRel = "$targetDirRel/station_$SiteId.csv"
        $resultRel = "$targetDirRel/result_$SiteId.csv"

        Download-File -Uri $stationUrl -OutFile (Join-Path $script:RunDir $stationRel)
        Download-File -Uri $resultUrl -OutFile (Join-Path $script:RunDir $resultRel)
        $coverage = Get-WqpCoverage -CsvPath (Join-Path $script:RunDir $resultRel)

        return [ordered]@{
            target_id = $TargetId
            source_name = "waterqualitydata.us"
            dataset_name = $SiteLabel
            collection_status = "collected"
            access_type = "direct_download"
            collection_method = "official_wqp_exports"
            requires_auth = $false
            provenance_urls = @($ProviderPage, $stationUrl, $resultUrl)
            blockers = @()
            notes = @("20-year target was requested conceptually; WQP returned coverage is profiled from the export.")
            join_keys = $JoinKeys
            staging_outputs = @("data/staging/clarks_hill/wqp_river_sites_summary.csv")
            analytic_outputs = @("data/analytic/clarks_hill/river_quality_site_year.csv")
            requested_year_start = 2006
            requested_year_end = 2026
            temporal_coverage_requested = "2006-2026"
            temporal_coverage_returned = $coverage
            raw_artifacts = @(
                (Normalize-Artifact -RelativePath $stationRel -DownloadUrl $stationUrl -FileFormat "csv" -MediaType "text/csv"),
                (Normalize-Artifact -RelativePath $resultRel -DownloadUrl $resultUrl -FileFormat "csv" -MediaType "text/csv")
            )
        }
    } catch {
        return New-TargetFailure -TargetId $TargetId -SourceName "waterqualitydata.us" -DatasetName $SiteLabel -StartUrl $ProviderPage -CollectionMethod "official_wqp_exports" -Message $_.Exception.Message
    }
}

function Collect-UsgsDvSeries {
    param(
        [string]$TargetId,
        [string]$DatasetName,
        [string]$SiteNo,
        [string]$ParameterList,
        [string[]]$JoinKeys
    )
    try {
        $targetDirRel = "collection/$TargetId"
        $targetDir = Join-Path $script:RunDir $targetDirRel
        Ensure-Dir $targetDir

        $url = "https://waterservices.usgs.gov/nwis/dv/?format=json&sites=$SiteNo&startDT=$TargetBeginDate&endDT=$TargetEndDate&parameterCd=$ParameterList&siteStatus=all"
        $jsonRel = "$targetDirRel/dv_$SiteNo.json"
        Download-Json -Uri $url -OutFile (Join-Path $script:RunDir $jsonRel) | Out-Null
        $coverage = Get-UsgsDvCoverage -JsonPath (Join-Path $script:RunDir $jsonRel)

        return [ordered]@{
            target_id = $TargetId
            source_name = "waterservices.usgs.gov"
            dataset_name = $DatasetName
            collection_status = "collected"
            access_type = "api_access"
            collection_method = "direct_usgs_waterservices_dv"
            requires_auth = $false
            provenance_urls = @($url)
            blockers = @()
            notes = @("Daily values collected over the requested 20-year window whenever exposed by the endpoint.")
            join_keys = $JoinKeys
            staging_outputs = @("data/staging/clarks_hill/usgs_river_daily_summary.csv")
            analytic_outputs = @("data/analytic/clarks_hill/river_flow_daily.csv")
            requested_year_start = 2006
            requested_year_end = 2026
            temporal_coverage_requested = "2006-2026"
            temporal_coverage_returned = $coverage
            raw_artifacts = @(
                (Normalize-Artifact -RelativePath $jsonRel -DownloadUrl $url -FileFormat "json" -MediaType "application/json")
            )
        }
    } catch {
        return New-TargetFailure -TargetId $TargetId -SourceName "waterservices.usgs.gov" -DatasetName $DatasetName -StartUrl "https://waterservices.usgs.gov/" -CollectionMethod "direct_usgs_waterservices_dv" -Message $_.Exception.Message
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
        [string]$CollectionMethod,
        [string[]]$Notes = @()
    )
    try {
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
            collection_method = $CollectionMethod
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
            temporal_coverage_returned = "Static or current-context artifact"
            raw_artifacts = @(
                (Normalize-Artifact -RelativePath $fileRel -DownloadUrl $Url -FileFormat $FileFormat)
            )
        }
    } catch {
        return New-TargetFailure -TargetId $TargetId -SourceName $SourceName -DatasetName $DatasetName -StartUrl $Url -CollectionMethod $CollectionMethod -Message $_.Exception.Message
    }
}

function Collect-LocalReference {
    param(
        [string]$TargetId,
        [string]$DatasetName,
        [string]$ReferencePath
    )
    $targetDirRel = "collection/$TargetId"
    $targetDir = Join-Path $script:RunDir $targetDirRel
    Ensure-Dir $targetDir
    $referenceRel = "$targetDirRel/reservoir_annex_reference.json"
    $referenceFull = Join-Path $script:RunDir $referenceRel

    $referencePayload = [ordered]@{
        reference_manifest = $ReferencePath
        note = "Reuse the existing Hartwell-Russell-Thurmond operational collection as annex context for river-first EDA."
    }
    if (Test-Path -LiteralPath $ReferencePath) {
        $manifest = Get-Content -LiteralPath $ReferencePath -Raw | ConvertFrom-Json
        $referencePayload["reference_run_id"] = $manifest.run_id
        $referencePayload["reference_target_count"] = $manifest.target_count
        $referencePayload["reference_collected_count"] = $manifest.collected_count
    }
    Write-JsonFile -Path $referenceFull -Object $referencePayload

    return [ordered]@{
        target_id = $TargetId
        source_name = "local_workspace"
        dataset_name = $DatasetName
        collection_status = "collected"
        access_type = "local_reference"
        collection_method = "reuse_existing_run"
        requires_auth = $false
        provenance_urls = @($ReferencePath)
        blockers = @()
        notes = @("No recollection performed; this is a pinned annex reference for Hartwell, Russell, and Thurmond.")
        join_keys = @("reservoir")
        staging_outputs = @("data/staging/clarks_hill/usace_system_snapshot.csv")
        analytic_outputs = @()
        requested_year_start = 2006
        requested_year_end = 2026
        temporal_coverage_requested = "2006-2026"
        temporal_coverage_returned = "Existing annex run"
        raw_artifacts = @(
            (Normalize-Artifact -RelativePath $referenceRel -DownloadUrl $ReferencePath -FileFormat "json" -MediaType "application/json")
        )
    }
}

if (-not $RunId) {
    $RunId = "operational-collect-savannah-river-" + (Get-Date -Format "yyyyMMdd-HHmmss")
}

$script:RunDir = Join-Path "data/runs" $RunId
Ensure-Dir $script:RunDir
Ensure-Dir (Join-Path $script:RunDir "config")
Ensure-Dir (Join-Path $script:RunDir "collection")
Ensure-Dir (Join-Path $script:RunDir "processing")
Ensure-Dir (Join-Path $script:RunDir "reports")

$options = [ordered]@{
    source_manifest = "data/runs/$SearchRunId/manifest.json"
    source_handoff = $HandoffPath
    reservoir_annex_manifest = $ReservoirAnnexManifest
    context_file = "config/context_clarkshill.yaml"
    target_begin = $TargetBeginDate
    target_end = $TargetEndDate
    target_window_years = 20
    analytical_frame = "river-first"
    excluded_sources = @("des.sc.gov")
}
Write-JsonFile -Path (Join-Path $script:RunDir "config/collection-options.json") -Object $options

$targets = @()
$targets += Collect-WqpRiverSite -TargetId "01-wqp-savannah-river-calhoun-falls" -SiteId "USGS-02189000" -SiteLabel "WQP Savannah River near Calhoun Falls, SC" -ProviderPage "https://www.waterqualitydata.us/provider/NWIS/USGS-SC/USGS-02189000" -JoinKeys @("site_id", "ActivityStartDate", "year")
$targets += Collect-WqpRiverSite -TargetId "02-wqp-savannah-river-us1-augusta" -SiteId "USGS-02196671" -SiteLabel "WQP Savannah River at US 1, Augusta, GA" -ProviderPage "https://www.waterqualitydata.us/provider/NWIS/USGS-GA/USGS-02196671" -JoinKeys @("site_id", "ActivityStartDate", "year")
$targets += Collect-UsgsDvSeries -TargetId "03-usgs-savannah-river-augusta-flow" -DatasetName "USGS Savannah River at Augusta flow and stage" -SiteNo "02197000" -ParameterList "00060,00065" -JoinKeys @("site_no", "date")
$targets += Collect-UsgsDvSeries -TargetId "04-usgs-savannah-river-usace-dock" -DatasetName "USGS Savannah River at USACE dock water data" -SiteNo "021989773" -ParameterList "00060,00065,00010,00095,00300,00400,63680" -JoinKeys @("site_no", "date")
$targets += Collect-WqpRiverSite -TargetId "05-wqp-savannah-river-augusta-intake" -SiteId "USGS-02196560" -SiteLabel "WQP Savannah River Augusta intake" -ProviderPage "https://www.waterqualitydata.us/provider/NWIS/USGS-GA/USGS-02196560" -JoinKeys @("site_id", "ActivityStartDate", "year")
$targets += Collect-StaticAsset -TargetId "06-nws-rvf-cae-text" -SourceName "forecast.weather.gov" -DatasetName "NWS River Forecast Text Product CAE RVF" -Url "https://forecast.weather.gov/product.php?site=ERH&issuedby=CAE&product=RVF&format=txt&version=1&glossary=0" -FileName "rvf_cae_v1.txt" -FileFormat "txt" -CollectionMethod "direct_download_text_product" -Notes @("Forecast-support context only; may still return HTML-wrapped text.")
$targets += Collect-StaticAsset -TargetId "07-clemson-middle-lower-savannah-water-quality-study" -SourceName "open.clemson.edu" -DatasetName "Water Quality Study of Savannah River Basin (2006-2008)" -Url "https://open.clemson.edu/cgi/viewcontent.cgi?article=1000&context=water-resources" -FileName "clemson_middle_lower_savannah_wq_study.pdf" -FileFormat "pdf" -CollectionMethod "direct_download"
$targets += Collect-StaticAsset -TargetId "08-epa-echo-data-downloads" -SourceName "echo.epa.gov" -DatasetName "EPA ECHO data downloads landing page" -Url "https://echo.epa.gov/tools/data-downloads" -FileName "echo_data_downloads.html" -FileFormat "html" -CollectionMethod "direct_download" -Notes @("Corridor pressure seed for NPDES, DMR, PFAS, and facility compliance exports.")
$targets += Collect-StaticAsset -TargetId "09-savannah-river-bacteria-tmdl-2023" -SourceName "epd.georgia.gov" -DatasetName "Savannah River Basin Bacteria TMDL Report 2023" -Url "https://epd.georgia.gov/document/document/savannah-bacteria-tmdl-report-2023/download" -FileName "savannah_bacteria_tmdl_2023.pdf" -FileFormat "pdf" -CollectionMethod "direct_download" -Notes @("Georgia EPD pollutant-pressure context for bacteria impairments and NPDES-linked loads.")
$targets += Collect-StaticAsset -TargetId "10-savannah-river-sediment-tmdl-2010" -SourceName "epd.georgia.gov" -DatasetName "Savannah River Basin Sediment TMDL Evaluation 2010" -Url "https://epd.georgia.gov/sites/epd.georgia.gov/files/related_files/site_page/EPD_Final_Savannah_BioSediment_TMDL_2010.pdf" -FileName "savannah_sediment_tmdl_2010.pdf" -FileFormat "pdf" -CollectionMethod "direct_download" -Notes @("Sediment-pressure context aligned with the final sediment bridge.")
$targets += Collect-StaticAsset -TargetId "11-savannah-sustainable-rivers-monitoring-plan" -SourceName "hec.usace.army.mil" -DatasetName "Sustainable Rivers Monitoring Plan Savannah River Basin" -Url "https://www.hec.usace.army.mil/sustainablerivers/publications/docs/Savannah%20-%20Monitoring%20plan.pdf" -FileName "savannah_sustainable_rivers_monitoring_plan.pdf" -FileFormat "pdf" -CollectionMethod "direct_download" -Notes @("USACE monitoring-plan context for river ecology, DO, turbidity, chlorophyll, and flow support.")
$targets += Collect-StaticAsset -TargetId "12-savannah-harbor-dissolved-oxygen-plan" -SourceName "epd.georgia.gov" -DatasetName "Savannah River Basin dissolved oxygen restoration plan" -Url "https://epd.georgia.gov/sites/epd.georgia.gov/files/related_files/site_page/SavannahHarbor5R_Restoration_Plan_11_10_2015.pdf" -FileName "savannah_harbor_do_restoration_plan_2015.pdf" -FileFormat "pdf" -CollectionMethod "direct_download" -Notes @("Lower-mainstem dissolved oxygen context below Thurmond toward Augusta and harbor reaches.")
$targets += Collect-LocalReference -TargetId "13-reservoir-operations-annex-reference" -DatasetName "Existing reservoir operations annex run" -ReferencePath $ReservoirAnnexManifest

Write-JsonFile -Path (Join-Path $script:RunDir "processing/01-collection-targets.json") -Object $targets

$manifest = [ordered]@{
    run_id = $RunId
    pipeline_name = "savannah_river_manual_collection"
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    source_research_id = $SearchRunId
    source_handoff = $HandoffPath
    analytical_frame = "river-first"
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
    "- Frame analitico: rio primeiro; reservatorios como anexo explicativo.",
    "- Janela-alvo solicitada: 20 anos ($TargetBeginDate a $TargetEndDate) quando a fonte permitiu.",
    "- Pesquisa base: $SearchRunId",
    "- Targets: $($manifest.target_count)",
    "- Coletados: $($manifest.collected_count)",
    "- Parciais: $($manifest.partial_count)",
    "- Bloqueados: $($manifest.blocked_count)",
    "- Erros: $($manifest.error_count)",
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
    foreach ($blocker in $target.blockers) {
        $reportLines += "- Bloqueio: $blocker"
    }
    $reportLines += ""
}
$reportLines -join "`n" | Set-Content -LiteralPath (Join-Path $script:RunDir "reports/$RunId.md") -Encoding UTF8

$targets |
    Select-Object target_id, source_name, dataset_name, collection_status, access_type, requested_year_start, requested_year_end |
    Export-Csv (Join-Path $script:RunDir "reports/collection_targets.csv") -NoTypeInformation -Encoding UTF8

Write-Output "Run directory: $script:RunDir"
Write-Output "Manifest: $(Join-Path $script:RunDir 'manifest.json')"
Write-Output "Collected targets: $($manifest.collected_count)"
