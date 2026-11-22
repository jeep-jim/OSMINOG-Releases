"""Synthetic evidence mutations only; these tests never claim native acceptance."""
import copy
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest

TOOLS = Path(__file__).parent
E = runpy.run_path(str(TOOLS / 'mouse637-guest-input-observer-evidence.py'))
F = runpy.run_path(str(TOOLS / 'test_mouse637_feature_readiness.py'))
PUBLISHER = '1' * 40
PREFIX = E['PREFIX']


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Proof:
    """Explicit synthetic producer-shaped records with real reviewed module bytes."""
    def __init__(self, root, feature_adapted, adapted):
        self.root = root
        self.feature = F['Proof'](root, feature_adapted)
        self.exe, self.app, self.output = self.feature.exe, self.feature.app, self.feature.output
        self.profile = '/owned/profiles/retained636'
        self.pid, self.controller_pid, self.port, self.nonce = 300, 400, 42000, 'c' * 64
        (root / (PREFIX + 'original.cjs')).write_bytes((TOOLS / 'fixtures/mouse637-retained-002.cjs').read_bytes())
        (root / (PREFIX + 'adapted.cjs')).write_bytes(adapted)
        self.adapted_sha = sha(adapted)
        self.summary = {'schema': 1, 'kind': 'mouse637-passive-guest-input-summary', 'source': E['SOURCE'], 'version': E['VERSION'],
            'publisherSHA': PUBLISHER, 'platform': 'darwin', 'arch': 'arm64', 'ok': True,
            'executable': self.exe, 'appPath': self.app, 'profile': self.profile, 'output': self.output,
            'wrapperSha256': sha((TOOLS / 'mouse637-guest-input-observer.py').read_bytes()),
            'controllerSha256': sha((TOOLS / 'mouse637-guest-input-observer.cjs').read_bytes()),
            'innerWrapperSha256': E['INNER_SHA'], 'startedAt': 500, 'finishedAt': 100000}
        self.row = {'phase': 'retained', 'flag': E['FLAG'], 'pid': self.pid, 'controllerPid': self.controller_pid,
            'nonce': self.nonce, 'port': self.port, 'profile': self.profile,
            'argv': [self.exe, '--inspect-brk=127.0.0.1:' + str(self.port), E['FLAG']], 'originalArgv': [self.exe, E['FLAG']],
            'addedEnvironment': {'MOUSE_637_GUEST_INPUT_NONCE': self.nonce}, 'bootstrapStartedAt': 1000,
            'controllerExitCode': 0, 'processExitCode': 0, 'bootstrapElapsedMs': 200,
            'receipt': PREFIX + 'bootstrap.json', 'controllerReceipt': PREFIX + 'controller.json',
            'config': PREFIX + 'config.json', 'listenerReceipt': PREFIX + 'listener.json', 'controllerLog': PREFIX + 'controller.log'}
        self.summary['launches'] = [self.row]
        (root / self.row['controllerLog']).write_bytes(b'synthetic controller output; no native execution\n')
        self.config = {'schema': 1, 'phase': 'retained', 'flag': E['FLAG'], 'pid': self.pid, 'nonce': self.nonce,
            'port': self.port, 'publisherSHA': PUBLISHER, 'executable': self.exe, 'appPath': self.app,
            'profile': self.profile, 'output': self.output, 'deadlineEpochMs': 31000,
            'receipt': self.output + '/' + self.row['receipt'], 'controllerReceipt': self.output + '/' + self.row['controllerReceipt'],
            'listenerReceipt': self.output + '/' + self.row['listenerReceipt']}
        runtime = {'pid': self.pid, 'execPath': self.exe, 'argv': self.row['argv'], 'platform': 'darwin', 'arch': 'arm64',
                   'CI': 'true', 'profile': self.profile, 'nonce': self.nonce}
        early = {**runtime, 'availability': {'pid': 'undefined', 'execPath': 'undefined', 'argv': 'undefined'},
                 'pid': None, 'execPath': None, 'argv': None}
        self.receipt = {'schema': 1, 'kind': 'mouse637-passive-guest-input-bootstrap', 'source': E['SOURCE'], 'version': E['VERSION'],
            'publisherSHA': PUBLISHER, 'phase': 'retained', 'flag': E['FLAG'], 'pid': self.pid,
            'controllerPid': self.controller_pid, 'nonce': self.nonce, 'executable': self.exe, 'appPath': self.app,
            'profile': self.profile, 'target': self.app + '/mouse-636-retained-smoke.cjs', 'platform': 'darwin', 'arch': 'arm64',
            'versions': {'electron': '44.5.0', 'node': 'synthetic'}, 'fullRuntimeIdentity': copy.deepcopy(runtime),
            'originalSha256': E['ORIGINAL_SHA'], 'originalGitBlob': E['ORIGINAL_BLOB'], 'adaptedSha256': self.adapted_sha,
            'mainSha256': E['MAIN_SHA'], 'applications': 1, 'scope': E['SCOPE'], 'loaderRestored': True,
            'inspectorClosed': True, 'inspectorUrl': None, 'closedAt': 1100, 'compiledAt': 1110, 'receiptBeforeFixtureInvocation': True}
        self.control = {'schema': 1, 'ok': True, 'phase': 'retained', 'pid': self.pid, 'controllerPid': self.controller_pid,
            'nonce': self.nonce, 'publisherSHA': PUBLISHER, 'port': self.port, 'host': '127.0.0.1', 'startedAt': 1000,
            'finishedAt': 1200, 'earlyRuntimeIdentity': early, 'fullRuntimeIdentity': copy.deepcopy(runtime),
            'ownershipBeforeResume': True, 'serverUnavailable': True, 'controllerSha256': self.summary['controllerSha256']}
        self.listener = {'schema': 1, 'kind': 'mouse637-inspector-listener', 'pid': self.pid, 'port': self.port, 'host': '127.0.0.1',
            'command': ['/usr/sbin/lsof', '-nP', '-a', '-iTCP:' + str(self.port), '-sTCP:LISTEN', '-F', 'pfnPT', '-Ts'],
            'startedAt': 1010, 'finishedAt': 1020, 'exitCode': 0, 'signal': None, 'ok': True,
            'stdout': 'p300\nf27\nPTCP\nn127.0.0.1:42000\nTST=LISTEN\n', 'stderr': '',
            'parsed': {'pid': self.pid, 'fd': '27', 'protocol': 'TCP', 'endpoint': '127.0.0.1:42000', 'state': 'LISTEN'}}
        self.facts = {'schema': 1, 'version': E['VERSION'], 'platform': 'darwin', 'arch': 'arm64', 'pid': self.pid,
            'budgetMs': 240000, 'packaged': True, 'profileIsolated': True, 'physicalUserDeviceVerified': False,
            'liveExternalAccountsVerified': False, 'stage': 'complete', 'ok': True, 'restored': True,
            'nativeInputSource': 'CGEvent', 'elapsedMs': 8000, 'nativeInputs': [], 'guestClickAttempts': [],
            'requests': [{'index': x, 'at': 1500} for x in range(4)]}
        self.trace = {'schema': 1, 'kind': 'mouse637-passive-guest-input', 'source': E['SOURCE'], 'publisherSHA': PUBLISHER,
            'pid': self.pid, 'nonce': self.nonce, 'originalSha256': E['ORIGINAL_SHA'], 'adaptedSha256': self.adapted_sha,
            'started': True, 'disposed': True, 'caps': {'records': 2048, 'posts': 64, 'webContents': 32, 'domPerDocument': 256},
            'stats': {k: 0 for k in ('dropped', 'postDropped', 'errors', 'foreignMessages', 'malformedMessages', 'unownedEvents', 'documents')},
            'registeredWebContents': [], 'documents': [], 'records': [], 'posts': [],
            'semantics': 'input-event observes browser-side processing, not delivery; DOM has separate clocks; no DOM mousemove'}
        self.facts['guestInputObserver'] = self.trace
        self.tabs = {wc: str(wc) * 8 + '-0000-0000-0000-' + str(wc) * 12 for wc in range(2, 6)}
        for wc in range(1, 6):
            self.trace['registeredWebContents'].append({'id': wc, 'registeredAt': 1500})
            self.trace['documents'].append({'id': 'synthetic-doc-' + str(wc), 'timeOrigin': 1200 + wc,
                'role': 'shell' if wc == 1 else 'guest', 'index': -1 if wc == 1 else wc - 2,
                'webContentsId': wc, 'lastSequence': 0, 'cap': 256})
            self.dom(wc, 'ready', at=1900)
        self.trace['stats']['documents'] = 5
        for kind in ('before-mouse-event', 'input-event'):
            self.trace['records'].append({'sequence': len(self.trace['records']) + 1, 'at': 1950, 'source': 'webContents',
                'event': kind, 'role': 'guest', 'webContentsId': 2, 'tabId': self.tabs[2], 'defaultPrevented': False,
                'input': {'type': 'mouseMove', 'x': 100, 'y': 149, 'movementX': 0, 'movementY': 0,
                          'button': 'none', 'clickCount': 0, 'modifiers': []}})
        for i, (selector, wc) in enumerate(zip(E['GUEST_SELECTORS'], (2, 3, 4, 4, 4, 4, 5))):
            self.input(selector, wc, i)
        self.input('#shell-button', 1, 7)
        self.refresh()

    def dom(self, wc, kind, *, at, event_type=None, target_id=None):
        d = self.trace['documents'][wc - 1]
        d['lastSequence'] += 1
        n = d['lastSequence']
        event = {'sequence': len(self.trace['records']) + 1, 'at': at, 'source': 'dom', 'role': d['role'],
            'webContentsId': wc, 'tabId': self.tabs.get(wc), 'document': {k: d[k] for k in ('id', 'timeOrigin', 'role', 'index')},
            'kind': kind, 'domSequence': n, 'domAt': at + 50000, 'domTime': 20 + n, 'emitted': n, 'dropped': 0,
            'type': event_type, 'trusted': True if kind == 'event' else None, 'defaultPrevented': False if kind == 'event' else None,
            'target': {'kind': 'element', 'tag': 'A' if wc != 1 else 'BUTTON', 'id': target_id, 'linkId': target_id if wc != 1 else ''} if kind == 'event' else None,
            'button': 0 if kind == 'event' else None, 'buttons': 0 if kind == 'event' else None, 'pointerId': None, 'pointerType': '',
            'x': 100 if kind == 'event' else None, 'y': 149 if kind == 'event' else None, 'documentFocused': True if kind == 'event' else None}
        self.trace['records'].append(event)

    def input(self, selector, wc, i):
        start = 2000 + i * 100
        point = {'x': 104 + i, 'y': 252 + i}
        sequence = len(self.trace['records'])
        self.trace['posts'].append({'id': i + 1, **point, 'beforeSequence': sequence, 'beforeAt': start,
            'primaryBefore': {'available': True, 'value': False}, 'returned': True, 'resultType': 'boolean', 'result': True,
            'primaryAfter': {'available': True, 'value': True}, 'afterAt': start + 1, 'afterSequence': sequence})
        if wc != 1:
            events = [{'id': selector[1:], 'trusted': True, 'isTrusted': True, 'at': start + 50010}]
            native = {'selector': selector, 'source': 'CGEvent', 'point': point, 'tabId': self.tabs[wc], 'webContentsId': wc, 'events': events}
            self.facts['guestClickAttempts'].append({**copy.deepcopy(native),
                'before': {'at': start - 1, 'native': {'focus': {'shell': True, 'webContentsId': 1}}},
                'posted': {'at': start + 2, 'result': True}, 'poll': {'at': start + 20, 'events': copy.deepcopy(events)}})
        else:
            native = {'selector': selector, 'source': 'CGEvent', 'point': point, 'at': start + 2, 'navigates': False,
                'events': [{'type': 'click', 'trusted': True, 'matches': True, 'target': selector[1:], 'at': start + 50010}]}
        self.facts['nativeInputs'].append(native)
        for n, kind in enumerate(('pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click')):
            self.dom(wc, 'event', at=start + 3 + n, event_type=kind, target_id=selector[1:])

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value, ensure_ascii=False) + '\n')

    def digest(self, name):
        return sha((self.root / name).read_bytes())

    def refresh(self):
        """Rebind every enclosing receipt/hash/log after deep semantic mutations."""
        self.feature.refresh()
        self.write(self.row['receipt'], self.receipt)
        self.write(self.row['listenerReceipt'], self.listener)
        self.control['receiptSha256'] = self.digest(self.row['receipt'])
        self.control['listenerReceiptSha256'] = self.digest(self.row['listenerReceipt'])
        self.write(self.row['controllerReceipt'], self.control)
        self.write(self.row['config'], self.config)
        for key in ('receipt', 'controllerReceipt', 'config', 'listenerReceipt', 'controllerLog'):
            self.row[key + 'Sha256'] = self.digest(self.row[key])
        self.write(E['REPORT'], self.facts)
        (self.root / E['LOG']).write_text('MOUSE_637_GUEST_INPUT_OBSERVER_BOOTSTRAP ' + json.dumps(self.receipt) + '\n' +
            'MOUSE_636_RETAINED_OWNER_FEEDBACK_PASS\nMOUSE_NATIVE_PROCESS_RETURN pid=' + str(self.pid) + ' code=0 elapsedMs=9000\n')
        self.summary['evidence'] = {name: {'size': (self.root / name).stat().st_size, 'sha256': self.digest(name)}
                                   for name in (E['FEATURE'], E['REPORT'], E['LOG'])}
        self.write(PREFIX + 'summary.json', self.summary)

    def remove_records(self, predicate):
        self.trace['records'] = [x for x in self.trace['records'] if not predicate(x)]
        seen = {}
        for i, row in enumerate(self.trace['records'], 1):
            row['sequence'] = i
            if row['source'] == 'dom':
                key = (row['webContentsId'], row['document']['id'])
                seen[key] = seen.get(key, 0) + 1
                row['domSequence'] = row['emitted'] = seen[key]
        for doc in self.trace['documents']:
            doc['lastSequence'] = seen.get((doc['webContentsId'], doc['id']), 0)
        for post in self.trace['posts']:
            post['beforeSequence'] = post['afterSequence'] = 0

    def verify(self):
        return E['verify'](self.root, publisher_sha=PUBLISHER)


class ObserverEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        node = os.environ.get('CODEX_PRIMARY_RUNTIME_NODE') or shutil.which('node')
        if not node:
            raise RuntimeError('Node is required for exact reviewed transform bytes')
        cls.feature_adapted = subprocess.check_output([node, '-e',
            'const a=require("./tools/mouse637-feature-readiness.cjs"),f=require("fs");process.stdout.write(a.transform(f.readFileSync("tools/fixtures/mouse637-readiness-002-features.cjs","utf8")))'], cwd=TOOLS.parent)
        cls.adapted = subprocess.check_output([node, '-e',
            'const a=require("./tools/mouse637-guest-input-observer.cjs"),f=require("fs");process.stdout.write(a.transform(f.readFileSync("tools/fixtures/mouse637-retained-002.cjs","utf8")))'], cwd=TOOLS.parent)

    def make(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        return Proof(Path(temp.name), self.feature_adapted, self.adapted)

    def assert_mutation_fails(self, mutation):
        proof = self.make()
        mutation(proof)
        proof.refresh()
        with self.assertRaises(ValueError):
            proof.verify()

    def test_synthetic_bound_proof_and_optional_primary_observations_pass(self):
        proof = self.make()
        result = proof.verify()
        self.assertTrue(result['ok'])
        self.assertEqual(result['coverage']['guestClicks'], 7)
        self.assertEqual(result['coverage']['posts'], 8)
        self.assertFalse(result['causalFixEstablished'])
        self.assertTrue(result['originalNativeGatesRemainRequired'])
        for name, digest in result['inputs'].items():
            self.assertEqual(digest, proof.digest(name))
        for value in ({'available': False}, {'available': True, 'error': 'synthetic read failure'},
                      {'available': True, 'value': None, 'unexpectedType': 'object'}, {'available': True, 'value': True}):
            proof.trace['posts'][0]['primaryBefore'] = copy.deepcopy(value)
            proof.refresh()
            self.assertTrue(proof.verify()['ok'])

    def test_rehashed_process_nonce_publisher_and_bootstrap_mutations_fail(self):
        cases = [lambda p: p.row.update(pid=True), lambda p: p.row.update(controllerPid=p.pid),
            lambda p: p.row.update(processExitCode=1), lambda p: p.row.update(controllerExitCode=1),
            lambda p: p.row.update(bootstrapElapsedMs=30001), lambda p: p.row.update(addedEnvironment={}),
            lambda p: p.row['originalArgv'].append('--other'), lambda p: p.summary.update(publisherSHA='2' * 40),
            lambda p: p.summary.update(innerWrapperSha256='f' * 64), lambda p: p.receipt.update(pid=999),
            lambda p: p.receipt.update(nonce='d' * 64), lambda p: p.receipt.update(applications=True),
            lambda p: p.receipt.update(loaderRestored=False), lambda p: p.receipt.update(inspectorClosed=False),
            lambda p: p.receipt.update(inspectorUrl='ws://127.0.0.1:1'), lambda p: p.receipt.update(compiledAt=3000),
            lambda p: p.config.update(profile='/unowned/retained636'), lambda p: p.config.update(deadlineEpochMs=999999),
            lambda p: p.control.update(ownershipBeforeResume=False), lambda p: p.control.update(serverUnavailable=False),
            lambda p: p.control.update(finishedAt=40000), lambda p: p.control['earlyRuntimeIdentity'].update(nonce='d' * 64),
            lambda p: p.control['earlyRuntimeIdentity'].update(pid=p.pid),
            lambda p: p.control['fullRuntimeIdentity'].update(execPath='/wrong/exe'),
            lambda p: p.receipt['fullRuntimeIdentity'].update(pid=999)]
        for index, mutate in enumerate(cases):
            with self.subTest(index=index):
                self.assert_mutation_fails(mutate)

    def test_actual_listener_stdout_is_reparsed_despite_coherent_receipt_hashes(self):
        cases = [lambda p: p.listener.update(stdout=p.listener['stdout'].replace('p300', 'p999')),
            lambda p: p.listener.update(stdout=p.listener['stdout'] + 'p301\nf28\nPTCP\nn127.0.0.1:42000\nTST=LISTEN\n'),
            lambda p: p.listener.update(stdout=p.listener['stdout'] + 'f28\nPTCP\nn127.0.0.1:42000\nTST=LISTEN\n'),
            lambda p: p.listener.update(stdout=p.listener['stdout'].replace('127.0.0.1', '*')),
            lambda p: p.listener.update(stdout=p.listener['stdout'].replace('TST=LISTEN', 'TST=ESTABLISHED')),
            lambda p: p.listener.update(stdout=p.listener['stdout'].replace('PTCP', 'PTCP\nPTCP')),
            lambda p: p.listener.update(stdout=p.listener['stdout'].replace('PTCP', 'TQR=0\nPTCP')),
            lambda p: p.listener.update(stdout=p.listener['stdout'].replace('\n', '\r\n')),
            lambda p: p.listener.update(stdout='PTCP\n' + p.listener['stdout']),
            lambda p: p.listener.update(stderr='warning'), lambda p: p.listener.update(signal='SIGKILL'),
            lambda p: p.listener.update(exitCode=1), lambda p: p.listener['parsed'].update(fd='28'),
            lambda p: p.listener['command'].remove('-Ts')]
        for index, mutate in enumerate(cases):
            with self.subTest(index=index):
                self.assert_mutation_fails(mutate)

    def test_rehashed_original_failure_post_and_runtime_mutations_fail(self):
        cases = [lambda p: p.facts.update(ok=False), lambda p: p.facts.update(pid=999),
            lambda p: p.facts.update(budgetMs=240001), lambda p: p.facts.update(elapsedMs=240001),
            lambda p: p.facts.update(error={'message': 'synthetic original failure'}),
            lambda p: p.trace.update(pid=999), lambda p: p.trace.update(nonce='d' * 64),
            lambda p: p.trace.update(disposed=False), lambda p: p.trace['stats'].update(postDropped=1),
            lambda p: p.trace['stats'].update(malformedMessages=1), lambda p: p.trace['posts'].pop(),
            lambda p: p.trace['posts'][0].update(result=False), lambda p: p.trace['posts'][0].update(x=999),
            lambda p: p.trace['posts'][0].update(beforeAt=100), lambda p: p.trace['posts'][0].update(primaryBefore={'available': True, 'value': 'yes'}),
            lambda p: p.facts['nativeInputs'][0]['events'][0].update(trusted=False),
            lambda p: p.facts['guestClickAttempts'][0]['posted'].update(result=False),
            lambda p: p.facts['guestClickAttempts'][0].update(error={'message': 'timeout'}),
            lambda p: p.facts['nativeInputs'][-1]['events'][0].update(matches=False)]
        for index, mutate in enumerate(cases):
            with self.subTest(index=index):
                self.assert_mutation_fails(mutate)

    def test_rehashed_foreign_malformed_and_missing_trace_records_fail(self):
        cases = [lambda p: p.trace['documents'][0].update(webContentsId=999),
            lambda p: p.trace['documents'][1].update(index=999),
            lambda p: p.trace['records'][0].update(webContentsId=999),
            lambda p: p.trace['records'][1].update(tabId='f' * 36),
            lambda p: p.trace['records'][0]['document'].update(id='foreign-document'),
            lambda p: p.trace['records'][0].update(extra={'unbounded': 'payload'}),
            lambda p: p.trace['records'][0].update(kind='overflow'),
            lambda p: p.trace['records'][0].update(emitted=True),
            lambda p: p.trace['records'][5]['input'].update(modifiers=list('123456789')),
            lambda p: p.trace['records'][5].update(defaultPrevented=0),
            lambda p: p.trace['records'][0].update(domSequence=2),
            lambda p: p.remove_records(lambda e: e.get('type') == 'click' and e.get('target', {}) and e['target'].get('linkId') == 'download-a'),
            lambda p: p.remove_records(lambda e: e.get('source') == 'dom' and e.get('role') == 'shell' and e.get('kind') == 'event'),
            lambda p: p.remove_records(lambda e: e.get('event') == 'before-mouse-event'),
            lambda p: p.remove_records(lambda e: e.get('kind') == 'ready' and e.get('webContentsId') == 2)]
        for index, mutate in enumerate(cases):
            with self.subTest(index=index):
                self.assert_mutation_fails(mutate)

    def test_missing_changed_module_and_installed_signature_dependency_fail(self):
        for name in (PREFIX + 'listener.json', PREFIX + 'bootstrap.json', PREFIX + 'original.cjs',
                     PREFIX + 'adapted.cjs', 'mouse-637-feature-readiness-codesign-after.log'):
            with self.subTest(name=name):
                proof = self.make()
                (proof.root / name).unlink()
                with self.assertRaises(ValueError):
                    proof.verify()
        for name in (PREFIX + 'original.cjs', PREFIX + 'adapted.cjs'):
            with self.subTest(name=name):
                proof = self.make()
                (proof.root / name).write_bytes((proof.root / name).read_bytes() + b'\n// synthetic tamper\n')
                key = 'originalSha256' if 'original' in name else 'adaptedSha256'
                proof.receipt[key] = proof.trace[key] = proof.digest(name)
                proof.refresh()
                with self.assertRaises(ValueError):
                    proof.verify()
        for mutate in (lambda p: p.feature.summary['after']['codesign'].update(exitCode=1),
                       lambda p: p.feature.summary['after']['components']['Contents/Resources/app.asar.unpacked/mouse-native-menu.node'].update(sha256='a' * 64),
                       lambda p: p.feature.summary['before']['components']['Contents/Resources/app.asar'].update(sha256='a' * 64)):
            self.assert_mutation_fails(mutate)

    def test_no_new_pointer_sequence_or_cross_clock_gate_is_introduced(self):
        proof = self.make()
        proof.remove_records(lambda e: e.get('type') in ('pointerdown', 'pointerup', 'mousedown', 'mouseup'))
        for e in proof.trace['records']:
            if e['source'] == 'dom':
                e['domAt'] += 1000000000
        proof.refresh()
        self.assertTrue(proof.verify()['ok'])


if __name__ == '__main__':
    unittest.main()
