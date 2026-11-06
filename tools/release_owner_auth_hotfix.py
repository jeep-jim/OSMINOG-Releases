"""One-purpose owner-auth hotfix based on the already published Chrome 4.0.25.
The release must change only owner guard plus manifest/build version metadata.
No owner credentials are read; verification uses synthetic credentials.
"""
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '4.0.25.1'
BASE = '4.0.25'
BASE_SHA = '9df95f731f5f073de69ce4e35b5f4acac0a58c7846da2854ec77c37ef95fa0e3'
BASE_SIZE = 9417551
SOURCE = '04e02d6dab70294bbfa5dc7cb4dc09753c876d59'
GUARD_BLOB = '303ce01d29948f049b9814eadb66b019672a9966'
NAME = 'OSMINOG-Chrome-4.0.25.1-OWNER-AUTH-FIX.zip'
CHANGED = {'osminog-owner-guard.js', 'manifest.json', 'OSMINOG_BUILD.json'}
PACKAGE = ROOT/'work/package'
DEST = ROOT/f'platforms/chrome-extension/releases/{VERSION}'
NOTES = ('Исправлена привязка Google Authenticator: ключ незавершённой настройки сохраняется при закрытии и перезагрузке; '
         'повторные запросы входа и вкладки используют одну настройку; исправлена вставка кода с пробелом. '
         'Готовая привязка не сбрасывается. Проверка GitHub и шестизначного кода сохранена. '
         'Основа — опубликованная Chrome 4.0.25; рабочий стол, папки, оформление и остальные функции побайтово сохранены. '
         'Обновление устанавливается штатной кнопкой «Обновить».')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def read_files(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if len(z.infolist()) > 10000 or sum(i.file_size for i in z.infolist()) > 128*1024*1024:
            raise ValueError('Oversized package')
        result = {}
        for item in z.infolist():
            p = PurePosixPath(item.filename)
            if p.is_absolute() or '..' in p.parts or '.git' in p.parts or '\\' in item.filename:
                raise ValueError('Unsafe package path')
            if (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Symlink in package')
            if not item.is_dir():
                if item.filename in result:
                    raise ValueError('Duplicate package path')
                result[item.filename] = z.read(item)
        return result

def baseline():
    folder = ROOT/f'platforms/chrome-extension/releases/{BASE}'
    meta = json.loads((folder/'release-v2.json').read_text())
    if meta['sha256'] != BASE_SHA or meta['size'] != BASE_SIZE:
        raise ValueError('Pinned baseline metadata mismatch')
    if PurePosixPath(meta['package']).name != meta['package']:
        raise ValueError('Unsafe baseline package name')
    data = (folder/meta['package']).read_bytes()
    if len(data) != BASE_SIZE or sha(data) != BASE_SHA:
        raise ValueError('Pinned baseline bytes mismatch')
    return read_files(data)

def guard_feed():
    feed = json.loads((ROOT/'channels/dev/chrome-extension.json').read_text())
    current = feed['signed']['latest']['version']
    if current not in (BASE, VERSION):
        raise ValueError('Channel advanced to '+current+'; refusing to replace a newer/different release')
    if feed.get('signature') is not None:
        raise ValueError('Signed channel requires its existing signing pipeline')
    return feed

def prepare():
    guard_feed()
    files = baseline()
    if PACKAGE.exists():
        shutil.rmtree(PACKAGE)
    for name, data in files.items():
        path = PACKAGE/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    source = ROOT/'work/source'
    guard = (source/'osminog-owner-guard.js').read_bytes()
    if hashlib.sha1(b'blob '+str(len(guard)).encode()+b'\0'+guard).hexdigest() != GUARD_BLOB:
        raise ValueError('Owner guard differs from reviewed and tested commit')
    (PACKAGE/'osminog-owner-guard.js').write_bytes(guard)
    manifest = json.loads(files['manifest.json'])
    manifest.update(version=VERSION, version_name=VERSION+' · Owner Authenticator Fix')
    write_json(PACKAGE/'manifest.json', manifest)
    build = json.loads(files['OSMINOG_BUILD.json'])
    build.update(version=VERSION, versionName=manifest['version_name'], manifestVersion=VERSION,
                 artifact=NAME, baseVersion=BASE, baseSha256=BASE_SHA,
                 runtimeVerified=False, ciVerified=True, authSourceCommit=SOURCE,
                 changedFiles=sorted(CHANGED), notes=NOTES,
                 verification={'ownerAuth': '14 independent-vector and lifecycle tests plus real Chromium extension verification gate',
                               'baseline': 'All other runtime files byte-identical to released Chrome 4.0.25',
                               'ownerDevice': 'Not tested on the owner device'})
    build.pop('verificationRun', None)
    write_json(PACKAGE/'OSMINOG_BUILD.json', build)
    (PACKAGE/'tests').mkdir(exist_ok=True)
    for name in ('owner-access-411.cjs', 'owner-totp-enrollment.cjs'):
        shutil.copyfile(source/'tests'/name, PACKAGE/'tests'/name)
    print('Prepared auth-only candidate from exact published baseline; no feed changed')

def archive():
    guard_feed()
    base = baseline()
    shutil.rmtree(PACKAGE/'tests')
    files = {p.relative_to(PACKAGE).as_posix(): p.read_bytes() for p in PACKAGE.rglob('*') if p.is_file()}
    if set(files) != set(base):
        raise ValueError('Package file list changed: '+str(set(files)^set(base)))
    changed = {name for name in files if files[name] != base[name]}
    if changed != CHANGED:
        raise ValueError('Unexpected runtime change: '+str(changed))
    before, after = (json.loads(x['manifest.json']) for x in (base, files))
    for field in set(before)|set(after):
        if field not in ('version', 'version_name') and before.get(field) != after.get(field):
            raise ValueError('Extension identity/permissions/config changed: '+field)
    result = io.BytesIO()
    with zipfile.ZipFile(result, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(files.items()):
            item = zipfile.ZipInfo(name, date_time=(1980,1,1,0,0,0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            z.writestr(item, data, compresslevel=9)
    data = result.getvalue()
    if read_files(data) != files:
        raise ValueError('Archive roundtrip mismatch')
    DEST.mkdir(parents=True, exist_ok=True)
    package = DEST/NAME
    if package.exists() and package.read_bytes() != data:
        raise ValueError('Refusing to overwrite immutable release bytes')
    package.write_bytes(data)
    run = os.environ['GITHUB_RUN_ID']
    verification = f"https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/{run}"
    meta = dict(schema='osminog-release/v2', product='OSMINOG', platform='chrome-extension',
                version=VERSION, package=NAME, size=len(data), sha256=sha(data), manifestVersion=VERSION,
                fixedExtensionKeyRequired=True, minDevHubVersion='2.0.0', runtimeVerified=False,
                ciVerified=True, baseVersion=BASE, baseSha256=BASE_SHA, authSourceCommit=SOURCE,
                verificationUrl=verification, changedFiles=sorted(changed), notes=NOTES)
    write_json(DEST/'release-v2.json', meta)
    write_json(DEST/'verification.json', dict(verificationUrl=verification, unitTests=14, legacyOwnerAccess='pass',
                 realChrome='pass', changedFiles=sorted(changed), unchangedFileCount=len(files)-len(changed),
                 manifestIdentityAndPermissionsPreserved=True, ownerDeviceTested=False,
                 changedFileSha256={name: sha(files[name]) for name in sorted(changed)}))
    (DEST/'README.md').write_text(f'# OSMINOG Chrome {VERSION}\n\n{NOTES}\n\n'
        f'Проверки: 14 тестов авторизации, прежний тест Owner Access и настоящая Chromium-сессия расширения.\n'
        f'Сборка: {verification}\n\nSHA-256: `{sha(data)}`\nРазмер: {len(data)} байт.\n'
        'Установка на компьютере владельца отдельно не проверялась.\n', encoding='utf-8')
    print(json.dumps(meta, ensure_ascii=False))

def advance():
    from datetime import datetime, timezone
    feed = guard_feed()
    meta = json.loads((DEST/'release-v2.json').read_text())
    data = (DEST/NAME).read_bytes()
    if sha(data) != meta['sha256'] or len(data) != meta['size']:
        raise ValueError('Archived package changed')
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
    feed['signed'].update(status='active', generatedAt=now,
        latest=dict(version=VERSION, kind='full-package',
            packageUrl=f'https://github.com/jeep-jim/OSMINOG-Releases/releases/download/chrome-v{VERSION}/{NAME}',
            size=meta['size'], sha256=meta['sha256'], manifestVersion=VERSION,
            fixedExtensionKeyRequired=True, minDevHubVersion='2.0.0', runtimeVerified=False,
            notesUrl=f'https://raw.githubusercontent.com/jeep-jim/OSMINOG-Releases/main/platforms/chrome-extension/releases/{VERSION}/README.md',
            publishedAt=now))
    meta['publishedAt'] = now
    write_json(DEST/'release-v2.json', meta)
    write_json(ROOT/'channels/dev/chrome-extension.json', feed)
    print('Verified channel advanced to '+VERSION)

if __name__ == '__main__':
    {'prepare': prepare, 'archive': archive, 'advance': advance, 'guard': guard_feed}[sys.argv[1]]()
