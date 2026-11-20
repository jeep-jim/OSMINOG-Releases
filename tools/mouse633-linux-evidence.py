#!/usr/bin/env python3
"""Bounded independent first-install Linux evidence, never another OS's report."""
import ast
import hashlib
import json
import math
from pathlib import Path
import re
import runpy

VERSION = '6.0.33'
FILES = ('mouse-linux-smoke-write.json', 'mouse-linux-smoke-read.json',
         'mouse-linux-appimage/mouse-linux-smoke-read.json')
TASK_MARKERS = ('MOUSE_631_TASK_ONLY_NATIVE_PASS', 'MOUSE_631_FIFTY_TABS_FIVE_DESKTOPS_NATIVE_PASS',
                'MOUSE_631_INSTALLED_TASK_STRESS_PASS', 'MOUSE_632_STATIONARY_MEDIA_PASS')
OWNER_MARKER = 'MOUSE_633_OWNER_FEEDBACK_PASS'
_tasks = runpy.run_path(str(Path(__file__).with_name('mouse633-task-evidence.py')))
_reuse = runpy.run_path(str(Path(__file__).with_name('mouse633-reuse.py')))


def need(condition, message):
    if not condition:
        raise ValueError('Mouse633 Linux evidence: '+message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def positive(value):
    return type(value) is int and value > 0


def digest(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value)


def raw_json(read, name):
    raw = read(name)
    need(isinstance(raw, bytes) and 0 < len(raw) <= 4*1024**2, 'missing/oversized report: '+name)
    value = json.loads(raw)
    need(isinstance(value, dict), 'report must be an object: '+name)
    return raw, value


def flags(value, keys, label):
    need(isinstance(value, dict) and all(value.get(key) is True for key in keys), label+' facts incomplete')


def scope(value):
    need(value.get('ok') is True and not value.get('error') and
         (value.get('version'), value.get('platform'), value.get('arch')) == (VERSION, 'linux', 'x64'),
         'failed or non-Linux/current report')


def sandbox(value, uid, count):
    need(isinstance(value, dict) and value.get('disabledFlags') == [], 'sandbox disabled or absent')
    rows = value.get('renderers', [])
    need(len(rows) == count and len({row.get('pid') for row in rows}) == count, 'native renderer identities missing')
    for row in rows:
        need(positive(row.get('pid')) and row.get('seccomp') == 2 and row.get('noNewPrivs') == 1 and
             row.get('uid') == uid and positive(row.get('webContentsId')), 'renderer /proc sandbox facts differ')
        argv = row.get('argv')
        need(isinstance(argv, list) and argv and all(isinstance(arg, str) for arg in argv) and
             '--type=renderer' in argv and not any(re.match(
                 r'--(?:no-sandbox|disable-setuid-sandbox|disable-seccomp-filter-sandbox|disable-gpu-sandbox)(?:=|$)', arg)
                 for arg in argv), 'renderer command disables isolation')
        prefs = row.get('preferences', {})
        need(prefs.get('sandbox') is True and prefs.get('contextIsolation') is True and
             prefs.get('webSecurity') is True and prefs.get('nodeIntegration') is False,
             'renderer native preferences unsafe')
    return rows


def process(read, value, markers, *, prefix=''):
    need(isinstance(value, dict) and value.get('exitCode') == 0 and positive(value.get('pid')) and
         type(value.get('elapsedMs')) in (int, float) and 0 < value['elapsedMs'] <= 400000,
         'actual native process did not finish within its budget')
    need(value.get('requiredMarkers') == list(markers), 'process required markers differ')
    name = value.get('log')
    need(isinstance(name, str) and re.fullmatch(r'mouse-[a-z0-9-]+\.log', name), 'unsafe process log')
    raw = read(prefix+name)
    need(isinstance(raw, bytes) and 0 < len(raw) <= 32*1024**2 and sha(raw) == value.get('logSha256'),
         'process log hash differs')
    lines = raw.decode('utf-8').splitlines()
    need(all(marker in lines for marker in markers), 'native log success marker missing')


def captures(read, native, prefix):
    rows = native.get('captures', [])
    need(len(rows) == 2 and {row.get('theme') for row in rows} == {'light', 'dark'}, 'both Linux themes required')
    output = []
    for row in rows:
        name = row.get('filename')
        need(name == 'mouse-linux-'+native['mode']+'-'+row['theme']+'.png', 'capture scope/name differs')
        raw = read(prefix+name)
        need(sha(raw) == row.get('sha256'), 'native PNG byte binding differs')
        image = _tasks['decode_png'](raw, prefix+name)
        need(row.get('source') == 'globalCapture.acquire(display)' and row.get('backend') == 'desktopCapturer',
             'Linux screenshot is not the native display capture')
        need(image['width'] >= 800 and image['height'] >= 600, 'capture is not a full native desktop')
        size = row.get('screenPixelSize', {})
        need((image['width'], image['height']) == (size.get('width'), size.get('height')), 'PNG dimensions differ')
        display = row.get('display', {})
        bounds, window = display.get('bounds', {}), row.get('window', {})
        for rect in (bounds, window):
            need(all(type(rect.get(key)) in (int, float) and math.isfinite(rect[key]) for key in ('x','y','width','height'))
                 and rect['width'] > 0 and rect['height'] > 0, 'native display/window geometry invalid')
        scale = display.get('scaleFactor')
        need(type(scale) in (int, float) and 0.5 <= scale <= 4 and
             abs(image['width']-bounds['width']*scale) <= 1 and abs(image['height']-bounds['height']*scale) <= 1,
             'native framebuffer scale differs')
        need(bounds['x'] <= window['x'] and bounds['y'] <= window['y'] and
             window['x']+window['width'] <= bounds['x']+bounds['width']+1 and
             window['y']+window['height'] <= bounds['y']+bounds['height']+1, 'window is outside the owned display')
        output.append({'name': prefix+name, 'sha256': sha(raw), 'size': size})
    need(output[0]['sha256'] != output[1]['sha256'], 'both themes reused the same native image')
    return output


def task_gate(read):
    # Expand only the exact reviewed native-wrapper algorithm, targeting Linux.
    tree = _reuse['adapted_tree']('mouse632-release.py')
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'verify_631')
    class Linux(ast.NodeTransformer):
        def visit_Constant(self, node):
            if node.value == 'darwin': node.value = 'linux'
            elif node.value == 'arm64': node.value = 'x64'
            return node
    fn = Linux().visit(fn)
    namespace = {'json': json, 'sha': sha, 'V': VERSION, '_tasks': _tasks}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])), __file__, 'exec'), namespace)
    return namespace['verify_631'](read)


def verify(read, p):
    raw, report = raw_json(read, 'mouse-linux-verification.json')
    scope(report)
    need(report.get('firstLinuxRelease') is True and report.get('previousVersion') is None and
         report.get('ownerDeviceVerified') is False, 'first-release scope is absent or overstated')
    need(report.get('source') == p['source'] and str(report.get('runId')) == str(p['run']) and
         str(report.get('runAttempt')) == str(p['attempt']) and report.get('packages') == p['packages'],
         'source/package provenance differs')
    runner = report.get('runner', {})
    uid = runner.get('uid')
    need(runner.get('system') == 'Linux' and positive(uid) and
         isinstance(runner.get('display'), str) and re.fullmatch(r':\d+(?:\.\d+)?', runner['display']),
         'native unprivileged Linux X11 runner missing')
    checks = report.get('checks', {})
    for name in ('debInstallation', 'debReinstallation'):
        value = checks.get(name, {})
        process(read, value, ())
        need(value.get('packageName') == 'mouse-browser' and value.get('version') == VERSION and
             isinstance(value.get('executable'), str) and value['executable'].startswith('/opt/') and
             Path(value['executable']).name == 'mouse-browser' and
             value.get('desktopFile') == '/usr/share/applications/mouse-browser.desktop' and
             digest(value.get('desktopSha256')) and digest(value.get('executableSha256')),
             'real deb installation identity missing')
    need(all(checks['debInstallation'][key] == checks['debReinstallation'][key]
             for key in ('desktopSha256', 'executableSha256')), 'reinstalled native package changed')
    native, inputs, images = [], {'mouse-linux-verification.json': sha(raw)}, []
    for name in FILES:
        data, facts = raw_json(read, name)
        inputs[name] = sha(data)
        scope(facts)
        need(positive(facts.get('pid')) and facts.get('physicalUserDeviceVerified') is False and
             facts.get('displayBackend') == 'X11' and digest(facts.get('asarSha256')), 'native Linux scope incomplete')
        need(facts.get('nativeClose') == {'accelerator':'Ctrl+Q','input':'XTest'}, 'native close accelerator missing')
        need(facts.get('mode') == ('write' if len(native) == 0 else 'read'), 'native write/read order differs')
        sandbox(facts.get('sandbox'), uid, 2)
        prefix = 'mouse-linux-appimage/' if name.startswith('mouse-linux-appimage/') else ''
        images += captures(read, facts, prefix)
        native.append(facts)
    written, reopened, portable = native
    need(len({item['pid'] for item in native}) == 3 and len({item['asarSha256'] for item in native}) == 1,
         'deb restart and AppImage must use distinct native processes with identical ASAR bytes')
    need(written.get('packageFormat') == reopened.get('packageFormat') == 'deb' and
         written.get('appImage') is None and reopened.get('appImage') is None and
         portable.get('packageFormat') == 'appimage' and isinstance(portable.get('appImage'), str) and
         Path(portable['appImage']).name == 'Mouse-Browser-6.0.33-Linux-x64.AppImage', 'actual package formats differ')
    need(written.get('profile', {}).get('written') is True and digest(written['profile'].get('tokenSha256')),
         'real profile was not written')
    preserved_keys = ('differentProcess','preferencesPreserved','cookiePreserved','localStoragePreserved','bookmarkPreserved')
    for facts in (reopened, portable):
        preserved = facts.get('profile', {})
        flags(preserved, preserved_keys, 'profile preservation')
        need((preserved.get('previousVersion'), preserved.get('currentVersion')) == (VERSION, VERSION) and
             preserved.get('previousPid') == written['pid'] and preserved.get('currentPid') == facts['pid'] and
             preserved.get('tokenSha256') == written['profile']['tokenSha256'] and
             preserved.get('pageId') == written['profile'].get('pageId'), 'profile belongs to another native process')
    restart = checks.get('profileRestart', {})
    process(read, restart.get('write'), ('MOUSE_LINUX_PROFILE_WRITE_PASS','MOUSE_LINUX_X64_SMOKE_PASS'))
    process(read, restart.get('read'), ('MOUSE_LINUX_PROFILE_RESTART_PASS','MOUSE_LINUX_X64_SMOKE_PASS'))
    flags(restart, ('differentPids','closedProfileUnchanged'), 'restart')
    need(restart['write']['pid'] == written['pid'] and restart['read']['pid'] == reopened['pid'] and
         restart.get('writeSha256') == inputs[FILES[0]] and restart.get('readSha256') == inputs[FILES[1]] and
         digest(restart.get('closedProfileSha256')) and restart.get('preserved') == reopened['profile'],
         'native restart reports are not byte-bound')
    launch = checks.get('appImageLaunch', {})
    process(read, launch, ('MOUSE_LINUX_PROFILE_RESTART_PASS','MOUSE_LINUX_X64_SMOKE_PASS'), prefix='mouse-linux-appimage/')
    appimage = 'Mouse-Browser-6.0.33-Linux-x64.AppImage'
    need(launch.get('package') == appimage and launch.get('packageSha256') == p['packages'][appimage]['sha256'] and
         launch.get('report') == FILES[2] and launch.get('reportSha256') == inputs[FILES[2]] and
         launch.get('sameAsar') is True and launch.get('asarSha256') == portable['asarSha256'] and
         launch.get('preserved') == portable['profile'], 'actual AppImage launch missing')
    aggregate = sandbox(report.get('sandbox'), uid, 4)
    need(aggregate == written['sandbox']['renderers']+portable['sandbox']['renderers'], 'aggregate sandbox facts differ')
    native_checks = written.get('checks', {})
    mouse = native_checks.get('nativeInput', {})
    flags(mouse, ('ctrlASelects','noCaptureFromCtrlA','scrollbarHidden'), 'native Linux input')
    need(mouse.get('source') == 'XTest via xdotool' and type(mouse.get('wheelScrollY')) in (int,float) and
         mouse['wheelScrollY'] > 0, 'XTest wheel did not move the native page')
    primary = mouse.get('primaryButton')
    need(isinstance(primary, dict) and primary.get('source') == 'XQueryPointer' and
         primary.get('before') is False and primary.get('pressed') is True and
         primary.get('released') is False, 'native primary-button readback missing or incorrect')
    flags(native_checks.get('private'), ('normalWebContentsPreserved','privateWebContentsClosed','privateCookiesCleared','noPrivateProfileMarker'), 'private isolation')
    terminal = native_checks.get('nativeRuntime', {})
    need(positive(terminal.get('terminalPid')) and terminal.get('terminalExitCode') == 0 and
         'MOUSE_LINUX_PTY_OK' in terminal.get('terminalOutput', '') and terminal.get('nativeFileRead') is True,
         'packaged native PTY/files module did not run')
    documents = native_checks.get('documents', {})
    need(documents.get('report') == 'mouse-632-documents.json' and
         documents.get('sha256') == sha(read('mouse-632-documents.json')), 'document report byte binding differs')
    for kind,name in [('footer','mouse-632-footer.json'),('scrollbars','mouse-629-ui-regressions.json')]:
        bound=native_checks.get(kind,{})
        need(bound.get('report')==name and bound.get('sha256')==sha(read(name)), 'native '+kind+' report byte binding differs')
    task = checks.get('retainedTaskStress', {})
    process(read, task, TASK_MARKERS)
    for name, key in [('mouse-631-native.json','reportSha256'),('mouse-631-task.json','taskSha256'),
                      ('mouse-631-stress.json','stressSha256'),('mouse-632-media.json','mediaSha256')]:
        need(task.get(key) == sha(read(name)), 'task/stress raw bytes differ: '+name)
    tasks = task_gate(read)
    owner = checks.get('ownerFeedback', {})
    process(read, owner, (OWNER_MARKER,))
    need(owner.get('reportSha256') == sha(read('mouse-633-owner-feedback.json')), 'owner report bytes differ')
    feedback = runpy.run_path(str(Path(__file__).with_name('mouse633-feedback-evidence.py')))
    current = feedback['verify'](read, expected_platform='linux', expected_arch='x64')
    ui_raw, ui = raw_json(read, 'mouse-629-ui-regressions.json')
    need((ui.get('version'),ui.get('platform'),ui.get('arch')) == (VERSION,'linux','x64') and
         not ui.get('error') and ui.get('restored') is True, 'Linux scrollbar wrapper failed')
    scrollbar = runpy.run_path(str(Path(__file__).with_name('mouse633-ui-evidence.py')))
    scrolling = scrollbar['verify_scrollbars'](ui.get('scrollbars'), read)
    return {'ok': True, 'version': VERSION, 'platform': 'linux', 'arch': 'x64',
            'firstLinuxRelease': True, 'previousVersion': None, 'inputs': inputs,
            'nativeCaptures': images, 'sandboxRendererCount': len(aggregate),
            'taskAndStress': tasks, 'feedback': current, 'scrollbars': scrolling,
            'scrollbarReportSHA256': sha(ui_raw)}
