#!/usr/bin/env python3
"""Require a fresh, read-only public HTTPS/STUN probe before either publication."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile

TOOLS = Path(__file__).resolve().parent
SOURCE = runpy.run_path(str(TOOLS / 'mouse645-source.py'))
ORIGIN = 'https://mouse.black'
ISSUER = 'MCowBQYDK2VwAyEAO8rQW1FjIamh9U92KeX5nofRoxyyFtr8SgzUs9K4GxA='
PROBE = 'infra/mouse-services/public-probe.py'
CONFIG = 'desktop/mouse-service-config.cjs'
MAX_SECONDS = 90


def need(value, message):
    if not value:
        raise ValueError('Mouse645 public services: ' + message)


def contract():
    return {'validator': 'tools/mouse645-readiness.py',
            'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'origin': ORIGIN, 'pinnedIssuer': ISSUER,
            'sourceProbe': PROBE, 'probeSHA256': hashlib.sha256(SOURCE['checked'](PROBE)).hexdigest(),
            'clientConfigSHA256': hashlib.sha256(SOURCE['checked'](CONFIG)).hexdigest(),
            'required': ['website', 'identity', 'broker', 'stun'],
            'beforePublish': True, 'beforeChannel': True, 'freshInvocationRequired': True,
            'savedReceiptAccepted': False, 'createsAccounts': False,
            'createsTransferRooms': False, 'uploadsFiles': False, 'maximumSeconds': MAX_SECONDS}


def validate_contract(stage):
    actual = json.loads(SOURCE['read_bytes'](stage, 'evidence.schema.json'))['x-public645ServicesGate']
    need(actual == contract(), 'reviewed public-readiness contract changed')
    need(("PIN = '" + ISSUER + "'").encode() in SOURCE['checked'](PROBE)
         and ("serverPublicKey:'" + ISSUER + "'").encode() in SOURCE['checked'](CONFIG),
         'the source probe and shipped client do not share the reviewed issuer')


def verify_result(value, started, finished):
    need(isinstance(value, dict) and value.get('schema') == 1 and value.get('ready') is True,
         'public HTTPS or STUN is not ready')
    need(all(type(value.get(key)) is int and value[key] == 0
             for key in ('accountsCreated', 'transferRoomsCreated', 'filesUploaded')),
         'readiness probe performed a write')
    stamp = datetime.fromisoformat(value.get('checkedAt', '').replace('Z', '+00:00'))
    need(stamp.tzinfo is not None and started <= stamp <= finished
         and (finished - started).total_seconds() <= MAX_SECONDS, 'stale or unbound readiness receipt')
    website, identity, broker, stun = (value.get(name, {}) for name in ('website', 'identity', 'broker', 'stun'))
    need(website.get('ok') is True and website.get('status') == 200, 'website failed')
    need(identity.get('ok') is True and identity.get('status') == 200 and identity.get('json') is True
         and identity.get('pinnedIssuerMatches') is True, 'exact HTTPS account issuer failed')
    need(broker.get('ok') is True and broker.get('status') == 404 and broker.get('json') is True,
         'the public broker did not return its own bounded route response')
    need(stun.get('ok') is True and stun.get('host') == 'mouse.black' and stun.get('port') == 3478
         and stun.get('transport') == 'udp' and type(stun.get('responseBytes')) is int
         and 28 <= stun['responseBytes'] <= 512 and type(stun.get('attempts')) is int
         and 1 <= stun['attempts'] <= 3, 'public STUN binding failed')
    return value


def require_ready(output, *, stage, phase):
    need(phase in ('publish', 'channel'), 'unsupported publication phase')
    validate_contract(stage)
    output = SOURCE['managed_root'](output)
    probe = SOURCE['guarded_path'](output, PROBE)
    need(SOURCE['read_bytes'](output, PROBE) == SOURCE['checked'](PROBE),
         'the exact-source read-only probe is missing or changed')
    need(SOURCE['read_bytes'](output, CONFIG) == SOURCE['checked'](CONFIG),
         'the shipped client issuer configuration differs')
    result_name = 'mouse-645-public-readiness-' + phase + '.json'
    result = SOURCE['guarded_path'](output, result_name, allow_missing=True)
    if result.exists():
        SOURCE['remove_file'](output, result_name)
    started = datetime.now(timezone.utc)
    env = {key: value for key, value in os.environ.items() if key not in ('GH_TOKEN', 'GITHUB_TOKEN')}
    # The unchanged source probe writes only into a newly owned private folder.
    # Publishing its receipt afterward uses the descriptor-relative safe writer.
    with tempfile.TemporaryDirectory(prefix='.mouse645-readiness-', dir=output) as directory:
        probe_result = SOURCE['guarded_path'](directory, 'probe.json', allow_missing=True)
        probe = SOURCE['guarded_path'](output, PROBE)
        subprocess.run([sys.executable, str(probe), '--output', str(probe_result), '--require-ready'],
                       check=True, timeout=MAX_SECONDS, env=env)
        finished = datetime.now(timezone.utc)
        raw = SOURCE['read_bytes'](directory, 'probe.json', limit=16384)
        value = verify_result(json.loads(raw), started, finished)
        SOURCE['write_bytes'](output, result_name, raw)
    print('MOUSE_645_PUBLIC_SERVICES_' + phase.upper() + '_PASS', flush=True)
    return value
