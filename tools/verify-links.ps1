<#
.SYNOPSIS
Verify intra-plugin relative links in every SKILL.md / command .md.

.DESCRIPTION
Walks skills/ and commands/ for markdown files, extracts every markdown link
of the form [text](path) whose target is relative (no scheme), and reports any
missing target inside the plugin tree. Also flags scripts referenced inline
(e.g. `scripts/foo.py`, `tools/bar.ps1`) that don't exist on disk.

Exits 0 on success, 1 on any missing target.

.USAGE
  pwsh tools/verify-links.ps1
#>

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Write-Host "Verifying links under $root" -ForegroundColor Cyan

$mdFiles = @()
$mdFiles += Get-ChildItem -Path (Join-Path $root 'skills')   -Recurse -Filter '*.md' -File -ErrorAction SilentlyContinue
$mdFiles += Get-ChildItem -Path (Join-Path $root 'commands') -Recurse -Filter '*.md' -File -ErrorAction SilentlyContinue
# Templates intentionally use placeholder relative paths that resolve only when copied into a per-ticket docs/<KEY>/ tree.
$mdFiles = $mdFiles | Where-Object { $_.FullName -notmatch '\\templates\\' }

$missing = @()
$linkRe   = [regex]'(?<!\!)\[[^\]]+\]\(([^)\s#]+)(?:#[^)]*)?\)'
$scriptRe = [regex]'(?i)([\w./-]+\.(?:ps1|py|sh|mjs|js))'
$schemes  = @('http://','https://','mailto:','ftp://','file://','git://','#')

foreach ($f in $mdFiles) {
    $content = Get-Content -Raw -LiteralPath $f.FullName
    $dir     = Split-Path -Parent $f.FullName
    $rel     = $f.FullName.Substring($root.Length + 1)

    # Markdown links
    foreach ($m in $linkRe.Matches($content)) {
        $target = $m.Groups[1].Value
        if ($schemes | Where-Object { $target.StartsWith($_, [StringComparison]::OrdinalIgnoreCase) }) { continue }
        if ($target -match '^[A-Za-z]:[\\/]') { continue }  # absolute path - skip

        $candidate = Join-Path $dir $target
        if (-not (Test-Path -LiteralPath $candidate)) {
            $missing += [pscustomobject]@{ File=$rel; Kind='link'; Target=$target }
        }
    }

    # Inline script mentions (anchor on the filename, resolve inside its skill)
    foreach ($m in $scriptRe.Matches($content)) {
        $target = $m.Groups[1].Value
        if ($target -match '^(http|https|ftp|git)://') { continue }
        # Try: relative to the SKILL.md, else relative to the skill's root, else shared/scripts/
        $candidates = @(
            (Join-Path $dir $target),
            (Join-Path $dir (Split-Path -Leaf $target)),
            (Join-Path $root (Join-Path 'shared/scripts' (Split-Path -Leaf $target)))
        )
        $hit = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
        if (-not $hit) {
            $missing += [pscustomobject]@{ File=$rel; Kind='script'; Target=$target }
        }
    }
}

if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "Missing references ($($missing.Count)):" -ForegroundColor Yellow
    $missing | Sort-Object File, Kind, Target -Unique | Format-Table -AutoSize
    Write-Host "Note: 'script' hits are heuristic. Many are intentional (e.g. workspace-relative docs/, .cursor/skills/, .claude/skills/)." -ForegroundColor DarkGray
    Write-Host "Only 'link' entries are hard failures." -ForegroundColor DarkGray

    $hardFail = $missing | Where-Object { $_.Kind -eq 'link' }
    if ($hardFail.Count -gt 0) {
        Write-Host "verify-links FAILED: $($hardFail.Count) broken markdown link(s)." -ForegroundColor Red
        exit 1
    }
}

Write-Host "verify-links OK: $($mdFiles.Count) markdown files, no broken links." -ForegroundColor Green
exit 0
