# Governance check -- runs after each Claude response via Stop hook.
# Reads project-status.md to find any in_progress step,
# checks git state, and prints only what is outstanding.

$root = Split-Path $PSScriptRoot -Parent
$statusFile = Join-Path $root "docs\project-status.md"

$inProgress = Select-String -Path $statusFile -Pattern "in_progress" -SimpleMatch
$uncommitted = & git -C $root status --porcelain 2>$null
$lastTag     = & git -C $root describe --tags --abbrev=0 2>$null
$lastCommit  = & git -C $root log -1 --format="%s" 2>$null

$issues = @()

if ($inProgress) {
    if ($uncommitted) {
        $issues += "UNCOMMITTED CHANGES detected - docs or code not yet saved to git"
    }
    if ($lastCommit -notmatch "^step-" -and $lastCommit -notmatch "^meta:") {
        $issues += "Last commit ('$lastCommit') does not follow step-N format - check CHANGELOG and commit"
    }
    if (-not $lastTag -or $lastTag -notmatch "^step-") {
        $issues += "No step-N git tag found - tag after each step completes"
    }
}

if ($issues.Count -gt 0) {
    $msg = "GOVERNANCE REMINDER:`n" + ($issues -join "`n") + "`n`nChecklist: project-status.md updated? CHANGELOG updated? git committed? git tagged? decision-log updated?"
    $output = [PSCustomObject]@{ systemMessage = $msg }
    Write-Output ($output | ConvertTo-Json -Compress)
}
