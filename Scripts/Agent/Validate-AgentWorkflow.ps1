[CmdletBinding()]
param(
    [string]$RepoRoot,
    [int]$MaxSnapshotAgeDays = 14
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}
$failures = [System.Collections.Generic.List[string]]::new()

$required = @(
    "AGENTS.md",
    "Docs/Knowledge/README.md",
    "Docs/Knowledge/project-overview.md",
    "Docs/Knowledge/design-snapshot.md",
    "Docs/Knowledge/implementation-status.md",
    "Docs/Knowledge/open-questions.md",
    "Docs/Knowledge/source-manifest.yaml",
    "Docs/Agent/approval-gate.md",
    "Docs/Agent/TEAM-SOP.md",
    "Docs/MCP/SOP.md",
    ".agents/skills/time-shuttler-context/SKILL.md",
    ".agents/skills/ue5-change-gate/SKILL.md",
    ".agents/skills/drive-knowledge-sync/SKILL.md"
)

foreach ($relative in $required) {
    if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot $relative) -PathType Leaf)) {
        $failures.Add("Missing required file: $relative")
    }
}

$skillFiles = Get-ChildItem -LiteralPath (Join-Path $RepoRoot ".agents\skills") -Filter "SKILL.md" -File -Recurse -ErrorAction SilentlyContinue
foreach ($skill in $skillFiles) {
    $text = Get-Content -Raw -LiteralPath $skill.FullName
    if ($text -notmatch '(?s)^---\s*\r?\nname:\s*[a-z0-9-]+\s*\r?\ndescription:\s*.+?\r?\n---') {
        $failures.Add("Invalid or incomplete skill frontmatter: $($skill.FullName)")
    }
}

$manifestPath = Join-Path $RepoRoot "Docs\Knowledge\source-manifest.yaml"
if (Test-Path -LiteralPath $manifestPath) {
    $manifest = Get-Content -Raw -LiteralPath $manifestPath
    $match = [regex]::Match($manifest, 'observed_at:\s*"([^"]+)"')
    if (-not $match.Success) {
        $failures.Add("Knowledge manifest has no snapshot observed_at value.")
    } else {
        $observed = [DateTimeOffset]::Parse($match.Groups[1].Value)
        $age = [DateTimeOffset]::Now - $observed
        if ($age.TotalDays -gt $MaxSnapshotAgeDays) {
            Write-Warning ("Knowledge snapshot is {0:N1} days old. Run `$drive-knowledge-sync before high-impact planning." -f $age.TotalDays)
        }
    }
}

if ($failures.Count -gt 0) {
    $failures | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Host "Agent workflow validation passed: $($required.Count) required files and $($skillFiles.Count) skills checked."
