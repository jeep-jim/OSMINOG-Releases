"""Copy a checksum-pinned, tested CI package into the release registry.
No code from the artifact is executed. Publication/feed changes remain the job
of the existing publisher after it verifies the uploaded release asset.
"""
import hashlib
import io
import json
import pathlib
import re
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = 'jeep-jim/OSMINOG'
REQUIRED = {'OSMINOG 4.0.22 workspace unification', 'Windows desktop compatibility candidate',
            'Workdesk and retained document regression', 'Retired studio compatibility'}
IDENTITY = '1ddb8d87f3a6f6cb38a229bd81ba8076d1d37d3ba6b8a15b2a91129d4904012e'
LIMIT = 64 * 1024 * 1024

def digest(data):
    return hashlib.sha256(data).hexdigest()

def api(path, binary=False):
    data = subprocess.check_output(['gh', 'api', f'repos/{SOURCE}/{path}'])
    return data if binary else json.loads(data)

def files(data):
    if len(data) > LIMIT:
        raise ValueError('Oversized package')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if len(z.infolist()) > 10000 or sum(x.file_size for x in z.infolist()) > 128*1024*1024:
            raise ValueError('Oversized expanded package')
        result = {}
        for item in z.infolist():
            p = pathlib.PurePosixPath(item.filename)
            if p.is_absolute() or '..' in p.parts or '.git' in p.parts or '\\' in item.filename or '\x00' in item.filename:
                raise ValueError('Unsafe ZIP path')
            if (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Symlink in package')
            if item.is_dir():
                continue
            if item.filename in result:
                raise ValueError('Duplicate package entry')
            result[item.filename] = z.read(item)
        return result

def main(version):
    if not re.fullmatch(r'\d+(?:\.\d+){2,3}', version):
        raise ValueError('Invalid version')
    request = json.loads((ROOT/f'staging/chrome-extension/{version}/import-ci.json').read_text())
    if request['version'] != version or request['sourceRepository'] != SOURCE:
        raise ValueError('Wrong import request')
    head = request['sourceCommit']
    if not re.fullmatch(r'[a-f0-9]{40}', head):
        raise ValueError('Invalid source commit')
    runs = [api(f'actions/runs/{int(run_id)}') for run_id in request['verificationRuns']]
    if {r['name'] for r in runs} != REQUIRED or len(runs) != len(REQUIRED):
        raise ValueError('Missing required verification')
    for run in runs:
        if run['head_sha'] != head or run['status'] != 'completed' or run['conclusion'] != 'success':
            raise ValueError('Source verification has not passed')
    comparison = api(f'compare/{head}...main')
    if comparison['status'] not in ('ahead', 'identical') or comparison['behind_by'] != 0:
        raise ValueError('Verified source is not merged into main')
    artifact_id = int(request['artifactId'])
    artifact = api(f'actions/artifacts/{artifact_id}')
    run_id = int(request['sourceWorkflowRun'])
    if artifact['expired'] or artifact['workflow_run']['id'] != run_id or artifact['workflow_run']['head_sha'] != head:
        raise ValueError('Wrong source artifact')
    if not any(r['id'] == run_id and r['name'] == 'OSMINOG 4.0.22 workspace unification' for r in runs):
        raise ValueError('Artifact did not come from the Chrome gate')
    outer = api(f'actions/artifacts/{artifact_id}/zip', binary=True)
    if artifact.get('digest') and artifact['digest'] != 'sha256:'+digest(outer):
        raise ValueError('Source artifact digest mismatch')
    name = request['package']
    if pathlib.PurePosixPath(name).name != name or not name.endswith('.zip'):
        raise ValueError('Invalid package name')
    with zipfile.ZipFile(io.BytesIO(outer)) as z:
        candidates = [i for i in z.infolist() if i.filename in (name, 'artifacts/'+name)]
        if len(candidates) != 1 or candidates[0].file_size > LIMIT:
            raise ValueError('Expected package missing or oversized')
        data = z.read(candidates[0])
    if len(data) != request['size'] or digest(data) != request['sha256']:
        raise ValueError('Tested ZIP byte size / SHA-256 mismatch')
    payload = files(data)
    manifest = json.loads(payload['manifest.json'])
    build = json.loads(payload['OSMINOG_BUILD.json'])
    if manifest['name'] != 'OSMINOG' or manifest['version'] != version or manifest['manifest_version'] != 3:
        raise ValueError('Wrong product / manifest')
    if digest(manifest.get('key', '').encode()) != IDENTITY:
        raise ValueError('Fixed extension identity changed')
    if build['version'] != version or build['manifestVersion'] != version or build['artifact'] != name or build['runtimeVerified'] is not True:
        raise ValueError('Wrong or unverified build metadata')
    if any(n.startswith(('logs/', 'desktop/', 'node_modules/')) or n.endswith('.log') for n in payload):
        raise ValueError('Unexpected build debris')
    feed = json.loads((ROOT/'channels/dev/chrome-extension.json').read_text())
    current = feed.get('signed', feed).get('latest', {}).get('version', '0.0.0')
    if tuple(map(int, current.split('.'))) > tuple(map(int, version.split('.'))):
        raise ValueError('Refusing a version downgrade')
    directory = ROOT/f'platforms/chrome-extension/releases/{version}'
    directory.mkdir(parents=True, exist_ok=True)
    package = directory/name
    if package.exists() and package.read_bytes() != data:
        raise ValueError('Refusing to replace immutable release bytes')
    package.write_bytes(data)
    metadata = dict(schema='osminog-release/v2', product='OSMINOG', platform='chrome-extension',
        version=version, size=len(data), sha256=digest(data), package=name, manifestVersion=version,
        fixedExtensionKeyRequired=True, minDevHubVersion='2.0.0', runtimeVerified=False, ciVerified=True,
        sourceCommit=head, verificationUrl=f'https://github.com/{SOURCE}/actions/runs/{run_id}',
        sourceWorkflowRun=run_id, sourceArtifactId=artifact_id, verificationRuns=request['verificationRuns'], notes=request['notes'])
    (directory/'release-v2.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n')
    (directory/'README.md').write_text(f"# OSMINOG Chrome {version}\n\n{request['notes']}\n\n"
        f"SHA-256: `{digest(data)}`\nРазмер: {len(data)} байт.\n\n"
        f"Проверенная сборка: {metadata['verificationUrl']}\n\n"
        'Архив побайтово совпадает с артефактом CI. Проверка на личном устройстве владельца отдельно не заявляется.\n')
    print(json.dumps({'version': version, 'size': len(data), 'sha256': digest(data)}))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: import_verified_chrome_ci.py VERSION')
    main(sys.argv[1])
