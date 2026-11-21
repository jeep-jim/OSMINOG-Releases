#!/usr/bin/env python3
"""Release636 only when all three native candidates share one merged source."""
from contextlib import redirect_stdout
import json
from pathlib import Path
import re
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = {
    'macos-arm64': ('6.0.36-arm64', 'mouse636-release.py', 'validate',
                    'Mouse Browser 6.0.36: publish pinned source and verified Mac packages'),
    'windows-x64': ('6.0.36-windows-x64', 'mouse636-windows-release.py', 'pin',
                    'Publish verified Mouse Browser 6.0.36 Windows x64'),
    'linux-x64': ('6.0.36-linux-x64', 'mouse636-linux-release.py', 'pin',
                  'Publish verified Mouse Browser 6.0.36 Linux x64'),
}
CLAIMS = ('source', 'sourceMerge', 'sourcePR', 'run', 'artifact', 'verificationArtifact',
          'sourceAttempt', 'sourceJob', 'attempt', 'job', 'archiveSHA256',
          'artifactSHA256', 'verificationSHA256')


def read_plan(root=ROOT):
    pins = {}
    for platform, (folder, _, _, trigger) in PLATFORMS.items():
        stage = root / 'staging/mouse' / folder
        value = json.loads((stage / 'pin.json').read_text(encoding='utf-8'))
        owner = stage / 'PUBLISH_OWNER'
        if value.get('version') != '6.0.36' or type(value.get('ready')) is not bool:
            raise ValueError('Invalid636 platform identity/readiness: ' + platform)
        if not value['ready']:
            if owner.exists() or any(value.get(key) is not None for key in CLAIMS):
                raise ValueError('Unready636 platform has publication or provenance claims: ' + platform)
            packages = value.get('packages') or {'installer': value.get('package')}
            if not packages or any(not isinstance(p, dict) or p.get('size') is not None or p.get('sha256') is not None for p in packages.values()):
                raise ValueError('Unready636 platform has package claims: ' + platform)
        elif not owner.is_file() or owner.is_symlink() or owner.read_text(encoding='utf-8').strip() != trigger:
            raise ValueError('Ready636 platform lacks its exact owner trigger: ' + platform)
        pins[platform] = value
    return pins


def publication_ready(platform, *, root=ROOT, load=runpy.run_path):
    if platform not in PLATFORMS:
        raise ValueError('Unknown636 publication platform')
    pins = read_plan(root)
    if not all(value['ready'] for value in pins.values()):
        return False
    for key in ('source', 'sourceMerge'):
        values = {value.get(key) for value in pins.values()}
        if len(values) != 1 or not re.fullmatch('[0-9a-f]{40}', next(iter(values)) or ''):
            raise ValueError('Three636 packages must share the same exact merged ' + key)
    if len({value.get('sourcePR') for value in pins.values()}) != 1:
        raise ValueError('Three636 packages must bind the same tested source PR')
    # Existing exact-source/bytes checks still run again inside each publisher.
    with redirect_stdout(sys.stderr):
        for _, module, entry, _ in PLATFORMS.values():
            load(str(root / 'tools' / module))[entry]()
    return True


def require_ready(platform):
    if not publication_ready(platform):
        raise ValueError('All three636 native candidates are required before publication')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Expected macos-arm64, windows-x64 or linux-x64')
    print('publish=' + str(publication_ready(sys.argv[1])).lower())
