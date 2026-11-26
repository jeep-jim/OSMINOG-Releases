"""Synthetic unit cache fixture only; never installed acceptance evidence."""
import datetime
import hashlib
import json
from pathlib import Path

VERSION = '6.0.40'


def sources():
    # The installed smoke checks these fixture identities against its actual
    # runtime SOURCES. Keep the portable publisher runner independent of a
    # source checkout or the runtime parser's Node dependency tree.
    return [{'id': ident, 'url': 'https://easylist-downloads.adblockplus.org/' + ident + '.txt'}
            for ident in ('easylist', 'ruadlist')]


def seed_cache(directory, profile, *, source_records=None, now=None):
    """Seed only the newly created CI profile; these are not downloaded lists."""
    directory, profile = Path(directory), Path(profile)
    cache = profile / 'mouse-adblock'
    cache.mkdir(mode=0o700)
    generated = (now or datetime.datetime.now(datetime.timezone.utc)).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    receipt = {'schema': 1, 'version': VERSION, 'synthetic': True,
               'purpose': 'isolated-installed-adblock-smoke', 'generatedAt': generated,
               'profile': str(profile), 'records': []}
    for source in source_records if source_records is not None else sources():
        ident, url = source['id'], source['url']
        if ident not in ('easylist', 'ruadlist') or url != 'https://easylist-downloads.adblockplus.org/' + ident + '.txt':
            raise ValueError('Unexpected production filter subscription identity')
        lines = ['[Adblock Plus 2.0]', '! MOUSE639 SYNTHETIC CI FIXTURE — not the actual subscription contents',
                 '! Only for an isolated installed-process acceptance profile.',
                 '/mouse-adblock-fixture/advertising-script.js']
        lines += ['||mouse639-' + ident + '-' + str(index).zfill(2) + '.test^' for index in range(60)]
        text = '\n'.join(lines) + '\n'
        record = {'schema': 1, 'source': ident, 'url': url, 'updatedAt': generated,
                  'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(), 'text': text, 'synthetic': True}
        raw = (json.dumps(record, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        target = cache / (ident + '.json')
        with target.open('xb') as stream:
            stream.write(raw)
        target.chmod(0o600)
        filename = 'mouse-639-adblock-cache-' + ident + '.json'
        (directory / filename).write_bytes(raw)
        receipt['records'].append({'source': ident, 'url': url, 'file': filename,
                                   'profileRelative': 'mouse-adblock/' + ident + '.json',
                                   'sha256': hashlib.sha256(raw).hexdigest(), 'textSha256': record['sha256'],
                                   'lines': len(text.splitlines()), 'supportedBlockRules': 61})
    if len(receipt['records']) != 2 or {row['source'] for row in receipt['records']} != {'easylist', 'ruadlist'}:
        raise ValueError('Two distinct synthetic filter records are required')
    (directory / 'mouse-639-adblock-cache.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    return receipt
