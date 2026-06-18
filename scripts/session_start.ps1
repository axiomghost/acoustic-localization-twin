# SessionStart hook -- prints current project state when Claude opens.
$root = Split-Path $PSScriptRoot -Parent
$statusFile = Join-Path $root "docs\project-status.md"

# Find current step (in_progress or last DONE)
$inProgress = Select-String -Path $statusFile -Pattern "\| \d+ \|.*in_progress" | Select-Object -Last 1
$lastDone   = Select-String -Path $statusFile -Pattern "\| \d+ \|.*DONE" | Select-Object -Last 1
$lastTag    = & git -C $root describe --tags --abbrev=0 2>$null
$dirty      = & git -C $root status --porcelain 2>$null

if ($inProgress) {
    $stepInfo = $inProgress.Line.Trim()
    $status = "IN PROGRESS"
} elseif ($lastDone) {
    $stepInfo = $lastDone.Line.Trim()
    $status = "LAST COMPLETED"
} else {
    $stepInfo = "No steps found"
    $status = "UNKNOWN"
}

$dirtyNote = if ($dirty) { " | DIRTY - uncommitted changes exist" } else { " | git clean" }
$tagNote   = if ($lastTag) { " | last tag: $lastTag" } else { " | no tags yet" }

$msg = "PROJECT: Acoustic Source Localization Digital Twin`n"
$msg += "Step status ($status): $stepInfo`n"
$msg += "Git$tagNote$dirtyNote`n"
$msg += "Boot file: CLAUDE.md | Status: docs/project-status.md"

$output = [PSCustomObject]@{ systemMessage = $msg }
Write-Output ($output | ConvertTo-Json -Compress)
