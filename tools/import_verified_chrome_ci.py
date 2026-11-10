"""Copy a checksum-pinned, tested CI package into the release registry.
No code from the artifact is executed. Publication/feed changes remain the job
of the existing publisher after it verifies the uploaded release asset.
"""
import base64
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
# Stable GitHub workflow identities for a Chrome-only package: Chrome runtime, documents, retained compatibility.
# The Windows native-shell workflow is not a release gate for the Chrome ZIP; its source is unchanged.
CHROME_WORKFLOW = 351479698
REQUIRED_WORKFLOWS = {CHROME_WORKFLOW, 351443074, 351468502}
LIGHT_WORKFLOW = 412858774

def required_workflows(profile):
    if profile not in (None, 'full-workspace', 'light-storage'):
        raise ValueError('Unknown release profile')
    return REQUIRED_WORKFLOWS | ({LIGHT_WORKFLOW} if profile == 'light-storage' else set())
IDENTITY = '1ddb8d87f3a6f6cb38a229bd81ba8076d1d37d3ba6b8a15b2a91129d4904012e'
LIMIT = 64 * 1024 * 1024
RECOVERY_LIMIT = 2 * 1024 * 1024
SAFE_UPDATER_RELEASE = (4, 0, 37, 0)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def version_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d+(?:\.\d+){2,3}', value):
        raise ValueError('Invalid version')
    parts = tuple(map(int, value.split('.')))
    return parts + (0,) * (4-len(parts))

def minimum_updater(metadata, version):
    value = metadata.get('minUpdaterVersion', '1.0.0')
    parsed = version_tuple(value)
    if version_tuple(version) >= SAFE_UPDATER_RELEASE and parsed < (2, 0, 0, 0):
        raise ValueError('This release requires the safe updater version 2.0.0 or newer')
    return value

def validate_build(build, version, name):
    if build.get('version') != version or build.get('manifestVersion') != version or build.get('artifact') != name:
        raise ValueError('Wrong build metadata')
    if version_tuple(version) >= SAFE_UPDATER_RELEASE:
        # CI is not an observation of the owner's installed Windows/Chrome.
        if build.get('ciVerified') is not True or build.get('runtimeVerified') is not False:
            raise ValueError('New packages must distinguish CI verification from owner runtime verification')
    elif build.get('runtimeVerified') is not True:
        # Preserve the historical import contract for immutable older artifacts.
        raise ValueError('Unverified legacy build metadata')

def artifact_member(archive, name, limit=LIMIT):
    candidates = [item for item in archive.infolist() if item.filename in (name, 'artifacts/'+name)]
    if len(candidates) != 1 or candidates[0].is_dir() or candidates[0].file_size > limit:
        raise ValueError('Expected artifact missing, duplicated or oversized: '+name)
    return archive.read(candidates[0])

def validate_recovery_request(value):
    if not isinstance(value, dict) or set(value) != {'filename', 'size', 'sha256'}:
        raise ValueError('Invalid recovery artifact request')
    name = value['filename']
    if not isinstance(name, str) or not re.fullmatch(r'OSMINOG-[A-Za-z0-9._-]+\.html', name):
        raise ValueError('Invalid recovery artifact filename')
    if type(value['size']) is not int or not 0 < value['size'] <= RECOVERY_LIMIT:
        raise ValueError('Invalid recovery artifact size')
    if not isinstance(value['sha256'], str) or not re.fullmatch(r'[a-f0-9]{64}', value['sha256']):
        raise ValueError('Invalid recovery artifact digest')
    return dict(value)

def validate_recovery_page(data, expected, version, manifest, payload):
    expected = validate_recovery_request(expected)
    if len(data) != expected['size'] or digest(data) != expected['sha256']:
        raise ValueError('Recovery artifact byte size / SHA-256 mismatch')
    text = data.decode('utf-8')
    match = re.search(r'const configuration = (\{[^\n]*\});', text)
    if not match:
        raise ValueError('Recovery configuration is missing')
    config = json.loads(match.group(1))
    updater = payload.get('osminog-folder-updater.js')
    if (config.get('schema') != 'osminog-updater-recovery/v1' or
            config.get('product') != 'OSMINOG' or config.get('manifestVersion') != 3 or
            config.get('minimumPackageVersion') != version or
            config.get('manifestKey') != manifest.get('key') or
            version_tuple(config.get('minimumUpdaterVersion')) < (2, 0, 0, 0) or
            updater is None or config.get('updaterSha256') != digest(updater) or
            updater.decode('utf-8') not in text):
        raise ValueError('Recovery page does not match the verified package and updater')
    scripts = re.findall(r'<script>([\s\S]*?)</script>', text)
    if len(scripts) != 1 or len(re.findall(r'<script\b', text, re.I)) != 1:
        raise ValueError('Recovery page must have exactly one embedded script')
    script_hash = base64.b64encode(hashlib.sha256(scripts[0].encode('utf-8')).digest()).decode('ascii')
    if "script-src 'sha256-"+script_hash+"'" not in text:
        raise ValueError('Recovery script CSP digest mismatch')
    return expected

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
    version_tuple(version)
    request = json.loads((ROOT/f'staging/chrome-extension/{version}/import-ci.json').read_text())
    if request['version'] != version or request['sourceRepository'] != SOURCE:
        raise ValueError('Wrong import request')
    min_updater = minimum_updater(request, version)
    recovery_request = validate_recovery_request(request['recovery']) if 'recovery' in request else None
    head = request['sourceCommit']
    if not re.fullmatch(r'[a-f0-9]{40}', head):
        raise ValueError('Invalid source commit')
    runs = [api(f'actions/runs/{int(run_id)}') for run_id in request['verificationRuns']]
    required = required_workflows(request.get('profile'))
    if {r['workflow_id'] for r in runs} != required or len(runs) != len(required):
        raise ValueError('Missing required verification')
    for run in runs:
        if run['head_sha'] != head or run['status'] != 'completed' or run['conclusion'] != 'success':
            raise ValueError('Source verification has not passed')
    # Normal merge commits make the tested source head an ancestor of main.
    # Squash merges do not preserve that ancestry, so bind the tested head to the
    # explicitly merged PR and independently verify that its merge commit is on main.
    merge_commit = request.get('sourceMergeCommit')
    if merge_commit:
        pr_number = int(request['pullRequestNumber'])
        pr = api(f'pulls/{pr_number}')
        if not pr.get('merged') or pr.get('state') != 'closed':
            raise ValueError('Source pull request is not merged')
        if pr.get('base', {}).get('ref') != 'main' or pr.get('head', {}).get('sha') != head:
            raise ValueError('Merged pull request does not match verified source head')
        if pr.get('merge_commit_sha') != merge_commit:
            raise ValueError('Unexpected squash/merge commit')
        comparison = api(f'compare/{merge_commit}...main')
    else:
        comparison = api(f'compare/{head}...main')
    if comparison['status'] not in ('ahead', 'identical') or comparison['behind_by'] != 0:
        raise ValueError('Verified source/merge commit is not merged into main')
    artifact_id = int(request['artifactId'])
    artifact = api(f'actions/artifacts/{artifact_id}')
    run_id = int(request['sourceWorkflowRun'])
    if artifact['expired'] or artifact['workflow_run']['id'] != run_id or artifact['workflow_run']['head_sha'] != head:
        raise ValueError('Wrong source artifact')
    package_workflow = LIGHT_WORKFLOW if request.get('profile') == 'light-storage' else CHROME_WORKFLOW
    if not any(r['id'] == run_id and r['workflow_id'] == package_workflow for r in runs):
        raise ValueError('Artifact did not come from the Chrome gate')
    outer = api(f'actions/artifacts/{artifact_id}/zip', binary=True)
    if artifact.get('digest') and artifact['digest'] != 'sha256:'+digest(outer):
        raise ValueError('Source artifact digest mismatch')
    name = request['package']
    if pathlib.PurePosixPath(name).name != name or not name.endswith('.zip'):
        raise ValueError('Invalid package name')
    with zipfile.ZipFile(io.BytesIO(outer)) as z:
        data = artifact_member(z, name)
        recovery_data = artifact_member(z, recovery_request['filename'], RECOVERY_LIMIT) if recovery_request else None
    if len(data) != request['size'] or digest(data) != request['sha256']:
        raise ValueError('Tested ZIP byte size / SHA-256 mismatch')
    payload = files(data)
    manifest = json.loads(payload['manifest.json'])
    build = json.loads(payload['OSMINOG_BUILD.json'])
    if manifest['name'] != 'OSMINOG' or manifest['version'] != version or manifest['manifest_version'] != 3:
        raise ValueError('Wrong product / manifest')
    if digest(manifest.get('key', '').encode()) != IDENTITY:
        raise ValueError('Fixed extension identity changed')
    validate_build(build, version, name)
    if request.get('profile') == 'light-storage':
        if build.get('profile') != 'light-storage' or build.get('sourceHeadCommit') != head:
            raise ValueError('Light profile/source mismatch')
        if manifest.get('background', {}).get('service_worker') != 'light/background.js':
            raise ValueError('Old background in light package')
        if manifest.get('optional_host_permissions') != ['https://api.openai.com/*', 'https://api.deepseek.com/*']:
            raise ValueError('Unexpected light AI providers')
        if any(n in payload for n in ['editor.js', 'background.js', 'module-frame.html']):
            raise ValueError('Legacy heavy runtime in light package')
        with zipfile.ZipFile(io.BytesIO(outer)) as z:
            report = json.loads(artifact_member(z, 'light-browser-results.json'))
        if report.get('ok') is not True or report.get('crashes') or report.get('errors'):
            raise ValueError('Light native browser report failed')
    if recovery_request:
        validate_recovery_page(recovery_data, recovery_request, version, manifest, payload)
    if any(n.startswith(('logs/', 'desktop/', 'node_modules/')) or n.endswith('.log') for n in payload):
        raise ValueError('Unexpected build debris')
    feed = json.loads((ROOT/'channels/dev/chrome-extension.json').read_text())
    current = feed.get('signed', feed).get('latest', {}).get('version', '0.0.0')
    if version_tuple(current) > version_tuple(version):
        raise ValueError('Refusing a version downgrade')
    directory = ROOT/f'platforms/chrome-extension/releases/{version}'
    directory.mkdir(parents=True, exist_ok=True)
    package = directory/name
    if package.exists() and package.read_bytes() != data:
        raise ValueError('Refusing to replace immutable release bytes')
    recovery_path = directory/recovery_request['filename'] if recovery_request else None
    if recovery_path and recovery_path.exists() and recovery_path.read_bytes() != recovery_data:
        raise ValueError('Refusing to replace immutable recovery bytes')
    package.write_bytes(data)
    if recovery_path:
        recovery_path.write_bytes(recovery_data)
    metadata = dict(schema='osminog-release/v2', product='OSMINOG', platform='chrome-extension',
        version=version, size=len(data), sha256=digest(data), package=name, manifestVersion=version,
        fixedExtensionKeyRequired=True, minDevHubVersion='2.0.0', minUpdaterVersion=min_updater, runtimeVerified=False, ciVerified=True,
        sourceCommit=head, verificationUrl=f'https://github.com/{SOURCE}/actions/runs/{run_id}',
        sourceWorkflowRun=run_id, sourceArtifactId=artifact_id, verificationRuns=request['verificationRuns'], notes=request['notes'])
    if recovery_request:
        metadata['recovery'] = recovery_request
    (directory/'release-v2.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n')
    (directory/'README.md').write_text(f"# OSMINOG Chrome {version}\n\n{request['notes']}\n\n"
        f"SHA-256: `{digest(data)}`\nРазмер: {len(data)} байт.\n\n"
        f"Проверенная сборка: {metadata['verificationUrl']}\n\n"
        'Архив побайтово совпадает с артефактом CI. Проверка на личном устройстве владельца отдельно не заявляется.\n'+
        (f"\nРазовый помощник восстановления: `{recovery_request['filename']}`; "
         f"SHA-256 `{recovery_request['sha256']}`, {recovery_request['size']} байт. "
         'Получен из того же проверенного CI-артефакта.\n' if recovery_request else ''))
    print(json.dumps({'version': version, 'size': len(data), 'sha256': digest(data),
        'minUpdaterVersion': min_updater, 'recovery': recovery_request}))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: import_verified_chrome_ci.py VERSION')
    main(sys.argv[1])
