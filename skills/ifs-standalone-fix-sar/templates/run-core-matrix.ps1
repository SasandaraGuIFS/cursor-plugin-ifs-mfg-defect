# Standalone fix SAR — RunCoreMatrix on MASTER DEV CMB
$ErrorActionPreference = 'Continue'
$exe = 'c:\Users\gunslk\Downloads\publish-commandline\ScriptARest.exe'
$server = 'https://ifsmasterbnddevcmb.rnd.ifsdevworld.com'
$mkd = Join-Path $PSScriptRoot 'RunCoreMatrix.mkd'
$logDir = Join-Path $PSScriptRoot '..\..\..\..\.sar-fda'
if (-not (Test-Path $logDir)) {
    $logDir = $PSScriptRoot
}
$log = Join-Path $logDir 'run-standalone-fix-sar-core.log'
if (-not (Test-Path $exe)) {
    Write-Error "ScriptARest not found at $exe"
    exit 2
}
"" | Set-Content -Path $log -Encoding utf8
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') START server=$server file=$mkd" | Tee-Object -FilePath $log -Append
$sw = [System.Diagnostics.Stopwatch]::StartNew()
& $exe "ServerUrl=$server" "FileToRead=$mkd" 2>&1 | Tee-Object -FilePath $log -Append
$sw.Stop()
$code = $LASTEXITCODE
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') END exit=$code duration=$([math]::Round($sw.Elapsed.TotalMinutes, 1))min" | Tee-Object -FilePath $log -Append
exit $code
