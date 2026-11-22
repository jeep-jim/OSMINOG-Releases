"""Publisher environment contract; this does not simulate native acceptance."""
from pathlib import Path
import re
import shlex
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/publish-mouse637-linux.yml'
STEP = 'Prepare native Linux desktop dependencies'


def require_native_window_dependencies(workflow):
    # The exact source002 mouse-637-update-window.py uses xprop WM_STATE to
    # identify the owned managed X11 window before focus or native input.
    # Ubuntu22.04 ships /usr/bin/xprop in x11-utils:
    # https://packages.ubuntu.com/jammy/amd64/x11-utils/filelist
    pattern = (r'^      - name: ' + re.escape(STEP)
               + r'\n        run: \|\n(?P<script>(?:          .*\n)*)')
    matches = list(re.finditer(pattern, workflow, re.MULTILINE))
    if len(matches) != 1:
        raise AssertionError('Expected one named native Linux dependency run block')
    script = '\n'.join(line[10:] for line in matches[0]['script'].splitlines())
    packages = set()
    for line in script.replace('\\\n', ' ').splitlines():
        words = shlex.split(line, comments=True)
        if words[:3] == ['sudo', 'apt-get', 'install']:
            packages.update(word for word in words[3:] if not word.startswith('-'))
    if 'x11-utils' not in packages:
        raise AssertionError('Native X11 owned-window verification requires xprop; '
                             'install x11-utils in the Linux dependency step')


class LinuxNativeDependencies(unittest.TestCase):
    def workflow(self):
        return WORKFLOW.read_text(encoding='utf-8')

    def test_actual_publisher_installs_required_window_ownership_tool(self):
        require_native_window_dependencies(self.workflow())

    def test_missing_package_is_rejected(self):
        missing = self.workflow().replace(' x11-utils', '')
        with self.assertRaisesRegex(AssertionError, 'requires xprop'):
            require_native_window_dependencies(missing)

    def test_comment_or_other_step_cannot_supply_the_dependency(self):
        missing = self.workflow().replace(' x11-utils', '')
        variants = {
            'comment': missing.replace('          sudo apt-get update',
                                       '          # x11-utils supplies xprop\n          sudo apt-get update'),
            'other step': missing + '\n      - name: Unrelated\n        run: |\n          sudo apt-get install -y x11-utils\n',
        }
        for kind, workflow in variants.items():
            with self.subTest(kind=kind), self.assertRaisesRegex(AssertionError, 'requires xprop'):
                require_native_window_dependencies(workflow)


if __name__ == '__main__':
    unittest.main()
