$ErrorActionPreference='Stop'
Push-Location windows-build
try {
 $meta=Get-Content release.json -Raw | ConvertFrom-Json
 $nextVersion=$meta.version
 $previous=(Get-Content ../channels/dev/windows.json -Raw | ConvertFrom-Json).latest
 if ([version]$previous.version -ge [version]$meta.version) { throw 'Candidate must be newer than the published release' }
 $destination=Join-Path $env:LOCALAPPDATA 'Проверка обновления\Trader OS'
 $baseInstaller=Join-Path $PWD 'previous-installer.exe'
 Invoke-WebRequest $previous.packageUrl -OutFile $baseInstaller
 if ((Get-FileHash $baseInstaller -Algorithm SHA256).Hash.ToLower() -ne $previous.sha256 -or (Get-Item $baseInstaller).Length -ne $previous.size) { throw 'Previous published installer digest/size mismatch' }
 $setup=Start-Process $baseInstaller -ArgumentList '/S','/currentuser',('/D='+$destination) -PassThru -Wait
 if ($setup.ExitCode -ne 0) { throw 'Initial installation failed' }
 $oldExe=@((Join-Path $destination 'Trader OS.exe'),(Join-Path $destination 'OSMINOG Preview.exe')) | Where-Object { Test-Path $_ } | Select-Object -First 1
 if (-not $oldExe) { throw 'Previous installed browser not found' }
 # The public 5.0.0 package contains a legacy test-only harness that still targets
 # the removed canvas. Patch only that harness; the installed UI/updater/profile
 # remain the exact published 5.0.0 code exercised below.
 $appAsar=Join-Path $destination 'resources/app.asar'
 $harness=(Resolve-Path '../tools/trader-update-smoke.cjs').Path
 $asarDir=Join-Path $PWD 'previous-app-asar'
 $patchedAsar=Join-Path $PWD 'previous-app-patched.asar'
 if (-not (Test-Path $appAsar)) { throw 'Previous installed app.asar not found' }
 node -e "const fs=require('node:fs'),path=require('node:path'),asar=require('@electron/asar');(async()=>{const [archive,dir,harness,out]=process.argv.slice(1);fs.rmSync(dir,{recursive:true,force:true});fs.rmSync(out,{force:true});asar.extractAll(archive,dir);fs.copyFileSync(harness,path.join(dir,'update-smoke.cjs'));await asar.createPackage(dir,out)})().catch(e=>{console.error(e);process.exit(1)})" $appAsar $asarDir $harness $patchedAsar
 if ($LASTEXITCODE -ne 0 -or -not (Test-Path $patchedAsar)) { throw 'Previous update harness patch failed' }
 Copy-Item $patchedAsar $appAsar -Force
 node -e "const asar=require('@electron/asar'),s=asar.extractFile(process.argv[1],'update-smoke.cjs').toString();if(!s.includes('TRADER_UPDATE_HARNESS_V2'))process.exit(1)" $appAsar
 if ($LASTEXITCODE -ne 0) { throw 'Previous update harness verification failed' }
 $server=Start-Process python -ArgumentList '-m','http.server','18891','--bind','127.0.0.1','--directory','dist' -PassThru -RedirectStandardOutput update-server.log -RedirectStandardError update-server-errors.log
 try {
  $serverReady = $false;$serverDeadline = (Get-Date).AddSeconds(30)
  do {
   if ($server.HasExited) { Get-Content update-server-errors.log; throw 'Update fixture server exited before readiness' }
   try {$probe=Invoke-WebRequest 'http://127.0.0.1:18891/latest.yml' -TimeoutSec 2;$probeText=if($probe.Content -is [byte[]]){[Text.Encoding]::UTF8.GetString($probe.Content)}else{[string]$probe.Content};if($probe.StatusCode -eq 200 -and $probeText -match [regex]::Escape($nextVersion)){$serverReady=$true;break}}catch{}
   Start-Sleep -Milliseconds 200
  } while ((Get-Date) -lt $serverDeadline)
  if (-not $serverReady) { Get-Content update-server-errors.log; throw 'Update fixture feed did not become ready' }
  $p=Start-Process $oldExe -ArgumentList '--update-smoke','--test-feed=http://127.0.0.1:18891/' -PassThru -RedirectStandardOutput update.log -RedirectStandardError update-errors.log
  if (-not $p.WaitForExit(120000)) { $p.Kill(); throw 'Update button path timed out' }
  Get-Content update.log;Get-Content update-errors.log
  if ($p.ExitCode -ne 0 -or -not (Select-String update.log -Pattern 'UPDATE_INSTALL_STARTED' -Quiet)) { throw 'Update installation never started' }
  $deadline=(Get-Date).AddSeconds(90)
  do {Start-Sleep -Seconds 2;$installers=Get-CimInstance Win32_Process | Where-Object { ($_.Name -like 'OSMINOG-Preview-*.exe' -or $_.Name -like 'Trader-OS-*.exe') -and $_.CommandLine -match '--updated' }} while ($installers -and (Get-Date) -lt $deadline)
  if ($installers) { throw 'NSIS update did not finish' }
  Get-Process | Where-Object { $_.Path -and $_.Path.StartsWith($destination,[StringComparison]::OrdinalIgnoreCase) } | Stop-Process -Force
  $updatedExe=Join-Path $destination 'Trader OS.exe'
  if (-not (Test-Path $updatedExe)) { throw 'Trader OS executable missing after upgrade' }
  $verify=Start-Process $updatedExe -ArgumentList '--verify-update-smoke',"--expect-version=$nextVersion" -PassThru -RedirectStandardOutput update-verify.log -RedirectStandardError update-verify-errors.log
  if (-not $verify.WaitForExit(90000)) { $verify.Kill(); throw 'Updated app verification timed out' }
  Get-Content update-verify.log;Get-Content update-verify-errors.log
  if ($verify.ExitCode -ne 0 -or -not (Select-String update-verify.log -Pattern 'INSTALLED_UPDATE_SMOKE_PASS' -Quiet)) { throw 'Version/profile/cookie preservation check failed' }
 } finally { Stop-Process -Id $server.Id -ErrorAction SilentlyContinue }
} finally { Pop-Location }
