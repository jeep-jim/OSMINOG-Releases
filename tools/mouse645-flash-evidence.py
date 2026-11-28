#!/usr/bin/env python3
"""Bind the separate real-RTC Mac job to the exact package source commit."""
import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import runpy
import subprocess
import zipfile

TOOLS = Path(__file__).resolve().parent
SOURCE_REPO = 'jeep-jim/OSMINOG'
SOURCE = runpy.run_path(str(TOOLS / 'mouse645-source.py'))
ARTIFACT = 'mouse-flash-direct-transfer-evidence'
ARCHIVE = ARTIFACT + '.zip'
FIELDS = ('run', 'attempt', 'job', 'artifact', 'archiveSHA256')
FILES = ('mouse-flash-rtc.json', 'rtc.log', 'flash-receiving.png', 'flash-complete.png')
CHECKS = (
    'actual RTC handshake, matching code, device proofs, direct candidate pair',
    'no file contents before receiver approval',
    'interrupted transfer preserves durable progress',
    'fresh handshake after reopening both device stores',
    'no file contents before receiver approval',
    'resume transmits only missing payload, final hashes match, rendezvous offline',
    'one-time session closes and completed checkpoints are removed')
STEPS = ('Check Apple Silicon runner', 'Transfer, account, profile and retained settings contracts',
         'Native account and sidebar behavior contracts', 'Compile protected Keychain and retained native modules',
         'Real RTC transfer, consent, interruption and resume in two sandboxed Mouse windows',
         'Profile placement, signed owner ID, photo, persistence and incognito in native settings')


def need(value, message):
    if not value:
        raise ValueError('Mouse645 RTC: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_pin(pin):
    value = pin.get('rtc')
    need(isinstance(value, dict) and set(value) == set(FIELDS), 'exact RTC provenance fields are missing')
    if pin.get('ready') is False:
        need(all(value[key] is None for key in FIELDS), 'unready template claims an accepted RTC artifact')
    else:
        need(all(type(value[key]) is int and value[key] > 0 for key in FIELDS[:-1])
             and isinstance(value['archiveSHA256'], str) and re.fullmatch('[a-f0-9]{64}', value['archiveSHA256']),
             'real RTC run/attempt/job/artifact/hash is not pinned')
    return value


def contract():
    return {'validator': 'tools/mouse645-flash-evidence.py', 'sha256': sha(Path(__file__).read_bytes()),
            'runtimeVersion': '6.0.45', 'platform': 'darwin', 'arch': 'arm64',
            'sameSourceCommitAsPackages': True, 'exactSuccessfulAttemptAndJob': True,
            'sourceArtifactSHA256Bound': True, 'sourceOnly': True,
            'freshInstalledSidebarBoundSeparately': True, 'physicalUserDeviceVerified': False,
            'realRTCDataChannel': True, 'relayPermitted': False,
            'payloadAfterBrokerAndStunShutdown': True, 'required': list(FILES),
            'sourceSmoke': 'tools/mouse-flash-rtc-smoke.cjs',
            'sourceSmokeSHA256': sha(SOURCE['checked']('tools/mouse-flash-rtc-smoke.cjs')),
            'sourceWorkflowSHA256': sha(SOURCE['checked']('.github/workflows/mouse-flash.yml')),
            'artifactName': ARTIFACT, 'jobName': 'direct-transfer', 'requiredSteps': list(STEPS)}


def validate_contract(stage):
    need(json.loads((Path(stage) / 'evidence.schema.json').read_text()).get('x-direct645RTCGate') == contract(),
         'reviewed direct-transfer gate changed')


def verify(read):
    blobs = {name: read(name) for name in FILES}
    need(all(isinstance(raw, bytes) and 0 < len(raw) <= 32 * 1024**2 for raw in blobs.values()), 'missing or oversized RTC evidence')
    facts = json.loads(blobs[FILES[0]])
    need(facts.get('schema') == 1 and facts.get('status') == 'PASS' and facts.get('platform') == 'darwin'
         and facts.get('architecture') == 'arm64' and isinstance(facts.get('electron'), str)
         and re.fullmatch(r'\d+\.\d+\.\d+', facts['electron']), 'real macOS Electron RTC receipt is absent')
    need(all(facts.get(key) is True for key in ('realRTCDataChannel', 'sandbox', 'contextIsolation', 'noRelay', 'stunClosedBeforeResumedPayload'))
         and facts.get('nodeIntegration') is False, 'RTC isolation or server-outage boundary differs')
    need(facts.get('discoveryImplementation') == 'production bounded STUN Binding, loopback binding for this test'
         and facts.get('fixture') == '48 MiB + 173 bytes, a text file, an empty file and empty directory; not a terabyte test',
         'RTC fixture or production STUN implementation differs')
    total = 48 * 1048576 + 173 + len('Mouse Flash — проверка прямой передачи\n'.encode())
    need(type(facts.get('payloadBytes')) is int and facts['payloadBytes'] == total
         and type(facts.get('durableBeforeResume')) is int and 4 * 1048576 <= facts['durableBeforeResume'] < total
         and type(facts.get('payloadBytesAfterResume')) is int
         and facts['payloadBytesAfterResume'] == total - facts['durableBeforeResume'], 'resume resent durable bytes or lost payload')
    checks = facts.get('checks')
    need(isinstance(checks, list) and [row.get('name') for row in checks] == list(CHECKS), 'required real-RTC phases are missing or reordered')
    need(checks[1] == {'name': CHECKS[1], 'resume': False} and checks[4] == {'name': CHECKS[4], 'resume': True},
         'receiver consent was not tested before both payload streams')
    need(checks[2] == {'name': CHECKS[2], 'durableBytes': facts['durableBeforeResume'], 'totalBytes': total},
         'durable resume checkpoint differs')
    for index in (0, 3):
        rows = checks[index].get('candidateTypes')
        need(isinstance(rows, list) and 1 <= len(rows) <= 8 and all(
             row.get('state') == 'connected' and row.get('local') in ('host', 'srflx', 'prflx')
             and row.get('remote') in ('host', 'srflx', 'prflx') for row in rows), 'a direct nominated RTC pair was not observed')
    for key in ('firstConnection', 'resumedConnection'):
        stats = facts.get(key, {})
        need(set(stats) == {'sentBinaryBytes', 'maxMessageBytes', 'maxBufferedBytes'}
             and all(type(value) is int for value in stats.values()) and stats['sentBinaryBytes'] > 0
             and 0 < stats['maxMessageBytes'] <= 16384 and 0 <= stats['maxBufferedBytes'] <= 4 * 1048576,
             'bounded RTC binary-message/backpressure proof failed')
    lines = blobs['rtc.log'].decode('utf-8', 'strict').splitlines()
    need(lines.count('MOUSE_FLASH_REAL_RTC_PASS') == 1
         and not any('MOUSE_FLASH_REAL_RTC_FAIL' in line or 'MOUSE_FLASH_REAL_RTC_GLOBAL_TIMEOUT' in line for line in lines)
         and all(lines.count('PASS ' + name) >= CHECKS.count(name) for name in set(CHECKS)), 'actual RTC log does not complete every phase')
    # Screenshots are bound and decoded; assertions about received file hashes
    # come from the exact successful smoke code, not fabricated payload uploads.
    pixels = runpy.run_path(str(TOOLS / 'mouse645-task-evidence.py'))
    for name in FILES[2:]:
        image = pixels['decode_png'](blobs[name], name)
        need(image['width'] >= 400 and image['height'] >= 400, 'RTC window screenshot is incomplete')
    return {'schema': 1, 'version': '6.0.45', 'status': 'PASS', 'platform': 'darwin', 'arch': 'arm64',
            'sourceOnly': True, 'physicalUserDeviceVerified': False, 'fixtureBytes': total,
            'durableBeforeResume': facts['durableBeforeResume'], 'payloadAfterResume': facts['payloadBytesAfterResume'],
            'checks': list(CHECKS), 'artifacts': [{'file': name, 'bytes': len(blobs[name]), 'sha256': sha(blobs[name])} for name in FILES]}


def verify_archive(file, digest):
    file = Path(file)
    need(file.is_file() and not file.is_symlink() and file.stat().st_size <= 128 * 1024**2
         and sha(file.read_bytes()) == digest, 'immutable RTC artifact ZIP differs')
    with zipfile.ZipFile(file) as archive:
        rows = archive.infolist()
        need(len(rows) <= 128 and len({row.filename for row in rows}) == len(rows)
             and sum(row.file_size for row in rows) <= 256 * 1024**2, 'RTC archive is duplicated or oversized')
        for row in rows:
            path = PurePosixPath(row.filename)
            need(not path.is_absolute() and '..' not in path.parts and '\\' not in row.filename
                 and (row.external_attr >> 16) & 0o170000 != 0o120000 and row.file_size <= 32 * 1024**2, 'unsafe RTC artifact entry')
        return verify(archive.read)


def import_source(module):
    pin, api, output = module['PIN'], module['api'], module['OUT']
    rtc = validate_pin(pin)
    run = api(SOURCE_REPO, f'actions/runs/{rtc["run"]}/attempts/{rtc["attempt"]}')
    need(run.get('head_sha') == pin['source'] and run.get('id') == rtc['run']
         and run.get('run_attempt') == rtc['attempt'] and run.get('status') == 'completed'
         and run.get('conclusion') == 'success' and run.get('path') == '.github/workflows/mouse-flash.yml',
         'RTC workflow did not succeed on the exact package source')
    jobs = api(SOURCE_REPO, f'actions/runs/{rtc["run"]}/attempts/{rtc["attempt"]}/jobs?per_page=100')['jobs']
    matches = [row for row in jobs if row.get('id') == rtc['job'] and row.get('name') == 'direct-transfer']
    need(len(matches) == 1, 'exact RTC job is missing')
    job = matches[0]
    need((job.get('head_sha'), job.get('run_id'), job.get('run_attempt'), job.get('status'), job.get('conclusion'))
         == (pin['source'], rtc['run'], rtc['attempt'], 'completed', 'success'), 'RTC job provenance differs')
    steps = {row.get('name') for row in job.get('steps', []) if row.get('status') == 'completed' and row.get('conclusion') == 'success'}
    need(set(STEPS) <= steps, 'a required native RTC/identity step did not pass')
    artifact = api(SOURCE_REPO, f'actions/artifacts/{rtc["artifact"]}')
    need(artifact.get('id') == rtc['artifact'] and artifact.get('name') == ARTIFACT
         and artifact.get('expired') is False and artifact.get('digest') == 'sha256:' + rtc['archiveSHA256']
         and artifact.get('workflow_run', {}).get('id') == rtc['run']
         and artifact.get('workflow_run', {}).get('head_sha') == pin['source']
         and type(artifact.get('size_in_bytes')) is int and 0 < artifact['size_in_bytes'] <= 128 * 1024**2,
         'RTC artifact does not belong to its exact source run')
    stamp = lambda value: datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
    need(stamp(job['started_at']) <= stamp(artifact['created_at']) <= stamp(job['completed_at']), 'RTC artifact belongs to another job attempt')
    file = output / ARCHIVE
    with file.open('wb') as target:
        subprocess.run(['gh', 'api', f'repos/{SOURCE_REPO}/actions/artifacts/{rtc["artifact"]}/zip'], stdout=target, check=True, timeout=180)
    result = verify_archive(file, rtc['archiveSHA256'])
    result['provenance'] = {'source': pin['source'], **rtc}
    (output / 'source645-flash-independent.json').write_text(json.dumps(result, indent=2) + '\n')
    print('MOUSE_645_SOURCE_REAL_RTC_ACCEPTANCE_PASS', flush=True)
    return result


def before_publication(module):
    rtc = validate_pin(module['PIN'])
    return verify_archive(module['OUT'] / ARCHIVE, rtc['archiveSHA256'])
