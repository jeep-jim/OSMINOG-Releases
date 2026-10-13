$ErrorActionPreference='Stop'
$work=Join-Path $PWD 'windows-build'
$meta=Get-Content (Join-Path $work 'release.json') -Raw | ConvertFrom-Json
$version=$meta.version;$tag="windows-v$version";$repo=$env:GITHUB_REPOSITORY
$exe=Get-ChildItem (Join-Path $work 'dist/*.exe') | Select-Object -First 1
$block=Get-ChildItem (Join-Path $work 'dist/*.blockmap') | Select-Object -First 1
$sha=(Get-FileHash $exe.FullName -Algorithm SHA256).Hash.ToLower();$url="https://github.com/$repo/releases/download/$tag/$($exe.Name)"
$notes="OSMINOG Windows Preview $version. Local native browser, canvas and provider DOM adapter. Unsigned preview. Source $($meta.source). Windows tests cover installed paths, native panes, fixture provider replies and a real N -> N+1 update preserving a project and browser cookie. Live provider accounts are not certified by fixture tests. SHA-256: $sha"
$notes | Set-Content (Join-Path $work 'release-notes.txt')
gh release view $tag --repo $repo *> $null
if ($LASTEXITCODE -eq 0) { throw 'Immutable Windows release tag already exists; inspect it before retrying' }
gh release create $tag $exe.FullName $block.FullName --repo $repo --title "OSMINOG Windows $version" --prerelease --notes-file (Join-Path $work 'release-notes.txt')
if ($LASTEXITCODE -ne 0) { throw 'Release upload failed' }
$remote=gh api "repos/$repo/releases/tags/$tag" | ConvertFrom-Json
$asset=$remote.assets | Where-Object name -eq $exe.Name
if ($asset.size -ne $exe.Length -or $asset.digest -ne "sha256:$sha") { throw 'Remote installer verification failed' }
$yaml=Get-Content (Join-Path $work 'dist/latest.yml') -Raw
$yaml=$yaml.Replace($exe.Name,$url)
$yaml | Set-Content (Join-Path $work 'latest.yml') -Encoding utf8
gh release view windows-preview --repo $repo *> $null
if ($LASTEXITCODE -ne 0) {
 gh release create windows-preview --repo $repo --title 'OSMINOG Windows Preview update channel' --prerelease --notes 'Mutable latest.yml only. Installers use immutable windows-vVERSION releases.'
 if ($LASTEXITCODE -ne 0) { throw 'Windows channel creation failed' }
}
gh release upload windows-preview (Join-Path $work 'latest.yml') --repo $repo --clobber
if ($LASTEXITCODE -ne 0) { throw 'Update feed publication failed' }
$feed=Invoke-WebRequest "https://github.com/$repo/releases/download/windows-preview/latest.yml"
if (-not $feed.Content.Contains($url)) { throw 'Published updater feed does not reference the verified installer' }
$record=@{schema='osminog-update-feed/v2';product='OSMINOG';platform='windows';channel='dev';generatedAt=[DateTime]::UtcNow.ToString('o');status='active';latest=@{version=$version;packageName=$exe.Name;packageUrl=$url;sha256=$sha;size=$exe.Length;sourceCommit=$meta.source;notes=$notes}}
$record | ConvertTo-Json -Depth 10 | Set-Content channels/dev/windows.json
$releaseDir="platforms/windows/releases/$version";New-Item -ItemType Directory $releaseDir -Force | Out-Null
$record.latest | ConvertTo-Json -Depth 10 | Set-Content "$releaseDir/release.json"
Remove-Item (Join-Path $meta.stage 'ASSEMBLE')
git config user.name 'github-actions[bot]';git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git add channels/dev/windows.json $releaseDir $meta.stage
git commit -m "Publish verified Windows browser $version and activate button update channel"
if ($LASTEXITCODE -ne 0) { throw 'Registry commit failed' }
git pull --rebase origin main
if ($LASTEXITCODE -ne 0) { throw 'Registry update conflict' }
git push origin HEAD:main
if ($LASTEXITCODE -ne 0) { throw 'Registry push failed' }
