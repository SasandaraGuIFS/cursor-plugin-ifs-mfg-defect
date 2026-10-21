# Fast deploy for IFS source .plsql files (entity LU package spec+body).
# Optimizations vs generate_and_deploy.ps1:
#   - Skips java codegen when build/gen artifacts are already up to date
#   - Deploys all files in a single SQLcl session (one DB connection)
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File fast-deploy-plsql.ps1 `
#     -PlsqlFile "c:\Dev\Master\workspace\shpord\source\shpord\database\ShopMaterialAlloc.plsql"
#
#   powershell ... -PlsqlFile ... -ForceGenerate   # always regenerate
#   powershell ... -PlsqlFile ... -SkipGenerate      # never regenerate

param(
    [Parameter(Mandatory = $true)]
    [string]$PlsqlFile,
    [string]$JarPath = (Join-Path (Join-Path $env:TEMP 'IFSLumos') 'ifs-dev-buildtasks.jar'),
    [string]$DbUser = 'ifsapp',
    [string]$DbPassword = 'ifsapp',
    [string]$JdbcUrl = 'jdbc:oracle:thin:@//AZSG1PDE573:1521/IFSPDB',
    [string]$SqlclCmd = 'sql',
    [string]$IfsappData = 'IFSAPP_DATA',
    [string]$IfsappIndex = 'IFSAPP_INDEX',
    [string]$IfsappLob = 'IFSAPP_LOB',
    [switch]$SkipGenerate,
    [switch]$ForceGenerate
)

$ErrorActionPreference = 'Stop'
$helpers = Join-Path $PSScriptRoot 'sqlcl-deploy-helpers.ps1'
if (-not (Test-Path $helpers)) {
    Write-Error "Missing helpers: $helpers"
}
. $helpers

function Get-BuildRoot {
    param([string]$ModelFile)
    $p = (Resolve-Path $ModelFile).Path
    for ($i = 0; $i -lt 5; $i++) { $p = Split-Path $p -Parent }
    return $p
}

function Resolve-SqlclCommand {
    param([string]$PreferredCmd)
    if ($PreferredCmd -and (Get-Command $PreferredCmd -ErrorAction SilentlyContinue)) {
        return (Get-Command $PreferredCmd).Source
    }
    $fallback = Join-Path (Join-Path (Join-Path $env:TEMP 'IFSLumos') 'sqlcl\bin') 'sql.exe'
    if (Test-Path $fallback) { return $fallback }
    Write-Error "SQLcl not found. Install SQLcl or set SqlclCmd."
}

function Find-GeneratedPackageFiles {
    param(
        [string]$BuildRoot,
        [string]$PackageName
    )
    $genDir = Join-Path (Join-Path $BuildRoot 'build') 'gen'
    $api = Get-ChildItem -Path $genDir -Recurse -Filter "$PackageName.api" -ErrorAction SilentlyContinue | Select-Object -First 1
    $apy = Get-ChildItem -Path $genDir -Recurse -Filter "$PackageName.apy" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($api -and $apy) {
        return @($api.FullName, $apy.FullName)
    }
    return @()
}

function Test-GeneratedArtifactsFresh {
    param(
        [string]$PlsqlPath,
        [string]$EntityPath,
        [string[]]$ArtifactPaths
    )
    foreach ($artifact in $ArtifactPaths) {
        if (-not (Test-Path $artifact)) { return $false }
    }
    $plsqlTime = (Get-Item $PlsqlPath).LastWriteTimeUtc
    $entityTime = (Get-Item $EntityPath).LastWriteTimeUtc
    foreach ($artifact in $ArtifactPaths) {
        $artifactTime = (Get-Item $artifact).LastWriteTimeUtc
        if ($plsqlTime -gt $artifactTime) { return $false }
        if ($entityTime -gt $artifactTime) { return $false }
    }
    return $true
}

$sw = [System.Diagnostics.Stopwatch]::StartNew()
$PlsqlFile = (Resolve-Path $PlsqlFile).Path
$normalized = $PlsqlFile -replace '\\', '/'
if ($normalized -notmatch '/source/[^/]+/[^/]+/[^/]+$') {
    Write-Error "Expected source-tree path: <comp>/source/<comp>/<subdir>/<file>.plsql"
}

$compDir = Split-Path (Split-Path $PlsqlFile -Parent) -Parent
$sourceDir = Split-Path $compDir -Parent
$componentRoot = Split-Path $sourceDir -Parent
$comp = Split-Path $compDir -Leaf
$packageName = [System.IO.Path]::GetFileNameWithoutExtension($PlsqlFile)
$entityPath = Join-Path (Join-Path (Join-Path $componentRoot 'model') $comp) "$packageName.entity"

if (-not (Test-Path $entityPath)) {
    Write-Error "Entity model not found: $entityPath"
}

$buildRoot = Get-BuildRoot $entityPath
$deployFiles = @()

Write-Host ''
Write-Host '============================================================'
Write-Host '  FAST DEPLOY: ' -NoNewline
Write-Host $packageName
Write-Host '============================================================'

$existing = Find-GeneratedPackageFiles -BuildRoot $buildRoot -PackageName $packageName
$artifactsFresh = ($existing.Count -eq 2) -and (Test-GeneratedArtifactsFresh -PlsqlPath $PlsqlFile -EntityPath $entityPath -ArtifactPaths $existing)

if ($ForceGenerate) { $artifactsFresh = $false }
if ($SkipGenerate -and $existing.Count -eq 2) { $artifactsFresh = $true }

if ($artifactsFresh) {
    Write-Host "Skipping codegen (build/gen artifacts are up to date)"
    $deployFiles = $existing | Sort-Object {
        if ($_ -match '\.api$') { 0 } else { 1 }
    }
} else {
    if (-not (Test-Path $JarPath)) {
        Write-Error "JAR not found at: $JarPath"
    }
    if (-not (Get-Command java -ErrorAction SilentlyContinue)) {
        Write-Error 'java not found on PATH'
    }

    Write-Host "Running codegen for $packageName.entity ..."
    $genCmd = "java -jar `"$JarPath`" `"$entityPath`""
    $genOutput = Invoke-Expression $genCmd 2>&1
  $genOutput | Write-Host

    $deployFiles = Find-GeneratedPackageFiles -BuildRoot $buildRoot -PackageName $packageName
    if ($deployFiles.Count -lt 2) {
        Write-Error "Generated .api/.apy not found under $(Join-Path $buildRoot 'build\gen')"
    }
    $deployFiles = $deployFiles | Sort-Object {
        if ($_ -match '\.api$') { 0 } else { 1 }
    }
}

Write-Host ''
Write-Host "Deploying $($deployFiles.Count) file(s) in one SQLcl session ..."
$deployFiles | ForEach-Object { Write-Host "  $(Split-Path $_ -Leaf)" }

$sqlcl = Resolve-SqlclCommand $SqlclCmd
$dbConn = "$DbUser/$DbPassword@$JdbcUrl"
$result = Invoke-SqlclDeployBatch -SqlclCmd $sqlcl -DbConn $dbConn -DeployFiles $deployFiles `
    -IfsappData $IfsappData -IfsappIndex $IfsappIndex -IfsappLob $IfsappLob

$sw.Stop()
Write-Host ''
if ($result.Success) {
    Write-Host "DEPLOYMENT COMPLETE in $([math]::Round($sw.Elapsed.TotalSeconds, 1))s"
    foreach ($f in $deployFiles) {
        Write-Host "  OK  $(Split-Path $f -Leaf)"
    }
    exit 0
}

Write-Host "DEPLOYMENT FAILED in $([math]::Round($sw.Elapsed.TotalSeconds, 1))s"
Get-SqlclFailureLines $result.Output | Select-Object -First 8 | ForEach-Object { Write-Host "  $_" }
exit 1
