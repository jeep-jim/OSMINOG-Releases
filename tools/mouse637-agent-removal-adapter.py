#!/usr/bin/env python3
"""Explicit637 contract changes for the owner's removal of Mouse Agent.

The predecessor files stay byte-frozen. These edits run only after their
existing identity/palette adapters. They remove named, retired Agent work;
they do not manufacture old successful evidence or change archived reports.
The installed removal checker is required by the current owner gate.
"""
import ast
import copy

REMOVED_TOKENS = {
    'agent-inline-settings', 'agent-messenger-native-streaming',
    'restored-agent-entry', 'agent-visible-restore-without-autoenable',
    'agent-service-layout-preserved-return-reload',
    'agent-local-scoped-cdp', 'agent-node-pty-xterm-terminal',
    'agent-external-worker-local-model-fixture',
    'agent-stop-revokes-listener-and-shell', 'agent-pixel-presence-on-owned-desktop',
    'local-mcp-readonly-edit-permission', 'local-mcp-native-directory-boundary',
    'local-mcp-live-tree-action-journal', 'managed-local-dev-restart',
}
TOKEN_RENAMES = {
    'five-mode-populated-presets-preserve-live-pages': 'four-mode-populated-presets-preserve-live-pages',
    'site-reported-eta-and-terminal-lifecycle': 'site-reported-eta-page-progress',
    'scoped-progress-determinate-indeterminate-stop': 'scoped-page-progress-determinate-indeterminate',
    'MOUSE_624_SCOPED_PROGRESS_PILL_PASS': 'MOUSE_624_SCOPED_PAGE_PROGRESS_PASS',
    'MOUSE_624_AGENT_SERVICE_LAYOUT_PERSIST_PASS': 'MOUSE_624_SETTINGS_LAYOUT_PERSIST_PASS',
    'mouse-624-agent-preserved.png': 'mouse-624-settings-preserved.png',
}
REMOVED_MARKERS = {
    'MOUSE_628_LOCAL_MCP_NATIVE_PASS',
    'MOUSE_622_AGENT_CDP_PTY_WORKER_STOP_PASS', 'MOUSE_632_OPTIONAL_HELPER_MANUAL_ONLY_PASS',
}
REMOVED_IMAGES = {'mouse-622-agent-running.png'}


def _need(value, message):
    if not value:
        raise ValueError('637 removal adapter target changed: ' + message)


def _function(tree, name):
    found = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    _need(len(found) == 1, name)
    return found[0]


def _source(node):
    return ast.unparse(node)


def _replace(tree, before, after, *, count=1, expression=False):
    mode = 'eval' if expression else 'exec'
    old = ast.parse(before, mode=mode)
    old = old.body if expression else old.body[0]
    new = ast.parse(after, mode=mode) if after else None
    new = (new.body if expression else new.body[0]) if new is not None else None
    wanted, hits = ast.dump(old), 0

    class Edit(ast.NodeTransformer):
        def visit(self, node):
            nonlocal hits
            if ast.dump(node) == wanted:
                hits += 1
                return ast.copy_location(copy.deepcopy(new), node) if new is not None else None
            return super().visit(node)

    tree = Edit().visit(tree)
    _need(hits == count, before[:120] + ' (' + str(hits) + ')')
    return tree


def _lists(tree, values):
    """Drop exact literal entries only, never arbitrary expressions/predicates."""
    class Edit(ast.NodeTransformer):
        def visit_List(self, node):
            node = self.generic_visit(node)
            node.elts = [v for v in node.elts if not (isinstance(v, ast.Constant) and isinstance(v.value, str) and v.value in values)]
            return node
        visit_Tuple = visit_List
        visit_Set = visit_List
    return Edit().visit(tree)


def _strings(tree, replacements):
    class Edit(ast.NodeTransformer):
        def visit_Constant(self, node):
            if isinstance(node.value, str) and node.value in replacements:
                return ast.copy_location(ast.Constant(replacements[node.value]), node)
            return node
    return Edit().visit(tree)


def _remove_local_capture_block(tree, *, ui):
    fn = _function(tree, 'verify_retained')
    # Exactly six consecutive statements belong to the retired Local/MCP
    # protocol/capture contract. The following page progress proof is retained.
    starts = [i for i, n in enumerate(fn.body) if _source(n).startswith("require(local.get('status')")]
    _need(len(starts) == 1, 'Local block start')
    start = starts[0]
    _need(len(fn.body[start:start + 6]) == 6 and
          _source(fn.body[start + 3]) == "captures = local.get('captures', [])" and
          isinstance(fn.body[start + 5], ast.For) and
          _source(fn.body[start + 6]) == "rows = progress.get('rows', [])", 'six-statement Local block')
    del fn.body[start:start + 6]
    before = ('local, progress, border, motion, slides, trace = (docs[n] for n in RETAINED_JSON_NAMES)' if ui else
              'local, progress, border, motion, slides, swipe, trace = (docs[n] for n in RETAINED_JSON_NAMES)')
    tree = _replace(tree, before, before.replace('local, ', '', 1))
    returns = [n for n in fn.body if isinstance(n, ast.Return)]
    _need(len(returns) == 1 and isinstance(returns[0].value, ast.Dict), 'retained return ledger')
    value = returns[0].value
    keys = [i for i, key in enumerate(value.keys) if isinstance(key, ast.Constant) and key.value == 'localCaptures']
    _need(len(keys) == 1 and isinstance(value.values[keys[0]], ast.Constant) and value.values[keys[0]].value == 4, 'retired Local count')
    del value.keys[keys[0]]; del value.values[keys[0]]
    return tree


def apply(name, tree):
    if name in ('mouse632-release.py', 'mouse633-release.py', 'mouse634-release.py',
                'mouse635-release.py', 'mouse636-release.py', 'mouse632-windows-release.py',
                'mouse633-windows-release.py', 'mouse634-windows-release.py',
                'mouse635-windows-release.py', 'mouse636-windows-release.py',
                'mouse633-linux-release.py', 'mouse634-linux-release.py',
                'mouse635-linux-release.py', 'mouse636-linux-release.py'):
        tree = _lists(tree, REMOVED_TOKENS | REMOVED_MARKERS | REMOVED_IMAGES)
        tree = _strings(tree, TOKEN_RENAMES)

    if name in ('mouse632-evidence.py', 'mouse632-ui-evidence.py'):
        tree = _remove_local_capture_block(tree, ui=name.endswith('-ui-evidence.py'))
        # The immutable628 dependency still supplies PNG/crop algorithms and
        # old names. Filter the retired Local entry before current637 consumes
        # its ledger; never edit the historical module or its report bytes.
        if name == 'mouse632-evidence.py':
            tree = _replace(tree, "reviewed['JSON_NAMES']", "tuple(n for n in reviewed['JSON_NAMES'] if n != 'mouse-628-local.json')", expression=True)
            tree = _replace(tree, "reviewed['NATIVE_MARKERS']", "tuple(n for n in reviewed['NATIVE_MARKERS'] if n != 'MOUSE_628_LOCAL_MCP_NATIVE_PASS')", expression=True, count=2)
        else:
            tree = _replace(tree, 'legacy.JSON_NAMES', "tuple(n for n in legacy.JSON_NAMES if n != 'mouse-628-local.json')", expression=True)
            tree = _replace(tree, 'legacy.NATIVE_MARKERS', "tuple(n for n in legacy.NATIVE_MARKERS if n != 'MOUSE_628_LOCAL_MCP_NATIVE_PASS')", expression=True)

    if name == 'mouse633-release.py':
        fn = _function(tree, '_current_agent_reports')
        fn.body = ast.parse("return runpy.run_path(str(Path(__file__).with_name('mouse637-agent-removal-evidence.py')))['verify'](read)").body
        # The unused historical entry helper is removed together with its
        # injection; full removal evidence replaces all old entry assertions.
        tree.body.remove(_function(tree, '_current_agent_entry'))
        class RemoveEntryInjection(ast.NodeTransformer):
            def visit_Call(self, node):
                node = self.generic_visit(node)
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == '_retained' and node.func.attr == 'update':
                    node.keywords = [v for v in node.keywords if v.arg != '_current_agent_entry']
                return node
        tree = RemoveEntryInjection().visit(tree)

    if name == 'mouse632-release.py':
        # Both historical helper-entry blocks are obsolete. Actual removal is
        # checked in633's current feedback wrapper and637's owner process.
        class RemoveEntry(ast.NodeTransformer):
            hits = 0
            def visit_If(self, node):
                if any(isinstance(n, ast.Constant) and n.value in (
                    'Mouse632 quiet optional helper entry evidence incomplete',
                    'Mouse632 helper automatically restores') for stmt in node.body for n in ast.walk(stmt)):
                    self.hits += 1
                    return None
                return self.generic_visit(node)
        edit = RemoveEntry(); tree = edit.visit(tree)
        _need(edit.hits == 3, 'three retired entry predicates')
        tree = _replace(tree, "entry = json.loads(read('mouse-623-verification.json')).get('agentEntry', {})", '')
        tree = _replace(tree, "entry = facts623.get('agentEntry', {})", '')
        tree = _lists(tree, {'externalWorker', 'ptyStdout', 'autonomousActions', 'stoppedListener', 'localhostPreview'})
        # Keep actual desk count, canonical requests, hidden capture count and
        # real thumbnail checks; only retired model request count is removed.
        class ModelCount(ast.NodeTransformer):
            hits = 0
            def visit_BoolOp(self, node):
                node = self.generic_visit(node)
                old = ast.dump(ast.parse("facts.get('localModelFixtureRequests') != 3", mode='eval').body)
                found = [v for v in node.values if ast.dump(v) == old]
                self.hits += len(found)
                node.values = [v for v in node.values if ast.dump(v) != old]
                return node.values[0] if len(node.values) == 1 else node
        edit = ModelCount(); tree = edit.visit(tree)
        _need(edit.hits == 1, 'one model request count')
        class Groups(ast.NodeTransformer):
            hits = 0
            def visit_List(self, node):
                node = self.generic_visit(node)
                keep = []
                for value in node.elts:
                    if isinstance(value, ast.Tuple) and len(value.elts) == 2 and isinstance(value.elts[0], ast.Constant) and value.elts[0].value == 'agent':
                        self.hits += 1
                        keep.append(ast.parse("('settings', ['layoutExact', 'pagesPreserved', 'aiReturn', 'reloadExact', 'fullscreenRestored'])", mode='eval').body)
                    else:
                        keep.append(value)
                node.elts = keep
                return node
        edit = Groups(); tree = edit.visit(tree)
        _need(edit.hits == 1, 'one624 Agent group replaced with retained settings layout proof')
        tree = _lists(tree, {'stopped'})

    if name == 'mouse633-owner-feedback-evidence.py':
        tree = _lists(tree, {'restoreAgent', 'agent', '.home-agent-open', '.ai-preset-card[data-ai-url="mouse://agent"]',
                            '#settings-dialog [data-action="assistant"]', 'mouse-633-agent-onboarding.png'})
        tree.body.remove(_function(tree, 'agent_contract'))
        tree = _replace(tree, 'agent = agent_contract(facts)', '')
        tree = _replace(tree, "isinstance(rows, list) and len(rows) == 17 and len({row.get('filename') for row in rows}) == 17",
                        "isinstance(rows, list) and len(rows) == 16 and len({row.get('filename') for row in rows}) == 16", expression=True)
        fn = _function(tree, 'verify')
        result = [n.value for n in fn.body if isinstance(n, ast.Return)]
        _need(len(result) == 1 and isinstance(result[0], ast.Dict), '633 return')
        value = result[0]; indices = [i for i, key in enumerate(value.keys) if isinstance(key, ast.Constant) and key.value == 'agent']
        _need(len(indices) == 1, '633 obsolete result field')
        del value.keys[indices[0]]; del value.values[indices[0]]

    if name == 'mouse636-owner-feedback-evidence.py':
        tree = _strings(tree, {'mouse637-agent-inline-evidence.py': 'mouse637-agent-removal-evidence.py', 'agentInline': 'agentRemoval'})

    if name == 'mouse636-feedback-evidence.py':
        tree = _replace(tree, "flags(facts.get('agentAvailability'), ('settingsEntry', 'startEntry', 'providerEntry', 'openedExplicitly', 'disabledUntilEnabled', 'closed', 'pagesPreserved', 'layoutPreserved', 'restoredAfterReload'), 'restored Agent')",
                        "flags(facts.get('workspaceReload'), ('pagesPreserved', 'layoutPreserved'), 'retained workspace reload')")
        fn = _function(tree, 'verify_footer'); result = [n.value for n in fn.body if isinstance(n, ast.Return)]
        fn.body[-1:-1] = ast.parse("""
frames = facts['workspaceReload'].get('shellFrames', {})
before, after = frames.get('before', {}), frames.get('after', {})
need(type(before.get('timeOrigin')) in (int, float) and type(after.get('timeOrigin')) in (int, float)
     and after['timeOrigin'] > before['timeOrigin'] > 0
     and before.get('detached') is False and after.get('detached') is False,
     'retained browser settings did not reload the shell while preserving pages/layout')
""").body
        _need(len(result) == 1 and isinstance(result[0], ast.Dict), 'footer return')
        value = result[0]; indices = [i for i, key in enumerate(value.keys) if isinstance(key, ast.Constant) and key.value == 'agentRestored']
        _need(len(indices) == 1, 'footer Agent result')
        del value.keys[indices[0]]; del value.values[indices[0]]

    if name == 'mouse633-linux-evidence.py':
        tree = _replace(tree, "terminal = native_checks.get('nativeRuntime', {})", '')
        tree = _replace(tree, "need(positive(terminal.get('terminalPid')) and terminal.get('terminalExitCode') == 0 and 'MOUSE_LINUX_PTY_OK' in terminal.get('terminalOutput', '') and terminal.get('nativeFileRead') is True, 'packaged native PTY/files module did not run')", '')

    return ast.fix_missing_locations(tree)
