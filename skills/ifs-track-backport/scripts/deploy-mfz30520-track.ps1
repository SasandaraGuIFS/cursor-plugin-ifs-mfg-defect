# Per-ticket deploy helper example (MFZ-30520). Copy/adapt as scripts/deploy-<jira-lower>-track.ps1
# when the same multi-file codegen+deploy sequence repeats across tracks. Use py, not python.
param(
    [Parameter(Mandatory = $true)][string]$Worktree,
    [Parameter(Mandatory = $true)][string]$JdbcConn
)

$ErrorActionPreference = 'Stop'
$gen = 'c:\Dev\Master\workspace\.claude\skills\ifs-codegen\tools\ifs-codegen.py'
$dep = 'c:\Dev\Master\workspace\.claude\skills\ifs-codegen\tools\ifs-deploy.mjs'

function Deploy-FromModel {
    param([string]$ModelPath)
    $out = & py $gen generate $ModelPath --json 2>&1 | Out-String
    if ($out -notmatch '"masterScript":\s*"([^"]+)"') {
        throw "No masterScript from codegen: $ModelPath`n$out"
    }
    $script = $Matches[1] -replace '\\', '/'
    $script = $script -replace '/', '\'
    Write-Host ">>> $ModelPath -> $script"
    & node $dep $JdbcConn --script $script
    if ($LASTEXITCODE -ne 0) { throw "Deploy failed: $ModelPath" }
}

Deploy-FromModel "$Worktree\cfgchr\model\cfgchr\ConfigMediaManager.utility"
Deploy-FromModel "$Worktree\cfgbb\model\cfgbb\OrderConfigurationTmp.entity"
Deploy-FromModel "$Worktree\cfgrul\model\cfgrul\PartMediaCombinationHandling.projection"
Deploy-FromModel "$Worktree\cfgchr\model\cfgchr\PartConfigurationAssistantHandling.projection"
Deploy-FromModel "$Worktree\cfgbb\model\cfgbb\B2bConfigurationService.projection"
Write-Host "Deploy complete for $Worktree"
