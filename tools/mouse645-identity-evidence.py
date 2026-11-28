#!/usr/bin/env python3
"""Run and independently verify the installed Mac645 account/Flash UI gate."""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import time

VERSION = '6.0.45'
PHASES = (('write', '--mouse-645-smoke', 'MOUSE_645_UI_WRITE_PASS', 300),
          ('read', '--mouse-645-read', 'MOUSE_645_UI_NATIVE_PASS', 120))
CAPTURES = {'mouse-645-account-light.png': '#mouse-account-intro',
            'mouse-645-account-dark.png': '#mouse-account-intro',
            'mouse-645-account-narrow.png': '#mouse-account-intro',
            'mouse-645-flash-light.png': '#flash-dialog>header',
            'mouse-645-flash-dark.png': '#flash-dialog>header',
            'mouse-645-restored.png': '#mouse-account-intro'}
_spec = importlib.util.spec_from_file_location('mouse645_retained_pixels', Path(__file__).with_name('mouse645-polish-evidence.py'))
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)
P = R.P


def need(value, message):
    if not value:
        raise ValueError('Mouse645: ' + message)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def image(read, name, digest, dimensions):
    need(isinstance(name, str) and re.fullmatch(r'mouse-645-[a-z0-9-]+\.png', name), 'unsafe screenshot filename')
    raw = read(name)
    need(sha(raw) == digest, 'screenshot bytes differ from their receipt')
    decoded = P.decode_png(raw, name)
    need(dimensions == {key: decoded[key] for key in ('width', 'height')}, 'screenshot dimensions differ')
    return decoded


# Reuse the retained OS-display crop, native input and exact shell-pixel gates.
# This suite changes only its own filename boundary, never the older checks.
R.image = image
P.read_png = image


def flash_pixels(read, capture):
    proof = capture.get('flash', {})
    need(proof.get('visible') is True and proof.get('attached') is True
         and proof.get('sandbox') is True and proof.get('contextIsolation') is True
         and proof.get('nodeIntegration') is False
         and proof.get('parentWindowId') == proof.get('mainWindowId'), 'Flash is not an attached sandboxed native child view')
    reference = image(read, proof.get('filename'), proof.get('sha256'), proof.get('pixelSize'))
    native = image(read, capture['filename'], capture['sha256'], capture['pixelSize'])
    bounds = P.rectangle(proof.get('bounds'), 'native Flash bounds')
    viewport = proof.get('viewport', {})
    need(viewport == {'width': bounds['width'], 'height': bounds['height']}, 'Flash renderer/native viewports differ')
    mapping = proof.get('mapping', {})
    expected = {**capture['mapping'],
                'originX': capture['mapping']['originX'] + bounds['x'] * capture['mapping']['scaleX'],
                'originY': capture['mapping']['originY'] + bounds['y'] * capture['mapping']['scaleY']}
    need(all(P.finite(mapping.get(key)) and abs(mapping[key] - value) < 1e-8 for key, value in expected.items()), 'Flash DPI mapping differs')
    regions = proof.get('regions', [])
    need([region.get('label') for region in regions] == ['.intro', '.modes'], 'real Flash explanation and controls were not captured')
    rsx, rsy = reference['width'] / viewport['width'], reference['height'] / viewport['height']
    for region in regions:
        box = P.rectangle(region.get('bounds'), 'Flash content')
        need(box['x'] >= 0 and box['y'] >= 0 and box['x'] + box['width'] <= viewport['width']
             and box['y'] + box['height'] <= viewport['height'], 'Flash content is clipped outside its native viewport')
        colors_a, colors_b = set(), set()
        for y in range(math.ceil((box['y'] + 1) * rsy), math.floor((box['y'] + box['height'] - 1) * rsy)):
            for x in range(math.ceil((box['x'] + 1) * rsx), math.floor((box['x'] + box['width'] - 1) * rsx)):
                ax = math.floor(mapping['originX'] + (x + .5) / rsx * mapping['scaleX'])
                ay = math.floor(mapping['originY'] + (y + .5) / rsy * mapping['scaleY'])
                a, b = P.pixel(reference, x, y), P.pixel(native, ax, ay)
                need(P.close_rgba(a, b, 2), 'actual OS pixels do not contain the native Flash content')
                if len(colors_a) < 3:
                    colors_a.add(tuple(a))
                if len(colors_b) < 3:
                    colors_b.add(tuple(b))
        need(len(colors_a) >= 3 and len(colors_b) >= 3, 'Flash is a blank rectangle')


def verify(read):
    facts = json.loads(read('mouse-645-ui.json'))
    written = json.loads(read('mouse-645-ui-write.json'))
    processes = json.loads(read('mouse-645-processes.json'))
    need(facts.get('schema') == 1 and facts.get('version') == VERSION
         and facts.get('platform') == 'darwin' and facts.get('arch') == 'arm64'
         and facts.get('packaged') is True and facts.get('physicalUserDeviceVerified') is False
         and facts.get('phase') == 'read' and facts.get('ok') is True
         and facts.get('writeComplete') is True and facts.get('awaitingRestart') is False, 'incomplete installed Mac proof')
    need(written.get('phase') == 'write' and written.get('writeComplete') is True
         and written.get('awaitingRestart') is True and written.get('ok') is False
         and written.get('write') == facts.get('write'), 'write phase was replaced')
    for key in ('schema', 'version', 'platform', 'arch', 'packaged', 'profile', 'pid', 'writePid'):
        need(written.get(key) == facts.get(key), 'native process identity changed')
    need(processes.get('version') == VERSION and processes.get('platform') == 'darwin'
         and processes.get('arch') == 'arm64' and processes.get('profile') == facts.get('profile')
         and Path(facts.get('profile', '')).is_absolute()
         and Path(processes.get('executable', '')).is_absolute()
         and re.fullmatch('[0-9a-f]{64}', processes.get('executableSha256', ''))
         and processes.get('reportSha256') == sha(read('mouse-645-ui.json')), 'executable/profile/report binding differs')
    for phase, _, marker, budget in PHASES:
        receipt = processes.get(phase, {})
        part = facts.get('write' if phase == 'write' else 'restart', {})
        report = 'mouse-645-ui-write.json' if phase == 'write' else 'mouse-645-ui.json'
        log = 'mouse-645-' + phase + '.log'
        need(type(part.get('pid')) is int and part['pid'] > 0 and receipt.get('pid') == part['pid']
             and receipt.get('exitCode') == 0 and receipt.get('report') == report
             and receipt.get('reportSha256') == sha(read(report))
             and receipt.get('log') == log and receipt.get('logSha256') == sha(read(log))
             and marker in read(log).decode('utf-8').splitlines()
             and 0 < receipt.get('elapsedMs', 0) <= budget * 1000, 'missing actual process/exit/marker binding')
    write, restart = facts['write'], facts['restart']
    need(write['pid'] == facts['pid'] and restart['pid'] != write['pid'], 'appearance was not checked in a distinct process')
    for row in (facts, written):
        need(not row.get('error') and not row.get('cleanupError') and row.get('cleanup', {}).get('restored') is True
             and row['cleanup'].get('desktopStateRestored') is True, 'fixture cleanup did not restore the browser')
    need(write.get('expectedAppearance') == write.get('persisted') == restart.get('nativeAppearance')
         == restart.get('initial', {}).get('appearance') == restart['initial'].get('preferences', {}).get('appearance')
         and write['expectedAppearance'].get('paneMode') == 'square'
         and write['expectedAppearance'].get('whiteTone') == 71
         and write['expectedAppearance'].get('tones') == {'whiteTemperature': 18, 'blackTone': 42, 'blackTemperature': -12}
         and restart['initial'].get('theme') == 'light' and restart['initial'].get('versionHidden') is True, 'full appearance failed native save/restart roundtrip')
    account = write.get('account', [])
    need([row.get('theme') for row in account] == ['light', 'dark'], 'both account themes are missing')
    for row in account:
        ui = row.get('ui', {})
        need(row.get('phase') == 'guest' and ui.get('accountOpen') is True and ui.get('settingsOpen') is True
             and ui.get('profileVisible') is True and ui.get('settingsVersion') == 'v' + VERSION
             and ui.get('settingsUpdateVisible') is True and ui.get('versionVisible') is False
             and ui.get('loginDisabled') is (not row.get('available')) and ui.get('sidebarOverflow') is False,
             'optional account or relocated version controls differ')
    narrow = write.get('narrow', {})
    need(narrow.get('ui', {}).get('sidebarOverflow') is False and narrow['ui']['settingsBounds']['width'] <= 620,
         'responsive account sidebar is missing')
    transfer = write.get('flash', [])
    need([row.get('theme') for row in transfer] == ['light', 'dark'], 'both native Flash themes are missing')
    for row in transfer:
        host, child, ui = row.get('host', {}), row.get('child', {}), row.get('ui', {})
        need(host.get('visible') is True and host.get('attached') is True and host.get('sandbox') is True
             and host.get('contextIsolation') is True and host.get('nodeIntegration') is False
             and host.get('parentWindowId') == host.get('mainWindowId')
             and child.get('panel') is True and child.get('overflow') is False
             and child.get('theme') == row['theme'] and ui.get('flashOpen') is True, 'Flash is not the live native sidebar')
        need(all(abs(host['bounds'][key] - ui['flashSlot'][key]) <= 1 for key in ('x', 'y', 'width', 'height')), 'native Flash does not occupy its actual DOM slot')
    overlay = write.get('overlay', {})
    need(overlay.get('modalOpen') is True and overlay.get('hidden', {}).get('visible') is False
         and overlay.get('restored', {}).get('visible') is True
         and overlay['hidden']['webContentsId'] == overlay['restored']['webContentsId']
         and write.get('receive', {}).get('child', {}).get('receivePanel') is True, 'native Flash modal barrier/receiver control failed')
    update = write.get('update', {})
    need(update.get('fixtureOnly') is True and update.get('externalReleaseVerified') is False
         and update.get('available', {}).get('phase') == 'available'
         and update['available'].get('availableVersion') == '6.0.46'
         and update.get('current', {}).get('phase') == 'current'
         and update['current'].get('availableVersion') == '', 'update entry did not follow actual checked manifest state')
    private = write.get('private', {})
    need(private.get('privateMode') is True and private.get('flashButtonDisabled') is True
         and private.get('accountOpen') is False and private.get('passwordsEmpty') is True, 'private profile exposed Flash or account fields')
    R.same_page(write.get('livePage', {}).get('before'), write.get('livePage', {}).get('after'))
    inputs = facts.get('nativeInputs', [])
    need(inputs and any(row.get('surface') == 'flash' and row.get('selector') == '#receive-mode' for row in inputs), 'native Flash button input was not delivered')
    for row in inputs:
        need(row.get('pid') in (write['pid'], restart['pid']), 'input is from an unrelated process')
        R.native_input(row, row['pid'])
    captures = facts.get('captures', [])
    need(len(captures) == len(CAPTURES) and {row.get('filename') for row in captures} == set(CAPTURES), 'required native screenshots are missing')
    for capture in captures:
        R.shell_capture(read, capture, capture['filename'], CAPTURES[capture['filename']])
        if '-flash-' in capture['filename']:
            flash_pixels(read, capture)
    return {'schema': 1, 'version': VERSION, 'status': 'PASS', 'platform': 'darwin', 'arch': 'arm64',
            'checks': ['native-account-sidebar-and-lightweight-sync-disclosure', 'native-flash-sidebar-and-overlay-barrier',
                       'conditional-update-entry', 'native-appearance-distinct-process-roundtrip'],
            'captures': list(CAPTURES), 'physicalUserDeviceVerified': False}


def run_phase(executable, directory, env, phase, flag, marker, budget):
    logfile = directory / ('mouse-645-' + phase + '.log')
    with logfile.open('w', encoding='utf-8') as log:
        started = time.monotonic()
        process = subprocess.Popen([str(executable), flag], cwd=directory, env=env, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            process.wait(timeout=budget)
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=20)
        elapsed = round((time.monotonic() - started) * 1000)
    output = logfile.read_text(encoding='utf-8')
    print(output, flush=True)
    need(process.returncode == 0 and marker in output.splitlines(), phase + ' process failed')
    return {'pid': process.pid, 'exitCode': process.returncode, 'elapsedMs': elapsed,
            'log': logfile.name, 'logSha256': sha(logfile.read_bytes())}


def run(executable, directory, profile, env=None):
    executable, directory, profile = map(lambda value: Path(value).resolve(), (executable, directory, profile))
    need(executable.is_file(), 'installed executable is missing')
    directory.mkdir(parents=True, exist_ok=True)
    need(not profile.exists() or profile.is_dir() and not any(profile.iterdir()), 'a fresh isolated CI profile is required')
    profile.mkdir(parents=True, exist_ok=True, mode=0o700)
    environment = {**(os.environ if env is None else env), 'CI': 'true', 'MOUSE_TEST_PROFILE': str(profile)}
    receipts = {'schema': 1, 'version': VERSION, 'platform': 'darwin', 'arch': 'arm64',
                'executable': str(executable), 'executableSha256': sha(executable.read_bytes()), 'profile': str(profile)}
    for phase, flag, marker, budget in PHASES:
        result = run_phase(executable, directory, environment, phase, flag, marker, budget)
        report = directory / 'mouse-645-ui.json'
        if phase == 'write':
            saved = directory / 'mouse-645-ui-write.json'
            saved.write_bytes(report.read_bytes())
            report = saved
        result.update(report=report.name, reportSha256=sha(report.read_bytes()))
        receipts[phase] = result
    receipts['reportSha256'] = sha((directory / 'mouse-645-ui.json').read_bytes())
    (directory / 'mouse-645-processes.json').write_text(json.dumps(receipts, indent=2) + '\n', encoding='utf-8')
    return finalize(directory)


def finalize(directory):
    directory = Path(directory).resolve()
    artifacts = {}
    def read(name):
        need(isinstance(name, str) and Path(name).name == name and '..' not in name, 'unsafe evidence path')
        filename = directory / name
        need(filename.is_file() and not filename.is_symlink(), 'missing or linked evidence file')
        raw = filename.read_bytes()
        receipt = {'file': name, 'bytes': len(raw), 'sha256': sha(raw)}
        need(name not in artifacts or artifacts[name] == receipt, 'evidence changed during verification')
        artifacts[name] = receipt
        return raw
    result = verify(read)
    result['artifacts'] = [artifacts[name] for name in sorted(artifacts)]
    (directory / 'mouse-645-acceptance.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('MOUSE_645_UI_ACCEPTANCE_PASS', flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--profile', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.verify_only:
        finalize(args.output)
    else:
        if args.executable is None or args.profile is None:
            parser.error('--executable and --profile are required for installed-app execution')
        run(args.executable, args.output, args.profile)
