#!/usr/bin/env python3
"""Bind actual Mac display names to the installed and updated application."""
from datetime import datetime
import hashlib
import json
from pathlib import PurePosixPath
import re

VERSION = '6.0.44'
TOKEN = 'native644-macos-display-name'
FILES = ('mouse-644-branding.json', 'mouse-644-branding-updated.json',
         'mouse-637-update-button.json', 'mouse-644-sync-processes.json')


def need(value, message):
    if not value:
        raise ValueError('Mouse644 branding: ' + message)


def names(value):
    expected = {'ok': True, 'displayName': 'Mouse', 'localizedDisplayName': 'Mouse',
                'localizedBundleName': 'Mouse', 'compatibilityBundleName': 'Mouse Browser.app',
                'executable': 'Mouse Browser', 'appId': 'com.osminog.desktop.preview', 'version': VERSION}
    need(isinstance(value, dict) and all(value.get(key) == wanted for key, wanted in expected.items()),
         'Finder/Bundle name, stable identity or installed version differs')
    path = value.get('application', '')
    need(isinstance(path, str) and PurePosixPath(path).is_absolute() and '..' not in PurePosixPath(path).parts
         and PurePosixPath(path).name == 'Mouse Browser.app', 'actual installed bundle path is missing')
    languages = value.get('languages')
    need(isinstance(languages, list) and languages == sorted(set(languages))
         and {'en.lproj', 'ru.lproj'} <= set(languages)
         and all(isinstance(item, str) and re.fullmatch('[A-Za-z0-9_-]+\\.lproj', item) for item in languages),
         'actual bundle localization inventory is missing')
    stamp = value.get('verifiedAt')
    need(isinstance(stamp, str), 'native verification time is missing')
    try:
        parsed = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
    except ValueError as error:
        raise ValueError('Mouse644 branding: invalid native verification time') from error
    need(parsed.tzinfo is not None, 'native verification time lacks a timezone')


def verify(read, *, platform='darwin', arch='arm64', build=None):
    need((platform, arch) == ('darwin', 'arm64'), 'only Mac arm64 is authorized')
    artifacts, values = [], []
    for name in FILES:
        raw = read(name)
        need(isinstance(raw, bytes) and 0 < len(raw) <= 16 * 1024**2, 'missing or oversized raw receipt: ' + name)
        artifacts.append({'file': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
        values.append(json.loads(raw))
    installed, updated, update, processes = values
    names(installed); names(updated)
    need(processes.get('version') == VERSION and processes.get('platform') == platform
         and processes.get('arch') == arch
         and processes.get('executable') == installed['application'] + '/Contents/MacOS/Mouse Browser',
         'display-name check belongs to another executable than native644')
    need(update.get('ok') is True and update.get('version') == VERSION
         and update.get('fromVersion') == '6.0.43' and update.get('toVersion') == VERSION
         and update.get('platform') == platform and update.get('arch') == arch
         and update.get('oldInstallation', {}).get('target') == updated['application']
         and update.get('updatedDisplayName') == updated,
         'display name after the actual643 update is unbound')
    if build is not None:
        need(build.get('displayName') == 'Mouse' and build.get('productName') == 'Mouse Browser'
             and build.get('branding') == installed and TOKEN in build.get('tests', []),
             'source manifest does not bind the actual display-name check')
    return {'schema': 1, 'version': VERSION, 'ok': True, 'platform': platform, 'arch': arch,
            'checks': [TOKEN], 'installedApplication': installed['application'],
            'updatedApplication': updated['application'], 'artifacts': artifacts,
            'physicalUserDeviceVerified': False}
