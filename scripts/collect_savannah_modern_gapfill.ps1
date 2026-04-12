param(
    [string]$RunId
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function New-RunId {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    return "operational-collect-savannah-modern-gapfill-$stamp"
}

function Ensure-Dir {
    param([string]$Path)
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Write-Utf8File {
    param(
        [string]$Path,
        [string]$Content
    )
    $dir = Split-Path -Parent $Path
    if ($dir) {
        Ensure-Dir -Path $dir
    }
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

function Save-Json {
    param(
        [string]$Path,
        $Data
    )
    $json = $Data | ConvertTo-Json -Depth 10
    Write-Utf8File -Path $Path -Content $json
}

function Normalize-Link {
    param(
        [string]$BaseUrl,
        [string]$Href
    )
    if ([string]::IsNullOrWhiteSpace($Href)) {
        return $null
    }

    if ($Href.StartsWith("http://") -or $Href.StartsWith("https://")) {
        return $Href
    }

    try {
        $base = [System.Uri]$BaseUrl
        $uri = [System.Uri]::new($base, $Href)
        return $uri.AbsoluteUri
    } catch {
        return $null
    }
}

function Get-SafeFileName {
    param(
        [string]$Url,
        [string]$Fallback
    )

    try {
        $uri = [System.Uri]$Url
        $name = [System.IO.Path]::GetFileName($uri.AbsolutePath)
        if (-not [string]::IsNullOrWhiteSpace($name)) {
            return $name
        }
    } catch {
    }

    return $Fallback
}

function Invoke-Download {
    param(
        [string]$Url,
        [string]$DestinationPath
    )

    Ensure-Dir -Path (Split-Path -Parent $DestinationPath)
    Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $DestinationPath

    $item = Get-Item -LiteralPath $DestinationPath -ErrorAction Stop
    if ($item.Length -le 0) {
        throw "Downloaded zero-byte artifact from $Url"
    }

    return @{
        relative_path = $DestinationPath.Replace("$repoRoot\", "").Replace("\", "/")
        download_url = $Url
        file_format = [System.IO.Path]::GetExtension($DestinationPath).TrimStart(".")
        content_length = $item.Length
        status = "collected"
        collected_at = (Get-Date).ToUniversalTime().ToString("o")
    }
}

function Invoke-DownloadText {
    param(
        [string]$Url,
        [string]$DestinationPath
    )

    Ensure-Dir -Path (Split-Path -Parent $DestinationPath)
    $response = Invoke-WebRequest -UseBasicParsing -Uri $Url
    Write-Utf8File -Path $DestinationPath -Content $response.Content

    $item = Get-Item -LiteralPath $DestinationPath -ErrorAction Stop
    if ($item.Length -le 0) {
        throw "Downloaded zero-byte text artifact from $Url"
    }

    return @{
        relative_path = $DestinationPath.Replace("$repoRoot\", "").Replace("\", "/")
        download_url = $Url
        file_format = [System.IO.Path]::GetExtension($DestinationPath).TrimStart(".")
        content_length = $item.Length
        status = "collected"
        collected_at = (Get-Date).ToUniversalTime().ToString("o")
        response = $response
    }
}

function Collect-HtmlWithLinks {
    param(
        [hashtable]$Target,
        [string]$RunCollectionRoot
    )

    $targetDir = Join-Path $RunCollectionRoot $Target.source_slug
    Ensure-Dir -Path $targetDir

    $artifacts = @()
    $notes = @()
    $blockers = @()

    try {
        $landing = Invoke-DownloadText -Url $Target.start_url -DestinationPath (Join-Path $targetDir "landing.html")
        $artifacts += @{
            relative_path = $landing.relative_path
            download_url = $landing.download_url
            file_format = "html"
            content_length = $landing.content_length
            status = "collected"
            collected_at = $landing.collected_at
        }

        $content = $landing.response.Content
        $regex = [regex]'href\s*=\s*"([^"]+)"'
        $matches = $regex.Matches($content) | ForEach-Object { Normalize-Link -BaseUrl $Target.start_url -Href $_.Groups[1].Value } | Where-Object { $_ } | Sort-Object -Unique

        $filtered = @()
        foreach ($link in $matches) {
            if ($Target.link_filter -and ($link -notmatch $Target.link_filter)) {
                continue
            }
            $filtered += $link
        }

        $filtered = $filtered | Select-Object -First $Target.max_links

        if (-not $filtered -or $filtered.Count -eq 0) {
            $notes += "Landing page collected, but no matching export links were discovered with the configured filter."
        } else {
            $notes += "Discovered $($filtered.Count) candidate link(s) from the landing page."
        }

        $linkIndex = 1
        foreach ($link in $filtered) {
            try {
                $ext = [System.IO.Path]::GetExtension(([System.Uri]$link).AbsolutePath)
                if ([string]::IsNullOrWhiteSpace($ext)) {
                    $ext = ".html"
                }
                $name = "{0:D2}_{1}" -f $linkIndex, (Get-SafeFileName -Url $link -Fallback ("artifact$linkIndex$ext"))
                $destination = Join-Path $targetDir $name

                if ($ext -match "\.(pdf|csv|xlsx|xls|zip|json|xml)$") {
                    $artifact = Invoke-Download -Url $link -DestinationPath $destination
                } else {
                    $artifact = Invoke-DownloadText -Url $link -DestinationPath $destination
                }

                $artifacts += @{
                    relative_path = $artifact.relative_path
                    download_url = $artifact.download_url
                    file_format = $artifact.file_format
                    content_length = $artifact.content_length
                    status = "collected"
                    collected_at = $artifact.collected_at
                }
            } catch {
                $blockers += "Failed to collect discovered link $link : $($_.Exception.Message)"
            }
            $linkIndex += 1
        }

        return @{
            status = $(if ($artifacts.Count -gt 1) { "collected" } else { "partial" })
            blockers = $blockers
            notes = $notes
            raw_artifacts = $artifacts
        }
    } catch {
        return @{
            status = "empty"
            blockers = @("Failed to collect landing page $($Target.start_url) : $($_.Exception.Message)")
            notes = @()
            raw_artifacts = @()
        }
    }
}

function Collect-DirectFile {
    param(
        [hashtable]$Target,
        [string]$RunCollectionRoot
    )

    $targetDir = Join-Path $RunCollectionRoot $Target.source_slug
    Ensure-Dir -Path $targetDir

    try {
        $fileName = if ($Target.file_name) { $Target.file_name } else { Get-SafeFileName -Url $Target.start_url -Fallback "artifact.bin" }
        $destination = Join-Path $targetDir $fileName
        $artifact = Invoke-Download -Url $Target.start_url -DestinationPath $destination

        return @{
            status = "collected"
            blockers = @()
            notes = @()
            raw_artifacts = @(
                @{
                    relative_path = $artifact.relative_path
                    download_url = $artifact.download_url
                    file_format = $artifact.file_format
                    content_length = $artifact.content_length
                    status = "collected"
                    collected_at = $artifact.collected_at
                }
            )
        }
    } catch {
        return @{
            status = "empty"
            blockers = @("Failed direct download $($Target.start_url) : $($_.Exception.Message)")
            notes = @()
            raw_artifacts = @()
        }
    }
}

function Collect-ScienceBase {
    param(
        [hashtable]$Target,
        [string]$RunCollectionRoot
    )

    $targetDir = Join-Path $RunCollectionRoot $Target.source_slug
    Ensure-Dir -Path $targetDir

    $artifacts = @()
    $notes = @()
    $blockers = @()

    try {
        $jsonArtifact = Invoke-DownloadText -Url $Target.start_url -DestinationPath (Join-Path $targetDir "sciencebase_item.json")
        $artifacts += @{
            relative_path = $jsonArtifact.relative_path
            download_url = $jsonArtifact.download_url
            file_format = "json"
            content_length = $jsonArtifact.content_length
            status = "collected"
            collected_at = $jsonArtifact.collected_at
        }

        $json = $jsonArtifact.response.Content | ConvertFrom-Json
        $candidateUrls = @()

        if ($json.files) {
            foreach ($file in $json.files) {
                if ($file.url) {
                    $candidateUrls += [string]$file.url
                }
            }
        }

        if ($json.facets) {
            foreach ($facet in $json.facets) {
                if ($facet.files) {
                    foreach ($file in $facet.files) {
                        if ($file.url) {
                            $candidateUrls += [string]$file.url
                        }
                    }
                }
            }
        }

        $candidateUrls = $candidateUrls | Sort-Object -Unique
        if (-not $candidateUrls -or $candidateUrls.Count -eq 0) {
            $notes += "ScienceBase item JSON collected, but no attached files were exposed in the parsed metadata."
        } else {
            $notes += "ScienceBase item JSON exposed $($candidateUrls.Count) attached file URL(s)."
        }

        $index = 1
        foreach ($url in ($candidateUrls | Select-Object -First 10)) {
            try {
                $fileName = "{0:D2}_{1}" -f $index, (Get-SafeFileName -Url $url -Fallback "sciencebase_$index.bin")
                $destination = Join-Path $targetDir $fileName
                $artifact = Invoke-Download -Url $url -DestinationPath $destination
                $artifacts += @{
                    relative_path = $artifact.relative_path
                    download_url = $artifact.download_url
                    file_format = $artifact.file_format
                    content_length = $artifact.content_length
                    status = "collected"
                    collected_at = $artifact.collected_at
                }
            } catch {
                $blockers += "Failed attached ScienceBase file $url : $($_.Exception.Message)"
            }
            $index += 1
        }

        return @{
            status = $(if ($artifacts.Count -gt 1) { "collected" } else { "partial" })
            blockers = $blockers
            notes = $notes
            raw_artifacts = $artifacts
        }
    } catch {
        return @{
            status = "empty"
            blockers = @("Failed ScienceBase item $($Target.start_url) : $($_.Exception.Message)")
            notes = @()
            raw_artifacts = @()
        }
    }
}

$repoRoot = (Resolve-Path ".").Path
if (-not $RunId) {
    $RunId = New-RunId
}

$runRoot = Join-Path $repoRoot ("data/runs/" + $RunId)
$configRoot = Join-Path $runRoot "config"
$collectionRoot = Join-Path $runRoot "collection"
$processingRoot = Join-Path $runRoot "processing"
$reportsRoot = Join-Path $runRoot "reports"

Ensure-Dir -Path $configRoot
Ensure-Dir -Path $collectionRoot
Ensure-Dir -Path $processingRoot
Ensure-Dir -Path $reportsRoot

$targets = @(
    @{
        target_id = "1001-savannah-water-quality-archive"
        source_name = "savannahwaterquality.com"
        source_slug = "1001-savannah-water-quality-archive"
        dataset_name = "Savannah Water Quality archive"
        start_url = "https://savannahwaterquality.com/archive"
        method = "html_links"
        link_filter = "savannahwaterquality\.com/reports/|\.pdf$|\.csv$|\.xlsx?$"
        max_links = 20
    },
    @{
        target_id = "1002-savannah-water-quality-pfas"
        source_name = "savannahwaterquality.com"
        source_slug = "1002-savannah-water-quality-pfas"
        dataset_name = "Savannah Water Quality PFAS"
        start_url = "https://savannahwaterquality.com/pfas"
        method = "html_links"
        link_filter = "savannahwaterquality\.com|\.pdf$|\.csv$|\.xlsx?$"
        max_links = 12
    },
    @{
        target_id = "1003-savannah-riverkeeper-program-overview"
        source_name = "savannahriverkeeper.org"
        source_slug = "1003-savannah-riverkeeper-program-overview"
        dataset_name = "Savannah Riverkeeper program overview"
        start_url = "https://savannahriverkeeper.org/program-overview.html"
        method = "html_links"
        link_filter = "arcgis\.com|storymaps\.arcgis\.com|savannahriverkeeper\.org|\.pdf$|\.csv$"
        max_links = 12
    },
    @{
        target_id = "1004-savannah-riverkeeper-forever-chemicals"
        source_name = "savannahriverkeeper.org"
        source_slug = "1004-savannah-riverkeeper-forever-chemicals"
        dataset_name = "Savannah Riverkeeper forever chemicals"
        start_url = "https://www.savannahriverkeeper.org/forever-chemicals-and-our-watershed.html"
        method = "html_links"
        link_filter = "arcgis\.com|storymaps\.arcgis\.com|savannahriverkeeper\.org|\.pdf$|\.csv$"
        max_links = 12
    },
    @{
        target_id = "1005-sciencebase-savannah-2020"
        source_name = "sciencebase.gov"
        source_slug = "1005-sciencebase-savannah-2020"
        dataset_name = "Water Quality Measurements in Savannah River, Savannah, Georgia, 2020"
        start_url = "https://www.sciencebase.gov/catalog/item/5f8746c182cebef40f1970e3?format=json"
        method = "sciencebase"
    },
    @{
        target_id = "1006-clemson-middle-lower-savannah-2006-2008"
        source_name = "open.clemson.edu"
        source_slug = "1006-clemson-middle-lower-savannah-2006-2008"
        dataset_name = "Water Quality Study of the Savannah River Basin (2006-2008)"
        start_url = "https://open.clemson.edu/cgi/viewcontent.cgi?article=1000&context=water-resources"
        method = "direct_file"
        file_name = "clemson_middle_lower_savannah_2006_2008.pdf"
    },
    @{
        target_id = "1007-srns-doe-ars"
        source_name = "srns.doe.gov"
        source_slug = "1007-srns-doe-ars"
        dataset_name = "SRNS ARS environmental reports"
        start_url = "https://srns.doe.gov/ars/"
        method = "html_links"
        link_filter = "environmental|annual|report|tritium|pfas|\.pdf$"
        max_links = 20
    }
)

Save-Json -Path (Join-Path $configRoot "collection-options.json") -Data @{
    source_research_id = "perplexity-intel-84e5fbc4"
    profile = "savannah-modern-gapfill"
    requested_period_start = "2006-01-01"
    requested_period_end = (Get-Date -Format "yyyy-MM-dd")
    target_window_years = 20
    target_count = $targets.Count
}

$targetResults = @()
foreach ($target in $targets) {
    $result = switch ($target.method) {
        "html_links" { Collect-HtmlWithLinks -Target $target -RunCollectionRoot $collectionRoot }
        "direct_file" { Collect-DirectFile -Target $target -RunCollectionRoot $collectionRoot }
        "sciencebase" { Collect-ScienceBase -Target $target -RunCollectionRoot $collectionRoot }
        default {
            @{
                status = "empty"
                blockers = @("Unknown collection method $($target.method)")
                notes = @()
                raw_artifacts = @()
            }
        }
    }

    $targetResults += [ordered]@{
        target_id = $target.target_id
        source_name = $target.source_name
        dataset_name = $target.dataset_name
        collection_status = $result.status
        access_type = "direct_download"
        collection_method = $target.method
        requires_auth = $false
        provenance_urls = @($target.start_url)
        blockers = $result.blockers
        notes = $result.notes
        raw_artifacts = $result.raw_artifacts
        target_window_years = 20
        requested_period_start = "2006-01-01"
        requested_period_end = (Get-Date -Format "yyyy-MM-dd")
    }
}

$manifest = [ordered]@{
    run_id = $RunId
    pipeline_name = "savannah_modern_gapfill"
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    source_research_id = "perplexity-intel-84e5fbc4"
    target_count = $targetResults.Count
    collected_count = ($targetResults | Where-Object { $_.collection_status -eq "collected" }).Count
    partial_count = ($targetResults | Where-Object { $_.collection_status -eq "partial" }).Count
    empty_count = ($targetResults | Where-Object { $_.collection_status -eq "empty" }).Count
    blocked_count = ($targetResults | Where-Object { $_.collection_status -eq "blocked" }).Count
    error_count = ($targetResults | Where-Object { $_.collection_status -eq "error" }).Count
    targets = $targetResults
}

Save-Json -Path (Join-Path $runRoot "manifest.json") -Data $manifest
Save-Json -Path (Join-Path $processingRoot "01-collection-targets.json") -Data $targetResults

$csvRows = $targetResults | ForEach-Object {
    [pscustomobject]@{
        target_id = $_.target_id
        source_name = $_.source_name
        dataset_name = $_.dataset_name
        collection_status = $_.collection_status
        artifact_count = $_.raw_artifacts.Count
        blocker_count = $_.blockers.Count
        note_count = $_.notes.Count
    }
}
$csvRows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $reportsRoot "collection_targets.csv")

$reportLines = @()
$reportLines += "# $RunId"
$reportLines += ""
$reportLines += "- source_research_id: perplexity-intel-84e5fbc4"
$reportLines += "- target_count: $($manifest.target_count)"
$reportLines += "- collected: $($manifest.collected_count)"
$reportLines += "- partial: $($manifest.partial_count)"
$reportLines += "- empty: $($manifest.empty_count)"
$reportLines += ""
foreach ($target in $targetResults) {
    $reportLines += "## $($target.target_id)"
    $reportLines += ""
    $reportLines += "- source: $($target.source_name)"
    $reportLines += "- dataset: $($target.dataset_name)"
    $reportLines += "- status: $($target.collection_status)"
    $reportLines += "- artifacts: $($target.raw_artifacts.Count)"
    if ($target.notes.Count -gt 0) {
        foreach ($note in $target.notes) {
            $reportLines += "- note: $note"
        }
    }
    if ($target.blockers.Count -gt 0) {
        foreach ($blocker in $target.blockers) {
            $reportLines += "- blocker: $blocker"
        }
    }
    $reportLines += ""
}

Write-Utf8File -Path (Join-Path $reportsRoot "$RunId.md") -Content ($reportLines -join [Environment]::NewLine)

Write-Output $RunId
