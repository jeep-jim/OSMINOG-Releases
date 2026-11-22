#!/usr/bin/env python3
"""Add external accounting to two unchanged original Mac performance launches."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import runpy
import secrets
import subprocess
import sys
import threading
import time

SOURCE = '0021084ccb9537e657d21e6f0c8e812dee6b461f'
INNER_SHA = '7fa48d60f514c82eb68a2d775dd06d1b34111a4f423e3b6c66cb81bac82fe517'
VERIFIER_SHA = '2f662f0de5d81a8013f77ef9cf24262eb50e96df2cfdd59eeb02691fddb22dc7'
BASELINE_SHA = '7603d348b4a125ecf73bad82e2cf24eb57d17b7b03dac02eb12527552c38eb6e'
PREFIX = 'mouse-637-host-observer-'
MAX_RAW_BYTES = 64 * 1024**2


def need(value, message):
    if not value:
        raise ValueError(message)


def binding(path):
    path = Path(path)
    need(path.is_file() and not path.is_symlink(), 'Expected regular evidence file: ' + str(path))
    data = path.read_bytes()
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


class ObservingLaunches:
    """The original Popen object and its constructor arguments are untouched."""
    def __init__(self, executable, output, sampler, publisher_sha, popen=None):
        self.executable, self.output, self.sampler = map(Path, (executable, output, sampler))
        self.publisher_sha = publisher_sha
        self.original = popen or subprocess.Popen
        self.records, self.threads, self.errors, self.processes = [], [], [], []
        self.abort = threading.Event()
        self.profile = Path(os.environ['RUNNER_TEMP']).resolve() / 'mouse-profiles' / 'task-stress-631'
        self.expected_roots = {'baseline': str(Path(sys.executable).resolve()),
                               'candidate': str(self.executable.resolve())}
        self.nonces = {phase: secrets.token_hex(32) for phase in ('baseline', 'candidate')}

    def __call__(self, args, *positional, **kwargs):
        argv = [str(x) for x in args] if isinstance(args, (list, tuple)) else []
        baseline = [sys.executable, str(self.output / 'mouse-637-baseline-performance.py'), '--output', str(self.output)]
        candidate = [str(self.executable), '--mouse-631-smoke']
        relevant = '--mouse-631-smoke' in argv or (len(argv) > 1 and Path(argv[1]).name == 'mouse-637-baseline-performance.py')
        if not relevant:
            return self.original(args, *positional, **kwargs)
        need(not positional and (argv == baseline or argv == candidate), 'Unexpected original performance launch')
        phase, budget, log = ('baseline', 900000, 'mouse-637-baseline-performance.log') if argv == baseline else ('candidate', 400000, 'mouse-631-native.log')
        need(phase not in [row['phase'] for row in self.records], 'Performance phase was launched more than once')
        need([row['phase'] for row in self.records] == ([] if phase == 'baseline' else ['baseline']), 'Original phase order differs')
        env = kwargs.get('env', {})
        need(env.get('CI') == 'true' and kwargs.get('shell', False) is False, 'Original CI launch differs')
        need(Path(kwargs['stdout'].name).resolve() == self.output / log, 'Original performance log differs')
        if phase == 'candidate':
            need(env.get('MOUSE_TEST_PROFILE') == str(self.profile), 'Original candidate profile differs')
        before_us, before_mono = time.time_ns() // 1000, time.monotonic_ns()
        process = self.original(args, *positional, **kwargs)
        after_mono, after_us = time.monotonic_ns(), time.time_ns() // 1000
        row = {'phase': phase, 'budgetMs': budget, 'pid': process.pid, 'parentPid': os.getpid(),
               'uid': os.geteuid(), 'argv': argv, 'expectedRootPath': self.expected_roots[phase],
               'nonce': self.nonces[phase], 'originalLog': log,
               'profile': str(self.profile) if phase == 'candidate' else None,
               'launchBeforeEpochUs': before_us, 'launchAfterEpochUs': after_us,
               'launchBeforeMonotonicNs': before_mono, 'launchAfterMonotonicNs': after_mono,
               'helperPid': None, 'helperExitCode': None}
        self.records.append(row)
        self.processes.append(process)
        thread = threading.Thread(target=self._observe, args=(process, row, after_mono), daemon=True)
        self.threads.append(thread)
        thread.start()
        # No handshake, evidence write, helper wait or clock reset is awaited.
        # Original run_logged receives its actual Electron/Python Popen object.
        return process

    def _observe(self, process, row, started_ns):
        helper = None
        name = PREFIX + row['phase']
        config, raw, log = (self.output / (name + suffix) for suffix in ('.json', '.jsonl', '.log'))
        try:
            need(row['launchBeforeEpochUs'] <= row['launchAfterEpochUs'], 'Launch wall clock moved backwards')
            need(process.poll() is None, 'Observed original process exited before sampler initialization')
            command = [str(self.sampler), row['phase'], str(row['pid']), str(row['parentPid']),
                       row['expectedRootPath'], str(row['launchBeforeEpochUs']), str(row['launchAfterEpochUs']),
                       str(row['budgetMs']), row['nonce'], str(raw), str(row['uid'])]
            cfg = {'schema': 1, 'kind': 'mouse637-host-observer-config', 'source': SOURCE,
                   'publisherSHA': self.publisher_sha, **row, 'sampler': str(self.sampler),
                   'samplerSha256': binding(self.sampler)['sha256'], 'output': str(raw), 'helperArgv': command}
            write_new(config, cfg)
            clean = {k: v for k, v in os.environ.items() if k not in ('GH_TOKEN', 'GITHUB_TOKEN', 'NODE_OPTIONS', 'ELECTRON_RUN_AS_NODE')}
            with log.open('xb') as stream:
                helper = self.original(command, env=clean, stdout=stream, stderr=subprocess.STDOUT)
                row['helperPid'] = helper.pid
                while helper.poll() is None:
                    remaining = row['budgetMs'] / 1000 - (time.monotonic_ns() - started_ns) / 1e9
                    if self.abort.is_set() or remaining <= 0:
                        raise RuntimeError('External sampler cancelled or reached original phase budget')
                    try:
                        helper.wait(timeout=min(.1, remaining))
                    except subprocess.TimeoutExpired:
                        pass
                row['helperExitCode'] = helper.returncode
                need(helper.returncode == 0, 'External sampler did not complete')
            need(raw.exists() and 0 < raw.stat().st_size <= MAX_RAW_BYTES, 'External accounting raw evidence absent or oversized')
            # The independent reader parses every record. This is only a launch receipt.
            row['completed'] = True
        except BaseException as cause:
            row['observerError'] = type(cause).__name__ + ': ' + str(cause)
            self.errors.append(row['observerError'])
        finally:
            if helper is not None:
                self._stop_helper(helper, row)
            try:
                row['originalExitCodeAtSamplerExit'] = process.poll()
            except BaseException as cause:
                row['originalPollError'] = type(cause).__name__ + ': ' + str(cause)
                self.errors.append(row['originalPollError'])
            row['finishedMonotonicNs'] = time.monotonic_ns()
            for key, file in [('config', config), ('raw', raw), ('helperLog', log)]:
                if file.exists():
                    try:
                        row[key] = {'filename': file.name, **binding(file)}
                    except BaseException as cause:
                        row['evidenceError'] = type(cause).__name__ + ': ' + str(cause)
                        self.errors.append(row['evidenceError'])

    def _stop_helper(self, helper, row):
        deadline = time.monotonic() + 3
        errors = []
        def attempt(action):
            try:
                return action()
            except BaseException as cause:
                errors.append(type(cause).__name__ + ': ' + str(cause))
                return None
        if attempt(helper.poll) is None:
            attempt(helper.terminate)  # only this sampler's actual Popen
            if attempt(helper.poll) is None:
                attempt(lambda: helper.wait(timeout=max(.001, min(2, deadline-time.monotonic()))))
            if attempt(helper.poll) is None:
                attempt(helper.kill)
                remaining = deadline-time.monotonic()
                if remaining > 0:
                    attempt(lambda: helper.wait(timeout=remaining))
        row['helperExitCode'] = helper.returncode
        if attempt(helper.poll) is None:
            errors.append('Owned sampler cleanup did not observe exit')
        if errors:
            row['helperCleanupErrors'] = errors
            self.errors.extend(errors)

    def finish(self, failed=False):
        if failed:
            self.abort.set()
        for thread in self.threads:
            thread.join(timeout=4)
        need(not any(thread.is_alive() for thread in self.threads), 'External sampler cleanup incomplete')
        # Original run_logged has already completed on the successful path.
        # Its actual Popen.returncode avoids an earlier concurrent poll lock miss.
        for row, process in zip(self.records, self.processes):
            row['originalExitCodeObserved'] = process.returncode
        if not failed:
            need(not self.errors and [row['phase'] for row in self.records] == ['baseline', 'candidate'] and
                 all(row.get('completed') is True and row.get('helperExitCode') == 0 and
                     row.get('originalExitCodeObserved') == 0 for row in self.records),
                 'Both original performance phases require complete external observations')


def save_summary(path, summary, error):
    """Diagnostics must never replace an already raised original verifier error."""
    try:
        write_new(path, summary)
    except BaseException as cause:
        if error is None:
            return cause
        print('MOUSE_637_HOST_OBSERVER_SUMMARY_SAVE_FAILED ' + type(cause).__name__, file=sys.stderr, flush=True)
    return error


def run(executable, sampler):
    need(sys.platform == 'darwin' and platform.machine() == 'arm64' and os.environ.get('CI') == 'true', 'Mac arm64 CI is required')
    tools, output = Path(__file__).resolve().parent, Path.cwd().resolve()
    executable, sampler = Path(executable).resolve(strict=True), Path(sampler).resolve(strict=True)
    need(sampler == output / (PREFIX + 'sampler.bin') and not Path(sampler).is_symlink(), 'Exact external sampler required')
    inner = tools / 'mouse637-guest-input-observer.py'
    expected = {inner: INNER_SHA, output / 'mouse-verify.py': VERIFIER_SHA,
                output / 'mouse-637-baseline-performance.py': BASELINE_SHA}
    for file, digest in expected.items():
        need(binding(file)['sha256'] == digest, 'Unchanged original tool differs: ' + file.name)
    publisher = os.environ.get('GITHUB_SHA', '')
    need(re.fullmatch('[0-9a-f]{40}', publisher), 'Exact publisher identity required')
    need(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=tools.parent, text=True).strip() == publisher, 'Publisher checkout differs')
    build_path = output / (PREFIX + 'build.json')
    build = json.loads(build_path.read_text(encoding='utf-8'))
    need(build.get('ok') is True and build.get('publisherSHA') == publisher and build.get('binary', {}).get('sha256') == binding(sampler)['sha256'] and
         build.get('source', {}).get('sha256') == binding(tools / 'mouse637-host-observer.c')['sha256'], 'Sampler build/source receipt differs')
    launches = ObservingLaunches(executable, output, sampler, publisher)
    summary = {'schema': 1, 'kind': 'mouse637-external-host-observer-summary', 'source': SOURCE, 'version': '6.0.37',
               'publisherSHA': publisher, 'platform': sys.platform, 'arch': platform.machine(),
               'runId': os.environ.get('GITHUB_RUN_ID'), 'runAttempt': os.environ.get('GITHUB_RUN_ATTEMPT'),
               'job': os.environ.get('GITHUB_JOB'), 'pid': os.getpid(), 'uid': os.geteuid(),
               'ok': False, 'originalSucceeded': False, 'releaseAcceptance': False,
               'causalConclusionEstablished': False, 'startedAtEpochUs': time.time_ns() // 1000,
               'wrapperSha256': binding(__file__)['sha256'], 'samplerSourceSha256': binding(tools / 'mouse637-host-observer.c')['sha256'],
               'innerWrapperSha256': INNER_SHA, 'verifierSha256': VERIFIER_SHA, 'baselineHelperSha256': BASELINE_SHA,
               'sampler': {'filename': sampler.name, **binding(sampler)},
               'build': {'filename': build_path.name, **binding(build_path)}, 'executable': str(executable), 'output': str(output)}
    previous_popen, previous_argv = subprocess.Popen, sys.argv
    error = None
    try:
        subprocess.Popen = launches
        sys.argv = [str(inner), str(executable)]
        runpy.run_path(str(inner), run_name='__main__')
        summary['originalSucceeded'] = True
        launches.finish()
        summary['ok'] = True
    except BaseException as cause:
        error = cause
        summary['error'] = type(cause).__name__ + ': ' + str(cause)
    finally:
        subprocess.Popen, sys.argv = previous_popen, previous_argv
        try:
            launches.finish(failed=error is not None)
            for file, digest in expected.items():
                need(binding(file)['sha256'] == digest, 'Original tool changed during observation')
            need(binding(sampler) == {k: summary['sampler'][k] for k in ('size', 'sha256')}, 'External sampler bytes changed')
            names = ['mouse-637-baseline-process.json', 'mouse-637-baseline-performance.json',
                     'mouse-637-baseline-performance/mouse-631-native.json', 'mouse-631-native.json',
                     'mouse-637-baseline-performance.log', 'mouse-631-native.log',
                     'mouse-637-guest-input-observer-summary.json', 'mouse-637-feature-readiness-summary.json']
            summary['evidence'] = {name: binding(output / name) for name in names if (output / name).exists()}
        except BaseException as cause:
            summary['ok'] = False
            summary['cleanupError'] = type(cause).__name__ + ': ' + str(cause)
            if error is None:
                error = cause
        summary['launches'] = launches.records
        summary['finishedAtEpochUs'] = time.time_ns() // 1000
        error = save_summary(output / (PREFIX + 'summary.json'), summary, error)
    if error is not None:
        raise error
    checker = runpy.run_path(str(tools / 'mouse637-host-observer-evidence.py'))
    checker['verify'](output)
    print('MOUSE_637_EXTERNAL_HOST_OBSERVER_PASS', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable')
    parser.add_argument('--sampler', required=True)
    args = parser.parse_args()
    run(args.executable, args.sampler)
