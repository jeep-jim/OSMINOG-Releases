#!/usr/bin/env python3
"""Observe one original retained Mac CI process, then retain all original gates.

The existing feature-readiness wrapper and exact source002 verifier are executed
unchanged. This outer layer only prepares the retained636 diagnostic observer.
"""
import argparse
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
INNER_SHA = '767217ed097c52703f8f8015fa1bf26e43c727447e05c74cfcbc43aaafcc255d'
FLAG = '--mouse-636-retained-smoke'
PREFIX = 'mouse-637-guest-input-observer-'


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def write_new(file, value):
    with Path(file).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


class RetainedLaunch:
    def __init__(self, executable, output, profile, controller, publisher_sha, popen=None):
        self.executable, self.output, self.profile = Path(executable), Path(output), Path(profile)
        self.controller, self.publisher_sha = Path(controller), publisher_sha
        self.original = popen or subprocess.Popen
        self.records, self.threads, self.children, self.errors = [], [], [], []
        self.abort = threading.Event()

    def __call__(self, args, *positional, **kwargs):
        argv = [str(x) for x in args] if isinstance(args, (list, tuple)) else []
        if FLAG not in argv:
            return self.original(args, *positional, **kwargs)
        need(not positional and argv == [str(self.executable), FLAG] and not self.records,
             'Only one exact original retained launch is allowed')
        env = kwargs.get('env', {})
        need(env.get('CI') == 'true' and env.get('MOUSE_TEST_PROFILE') == str(self.profile), 'Retained profile/CI differs')
        need(kwargs.get('shell', False) is False, 'Retained launch must not use a shell')
        need(Path(kwargs['stdout'].name).name == 'mouse-636-retained-owner-feedback.log', 'Retained native log differs')
        need('MOUSE_637_GUEST_INPUT_NONCE' not in env, 'Unexpected inherited observer nonce')
        with socket.socket() as reserved:
            reserved.bind(('127.0.0.1', 0))
            port = reserved.getsockname()[1]
        nonce = secrets.token_hex(32)
        inspected = [argv[0], '--inspect-brk=127.0.0.1:' + str(port), FLAG]
        process = self.original(inspected, **{**kwargs, 'env': {**env, 'MOUSE_637_GUEST_INPUT_NONCE': nonce}})
        started = time.monotonic()
        row = {'phase': 'retained', 'flag': FLAG, 'pid': process.pid, 'nonce': nonce, 'port': port,
               'argv': inspected, 'originalArgv': argv, 'profile': str(self.profile),
               'addedEnvironment': {'MOUSE_637_GUEST_INPUT_NONCE': nonce},
               'bootstrapStartedAt': round(time.time() * 1000), 'controllerExitCode': None}
        self.records.append(row)
        self.children.append(process)
        thread = threading.Thread(target=self._control, args=(process, row, started), daemon=True)
        self.threads.append(thread)
        thread.start()
        # Return the actual Electron Popen immediately. No bootstrap handshake or
        # file I/O is synchronously awaited before original run_logged starts.
        return process

    def _control(self, process, row, started):
        controller = None
        try:
            receipt = self.output / (PREFIX + 'bootstrap.json')
            control_receipt = self.output / (PREFIX + 'controller.json')
            listener_receipt = self.output / (PREFIX + 'listener.json')
            config = self.output / (PREFIX + 'config.json')
            controller_log = self.output / (PREFIX + 'controller.log')
            data = {'schema': 1, 'phase': 'retained', 'flag': FLAG, 'pid': process.pid,
                    'nonce': row['nonce'], 'port': row['port'], 'publisherSHA': self.publisher_sha,
                    'executable': str(self.executable),
                    'appPath': str(self.executable.parent.parent / 'Resources/app.asar'),
                    'profile': str(self.profile), 'output': str(self.output), 'receipt': str(receipt),
                    'controllerReceipt': str(control_receipt), 'listenerReceipt': str(listener_receipt),
                    'deadlineEpochMs': row['bootstrapStartedAt'] + 30000}
            write_new(config, data)
            clean = {key: value for key, value in os.environ.items()
                     if key not in ('GH_TOKEN', 'GITHUB_TOKEN', 'NODE_OPTIONS', 'ELECTRON_RUN_AS_NODE')}
            clean['CI'] = 'true'
            with controller_log.open('xb') as log:
                controller = self.original(['node', str(self.controller), 'control', str(config)], env=clean,
                                           stdout=log, stderr=subprocess.STDOUT)
                row['controllerPid'] = controller.pid
                while controller.poll() is None:
                    remaining = 30 - (time.monotonic() - started)
                    if self.abort.is_set() or remaining <= 0 or process.poll() is not None:
                        raise RuntimeError('Owned retained observer cancelled, expired, or Electron exited')
                    try:
                        controller.wait(timeout=min(.1, remaining))
                    except subprocess.TimeoutExpired:
                        pass
                row['controllerExitCode'] = controller.returncode
                need(controller.returncode == 0, 'Owned retained Inspector controller failed')
            row.update(controllerLog=controller_log.name, controllerLogSha256=sha(controller_log),
                       receipt=receipt.name, receiptSha256=sha(receipt), controllerReceipt=control_receipt.name,
                       controllerReceiptSha256=sha(control_receipt), config=config.name, configSha256=sha(config),
                       listenerReceipt=listener_receipt.name, listenerReceiptSha256=sha(listener_receipt),
                       bootstrapElapsedMs=round((time.monotonic() - started) * 1000))
            actual = json.loads(receipt.read_text())
            need(actual['pid'] == process.pid and actual['nonce'] == row['nonce'] and
                 actual['controllerPid'] == controller.pid and actual['publisherSHA'] == self.publisher_sha,
                 'Retained observer receipt identity differs')
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
            for child in self.children:
                if child.poll() is None:
                    child.kill()
        for thread in self.threads:
            thread.join(timeout=2)
        need(not any(thread.is_alive() for thread in self.threads), 'Retained observer cleanup incomplete')
        for row, child in zip(self.records, self.children):
            row['processExitCode'] = child.returncode
        if not failed:
            need(not self.errors and len(self.records) == 1, 'Retained observer was not completed exactly once')


def run(executable):
    need(sys.platform == 'darwin' and os.environ.get('CI') == 'true', 'Observer restricted to Mac CI')
    executable = Path(executable).resolve(strict=True)
    need(executable.name == 'Mouse Browser' and executable.parent.name == 'MacOS', 'Expected installed executable')
    output = Path.cwd().resolve()
    tools = Path(__file__).parent.resolve()
    inner = tools / 'mouse637-feature-readiness.py'
    need(sha(inner) == INNER_SHA, 'Existing feature-readiness wrapper changed')
    publisher_sha = os.environ.get('GITHUB_SHA', '')
    need(re.fullmatch('[0-9a-f]{40}', publisher_sha), 'Exact publisher SHA required')
    need(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=tools.parent, text=True).strip() == publisher_sha,
         'Publisher checkout differs from workflow SHA')
    profile = Path(os.environ['RUNNER_TEMP']).resolve() / 'mouse-profiles' / 'retained636'
    need(not profile.exists(), 'Original retained profile must be fresh')
    controller = tools / 'mouse637-guest-input-observer.cjs'
    launches = RetainedLaunch(executable, output, profile, controller, publisher_sha)
    summary = {'schema': 1, 'kind': 'mouse637-passive-guest-input-summary', 'source': SOURCE, 'version': '6.0.37',
               'publisherSHA': publisher_sha, 'platform': 'darwin', 'arch': 'arm64', 'ok': False,
               'executable': str(executable), 'appPath': str(executable.parent.parent / 'Resources/app.asar'),
               'profile': str(profile), 'output': str(output), 'wrapperSha256': sha(__file__),
               'controllerSha256': sha(controller), 'innerWrapperSha256': sha(inner), 'startedAt': round(time.time() * 1000)}
    previous_popen, previous_argv = subprocess.Popen, sys.argv
    error = None
    try:
        subprocess.Popen = launches
        sys.argv = [str(inner), str(executable)]
        runpy.run_path(str(inner), run_name='__main__')
        launches.finish()
        summary['ok'] = True
    except BaseException as cause:
        error = cause
        summary['error'] = type(cause).__name__ + ': ' + str(cause)
    finally:
        subprocess.Popen, sys.argv = previous_popen, previous_argv
        try:
            launches.finish(failed=error is not None)
            need(sha(inner) == INNER_SHA, 'Existing feature-readiness wrapper modified')
            bound = {}
            for name in ['mouse-637-feature-readiness-summary.json', 'mouse-636-retained-owner-feedback.json',
                         'mouse-636-retained-owner-feedback.log']:
                file = output / name
                if file.exists():
                    bound[name] = {'size': file.stat().st_size, 'sha256': sha(file)}
            summary['evidence'] = bound
        except BaseException as cleanup_error:
            summary['ok'] = False
            summary['cleanupError'] = type(cleanup_error).__name__ + ': ' + str(cleanup_error)
            if error is None:
                error = cleanup_error
        summary['launches'] = launches.records
        summary['finishedAt'] = round(time.time() * 1000)
        write_new(output / (PREFIX + 'summary.json'), summary)
    if error is not None:
        raise error
    checker = runpy.run_path(str(tools / 'mouse637-guest-input-observer-evidence.py'))
    checker['verify'](output)
    print('MOUSE_637_PASSIVE_GUEST_INPUT_OBSERVER_PASS', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable')
    run(parser.parse_args().executable)
