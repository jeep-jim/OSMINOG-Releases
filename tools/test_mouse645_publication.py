"""Publisher rejection tests. Synthetic receipts are never native release proof."""
import ast
import base64
import copy
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import runpy
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'
STAGE = ROOT / 'staging/mouse/6.0.45-arm64'
PLAN = runpy.run_path(str(TOOLS / 'mouse645-publish-plan.py'))
REUSE = runpy.run_path(str(TOOLS / 'mouse645-reuse.py'))
SOURCE = runpy.run_path(str(TOOLS / 'mouse645-source.py'))
SERVICES = runpy.run_path(str(TOOLS / 'mouse645-readiness.py'))
NEW = runpy.run_path(str(TOOLS / 'mouse645-new-evidence.py'))
RTC = runpy.run_path(str(TOOLS / 'mouse645-flash-evidence.py'))
PIN = json.loads((STAGE / 'pin.json').read_text())
SCHEMA = json.loads((STAGE / 'evidence.schema.json').read_text())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def source_api(_repo, endpoint):
    prefix, source = endpoint.rsplit('?ref=', 1)
    assert source == 'a' * 40
    name = prefix.removeprefix('contents/')
    raw = SOURCE['checked'](name)
    return {'type': 'file', 'encoding': 'base64', 'content': base64.b64encode(raw).decode(),
            'sha': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()}


def flat_helper_fixture(directory):
    for name in SOURCE['FLAT_HELPERS']:
        (Path(directory) / name).write_text('# synthetic unused flat helper\n')


def ready_services(now=None):
    return {'schema': 1, 'checkedAt': (now or datetime.now(timezone.utc)).isoformat(), 'ready': True,
            'website': {'ok': True, 'status': 200},
            'identity': {'ok': True, 'status': 200, 'json': True, 'pinnedIssuerMatches': True},
            'broker': {'ok': True, 'status': 404, 'json': True},
            'stun': {'ok': True, 'host': 'mouse.black', 'port': 3478, 'transport': 'udp', 'responseBytes': 32, 'attempts': 1},
            'accountsCreated': 0, 'transferRoomsCreated': 0, 'filesUploaded': 0}


def synthetic_png():
    def chunk(kind, raw):
        return struct.pack('!I', len(raw)) + kind + raw + struct.pack('!I', zlib.crc32(kind + raw))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!IIBBBBB', 400, 400, 8, 6, 0, 0, 0)) + chunk(
        b'IDAT', zlib.compress((b'\0' + bytes([60, 90, 120, 255]) * 400) * 400)) + chunk(b'IEND', b'')


def synthetic_rtc():
    total = 48 * 1048576 + 173 + len('Mouse Flash — проверка прямой передачи\n'.encode())
    durable = 8 * 1048576
    checks = [{'name': name} for name in RTC['CHECKS']]
    for i in (0, 3): checks[i]['candidateTypes'] = [{'state': 'connected', 'local': 'host', 'remote': 'srflx'}]
    checks[1]['resume'] = False; checks[4]['resume'] = True
    checks[2].update(durableBytes=durable, totalBytes=total)
    facts = {'schema': 1, 'status': 'PASS', 'platform': 'darwin', 'architecture': 'arm64', 'electron': '35.1.0',
             'realRTCDataChannel': True, 'sandbox': True, 'contextIsolation': True, 'noRelay': True,
             'stunClosedBeforeResumedPayload': True, 'nodeIntegration': False,
             'discoveryImplementation': 'production bounded STUN Binding, loopback binding for this test',
             'fixture': '48 MiB + 173 bytes, a text file, an empty file and empty directory; not a terabyte test',
             'payloadBytes': total, 'durableBeforeResume': durable, 'payloadBytesAfterResume': total - durable,
             'checks': checks, 'firstConnection': {'sentBinaryBytes': durable, 'maxMessageBytes': 16384, 'maxBufferedBytes': 1048576},
             'resumedConnection': {'sentBinaryBytes': total - durable, 'maxMessageBytes': 16384, 'maxBufferedBytes': 1048576}}
    return {'mouse-flash-rtc.json': json.dumps(facts).encode(),
            'rtc.log': ('Synthetic unit fixture only\n' + '\n'.join('PASS ' + name for name in RTC['CHECKS']) + '\nMOUSE_FLASH_REAL_RTC_PASS\n').encode(),
            'flash-receiving.png': synthetic_png(), 'flash-complete.png': synthetic_png()}


class ActivationAndLineage(unittest.TestCase):
    def test_template_is_unready_and_performs_no_validation_or_network(self):
        self.assertFalse(PLAN['publication_ready']('macos-arm64', load=lambda _: self.fail('unready template loaded a publisher')))
        self.assertFalse((STAGE / 'PUBLISH_OWNER').exists())
        self.assertTrue(all(PIN[key] is None for key in PLAN['CLAIMS']))
        self.assertTrue(all(value is None for value in PIN['rtc'].values()))

    def test_unready_claims_and_foreign_platforms_cannot_activate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); stage = root / 'staging/mouse/6.0.45-arm64'; stage.mkdir(parents=True)
            for mutation in [lambda p: p.update(source='a' * 40), lambda p: p['rtc'].update(artifact=1),
                             lambda p: p['packages']['Mouse-Browser-6.0.45-mac-arm64.dmg'].update(size=1)]:
                value = copy.deepcopy(PIN); mutation(value); (stage / 'pin.json').write_text(json.dumps(value))
                with self.assertRaises(ValueError): PLAN['read_plan'](root)
            (stage / 'pin.json').write_text(json.dumps(PIN)); (stage / 'PUBLISH_OWNER').write_text('unready')
            with self.assertRaises(ValueError): PLAN['read_plan'](root)
        for platform in ('linux-x64', 'windows-x64', 'darwin-x64'):
            with self.assertRaises(ValueError): PLAN['publication_ready'](platform)

    def test_all_predecessor_bytes_and_exact644_package_are_frozen(self):
        REUSE['verify_frozen']()
        self.assertEqual(REUSE['previous']('darwin'), PIN['currentPrevious'])
        self.assertEqual(PIN['currentPrevious']['version'], '6.0.44')
        self.assertEqual(PIN['previous']['version'], '6.0.29')
        for name in REUSE['RETAINED_PLATFORM_MODULES']:
            self.assertEqual(REUSE['target'](name), name)

    def test_exact_upgrade_identities_and_flash_footer_keep_retained_geometry(self):
        upgrades = ast.unparse(REUSE['adapted_tree']('mouse637-upgrade-evidence.py'))
        self.assertIn('MOUSE_645_REAL_644_TO_645_PROFILE_PASS', upgrades)
        self.assertIn('Mouse-Browser-6.0.44-mac-arm64.dmg', upgrades)
        footer = ast.unparse(REUSE['adapted_tree']('mouse636-feedback-evidence.py'))
        self.assertIn("row.get('count') == 7", footer)
        self.assertIn("['emoji', 'zoom', 'history', 'bookmarks', 'downloads', 'flash', 'screenshot']", footer)
        self.assertIn("row.get('overflow', 99) <= 1", footer)
        self.assertIn("len(cases) == 6", footer)
        self.assertIn('Флэш и скриншот', footer)
        search = ast.unparse(REUSE['adapted_tree']('mouse636-search-removal-evidence.py'))
        self.assertIn("FOOTER = ['emoji', 'zoom', 'history', 'bookmarks', 'downloads', 'flash', 'screenshot']", search)
        self.assertIn('Эмодзи, масштаб, история, закладки, загрузки, Флэш и скриншот', search)
        self.assertIn('Emoji, zoom, history, bookmarks, downloads, Flash and screenshot', search)
        # Nothing besides the known inventory and labels is adapted by645.
        baseline = ast.unparse(REUSE['legacy']()['adapted_tree']('mouse636-search-removal-evidence.py'))
        for marker in ('tile-search', 'TileSearchUI', 'MOUSE_636_SEARCH_REMOVAL_PASS'):
            self.assertEqual(search.count(marker), baseline.count(marker))

    def test_workflow_uses_structured_driver_and_all_retained_markers(self):
        old = (ROOT / '.github/workflows/publish-mouse644.yml').read_text()
        new = (ROOT / '.github/workflows/publish-mouse645.yml').read_text()
        self.assertIn('env -u GH_TOKEN python3 tools/mouse-verify.py', new)
        self.assertIn('python3 ../tools/mouse645-source.py verify .', new)
        for line in old.splitlines():
            if 'grep -' not in line: continue
            expected = line.replace('MOUSE_644_REAL_643_TO_644_', 'MOUSE_645_REAL_644_TO_645_').replace('MOUSE_644_REAL_629_TO_644_', 'MOUSE_645_REAL_629_TO_645_')
            self.assertIn(expected, new)
        for marker in ('MOUSE_645_ACCOUNT_ACCEPTANCE_PASS', 'MOUSE_645_UI_WRITE_PASS', 'MOUSE_645_UI_NATIVE_PASS'):
            self.assertIn(marker, new)
        self.assertNotIn('windows-latest', new)
        self.assertNotIn('publish-mouse642', new)


class SettingsUpdateRoute(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.legacy = runpy.run_path(str(TOOLS / 'test_mouse637_update_ui_evidence.py'))
        cls.reader = runpy.run_path(str(TOOLS / 'mouse645-update-ui-evidence.py'))

    def fixture(self):
        report, owners, _ = self.legacy['fixture']()
        report['version'] = '6.0.45'
        inputs = []
        for index, sample in enumerate(report['samples']):
            sample['settingsOpenInput'] = copy.deepcopy(sample['openInput'])
            sample['settingsOpenInput']['selector'] = '#settings-button'
            sample['openInput']['selector'] = '#settings-sidebar-update'
            sample['settingsCloseInput'] = copy.deepcopy(sample['dismissInput'])
            sample['settingsCloseInput']['selector'] = '#settings-dialog [data-close-dialog]'
            sample['settingsHandoff'] = {'settingsOpen': True, 'updateOpen': True, 'updateModal': True}
            sample['after']['settingsOpen'] = False
            for offset, field in enumerate(('settingsOpenInput', 'openInput', 'dismissInput', 'settingsCloseInput')):
                event = sample[field]
                event['source'] = self.reader['N']['source']('darwin')
                event['at'] = 100 + index * 4 + offset
                inputs.append(event)
        return report, owners, inputs

    def verify(self, data):
        report, owners, inputs = data
        return self.reader['verify'](report, owners, pid=11, platform='darwin', inputs=inputs,
                                     input_check=self.legacy['F']['input_event'], origin=self.legacy['ORIGIN'])

    def test_settings_route_keeps_the_retained_phases_geometry_and_surface_probes(self):
        self.assertEqual(self.verify(self.fixture()), self.legacy['verify'](self.legacy['fixture']()))

    def test_settings_route_requires_all_four_owned_trusted_native_clicks(self):
        for field in ('settingsOpenInput', 'openInput', 'dismissInput', 'settingsCloseInput'):
            mutations = [lambda sample: sample.pop(field),
                         lambda sample: sample[field].update(selector='#version-button'),
                         lambda sample: sample[field].update(pid=12),
                         lambda sample: sample[field].update(source='script'),
                         lambda sample: sample[field].update(tabId='foreign-page'),
                         lambda sample: sample[field].update(action='drag'),
                         lambda sample: sample[field]['events'][0].update(trusted=False)]
            for mutation in mutations:
                with self.subTest(field=field, mutation=mutation):
                    data = self.fixture(); mutation(data[0]['samples'][0])
                    with self.assertRaises(ValueError): self.verify(data)

    def test_settings_route_requires_actual_modal_handoff_and_settings_restoration(self):
        mutations = [lambda sample: sample.pop('settingsHandoff'),
                     lambda sample: sample.update(settingsHandoff=[]),
                     lambda sample: sample['settingsHandoff'].update(settingsOpen=False),
                     lambda sample: sample['settingsHandoff'].update(updateOpen=False),
                     lambda sample: sample['settingsHandoff'].update(updateModal=False),
                     lambda sample: sample['settingsHandoff'].update(updateModal=1),
                     lambda sample: sample['settingsHandoff'].update(unobserved=True),
                     lambda sample: sample['after'].pop('settingsOpen'),
                     lambda sample: sample['after'].update(settingsOpen=True)]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                data = self.fixture(); mutation(data[0]['samples'][0])
                with self.assertRaises(ValueError): self.verify(data)

    def test_settings_route_rejects_missing_detached_and_reordered_ledger_events(self):
        for field in ('settingsOpenInput', 'openInput', 'dismissInput', 'settingsCloseInput'):
            with self.subTest(field=field, corruption='missing'):
                data = self.fixture(); data[2].remove(data[0]['samples'][0][field])
                with self.assertRaises(ValueError): self.verify(data)
            with self.subTest(field=field, corruption='detached'):
                data = self.fixture(); sample = data[0]['samples'][0]
                sample[field] = copy.deepcopy(sample[field]); sample[field]['at'] += 100
                with self.assertRaises(ValueError): self.verify(data)
        for index in range(3):
            with self.subTest(swapped=index):
                data = self.fixture(); data[2][index], data[2][index + 1] = data[2][index + 1], data[2][index]
                with self.assertRaises(ValueError): self.verify(data)

    def test_settings_route_adapter_rejects_missing_changed_or_duplicate_frozen_loop(self):
        scope = REUSE['adapted_tree'].__globals__
        original = ast.parse("[('openInput', '#version-button'), ('dismissInput', CONTROLS[-1] if theme == 'light' else '#update-minimize')]", mode='eval').body
        for corruption in ('missing', 'changed', 'duplicate'):
            tree = REUSE['legacy']()['adapted_tree']('mouse637-update-ui-evidence.py')
            class Corrupt(ast.NodeTransformer):
                def visit_For(self, node):
                    node = self.generic_visit(node)
                    if ast.dump(node.iter) == ast.dump(original):
                        if corruption == 'missing': return []
                        if corruption == 'duplicate': return [node, copy.deepcopy(node)]
                        node.iter.elts[0].elts[1].value = '#unknown-update-entry'
                    return node
            tree = Corrupt().visit(tree)
            with self.subTest(corruption=corruption), patch.dict(scope, {
                    'legacy': lambda: {'adapted_tree': lambda *_args, **_kwargs: copy.deepcopy(tree)}}):
                with self.assertRaisesRegex(ValueError, 'exactly one frozen native route'):
                    REUSE['adapted_tree']('mouse637-update-ui-evidence.py')


class StructuredSource(unittest.TestCase):
    def test_import_preserves_tree_and_executes_real_http_sqlite_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            flat_helper_fixture(output)
            SOURCE['fetch'](source_api, 'jeep-jim/OSMINOG', 'a' * 40, output)
            self.assertEqual((output / 'tools/mouse-verify.py').read_bytes(), (output / 'mouse-verify.py').read_bytes())
            script = """const assert=require('node:assert/strict');
const {serviceFixture}=require(process.argv[1]);
(async()=>{const f=await serviceFixture();try{
  const response=await fetch(f.identityOrigin+'/v1/accounts/info');assert.equal(response.status,200);
  const value=await response.json();assert.equal(typeof value.serverPublicKey,'string');
  assert.equal(f.service.get('SELECT status FROM accounts WHERE id=1').status,'reserved');
  console.log('REAL_HTTP_SQLITE_SOURCE_TREE_PASS');
}finally{await f.close();}})().catch(e=>{console.error(e);process.exitCode=1;});"""
            result = subprocess.run(['node', '-e', script, str(output / 'tools/mouse-645-account-verify.cjs')],
                                    check=True, capture_output=True, text=True, timeout=30)
            self.assertIn('REAL_HTTP_SQLITE_SOURCE_TREE_PASS', result.stdout)

    def test_git_blob_or_reviewed_source_mismatch_fails_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            flat_helper_fixture(directory)
            def changed(repo, endpoint):
                value = source_api(repo, endpoint); value['sha'] = '0' * 40; return value
            with self.assertRaises(ValueError): SOURCE['fetch'](changed, 'jeep-jim/OSMINOG', 'a' * 40, Path(directory))
            def rewritten(repo, endpoint):
                value = source_api(repo, endpoint); raw = b'console.log("wrong source")'; value['content'] = base64.b64encode(raw).decode()
                value['sha'] = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest(); return value
            with self.assertRaises(ValueError): SOURCE['fetch'](rewritten, 'jeep-jim/OSMINOG', 'a' * 40, Path(directory))

    def test_modified_structured_helper_is_rejected_on_reverification(self):
        with tempfile.TemporaryDirectory() as directory:
            flat_helper_fixture(directory)
            SOURCE['fetch'](source_api, 'jeep-jim/OSMINOG', 'a' * 40, Path(directory))
            # Retained native gates legitimately export inspected app code into
            # the evidence directory. It is not an imported executable helper.
            (Path(directory) / 'mouse-637-agent-code-main.cjs').write_text('// inspected native artifact\n')
            SOURCE['verify'](Path(directory))
            (Path(directory) / 'services/mouse-identity/service.cjs').write_text('changed')
            with self.assertRaises(ValueError): SOURCE['verify'](Path(directory))

    def test_tools_parent_symlink_repro_never_writes_outside(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); output = base / 'output'; outside = base / 'outside'
            output.mkdir(); outside.mkdir(); flat_helper_fixture(output)
            (outside / 'untouched.txt').write_bytes(b'outside sentinel')
            (output / 'tools').symlink_to(outside, target_is_directory=True)
            api = Mock(wraps=source_api)
            with self.assertRaisesRegex(ValueError, 'linked managed path component'):
                SOURCE['fetch'](api, 'jeep-jim/OSMINOG', 'a' * 40, output)
            api.assert_not_called()
            self.assertEqual(sorted(p.name for p in outside.iterdir()), ['untouched.txt'])
            self.assertEqual((outside / 'untouched.txt').read_bytes(), b'outside sentinel')

    def test_verification_rejects_linked_parent_even_when_all_bytes_match(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); output = base / 'output'; outside = base / 'outside'
            output.mkdir(); outside.mkdir(); flat_helper_fixture(output)
            SOURCE['fetch'](source_api, 'jeep-jim/OSMINOG', 'a' * 40, output)
            shutil.move(str(output / 'tools'), str(outside / 'tools'))
            (output / 'tools').symlink_to(outside / 'tools', target_is_directory=True)
            before = {file.name: file.read_bytes() for file in (outside / 'tools').iterdir()}
            with self.assertRaisesRegex(ValueError, 'linked managed path component'): SOURCE['verify'](output)
            with self.assertRaisesRegex(ValueError, 'linked managed path component'):
                SOURCE['fetch'](source_api, 'jeep-jim/OSMINOG', 'a' * 40, output)
            self.assertEqual(before, {file.name: file.read_bytes() for file in (outside / 'tools').iterdir()})

    def test_output_root_and_flat_helper_target_links_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); real = base / 'real'; real.mkdir(); flat_helper_fixture(real)
            output = base / 'output'; output.symlink_to(real, target_is_directory=True)
            for action in (lambda: SOURCE['fetch'](source_api, 'jeep-jim/OSMINOG', 'a' * 40, output),
                           lambda: SOURCE['verify'](output)):
                with self.assertRaisesRegex(ValueError, 'managed root'): action()
            output.unlink(); output.mkdir(); flat_helper_fixture(output); (output / 'tools').mkdir()
            victim = real / 'victim'; victim.write_bytes(b'not source')
            (output / 'tools/mouse-verify.py').symlink_to(victim)
            with self.assertRaisesRegex(ValueError, 'linked managed path component'):
                SOURCE['fetch'](source_api, 'jeep-jim/OSMINOG', 'a' * 40, output)
            self.assertEqual(victim.read_bytes(), b'not source')

    def test_snapshot_root_or_descendant_link_is_not_read(self):
        name = 'desktop/mouse-645-account-smoke.cjs'; raw = SOURCE['checked'](name)
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); snapshot = base / 'snapshot'; outside = base / 'outside'
            snapshot.mkdir(); outside.mkdir(); (outside / Path(name).name).write_bytes(raw)
            (snapshot / 'desktop').symlink_to(outside, target_is_directory=True)
            with patch.dict(SOURCE['checked'].__globals__, {'SNAPSHOT': snapshot}):
                with self.assertRaisesRegex(ValueError, 'linked managed path component'): SOURCE['checked'](name)
            alias = base / 'snapshot-alias'; alias.symlink_to(snapshot, target_is_directory=True)
            with patch.dict(SOURCE['checked'].__globals__, {'SNAPSHOT': alias}):
                with self.assertRaisesRegex(ValueError, 'managed root'): SOURCE['checked'](name)
            self.assertEqual((outside / Path(name).name).read_bytes(), raw)

    def test_approved_parent_alias_is_supported_but_child_alias_is_not(self):
        # Models macOS /var -> /private/var without permitting a managed child link.
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); canonical = base / 'canonical'; canonical.mkdir()
            alias = base / 'system-alias'; alias.symlink_to(canonical, target_is_directory=True)
            (canonical / 'output').mkdir(); root = alias / 'output'
            SOURCE['write_bytes'](root, 'nested/proof.txt', b'owned bytes')
            self.assertEqual(SOURCE['read_bytes'](root, 'nested/proof.txt'), b'owned bytes')
            self.assertEqual(SOURCE['managed_root'](root), (canonical / 'output').resolve())
            (root / 'nested-link').symlink_to(canonical / 'output/nested', target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'linked managed path component'):
                SOURCE['read_bytes'](root, 'nested-link/proof.txt')


class PublicServices(unittest.TestCase):
    def _files(self, output):
        for name in (SERVICES['PROBE'], SERVICES['CONFIG']):
            file = output / name; file.parent.mkdir(parents=True, exist_ok=True); file.write_bytes(SOURCE['checked'](name))

    def test_readiness_requires_each_route_pinned_issuer_stun_and_no_writes(self):
        now = datetime.now(timezone.utc); good = ready_services(now)
        self.assertEqual(SERVICES['verify_result'](good, now - timedelta(seconds=1), now + timedelta(seconds=1)), good)
        mutations = [lambda r: r.update(ready=False), lambda r: r['identity'].update(pinnedIssuerMatches=False),
                     lambda r: r['broker'].update(status=200), lambda r: r['stun'].update(transport='tcp'),
                     lambda r: r['stun'].update(ok=False), lambda r: r.update(accountsCreated=1),
                     lambda r: r.update(filesUploaded=True), lambda r: r.update(checkedAt=(now - timedelta(days=1)).isoformat())]
        for mutate in mutations:
            changed = copy.deepcopy(good); mutate(changed)
            with self.assertRaises(ValueError): SERVICES['verify_result'](changed, now - timedelta(seconds=1), now + timedelta(seconds=1))

    def test_saved_ready_receipt_cannot_replace_fresh_probe(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for name in (SERVICES['PROBE'], SERVICES['CONFIG']):
                file = output / name; file.parent.mkdir(parents=True, exist_ok=True); file.write_bytes(SOURCE['checked'](name))
            result = output / 'mouse-645-public-readiness-publish.json'; result.write_text(json.dumps(ready_services()))
            with patch.object(SERVICES['subprocess'], 'run', side_effect=subprocess.CalledProcessError(1, 'probe')) as execute:
                with self.assertRaises(subprocess.CalledProcessError): SERVICES['require_ready'](output, stage=STAGE, phase='publish')
            self.assertEqual(execute.call_count, 1)
            self.assertFalse(result.exists())

    def test_both_phases_require_verified_probe_bytes_and_each_new_success(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for name in (SERVICES['PROBE'], SERVICES['CONFIG']):
                file = output / name; file.parent.mkdir(parents=True, exist_ok=True); file.write_bytes(SOURCE['checked'](name))
            calls = []
            def execute(command, **kwargs):
                calls.append(command); self.assertIn('--require-ready', command)
                Path(command[command.index('--output') + 1]).write_text(json.dumps(ready_services()))
                return subprocess.CompletedProcess(command, 0)
            with patch.object(SERVICES['subprocess'], 'run', side_effect=execute):
                SERVICES['require_ready'](output, stage=STAGE, phase='publish')
                SERVICES['require_ready'](output, stage=STAGE, phase='channel')
            self.assertEqual(len(calls), 2)
            (output / SERVICES['PROBE']).write_text('# changed\n')
            with patch.object(SERVICES['subprocess'], 'run', side_effect=AssertionError('must reject before executing')):
                with self.assertRaises(ValueError): SERVICES['require_ready'](output, stage=STAGE, phase='publish')

    def test_root_probe_config_and_result_links_reject_before_execution(self):
        for kind in ('root', 'probe-parent', 'config-parent', 'result'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                base = Path(directory); output = base / 'output'; outside = base / 'outside'
                output.mkdir(); outside.mkdir(); self._files(output)
                victim = outside / 'victim'; victim.write_bytes(b'outside readiness sentinel')
                if kind == 'root':
                    real = base / 'real'; output.rename(real); output.symlink_to(real, target_is_directory=True)
                elif kind in ('probe-parent', 'config-parent'):
                    name = 'infra' if kind == 'probe-parent' else 'desktop'
                    shutil.move(str(output / name), str(outside / name)); (output / name).symlink_to(outside / name, target_is_directory=True)
                else:
                    (output / 'mouse-645-public-readiness-publish.json').symlink_to(victim)
                with patch.object(SERVICES['subprocess'], 'run', side_effect=AssertionError('must not execute a linked probe path')):
                    with self.assertRaises(ValueError): SERVICES['require_ready'](output, stage=STAGE, phase='publish')
                self.assertEqual(victim.read_bytes(), b'outside readiness sentinel')

    def test_probe_receipt_link_is_rejected_before_reading_or_publishing(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); output = base / 'output'; output.mkdir(); self._files(output)
            victim = base / 'outside.json'; raw = json.dumps(ready_services()).encode(); victim.write_bytes(raw)
            def execute(command, **_kwargs):
                target = Path(command[command.index('--output') + 1])
                self.assertNotEqual(target.parent, output)
                target.symlink_to(victim)
                return subprocess.CompletedProcess(command, 0)
            with patch.object(SERVICES['subprocess'], 'run', side_effect=execute):
                with self.assertRaisesRegex(ValueError, 'linked managed path component'):
                    SERVICES['require_ready'](output, stage=STAGE, phase='publish')
            self.assertEqual(victim.read_bytes(), raw)
            self.assertFalse((output / 'mouse-645-public-readiness-publish.json').exists())


class Native645Evidence(unittest.TestCase):
    def test_contract_rejects_weakening_account_ui_and_public_prerequisites(self):
        NEW['validate_contract'](STAGE); SERVICES['validate_contract'](STAGE); RTC['validate_contract'](STAGE)
        cases = [('x-current645AccountGate', 'installedProcesses', 2, NEW['validate_contract']),
                 ('x-current645IdentityGate', 'actualOSInputAndPixels', False, NEW['validate_contract']),
                 ('x-public645ServicesGate', 'beforeChannel', False, SERVICES['validate_contract']),
                 ('x-direct645RTCGate', 'sameSourceCommitAsPackages', False, RTC['validate_contract'])]
        with tempfile.TemporaryDirectory() as directory:
            for key, field, value, verify in cases:
                changed = copy.deepcopy(SCHEMA); changed[key][field] = value
                (Path(directory) / 'evidence.schema.json').write_text(json.dumps(changed))
                with self.assertRaises(ValueError): verify(Path(directory))

    def test_account_acceptance_recomputes_facts_and_rejects_rehashed_forgery(self):
        # This fixture is visibly synthetic and stays in a disposable test folder.
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            script = "const fs=require('node:fs'),path=require('node:path');const f=require(process.argv[1]).envelope();for(const [n,b]of f.files)fs.writeFileSync(path.join(process.argv[3],n),b);require(process.argv[2]).finalize(process.argv[3]);"
            subprocess.run(['node', '-e', script, str(TOOLS / 'fixtures/mouse645-account-evidence.cjs'),
                            str(TOOLS / 'mouse645-source/tools/mouse-645-account-verify.cjs'), directory],
                           check=True, capture_output=True, timeout=30)
            read = lambda name: (output / name).read_bytes()
            accepted = NEW['account'](read)
            self.assertEqual(accepted['installedProcesses'], 14)
            self.assertEqual(accepted['logicalDevices'], 2)
            receipt_name = 'mouse-645-account-acceptance.json'
            pristine_receipt = read(receipt_name)
            def late_frame(facts):
                state = facts['desktopSelection']['after']
                state['trace'][1]['at'] = state['transition']['layoutAt'] + 1501
                state['trace'][1]['frameTime'] = state['trace'][1]['at'] - 1
                state['transition']['totalDurationMs'] = 2000
            edits = [
                ('retained credentials', 'mouse-645-account-02.json', lambda f: f['credentials'].update(present=True)),
                ('untrusted click', 'mouse-645-account-00.json', lambda f: f['desktopSelection']['nativeInputs'][1]['events'][0].update(trusted=False)),
                ('invented input source', 'mouse-645-account-00.json', lambda f: f['desktopSelection']['nativeInputs'][1].update(source='DOM click')),
                ('stale transition', 'mouse-645-account-00.json', lambda f: f['desktopSelection']['before'].update(transition=copy.deepcopy(f['desktopSelection']['after']['transition']))),
                ('missing real RAF2', 'mouse-645-account-00.json', lambda f: f['desktopSelection']['after']['trace'].pop()),
                ('presentation after deadline', 'mouse-645-account-00.json', late_frame),
            ]
            for label, name, edit in edits:
                with self.subTest(label=label):
                    pristine_facts = read(name)
                    try:
                        facts = json.loads(pristine_facts); edit(facts)
                        (output / name).write_text(json.dumps(facts))
                        receipt = json.loads(pristine_receipt)
                        row = next(item for item in receipt['artifacts'] if item['file'] == name)
                        row.update(bytes=len(read(name)), sha256=sha(read(name)))
                        (output / receipt_name).write_text(json.dumps(receipt))
                        with self.assertRaises(subprocess.CalledProcessError): NEW['account'](read)
                    finally:
                        (output / name).write_bytes(pristine_facts)
                        (output / receipt_name).write_bytes(pristine_receipt)

    def test_artifact_inventory_rejects_duplicate_traversal_and_changed_bytes(self):
        rows = [{'file': 'mouse-645-test-' + str(i) + '.json', 'bytes': 2, 'sha256': sha(b'{}')} for i in range(5)]
        blobs = {item['file']: b'{}' for item in rows}; receipt = 'mouse-645-acceptance.json'
        for mutate in [lambda r: r.append(copy.deepcopy(r[0])), lambda r: r[0].update(file='../outside'),
                       lambda r: r[0].update(sha256='0' * 64)]:
            changed = copy.deepcopy(rows); mutate(changed)
            files = {**blobs, receipt: json.dumps({'artifacts': changed}).encode()}
            with self.assertRaises(ValueError): NEW['inventory'](files.__getitem__, receipt, r'mouse-645-[a-z0-9.-]+')


class DirectRTC(unittest.TestCase):
    def test_exact_payload_resume_candidates_and_offline_servers(self):
        files = synthetic_rtc(); value = RTC['verify'](files.__getitem__)
        self.assertEqual(value['fixtureBytes'], 50331884)
        self.assertEqual(value['payloadAfterResume'], value['fixtureBytes'] - value['durableBeforeResume'])
        mutations = [lambda r: r.update(stunClosedBeforeResumedPayload=False),
                     lambda r: r.update(payloadBytesAfterResume=r['payloadBytes']),
                     lambda r: r['checks'][0]['candidateTypes'][0].update(local='relay'),
                     lambda r: r['checks'][4].update(resume=False),
                     lambda r: r['firstConnection'].update(maxMessageBytes=65536),
                     lambda r: r['checks'].pop()]
        for mutate in mutations:
            changed = dict(files); facts = json.loads(changed['mouse-flash-rtc.json']); mutate(facts)
            changed['mouse-flash-rtc.json'] = json.dumps(facts).encode()
            with self.assertRaises(ValueError): RTC['verify'](changed.__getitem__)

    def test_failure_log_and_missing_native_screenshot_cannot_pass(self):
        files = synthetic_rtc(); files['rtc.log'] += b'MOUSE_FLASH_REAL_RTC_FAIL bad\n'
        with self.assertRaises(ValueError): RTC['verify'](files.__getitem__)
        files = synthetic_rtc(); files['flash-complete.png'] = b'not png'
        with self.assertRaises(ValueError): RTC['verify'](files.__getitem__)

    def test_zip_hash_duplicate_and_traversal_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / 'rtc.zip'; files = synthetic_rtc()
            with zipfile.ZipFile(file, 'w') as archive:
                for name, raw in files.items(): archive.writestr(name, raw)
            self.assertEqual(RTC['verify_archive'](file, sha(file.read_bytes()))['status'], 'PASS')
            with self.assertRaises(ValueError): RTC['verify_archive'](file, '0' * 64)
            with zipfile.ZipFile(file, 'a') as archive: archive.writestr('../outside', b'bad')
            with self.assertRaises(ValueError): RTC['verify_archive'](file, sha(file.read_bytes()))

    def test_other_source_or_failed_job_is_rejected_before_download(self):
        pin = {**PIN, 'ready': True, 'source': 'a' * 40, 'rtc': dict(run=2, attempt=1, job=3, artifact=4, archiveSHA256='b' * 64)}
        with tempfile.TemporaryDirectory() as directory:
            def api(_repo, endpoint):
                return {'head_sha': 'c' * 40, 'id': 2, 'run_attempt': 1, 'status': 'completed', 'conclusion': 'success', 'path': '.github/workflows/mouse-flash.yml'}
            with patch.object(RTC['subprocess'], 'run', side_effect=AssertionError('must not download unbound RTC')):
                with self.assertRaises(ValueError): RTC['import_source']({'PIN': pin, 'api': api, 'OUT': Path(directory)})
            changed = copy.deepcopy(pin); changed['rtc']['job'] = None
            with self.assertRaises(ValueError): RTC['validate_pin'](changed)


class PublicationOrdering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with redirect_stdout(io.StringIO()): cls.release = runpy.run_path(str(TOOLS / 'mouse645-release.py'))

    def test_publication_and_channel_reject_unready_services_before_writing(self):
        for action, original in [('publish', '_original638_publish'), ('channel', '_original645_channel')]:
            calls = []; function = self.release[action]; scope = function.__globals__
            def service(*_args, **_kwargs): calls.append('services'); raise ValueError('HTTPS unavailable')
            replacements = {'validate_template': lambda: calls.append('contract'),
                            '_source645': {'verify': lambda _: calls.append('source')},
                            '_rtc645': {'before_publication': lambda _: calls.append('rtc')},
                            '_extra638': {'fresh': lambda *_: calls.append('native')},
                            '_services645': {'require_ready': service},
                            original: lambda: calls.append('WRITE')}
            with patch.dict(scope, replacements):
                with self.assertRaisesRegex(ValueError, 'HTTPS unavailable'): function()
            self.assertNotIn('WRITE', calls)
            self.assertEqual(calls[-1], 'services')
            self.assertIn('rtc', calls)


if __name__ == '__main__':
    unittest.main()
