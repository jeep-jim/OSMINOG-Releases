#!/usr/bin/env python3
"""Import, freshly verify and publish the first Linux x64 Mouse release.

Both packages come from one immutable successful source job. Linux has no
historical release baseline; Windows/macOS reports cannot satisfy this gate.
"""
import base64
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import time
import urllib.request
import zipfile

VERSION = '6.0.33'
SOURCE = 'jeep-jim/OSMINOG'
REPO = 'jeep-jim/OSMINOG-Releases'
TAG = 'mouse-linux-v6.0.33-x64'
RELEASE_TITLE = 'Mouse Browser 6.0.33 — Linux x64'
APPIMAGE = 'Mouse-Browser-6.0.33-Linux-x64.AppImage'
DEB = 'Mouse-Browser-6.0.33-Linux-x64.deb'
PACKAGES = (APPIMAGE, DEB)
ASSETS = (*PACKAGES, 'SHA256SUMS.txt', 'mouse-linux-build.json')
ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT/'staging/mouse/6.0.33-linux-x64'
OUT = ROOT/'mouse633-linux-release'
CHANNEL_PATH = 'platforms/linux/mouse-x64/latest.json'
CHANNEL = 'https://raw.githubusercontent.com/'+REPO+'/main/'+CHANNEL_PATH
MARKERS = ('MOUSE_631_TASK_ONLY_NATIVE_PASS', 'MOUSE_631_FIFTY_TABS_FIVE_DESKTOPS_NATIVE_PASS',
           'MOUSE_631_INSTALLED_TASK_STRESS_PASS', 'MOUSE_632_STATIONARY_MEDIA_PASS')
OWNER_MARKER = 'MOUSE_633_OWNER_FEEDBACK_PASS'
_reuse = runpy.run_path(str(Path(__file__).with_name('mouse633-reuse.py')))
_transport = _reuse['load']('mouse632-windows-release.py')
# Reuse the reviewed bounded API/artifact/draft-listing/upload transport. Identity
# and all OS acceptance are Linux-specific below; no Windows report is reused.
api, read_artifact = _transport['api'], _transport['read_artifact']
_find_release, _read_release = _transport['find_release'], _transport['read_release']
_upload_release_asset = _transport['upload_release_asset']


def sync_transport():
    _transport.update(api=api, OUT=OUT, release_identity=release_identity)


def find_release(p):
    sync_transport()
    return _find_release(p)


def read_release(release_id, p):
    sync_transport()
    return _read_release(release_id, p)


def upload_release_asset(release_id, name):
    sync_transport()
    return _upload_release_asset(release_id, name)


def need(value, message):
    if not value:
        raise ValueError('Mouse633 Linux: '+message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, allow_nan=False)+'\n').encode()


def validate_template():
    p = json.loads((STAGE/'pin.json').read_text())
    need(p.get('version') == VERSION and type(p.get('ready')) is bool, 'invalid template identity')
    need(p.get('sourceBranch') == 'main' and p.get('previous') is None,
         'first Linux release must have main source and no invented baseline')
    need(set(p.get('packages', {})) == set(PACKAGES), 'both Linux formats must be pinned')
    need((STAGE/'RELEASE_NOTES.md').read_text().startswith('# Mouse Browser '+VERSION), 'release notes identity')
    if p['ready'] is False:
        for key in ('source', 'sourceMerge', 'sourcePR', 'run', 'attempt', 'job', 'artifact',
                    'artifactSHA256', 'verificationArtifact', 'verificationSHA256'):
            need(p.get(key) is None, 'unready provenance must be null: '+key)
        need(all(value == {'size': None, 'sha256': None} for value in p['packages'].values()),
             'unready package claims must be null')
        need(not (STAGE/'PUBLISH_OWNER').exists(), 'unready template has a publication trigger')
    return p


def pin():
    p = validate_template()
    need(p['ready'] is True, 'publication pin is not ready')
    for key in ('source', 'sourceMerge'):
        need(isinstance(p.get(key), str) and re.fullmatch('[0-9a-f]{40}', p[key]), 'missing immutable '+key)
    for key in ('artifactSHA256', 'verificationSHA256'):
        need(isinstance(p.get(key), str) and re.fullmatch('[0-9a-f]{64}', p[key]), 'missing immutable '+key)
    for key in ('sourcePR', 'run', 'attempt', 'job', 'artifact', 'verificationArtifact'):
        need(type(p.get(key)) is int and p[key] > 0, 'invalid source provenance: '+key)
    for name, item in p['packages'].items():
        need(type(item.get('size')) is int and 50*1024**2 < item['size'] < 500*1024**2,
             'unexpected package size: '+name)
        need(isinstance(item.get('sha256'), str) and re.fullmatch('[0-9a-f]{64}', item['sha256']),
             'missing package digest: '+name)
    need((STAGE/'PUBLISH_OWNER').read_text().strip() == 'Publish verified Mouse Browser 6.0.33 Linux x64',
         'publication trigger differs')
    return p


def verify_source(p):
    run = api(SOURCE, f'actions/runs/{p["run"]}')
    need((run.get('head_sha'), run.get('path'), run.get('run_attempt'), run.get('status'), run.get('conclusion')) ==
         (p['source'], '.github/workflows/mouse-linux.yml', p['attempt'], 'completed', 'success'),
         'exact Linux source workflow/attempt has not passed')
    jobs = api(SOURCE, f'actions/runs/{p["run"]}/attempts/{p["attempt"]}/jobs?per_page=100')['jobs']
    found = [job for job in jobs if job.get('id') == p['job'] and job.get('name') == 'mouse-linux-x64']
    need(len(found) == 1, 'exact Linux builder job missing')
    job = found[0]
    need((job.get('run_id'), job.get('run_attempt'), job.get('head_sha'), job.get('status'), job.get('conclusion')) ==
         (p['run'], p['attempt'], p['source'], 'completed', 'success'), 'Linux source job provenance differs')
    required = {'Run retained and Linux Mouse contracts', 'Build Linux AppImage and deb',
                'Verify installed Linux packages and native behavior', 'Bind verified Linux packages to source evidence'}
    actual = {step.get('name') for step in job.get('steps', [])
              if step.get('status') == 'completed' and step.get('conclusion') == 'success'}
    need(required <= actual, 'one or more source package/native gates did not run')
    pr = api(SOURCE, f'pulls/{p["sourcePR"]}')
    need(pr.get('merged') is True and pr.get('head', {}).get('sha') == p['source'] and
         pr.get('base', {}).get('ref') == 'main' and pr.get('merge_commit_sha') == p['sourceMerge'],
         'exact tested source PR is not merged into main')
    ancestry = api(SOURCE, f'compare/{p["source"]}...main')
    need(ancestry.get('status') in ('ahead', 'identical') and ancestry.get('behind_by') == 0,
         'tested source is not an ancestor of main')
    return job


def artifact_from_job(item, p, job):
    origin = item.get('workflow_run', {})
    need(origin.get('id') == p['run'] and origin.get('head_sha') == p['source'], 'artifact source/run differs')
    parsed = lambda value: datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
    need(parsed(job['started_at']) <= parsed(item['created_at']) <= parsed(job['completed_at']),
         'artifact is outside the successful pinned job')


def verify_packages(p):
    for name in PACKAGES:
        raw = (OUT/name).read_bytes()
        need(len(raw) == p['packages'][name]['size'] and sha(raw) == p['packages'][name]['sha256'],
             'package bytes changed: '+name)
    expected = {name: p['packages'][name]['sha256'] for name in PACKAGES}
    actual = {}
    for line in (OUT/'SHA256SUMS.txt').read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        need(name not in actual, 'duplicate checksum')
        actual[name] = digest
    need(actual == expected, 'declared package checksums differ')


def verify_evidence(read, p):
    verifier = runpy.run_path(str(Path(__file__).with_name('mouse633-linux-evidence.py')))
    return verifier['verify'](read, p)


def import_candidate():
    p = pin()
    job = verify_source(p)
    artifacts = api(SOURCE, f'actions/runs/{p["run"]}/artifacts?per_page=100')['artifacts']
    def exact(key, name):
        found = [item for item in artifacts if item.get('id') == p[key] and item.get('name') == name]
        need(len(found) == 1, 'exact source artifact missing: '+name)
        artifact_from_job(found[0], p, job)
        return found[0]
    candidate = exact('artifact', 'mouse-linux-x64-candidate')
    evidence = exact('verificationArtifact', 'mouse-linux-x64-verification')
    OUT.mkdir(exist_ok=True)
    with read_artifact(candidate, p['artifactSHA256'], 1024**3) as archive:
        entries = archive.infolist()
        need(len(entries) == len(ASSETS) and {item.filename for item in entries} == set(ASSETS),
             'candidate must contain exactly both packages, checksums and build manifest')
        need(sum(item.file_size for item in entries) <= 1024**3, 'candidate expanded size exceeded')
        for item in entries:
            need(not item.is_dir() and item.file_size <= 500*1024**2 and
                 (item.external_attr >> 16) & 0o170000 != 0o120000, 'unsafe artifact entry')
            (OUT/item.filename).write_bytes(archive.read(item))
    verify_packages(p)
    build = json.loads((OUT/'mouse-linux-build.json').read_bytes())
    need((build.get('version'), build.get('platform'), build.get('arch'), build.get('productName'), build.get('signing')) ==
         (VERSION, 'linux', 'x64', 'Mouse Browser', 'unsigned'), 'build product identity differs')
    need(build.get('source') == p['source'] and int(build.get('runId', 0)) == p['run'] and
         int(build.get('runAttempt', 0)) == p['attempt'] and build.get('packages') == p['packages'] and
         build.get('updateChannel') == CHANNEL, 'build package/source/channel provenance differs')
    with read_artifact(evidence, p['verificationSHA256'], 512*1024**2) as archive:
        entries = archive.infolist()
        need(len(entries) <= 1024 and len({item.filename for item in entries}) == len(entries) and
             sum(item.file_size for item in entries) <= 768*1024**2, 'unsafe or oversized evidence archive')
        raw = archive.read('mouse-linux-verification.json')
        need(build.get('verification', {}).get('file') == 'mouse-linux-verification.json' and
             sha(raw) == build['verification'].get('sha256') and
             json.loads(raw) == build['verification'].get('result'), 'build and raw verification differ')
        summary = verify_evidence(archive.read, p)
        (OUT/'source-linux-verification.json').write_bytes(raw)
        (OUT/'source-independent-evidence.json').write_bytes(json_bytes(summary))
    for file in ('tools/mouse-linux-verify.py', 'tools/mouse-631-acceptance.py', 'desktop/mouse-update.cjs'):
        obj = api(SOURCE, f'contents/{file}?ref={p["source"]}')
        raw = base64.b64decode(obj['content'])
        need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == obj['sha'],
             'source helper Git blob differs')
        if file == 'tools/mouse-631-acceptance.py':
            need(raw == Path(__file__).with_name('mouse633-task-evidence.py').read_bytes(),
                 'source and independent task checker bytes differ')
        (OUT/Path(file).name).write_bytes(raw)
    notes = (STAGE/'RELEASE_NOTES.md').read_text()
    notes += f'\nSource: https://github.com/{SOURCE}/commit/{p["source"]}\nSource checks: https://github.com/{SOURCE}/actions/runs/{p["run"]}\n'
    notes += f'Independent installation: https://github.com/{REPO}/actions/runs/{os.environ["GITHUB_RUN_ID"]}\n\nSHA-256:\n```\n'+(OUT/'SHA256SUMS.txt').read_text()+'```\n'
    (OUT/'RELEASE_NOTES.md').write_text(notes)
    print('MOUSE633_LINUX_IMMUTABLE_SOURCE_IMPORT_PASS', flush=True)


def verify_installed():
    p = pin()
    verify_packages(p)
    environment = {key: value for key, value in os.environ.items() if key not in ('GH_TOKEN', 'GITHUB_TOKEN')}
    with (OUT/'mouse-linux-fresh-verify.log').open('wb') as log:
        subprocess.run([sys.executable, str(OUT/'mouse-linux-verify.py'), str(OUT)],
                       cwd=OUT, env=environment, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=2400)
    summary = verify_evidence(lambda name: (OUT/name).read_bytes(), p)
    (OUT/'installed-independent-evidence.json').write_bytes(json_bytes(summary))
    print('MOUSE633_LINUX_FRESH_INSTALLED_PASS', flush=True)


def release_identity(value, p, expected_id=None):
    release_id = value.get('id') if isinstance(value, dict) else None
    need(type(release_id) is int and release_id > 0 and (expected_id is None or release_id == expected_id) and
         value.get('url') == f'https://api.github.com/repos/{REPO}/releases/{release_id}' and
         value.get('tag_name') == TAG and value.get('name') == RELEASE_TITLE and
         type(value.get('draft')) is bool and value.get('prerelease') is True and
         isinstance(value.get('assets'), list), 'unexpected release identity')
    lines = (value.get('body') or '').splitlines()
    required = [f'Source: https://github.com/{SOURCE}/commit/{p["source"]}',
                f'Source checks: https://github.com/{SOURCE}/actions/runs/{p["run"]}']
    required += [p['packages'][name]['sha256']+'  '+name for name in PACKAGES]
    need(all(line in lines for line in required), 'release does not match both pinned packages and tested source')
    return value


def verify_public_assets(release, p):
    release_identity(release, p)
    verify_packages(p)
    for name in ASSETS:
        raw = (OUT/name).read_bytes()
        found = [asset for asset in release['assets'] if asset.get('name') == name]
        need(len(found) == 1 and found[0].get('state') == 'uploaded' and
             found[0].get('size') == len(raw) and found[0].get('digest') == 'sha256:'+sha(raw),
             'immutable remote asset differs: '+name)
    return release


def publish():
    p = pin()
    verify_packages(p)
    verify_evidence(lambda name: (OUT/name).read_bytes(), p)
    release = find_release(p)
    notes = (OUT/'RELEASE_NOTES.md').read_text()
    if release is None:
        release = release_identity(api(REPO, 'releases', 'POST', {
            'tag_name': TAG, 'target_commitish': 'main', 'name': RELEASE_TITLE, 'body': notes,
            'draft': True, 'prerelease': True, 'make_latest': 'false'}), p)
        need(release['draft'] is True, 'new release must remain draft until all bytes are checked')
    missing = []
    for name in (*ASSETS, 'mouse-linux-verification.json'):
        found = [asset for asset in release['assets'] if asset.get('name') == name]
        raw = (OUT/name).read_bytes()
        if found:
            need(len(found) == 1 and found[0].get('state') == 'uploaded', 'invalid existing asset: '+name)
            if name != 'mouse-linux-verification.json':
                need(found[0].get('size') == len(raw) and found[0].get('digest') == 'sha256:'+sha(raw),
                     'refusing to overwrite immutable asset: '+name)
        else:
            missing.append(name)
    for name in missing:
        upload_release_asset(release['id'], name)
    release = verify_public_assets(read_release(release['id'], p), p)
    if release['draft']:
        release_identity(api(REPO, f'releases/{release["id"]}', 'PATCH', {
            'draft': False, 'prerelease': True, 'make_latest': 'false', 'body': notes}), p, release['id'])
    release = verify_public_assets(read_release(release['id'], p), p)
    need(release['draft'] is False and release.get('published_at'), 'release is not public')
    (OUT/'public-release-verification.json').write_bytes(json_bytes(release))
    print('MOUSE633_LINUX_PUBLIC_PACKAGE_HASHES_PASS', flush=True)


def put_json(file, content):
    old = api(REPO, 'contents/'+file+'?ref=main', missing=True)
    if old:
        previous = json.loads(base64.b64decode(old['content']))
        if previous == content:
            return
        need(previous.get('version') != VERSION, 'same-version metadata is immutable')
        need(tuple(map(int, previous['version'].split('.'))) < tuple(map(int, VERSION.split('.'))),
             'channel downgrade is forbidden')
    payload = {'message': 'Publish verified Mouse Browser 6.0.33 Linux x64 channel', 'branch': 'main',
               'content': base64.b64encode(json_bytes(content)).decode()}
    if old:
        payload['sha'] = old['sha']
    api(REPO, 'contents/'+file, 'PUT', payload)


def channel():
    p = pin()
    verify_packages(p)
    release = verify_public_assets(find_release(p), p)
    need(release['draft'] is False and release.get('published_at'), 'channel requires public packages')
    packages = {}
    for format_, name in [('appimage', APPIMAGE), ('deb', DEB)]:
        asset = next(item for item in release['assets'] if item['name'] == name)
        expected_url = f'https://github.com/{REPO}/releases/download/{TAG}/{name}'
        need(asset.get('browser_download_url') == expected_url, 'public package URL differs')
        packages[format_] = {'url': expected_url, 'size': asset['size'], 'digest': asset['digest']}
    data = {'schema': 1, 'version': VERSION, 'platform': 'linux', 'arch': 'x64',
            **packages['appimage'], 'packages': packages, 'publishedAt': release['published_at']}
    put_json('platforms/linux/mouse-x64/releases/'+VERSION+'.json', data)
    put_json(CHANNEL_PATH, data)
    # Anonymous raw-feed visibility can lag a successful Git commit. Each
    # observation remains recorded; no auth token is supplied to these requests.
    observations = []
    for attempt in range(72):
        try:
            with urllib.request.urlopen(CHANNEL, timeout=30) as response:
                observed = json.load(response)
            observations.append({'attempt': attempt+1, 'version': observed.get('version'), 'matches': observed == data})
            if observed == data:
                break
        except Exception as error:
            observations.append({'attempt': attempt+1, 'error': str(error)[:300]})
        time.sleep(5)
    else:
        (OUT/'linux-channel-observations.json').write_bytes(json_bytes(observations))
        raise ValueError('Anonymous Linux channel did not expose the exact public metadata')
    (OUT/'linux-channel-observations.json').write_bytes(json_bytes(observations))
    (OUT/'linux-channel-expected.json').write_bytes(json_bytes(data))
    environment = {key: value for key, value in os.environ.items() if key not in ('GH_TOKEN', 'GITHUB_TOKEN')}
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs/promises'),os=require('node:os');
const {MouseUpdates,LINUX_CHANNEL}=require('./mouse-update.cjs');
(async()=>{
 const expected=JSON.parse(await fs.readFile('linux-channel-expected.json','utf8')),downloads={};
 assert.equal(LINUX_CHANNEL,'https://raw.githubusercontent.com/jeep-jim/OSMINOG-Releases/main/platforms/linux/mouse-x64/latest.json');
 for(const format of ['appimage','deb']){
  const target={platform:'linux',arch:'x64',format};
  const current=new MouseUpdates({app:{getVersion:()=> '6.0.33'},shell:{},target});
  assert.equal((await current.run('check')).phase,'current');assert.equal(current.state.channel,'static');
  // This is the first Linux release: 0.0.0 is explicitly a comparison fixture,
  // never claimed to be an actual previously shipped Linux binary or updater.
  const test=new MouseUpdates({app:{getVersion:()=> '0.0.0',getPath:()=>os.tmpdir()},shell:{},target});
  assert.equal((await test.run('check')).phase,'available');assert.equal(test.state.channel,'static');
  assert.equal(test.candidate.version,'6.0.33');assert.equal(test.candidate.url,expected.packages[format].url);
  assert.equal(test.candidate.hash,expected.packages[format].digest.slice(7));
  assert.equal(test.candidate.size,expected.packages[format].size);
  assert.equal((await test.run('download')).phase,'ready');await test.verified();
  downloads[format]={size:test.candidate.size,sha256:test.candidate.hash,verified:true,currentVersionCheck:true};
 }
 await fs.writeFile('linux-channel-verification.json',JSON.stringify({ok:true,version:'6.0.33',platform:'linux',arch:'x64',channel:LINUX_CHANNEL,
  anonymous:true,previousVersion:null,firstLinuxRelease:true,comparisonVersionIsFixture:true,comparisonVersion:'0.0.0',
  olderReleasedLinuxUpdaterVerified:false,downloads},null,2));
})().catch(error=>{console.error(error);process.exit(1)});
"""
    subprocess.run(['node', '-e', script], cwd=OUT, env=environment, check=True, timeout=900)
    print('MOUSE633_LINUX_ANONYMOUS_CHANNEL_PACKAGES_PASS', flush=True)


_transport.update(REPO=REPO, SOURCE=SOURCE, VERSION=VERSION, TAG=TAG, RELEASE_TITLE=RELEASE_TITLE,
                  OUT=OUT, api=api, release_identity=release_identity)
if __name__ == '__main__':
    actions = {'validate-template': validate_template, 'import': import_candidate,
               'verify': verify_installed, 'publish': publish, 'channel': channel}
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        raise SystemExit('Expected validate-template, import, verify, publish or channel')
    actions[sys.argv[1]]()
