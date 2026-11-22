#!/usr/bin/env python3
"""Run one immutable installed 631 workload for a nonpublishing CDP diagnosis.

The original parent350s/stress200s and original run_logged400s remain in force.
Only the exact CI stress module receives an observation adapter. No release gate
or publisher command is called by this launcher.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import secrets
import socket
import subprocess
import sys
import threading
import time

SOURCE = '0021084ccb9537e657d21e6f0c8e812dee6b461f'
VERIFIER_SHA = '2f662f0de5d81a8013f77ef9cf24262eb50e96df2cfdd59eeb02691fddb22dc7'
SNAPSHOT_TOOL_SHA = '767217ed097c52703f8f8015fa1bf26e43c727447e05c74cfcbc43aaafcc255d'
NATIVE_VALIDATOR_SHA = '5d1d700f1d8ef19663d2e7fe15c21ee40967aee12f598910ca6192eddaeeb7a8'
FUNCTION_SHAS = {'sample_native_exit': 'a368760a8189b1f13b8fd8bec2e4c020501f37153917dfd7ec13e85b8b81f0a1',
                'run_logged': 'aa0e5b101922ca42b0374635b07569328f35cb0add5921e24da5b7e6f73fc052'}
FLAG = '--mouse-631-smoke'
PREFIX = 'mouse-637-performance-trace-'
MARKERS = ['MOUSE_631_TASK_ONLY_NATIVE_PASS', 'MOUSE_631_FIFTY_TABS_FIVE_DESKTOPS_NATIVE_PASS',
           'MOUSE_631_INSTALLED_TASK_STRESS_PASS', 'MOUSE_632_STATIONARY_MEDIA_PASS']


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(file):
    digest = hashlib.sha256()
    with Path(file).open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(data)
    return digest.hexdigest()


def write_new(file, value):
    with Path(file).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def save_summary(output, summary, original_error=None):
    """Best-effort metadata must never replace an existing native exception."""
    error = original_error
    try:
        summary['evidence'] = {file.name: {'size': file.stat().st_size, 'sha256': sha(file)}
                               for file in sorted(output.iterdir()) if file.is_file() and file.name != PREFIX + 'summary.json'}
    except BaseException as cause:
        summary['ok'] = False
        summary['metadataError'] = type(cause).__name__ + ': ' + str(cause)
        error = error or cause
    try:
        write_new(output / (PREFIX + 'summary.json'), summary)
    except BaseException as cause:
        summary['ok'] = False
        error = error or cause
        try:
            print('MOUSE_637_DIAGNOSTIC_SUMMARY_SAVE_FAILED ' + type(cause).__name__ + ': ' + str(cause), file=sys.stderr, flush=True)
        except BaseException:
            pass
    return error


def original_functions(verifier):
    """Compile the exact two existing definitions, without executing its phases."""
    need(sha(verifier) == VERIFIER_SHA, 'Fetched source002 verifier differs')
    tree = ast.parse(Path(verifier).read_text(encoding='utf-8'))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in FUNCTION_SHAS]
    need([node.name for node in functions] == ['sample_native_exit', 'run_logged'], 'Original function inventory differs')
    for node in functions:
        need(hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest() == FUNCTION_SHAS[node.name],
             'Original deadline function AST differs: ' + node.name)
    namespace = {'subprocess': subprocess, 'time': time, 'sys': sys}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(verifier), 'exec'), namespace)
    return namespace


class StressLaunch:
    def __init__(self, executable, output, profile, controller, publisher_sha, popen=None):
        self.executable, self.output, self.profile = Path(executable), Path(output), Path(profile)
        self.controller, self.publisher_sha = Path(controller), publisher_sha
        self.original = popen or subprocess.Popen
        self.records, self.children, self.threads, self.errors = [], [], [], []
        self.abort = threading.Event()

    def __call__(self, args, *positional, **kwargs):
        argv = [str(x) for x in args] if isinstance(args, (list, tuple)) else []
        if FLAG not in argv:
            return self.original(args, *positional, **kwargs)
        need(not positional and argv == [str(self.executable), FLAG] and not self.records, 'One exact original stress launch required')
        environment = kwargs.get('env', {})
        need(environment.get('CI') == 'true' and environment.get('MOUSE_TEST_PROFILE') == str(self.profile), 'Stress CI/profile differs')
        need(kwargs.get('shell', False) is False, 'Stress launch must not use shell')
        need(Path(kwargs['stdout'].name).name == 'mouse-631-native.log', 'Original native log filename differs')
        need('MOUSE_637_PERFORMANCE_TRACE_NONCE' not in environment, 'Unexpected inherited trace nonce')
        with socket.socket() as reserved:
            reserved.bind(('127.0.0.1', 0))
            port = reserved.getsockname()[1]
        nonce = secrets.token_hex(32)
        inspected = [argv[0], '--inspect-brk=127.0.0.1:' + str(port), FLAG]
        child = self.original(inspected, **{**kwargs, 'env': {**environment, 'MOUSE_637_PERFORMANCE_TRACE_NONCE': nonce}})
        started = time.monotonic()
        row = {'phase': 'performance-trace', 'flag': FLAG, 'pid': child.pid, 'nonce': nonce, 'port': port,
               'originalArgv': argv, 'argv': inspected, 'profile': str(self.profile),
               'addedEnvironment': {'MOUSE_637_PERFORMANCE_TRACE_NONCE': nonce},
               'bootstrapStartedAt': round(time.time() * 1000), 'controllerExitCode': None}
        self.records.append(row)
        self.children.append(child)
        thread = threading.Thread(target=self._control, args=(child, row, started), daemon=True)
        self.threads.append(thread)
        thread.start()
        # Return the actual Electron Popen immediately. The unchanged original
        # run_logged starts its400s clock without waiting for the sidecar.
        return child

    def _control(self, child, row, started):
        controller = None
        try:
            config = self.output / (PREFIX + 'config.json')
            data = {'schema': 1, 'phase': row['phase'], 'flag': FLAG, 'pid': child.pid,
                    'nonce': row['nonce'], 'port': row['port'], 'publisherSHA': self.publisher_sha,
                    'executable': str(self.executable),
                    'appPath': str(self.executable.parent.parent / 'Resources/app.asar'),
                    'profile': str(self.profile), 'output': str(self.output),
                    'deadlineEpochMs': row['bootstrapStartedAt'] + 30000}
            for key, suffix in [('receipt', 'bootstrap'), ('moduleReceipt', 'module'),
                                ('controllerReceipt', 'controller'), ('listenerReceipt', 'listener')]:
                data[key] = str(self.output / (PREFIX + suffix + '.json'))
            write_new(config, data)
            clean = {key: value for key, value in os.environ.items()
                     if key not in ('GH_TOKEN', 'GITHUB_TOKEN', 'NODE_OPTIONS', 'ELECTRON_RUN_AS_NODE')}
            clean['CI'] = 'true'
            with (self.output / (PREFIX + 'controller.log')).open('xb') as stream:
                controller = self.original(['node', str(self.controller), 'control', str(config)], env=clean,
                                           stdout=stream, stderr=subprocess.STDOUT)
                row['controllerPid'] = controller.pid
                while controller.poll() is None:
                    remaining = 30 - (time.monotonic() - started)
                    if self.abort.is_set() or remaining <= 0 or child.poll() is not None:
                        raise RuntimeError('Owned diagnostic bootstrap cancelled, expired, or Electron exited')
                    try:
                        controller.wait(timeout=min(.1, remaining))
                    except subprocess.TimeoutExpired:
                        pass
                row['controllerExitCode'] = controller.returncode
                need(controller.returncode == 0, 'Owned trace controller failed')
            receipt = json.loads(Path(data['receipt']).read_text(encoding='utf-8'))
            need(receipt.get('pid') == child.pid and receipt.get('nonce') == row['nonce']
                 and receipt.get('controllerPid') == controller.pid and receipt.get('inspectorClosed') is True
                 and receipt.get('parentBytesDelegated') is True and receipt.get('receiptBeforeParentInvocation') is True,
                 'Original parent bootstrap receipt differs')
            row['receiptSha256'] = sha(data['receipt'])
            row['controllerReceiptSha256'] = sha(data['controllerReceipt'])
            row['bootstrapFinishedAt'] = round(time.time() * 1000)
        except BaseException as error:
            self.errors.append(type(error).__name__ + ': ' + str(error))
            row['error'] = self.errors[-1]
            if child.poll() is None:
                child.kill()
        finally:
            if controller is not None and controller.poll() is None:
                controller.kill()
                controller.wait(timeout=2)

    def finish(self, failed=False):
        if failed:
            self.abort.set()
            for child in self.children:
                if child.poll() is None:
                    child.kill()
        for thread in self.threads:
            thread.join(timeout=2)
        need(not any(thread.is_alive() for thread in self.threads), 'Diagnostic sidecar cleanup incomplete')
        for row, child in zip(self.records, self.children):
            row['processExitCode'] = child.returncode
        if not failed:
            need(not self.errors and len(self.records) == 1, 'One completed diagnostic bootstrap required')


def package_snapshot(candidate, pin):
    result = {}
    need(pin.get('source') == SOURCE and pin.get('version') == '6.0.37', 'Diagnostic pin is not immutable source002')
    expected = ['Mouse-Browser-6.0.37-mac-arm64.dmg', 'Mouse-Browser-6.0.37-mac-arm64.zip']
    need(sorted(pin['packages']) == expected, 'Pinned Mac package inventory differs')
    for name in expected:
        file = candidate / name
        need(file.is_file() and not file.is_symlink(), 'Pinned diagnostic package missing')
        value = {'size': file.stat().st_size, 'sha256': sha(file)}
        need(value == pin['packages'][name], 'Actual package differs from the immutable pin')
        result[name] = value
    return result


def run(executable):
    need(sys.platform == 'darwin' and os.environ.get('CI') == 'true', 'Diagnostic restricted to native Mac CI')
    executable = Path(executable).resolve(strict=True)
    need(executable.name == 'Mouse Browser' and executable.parent.name == 'MacOS', 'Expected installed executable')
    output = Path.cwd().resolve()
    need(output.name == 'mouse637-performance-diagnostic', 'Dedicated nonpublishing output directory required')
    candidate = output.parent / 'mouse637-release'
    tools = Path(__file__).parent.resolve()
    publisher_sha = os.environ.get('GITHUB_SHA', '')
    need(re.fullmatch('[0-9a-f]{40}', publisher_sha), 'Exact diagnostic commit SHA required')
    need(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=tools.parent, text=True).strip() == publisher_sha,
         'Diagnostic checkout differs from workflow SHA')
    snapshot_tool = tools / 'mouse637-feature-readiness.py'
    need(sha(snapshot_tool) == SNAPSHOT_TOOL_SHA, 'Immutable installed-byte snapshot helper changed')
    snapshot = runpy.run_path(str(snapshot_tool))['snapshot']
    pin_file = tools.parent / 'staging/mouse/6.0.37-arm64/pin.json'
    pin = json.loads(pin_file.read_text(encoding='utf-8'))
    verifier = candidate / 'mouse-verify.py'
    original = original_functions(verifier)
    profile = Path(os.environ['RUNNER_TEMP']).resolve() / 'mouse-profiles/task-stress-631'
    need(not profile.exists(), 'The original diagnostic profile must be fresh')
    need(not (output / 'mouse-631-native.log').exists(), 'Prior diagnostic output may not be reused')
    controller = tools / 'mouse637-performance-trace.cjs'
    launch = StressLaunch(executable, output, profile, controller, publisher_sha)
    app = executable.parent.parent.parent
    summary = {'schema': 1, 'kind': 'mouse637-nonpublishing-performance-summary', 'diagnosticOnly': True,
               'releaseAcceptance': False, 'source': SOURCE, 'publisherSHA': publisher_sha, 'version': '6.0.37',
               'platform': 'darwin', 'arch': 'arm64', 'ok': False, 'startedAt': round(time.time() * 1000),
               'executable': str(executable), 'appPath': str(app / 'Contents/Resources/app.asar'),
               'profile': str(profile), 'output': str(output), 'candidate': str(candidate),
               'wrapperSha256': sha(__file__), 'controllerSha256': sha(controller),
               'snapshotToolSha256': sha(snapshot_tool), 'verifierSha256': sha(verifier),
               'originalFunctionASTs': FUNCTION_SHAS, 'pinSha256': sha(pin_file),
               'budgetsMs': {'outer': 400000, 'native': 350000, 'stress': 200000, 'bootstrap': 30000}}
    previous = subprocess.Popen
    error = None
    try:
        summary['packagesBefore'] = package_snapshot(candidate, pin)
        summary['installedBefore'] = snapshot(app, output, 'trace-before')
        environment = {key: value for key, value in os.environ.items()
                       if key not in ('GH_TOKEN', 'GITHUB_TOKEN', 'NODE_OPTIONS', 'ELECTRON_RUN_AS_NODE')}
        environment.update(CI='true', MOUSE_TEST_PROFILE=str(profile))
        subprocess.Popen = launch
        result, log = original['run_logged']([str(executable), FLAG], environment, output / 'mouse-631-native.log', 400)
        subprocess.Popen = previous
        summary['native'] = {'pid': result.pid, 'exitCode': result.returncode, 'elapsedMs': result.elapsedMs,
                             'log': 'mouse-631-native.log', 'logSha256': sha(output / 'mouse-631-native.log'),
                             'requiredMarkers': MARKERS}
        need(result.returncode == 0 and all(marker in log.splitlines() for marker in MARKERS), 'Original installed workload failed')
        launch.finish()
        # This unchanged631 reader validates only its own native workload. It is
        # not the637 comparison, source=False publisher, update or release gate.
        validator = candidate / 'mouse-631-acceptance.py'
        summary['nativeValidatorSha256'] = sha(validator)
        need(summary['nativeValidatorSha256'] == NATIVE_VALIDATOR_SHA, 'Fetched original631 evidence reader changed')
        with (output / (PREFIX + 'native-validation.log')).open('xb') as stream:
            checked = subprocess.run([sys.executable, str(validator), '--directory', str(output), '--platform', 'darwin', '--arch', 'arm64'],
                                     stdout=stream, stderr=subprocess.STDOUT, timeout=60, check=False)
        summary['nativeValidatorExitCode'] = checked.returncode
        need(checked.returncode == 0, 'Original631 native evidence reader failed')
        summary['ok'] = True
    except BaseException as cause:
        error = cause
        summary['error'] = type(cause).__name__ + ': ' + str(cause)
    finally:
        subprocess.Popen = previous
        try:
            launch.finish(failed=error is not None)
            summary['installedAfter'] = snapshot(app, output, 'trace-after')
            summary['packagesAfter'] = package_snapshot(candidate, pin)
            need(summary.get('installedBefore', {}).get('components') == summary['installedAfter']['components'], 'Installed bytes changed')
            need(summary.get('packagesBefore') == summary['packagesAfter'], 'Package bytes changed')
            need(sha(verifier) == VERIFIER_SHA and sha(snapshot_tool) == SNAPSHOT_TOOL_SHA, 'Frozen external helper changed')
        except BaseException as cleanup_error:
            summary['ok'] = False
            summary['cleanupError'] = type(cleanup_error).__name__ + ': ' + str(cleanup_error)
            error = error or cleanup_error
        summary['launches'] = launch.records
        summary['finishedAt'] = round(time.time() * 1000)
        error = save_summary(output, summary, error)
    if error is not None:
        raise error
    checker = runpy.run_path(str(tools / 'mouse637-performance-trace-evidence.py'))
    checker['verify'](output)
    print('MOUSE_637_DIAGNOSTIC_TRACE_COLLECTED_NOT_RELEASE_ACCEPTANCE', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable')
    run(parser.parse_args().executable)
