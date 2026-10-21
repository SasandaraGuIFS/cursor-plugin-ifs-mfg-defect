# Deploy generated DUT files to MASTER DEV CMB (edit $files after codegen)
$ErrorActionPreference = 'Stop'
$conn = 'ifsapp/ifsapp@DLK1PDE139:1521/IFSPDB'
$codegen = 'c:\Dev\Master\workspace\.claude\skills\ifs-codegen\tools\ifs-codegen.py'
$deploy = 'c:\Dev\Master\workspace\.claude\skills\ifs-codegen\tools\ifs-deploy.mjs'
# Set to the projection that exposes the new action parameter
$proj = 'c:\Dev\Master\workspace\COMPONENT\model\COMPONENT\Handling.projection'
$log = 'c:\Dev\Master\workspace\.sar-fda\deploy-standalone-fix-dut.log'

"" | Set-Content -Path $log -Encoding utf8
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') codegen $proj" | Tee-Object -FilePath $log -Append
py -3 $codegen generate $proj --json 2>&1 | Tee-Object -FilePath $log -Append

# Replace with paths from codegen deployFiles (never raw .plsvc)
$files = @(
    # 'c:\Dev\Master\build\gen\db\COMPONENT\database\COMPONENT\Foo.api',
    # 'c:\Dev\Master\build\gen\db\COMPONENT\database\COMPONENT\Foo.apy',
    # 'c:\Dev\Master\build\gen\db\COMPONENT\database\COMPONENT\FooHandling.svc'
)
if ($files.Count -eq 0) {
    Write-Error 'Fill $files with codegen deployFiles before running.'
    exit 2
}
node $deploy $conn @files 2>&1 | Tee-Object -FilePath $log -Append
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') DONE" | Tee-Object -FilePath $log -Append
