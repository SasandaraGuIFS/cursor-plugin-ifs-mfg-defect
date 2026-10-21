<#
.SYNOPSIS
Build dist/ifs-mfg-defect-<version>.zip from the plugin tree.

.DESCRIPTION
Runs verify-links.ps1 first, then zips the plugin excluding dist/, .git/, node_modules/.
Version is read from .cursor-plugin/plugin.json.

.USAGE
  pwsh tools/package.ps1
#>

$ErrorActionPreference = 'Stop'
$root  = Split-Path -Parent $PSScriptRoot
$dist  = Join-Path $root 'dist'

# 1. Verify
Write-Host "[1/3] verify-links" -ForegroundColor Cyan
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'verify-links.ps1')
if ($LASTEXITCODE -ne 0) { throw "verify-links failed" }

# 2. Read version
$manifest = Get-Content -Raw (Join-Path $root '.cursor-plugin/plugin.json') | ConvertFrom-Json
$version  = $manifest.version
$name     = $manifest.name
if (-not $version -or -not $name) { throw "name/version missing in .cursor-plugin/plugin.json" }

# 3. Zip
New-Item -ItemType Directory -Force -Path $dist | Out-Null
$zipPath = Join-Path $dist "$name-$version.zip"
if (Test-Path $zipPath) { Remove-Item -Force $zipPath }

Write-Host "[2/3] packaging $zipPath" -ForegroundColor Cyan

$exclude = @('dist', '.git', 'node_modules', '.vscode', '.idea')
$items = Get-ChildItem -LiteralPath $root -Force |
    Where-Object { $exclude -notcontains $_.Name }

$staging = Join-Path $env:TEMP ("ifs-mfg-defect-pkg-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $staging | Out-Null
try {
    foreach ($item in $items) {
        Copy-Item -LiteralPath $item.FullName -Destination $staging -Recurse -Force
    }
    Compress-Archive -Path (Join-Path $staging '*') -DestinationPath $zipPath -Force
} finally {
    Remove-Item -Recurse -Force $staging -ErrorAction SilentlyContinue
}

$size = (Get-Item $zipPath).Length
Write-Host "[3/3] done: $zipPath ($([math]::Round($size/1KB,1)) KB)" -ForegroundColor Green
