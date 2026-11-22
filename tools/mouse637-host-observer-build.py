#!/usr/bin/env python3
"""Build and bind the external Mac observer; this never launches Mouse."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys


def binding(file_path, **extra):
    data = Path(file_path).read_bytes()
    return {**extra, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def build(output, receipt):
    tools = Path(__file__).resolve().parent
    root = tools.parent
    source = tools / 'mouse637-host-observer.c'
    output = Path(output).resolve()
    receipt = Path(receipt).resolve()
    if output.exists() or receipt.exists():
        raise ValueError('Observer build output and receipt must be fresh')
    if output.name != 'mouse-637-host-observer-sampler.bin':
        raise ValueError('Unexpected observer binary name')
    output.parent.mkdir(parents=True, exist_ok=True)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    facts = {'schema': 1, 'kind': 'mouse637-host-observer-build', 'ok': False,
             'platform': sys.platform, 'arch': platform.machine(), 'startedAtUTC': now(),
             'publisherSHA': os.environ.get('GITHUB_SHA', ''), 'commands': [], 'errors': []}

    def run(argv):
        row = {'argv': [str(x) for x in argv]}
        facts['commands'].append(row)
        try:
            result = subprocess.run(row['argv'], cwd=root, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, timeout=60, check=False)
        except subprocess.TimeoutExpired as error:
            row.update(returncode=None, timedOut=True,
                       output=(error.stdout or b'')[:1048576].decode('utf-8', errors='replace'))
            raise
        row.update(returncode=result.returncode,
                   output=result.stdout[:1048576].decode('utf-8', errors='replace'))
        if len(result.stdout) > 1048576 or result.returncode:
            raise RuntimeError('Observer build command failed or exceeded its output bound')
        return row['output'].strip()

    error = None
    try:
        if sys.platform != 'darwin' or platform.machine() != 'arm64':
            raise ValueError('Observer build requires the actual arm64 Mac runner')
        if os.environ.get('CI') != 'true' or not re.fullmatch('[0-9a-f]{40}', facts['publisherSHA']):
            raise ValueError('Exact CI publisher identity is required')
        if run(['git', 'rev-parse', 'HEAD']) != facts['publisherSHA']:
            raise ValueError('Observer build checkout differs from GITHUB_SHA')
        for file in [source, Path(__file__).resolve()]:
            relative = file.relative_to(root).as_posix()
            if run(['git', 'hash-object', str(file)]) != run(['git', 'rev-parse', 'HEAD:' + relative]):
                raise ValueError('Observer build source differs from the committed file')
        facts['source'] = binding(source, path='tools/' + source.name)
        facts['builder'] = binding(__file__, path='tools/' + Path(__file__).name)
        facts['compilerVersion'] = run(['xcrun', 'clang', '--version'])
        facts['sdkPath'] = run(['xcrun', '--show-sdk-path'])
        facts['sdkVersion'] = run(['xcrun', '--show-sdk-version'])
        facts['command'] = ['xcrun', 'clang', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                            str(source), '-o', str(output)]
        run(facts['command'])
        arch = run(['xcrun', 'lipo', '-archs', str(output)])
        if arch != 'arm64':
            raise ValueError('Observer binary is not the required arm64 Mach-O')
        if binding(source, path='tools/' + source.name) != facts['source']:
            raise ValueError('Observer source changed while compiling')
        if binding(__file__, path='tools/' + Path(__file__).name) != facts['builder']:
            raise ValueError('Observer builder changed while compiling')
        facts['binary'] = binding(output, filename=output.name, path=str(output), arch=arch)
        facts['ok'] = True
    except BaseException as cause:
        error = cause
        facts['errors'].append(type(cause).__name__ + ': ' + str(cause))
    finally:
        facts['finishedAtUTC'] = now()
        with receipt.open('x', encoding='utf-8') as stream:
            json.dump(facts, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
    if error is not None:
        raise error
    print('MOUSE_637_HOST_OBSERVER_BUILD_PASS', flush=True)
    return facts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--receipt', required=True)
    args = parser.parse_args()
    build(args.output, args.receipt)
