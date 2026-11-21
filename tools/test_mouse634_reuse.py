#!/usr/bin/env python3
"""Fail-closed634 adapter/pipeline contracts; all fixtures are synthetic."""
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
R=runpy.run_path(str(ROOT/'tools/mouse634-reuse.py'))
PUBLISHERS=(
 ('6.0.34-arm64','mouse634-release.py','validate','Mouse Browser 6.0.34: publish pinned source and verified Mac packages'),
 ('6.0.34-windows-x64','mouse634-windows-release.py','pin','Publish verified Mouse Browser 6.0.34 Windows x64'),
 ('6.0.34-linux-x64','mouse634-linux-release.py','pin','Publish verified Mouse Browser 6.0.34 Linux x64'),
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
 with tempfile.TemporaryDirectory(prefix='mouse634-contract-') as temporary:
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


class Reuse634(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.publishers={folder:runpy.run_path(str(ROOT/'tools'/module)) for folder,module,_,_ in PUBLISHERS}
 def assert_unready(self,path,value):
  self.assertIs(value['ready'],False);self.assertEqual(value['version'],'6.0.34');self.assertFalse((path/'PUBLISH_OWNER').exists())
  for key in REQUIRED_CLAIMS:self.assertIsNone(value[key],key)
  for key in CLAIMS:
   if key not in REQUIRED_CLAIMS and key in value:self.assertIsNone(value[key],key)
  packages=value.get('packages') or {value['package']['name']:{key:value['package'][key] for key in ('size','sha256')}}
  self.assertTrue(all(row=={'size':None,'sha256':None} for row in packages.values()))
 def test_every_frozen633_dependency_keeps_its_exact_published_bytes(self):
  for name,digest in R['FROZEN'].items():self.assertEqual(hashlib.sha256(R['checked'](name)).hexdigest(),digest,name)
  with self.assertRaises(ValueError):R['checked']('unreviewed.py')
 def test_historical_fixture_routes_and_native_filenames_are_not_relabelled(self):
  ui=R['load']('mouse632-ui-evidence.py')
  constants=[n.value for n in ast.walk(R['adapted_tree']('mouse632-ui-evidence.py')) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
  self.assertTrue(any('/mouse632-encapsulated' in value for value in constants));self.assertFalse(any('/mouse633-encapsulated' in value or '/mouse634-encapsulated' in value for value in constants))
  oldowner=R['load']('mouse633-owner-feedback-evidence.py');self.assertEqual(oldowner['VERSION'],'6.0.34');self.assertEqual(oldowner['NAME'],'mouse-633-owner-feedback.json')
  owner_constants=[n.value for n in ast.walk(R['adapted_tree']('mouse633-owner-feedback-evidence.py')) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
  self.assertTrue(any('mouse633-known.bin' in value for value in owner_constants));self.assertFalse(any('mouse634-known.bin' in value for value in owner_constants))
 def test_only_two_explicitly_superseded_download_function_bodies_change(self):
  original=ast.parse((ROOT/'tools/mouse632-evidence.py').read_text());current=R['adapted_tree']('mouse632-evidence.py')
  class Restore(ast.NodeTransformer):
   def visit_Constant(self,node):
    if isinstance(node.value,str):node.value=node.value.replace('6.0.34','6.0.32').replace('mouse634-','mouse632-')
    return node
  old={n.name:ast.dump(n) for n in original.body if isinstance(n,ast.FunctionDef)};new={n.name:ast.dump(Restore().visit(n)) for n in current.body if isinstance(n,ast.FunctionDef)}
  self.assertEqual(set(old),set(new));self.assertEqual({k for k in old if old[k]!=new[k]},{'download_geometry','verify_feedback'})
 def test_current_composition_cannot_skip_either_owner_or_geometry(self):
  path=ROOT/'tools/mouse634-feedback-evidence.py';source=path.read_text();self.assertIn('_verify_preserved(read',source);self.assertIn("mouse634-owner-feedback-evidence.py",source)
  current=runpy.run_path(str(path));self.assertNotEqual(current['verify'],current['_verify_preserved'])
  linux=runpy.run_path(str(ROOT/'tools/mouse634-linux-evidence.py'));self.assertNotEqual(linux['verify'],linux['verify_preserved'])
  self.assertIn("_current634['verify_upgrade']",(ROOT/'tools/mouse634-linux-evidence.py').read_text())
  tree=R['adapted_tree']('mouse632-windows-release.py')
  for fn in ('import_candidate','verify_installed','publish'):
   node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==fn)
   self.assertEqual(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_verify_current_upgrade' for n in ast.walk(node)),1,fn)
 def test_current_footer_changes_only_search_label_count_and_action_order(self):
  original=ast.parse(R['checked']('mouse633-feedback-evidence.py'))
  current=R['adapted_tree']('mouse633-feedback-evidence.py')
  old=next(n for n in original.body if isinstance(n,ast.FunctionDef) and n.name=='verify_footer')
  new=next(n for n in current.body if isinstance(n,ast.FunctionDef) and n.name=='verify_footer')
  reverse={"row.get('count') == 6":"row.get('count') == 5",
           "row.get('actions') == ['tile-search', 'emoji', 'zoom', 'history', 'bookmarks', 'downloads']":
           "row.get('actions') == ['emoji', 'zoom', 'history', 'bookmarks', 'downloads']"}
  changed=set()
  for node in ast.walk(new):
   if isinstance(node,ast.Compare) and ast.unparse(node) in reverse:
    value=ast.unparse(node);changed.add(value)
    node.comparators=ast.parse(reverse[value],mode='eval').body.comparators
  self.assertEqual(changed,set(reverse))
  loop=next(n for n in new.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='row')
  label=ast.parse("need(row.get('label') == 'Поиск, эмодзи, история, закладки и загрузки', 'search footer accessible label differs')").body[0]
  self.assertEqual(ast.dump(loop.body.pop(0)),ast.dump(label))
  self.assertEqual(ast.dump(old),ast.dump(new))
 def test_version_scoped_pipelines_and_native_environment_are_preserved(self):
  for suffix,stage in [('', '6.0.34-arm64'),('-windows','6.0.34-windows-x64'),('-linux','6.0.34-linux-x64')]:
   name='publish-mouse634'+suffix+'.yml';text=(ROOT/'.github/workflows'/name).read_text()
   self.assertIn("paths: ['staging/mouse/"+stage+"/PUBLISH_OWNER', '.github/workflows/"+name+"']",text)
   for token in ('branches: [main]','needs: contract','cancel-in-progress: false',"if: github.event_name != 'pull_request'",'test_mouse634_owner_feedback_evidence.py','test_mouse634_retained_owner_evidence.py','test_mouse634_context_evidence.py'):self.assertIn(token,text)
   self.assertNotIn('--no-sandbox',text)
  win=(ROOT/'.github/workflows/publish-mouse634-windows.yml').read_text().split('  publish-windows:',1)[1];self.assertLess(win.index('core.autocrlf false'),win.index('actions/checkout'))
  linux=(ROOT/'.github/workflows/publish-mouse634-linux.yml').read_text();self.assertIn('-screen 0 1600x1100x24',linux);self.assertIn('libxext6',linux)
 def test_unready_templates_cannot_claim_provenance_or_trigger_publication(self):
  for folder,_,_,_ in PUBLISHERS:
   with self.subTest(folder=folder),isolated_stage(self.publishers[folder],folder,pin_fixture(folder)) as (path,check):
    self.assert_unready(path,json.loads((path/'pin.json').read_text()))
    with self.assertRaisesRegex(ValueError,'not ready'):check()
 def test_unknown_archive_and_native_evidence_cannot_set_ready(self):
  folder='6.0.34-linux-x64';linux=self.publishers[folder]
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
