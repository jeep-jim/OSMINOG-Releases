#!/usr/bin/env python3
"""Run byte-frozen633 algorithms against634 facts; never rewrite evidence."""
import runpy
from pathlib import Path
_reuse = runpy.run_path(str(Path(__file__).with_name('mouse634-reuse.py')))
_retained = _reuse['load']('test_mouse633_owner_feedback_evidence.py', namespace=globals())
globals().update({key: value for key, value in _retained.items() if not key.startswith('__')})

def full_composition634(self):
 module=runpy.run_path(str(Path(__file__).with_name('test_mouse634_feedback_evidence.py')))
 files,facts=module['fixtures']();owner_files,owner=fixture();files.update(owner_files)
 geometry=runpy.run_path(str(Path(__file__).with_name('test_mouse634_workspace_evidence.py')))
 workspace_files,workspace=geometry['fixture']('win32');files.update(workspace_files)
 current=runpy.run_path(str(Path(__file__).with_name('test_mouse634_owner_feedback_evidence.py')))
 current_files,current_facts,refresh=current['fixture']('win32');files.update(current_files)
 for name,value in facts.items():files[name]=json.dumps(value).encode()
 files[E['NAME']]=json.dumps(owner).encode();files['mouse-629-ui-regressions.json']=json.dumps(workspace).encode()
 result=module['CURRENT'].verify(files.__getitem__,expected_platform='win32',expected_arch='x64')
 self.assertEqual(result['documents']['unchangedOriginalFiles'],9);self.assertTrue(result['owner']['ok']);self.assertTrue(result['owner634']['ok']);self.assertTrue(result['owner']['contextMenu']['ok']);self.assertEqual(len(result['inputs']),7);self.assertEqual(result['workspaceGeometry']['scenes'],6)
 del workspace['workspace633'];files['mouse-629-ui-regressions.json']=json.dumps(workspace).encode()
 with self.assertRaisesRegex(ValueError,'workspace geometry'):module['CURRENT'].verify(files.__getitem__,expected_platform='win32',expected_arch='x64')

CurrentOwnerEvidence.test_full_composition_runs_owner_and_retained_verifiers_without_mocks=full_composition634

if __name__=='__main__':unittest.main()
