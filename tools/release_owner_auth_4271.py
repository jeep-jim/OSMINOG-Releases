"""Auth-only 4.0.27.1 based on the owner's exact original Chrome 4.0.27 files.
The original ZIP was recovered from the earlier conversation (SHA below).
Existing repository blobs are only a transport; the recovered full file set
must match the original archive's content digest before any hotfix is applied.
No credentials or user workspace data are read by this release tool.
"""
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sys
import release_owner_auth_hotfix as release

ROOT = Path(__file__).resolve().parents[1]
VERSION = '4.0.27.1'
ORIGINAL_SHA = '4e8b8cae4fb69b209bd034f8d6b27ed3670f11ada1087653a2df736692225493'
ORIGINAL_SIZE = 9437252
CONTENT_SHA = '8cf2c8a2453a0b7282ba468d3ac79d91aae7521c7ad5b96951f1a50fe6ff1132'
RECIPE_SHA = 'f0575bf3cbd8ba8ab2f35880ea0ae2c74b98c1a85ed783781e75e3d0f516245e'
TRANSPORT_SHA = 'dba42180425300c5a07d33c1d7d70db82118a529140e33d9c88c63535b7060ea'
TRANSPORT_NAME = 'OSMINOG-Chrome-4.0.25.1-OWNER-AUTH-FIX.zip'
NAME = 'OSMINOG-Chrome-4.0.27.1-OWNER-AUTH-FIX.zip'
NOTES = ('Исправление авторизации поверх исходной OSMINOG Chrome 4.0.27, которую владелец уже установил. '
         'Не переименованная 4.0.25: все 150 файлов исходной 4.0.27 восстановлены с проверкой общего SHA-256. '
         'В готовом выпуске изменены только osminog-owner-guard.js и служебные manifest.json / OSMINOG_BUILD.json; '
         'остальные 147 файлов побайтово сохранены. Ключ незавершённой настройки Authenticator сохраняется '
         'при закрытии и перезагрузке, одновременные запросы не меняют ключ, вставка кода с пробелом исправлена. '
         'Проверка GitHub и одноразового кода сохранена. Обновление — штатной кнопкой «Обновить».')

# Reuse the already-reviewed immutable package / publish metadata implementation.
old = Path(release.__file__).read_bytes()
if hashlib.sha1(b'blob '+str(len(old)).encode()+b'\0'+old).hexdigest() != 'df2c456f78e92b513ac616737b9c41a7ef267e8b':
    raise ValueError('Reviewed release implementation changed')
release.VERSION = VERSION
release.BASE = '4.0.27'
release.BASE_SHA = ORIGINAL_SHA
release.BASE_SIZE = ORIGINAL_SIZE
release.NAME = NAME
release.DEST = ROOT/f'platforms/chrome-extension/releases/{VERSION}'
release.NOTES = NOTES


def safe_name(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or '.git' in p.parts or '\\' in name or '\x00' in name:
        raise ValueError('Unsafe recovery path')
    return name


def content_sha(files):
    return release.sha(''.join(n+'\0'+release.sha(b)+'\n' for n,b in sorted(files.items())).encode())


def baseline():
    archive = ROOT/'platforms/chrome-extension/releases/4.0.25.1'/TRANSPORT_NAME
    data = archive.read_bytes()
    if len(data) != 9354946 or release.sha(data) != TRANSPORT_SHA:
        raise ValueError('Transport package checksum mismatch')
    transport = release.read_files(data)
    path = ROOT/f'staging/chrome-extension/{VERSION}/recover27.json.gz.b64'
    compressed = base64.b64decode(''.join(path.read_text('ascii').split()), validate=True)
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
        raw = stream.read(1024*1024+1)
    if len(raw) > 1024*1024 or release.sha(raw) != RECIPE_SHA:
        raise ValueError('Recovery recipe checksum mismatch')
    recipe = json.loads(raw)
    if recipe['schema'] != 'osminog-recovered-427/v1' or recipe['originalArchiveSha256'] != ORIGINAL_SHA or recipe['originalArchiveSize'] != ORIGINAL_SIZE:
        raise ValueError('Wrong original baseline identity')
    names = recipe['files']
    if len(names) != 150 or len(set(names)) != 150:
        raise ValueError('Wrong original file list')
    result = {}
    for name in names:
        safe_name(name)
        source = ROOT/'work/source'/name
        original = source.read_bytes() if source.is_file() else transport.get(name)
        if original is None:
            raise ValueError('Missing transport file: '+name)
        if name in recipe['changes']:
            parts = []
            for op in recipe['changes'][name]:
                if isinstance(op, list):
                    if len(op) != 2 or any(type(n) is not int for n in op):
                        raise ValueError('Invalid copy operation')
                    offset, count = op
                    if offset < 0 or count < 0 or offset+count > len(original):
                        raise ValueError('Copy operation out of bounds')
                    parts.append(original[offset:offset+count])
                elif isinstance(op, str):
                    parts.append(base64.b64decode(op, validate=True))
                else:
                    raise ValueError('Invalid recovery operation')
            result[name] = b''.join(parts)
        else:
            result[name] = original
    if content_sha(result) != CONTENT_SHA or recipe['contentSha256'] != CONTENT_SHA:
        raise ValueError('Recovered files differ from the owner original 4.0.27 archive')
    if json.loads(result['manifest.json'])['version'] != '4.0.27':
        raise ValueError('Recovered baseline is not Chrome 4.0.27')
    return result


def guard_feed():
    feed = json.loads((ROOT/'channels/dev/chrome-extension.json').read_text())
    current = feed['signed']['latest']['version']
    if tuple(map(int, current.split('.'))) > tuple(map(int, VERSION.split('.'))):
        raise ValueError('A newer channel '+current+' exists; refusing downgrade')
    if feed.get('signature') is not None:
        raise ValueError('Signed channel requires its existing signing pipeline')
    return feed


release.baseline = baseline
release.guard_feed = guard_feed


def prepare():
    release.prepare()
    build_path = release.PACKAGE/'OSMINOG_BUILD.json'
    build = json.loads(build_path.read_text())
    build['baseContentSha256'] = CONTENT_SHA
    build['baseSource'] = 'Recovered original OSMINOG-Chrome-4.0.27.zip from earlier conversation'
    build['verification']['baseline'] = 'All 147 non-auth/non-version files byte-identical to original Chrome 4.0.27'
    release.write_json(build_path, build)
    print('ORIGINAL_4_0_27_BASELINE_VERIFIED: 150 files; content SHA-256 '+CONTENT_SHA)


def archive():
    release.archive()
    for name in ('release-v2.json', 'verification.json'):
        path = release.DEST/name
        record = json.loads(path.read_text())
        record.update(baseVersion='4.0.27', originalArchiveSha256=ORIGINAL_SHA,
                      originalArchiveSize=ORIGINAL_SIZE, baseContentSha256=CONTENT_SHA,
                      baselineFileCount=150, baselineRecoveredFromOriginalArchive=True)
        release.write_json(path, record)
    print('AUTH_ONLY_DIFF_VERIFIED: original 4.0.27 -> 4.0.27.1; 147 files unchanged')


if __name__ == '__main__':
    {'prepare': prepare, 'archive': archive, 'advance': release.advance, 'guard': guard_feed}[sys.argv[1]]()
