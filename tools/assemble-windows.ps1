$ErrorActionPreference = 'Stop'
$marker = Get-ChildItem staging/windows -Recurse -Filter ASSEMBLE | Sort-Object { [version]$_.Directory.Name } | Select-Object -Last 1
if (-not $marker) { throw 'No Windows runtime staged' }
$stage = $marker.Directory.FullName
$meta = Get-Content (Join-Path $stage 'release.json') -Raw | ConvertFrom-Json
if ($meta.version -notmatch '^\d+\.\d+\.\d+$' -or $meta.electron -notmatch '^\d+\.\d+\.\d+$' -or $meta.builder -notmatch '^\d+\.\d+\.\d+$') { throw 'Invalid release versions' }
if ($meta.source -notmatch '^[0-9a-f]{40}$' -or $meta.sha256 -notmatch '^[0-9a-f]{64}$') { throw 'Missing source provenance or runtime digest' }
$work = Join-Path $PWD 'windows-build'
New-Item -ItemType Directory $work -Force | Out-Null
$runtime = Join-Path $work 'runtime.zip'
$parts = Get-ChildItem (Join-Path $stage 'parts/part-*.b64') | Sort-Object Name
if (-not $parts) { throw 'Runtime parts missing' }
$encoded = ($parts | ForEach-Object { Get-Content $_.FullName -Raw }) -join ''
[IO.File]::WriteAllBytes($runtime, [Convert]::FromBase64String($encoded))
if ((Get-FileHash $runtime -Algorithm SHA256).Hash.ToLower() -ne $meta.sha256 -or (Get-Item $runtime).Length -ne $meta.size) { throw 'Runtime digest/size mismatch' }
Expand-Archive $runtime (Join-Path $work 'runtime') -Force
$info = Get-Content (Join-Path $work 'runtime/runtime.json') -Raw | ConvertFrom-Json
foreach ($key in @('version','electron','builder','source')) { if ($info.$key -ne $meta.$key) { throw "Runtime metadata differs: $key" } }
if ($info.appId -ne 'com.osminog.desktop.preview' -or $info.productName -ne 'OSMINOG Preview') { throw 'Installed identity must be preserved' }
$electronZip = "electron-v$($meta.electron)-win32-x64.zip"
$electronBase = "https://github.com/electron/electron/releases/download/v$($meta.electron)"
Invoke-WebRequest "$electronBase/$electronZip" -OutFile (Join-Path $work $electronZip)
Invoke-WebRequest "$electronBase/SHASUMS256.txt" -OutFile (Join-Path $work 'SHASUMS256.txt')
$line = Get-Content (Join-Path $work 'SHASUMS256.txt') | Where-Object { $_ -match ('\s\*?' + [regex]::Escape($electronZip) + '$') }
if (-not $line -or (Get-FileHash (Join-Path $work $electronZip) -Algorithm SHA256).Hash.ToLower() -ne (($line -split '\s+')[0])) { throw 'Electron archive digest mismatch' }
Expand-Archive (Join-Path $work $electronZip) (Join-Path $work 'app') -Force
Remove-Item (Join-Path $work 'app/resources/default_app.asar') -ErrorAction SilentlyContinue
Copy-Item (Join-Path $work 'runtime/resources/*') (Join-Path $work 'app/resources/') -Recurse -Force
Rename-Item (Join-Path $work 'app/electron.exe') 'OSMINOG Preview.exe'
$package = @{ name='osminog-desktop'; version=$meta.version; private=$true; description='OSMINOG local browser'; author='OSMINOG'; devDependencies=@{'electron-builder'=$meta.builder} }
$package | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $work 'package.json')
$config = @{ appId=$info.appId; productName=$info.productName; electronVersion=$meta.electron; directories=@{output='dist'}; artifactName='OSMINOG-Preview-${version}-${arch}.${ext}'; win=@{target='nsis'}; nsis=@{oneClick=$false;perMachine=$false;allowToChangeInstallationDirectory=$true;deleteAppDataOnUninstall=$false}; publish=@(@{provider='generic';url='https://github.com/jeep-jim/OSMINOG-Releases/releases/download/windows-preview/'}) }
$config.releaseInfo = @{releaseName="OSMINOG $($meta.version)";releaseNotes=[string]$meta.notes}
$config | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $work 'builder.json')
$meta | Add-Member -NotePropertyName stage -NotePropertyValue $stage
$meta | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $work 'release.json')
Push-Location $work
try {
 npm install --ignore-scripts --no-audit --no-fund
 if ($LASTEXITCODE -ne 0) { throw 'Builder installation failed' }
 if ([version]$meta.version -ge [version]'0.3.2') {
  node -e "const fs=require('node:fs'),asar=require('@electron/asar');fs.writeFileSync('osminog-eye.ico',asar.extractFile('app/resources/app.asar','icons/osminog-eye.ico'))"
  if ($LASTEXITCODE -ne 0) { throw 'Required OSMINOG eye icon missing from runtime' }
  $config.win.icon='osminog-eye.ico'
  $config.nsis.installerIcon='osminog-eye.ico'
  $config.nsis.uninstallerIcon='osminog-eye.ico'
  $config.nsis.installerHeaderIcon='osminog-eye.ico'
  $config | ConvertTo-Json -Depth 10 | Set-Content builder.json
 }
 npx electron-builder --prepackaged app --win nsis --x64 --config builder.json --publish never
 if ($LASTEXITCODE -ne 0) { throw 'Windows installer build failed' }
 foreach ($mode in @('smoke','browser-smoke','provider-smoke','shell-smoke')) {
  $p = Start-Process -FilePath 'app/OSMINOG Preview.exe' -ArgumentList "--$mode" -PassThru -RedirectStandardOutput "release-$mode.log" -RedirectStandardError "release-$mode-errors.log"
  if (-not $p.WaitForExit(90000)) { $p.Kill(); throw "$mode timed out" }
  Get-Content "release-$mode.log"; Get-Content "release-$mode-errors.log"
  if ($p.ExitCode -ne 0 -or -not (Select-String -Path "release-$mode.log" -Pattern 'SMOKE_PASS' -Quiet)) { throw "$mode failed" }
 }
} finally { Pop-Location }

