#!/usr/bin/env python3
"""Read-only public reachability; never creates an account or a transfer room."""
import argparse
import datetime
import json
import secrets
import socket
import struct
import urllib.error
import urllib.request
from pathlib import Path

PIN = 'MCowBQYDK2VwAyEAO8rQW1FjIamh9U92KeX5nofRoxyyFtr8SgzUs9K4GxA='


def stun():
    result = {'host': 'mouse.black', 'port': 3478, 'transport': 'udp', 'ok': False}
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.settimeout(3)
        for attempt in range(3):
            transaction = secrets.token_bytes(12)
            request = struct.pack('!HHI', 1, 0, 0x2112A442) + transaction
            try:
                client.sendto(request, ('mouse.black', 3478))
                response, peer = client.recvfrom(512)
                assert peer[0] == socket.gethostbyname('mouse.black') and peer[1] == 3478
                kind, size, magic = struct.unpack('!HHI', response[:8])
                assert kind == 0x0101 and size == len(response) - 20 and magic == 0x2112A442
                assert response[8:20] == transaction
                offset, mapped = 20, False
                while offset + 4 <= len(response):
                    attribute, length = struct.unpack('!HH', response[offset:offset + 4])
                    value = response[offset + 4:offset + 4 + length]
                    assert len(value) == length
                    if attribute == 0x0020:
                        assert length == 8 and value[0] == 0 and value[1] == 1
                        assert struct.unpack('!H', value[2:4])[0] ^ 0x2112
                        mapped = True
                    offset += 4 + (length + 3) // 4 * 4
                assert offset == len(response) and mapped
                result.update(ok=True, responseBytes=len(response), attempts=attempt + 1)
                return result
            except (OSError, AssertionError, struct.error) as error:
                result['error'] = type(error).__name__
    return result


def get(endpoint):
    url = 'https://mouse.black' + endpoint
    try:
        response = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mouse645-readonly-probe'}), timeout=15)
    except urllib.error.HTTPError as error:
        response = error
    except (OSError, urllib.error.URLError) as error:
        return {'ok': False, 'error': type(error).__name__}, None
    with response:
        raw = response.read(8193)
        status = response.status
        if endpoint == '/':
            return {'status': status, 'ok': status == 200}, None
        try:
            data = json.loads(raw) if len(raw) <= 8192 else None
        except (ValueError, UnicodeError):
            data = None
        return {'status': status, 'json': isinstance(data, dict)}, data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--require-ready', action='store_true')
    args = parser.parse_args()
    website, _ = get('/')
    identity, info = get('/v1/accounts/info')
    identity['ok'] = identity.get('status') == 200 and isinstance(info, dict) and info.get('serverPublicKey') == PIN
    identity['pinnedIssuerMatches'] = identity['ok']
    broker, error = get('/v1/rooms')
    broker['ok'] = broker.get('status') == 404 and isinstance(error, dict) and error.get('error', {}).get('code') == 'NOT_FOUND'
    result = {'schema': 1, 'checkedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'website': website, 'identity': identity, 'broker': broker, 'stun': stun(),
              'accountsCreated': 0, 'transferRoomsCreated': 0, 'filesUploaded': 0}
    result['ready'] = all(result[name].get('ok') for name in ['website', 'identity', 'broker', 'stun'])
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    if args.require_ready and not result['ready']:
        raise SystemExit('Mouse HTTPS/STUN public readiness is incomplete.')


if __name__ == '__main__':
    main()
