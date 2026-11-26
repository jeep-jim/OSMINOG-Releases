#!/usr/bin/env python3
"""Fail-closed638 pins and verified macOS → Linux → Windows publication."""
from contextlib import redirect_stdout
import hashlib
import json
from pathlib import Path
import re
import runpy
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
VERSION = '6.0.40'
PLATFORMS = {
    'macos-arm64': ('6.0.40-arm64', 'mouse640-release.py', 'validate',
                    'Mouse Browser 6.0.40: publish pinned source and verified Mac packages'),
    'linux-x64': ('6.0.40-linux-x64', 'mouse640-linux-release.py', 'pin',
                  'Publish verified Mouse Browser 6.0.40 Linux x64'),
    'windows-x64': ('6.0.40-windows-x64', 'mouse640-windows-release.py', 'pin',
                    'Publish verified Mouse Browser 6.0.40 Windows x64'),
}
CHANNELS = {
    'macos-arm64': ('channels/mouse/macos-arm64.json', 'darwin', 'arm64', 'quadro-macos-v6.0.40-arm64'),
    'linux-x64': ('platforms/linux/mouse-x64/latest.json', 'linux', 'x64', 'mouse-linux-v6.0.40-x64'),
    'windows-x64': ('platforms/windows/mouse-x64/latest.json', 'win32', 'x64', 'mouse-windows-v6.0.40-x64'),
}
CLAIMS = ('source', 'sourceMerge', 'sourcePR', 'run', 'artifact', 'verificationArtifact',
          'sourceAttempt', 'sourceJob', 'attempt', 'job', 'archiveSHA256',
          'artifactSHA256', 'verificationSHA256', 'nobleJob', 'nobleArtifact', 'nobleSHA256',
          'modernJob', 'modernArtifact', 'modernSHA256')


def need(value, message):
    if not value:
        raise ValueError(message)


def read_plan(root=ROOT):
    pins = {}
    for platform, (folder, _, _, trigger) in PLATFORMS.items():
        stage = root / 'staging/mouse' / folder
        value = json.loads((stage / 'pin.json').read_text(encoding='utf-8'))
        owner = stage / 'PUBLISH_OWNER'
        need(value.get('version') == VERSION and type(value.get('ready')) is bool,
             'Invalid638 platform identity/readiness: ' + platform)
        if not value['ready']:
            need(not owner.exists() and all(value.get(key) is None for key in CLAIMS),
                 'Unready638 platform claims publication/provenance: ' + platform)
            packages = value.get('packages') or {'installer': value.get('package')}
            need(packages and all(isinstance(p, dict) and p.get('size') is None and p.get('sha256') is None
                                  for p in packages.values()), 'Unready638 platform claims package bytes')
        else:
            need(owner.is_file() and not owner.is_symlink() and owner.read_text(encoding='utf-8').strip() == trigger,
                 'Ready638 platform lacks its exact owner trigger: ' + platform)
        pins[platform] = value
    ready = [p for p in pins.values() if p['ready']]
    for key in ('source', 'sourceMerge'):
        values = {p.get(key) for p in ready}
        need(not values or (len(values) == 1 and re.fullmatch('[0-9a-f]{40}', next(iter(values)) or '')),
             'Ready638 packages do not share the same tested/merged source')
    need(len({p.get('sourcePR') for p in ready}) <= 1, 'Ready638 packages have different source PRs')
    return pins


def get_json(url):
    request = urllib.request.Request(url, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'Mouse638-release-order'})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read(4 * 1024**2 + 1)
    need(len(raw) <= 4 * 1024**2, 'Public order-check response is oversized')
    return json.loads(raw)


def verify_previous_public(platform, pin, *, fetch=get_json, download=True):
    path, os_name, arch, tag = CHANNELS[platform]
    feed = fetch('https://raw.githubusercontent.com/jeep-jim/OSMINOG-Releases/main/' + path)
    need((feed.get('version'), feed.get('platform'), feed.get('arch')) == (VERSION, os_name, arch),
         'Earlier platform public update feed is not638: ' + platform)
    release = fetch('https://api.github.com/repos/jeep-jim/OSMINOG-Releases/releases/tags/' + tag)
    need(release.get('tag_name') == tag and release.get('draft') is False and release.get('published_at'),
         'Earlier platform638 release is not public: ' + platform)
    packages = pin.get('packages') or {pin['package']['name']: pin['package']}
    assets = {a.get('name'): a for a in release.get('assets', [])}
    expected = {}
    for name, package in packages.items():
        url = 'https://github.com/jeep-jim/OSMINOG-Releases/releases/download/' + tag + '/' + name
        asset = assets.get(name, {})
        need(asset.get('browser_download_url') == url and asset.get('size') == package['size']
             and asset.get('digest') == 'sha256:' + package['sha256'], 'Earlier platform public asset differs: ' + name)
        expected[name] = {'url': url, 'size': package['size'], 'digest': 'sha256:' + package['sha256']}
        if download:
            digest, size = hashlib.sha256(), 0
            with urllib.request.urlopen(url, timeout=180) as response:
                while chunk := response.read(1024**2):
                    size += len(chunk)
                    need(size <= package['size'], 'Earlier platform public download exceeds pinned size')
                    digest.update(chunk)
            need(size == package['size'] and digest.hexdigest() == package['sha256'],
                 'Earlier platform anonymous package download differs: ' + name)
    primary = ('Mouse-Browser-6.0.40-mac-arm64.dmg' if os_name == 'darwin' else
               'Mouse-Browser-6.0.40-Linux-x64.AppImage' if os_name == 'linux' else 'Mouse-Browser-6.0.40-Windows-x64.exe')
    need(all(feed.get(k) == v for k, v in expected[primary].items()), 'Earlier platform feed points to different bytes')
    if os_name == 'linux':
        need(feed.get('packages') == {'appimage': expected[primary], 'deb': expected['Mouse-Browser-6.0.40-Linux-x64.deb']},
             'Earlier Linux feed does not contain both verified formats')
    return {'platform': platform, 'version': VERSION, 'releaseId': release['id'], 'publishedAt': release['published_at'],
            'packages': expected, 'anonymousDownloadsVerified': download}


def publication_ready(platform, *, root=ROOT, load=runpy.run_path, check_public=verify_previous_public):
    need(platform in PLATFORMS, 'Unknown638 publication platform')
    pins = read_plan(root)
    order = list(PLATFORMS)
    needed = order[:order.index(platform) + 1]
    if any(not pins[item]['ready'] for item in needed):
        return False
    with redirect_stdout(sys.stderr):
        for item in needed:
            _, module, entry, _ = PLATFORMS[item]
            load(str(root / 'tools' / module))[entry]()
        for previous_platform in needed[:-1]:
            check_public(previous_platform, pins[previous_platform])
    return True


def require_ready(platform):
    need(publication_ready(platform), 'Selected638 candidate or preceding public platform is not ready')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Expected macos-arm64, linux-x64 or windows-x64')
    print('publish=' + str(publication_ready(sys.argv[1])).lower())
