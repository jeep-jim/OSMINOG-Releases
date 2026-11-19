#!/usr/bin/env python3
"""Import, independently install and publish immutable Windows Mouse CI bytes."""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import quote
import zipfile

SOURCE = 'jeep-jim/OSMINOG'
SOURCE_BRANCH = 'release/mouse-6.0.29'
REPO = 'jeep-jim/OSMINOG-Releases'
VERSION = '6.0.29'
TAG = 'mouse-windows-v6.0.29-x64'
INSTALLER = 'Mouse-Browser-6.0.29-Windows-x64.exe'
ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'staging/mouse/6.0.29-windows-x64'
OUT = ROOT / 'mouse629-windows-release'
ASSETS = (INSTALLER, 'SHA256SUMS.txt', 'mouse-windows-build.json')
RELEASE_TITLE = 'Mouse Browser 6.0.29 — Windows x64'
RELEASE_PAGE_LIMIT = 20


def sha(data):
    return hashlib.sha256(data).hexdigest()


def api(repo, resource, method='GET', payload=None, missing=False):
    args = ['gh', 'api', f'repos/{repo}/{resource}', '--method', method]
    if payload is not None:
        args += ['--input', '-']
    result = subprocess.run(args, input=json.dumps(payload).encode() if payload is not None else None,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
    if result.returncode:
        if missing and b'HTTP 404' in result.stderr:
            return None
        raise RuntimeError(resource + ': ' + result.stderr.decode(errors='replace')[:500])
    return json.loads(result.stdout)


def pin():
    value = json.loads((STAGE / 'pin.json').read_text(encoding='utf-8'))
    if value.get('version') != VERSION or value.get('ready') is not True:
        raise ValueError('Windows publication pin is not ready')
    if value.get('sourceBranch') != SOURCE_BRANCH:
        raise ValueError('Windows publication requires the fixed 6.0.29 source branch')
    for key in ['source', 'sourceMerge']:
        if not re.fullmatch('[0-9a-f]{40}', value.get(key, '')):
            raise ValueError('Missing immutable ' + key)
    for key in ['artifactSHA256', 'verificationSHA256']:
        if not re.fullmatch('[0-9a-f]{64}', value.get(key, '')):
            raise ValueError('Missing immutable ' + key)
    for key in ['sourcePR', 'run', 'attempt', 'job', 'artifact', 'verificationArtifact']:
        if not isinstance(value.get(key), int) or value[key] < 1:
            raise ValueError('Invalid source provenance: ' + key)
    package = value['package']
    if package['name'] != INSTALLER or not 50 * 1024**2 < package['size'] < 500 * 1024**2:
        raise ValueError('Unexpected Windows installer')
    if not re.fullmatch('[0-9a-f]{64}', package['sha256']):
        raise ValueError('Invalid installer hash')
    if (STAGE / 'PUBLISH_OWNER').read_text(encoding='utf-8').strip() != 'Publish verified Mouse Browser 6.0.29 Windows x64':
        raise ValueError('Unexpected publication trigger')
    return value


def read_artifact(info, expected_hash, maximum):
    if info.get('expired') or info.get('digest') != 'sha256:' + expected_hash:
        raise ValueError('Pinned artifact expired or digest changed')
    data = subprocess.check_output(['gh', 'api', f'repos/{SOURCE}/actions/artifacts/{info["id"]}/zip'], timeout=300)
    if len(data) > maximum or sha(data) != expected_hash:
        raise ValueError('Artifact download size/hash mismatch')
    return zipfile.ZipFile(io.BytesIO(data))


def verification(value):
    if value.get('ok') is not True or (value.get('version'), value.get('platform'), value.get('arch')) != (VERSION, 'win32', 'x64'):
        raise ValueError('Successful installed Windows x64 evidence required')
    checks = value.get('checks', {})
    for name in ['installation', 'write', 'read', 'reinstallation', 'actualUpdateButton',
                 'postUpdateProfile', 'ordinaryLaunch']:
        if not checks.get(name):
            raise ValueError('Missing installed check: ' + name)
    for name in ['installation', 'write', 'read', 'reinstallation', 'postUpdateProfile']:
        if checks[name].get('exitCode') != 0:
            raise ValueError('Installed process did not finish successfully: ' + name)
    if checks['reinstallation'].get('profileUnchanged') is not True:
        raise ValueError('Actual reinstall profile preservation missing')
    for name in ['installation', 'reinstallation']:
        if checks[name].get('peMachine') != '0x8664' or checks[name].get('unicodeAndSpaces') is not True:
            raise ValueError('Actual AMD64 installation in a Unicode/spaced path missing')
    update = checks['actualUpdateButton']
    for name in ['ok', 'sameVersion', 'downloadButton', 'installButton',
                 'receiptAcknowledged', 'profileRetestedAfterward']:
        if update.get(name) is not True:
            raise ValueError('Actual updater acceptance missing: ' + name)
    if (update.get('exitCode') != 0 or update.get('helperResult') != 'Installer completed'
            or update.get('transport') != 'owned local installer stream'
            or update.get('publicChannelDownloadVerified') is not False):
        raise ValueError('Updater roundtrip evidence is invalid or overstates public transport')
    window = update.get('newWindow', {})
    if (window.get('title') != 'Mouse Browser' or not isinstance(window.get('pid'), int)
            or window['pid'] <= 0 or window['pid'] == update.get('pid')
            or window.get('minimized') is not False or not window.get('handle')):
        raise ValueError('Updated application has no independently observed new visible process')
    if (checks['ordinaryLaunch'].get('ok') is not True
            or checks['ordinaryLaunch'].get('nativeCloseExitCode') != 0
            or checks['ordinaryLaunch'].get('secondInstance', {}).get('exitCode') != 0):
        raise ValueError('Ordinary launch, second-instance restore or native close missing')


def verify_source_merge(p):
    pr = api(SOURCE, f'pulls/{p["sourcePR"]}')
    if (not pr.get('merged') or pr['head']['sha'] != p['source']
            or pr['merge_commit_sha'] != p['sourceMerge'] or pr['base']['ref'] != SOURCE_BRANCH):
        raise ValueError('Exact tested source PR is not merged into the fixed 6.0.29 branch')
    comparison = api(SOURCE, f'compare/{p["source"]}...{quote(SOURCE_BRANCH, safe="")}')
    if comparison['status'] not in ['ahead', 'identical'] or comparison['behind_by'] != 0:
        raise ValueError('Tested source is not an ancestor of the fixed 6.0.29 branch')


def verify_source_run(p):
    run = api(SOURCE, f'actions/runs/{p["run"]}')
    if run.get('head_sha') != p['source'] or run.get('path') != '.github/workflows/mouse-windows.yml':
        raise ValueError('Pinned run is not the Windows source workflow')
    if run.get('status') != 'completed' or run.get('conclusion') != 'success':
        raise ValueError('Entire Windows source run has not completed successfully')
    if run.get('run_attempt') != p['attempt']:
        raise ValueError('Source run is not the pinned attempt')
    jobs = api(SOURCE, f'actions/runs/{p["run"]}/attempts/{p["attempt"]}/jobs?per_page=100')['jobs']
    job = [j for j in jobs if j['id'] == p['job'] and j['name'] == 'mouse-windows-x64' and j['conclusion'] == 'success' and j['status'] == 'completed']
    if len(job) != 1:
        raise ValueError('Exact Windows source job has not passed')
    if (job[0].get('run_id'), job[0].get('run_attempt'), job[0].get('head_sha')) != (p['run'], p['attempt'], p['source']):
        raise ValueError('Source build job is not from the pinned source attempt')
    required_steps = {'Run retained and Windows Mouse tests', 'Build Mouse Browser NSIS installer',
                      'Verify installed app, native UI, restart and profile preservation',
                      'Bind verified installer bytes to source and test evidence',
                      'Require both unit and installed acceptance'}
    if not required_steps.issubset({s['name'] for s in job[0]['steps'] if s['status'] == 'completed' and s['conclusion'] == 'success'}):
        raise ValueError('Source job did not execute every release gate')
    modern = [j for j in jobs if j.get('name') == 'mouse-windows-x64-modern']
    if len(modern) != 1 or modern[0].get('status') != 'completed' or modern[0].get('conclusion') != 'success':
        raise ValueError('Modern Windows installed verification job has not passed')
    if (modern[0].get('run_id'), modern[0].get('run_attempt'), modern[0].get('head_sha')) != (p['run'], p['attempt'], p['source']):
        raise ValueError('Modern Windows job is not from the pinned source attempt')
    modern_steps = {'Verify immutable installer and source evidence',
                    'Verify same installed app on modern Windows',
                    'Upload modern Windows verification evidence'}
    if not modern_steps.issubset({s['name'] for s in modern[0].get('steps', [])
                                 if s.get('status') == 'completed' and s.get('conclusion') == 'success'}):
        raise ValueError('Modern Windows job did not execute every modern release gate')


def import_candidate():
    p = pin()
    verify_source_run(p)
    verify_source_merge(p)
    artifacts = api(SOURCE, f'actions/runs/{p["run"]}/artifacts?per_page=100')['artifacts']
    candidate = [a for a in artifacts if a['id'] == p['artifact'] and a['name'] == 'mouse-windows-x64-candidate']
    evidence = [a for a in artifacts if a['id'] == p['verificationArtifact'] and a['name'] == 'mouse-windows-x64-verification']
    if len(candidate) != 1 or len(evidence) != 1:
        raise ValueError('Exact source artifacts unavailable')
    OUT.mkdir(exist_ok=True)
    with read_artifact(candidate[0], p['artifactSHA256'], 600 * 1024**2) as archive:
        entries = archive.infolist()
        if len(entries) != len(ASSETS) or {x.filename for x in entries} != set(ASSETS):
            raise ValueError('Unexpected installer archive entries')
        for item in entries:
            if item.is_dir() or item.file_size > 500 * 1024**2 or (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Invalid archive entry')
            (OUT / item.filename).write_bytes(archive.read(item))
    build = json.loads((OUT / 'mouse-windows-build.json').read_text(encoding='utf-8'))
    if build['source'] != p['source'] or int(build['runId']) != p['run'] or int(build['runAttempt']) != p['attempt'] or build['package'] != p['package']:
        raise ValueError('Build provenance mismatch')
    if (build['version'], build['platform'], build['arch'], build['productName'], build['signing']) != (VERSION, 'win32', 'x64', 'Mouse Browser', 'unsigned'):
        raise ValueError('Unexpected application identity')
    installer = (OUT / INSTALLER).read_bytes()
    if len(installer) != p['package']['size'] or sha(installer) != p['package']['sha256']:
        raise ValueError('Installer bytes mismatch')
    if (OUT / 'SHA256SUMS.txt').read_text().strip() != p['package']['sha256'] + '  ' + INSTALLER:
        raise ValueError('Declared checksum mismatch')
    with read_artifact(evidence[0], p['verificationSHA256'], 300 * 1024**2) as archive:
        report = archive.read('mouse-windows-verification.json')
        if sha(report) != build['verification']['sha256']:
            raise ValueError('Source verification hash mismatch')
        source_verification = json.loads(report)
        verification(source_verification)
        if build['verification'].get('result') != source_verification:
            raise ValueError('Embedded build verification differs from the hashed source report')
        (OUT / 'source-windows-verification.json').write_bytes(report)
    for file in ['tools/mouse-windows-verify.py', 'desktop/mouse-update.cjs']:
        obj = api(SOURCE, f'contents/{file}?ref={p["source"]}')
        data = base64.b64decode(obj['content'])
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if blob != obj['sha']:
            raise ValueError('Source helper blob mismatch')
        (OUT / Path(file).name).write_bytes(data)
    notes = (STAGE / 'RELEASE_NOTES.md').read_text(encoding='utf-8')
    notes += f'\n\nSource: https://github.com/{SOURCE}/commit/{p["source"]}\nSource checks: https://github.com/{SOURCE}/actions/runs/{p["run"]}\nIndependent installation: https://github.com/{REPO}/actions/runs/{os.environ["GITHUB_RUN_ID"]}\n\nSHA-256:\n```\n' + (OUT / 'SHA256SUMS.txt').read_text() + '```\n'
    (OUT / 'RELEASE_NOTES.md').write_text(notes, encoding='utf-8')
    print('MOUSE_WINDOWS_IMMUTABLE_SOURCE_IMPORT_PASS', flush=True)


def verify_installed():
    environment = {k: v for k, v in os.environ.items() if k not in ['GH_TOKEN', 'GITHUB_TOKEN']}
    subprocess.run([sys.executable, str(OUT / 'mouse-windows-verify.py'), str(OUT / INSTALLER)],
                   cwd=OUT, env=environment, timeout=2400, check=True)
    verification(json.loads((OUT / 'mouse-windows-verification.json').read_text(encoding='utf-8')))


def release_identity(value, p, expected_id=None):
    release_id = value.get('id') if isinstance(value, dict) else None
    if (type(release_id) is not int or release_id <= 0
            or expected_id is not None and release_id != expected_id
            or value.get('url') != f'https://api.github.com/repos/{REPO}/releases/{release_id}'
            or value.get('tag_name') != TAG or value.get('name') != RELEASE_TITLE
            or type(value.get('draft')) is not bool or value.get('prerelease') is not True
            or not isinstance(value.get('assets'), list)):
        raise ValueError('Unexpected Windows release identity')
    lines = (value.get('body') or '').splitlines()
    required = [f'Source: https://github.com/{SOURCE}/commit/{p["source"]}',
                f'Source checks: https://github.com/{SOURCE}/actions/runs/{p["run"]}',
                p['package']['sha256'] + '  ' + INSTALLER]
    if not all(line in lines for line in required):
        raise ValueError('Existing Windows release does not match the pinned source and installer')
    return value


def read_release(release_id, p):
    return release_identity(api(REPO, f'releases/{release_id}'), p, release_id)


def find_release(p):
    # By-tag lookup only promises a published release. Authenticated listing
    # includes drafts; finish every page before deciding that a tag is unique.
    # https://docs.github.com/en/rest/releases/releases#list-releases
    matches = {}
    published = api(REPO, f'releases/tags/{TAG}', missing=True)
    if published is not None:
        published = release_identity(published, p)
        matches[published['id']] = published
    for page in range(1, RELEASE_PAGE_LIMIT + 1):
        releases = api(REPO, f'releases?per_page=100&page={page}')
        if not isinstance(releases, list) or len(releases) > 100:
            raise ValueError('Invalid authenticated release listing')
        for release in releases:
            if release.get('tag_name') == TAG:
                release = release_identity(release, p)
                matches[release['id']] = release
        if len(releases) < 100:
            break
    else:
        raise ValueError('Release listing exceeded the bounded pagination limit')
    if len(matches) > 1:
        raise ValueError('Ambiguous Windows releases for the exact tag')
    return read_release(next(iter(matches)), p) if matches else None


def upload_release_asset(release_id, name):
    # The upload endpoint is keyed by the validated release ID, including for
    # drafts. No tag lookup or --clobber operation occurs inside this command.
    endpoint = f'https://uploads.github.com/repos/{REPO}/releases/{release_id}/assets?name={quote(name, safe="")}'
    subprocess.run(['gh', 'api', endpoint, '--method', 'POST',
                    '--header', 'Content-Type: application/octet-stream',
                    '--input', str(OUT / name)], stdout=subprocess.DEVNULL, check=True, timeout=300)


def publish():
    p = pin()
    verification(json.loads((OUT / 'mouse-windows-verification.json').read_text(encoding='utf-8')))
    if sha((OUT / INSTALLER).read_bytes()) != p['package']['sha256']:
        raise ValueError('Installer changed after verification')
    release = find_release(p)
    notes = (OUT / 'RELEASE_NOTES.md').read_text(encoding='utf-8')
    if release is None:
        release = release_identity(api(REPO, 'releases', 'POST', {
            'tag_name': TAG, 'target_commitish': 'main', 'name': RELEASE_TITLE,
            'body': notes, 'draft': True, 'prerelease': True, 'make_latest': 'false',
        }), p)
        if release['draft'] is not True:
            raise ValueError('New Windows release must remain a draft until assets are verified')
    release_id = release['id']
    names = [*ASSETS, 'mouse-windows-verification.json']
    missing = []
    # Inspect every existing immutable asset before uploading any missing one.
    for name in names:
        data = (OUT / name).read_bytes()
        existing = [a for a in release['assets'] if a['name'] == name]
        if existing:
            if len(existing) != 1 or existing[0].get('state') != 'uploaded':
                raise ValueError('Unexpected existing Windows release asset: ' + name)
            if existing[0]['size'] != len(data) or existing[0].get('digest') != 'sha256:' + sha(data):
                # Installer and original evidence are immutable, including across reruns.
                # A fresh rerun report belongs in CI artifacts, not over an old release asset.
                if name == 'mouse-windows-verification.json':
                    continue
                raise ValueError('Refusing to overwrite an immutable release asset: ' + name)
        else:
            missing.append(name)
    for name in missing:
        upload_release_asset(release_id, name)
    release = read_release(release_id, p)
    for name in ASSETS:
        actual = [a for a in release['assets'] if a['name'] == name]
        data = (OUT / name).read_bytes()
        if len(actual) != 1 or actual[0].get('state') != 'uploaded' or actual[0]['size'] != len(data) or actual[0].get('digest') != 'sha256:' + sha(data):
            raise ValueError('Remote release asset checksum mismatch: ' + name)
    if release['draft']:
        # Refresh only this verified draft's notes to link the current successful
        # fresh-install run. Existing public releases and assets stay immutable.
        release_identity(api(REPO, f'releases/{release_id}', 'PATCH', {
            'draft': False, 'prerelease': True, 'make_latest': 'false', 'body': notes,
        }), p, release_id)
    release = read_release(release_id, p)
    if release['draft'] or not release.get('published_at'):
        raise ValueError('Release is not public')
    (OUT / 'public-release-verification.json').write_text(json.dumps(release, indent=2) + '\n', encoding='utf-8')
    print('MOUSE_WINDOWS_PUBLIC_INSTALLER_HASH_VERIFIED', flush=True)


def put_json(file, content):
    old = api(REPO, 'contents/' + file, missing=True)
    data = (json.dumps(content, indent=2) + '\n').encode()
    if old:
        previous = json.loads(base64.b64decode(old['content']))
        if previous == content:
            return
        if previous.get('version') == VERSION:
            raise ValueError('Refusing to rewrite existing metadata for the same Windows release')
        if tuple(map(int, previous['version'].split('.'))) > tuple(map(int, VERSION.split('.'))):
            raise ValueError('Refusing to downgrade Windows feed')
    payload = {'message': 'Publish verified Mouse Browser 6.0.29 Windows x64 channel', 'content': base64.b64encode(data).decode(), 'branch': 'main'}
    if old:
        payload['sha'] = old['sha']
    api(REPO, 'contents/' + file, 'PUT', payload)


def channel():
    p = pin()
    release = api(REPO, f'releases/tags/{TAG}')
    assets = [a for a in release['assets'] if a['name'] == INSTALLER]
    if release['draft'] or not release.get('published_at') or len(assets) != 1 or assets[0].get('digest') != 'sha256:' + p['package']['sha256'] or assets[0]['size'] != p['package']['size']:
        raise ValueError('Public installer is not verified')
    value = {'schema': 1, 'version': VERSION, 'platform': 'win32', 'arch': 'x64',
             'url': f'https://github.com/{REPO}/releases/download/{TAG}/{INSTALLER}',
             'size': p['package']['size'], 'digest': 'sha256:' + p['package']['sha256'],
             'publishedAt': release['published_at']}
    put_json('platforms/windows/mouse-x64/releases/6.0.29.json', value)
    put_json('platforms/windows/mouse-x64/latest.json', value)
    environment = {k: v for k, v in os.environ.items() if k not in ['GH_TOKEN', 'GITHUB_TOKEN']}
    environment['MOUSE_WINDOWS_RELEASE_SHA256'] = p['package']['sha256']
    environment['MOUSE_WINDOWS_RELEASE_SIZE'] = str(p['package']['size'])
    # The earlier version is only a comparison fixture: no earlier Windows
    # Mouse release exists. Download the real public installer anonymously.
    script = r'''
const assert=require('node:assert/strict'),fs=require('node:fs/promises'),os=require('node:os');
const {MouseUpdates,WINDOWS_CHANNEL}=require('./mouse-update.cjs');
(async()=>{
 const target={platform:'win32',arch:'x64'},app={getVersion:()=> '6.0.28',getPath:()=>os.tmpdir()};
 let updater,error;const observations=[];
 // The preceding Mac publication needed more than three minutes before the
 // static channel was observed. Keep a bounded six-minute visibility budget.
 for(let i=0;i<72;i++){
  try{updater=new MouseUpdates({app,shell:{},target});const state=await updater.run('check');observations.push({attempt:i+1,...state});assert.equal(state.phase,'available');assert.equal(state.channel,'static');assert.equal(state.availableVersion,'6.0.29');error=null;break;}
  catch(e){error=e;await new Promise(r=>setTimeout(r,5000));}
 }
 await fs.writeFile('windows-channel-observations.json',JSON.stringify(observations,null,2));if(error)throw error;
 assert.equal((await updater.run('download')).phase,'ready');await updater.verified();
 assert.equal(updater.candidate.hash,process.env.MOUSE_WINDOWS_RELEASE_SHA256);
 assert.equal(updater.candidate.size,Number(process.env.MOUSE_WINDOWS_RELEASE_SIZE));
 const current=new MouseUpdates({app:{getVersion:()=> '6.0.29'},shell:{},target});
 assert.equal((await current.run('check')).phase,'current');assert.equal(current.state.channel,'static');
 await fs.writeFile('windows-channel-verification.json',JSON.stringify({ok:true,version:'6.0.29',platform:'win32',arch:'x64',channel:WINDOWS_CHANNEL,anonymous:true,comparisonVersionIsFixture:true,verifiedDownload:true,currentVersionCheck:true,sha256:updater.candidate.hash,size:updater.candidate.size},null,2));
 console.log('MOUSE_WINDOWS_ANONYMOUS_CHANNEL_DOWNLOAD_PASS');
})().catch(e=>{console.error(e);process.exit(1)});
'''
    subprocess.run(['node', '-e', script], cwd=OUT, env=environment, check=True, timeout=600)


if __name__ == '__main__':
    commands = {'import': import_candidate, 'verify': verify_installed, 'publish': publish, 'channel': channel}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        raise SystemExit('Expected import, verify, publish or channel')
    commands[sys.argv[1]]()
