#!/usr/bin/env python3
"""Run exact source verification with a bounded external CI fixture adapter.

Only the two feature Electron launches are intercepted. The original verifier,
actual Popen object/PID, all deadlines, product bytes and validators are retained.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import re
import secrets
import socket
import subprocess
import sys
import threading
import time

SOURCE = '0021084ccb9537e657d21e6f0c8e812dee6b461f'
VERIFIER_SHA = '2f662f0de5d81a8013f77ef9cf24262eb50e96df2cfdd59eeb02691fddb22dc7'
ASAR_SHA = '62b5472c62e475b28935b110330a602311fa8227b79666f375269fcdc8eb260e'
FLAGS = {'write': '--mouse-637-features-smoke', 'read': '--mouse-637-features-restore-read'}
COMPONENTS = ('Contents/MacOS/Mouse Browser', 'Contents/Resources/app.asar',
              'Contents/Resources/app.asar.unpacked/mouse-native-menu.node',
              'Contents/Resources/app.asar.unpacked/mouse-screen-capture.node')
NAME = 'mouse-637-feature-readiness-summary.json'


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as target:
        json.dump(value, target, ensure_ascii=False, indent=2, allow_nan=False)
        target.write('\n')


def snapshot(app, output, label):
    inventory = sorted(str(file.relative_to(app)) for file in (app / 'Contents/Resources/app.asar.unpacked').rglob('*.node'))
    need(inventory == sorted(COMPONENTS[2:]), 'Unexpected installed native addon inventory')
    components = {}
    for name in COMPONENTS:
        file = app / name
        need(file.is_file() and not file.is_symlink(), 'Installed component is not an owned regular file: ' + name)
        components[name] = {'size': file.stat().st_size, 'sha256': sha(file)}
    need(components['Contents/Resources/app.asar']['sha256'] == ASAR_SHA, 'Installed ASAR differs from exact accepted package')
    log = output / ('mouse-637-feature-readiness-codesign-' + label + '.log')
    with log.open('xb') as target:
        result = subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(app)],
                                stdout=target, stderr=subprocess.STDOUT, timeout=30, check=False)
    need(result.returncode == 0, 'Installed application signature verification failed: ' + label)
    return {'components': components, 'nativeInventory': inventory, 'codesign': {'exitCode': result.returncode,
             'log': log.name, 'logSha256': sha(log), 'command': ['codesign', '--verify', '--deep', '--strict']}}


class FeatureLaunches:
    """Return the real Electron process immediately; setup runs in a sidecar."""
    def __init__(self, executable, output, profile, controller, popen=None):
        self.executable, self.output, self.profile = Path(executable), Path(output), Path(profile)
        self.controller = Path(controller)
        self.original = popen or subprocess.Popen
        self.records, self.threads, self.children, self.controllers, self.errors = [], [], [], [], []
        self.abort = threading.Event()

    def __call__(self, args, *positional, **kwargs):
        argv = [str(x) for x in args] if isinstance(args, (list, tuple)) else []
        selected = [phase for phase, flag in FLAGS.items() if flag in argv]
        if not selected:
            return self.original(args, *positional, **kwargs)
        need(len(selected) == 1 and not positional, 'Ambiguous feature launch')
        phase = selected[0]
        need(argv == [str(self.executable), FLAGS[phase]], 'Feature launch executable/arguments differ')
        need([row['phase'] for row in self.records] == ([] if phase == 'write' else ['write']), 'Duplicate or reordered feature launch')
        environment = kwargs.get('env', {})
        need(environment.get('CI') == 'true' and environment.get('MOUSE_TEST_PROFILE') == str(self.profile), 'Feature launch profile/CI differs')
        need(kwargs.get('shell', False) is False, 'Feature launch must not use a shell')
        need(Path(kwargs['stdout'].name).name == 'mouse-637-features-' + phase + '.log', 'Feature native log path differs')
        with socket.socket() as reserved:
            reserved.bind(('127.0.0.1', 0))
            port = reserved.getsockname()[1]
        nonce = secrets.token_hex(32)
        need('MOUSE_637_FEATURE_READINESS_NONCE' not in environment, 'Unexpected inherited readiness nonce')
        child_environment = {**environment, 'MOUSE_637_FEATURE_READINESS_NONCE': nonce}
        inspected = [argv[0], '--inspect-brk=127.0.0.1:' + str(port), argv[1]]
        process = self.original(inspected, **{**kwargs, 'env': child_environment})
        started = time.monotonic()
        row = {'phase': phase, 'flag': FLAGS[phase], 'pid': process.pid, 'nonce': nonce, 'port': port,
               'argv': inspected, 'originalArgv': argv, 'profile': str(self.profile),
               'addedEnvironment': {'MOUSE_637_FEATURE_READINESS_NONCE': nonce},
               'bootstrapStartedAt': round(time.time() * 1000), 'controllerExitCode': None}
        self.records.append(row)
        self.children.append(process)
        # No Inspector connection, file I/O or setup handshake is synchronously
        # awaited here. The sidecar may run concurrently before this return.
        # Original run_logged starts its own clock with the actual Popen object.
        thread = threading.Thread(target=self._control, args=(process, row, started), daemon=True)
        self.threads.append(thread)
        thread.start()
        return process

    def _control(self, process, row, started):
        controller = None
        try:
            phase = row['phase']
            receipt = self.output / ('mouse-637-feature-readiness-' + phase + '.json')
            control_receipt = self.output / ('mouse-637-feature-readiness-controller-' + phase + '.json')
            config = self.output / ('mouse-637-feature-readiness-config-' + phase + '.json')
            controller_log = self.output / ('mouse-637-feature-readiness-controller-' + phase + '.log')
            app_path = self.executable.parent.parent / 'Resources' / 'app.asar'
            data = {'schema': 1, 'phase': phase, 'flag': row['flag'], 'pid': process.pid, 'nonce': row['nonce'],
                    'port': row['port'], 'executable': str(self.executable), 'appPath': str(app_path),
                    'profile': str(self.profile), 'output': str(self.output), 'receipt': str(receipt),
                    'controllerReceipt': str(control_receipt), 'deadlineEpochMs': row['bootstrapStartedAt'] + 30000}
            write_new(config, data)
            clean = {key: value for key, value in os.environ.items()
                     if key not in ('GH_TOKEN', 'GITHUB_TOKEN', 'NODE_OPTIONS', 'ELECTRON_RUN_AS_NODE')}
            clean['CI'] = 'true'
            with controller_log.open('xb') as log:
                controller = self.original(['node', str(self.controller), 'control', str(config)], env=clean,
                                           stdout=log, stderr=subprocess.STDOUT)
                self.controllers.append(controller)
                row['controllerPid'] = controller.pid
                while controller.poll() is None:
                    remaining = 30 - (time.monotonic() - started)
                    if self.abort.is_set() or remaining <= 0 or process.poll() is not None:
                        raise RuntimeError('Owned feature bootstrap cancelled, expired, or Electron exited')
                    try:
                        controller.wait(timeout=min(.1, remaining))
                    except subprocess.TimeoutExpired:
                        pass
                row['controllerExitCode'] = controller.returncode
                need(controller.returncode == 0, 'Owned Inspector controller failed')
            row.update(controllerLog=controller_log.name, controllerLogSha256=sha(controller_log),
                       receipt=receipt.name, receiptSha256=sha(receipt), controllerReceipt=control_receipt.name,
                       controllerReceiptSha256=sha(control_receipt), config=config.name, configSha256=sha(config),
                       bootstrapElapsedMs=round((time.monotonic() - started) * 1000))
            observed = json.loads(receipt.read_text())
            need(observed['pid'] == process.pid and observed['nonce'] == row['nonce'] and
                 observed['phase'] == row['phase'] and observed['controllerPid'] == controller.pid,
                 'Owned feature bootstrap receipt identity differs')
        except BaseException as error:
            row['bootstrapError'] = type(error).__name__ + ': ' + str(error)
            self.errors.append(row['bootstrapError'])
            if process.poll() is None:
                process.kill()
        finally:
            if controller is not None and controller.poll() is None:
                controller.kill()
                controller.wait(timeout=2)

    def finish(self, failed=False):
        if failed:
            self.abort.set()
            for process in self.children:
                if process.poll() is None:
                    process.kill()
        for thread in self.threads:
            thread.join(timeout=2)
        need(not any(thread.is_alive() for thread in self.threads), 'Feature controller cleanup did not finish')
        if not failed:
            need(not self.errors, 'Feature bootstrap failed: ' + '; '.join(self.errors))
            need([row['phase'] for row in self.records] == ['write', 'read'], 'Both actual feature phases are required')


def run(executable):
    need(sys.platform == 'darwin' and os.environ.get('CI') == 'true', 'Readiness adapter is restricted to Mac CI')
    executable = Path(executable).resolve(strict=True)
    need(executable.name == 'Mouse Browser' and executable.parent.name == 'MacOS', 'Expected installed Mouse executable')
    output = Path.cwd().resolve()
    verifier = output / 'mouse-verify.py'
    need(sha(verifier) == VERIFIER_SHA, 'Fetched original verifier differs from source002')
    profile = Path(os.environ['RUNNER_TEMP']).resolve() / 'mouse-profiles' / 'features637'
    need(not profile.exists(), 'Feature profile must be fresh before the original full verifier')
    app = executable.parents[2]
    controller = Path(__file__).with_suffix('.cjs').resolve()
    publisher = os.environ.get('GITHUB_SHA', '')
    need(re.fullmatch('[0-9a-f]{40}', publisher), 'Exact publisher SHA is required')
    need(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=Path(__file__).parent.parent, text=True).strip() == publisher,
         'Publisher checkout differs from the actual workflow SHA')
    summary = {'schema': 1, 'kind': 'mouse637-external-feature-readiness', 'source': SOURCE,
               'version': '6.0.37', 'platform': 'darwin', 'arch': 'arm64', 'ok': False, 'publisherSHA': publisher,
               'executable': str(executable), 'appPath': str(app / 'Contents/Resources/app.asar'),
               'profile': str(profile), 'output': str(output), 'verifierSha256': sha(verifier),
               'wrapperSha256': sha(__file__), 'controllerSha256': sha(controller), 'startedAt': round(time.time() * 1000)}
    summary['before'] = snapshot(app, output, 'before')
    launches = FeatureLaunches(executable, output, profile, controller)
    previous_popen, previous_argv = subprocess.Popen, sys.argv
    error = None
    try:
        subprocess.Popen = launches
        sys.argv = [str(verifier), str(executable)]
        runpy.run_path(str(verifier), run_name='__main__')
        launches.finish()
        summary['ok'] = True
    except BaseException as cause:
        error = cause
        summary['error'] = type(cause).__name__ + ': ' + str(cause)
    finally:
        subprocess.Popen, sys.argv = previous_popen, previous_argv
        try:
            launches.finish(failed=error is not None)
            summary['after'] = snapshot(app, output, 'after')
            need(summary['before']['components'] == summary['after']['components'], 'Installed bytes changed during external verification')
            need(sha(verifier) == VERIFIER_SHA, 'Original verifier was modified')
        except BaseException as final_error:
            summary['ok'] = False
            summary['cleanupError'] = type(final_error).__name__ + ': ' + str(final_error)
            if error is None:
                error = final_error
        summary['launches'] = launches.records
        summary['finishedAt'] = round(time.time() * 1000)
        write_new(output / NAME, summary)
    if error is not None:
        raise error
    checker = runpy.run_path(str(Path(__file__).with_name('mouse637-feature-readiness-evidence.py')))
    checker['verify'](output)
    print('MOUSE_637_EXTERNAL_FEATURE_READINESS_PASS', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable')
    options = parser.parse_args()
    run(options.executable)
