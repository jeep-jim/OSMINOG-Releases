#!/usr/bin/env python3
"""Retain byte-frozen634 algorithms with explicit635 identities."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name("mouse635-reuse.py")))
_reuse["load"]('test_mouse634_windows_release.py',namespace=globals())

# Current635 publishes each platform only after its own owner trigger and full
# pin validation. Retain every old branch/path/concurrency assertion, replacing
# only the old unconditional non-PR job selection with that stricter condition.
def _current_platform_publication_scope(self):
 workflow=(SCRIPT.parents[1]/'.github/workflows/publish-mouse635-windows.yml').read_text()
 push=workflow.split('  push:\n',1)[1].split('  workflow_dispatch:\n',1)[0]
 fields=dict(line.strip().split(': ',1) for line in push.splitlines() if line.strip())
 self.assertEqual(fields['branches'],'[main]')
 self.assertEqual(ast.literal_eval(fields['paths']),['staging/mouse/6.0.35-windows-x64/PUBLISH_OWNER','.github/workflows/publish-mouse635-windows.yml'])
 publisher=workflow.split('  publish-windows:\n',1)[1]
 for gate in ["    if: github.event_name != 'pull_request' && needs.contract.outputs.publish == 'true'\n",'    needs: contract\n','      group: mouse-windows-x64-release\n','      cancel-in-progress: false\n']:
  self.assertIn(gate,publisher)
 self.assertIn('      publish: ${{ steps.publish_plan.outputs.publish }}\n',workflow)
 self.assertIn('python3 tools/mouse635-publish-plan.py windows-x64 >> "$GITHUB_OUTPUT"',workflow)

WindowsCanonicalCheckout.test_pipeline_retry_is_scoped_to_this_windows_version_on_main=_current_platform_publication_scope

if __name__=="__main__":
 import unittest
 unittest.main()
