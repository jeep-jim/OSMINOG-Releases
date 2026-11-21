#!/usr/bin/env python3
"""Retain byte-frozen634 algorithms with explicit635 identities."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name("mouse635-reuse.py")))
_reuse["load"]('test_mouse634_retained_owner_evidence.py',namespace=globals())


def full_composition635(self):
 module=runpy.run_path(str(Path(__file__).with_name('test_mouse635_feedback_evidence.py')))
 files,facts=module['fixtures']();owner_files,owner=fixture();files.update(owner_files)
 geometry=runpy.run_path(str(Path(__file__).with_name('test_mouse635_workspace_evidence.py')))
 workspace_files,workspace=geometry['fixture']('win32');files.update(workspace_files)
 retained=runpy.run_path(str(Path(__file__).with_name('test_mouse635_retained_owner_evidence.py')))
 retained_files,retained_facts,refresh=retained['fixture']('win32');files.update(retained_files)
 current=runpy.run_path(str(Path(__file__).with_name('test_mouse635_owner_feedback_evidence.py')))
 current_files,current_facts,wrapper=current['fixture']('win32')
 wrapper_name='mouse-windows-verification.json'
 if wrapper_name in files:
  preserved=json.loads(files[wrapper_name]);preserved.setdefault('checks',{}).update(wrapper['checks'])
  current_files[wrapper_name]=json.dumps(preserved).encode()
 files.update(current_files)
 for name,value in facts.items():files[name]=json.dumps(value).encode()
 files[E['NAME']]=json.dumps(owner).encode();files['mouse-629-ui-regressions.json']=json.dumps(workspace).encode()
 result=module['CURRENT'].verify(files.__getitem__,expected_platform='win32',expected_arch='x64')
 self.assertEqual(result['documents']['unchangedOriginalFiles'],9);self.assertTrue(result['owner']['ok']);self.assertTrue(result['owner634']['ok']);self.assertTrue(result['owner635']['ok']);self.assertTrue(result['owner635']['agentChat']['ok']);self.assertTrue(result['owner']['contextMenu']['ok']);self.assertEqual(result['workspaceGeometry']['scenes'],6)
 for name,digest in result['inputs'].items():self.assertEqual(digest,E['digest'](files[name]),name)
 for name in ('mouse-633-owner-feedback.json','mouse-634-owner-feedback.json','mouse-635-owner-feedback.json','mouse-635-library.json','mouse-635-public-search.json'):
  self.assertIn(name,result['inputs'])
 del workspace['workspace633'];files['mouse-629-ui-regressions.json']=json.dumps(workspace).encode()
 with self.assertRaisesRegex(ValueError,'workspace geometry'):module['CURRENT'].verify(files.__getitem__,expected_platform='win32',expected_arch='x64')


CurrentOwnerEvidence.test_full_composition_runs_owner_and_retained_verifiers_without_mocks=full_composition635

if __name__=="__main__":
 import unittest
 unittest.main()
