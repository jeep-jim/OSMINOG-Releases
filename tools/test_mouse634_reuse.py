#!/usr/bin/env python3
"""Fail-closed634 adapter/pipeline contracts; all fixtures are synthetic."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import runpy
import unittest
ROOT=Path(__file__).resolve().parents[1]
R=runpy.run_path(str(ROOT/'tools/mouse634-reuse.py'))


class Reuse634(unittest.TestCase):
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
  for folder in ('6.0.34-arm64','6.0.34-windows-x64','6.0.34-linux-x64'):
   path=ROOT/'staging/mouse'/folder;value=json.loads((path/'pin.json').read_text());self.assertIs(value['ready'],False);self.assertEqual(value['version'],'6.0.34');self.assertFalse((path/'PUBLISH_OWNER').exists())
   for key in ('source','sourceMerge','sourcePR','run','artifact','verificationArtifact'):self.assertIsNone(value[key])
   packages=value.get('packages') or {value['package']['name']:{key:value['package'][key] for key in ('size','sha256')}}
   self.assertTrue(all(row=={'size':None,'sha256':None} for row in packages.values()))
 def test_unknown_archive_and_native_evidence_cannot_set_ready(self):
  linux=runpy.run_path(str(ROOT/'tools/mouse634-linux-release.py'));self.assertEqual(linux['validate_template']()['previous'],linux['PREVIOUS'])
  with self.assertRaisesRegex(ValueError,'not ready'):linux['pin']()


if __name__=='__main__':unittest.main()
