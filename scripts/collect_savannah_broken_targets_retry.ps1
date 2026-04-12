param(
    [string]$SearchRunId = "perplexity-intel-0dc4b629",
    [string]$RunId,
    [string]$RequestedPeriodStart = "2006-01-01",
    [string]$RequestedPeriodEnd = "2026-04-11"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$script:BrowserHeaders = @{
    "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
}

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
        [int]$Depth = 16
    )
    $Object | ConvertTo-Json -Depth $Depth | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Invoke-Download {
    param(
        [string]$Uri,
        [string]$OutFile
    )
    Invoke-WebRequest -Uri $Uri -Headers $script:BrowserHeaders -MaximumRedirection 10 -UseBasicParsing -OutFile $OutFile
    if ((Test-Path -LiteralPath $OutFile) -and ((Get-Item -LiteralPath $OutFile).Length -eq 0)) {
        throw "Downloaded file is empty: $OutFile"
    }
}

function Invoke-DownloadText {
    param(
        [string]$Uri,
        [string]$OutFile
    )
    $response = Invoke-WebRequest -Uri $Uri -Headers $script:BrowserHeaders -MaximumRedirection 10 -UseBasicParsing
    $response.Content | Set-Content -LiteralPath $OutFile -Encoding UTF8
    if ((Test-Path -LiteralPath $OutFile) -and ((Get-Item -LiteralPath $OutFile).Length -eq 0)) {
        throw "Downloaded text response is empty: $OutFile"
    }
    return $response
}

function Invoke-DownloadJson {
    param(
        [string]$Uri,
        [string]$OutFile
    )
    $response = Invoke-WebRequest -Uri $Uri -Headers $script:BrowserHeaders -MaximumRedirection 10 -UseBasicParsing
    $response.Content | Set-Content -LiteralPath $OutFile -Encoding UTF8
    return (Get-Content -LiteralPath $OutFile -Raw | ConvertFrom-Json)
}

function Normalize-Artifact {
    param(
        [string]$RelativePath,
        [string]$DownloadUrl,
        [string]$FileFormat,
        [string]$MediaType = "",
        [string[]]$Notes = @()
    )
    $fullPath = Join-Path $script:RunDir $RelativePath
    return [ordered]@{
        relative_path = $RelativePath
        download_url = $DownloadUrl
        file_format = $FileFormat
        media_type = $MediaType
        status = "collected"
        content_length = if (Test-Path -LiteralPath $fullPath) { (Get-Item -LiteralPath $fullPath).Length } else { 0 }
        notes = $Notes
        collected_at = (Get-Date).ToUniversalTime().ToString("o")
    }
}

function New-TargetRecord {
    param(
        [string]$TargetId,
        [string]$SourceName,
        [string]$DatasetName,
        [string]$CollectionStatus,
        [string]$AccessType,
        [string]$CollectionMethod,
        [string[]]$ProvenanceUrls,
        [string[]]$Blockers,
        [string[]]$Notes,
        [string[]]$JoinKeys,
        [object[]]$RawArtifacts
    )
    return [ordered]@{
        target_id = $TargetId
        source_name = $SourceName
        dataset_name = $DatasetName
        collection_status = $CollectionStatus
        access_type = $AccessType
        collection_method = $CollectionMethod
        requires_auth = $false
        provenance_urls = $ProvenanceUrls
        blockers = $Blockers
        notes = $Notes
        join_keys = $JoinKeys
        staging_outputs = @()
        analytic_outputs = @()
        requested_period_start = $RequestedPeriodStart
        requested_period_end = $RequestedPeriodEnd
        target_window_years = 20
        raw_artifacts = $RawArtifacts
    }
}

function Collect-WqpSiteBundle {
    param(
        [string]$TargetId,
        [string]$SiteId,
        [string]$DatasetName
    )

    $targetDirRel = "collection/$TargetId"
    $targetDir = Join-Path $script:RunDir $targetDirRel
    Ensure-Dir $targetDir

    $stationUrl = "https://www.waterqualitydata.us/data/Station/search?siteid=$SiteId&mimeType=csv&zip=no&providers=NWIS"
    $resultUrl = "https://www.waterqualitydata.us/data/Result/search?siteid=$SiteId&mimeType=csv&zip=no&providers=NWIS"
    $stationRel = "$targetDirRel/station_$SiteId.csv"
    $resultRel = "$targetDirRel/result_$SiteId.csv"

    $artifacts = @()
    $blockers = @()

    try {
        Invoke-Download -Uri $stationUrl -OutFile (Join-Path $script:RunDir $stationRel)
        $artifacts += Normalize-Artifact -RelativePath $stationRel -DownloadUrl $stationUrl -FileFormat "csv" -MediaType "text/csv"
    } catch {
        $blockers += "Station/search failed: $($_.Exception.Message)"
    }

    try {
        Invoke-Download -Uri $resultUrl -OutFile (Join-Path $script:RunDir $resultRel)
        $artifacts += Normalize-Artifact -RelativePath $resultRel -DownloadUrl $resultUrl -FileFormat "csv" -MediaType "text/csv"
    } catch {
        $blockers += "Result/search failed: $($_.Exception.Message)"
    }

    $status = if ($artifacts.Count -ge 2) { "collected" } elseif ($artifacts.Count -eq 1) { "partial" } else { "error" }
    return New-TargetRecord `
        -TargetId $TargetId `
        -SourceName "waterqualitydata.us" `
        -DatasetName $DatasetName `
        -CollectionStatus $status `
        -AccessType "direct_download" `
        -CollectionMethod "confirmed_wqp_station_and_result_exports" `
        -ProvenanceUrls @($stationUrl, $resultUrl) `
        -Blockers $blockers `
        -Notes @("Confirmed site-specific WQP export using deterministic Station/search and Result/search endpoints.") `
        -JoinKeys @("MonitoringLocationIdentifier", "ActivityStartDate", "year", "month", "ano_mes") `
        -RawArtifacts $artifacts
}

function Collect-WqpOrganizationStations {
    param(
        [string]$TargetId,
        [string]$Organization,
        [string]$DatasetName
    )

    $targetDirRel = "collection/$TargetId"
    $targetDir = Join-Path $script:RunDir $targetDirRel
    Ensure-Dir $targetDir

    $stationUrl = "https://www.waterqualitydata.us/data/Station/search?organization=$Organization&mimeType=csv&zip=no&providers=NWIS"
    $stationRel = "$targetDirRel/station_$Organization.csv"
    $artifacts = @()
    $blockers = @()

    try {
        Invoke-Download -Uri $stationUrl -OutFile (Join-Path $script:RunDir $stationRel)
        $artifacts += Normalize-Artifact -RelativePath $stationRel -DownloadUrl $stationUrl -FileFormat "csv" -MediaType "text/csv"
    } catch {
        $blockers += "Organization Station/search failed: $($_.Exception.Message)"
    }

    $status = if ($artifacts.Count -gt 0) { "collected" } else { "error" }
    return New-TargetRecord `
        -TargetId $TargetId `
        -SourceName "waterqualitydata.us" `
        -DatasetName $DatasetName `
        -CollectionStatus $status `
        -AccessType "direct_download" `
        -CollectionMethod "organization_station_inventory_export" `
        -ProvenanceUrls @($stationUrl) `
        -Blockers $blockers `
        -Notes @("The generic provider target was normalized into a station inventory export for organization USGS-GA.") `
        -JoinKeys @("OrganizationIdentifier", "MonitoringLocationIdentifier") `
        -RawArtifacts $artifacts
}

function Collect-UsgsSiteBundle {
    param(
        [string]$TargetId,
        [string]$DatasetName,
        [string]$SiteNo,
        [string]$ParameterList
    )

    $targetDirRel = "collection/$TargetId"
    $targetDir = Join-Path $script:RunDir $targetDirRel
    Ensure-Dir $targetDir

    $siteUrl = "https://waterservices.usgs.gov/nwis/site/?format=rdb&sites=$SiteNo&siteOutput=expanded"
    $ivUrl = "https://waterservices.usgs.gov/nwis/iv/?format=json&sites=$SiteNo&startDT=$RequestedPeriodStart&endDT=$RequestedPeriodEnd&parameterCd=$ParameterList&siteStatus=all"
    $dvUrl = "https://waterservices.usgs.gov/nwis/dv/?format=json&sites=$SiteNo&startDT=$RequestedPeriodStart&endDT=$RequestedPeriodEnd&parameterCd=$ParameterList&siteStatus=all"

    $siteRel = "$targetDirRel/site_$SiteNo.rdb"
    $ivRel = "$targetDirRel/iv_$SiteNo.json"
    $dvRel = "$targetDirRel/dv_$SiteNo.json"

    $artifacts = @()
    $blockers = @()

    foreach ($item in @(
        @{ Url = $siteUrl; Rel = $siteRel; Format = "rdb"; Media = "text/plain" },
        @{ Url = $ivUrl; Rel = $ivRel; Format = "json"; Media = "application/json" },
        @{ Url = $dvUrl; Rel = $dvRel; Format = "json"; Media = "application/json" }
    )) {
        try {
            Invoke-Download -Uri $item.Url -OutFile (Join-Path $script:RunDir $item.Rel)
            $artifacts += Normalize-Artifact -RelativePath $item.Rel -DownloadUrl $item.Url -FileFormat $item.Format -MediaType $item.Media
        } catch {
            $blockers += "USGS endpoint failed for $($item.Rel): $($_.Exception.Message)"
        }
    }

    $status = if ($artifacts.Count -eq 3) { "collected" } elseif ($artifacts.Count -gt 0) { "partial" } else { "error" }
    return New-TargetRecord `
        -TargetId $TargetId `
        -SourceName "waterservices.usgs.gov" `
        -DatasetName $DatasetName `
        -CollectionStatus $status `
        -AccessType "api_access" `
        -CollectionMethod "direct_usgs_site_iv_dv" `
        -ProvenanceUrls @($siteUrl, $ivUrl, $dvUrl) `
        -Blockers $blockers `
        -Notes @("Generic USGS target normalized to an explicit site number before collection.") `
        -JoinKeys @("site_no", "date", "datetime") `
        -RawArtifacts $artifacts
}

function Collect-ScienceBaseRelease {
    param(
        [string]$TargetId,
        [string]$DatasetName,
        [string]$ItemId
    )

    $targetDirRel = "collection/$TargetId"
    $targetDir = Join-Path $script:RunDir $targetDirRel
    Ensure-Dir $targetDir

    $metaUrl = "https://www.sciencebase.gov/catalog/item/$($ItemId)?format=json"
    $metaRel = "$targetDirRel/sciencebase_$ItemId.json"
    $artifacts = @()
    $blockers = @()

    try {
        $payload = Invoke-DownloadJson -Uri $metaUrl -OutFile (Join-Path $script:RunDir $metaRel)
        $artifacts += Normalize-Artifact -RelativePath $metaRel -DownloadUrl $metaUrl -FileFormat "json" -MediaType "application/json"
        $files = @($payload.files | Where-Object { $_.contentType -match "csv" -or $_.name -match "\.csv$" })
        foreach ($file in $files) {
            $safeName = ($file.name -replace "[^\w\.-]", "_")
            $rel = "$targetDirRel/$safeName"
            try {
                Invoke-Download -Uri $file.url -OutFile (Join-Path $script:RunDir $rel)
                $artifacts += Normalize-Artifact -RelativePath $rel -DownloadUrl $file.url -FileFormat "csv" -MediaType "text/csv"
            } catch {
                $blockers += "ScienceBase attached file failed: $($file.name) - $($_.Exception.Message)"
            }
        }
    } catch {
        $blockers += "ScienceBase metadata failed: $($_.Exception.Message)"
    }

    $status = if ($artifacts.Count -gt 1) { "collected" } elseif ($artifacts.Count -eq 1) { "partial" } else { "error" }
    return New-TargetRecord `
        -TargetId $TargetId `
        -SourceName "sciencebase.gov" `
        -DatasetName $DatasetName `
        -CollectionStatus $status `
        -AccessType "direct_download" `
        -CollectionMethod "sciencebase_metadata_plus_attached_csvs" `
        -ProvenanceUrls @($metaUrl) `
        -Blockers $blockers `
        -Notes @("Catalog.data.gov landing was replaced by the canonical ScienceBase item and attached CSV files.") `
        -JoinKeys @("timestamp", "station", "parameter") `
        -RawArtifacts $artifacts
}

function Collect-StaticBundle {
    param(
        [string]$TargetId,
        [string]$SourceName,
        [string]$DatasetName,
        [object[]]$Downloads,
        [string[]]$Notes = @()
    )

    $targetDirRel = "collection/$TargetId"
    $targetDir = Join-Path $script:RunDir $targetDirRel
    Ensure-Dir $targetDir

    $artifacts = @()
    $blockers = @()
    foreach ($download in $Downloads) {
        $rel = "$targetDirRel/$($download.FileName)"
        try {
            if ($download.Text) {
                Invoke-DownloadText -Uri $download.Url -OutFile (Join-Path $script:RunDir $rel) | Out-Null
            } else {
                Invoke-Download -Uri $download.Url -OutFile (Join-Path $script:RunDir $rel)
            }
            $artifacts += Normalize-Artifact -RelativePath $rel -DownloadUrl $download.Url -FileFormat $download.FileFormat -MediaType $download.MediaType -Notes @($download.Note)
        } catch {
            $blockers += "Download failed for $($download.Url): $($_.Exception.Message)"
        }
    }

    $status = if ($artifacts.Count -eq $Downloads.Count) { "collected" } elseif ($artifacts.Count -gt 0) { "partial" } else { "error" }
    return New-TargetRecord `
        -TargetId $TargetId `
        -SourceName $SourceName `
        -DatasetName $DatasetName `
        -CollectionStatus $status `
        -AccessType "direct_download" `
        -CollectionMethod "curated_direct_downloads" `
        -ProvenanceUrls @($Downloads | ForEach-Object { $_.Url }) `
        -Blockers $blockers `
        -Notes $Notes `
        -JoinKeys @() `
        -RawArtifacts $artifacts
}

if (-not $RunId) {
    $RunId = "operational-collect-savannah-broken-retry-" + (Get-Date -Format "yyyyMMdd-HHmmss")
}

$script:RunDir = Join-Path "data/runs" $RunId
Ensure-Dir $script:RunDir
Ensure-Dir (Join-Path $script:RunDir "config")
Ensure-Dir (Join-Path $script:RunDir "collection")
Ensure-Dir (Join-Path $script:RunDir "processing")
Ensure-Dir (Join-Path $script:RunDir "reports")

$options = [ordered]@{
    source_research_id = $SearchRunId
    target_window_years = 20
    requested_period_start = $RequestedPeriodStart
    requested_period_end = $RequestedPeriodEnd
    purpose = "retry broken Savannah River discovery targets with corrected canonical endpoints"
    source_failed_collection = "data/runs/operational-collect-savannah-system-20260411-200900/manifest.json"
}
Write-JsonFile -Path (Join-Path $script:RunDir "config/collection-options.json") -Object $options

$targets = @()
$targets += Collect-WqpOrganizationStations -TargetId "02-water-quality-data-sites-in-georgia" -Organization "USGS-GA" -DatasetName "Water Quality Data Sites in Georgia"
$targets += Collect-ScienceBaseRelease -TargetId "03-water-quality-measurements-in-savannah-river-savannah-georgia-2020" -DatasetName "Water Quality Measurements in Savannah River, Savannah, Georgia, 2020" -ItemId "5f8746c182cebef40f1970e3"
$targets += Collect-StaticBundle -TargetId "05-epa-enforcement-and-compliance-history-online-data-sets" -SourceName "echo.epa.gov" -DatasetName "EPA Enforcement and Compliance History Online Data Sets" -Downloads @(
    @{ Url = "https://echo.epa.gov/tools/data-downloads"; FileName = "echo_data_downloads.html"; FileFormat = "html"; MediaType = "text/html"; Text = $true; Note = "Canonical ECHO data downloads page." },
    @{ Url = "https://echo.epa.gov/files/echodownloads/npdes_downloads.zip"; FileName = "npdes_downloads.zip"; FileFormat = "zip"; MediaType = "application/zip"; Text = $false; Note = "ICIS-NPDES National Dataset (Part 1)." },
    @{ Url = "https://echo.epa.gov/files/echodownloads/npdes_eff_downloads.zip"; FileName = "npdes_eff_downloads.zip"; FileFormat = "zip"; MediaType = "application/zip"; Text = $false; Note = "ICIS-NPDES National Dataset (Part 2 - effluent violations)." },
    @{ Url = "https://echo.epa.gov/files/echodownloads/npdes_attains_downloads.zip"; FileName = "npdes_attains_downloads.zip"; FileFormat = "zip"; MediaType = "application/zip"; Text = $false; Note = "NPDES Catchment Indexing and Assessed Waters." }
) -Notes @("Catalog.data.gov landing was replaced by the official ECHO downloads page and relevant water-pressure ZIP bundles.")
$targets += Collect-UsgsSiteBundle -TargetId "06-savannah-river-water-data-at-usace-dock" -DatasetName "Savannah River Water Data at USACE Dock" -SiteNo "021989773" -ParameterList "00060,00065,00010,00095,00300,00400,63680"
$targets += Collect-UsgsSiteBundle -TargetId "07-usgs-savannah-river-water-data" -DatasetName "USGS Savannah River Water Data" -SiteNo "021989773" -ParameterList "00060,00065,00010,00095,00300,00400,63680"
$targets += Collect-WqpSiteBundle -TargetId "08-savannah-river-water-quality-data-at-us-1-augusta-ga" -SiteId "USGS-02196671" -DatasetName "Savannah River Water Quality Data at US 1, Augusta, GA"
$targets += Collect-StaticBundle -TargetId "09-water-quality-study-of-savannah-river-basin-2006-2008" -SourceName "open.clemson.edu" -DatasetName "Water Quality Study of Savannah River Basin (2006-2008)" -Downloads @(
    @{ Url = "https://open.clemson.edu/cgi/viewcontent.cgi?article=1000&context=water-resources"; FileName = "water_quality_study_middle_lower_savannah_2006_2008.pdf"; FileFormat = "pdf"; MediaType = "application/pdf"; Text = $false; Note = "Canonical Clemson PDF link." }
) -Notes @("The broken bare cgi/viewcontent URL was replaced by the article-specific Clemson PDF.")
$targets += Collect-WqpSiteBundle -TargetId "10-water-quality-data-savannah-river-near-clyo-ga" -SiteId "USGS-02198500" -DatasetName "Water Quality Data - Savannah River near Clyo, GA"
$targets += Collect-StaticBundle -TargetId "11-water-quality-conditions-in-georgia" -SourceName "waterdata.usgs.gov" -DatasetName "Water Quality Conditions in Georgia" -Downloads @(
    @{ Url = "https://waterdata.usgs.gov/ga/nwis/uv"; FileName = "usgs_ga_nwis_uv.html"; FileFormat = "html"; MediaType = "text/html"; Text = $true; Note = "Generic Georgia current-conditions page still works at /ga/nwis/uv." }
) -Notes @("The original /ga/nwis/current target is dead. The working state landing page was captured, while site-specific Savannah data are handled in targets 06 and 07.")
$targets += Collect-StaticBundle -TargetId "13-water-quality-in-georgia" -SourceName "epd.georgia.gov" -DatasetName "Water Quality in Georgia" -Downloads @(
    @{ Url = "https://epd.georgia.gov/https%3A/epd.georgia.gov/assessment/water-quality-georgia"; FileName = "water_quality_in_georgia.html"; FileFormat = "html"; MediaType = "text/html"; Text = $true; Note = "Canonical page reached through the odd but working EPD URL." },
    @{ Url = "https://epd.georgia.gov/media/131606/download"; FileName = "ga_2024_305b_303d_integrated_report.pdf"; FileFormat = "pdf"; MediaType = "application/pdf"; Text = $false; Note = "2024 Georgia 305(b)/303(d) Integrated Report." },
    @{ Url = "https://epd.georgia.gov/document/document/2024305b303dexcelversionxlsx/download"; FileName = "ga_2024_305b_303d_list.xlsx"; FileFormat = "xlsx"; MediaType = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"; Text = $false; Note = "2024 Georgia 305(b)/303(d) list in Excel format." },
    @{ Url = "https://epd.georgia.gov/document/document/ga2024305b303dshapefilezip/download"; FileName = "ga_2024_305b_303d_gis.zip"; FileFormat = "zip"; MediaType = "application/zip"; Text = $false; Note = "2024 Georgia 305(b)/303(d) GIS dataset." }
) -Notes @("The malformed discovery URL was replaced by the working Water Quality in Georgia page plus core 2024 tabular and GIS artifacts.")

Write-JsonFile -Path (Join-Path $script:RunDir "processing/01-collection-targets.json") -Object $targets

$manifest = [ordered]@{
    run_id = $RunId
    pipeline_name = "savannah_broken_targets_retry"
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    source_research_id = $SearchRunId
    target_count = $targets.Count
    target_ids = @($targets | ForEach-Object { $_.target_id })
    collected_count = @($targets | Where-Object collection_status -eq "collected").Count
    partial_count = @($targets | Where-Object collection_status -eq "partial").Count
    error_count = @($targets | Where-Object collection_status -eq "error").Count
    targets = $targets
}
Write-JsonFile -Path (Join-Path $script:RunDir "manifest.json") -Object $manifest

$targets |
    Select-Object target_id, source_name, dataset_name, collection_status, requested_period_start, requested_period_end, blockers |
    Export-Csv (Join-Path $script:RunDir "reports/collection_targets.csv") -NoTypeInformation -Encoding UTF8

$reportLines = @(
    "# Retry de alvos quebrados do Savannah River",
    "",
    "- Run: $RunId",
    "- Pesquisa origem: $SearchRunId",
    "- Janela-alvo: $RequestedPeriodStart -> $RequestedPeriodEnd",
    "- Targets: $($manifest.target_count)",
    "- Coletados: $($manifest.collected_count)",
    "- Parciais: $($manifest.partial_count)",
    "- Erros: $($manifest.error_count)",
    ""
)

foreach ($target in $targets) {
    $reportLines += "## $($target.target_id)"
    $reportLines += "- Fonte: $($target.source_name)"
    $reportLines += "- Dataset: $($target.dataset_name)"
    $reportLines += "- Status: $($target.collection_status)"
    foreach ($note in $target.notes) {
        $reportLines += "- Nota: $note"
    }
    foreach ($blocker in $target.blockers) {
        $reportLines += "- Bloqueio: $blocker"
    }
    $reportLines += ""
}

$reportPath = Join-Path $script:RunDir "reports/$RunId.md"
$reportLines -join "`n" | Set-Content -LiteralPath $reportPath -Encoding UTF8

Write-Output "run_id=$RunId"
Write-Output "run_dir=$script:RunDir"
Write-Output "manifest=$(Join-Path $script:RunDir 'manifest.json')"
Write-Output "report=$reportPath"
