param(
    [string]$SearchRunId = "perplexity-intel-84e5fbc4",
    [string]$RunId
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
        [int]$Depth = 20
    )
    $Object | ConvertTo-Json -Depth $Depth | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Get-Headers {
    return @{
        "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
        "Accept" = "*/*"
    }
}

function Invoke-DownloadBinary {
    param(
        [string]$Uri,
        [string]$OutFile
    )
    Invoke-WebRequest -Uri $Uri -Headers (Get-Headers) -MaximumRedirection 10 -UseBasicParsing -OutFile $OutFile
    if ((Test-Path -LiteralPath $OutFile) -and ((Get-Item -LiteralPath $OutFile).Length -eq 0)) {
        throw "Downloaded file is empty: $OutFile"
    }
}

function Invoke-DownloadText {
    param(
        [string]$Uri,
        [string]$OutFile
    )
    $response = Invoke-WebRequest -Uri $Uri -Headers (Get-Headers) -MaximumRedirection 10 -UseBasicParsing
    $response.Content | Set-Content -LiteralPath $OutFile -Encoding UTF8
    return $response
}

function Invoke-DownloadJson {
    param(
        [string]$Uri,
        [string]$OutFile
    )
    $response = Invoke-WebRequest -Uri $Uri -Headers (Get-Headers) -MaximumRedirection 10 -UseBasicParsing
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
        [object[]]$RawArtifacts,
        [string]$CoverageWindowStatus,
        [string]$CoverageNote,
        [string]$TemporalCoverageHint = ""
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
        requested_period_start = "2006-01-01"
        requested_period_end = "2026-12-31"
        target_window_years = 20
        actual_period_start = $null
        actual_period_end = $null
        coverage_window_status = $CoverageWindowStatus
        coverage_note = $CoverageNote
        temporal_coverage_hint = $TemporalCoverageHint
        raw_artifacts = $RawArtifacts
    }
}

function Resolve-LinksFromHtml {
    param(
        [string]$HtmlText,
        [string]$BaseUrl
    )
    $results = New-Object System.Collections.Generic.List[string]
    $seen = New-Object 'System.Collections.Generic.HashSet[string]'
    $regex = 'href=["'']([^"'']+)["'']'
    $matches = [regex]::Matches($HtmlText, $regex, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    foreach ($match in $matches) {
        $href = $match.Groups[1].Value
        try {
            $absolute = [System.Uri]::new([System.Uri]$BaseUrl, $href).AbsoluteUri
        } catch {
            continue
        }
        if ($seen.Add($absolute)) {
            $results.Add($absolute) | Out-Null
        }
    }
    return @($results)
}

function Resolve-JsonLinks {
    param([object]$Object)
    $results = New-Object System.Collections.Generic.List[string]
    $seen = New-Object 'System.Collections.Generic.HashSet[string]'
    function Walk {
        param([object]$Value)
        if ($null -eq $Value) { return }
        if ($Value -is [System.Collections.IDictionary]) {
            foreach ($item in $Value.Values) { Walk $item }
            return
        }
        if ($Value -is [System.Collections.IEnumerable] -and -not ($Value -is [string])) {
            foreach ($item in $Value) { Walk $item }
            return
        }
        if ($Value -is [string] -and $Value -match '^https?://') {
            if ($Value -match '(\.csv|\.zip|\.pdf|\.xlsx|/download)') {
                if ($seen.Add($Value)) {
                    $results.Add($Value) | Out-Null
                }
            }
        }
    }
    Walk $Object
    return @($results)
}

function Collect-HtmlPortal {
    param(
        [string]$TargetId,
        [string]$SourceName,
        [string]$DatasetName,
        [string]$Url,
        [string[]]$JoinKeys = @()
    )

    $targetDirRel = "collection/$TargetId"
    $targetDir = Join-Path $script:RunDir $targetDirRel
    Ensure-Dir $targetDir

    $artifacts = @()
    $blockers = @()
    $notes = @()
    $provenance = @($Url)
    $landingRel = "$targetDirRel/landing.html"

    try {
        $response = Invoke-DownloadText -Uri $Url -OutFile (Join-Path $script:RunDir $landingRel)
        $artifacts += Normalize-Artifact -RelativePath $landingRel -DownloadUrl $Url -FileFormat "html" -MediaType "text/html" -Notes @("Landing page persisted for portal-first discovery.")
        $links = Resolve-LinksFromHtml -HtmlText ([string]$response.Content) -BaseUrl $response.BaseResponse.ResponseUri.AbsoluteUri
        $wanted = @($links | Where-Object { $_ -match '(\.pdf$|\.csv$|\.xlsx$|\.zip$|FeatureServer|MapServer|/download|arcgis)' } | Select-Object -First 8)
        if ($wanted.Count -eq 0) {
            $notes += "Landing page persisted but no direct export or GIS service link was discovered in the HTML."
        }
        foreach ($link in $wanted) {
            try {
                $name = [System.IO.Path]::GetFileName(([System.Uri]$link).AbsolutePath)
                if ([string]::IsNullOrWhiteSpace($name)) { $name = ('asset_' + ($wanted.IndexOf($link) + 1) + '.txt') }
                $ext = [System.IO.Path]::GetExtension($name)
                $rel = "$targetDirRel/$name"
                if ($link -match 'FeatureServer|MapServer|arcgis' -and -not $ext) {
                    $rel = "$targetDirRel/" + ($name + '.txt')
                    Invoke-DownloadText -Uri $link -OutFile (Join-Path $script:RunDir $rel) | Out-Null
                    $artifacts += Normalize-Artifact -RelativePath $rel -DownloadUrl $link -FileFormat "txt" -MediaType "text/plain" -Notes @("GIS or ArcGIS service endpoint discovered from landing page.")
                } elseif ($link -match '\.(pdf|zip|csv|xlsx)$' -or $link -match '/download') {
                    Invoke-DownloadBinary -Uri $link -OutFile (Join-Path $script:RunDir $rel)
                    $format = if ($ext) { $ext.TrimStart('.') } else { "bin" }
                    $artifacts += Normalize-Artifact -RelativePath $rel -DownloadUrl $link -FileFormat $format -MediaType "" -Notes @("Artifact discovered from landing page.")
                } else {
                    $rel = "$targetDirRel/" + ($name + '.txt')
                    Invoke-DownloadText -Uri $link -OutFile (Join-Path $script:RunDir $rel) | Out-Null
                    $artifacts += Normalize-Artifact -RelativePath $rel -DownloadUrl $link -FileFormat "txt" -MediaType "text/plain" -Notes @("Auxiliary endpoint discovered from landing page.")
                }
                $provenance += $link
            } catch {
                $blockers += "Discovered link failed: $link - $($_.Exception.Message)"
            }
        }
    } catch {
        $blockers += "Landing page failed: $($_.Exception.Message)"
    }

    $status = if ($artifacts.Count -gt 1) { "collected" } elseif ($artifacts.Count -eq 1) { "partial" } else { "blocked" }
    $coverage = if ($artifacts.Count -gt 0) { "not_applicable_static_context" } else { "unresolved_no_artifact" }
    $coverageNote = if ($artifacts.Count -gt 0) { "Static portal context persisted; temporal coverage requires later profiling from the captured artifacts." } else { "No artifact was persisted from the target portal." }

    return New-TargetRecord -TargetId $TargetId -SourceName $SourceName -DatasetName $DatasetName -CollectionStatus $status -AccessType "web_portal" -CollectionMethod "portal_first_then_deterministic_download" -ProvenanceUrls $provenance -Blockers $blockers -Notes $notes -JoinKeys $JoinKeys -RawArtifacts $artifacts -CoverageWindowStatus $coverage -CoverageNote $coverageNote
}

function Collect-ScienceBase {
    param(
        [string]$TargetId,
        [string]$DatasetName,
        [string]$Url
    )
    $targetDirRel = "collection/$TargetId"
    $targetDir = Join-Path $script:RunDir $targetDirRel
    Ensure-Dir $targetDir

    $artifacts = @()
    $blockers = @()
    $provenance = @($Url)
    $metaRel = "$targetDirRel/sciencebase_metadata.json"

    try {
        $payload = Invoke-DownloadJson -Uri $Url -OutFile (Join-Path $script:RunDir $metaRel)
        $artifacts += Normalize-Artifact -RelativePath $metaRel -DownloadUrl $Url -FileFormat "json" -MediaType "application/json" -Notes @("ScienceBase metadata persisted.")
        $links = Resolve-JsonLinks -Object $payload | Select-Object -First 8
        foreach ($link in $links) {
            try {
                $name = [System.IO.Path]::GetFileName(([System.Uri]$link).AbsolutePath)
                if ([string]::IsNullOrWhiteSpace($name)) { $name = "sciencebase_asset.bin" }
                $rel = "$targetDirRel/$name"
                Invoke-DownloadBinary -Uri $link -OutFile (Join-Path $script:RunDir $rel)
                $format = ([System.IO.Path]::GetExtension($name)).TrimStart('.')
                if (-not $format) { $format = 'bin' }
                $artifacts += Normalize-Artifact -RelativePath $rel -DownloadUrl $link -FileFormat $format -Notes @("Artifact discovered from ScienceBase metadata.")
                $provenance += $link
            } catch {
                $blockers += "ScienceBase asset failed: $link - $($_.Exception.Message)"
            }
        }
    } catch {
        $blockers += "ScienceBase metadata failed: $($_.Exception.Message)"
    }

    $status = if ($artifacts.Count -gt 1) { "collected" } elseif ($artifacts.Count -eq 1) { "partial" } else { "blocked" }
    $coverageNote = if ($artifacts.Count -gt 0) { "ScienceBase metadata and any discovered attached files were persisted; returned period is campaign-based and not expected to meet the 20-year target window." } else { "No ScienceBase artifact was persisted." }
    return New-TargetRecord -TargetId $TargetId -SourceName "sciencebase.gov" -DatasetName $DatasetName -CollectionStatus $status -AccessType "direct_download" -CollectionMethod "sciencebase_metadata_plus_assets" -ProvenanceUrls $provenance -Blockers $blockers -Notes @() -JoinKeys @("station","timestamp","parameter") -RawArtifacts $artifacts -CoverageWindowStatus "campaign_context_shorter_than_target" -CoverageNote $coverageNote -TemporalCoverageHint "2020"
}

function Collect-DirectFile {
    param(
        [string]$TargetId,
        [string]$SourceName,
        [string]$DatasetName,
        [string]$Url,
        [string]$FileName
    )
    $targetDirRel = "collection/$TargetId"
    Ensure-Dir (Join-Path $script:RunDir $targetDirRel)
    $rel = "$targetDirRel/$FileName"
    $artifacts = @()
    $blockers = @()
    try {
        Invoke-DownloadBinary -Uri $Url -OutFile (Join-Path $script:RunDir $rel)
        $format = ([System.IO.Path]::GetExtension($FileName)).TrimStart('.')
        if (-not $format) { $format = 'bin' }
        $artifacts += Normalize-Artifact -RelativePath $rel -DownloadUrl $Url -FileFormat $format -Notes @("Direct canonical file persisted.")
    } catch {
        $blockers += "Direct file failed: $($_.Exception.Message)"
    }
    $status = if ($artifacts.Count -gt 0) { "collected" } else { "blocked" }
    return New-TargetRecord -TargetId $TargetId -SourceName $SourceName -DatasetName $DatasetName -CollectionStatus $status -AccessType "direct_download" -CollectionMethod "deterministic_http_download" -ProvenanceUrls @($Url) -Blockers $blockers -Notes @() -JoinKeys @() -RawArtifacts $artifacts -CoverageWindowStatus "campaign_context_shorter_than_target" -CoverageNote "Canonical direct file attempted for a campaign/report target." -TemporalCoverageHint "2006-2008"
}

if (-not $RunId) {
    $RunId = "operational-collect-savannah-modern-short-" + (Get-Date -Format "yyyyMMdd-HHmmss")
}

$script:RunDir = Join-Path "data/runs" $RunId
Ensure-Dir $script:RunDir
Ensure-Dir (Join-Path $script:RunDir "config")
Ensure-Dir (Join-Path $script:RunDir "collection")
Ensure-Dir (Join-Path $script:RunDir "processing")
Ensure-Dir (Join-Path $script:RunDir "reports")

$options = [ordered]@{
    source_research_id = $SearchRunId
    purpose = "short targeted pass for modern Savannah River pollution-context gaps"
    requested_period_start = "2006-01-01"
    requested_period_end = "2026-12-31"
    target_window_years = 20
    focus_targets = @(
        "savannahwaterquality archive",
        "savannahwaterquality pfas",
        "savannahriverkeeper program overview",
        "savannahriverkeeper forever chemicals",
        "sciencebase Savannah 2020",
        "Clemson 2006-2008",
        "SRNS DOE annual reports"
    )
}
Write-JsonFile -Path (Join-Path $script:RunDir "config/collection-options.json") -Object $options

$targets = @()
$targets += Collect-HtmlPortal -TargetId "01-savannah-water-quality-archive" -SourceName "savannahwaterquality.com" -DatasetName "City of Savannah Water Quality Archive" -Url "https://savannahwaterquality.com/archive" -JoinKeys @("date","year","year_month")
$targets += Collect-HtmlPortal -TargetId "02-savannah-water-quality-pfas" -SourceName "savannahwaterquality.com" -DatasetName "City of Savannah PFAS" -Url "https://savannahwaterquality.com/pfas" -JoinKeys @("date","year","year_month")
$targets += Collect-HtmlPortal -TargetId "03-savannah-riverkeeper-program-overview" -SourceName "savannahriverkeeper.org" -DatasetName "Savannah Riverkeeper Program Overview" -Url "https://savannahriverkeeper.org/program-overview"
$targets += Collect-HtmlPortal -TargetId "04-savannah-riverkeeper-forever-chemicals" -SourceName "savannahriverkeeper.org" -DatasetName "Savannah Riverkeeper Forever Chemicals" -Url "https://savannahriverkeeper.org/forever-chemicals"
$targets += Collect-ScienceBase -TargetId "05-sciencebase-savannah-2020" -DatasetName "Water Quality Measurements in Savannah River, Savannah, Georgia 2020" -Url "https://www.sciencebase.gov/catalog/item/5f8746c182cebef40f1970e3?format=json"
$targets += Collect-DirectFile -TargetId "06-clemson-savannah-2006-2008" -SourceName "open.clemson.edu" -DatasetName "Water Quality Study of the Savannah River Basin (2006-2008)" -Url "https://open.clemson.edu/cgi/viewcontent.cgi?article=1000&context=water-resources" -FileName "water_quality_study_middle_lower_savannah_2006_2008.pdf"
$targets += Collect-HtmlPortal -TargetId "07-srns-doe-ars" -SourceName "srns.doe.gov" -DatasetName "SRNS Annual Reports and SRS Monitoring" -Url "https://srns.doe.gov/ars/"

Write-JsonFile -Path (Join-Path $script:RunDir "processing/01-collection-targets.json") -Object $targets

$manifest = [ordered]@{
    run_id = $RunId
    pipeline_name = "savannah_modern_short_collection"
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    source_research_id = $SearchRunId
    target_count = $targets.Count
    collected_count = @($targets | Where-Object collection_status -eq "collected").Count
    partial_count = @($targets | Where-Object collection_status -eq "partial").Count
    blocked_count = @($targets | Where-Object collection_status -eq "blocked").Count
    error_count = @($targets | Where-Object collection_status -eq "error").Count
    targets = $targets
}
Write-JsonFile -Path (Join-Path $script:RunDir "manifest.json") -Object $manifest

$csvRows = $targets | ForEach-Object {
    [pscustomobject]@{
        target_id = $_.target_id
        source_name = $_.source_name
        dataset_name = $_.dataset_name
        collection_status = $_.collection_status
        raw_artifact_count = $_.raw_artifacts.Count
        coverage_window_status = $_.coverage_window_status
        coverage_note = $_.coverage_note
        blockers = ($_.blockers -join " | ")
    }
}
$csvRows | Export-Csv (Join-Path $script:RunDir "reports/collection_targets.csv") -NoTypeInformation -Encoding UTF8

$report = @()
$report += "# Coleta curta moderna Savannah River"
$report += ""
$report += "- Run: $RunId"
$report += "- Escopo: lacunas modernas de poluicao/descarga do Savannah River"
$report += "- Metodo: portal-first apenas para descoberta de links/exportaveis; download HTTP deterministico quando possivel"
$report += ""
$report += "- Targets: $($targets.Count)"
$report += "- Coletados: $(@($targets | Where-Object collection_status -eq 'collected').Count)"
$report += "- Parciais: $(@($targets | Where-Object collection_status -eq 'partial').Count)"
$report += "- Bloqueados: $(@($targets | Where-Object collection_status -eq 'blocked').Count)"
$report += "- Erros: $(@($targets | Where-Object collection_status -eq 'error').Count)"
$report += ""
foreach ($target in $targets) {
    $report += "## $($target.target_id)"
    $report += ""
    $report += "- Status: $($target.collection_status)"
    $report += "- Fonte: $($target.source_name)"
    $report += "- Dataset: $($target.dataset_name)"
    $report += "- Artefatos: $($target.raw_artifacts.Count)"
    $report += "- Cobertura: $($target.coverage_note)"
    if ($target.blockers.Count -gt 0) {
        $report += "- Limites: $($target.blockers -join ' | ')"
    }
    $report += ""
}
Set-Content -LiteralPath (Join-Path $script:RunDir "reports/$RunId.md") -Value ($report -join "`r`n") -Encoding UTF8

Write-Output (@{
    run_id = $RunId
    run_dir = $script:RunDir
    manifest_path = (Join-Path $script:RunDir "manifest.json")
} | ConvertTo-Json -Depth 5)
