#!/usr/bin/env python3
"""Independent637 four populated presets and live-page retention evidence.

The637 contract replaces the obsolete seven empty-desktop suggestions with
actual service requests on populated desktops. It never rewrites frozen gates
or the emitted native request count. Synthetic unit fixtures are not evidence.
"""
from collections import Counter
import math
from pathlib import Path
import re
import runpy
from urllib.parse import quote, urlsplit

N = runpy.run_path(str(Path(__file__).with_name('mouse637-native-evidence.py')))
need, finite, positive, rect, sha = (N[k] for k in ('need', 'finite', 'positive', 'rect', 'sha'))
SOURCE = 'Owned loopback pages opened by native preset controls; no external account access'
CATALOG = {
    'trader': ['https://www.tradingview.com/chart/', 'https://www.investing.com/economic-calendar/',
               'https://finviz.com/', 'https://coinmarketcap.com/'],
    'support': ['https://web.telegram.org/k/', 'https://web.whatsapp.com/', 'https://web.max.ru/',
                'https://web.wechat.com/', 'https://www.google.com/maps/'],
    'design': ['https://www.figma.com/', 'https://github.com/', 'https://developer.mozilla.org/',
               'https://stackoverflow.com/', 'https://www.google.com/'],
    'content': ['https://www.instagram.com/explore/', 'https://www.twitch.tv/',
                'https://www.tiktok.com/explore', 'https://www.youtube.com/', 'https://x.com/',
                'https://www.facebook.com/', 'https://www.reddit.com/', 'https://www.threads.com/',
                'https://web.telegram.org/k/', 'https://web.wechat.com/',
                'https://web.whatsapp.com/', 'https://web.max.ru/'],
}
SEQUENCE = ['support', 'trader', 'design', 'content', 'support', 'support']
DELTAS = [5, 4, 5, 8, 0, 5]


def tree_rects(tree, bounds=(0, 0, 1, 1), depth=0):
    need(isinstance(tree, dict) and depth <= 20, 'preset tree missing or too deep')
    x, y, w, h = bounds
    if 'id' in tree:
        need(set(tree) == {'id'} and re.fullmatch(r'p[1-9][0-9]?', tree['id']), 'preset leaf malformed')
        return {tree['id']: bounds}
    need(set(tree) == {'axis', 'ratio', 'a', 'b'} and tree['axis'] in ('x', 'y')
         and finite(tree['ratio']) and 0 < tree['ratio'] < 1, 'preset split malformed')
    r = tree['ratio']
    a, b = ((x, y, w * r, h), (x + w * r, y, w * (1 - r), h)) if tree['axis'] == 'x' else (
        (x, y, w, h * r), (x, y + h * r, w, h * (1 - r)))
    left, right = tree_rects(tree['a'], a, depth + 1), tree_rects(tree['b'], b, depth + 1)
    need(not set(left) & set(right), 'preset repeats a pane')
    return {**left, **right}


def expected_rects(mode):
    if mode == 'content':
        return {'p' + str(i + 1): (math.floor(i / 2) / 6, (i % 2) / 2, 1 / 6, .5) for i in range(12)}
    if mode == 'support':
        return {**{'p' + str(i + 1): (math.floor(i / 2) * .32, (i % 2) * .5, .32, .5) for i in range(4)},
                'p5': (.64, 0, .36, 1)}
    if mode == 'trader':
        return {'p1': (0, 0, .66, 1), **{'p' + str(i + 2): (.66, i / 3, .34, 1 / 3) for i in range(3)}}
    if mode == 'design':
        return {'p1': (0, 0, .64, .66), 'p2': (0, .66, .32, .34), 'p3': (.32, .66, .32, .34),
                'p4': (.64, 0, .36, .5), 'p5': (.64, .5, .36, .5)}
    raise ValueError('unknown current preset mode: ' + str(mode))


def geometry(tree, mode):
    actual, expected = tree_rects(tree), expected_rects(mode)
    need(list(actual) == list(expected), 'preset pane order differs')
    need(all(all(abs(a - b) <= 1e-9 for a, b in zip(actual[key], expected[key])) for key in expected),
         'preset geometry differs from the requested grid: ' + mode)


def identifier(value):
    return isinstance(value, str) and 0 < len(value) <= 100


def page(value, origin):
    need(isinstance(value, dict) and identifier(value.get('id')) and type(value.get('internal')) is bool,
         'preset page identity absent')
    if value['internal']:
        need(value.get('url') == 'mouse://start' and value.get('webContentsId') is None
             and value.get('identity') is None, 'internal preset page differs')
    else:
        need(positive(value.get('webContentsId')) and isinstance(value.get('url'), str)
             and value['url'].startswith(origin + '/') and finite(value.get('identity'))
             and 0 <= value['identity'] < 1 and finite(value.get('timeOrigin')) and value['timeOrigin'] > 0
             and type(value.get('navigationEpoch')) is int and value['navigationEpoch'] >= 0
             and value.get('field') == 'preserved-preset-' + value['id']
             and all(finite(value.get(key)) for key in ('scrollX', 'scrollY')), 'owned preset document/state absent')
    return value


def preserved(before, after, origin, *, count=None):
    need(isinstance(before, list) and isinstance(after, list) and len(before) <= 60 and before == after,
         'preset navigation replaced or changed a live document')
    if count is not None:
        need(len(before) == count, 'preset retained page count differs')
    need(len({p.get('id') for p in before}) == len(before), 'preset retained IDs repeat')
    for item in before:
        page(item, origin)


def trusted(value, selector, platform, inputs=None):
    need(isinstance(value, dict) and value.get('selector') == selector and value.get('source') == N['source'](platform)
         and value.get('trusted') is True and positive(value.get('at'))
         and all(finite(value.get('point', {}).get(axis)) for axis in ('x', 'y')), 'preset native control receipt absent')
    if inputs is not None:
        matches = [row for row in inputs if row.get('selector') == selector and row.get('point') == value['point']
                   and row.get('source') == value['source'] and row.get('at') == value.get('ledgerAt', value['at'])]
        # The native event listener and the outer click ledger can timestamp the
        # same click a few milliseconds apart. Bind its exact event list instead
        # when the shared helper retains the full original receipt.
        if not matches and 'events' in value:
            matches = [row for row in inputs if row.get('selector') == selector and row.get('point') == value['point']
                       and row.get('source') == value['source'] and row.get('events') == value['events']]
        need(len(matches) == 1 and any(e.get('type') == 'click' and e.get('trusted') is True
             and e.get('matches') is True for e in matches[0].get('events', [])), 'preset click is absent from the native ledger')


def verify_contract(value, platform, pid, inputs=None):
    need(value.get('schema') == 1 and value.get('version') == '6.0.37' and value.get('platform') == platform
         and value.get('pid') == pid and positive(pid) and value.get('packaged') is True
         and value.get('arch') == ('arm64' if platform == 'darwin' else 'x64') and value.get('source') == SOURCE,
         'packaged preset process identity differs')
    origin = value.get('fixtureOrigin', '')
    parsed = urlsplit(origin)
    need(parsed.scheme == 'http' and parsed.hostname == '127.0.0.1' and parsed.port is not None
         and parsed.path == '' and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment,
         'preset fixture origin is not an isolated loopback server')
    catalog = value.get('catalog', [])
    need([item.get('id') for item in catalog] == list(CATALOG), 'four preset catalog/order missing')
    for entry in catalog:
        need(entry.get('sites') == CATALOG[entry['id']], 'preset service URL differs; use the actual web application')
        geometry(entry.get('tree'), entry['id'])
    apps, requests = value.get('applications', []), value.get('selectedRequests', [])
    need([row.get('mode') for row in apps] == SEQUENCE and isinstance(requests, list)
         and len(requests) == sum(DELTAS), 'populated and repeated preset application sequence/count differs')
    need(all(row.get('desk') == 'desk-2' for row in apps[:-1]) and apps[-1].get('desk') == 'desk-4',
         'preset application desktop ownership differs')
    selected_by_desk, request_at = {}, 0
    for index, sample in enumerate(apps):
        mode, desk, delta = sample['mode'], sample['desk'], DELTAS[index]
        geometry(sample.get('tree'), mode)
        need(sample.get('requestBefore') == request_at and sample.get('requestDelta') == delta
             and sample.get('requestAfter') == request_at + delta, 'actual preset request delta differs')
        preserved(sample.get('beforePages'), sample.get('afterPages'), origin)
        trusted(sample.get('input'), '#desk-modes [data-mode="' + mode + '"]', platform, inputs)
        slots, rows = sample.get('slots', {}), sample.get('selected', [])
        panes = list(expected_rects(mode))
        need(list(slots) == panes and len(rows) == len(panes) and len({row.get('id') for row in rows}) == len(rows),
             'preset has empty, duplicate or excess panes')
        known = selected_by_desk.setdefault(desk, {})
        missing = []
        for pane_id, canonical, row in zip(panes, CATALOG[mode], rows):
            need(row.get('pane') == pane_id and row.get('url') == canonical and identifier(row.get('id'))
                 and slots.get(pane_id) == row['id'], 'preset page is assigned to the wrong tile')
            need(row.get('internal') is False and positive(row.get('webContentsId')) and finite(row.get('identity'))
                 and row.get('observedURL') == origin + '/suggested/' + quote(canonical, safe="~()*!.'-_"),
                 'preset service did not open the owned redirected document')
            if canonical not in known:
                missing.append(canonical)
            else:
                prior = known[canonical]
                need(all(row.get(k) == prior.get(k) for k in ('id', 'webContentsId', 'identity')),
                     'revisiting a shared service replaced its live page')
            known[canonical] = row
        need(len(missing) == delta and Counter(requests[request_at:request_at + delta]) == Counter(missing),
             'raw intercepted requests do not match newly opened services')
        request_at += delta
    primary_ids = {row['id'] for row in selected_by_desk['desk-2'].values()}
    secondary_ids = {row['id'] for row in selected_by_desk['desk-4'].values()}
    need(not primary_ids & secondary_ids, 'different desktops borrowed the same page ownership')
    repeat = value.get('repeat', {})
    need(repeat.get('mode') == 'support' and repeat.get('requestBefore') == repeat.get('requestAfter') == 22
         and repeat.get('newRequests') == 0, 'repeated mode opened duplicate service pages')
    preserved(repeat.get('beforePages'), repeat.get('afterPages'), origin, count=23)
    preservation = value.get('preservation', {})
    preserved(preservation.get('beforePages'), preservation.get('afterPages'), origin, count=6)
    only = value.get('aiOnly', {})
    preserved(only.get('beforePages'), only.get('afterPages'), origin, count=1)
    need(only.get('id') == only['beforePages'][0]['id'] and only.get('application') == apps[-1]
         and only.get('requestBefore') == 22 and only.get('requestAfter') == 27
         and only['beforePages'][0]['url'] == origin + '/ai-only', 'AI-only desktop did not retain its chat')
    need('agentLanding' not in value, 'removed Agent landing must not be reported as a current preset')
    return {}


def verify(value, evidence, platform, pid, inputs=None):
    need(value.get('ok') is True, 'portable preset scenario did not complete')
    return verify_contract(value, platform, pid, inputs)


def verify_legacy_facts(facts, output):
    need(facts.get('suggestedRequests') == 27 and facts.get('preservedTabs') == 23,
         'legacy report must keep its actual four-preset request/page counts')
    value = facts.get('presetEvidence', {})
    verify_contract(value, 'darwin', value.get('pid'))
    return True
