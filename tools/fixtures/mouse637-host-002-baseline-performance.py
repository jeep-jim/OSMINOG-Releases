#!/usr/bin/env python3
"""Measure the exact published predecessor in an isolated native CI process.

The original installed --mouse-631-smoke workload runs unchanged. Its raw
reports and OS frames remain separate from the candidate's later workload.
No historical timing receipt is accepted as a same-run measurement.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time


def load_upgrade():
    spec = importlib.util.spec_from_file_location('mouse637_baseline_upgrade', Path(__file__).with_name('mouse-637-upgrade.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


U = load_upgrade()
FOLDER = 'mouse-637-baseline-performance'
NAME = FOLDER + '.json'
MARKERS = ['MOUSE_631_TASK_ONLY_NATIVE_PASS', 'MOUSE_631_FIFTY_TABS_FIVE_DESKTOPS_NATIVE_PASS',
           'MOUSE_631_INSTALLED_TASK_STRESS_PASS', 'MOUSE_632_STATIONARY_MEDIA_PASS']
REPORTS = ['mouse-631-native.json', 'mouse-631-task.json', 'mouse-631-stress.json', 'mouse-632-media.json']
PUBLISHED_SOURCES = {'darwin': '7c09b6cb9885ce72be41e8f16a35d4c55c9ecde3',
                     'win32': '7c09b6cb9885ce72be41e8f16a35d4c55c9ecde3',
                     'linux': '7c09b6cb9885ce72be41e8f16a35d4c55c9ecde3'}


def utc():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def validate_process(output, receipt, old_version, target_platform):
    U.require(receipt.get('exitCode') == 0 and type(receipt.get('pid')) is int and receipt['pid'] > 0,
              'Published baseline native process did not exit successfully')
    U.require(type(receipt.get('elapsedMs')) in (int, float) and 0 < receipt['elapsedMs'] <= 400000,
              'Published baseline native process exceeded its fixed process deadline')
    log = output / 'mouse-631-native.log'
    U.require(log.is_file() and 0 < log.stat().st_size <= 16 * 1024**2, 'Published baseline native log is missing')
    lines = log.read_text(encoding='utf-8', errors='strict').splitlines()
    U.require(all(marker in lines for marker in MARKERS), 'Published baseline task/stress/media marker missing')
    reports = {}
    for name in REPORTS:
        path = output / name
        U.require(path.is_file() and not path.is_symlink() and 0 < path.stat().st_size <= 8 * 1024**2,
                  'Published baseline raw report missing: ' + name)
        value = json.loads(path.read_bytes())
        U.require(value.get('ok') is True and value.get('version') == old_version
                  and value.get('platform') == target_platform and value.get('arch') == ('arm64' if target_platform == 'darwin' else 'x64'),
                  'Published baseline report has another native identity: ' + name)
        U.require(not value.get('error') and not value.get('cleanupError'), 'Published baseline report contains an error')
        reports[name] = value
    native = reports['mouse-631-native.json']
    U.require(native.get('pid') == receipt['pid'] and native.get('budgetMs') == 350000,
              'Published baseline process/report PID or native budget differs')
    U.require([row.get('name') for row in native.get('stages', [])] == ['taskOnly', 'fiftyTabs', 'stationaryMedia']
              and all(row.get('ok') is True for row in native['stages']), 'Published baseline did not run the unchanged installed workload')
    stress = reports['mouse-631-stress.json']
    U.require(stress.get('restored') is True and [row.get('ownedPageCount') for row in stress.get('stages', [])] == [20, 50],
              'Published baseline did not preserve both actual stress workloads')
    return reports


def inventory(output):
    rows = {}
    for path in sorted(output.iterdir()):
        U.require(path.is_file() and not path.is_symlink(), 'Baseline evidence contains a non-file or symlink')
        U.require(path.name.startswith(('mouse-631-', 'mouse-632-')) and path.suffix in ('.json', '.png', '.log'),
                  'Unexpected baseline evidence file')
        U.require(0 < path.stat().st_size <= 64 * 1024**2, 'Baseline evidence file is empty or oversized')
        rows[FOLDER + '/' + path.name] = {'size': path.stat().st_size, 'sha256': U.sha256(path)}
    U.require(all(FOLDER + '/' + name in rows for name in REPORTS), 'Baseline evidence inventory is incomplete')
    return rows


def measure(executable, profile, output, env):
    log = output / 'mouse-631-native.log'
    started_at, started = utc(), time.monotonic()
    process = {'argv': [str(executable), '--mouse-631-smoke'], 'startedAt': started_at, 'pid': None,
               'exitCode': None, 'elapsedMs': None, 'budgetMs': 400000, 'requiredMarkers': MARKERS,
               'profile': str(profile), 'cwd': str(output), 'log': FOLDER + '/' + log.name}
    with log.open('w', encoding='utf-8') as stream:
        child = subprocess.Popen(process['argv'], cwd=output, env=env, stdout=stream, stderr=subprocess.STDOUT)
        process['pid'] = child.pid
        try:
            process['exitCode'] = child.wait(timeout=400)
        except subprocess.TimeoutExpired:
            process['timedOut'] = True
            child.kill()
            process['exitCode'] = child.wait(timeout=10)
            raise
        finally:
            process['elapsedMs'] = (time.monotonic() - started) * 1000
            process['finishedAt'] = utc()
            stream.flush()
            process['logSha256'] = U.sha256(log)
            write(output.parent / 'mouse-637-baseline-process.json', process)
    print(log.read_text(encoding='utf-8', errors='replace'), flush=True)
    return process


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    U.require(sys.platform in U.BASELINES and os.environ.get('CI') == 'true', 'An actual native CI runner is required')
    if sys.platform == 'linux':
        U.require(os.getuid() > 0 and platform.machine() == 'x86_64' and os.environ.get('DISPLAY'),
                  'Baseline Linux needs the owned unprivileged X11 desktop')
    output = args.output.resolve()
    raw_output = output / FOLDER
    U.require(not raw_output.exists(), 'Refusing to reuse prior baseline measurements')
    output.mkdir(parents=True, exist_ok=True)
    raw_output.mkdir()
    old_version = U.OLD_VERSIONS[sys.platform]
    baseline = U.BASELINES[sys.platform]['deb'] if sys.platform == 'linux' else U.BASELINES[sys.platform]
    facts = {'schema': 1, 'kind': 'published-baseline-stress-run', 'version': '6.0.37', 'ok': False,
             'platform': sys.platform, 'arch': 'arm64' if sys.platform == 'darwin' else 'x64',
             'baselineVersion': old_version, 'baselineSource': PUBLISHED_SOURCES[sys.platform],
             'baseline': {**baseline, 'url': U.baseline_url(baseline)}, 'rawDirectory': FOLDER,
             'source': 'Verified published package and unchanged installed --mouse-631-smoke process',
             'physicalUserDeviceVerified': False, 'startedAt': utc(),
             'runner': {'runId': os.environ.get('GITHUB_RUN_ID'), 'runAttempt': os.environ.get('GITHUB_RUN_ATTEMPT'),
                        'job': os.environ.get('GITHUB_JOB'), 'workflow': os.environ.get('GITHUB_WORKFLOW'),
                        'sha': os.environ.get('GITHUB_SHA'), 'host': platform.node(), 'system': platform.system(),
                        'machine': platform.machine(), 'display': os.environ.get('DISPLAY')}}
    try:
        with tempfile.TemporaryDirectory(prefix='mouse637-baseline-', dir=os.environ.get('RUNNER_TEMP')) as temporary:
            root = Path(temporary)
            package = U.download_baseline(baseline, root)
            profile = root / 'Isolated previous-version performance profile'
            env = {**os.environ, 'CI': 'true', 'MOUSE_TEST_PROFILE': str(profile), 'GDK_SCALE': '1', 'GDK_DPI_SCALE': '1'}
            for key in ('ELECTRON_RUN_AS_NODE', 'APPIMAGE', 'APPDIR', 'GH_TOKEN', 'GITHUB_TOKEN'):
                env.pop(key, None)
            target = root / 'Installed previous Mouse'
            if sys.platform == 'darwin':
                executable = U.mac_install(package, target / 'Mouse Browser.app', root, old_version, 'baseline')
            elif sys.platform == 'win32':
                installer = U.sibling('mouse-windows-verify.py')
                facts['installation'] = installer.install(package, target, env, output / 'mouse-637-baseline-install.log')
                executable = target / 'Mouse Browser.exe'
            else:
                installer = U.sibling('mouse-linux-verify.py')
                facts['installation'] = installer.install_deb(package, output, 'mouse-637-baseline-install.log', expected_version=old_version)
                executable = installer.installed_executable()
            U.require(executable.is_file() and not executable.is_symlink(), 'Installed baseline executable is missing')
            facts['executable'] = {'path': str(executable), 'size': executable.stat().st_size, 'sha256': U.sha256(executable)}
            facts['process'] = measure(executable, profile, raw_output, env)
            validate_process(raw_output, facts['process'], old_version, sys.platform)
            facts['files'] = inventory(raw_output)
            facts['ok'] = True
    except Exception as error:
        facts['error'] = {'type': type(error).__name__, 'message': str(error)}
        raise
    finally:
        facts['finishedAt'] = utc()
        write(output / NAME, facts)
    print('MOUSE_637_BASELINE_PERFORMANCE_PASS', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
