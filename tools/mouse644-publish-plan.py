#!/usr/bin/env python3
"""Only the exact Mac644 candidate may activate; other platforms stay on642."""
from contextlib import redirect_stdout
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
VERSION = '6.0.44'
PLATFORMS = {'macos-arm64': ('6.0.44-arm64', 'mouse644-release.py', 'validate',
    'Mouse Browser 6.0.44: publish pinned source and verified Mac packages')}
CLAIMS = ('source', 'sourceMerge', 'sourcePR', 'run', 'artifact', 'verificationArtifact',
          'sourceAttempt', 'sourceJob', 'archiveSHA256', 'verificationSHA256')
PACKAGES = {'Mouse-Browser-6.0.44-mac-arm64.dmg', 'Mouse-Browser-6.0.44-mac-arm64.zip'}


def need(value, message):
    if not value:
        raise ValueError('Mouse644 Mac publication: ' + message)


def read_plan(root=ROOT):
    need(not (root / 'staging/mouse/6.0.44-linux-x64').exists()
         and not (root / 'staging/mouse/6.0.44-windows-x64').exists(),
         'Linux and Windows644 stages are not authorized')
    folder, _, _, trigger = PLATFORMS['macos-arm64']
    stage = root / 'staging/mouse' / folder
    value = json.loads((stage / 'pin.json').read_text(encoding='utf-8'))
    owner = stage / 'PUBLISH_OWNER'
    need(value.get('version') == VERSION and type(value.get('ready')) is bool, 'invalid version/readiness')
    need(set(value.get('packages', {})) == PACKAGES, 'only the Mac644 DMG and ZIP are admitted')
    if not value['ready']:
        need(not owner.exists() and all(value.get(key) is None for key in CLAIMS), 'unready pin claims publication/provenance')
        need(all(isinstance(p, dict) and p.get('size') is None and p.get('sha256') is None
                 for p in value['packages'].values()), 'unready pin claims package bytes')
    else:
        need(owner.is_file() and not owner.is_symlink() and owner.read_text(encoding='utf-8').strip() == trigger,
             'ready pin lacks its exact owner trigger')
    return {'macos-arm64': value}


def publication_ready(platform, *, root=ROOT, load=runpy.run_path):
    need(platform == 'macos-arm64', 'only macos-arm64 is authorized')
    pin = read_plan(root)['macos-arm64']
    if not pin['ready']:
        return False
    with redirect_stdout(sys.stderr):
        load(str(root / 'tools/mouse644-release.py'))['validate']()
    return True


def require_ready(platform):
    need(publication_ready(platform), 'the exact Mac candidate is not ready')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Expected macos-arm64')
    print('publish=' + str(publication_ready(sys.argv[1])).lower())
