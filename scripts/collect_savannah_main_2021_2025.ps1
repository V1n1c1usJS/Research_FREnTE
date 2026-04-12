param(
    [string]$RunId
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function New-RunId {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    return "operational-collect-savannah-main-2021-2025-$stamp"
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

    $base = [System.Uri]$BaseUrl
    return ([System.Uri]::new($base, $Href)).AbsoluteUri
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
        response = $response
        relative_path = $DestinationPath.Replace("$repoRoot\", "").Replace("\", "/")
        content_length = $item.Length
    }
}

function Invoke-DownloadBinary {
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
        content_length = $item.Length
    }
}

if (-not $RunId) {
    $RunId = New-RunId
}

$repoRoot = (Get-Location).Path
$runRoot = Join-Path $repoRoot "data/runs/$RunId"
$collectionRoot = Join-Path $runRoot "collection/savannah-main-2021-2025"
$configRoot = Join-Path $runRoot "config"
$processingRoot = Join-Path $runRoot "processing"
$reportsRoot = Join-Path $runRoot "reports"

Ensure-Dir -Path $collectionRoot
Ensure-Dir -Path $configRoot
Ensure-Dir -Path $processingRoot
Ensure-Dir -Path $reportsRoot

$archiveUrl = "https://savannahwaterquality.com/archive"
$years = 2021..2025
$targets = @()
foreach ($year in $years) {
    $targets += [ordered]@{
        source_slug = "savannah-main-$year"
        source_name = "City of Savannah Water Quality Reports"
        dataset_name = "Savannah Main Report $year"
        year = $year
        start_url = "https://savannahwaterquality.com/reports/$year/savannah-main"
        access_type = "web_page_or_pdf"
        data_format = "html_or_pdf"
    }
}

Save-Json -Path (Join-Path $configRoot "collection-options.json") -Data ([ordered]@{
    run_id = $RunId
    collected_at = (Get-Date).ToUniversalTime().ToString("o")
    source = "savannahwaterquality.com"
    target = "Savannah Main reports 2021-2025"
    archive_url = $archiveUrl
    targets = $targets
})

$artifacts = @()
$targetResults = @()
$landing = Invoke-DownloadText -Url $archiveUrl -DestinationPath (Join-Path $collectionRoot "archive_landing.html")
$artifacts += [ordered]@{
    relative_path = $landing.relative_path
    download_url = $archiveUrl
    file_format = "html"
    content_length = $landing.content_length
    status = "collected"
}

foreach ($target in $targets) {
    $targetDir = Join-Path $collectionRoot $target.source_slug
    Ensure-Dir -Path $targetDir
    $pageUrl = $target.start_url
    $status = "empty"
    $notes = @()
    $blockers = @()
    $rawArtifacts = @()

    try {
        $page = Invoke-DownloadText -Url $pageUrl -DestinationPath (Join-Path $targetDir "landing.html")
        $rawArtifacts += [ordered]@{
            relative_path = $page.relative_path
            download_url = $pageUrl
            file_format = "html"
            content_length = $page.content_length
            status = "collected"
        }

        $pdfLink = $null
        $content = $page.response.Content
        $hrefMatches = [regex]::Matches($content, 'href\s*=\s*"([^"]+)"')
        foreach ($match in $hrefMatches) {
            $link = Normalize-Link -BaseUrl $pageUrl -Href $match.Groups[1].Value
            if (-not $link) {
                continue
            }
            if ($link -match "\.pdf($|\?)") {
                $pdfLink = $link
                break
            }
        }

        $hasTables = $content -match "<table"
        $violationLink = $null
        foreach ($match in $hrefMatches) {
            $link = Normalize-Link -BaseUrl $pageUrl -Href $match.Groups[1].Value
            if (-not $link) {
                continue
            }
            if ($link -match "/violation($|\?)") {
                $violationLink = $link
                break
            }
        }

        if ($pdfLink) {
            $pdfPath = Join-Path $targetDir ("savannah-main-{0}.pdf" -f $target.year)
            $pdf = Invoke-DownloadBinary -Url $pdfLink -DestinationPath $pdfPath
            $rawArtifacts += [ordered]@{
                relative_path = $pdf.relative_path
                download_url = $pdfLink
                file_format = "pdf"
                content_length = $pdf.content_length
                status = "collected"
            }
            $notes += "Downloaded report PDF discovered from landing page."
            $status = "collected"
        } elseif ($hasTables) {
            $notes += "Collected the HTML report page with embedded water-quality tables."
            $status = "collected"
        } else {
            $notes += "Landing page collected, but no PDF link was discovered in-page."
            $status = "partial"
        }

        if ($violationLink) {
            try {
                $violation = Invoke-DownloadText -Url $violationLink -DestinationPath (Join-Path $targetDir "violation.html")
                $rawArtifacts += [ordered]@{
                    relative_path = $violation.relative_path
                    download_url = $violationLink
                    file_format = "html"
                    content_length = $violation.content_length
                    status = "collected"
                }
                $notes += "Collected the violation detail page linked from the report."
            } catch {
                $blockers += "Failed to collect violation page $violationLink : $($_.Exception.Message)"
            }
        }
    } catch {
        $blockers += $_.Exception.Message
        $status = "empty"
    }

    $targetResults += [ordered]@{
        source_slug = $target.source_slug
        source_name = $target.source_name
        dataset_name = $target.dataset_name
        year = $target.year
        start_url = $pageUrl
        status = $status
        blockers = $blockers
        notes = $notes
        raw_artifacts = $rawArtifacts
    }
}

Save-Json -Path (Join-Path $processingRoot "01-collection-targets.json") -Data $targetResults

$statusCounts = @($targetResults | Group-Object -Property status | ForEach-Object { @{ key = $_.Name; count = $_.Count } })
$manifest = [ordered]@{
    run_id = $RunId
    run_type = "collect-operational"
    collected_at = (Get-Date).ToUniversalTime().ToString("o")
    source = "savannahwaterquality.com"
    target = "Savannah Main reports 2021-2025"
    status_counts = $statusCounts
    outputs = [ordered]@{
        collection_targets_json = "processing/01-collection-targets.json"
        report_markdown = "reports/$RunId.md"
        report_csv = "reports/collection_targets.csv"
    }
}
Save-Json -Path (Join-Path $runRoot "manifest.json") -Data $manifest

$csvRows = foreach ($result in $targetResults) {
    [pscustomobject]@{
        source_slug = $result.source_slug
        year = $result.year
        status = $result.status
        start_url = $result.start_url
        notes = ($result.notes -join " | ")
        blockers = ($result.blockers -join " | ")
        artifact_count = $result.raw_artifacts.Count
    }
}
$csvRows | Export-Csv -Path (Join-Path $reportsRoot "collection_targets.csv") -NoTypeInformation -Encoding UTF8

$lines = @(
    "# $RunId",
    "",
    "- Source: City of Savannah Water Quality Reports",
    "- Target: Savannah Main 2021-2025",
    "- Archive: $archiveUrl",
    ""
)
foreach ($result in $targetResults) {
    $lines += "- $($result.year): $($result.status) ($($result.raw_artifacts.Count) artifacts)"
    if ($result.notes.Count -gt 0) {
        foreach ($note in $result.notes) {
            $lines += "  - Note: $note"
        }
    }
    if ($result.blockers.Count -gt 0) {
        foreach ($blocker in $result.blockers) {
            $lines += "  - Blocker: $blocker"
        }
    }
}
Write-Utf8File -Path (Join-Path $reportsRoot "$RunId.md") -Content ($lines -join "`n")

Write-Output "Created run $RunId"
