# SQLcl deploy output helpers for generate_and_deploy.ps1
# Dot-source from a generated deploy script to ignore benign Java/SQLcl warnings
# and detect success from __DEPLOY_MARKER_DONE__ / __OBJ_STATUS__ markers.

function Convert-ToSqlclOutputLines {
    param([object[]]$Output)
    $lines = [System.Collections.Generic.List[string]]::new()
    foreach ($item in $Output) {
        if ($null -eq $item) { continue }

        $chunks = @()
        if ($item -is [System.Management.Automation.ErrorRecord]) {
            if ($null -ne $item.TargetObject) {
                $chunks += [string]$item.TargetObject
            } elseif ($item.Exception -and $item.Exception.Message -and
                $item.Exception.Message -ne 'System.Management.Automation.RemoteException') {
                $chunks += $item.Exception.Message
            }
        } else {
            $chunks += [string]$item
        }

        foreach ($chunk in $chunks) {
            if ([string]::IsNullOrWhiteSpace($chunk)) { continue }
            foreach ($sub in ($chunk -split "`r?`n")) {
                if (-not [string]::IsNullOrWhiteSpace($sub)) {
                    $lines.Add($sub.TrimEnd())
                }
            }
        }
    }
    return $lines.ToArray()
}

function Test-IsBenignSqlclLine {
    param([string]$Text)
    $benignPatterns = @(
        '^System\.Management\.Automation\.RemoteException\s*$',
        '^WARNING: A restricted method in java\.lang\.System has been called',
        '^WARNING: java\.lang\.System::load has been called by',
        '^WARNING: Use --enable-native-access=ALL-UNNAMED',
        '^WARNING: Restricted methods will be blocked in a future release'
    )
    foreach ($pat in $benignPatterns) {
        if ($Text -match $pat) { return $true }
    }
    return $false
}

function Get-SqlclMeaningfulLines {
    param([object[]]$Output)
    return @(Convert-ToSqlclOutputLines $Output | Where-Object { -not (Test-IsBenignSqlclLine $_) })
}

function Test-SqlclOutputError {
    param([object[]]$Output)
    $patterns = @(
        'ORA-\d+',
        'SP2-\d+',
        'PLS-\d+',
        'SEVERE',
        'Incorrect function',
        'Error report',
        'Error starting at',
        'created with compilation errors',
        'compiled with .* errors',
        'Exception in thread'
    )
    foreach ($line in (Get-SqlclMeaningfulLines $Output)) {
        foreach ($pat in $patterns) {
            if ($line -match $pat) { return $true }
        }
        if ($line -cmatch '\bERROR\b' -and $line -notmatch '(?i)no errors') { return $true }
    }
    return $false
}

function Test-SqlclDeploySucceeded {
    param(
        [object[]]$Output,
        [int]$ExitCode
    )
    $lines = Get-SqlclMeaningfulLines $Output
    $text = $lines -join "`n"

    if ($text -notmatch '__DEPLOY_MARKER_DONE__') {
        return $false
    }
    if ($text -match '__OBJ_STATUS__:.*:INVALID') { return $false }
    if ($text -match '__USER_ERR__:') { return $false }
    if ($text -match '__OBJ_STATUS__' -and $text -notmatch '__OBJ_STATUS__:.*:VALID') {
        return $false
    }
    if (Test-SqlclOutputError $lines) { return $false }

    return $true
}

function Get-SqlclFailureLines {
    param([object[]]$Output)
    $patterns = @(
        'ORA-\d+',
        'SP2-\d+',
        'PLS-\d+',
        'SEVERE',
        'Incorrect function',
        'Error report',
        'Error starting at',
        'created with compilation errors',
        'compiled with .* errors',
        'Exception in thread',
        '__OBJ_STATUS__:.*:INVALID',
        '__USER_ERR__:'
    )
    $failLines = @()
    foreach ($line in (Get-SqlclMeaningfulLines $Output)) {
        foreach ($pat in $patterns) {
            if ($line -match $pat) { $failLines += $line; break }
        }
        if ($line -cmatch '\bERROR\b' -and $line -notmatch '(?i)no errors') {
            $failLines += $line
        }
    }
    if ($failLines.Count -eq 0) {
        $failLines += 'Deploy did not complete successfully (missing __DEPLOY_MARKER_DONE__ or compilation errors).'
    }
    return $failLines
}

function Get-DeploySqlTrailer {
    param(
        [string]$Content,
        [switch]$IncludeDoneMarker
    )
    $lines = @('SHOW ERRORS;')
    $seen = @{}
    foreach ($line in ($Content -split "`r?`n")) {
        if ($line -match '(?i)^CREATE\s+OR\s+REPLACE\s+(PACKAGE\s+BODY|PACKAGE|VIEW|TRIGGER|PROCEDURE|FUNCTION|TYPE\s+BODY|TYPE)\s+(\w+)') {
            $objType = ($Matches[1].ToUpper() -replace '\s+', ' ')
            $objName = $Matches[2].ToUpper()
            $key = "$objType`:$objName"
            if ($seen.ContainsKey($key)) { continue }
            $seen[$key] = $true
            $lines += "SELECT '__OBJ_STATUS__:' || object_type || ':' || status FROM all_objects WHERE owner = USER AND object_name = '$objName' AND object_type = '$objType';"
            $lines += "SELECT '__USER_ERR__:' || name || ':' || line || ':' || position || ':' || text FROM user_errors WHERE name = '$objName' AND type = '$objType';"
        }
    }
    if ($IncludeDoneMarker) {
        $lines += 'PROMPT __DEPLOY_MARKER_DONE__'
    }
    return ($lines -join "`n")
}

function Resolve-DeployFileContent {
    param(
        [string]$FilePath,
        [string]$IfsappData  = 'IFSAPP_DATA',
        [string]$IfsappIndex = 'IFSAPP_INDEX',
        [string]$IfsappLob   = 'IFSAPP_LOB'
    )
    $content = Get-Content $FilePath -Raw -ErrorAction Stop
    $content = $content -replace [regex]::Escape('&IFSAPP_DATA'),  $IfsappData
    $content = $content -replace [regex]::Escape('&IFSAPP_INDEX'), $IfsappIndex
    $content = $content -replace [regex]::Escape('&IFSAPP_LOB'),   $IfsappLob
    return $content
}

function Invoke-SqlclDeployBatch {
    param(
        [string]$SqlclCmd,
        [string]$DbConn,
        [string[]]$DeployFiles,
        [string]$IfsappData  = 'IFSAPP_DATA',
        [string]$IfsappIndex = 'IFSAPP_INDEX',
        [string]$IfsappLob   = 'IFSAPP_LOB'
    )

    $scriptParts = [System.Collections.Generic.List[string]]::new()
    foreach ($f in $DeployFiles) {
        $fname = Split-Path $f -Leaf
        $content = Resolve-DeployFileContent -FilePath $f -IfsappData $IfsappData -IfsappIndex $IfsappIndex -IfsappLob $IfsappLob
        $scriptParts.Add("PROMPT __DEPLOY_FILE__:$fname")
        $scriptParts.Add($content)
        $scriptParts.Add((Get-DeploySqlTrailer -Content $content -IncludeDoneMarker:$false))
        $scriptParts.Add('')
    }
    $scriptParts.Add('PROMPT __DEPLOY_MARKER_DONE__')
    $scriptParts.Add('EXIT;')

    $tmpSql = [System.IO.Path]::GetTempFileName() + '.sql'
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($tmpSql, ($scriptParts -join "`n"), $utf8NoBom)

    try {
        $output = Invoke-SqlclDeployCommand -SqlclCmd $SqlclCmd -DbConn $DbConn -TmpSql $tmpSql
        $exitCode = $LASTEXITCODE
        $success = Test-SqlclDeploySucceeded -Output $output -ExitCode $exitCode
        return @{
            Output   = $output
            ExitCode = $exitCode
            Success  = $success
        }
    } finally {
        Remove-Item $tmpSql -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-SqlclDeployCommand {
    param(
        [string]$SqlclCmd,
        [string]$DbConn,
        [string]$TmpSql
    )
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        return & $SqlclCmd -S $DbConn "@$TmpSql" 2>&1 | ForEach-Object {
            if ($_ -is [System.Management.Automation.ErrorRecord]) {
                if ($null -ne $_.TargetObject) { $_.TargetObject }
                elseif ($_.Exception -and $_.Exception.Message -and
                    $_.Exception.Message -ne 'System.Management.Automation.RemoteException') {
                    $_.Exception.Message
                }
            } else {
                $_
            }
        }
    } finally {
        $ErrorActionPreference = $prevEap
    }
}
