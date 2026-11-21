#!/usr/bin/env python3
"""Bind exact-source636 helpers and actual predecessor profile replacement."""
import base64
import hashlib
import json
from pathlib import Path
import runpy

HELPERS = ('mouse-636-upgrade.py', 'mouse-636-profile-upgrade.cjs',
           'mouse-636-baseline-performance.py')


def fetch_helpers(api, source_repo, source, output):
    for name in HELPERS:
        value = api(source_repo, 'contents/tools/' + name + '?ref=' + source)
        raw = base64.b64decode(value['content'])
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        if blob != value.get('sha'):
            raise ValueError('Mouse636 source helper Git blob differs: ' + name)
        (output / name).write_bytes(raw)


def verify_upgrade(read, *, platform, arch, package=None, packages=None):
    previous = '635' if platform == 'darwin' else '634'
    marker = 'MOUSE_636_REAL_' + previous + '_TO_636_PROFILE_PASS'
    outer = read('mouse-636-upgrade.log')
    if not isinstance(outer, bytes) or not 0 < len(outer) <= 16 * 1024**2 or marker not in outer.decode('utf-8').splitlines():
        raise ValueError('Actual published predecessor replacement marker missing')
    if platform in ('win32', 'linux'):
        raw = read('mouse-' + ('windows' if platform == 'win32' else 'linux') + '-verification.json')
        if not isinstance(raw, bytes) or not 0 < len(raw) <= 4 * 1024**2:
            raise ValueError('Current profile process wrapper missing')
        report = json.loads(raw)
        stage = report.get('checks', {}).get('freshUpgrade', {})
        budget = 720000 if platform == 'linux' else 480000
        if (stage.get('exitCode') != 0 or type(stage.get('pid')) is not int or stage['pid'] <= 0 or
                type(stage.get('elapsedMs')) not in (int, float) or not 0 < stage['elapsedMs'] <= budget or
                stage.get('requiredMarkers') != [marker] or
                stage.get('reportSha256') != hashlib.sha256(read('mouse-636-upgrade.json')).hexdigest()):
            raise ValueError('Current profile process/report byte binding failed')
        if platform == 'linux' and (stage.get('log') != 'mouse-636-upgrade.log' or
                stage.get('logSha256') != hashlib.sha256(outer).hexdigest()):
            raise ValueError('Linux current profile process/log byte binding failed')
        if platform == 'win32':
            retained = report.get('checks', {}).get('ownerFeedback', {})
            if (retained.get('exitCode') != 0 or type(retained.get('pid')) is not int or retained['pid'] <= 0 or
                    type(retained.get('elapsedMs')) not in (int, float) or not 0 < retained['elapsedMs'] <= 270000 or
                    retained.get('requiredMarkers') != ['MOUSE_633_OWNER_FEEDBACK_PASS'] or
                    retained.get('reportSha256') != hashlib.sha256(read('mouse-633-owner-feedback.json')).hexdigest()):
                raise ValueError('Retained owner process/report byte binding failed')
    checker = runpy.run_path(str(Path(__file__).with_name('mouse636-upgrade-evidence.py')))
    return checker['verify'](read, expected_platform=platform, expected_arch=arch,
                             expected_package=package, expected_packages=packages)
