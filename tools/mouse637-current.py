#!/usr/bin/env python3
"""Bind exact-source637 helpers and actual predecessor profile replacement."""
import base64
import hashlib
import json
from pathlib import Path
import runpy

HELPERS = ('mouse-637-upgrade.py', 'mouse-637-profile-upgrade.cjs',
           'mouse-637-baseline-performance.py', 'mouse-637-update-button.py',
           'mouse-637-update-button.cjs', 'mouse-637-update-window.py', 'mouse-smoke-hit-target.cjs')
PUBLISHED_SOURCE = '7c09b6cb9885ce72be41e8f16a35d4c55c9ecde3'
PUBLISHED_UPDATER_BLOB = '91ab363f926774825caf8055b2d3d81bf0d51264'


def fetch_helpers(api, source_repo, source, output):
    for name in HELPERS:
        directory = 'desktop/' if name == 'mouse-smoke-hit-target.cjs' else 'tools/'
        value = api(source_repo, 'contents/' + directory + name + '?ref=' + source)
        raw = base64.b64decode(value['content'])
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        if blob != value.get('sha'):
            raise ValueError('Mouse637 source helper Git blob differs: ' + name)
        (output / name).write_bytes(raw)
    value = api(source_repo, 'contents/desktop/mouse-update.cjs?ref=' + PUBLISHED_SOURCE)
    raw = base64.b64decode(value['content'])
    blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    if blob != value.get('sha') or blob != PUBLISHED_UPDATER_BLOB:
        raise ValueError('Actual published636 updater Git blob differs')
    (output / 'legacy636-update.cjs').write_bytes(raw)


def verify_upgrade(read, *, platform, arch, package=None, packages=None):
    previous = '636'
    marker = 'MOUSE_637_REAL_' + previous + '_TO_637_PROFILE_PASS'
    outer = read('mouse-637-upgrade.log')
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
                stage.get('reportSha256') != hashlib.sha256(read('mouse-637-upgrade.json')).hexdigest()):
            raise ValueError('Current profile process/report byte binding failed')
        if platform == 'linux' and (stage.get('log') != 'mouse-637-upgrade.log' or
                stage.get('logSha256') != hashlib.sha256(outer).hexdigest()):
            raise ValueError('Linux current profile process/log byte binding failed')
        if platform == 'win32':
            retained = report.get('checks', {}).get('ownerFeedback', {})
            if (retained.get('exitCode') != 0 or type(retained.get('pid')) is not int or retained['pid'] <= 0 or
                    type(retained.get('elapsedMs')) not in (int, float) or not 0 < retained['elapsedMs'] <= 270000 or
                    retained.get('requiredMarkers') != ['MOUSE_633_OWNER_FEEDBACK_PASS'] or
                    retained.get('reportSha256') != hashlib.sha256(read('mouse-633-owner-feedback.json')).hexdigest()):
                raise ValueError('Retained owner process/report byte binding failed')
    checker = runpy.run_path(str(Path(__file__).with_name('mouse637-upgrade-evidence.py')))
    result = checker['verify'](read, expected_platform=platform, expected_arch=arch,
                               expected_package=package, expected_packages=packages)
    button = runpy.run_path(str(Path(__file__).with_name('mouse637-update-button-evidence.py')))
    if platform in ('win32', 'linux'):
        child = report.get('checks', {}).get('updateFrom636', {})
        button_log = read('mouse-637-update-button.log')
        if (child.get('exitCode') != 0 or type(child.get('pid')) is not int or child['pid'] <= 0 or
                type(child.get('elapsedMs')) not in (int, float) or not 0 < child['elapsedMs'] <= 720000 or
                child.get('requiredMarkers') != [button['MARKER']] or
                child.get('reportSha256') != hashlib.sha256(read(button['NAME'])).hexdigest() or
                child.get('logSha256') != hashlib.sha256(button_log).hexdigest()):
            raise ValueError('Current native update-button process/log/report binding failed')
        if platform == 'linux' and child.get('log') != 'mouse-637-update-button.log':
            raise ValueError('Linux native button process log differs')
    result['updateFrom636'] = button['verify'](read, expected_platform=platform, expected_arch=arch,
                                            expected_package=package, expected_packages=packages)
    features = runpy.run_path(str(Path(__file__).with_name('mouse637-features-evidence.py')))
    result['features'] = features['verify'](read, expected_platform=platform, expected_arch=arch)
    return result
