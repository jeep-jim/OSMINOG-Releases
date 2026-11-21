#!/usr/bin/env python3
"""Fail-closed635 adapter/pipeline contracts; all fixtures are synthetic."""
import ast
import copy
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
R=runpy.run_path(str(ROOT/'tools/mouse635-reuse.py'))
PUBLISHERS=(
 ('6.0.35-arm64','mouse635-release.py','validate','Mouse Browser 6.0.35: publish pinned source and verified Mac packages'),
 ('6.0.35-windows-x64','mouse635-windows-release.py','pin','Publish verified Mouse Browser 6.0.35 Windows x64'),
 ('6.0.35-linux-x64','mouse635-linux-release.py','pin','Publish verified Mouse Browser 6.0.35 Linux x64'),
)
CLAIMS={'source':'a'*40,'sourceMerge':'b'*40,'sourcePR':1,'run':2,'artifact':3,'verificationArtifact':4,
        'sourceAttempt':1,'sourceJob':5,'attempt':1,'job':5,'archiveSHA256':'c'*64,
        'artifactSHA256':'c'*64,'verificationSHA256':'d'*64}
REQUIRED_CLAIMS=('source','sourceMerge','sourcePR','run','artifact','verificationArtifact')


def pin_fixture(folder,ready=False):
 value=json.loads((ROOT/'staging/mouse'/folder/'pin.json').read_text())
 value['ready']=ready
 for key,claim in CLAIMS.items():
  if key in value:value[key]=claim if ready else None
 packages=value.get('packages') or {'installer':value['package']}
 for row in packages.values():row.update(size=150*1024**2 if ready else None,sha256='e'*64 if ready else None)
 return value


@contextmanager
def isolated_stage(publisher,folder,value,owner=None):
 # Only the static notes/schema are copied; pin/owner are explicit test inputs.
 with tempfile.TemporaryDirectory(prefix='mouse635-contract-') as temporary:
  stage=Path(temporary)
  for name in ('RELEASE_NOTES.md','evidence.schema.json'):
   source=ROOT/'staging/mouse'/folder/name
   if source.is_file():(stage/name).write_bytes(source.read_bytes())
  (stage/'pin.json').write_text(json.dumps(value)+'\n')
  if owner is not None:(stage/'PUBLISH_OWNER').write_text(owner+'\n')
  check=publisher['validate' if folder.endswith('arm64') else 'pin']
  bindings={'STAGE':stage}
  if folder.endswith('arm64'):bindings['PIN']=value
  # runpy's returned dict is a copy: patch the actual callable globals.
  with patch.dict(check.__globals__,bindings):yield stage,check


class Reuse635(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.publishers={folder:runpy.run_path(str(ROOT/'tools'/module)) for folder,module,_,_ in PUBLISHERS}
 def assert_unready(self,path,value):
  self.assertIs(value['ready'],False);self.assertEqual(value['version'],'6.0.35');self.assertFalse((path/'PUBLISH_OWNER').exists())
  for key in REQUIRED_CLAIMS:self.assertIsNone(value[key],key)
  for key in CLAIMS:
   if key not in REQUIRED_CLAIMS and key in value:self.assertIsNone(value[key],key)
  packages=value.get('packages') or {value['package']['name']:{key:value['package'][key] for key in ('size','sha256')}}
  self.assertTrue(all(row=={'size':None,'sha256':None} for row in packages.values()))
 def test_exact_frozen634_bytes_and_transitive_gates(self):
  for name,digest in R['FROZEN'].items():self.assertEqual(hashlib.sha256(R['checked'](name)).hexdigest(),digest,name)
  with self.assertRaises(ValueError):R['checked']('unreviewed.py')
  old=R['legacy']()
  for name,digest in old['FROZEN'].items():self.assertEqual(hashlib.sha256(old['checked'](name)).hexdigest(),digest,name)
 def test_frozen_algorithm_ast_changes_only_identity_constants_and_baselines(self):
  class NeutralStrings(ast.NodeTransformer):
   def visit_Constant(self,node):
    if isinstance(node.value,str):node.value='IDENTITY'
    return node
   def visit_Assign(self,node):
    if any(isinstance(t,ast.Name) and t.id in ('BASELINES','PREVIOUS') for t in node.targets):node.value=ast.Constant('IMMUTABLE_PREDECESSOR')
    return self.generic_visit(node)
  for name in R['FROZEN']:
   if name.startswith('test') or name=='mouse634-reuse.py':continue
   original=ast.parse(R['checked'](name));current=R['adapted_tree'](name)
   self.assertEqual(ast.dump(NeutralStrings().visit(original)),ast.dump(NeutralStrings().visit(current)),name)
  for name in ('mouse632-evidence.py','mouse632-windows-release.py','mouse633-feedback-evidence.py','mouse633-linux-evidence.py'):
   old=R['legacy']()['adapted_tree'](name);current=R['adapted_tree'](name)
   self.assertEqual(ast.dump(NeutralStrings().visit(old)),ast.dump(NeutralStrings().visit(current)),name)
 def test_retained_raw_names_and_new_native_namespace(self):
  retained=R['load']('mouse634-owner-feedback-evidence.py');self.assertEqual(retained['NAME'],'mouse-634-owner-feedback.json');self.assertEqual(retained['N']['VERSION'],'6.0.35');self.assertEqual(retained['S']['NAME'],'mouse-635-search.json')
  older=R['load']('mouse634-retained-owner-evidence.py');self.assertEqual(older['NAME'],'mouse-633-owner-feedback.json')
  for current,pattern in [(False,r'mouse-(?:634-|635-search-)[a-z0-9-]+\.png'),(True,r'mouse-635-[a-z0-9-]+\.png')]:
   values=[n.value for n in ast.walk(R['adapted_tree']('mouse634-native-evidence.py',current_native=current)) if isinstance(n,ast.Constant)]
   self.assertIn(pattern,values)
  native=R['load']('mouse634-upgrade-evidence.py');self.assertEqual(native['BASELINES'],R['BASELINES'])
  values=[n.value for n in ast.walk(R['adapted_tree']('mouse634-upgrade-evidence.py')) if isinstance(n,ast.Constant)];self.assertIn('6.0.34',values);self.assertIn('6.0.35',values)
 def test_task_checker_is_full_source_form_with_unchanged_native_predicates(self):
  # All three actual importers require exact source-file bytes. A runpy-only
  # adapter can pass unit verification yet is never equal to that source file.
  original=R['adapted_tree']('mouse634-task-evidence.py')
  current=ast.parse((ROOT/'tools/mouse635-task-evidence.py').read_bytes())
  class WithoutApprovedPNGDecoder(ast.NodeTransformer):
   def visit_FunctionDef(self,node):
    if node.name=='decode_png':node.body=[ast.Pass()]
    return node
  self.assertEqual(ast.dump(WithoutApprovedPNGDecoder().visit(original)),ast.dump(WithoutApprovedPNGDecoder().visit(current)))
  for module in ('mouse632-release.py','mouse632-windows-release.py','mouse633-linux-release.py'):
   tree=R['adapted_tree'](module);fn=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='import_candidate')
   text=ast.unparse(fn)
   self.assertIn('tools/mouse-631-acceptance.py',text)
   self.assertIn("with_name('mouse635-task-evidence.py').read_bytes()",text)
 def test_source_and_fresh_publisher_paths_require_composed_feedback_and_upgrade(self):
  current=runpy.run_path(str(ROOT/'tools/mouse635-feedback-evidence.py'));self.assertNotEqual(current['verify'],current['_verify_634'])
  for name in ('mouse632-windows-release.py','mouse633-release.py','mouse634-linux-release.py'):
   constants=[n.value for n in ast.walk(R['adapted_tree'](name)) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
   self.assertTrue(any('mouse635-' in value for value in constants),name)
  tree=R['adapted_tree']('mouse632-windows-release.py')
  for name in ('import_candidate','verify_installed','publish'):
   fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
   self.assertEqual(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_verify_current_upgrade' for n in ast.walk(fn)),1,name)
 def test_version_scoped_pipeline_and_key_only_in_installed_step(self):
  for suffix,stage in [('', '6.0.35-arm64'),('-windows','6.0.35-windows-x64'),('-linux','6.0.35-linux-x64')]:
   name='publish-mouse635'+suffix+'.yml';text=(ROOT/'.github/workflows'/name).read_text()
   self.assertIn("paths: ['staging/mouse/"+stage+"/PUBLISH_OWNER', '.github/workflows/"+name+"']",text)
   for token in ('branches: [main]','needs: contract','cancel-in-progress: false',"if: github.event_name != 'pull_request'",'test_mouse635_633_owner_evidence.py','test_mouse635_retained_owner_evidence.py','test_mouse635_owner_feedback_evidence.py','test_mouse635_search_evidence.py','test_mouse635_public_search_evidence.py','test_mouse635_library_evidence.py'):self.assertIn(token,text)
   self.assertNotIn('--no-sandbox',text);self.assertLessEqual(text.count('MOUSE_TEST_BRAVE_SEARCH_API_KEY:'),1)
   for step in (chunk for chunk in text.split('      - name: ') if 'MOUSE_TEST_BRAVE_SEARCH_API_KEY:' in chunk):
    self.assertTrue(step.startswith(('Verify installed DMG','Verify exact installer','Verify exact packages')));self.assertIn('${{ secrets.BRAVE_SEARCH_API_KEY }}',step)
  win=(ROOT/'.github/workflows/publish-mouse635-windows.yml').read_text().split('  publish-windows:',1)[1];self.assertLess(win.index('core.autocrlf false'),win.index('actions/checkout'))
  linux=(ROOT/'.github/workflows/publish-mouse635-linux.yml').read_text();self.assertIn('-screen 0 1600x1100x24',linux);self.assertIn('libxext6',linux)
 def test_unready_templates_cannot_claim_provenance_or_trigger_publication(self):
  for folder,_,_,_ in PUBLISHERS:
   with self.subTest(folder=folder),isolated_stage(self.publishers[folder],folder,pin_fixture(folder)) as (path,check):
    self.assert_unready(path,json.loads((path/'pin.json').read_text()))
    with self.assertRaisesRegex(ValueError,'not ready'):check()
 def test_unknown_archive_and_native_evidence_cannot_set_ready(self):
  folder='6.0.35-linux-x64';linux=self.publishers[folder]
  with isolated_stage(linux,folder,pin_fixture(folder)) as (_,check):
   self.assertEqual(linux['validate_template']()['previous'],linux['PREVIOUS'])
   with self.assertRaisesRegex(ValueError,'not ready'):check()
 def test_unready_claims_and_owner_are_always_rejected(self):
  for folder,_,_,owner in PUBLISHERS:
   publisher=self.publishers[folder]
   for claim in ('source','owner'):
    value=pin_fixture(folder)
    if claim=='source':value['source']='a'*40
    with self.subTest(folder=folder,claim=claim),isolated_stage(publisher,folder,value,owner if claim=='owner' else None) as (_,check):
     if 'validate_template' in publisher:
      with self.assertRaises(ValueError):publisher['validate_template']()
     with self.assertRaises(ValueError):check()
 def test_checked_in_stages_validate_their_declared_readiness(self):
  for folder,_,entry,_ in PUBLISHERS:
   with self.subTest(folder=folder):
    path=ROOT/'staging/mouse'/folder;value=json.loads((path/'pin.json').read_text());check=self.publishers[folder][entry]
    if value['ready'] is True:check()
    else:
     self.assert_unready(path,value)
     with self.assertRaisesRegex(ValueError,'not ready'):check()
 def test_corrupt_ready_provenance_and_owner_are_rejected(self):
  for folder,_,_,owner in PUBLISHERS:
   publisher=self.publishers[folder];value=pin_fixture(folder,ready=True)
   with self.subTest(folder=folder,state='valid synthetic ready'),isolated_stage(publisher,folder,value,owner) as (_,check):check()
   archive='archiveSHA256' if folder.endswith('arm64') else 'artifactSHA256'
   for key in ('source',archive,'verificationSHA256','artifact','verificationArtifact','owner'):
    broken=copy.deepcopy(value)
    if key!='owner':broken[key]=0 if isinstance(broken[key],int) else ''
    with self.subTest(folder=folder,corrupt=key),isolated_stage(publisher,folder,broken,'wrong owner' if key=='owner' else owner) as (_,check):
     with self.assertRaises(ValueError):check()


if __name__=='__main__':unittest.main()
