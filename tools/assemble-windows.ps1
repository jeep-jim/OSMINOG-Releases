$ErrorActionPreference = 'Stop'
$sourceRepo = 'jeep-jim/OSMINOG'
$sourceWorkflowId = 370781122
$marker = Get-ChildItem staging/windows -Recurse -Filter ASSEMBLE | Sort-Object { [version]$_.Directory.Name } | Select-Object -Last 1
if (-not $marker) { throw 'No Windows runtime staged' }
$stage = $marker.Directory.FullName
$meta = Get-Content (Join-Path $stage 'release.json') -Raw | ConvertFrom-Json
if ($meta.version -notmatch '^\d+\.\d+\.\d+$' -or $meta.electron -notmatch '^\d+\.\d+\.\d+$' -or $meta.builder -notmatch '^\d+\.\d+\.\d+$') { throw 'Invalid release versions' }
if ($meta.source -notmatch '^[0-9a-f]{40}$' -or $meta.sha256 -notmatch '^[0-9a-f]{64}$' -or [long]$meta.size -le 0) { throw 'Missing source provenance or runtime digest' }
if ([long]$meta.sourceRun -le 0 -or [long]$meta.sourceArtifact -le 0) { throw 'Missing verified workflow provenance' }

$run = gh api "repos/$sourceRepo/actions/runs/$($meta.sourceRun)" | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or $run.status -ne 'completed' -or $run.conclusion -ne 'success' -or $run.head_sha -ne $meta.source -or [long]$run.workflow_id -ne $sourceWorkflowId) { throw 'Source Windows workflow is not the approved successful run' }
$artifactInfo = gh api "repos/$sourceRepo/actions/artifacts/$($meta.sourceArtifact)" | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or $artifactInfo.expired -or $artifactInfo.name -ne 'windows-desktop-candidate' -or [long]$artifactInfo.workflow_run.id -ne [long]$meta.sourceRun -or $artifactInfo.workflow_run.head_sha -ne $meta.source) { throw 'Source artifact provenance mismatch' }
$compare = gh api "repos/$sourceRepo/compare/$($meta.source)...main" | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or [int]$compare.behind_by -ne 0) { throw 'Verified source commit is not merged into source main' }

$work = Join-Path $PWD 'windows-build'
New-Item -ItemType Directory $work -Force | Out-Null
$artifactZip = Join-Path $work 'source-artifact.zip'
$headers = @{ Authorization = "Bearer $env:GH_TOKEN"; Accept = 'application/vnd.github+json'; 'X-GitHub-Api-Version' = '2022-11-28' }
Invoke-WebRequest "https://api.github.com/repos/$sourceRepo/actions/artifacts/$($meta.sourceArtifact)/zip" -Headers $headers -OutFile $artifactZip
$artifactDir = Join-Path $work 'source-artifact'
Expand-Archive $artifactZip $artifactDir -Force
$runtimeCandidate = Get-ChildItem $artifactDir -Recurse -Filter 'Trader-OS-Windows-Runtime.zip' | Select-Object -First 1
if (-not $runtimeCandidate) { throw 'Verified Trader OS runtime missing from source artifact' }
$runtime = Join-Path $work 'runtime.zip'
Copy-Item $runtimeCandidate.FullName $runtime -Force
if ((Get-FileHash $runtime -Algorithm SHA256).Hash.ToLower() -ne $meta.sha256 -or (Get-Item $runtime).Length -ne [long]$meta.size) { throw 'Runtime digest/size mismatch' }

Expand-Archive $runtime (Join-Path $work 'runtime') -Force
$info = Get-Content (Join-Path $work 'runtime/runtime.json') -Raw | ConvertFrom-Json
foreach ($key in @('version','electron','builder','source')) { if ($info.$key -ne $meta.$key) { throw "Runtime metadata differs: $key" } }
if ($info.appId -ne 'com.osminog.desktop.preview' -or $info.productName -ne 'Trader OS') { throw 'Trader OS identity mismatch' }

$electronZip = "electron-v$($meta.electron)-win32-x64.zip"
$electronBase = "https://github.com/electron/electron/releases/download/v$($meta.electron)"
Invoke-WebRequest "$electronBase/$electronZip" -OutFile (Join-Path $work $electronZip)
Invoke-WebRequest "$electronBase/SHASUMS256.txt" -OutFile (Join-Path $work 'SHASUMS256.txt')
$line = Get-Content (Join-Path $work 'SHASUMS256.txt') | Where-Object { $_ -match ('\s\*?' + [regex]::Escape($electronZip) + '$') }
if (-not $line -or (Get-FileHash (Join-Path $work $electronZip) -Algorithm SHA256).Hash.ToLower() -ne (($line -split '\s+')[0])) { throw 'Electron archive digest mismatch' }
Expand-Archive (Join-Path $work $electronZip) (Join-Path $work 'app') -Force
Remove-Item (Join-Path $work 'app/resources/default_app.asar') -ErrorAction SilentlyContinue
Copy-Item (Join-Path $work 'runtime/resources/*') (Join-Path $work 'app/resources/') -Recurse -Force
Rename-Item (Join-Path $work 'app/electron.exe') 'Trader OS.exe'

$package = @{ name='trader-os-desktop'; version=$meta.version; private=$true; description='Trader OS local-first trading browser'; author='Trader OS'; devDependencies=@{'electron-builder'=$meta.builder;'rcedit'='5.0.2'} }
$package | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $work 'package.json')
$config = @{ appId=$info.appId; productName=$info.productName; electronVersion=$meta.electron; directories=@{output='dist'}; artifactName='Trader-OS-${version}-${arch}.${ext}'; win=@{target='nsis'}; nsis=@{oneClick=$false;perMachine=$false;allowToChangeInstallationDirectory=$true;deleteAppDataOnUninstall=$false}; publish=@(@{provider='generic';url='https://github.com/jeep-jim/OSMINOG-Releases/releases/download/windows-preview/'}) }
$config.releaseInfo = @{releaseName="Trader OS $($meta.version)";releaseNotes=[string]$meta.notes}
$meta | Add-Member -NotePropertyName stage -NotePropertyValue $stage
$meta | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $work 'release.json')

Push-Location $work
try {
 npm install --ignore-scripts --no-audit --no-fund
 if ($LASTEXITCODE -ne 0) { throw 'Builder installation failed' }
 node -e "const fs=require('node:fs'),asar=require('@electron/asar');fs.writeFileSync('trader-os.ico',asar.extractFile('app/resources/app.asar','icons/trader-os.ico'))"
 if ($LASTEXITCODE -ne 0) { throw 'Required Trader OS icon missing from runtime' }
 node -e "import('rcedit').then(({rcedit})=>rcedit('app/Trader OS.exe',{icon:'trader-os.ico'})).catch(e=>{console.error(e);process.exit(1)})"
 if ($LASTEXITCODE -ne 0) { throw 'Executable icon patch failed' }
 Add-Type -AssemblyName System.Drawing
 $icon=[System.Drawing.Icon]::ExtractAssociatedIcon((Join-Path $PWD 'app/Trader OS.exe'))
 $bitmap=$icon.ToBitmap();$red=0;$green=0
 for($y=0;$y -lt $bitmap.Height;$y++){for($x=0;$x -lt $bitmap.Width;$x++){$pixel=$bitmap.GetPixel($x,$y);if($pixel.R -gt 150 -and $pixel.R -gt $pixel.G*1.25){$red++};if($pixel.G -gt 130 -and $pixel.G -gt $pixel.R*1.25){$green++}}}
 $bitmap.Save((Join-Path $PWD 'executable-icon.png'));$bitmap.Dispose();$icon.Dispose()
 if ($red -lt 20 -or $green -lt 20) { throw 'Executable lacks the red-green Trader OS pictogram' }
 $config.win.icon='trader-os.ico';$config.nsis.installerIcon='trader-os.ico';$config.nsis.uninstallerIcon='trader-os.ico';$config.nsis.installerHeaderIcon='trader-os.ico'
 $config | ConvertTo-Json -Depth 10 | Set-Content builder.json
 npx electron-builder --prepackaged app --win nsis --x64 --config builder.json --publish never
 if ($LASTEXITCODE -ne 0) { throw 'Windows installer build failed' }
 $p = Start-Process -FilePath 'app/Trader OS.exe' -ArgumentList '--smoke' -PassThru -RedirectStandardOutput 'release-smoke.log' -RedirectStandardError 'release-smoke-errors.log'
 if (-not $p.WaitForExit(90000)) { $p.Kill(); throw 'Trader OS smoke timed out' }
 Get-Content 'release-smoke.log'; Get-Content 'release-smoke-errors.log'
 if ($p.ExitCode -ne 0 -or -not (Select-String -Path 'release-smoke.log' -Pattern 'TRADER_OS_SMOKE_PASS' -Quiet)) { throw 'Trader OS smoke failed' }
} finally { Pop-Location }
