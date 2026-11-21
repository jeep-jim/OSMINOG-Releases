#!/usr/bin/env python3
"""Platform publication selection, with synthetic pins and validator spies."""
import json
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
C=runpy.run_path(str(ROOT/'tools/mouse635-publish-plan.py'))


class PublishPlan(unittest.TestCase):
 def setUp(self):
  self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup);self.root=Path(self.temporary.name);self.validated=[]
 def stage(self,platform,ready=False,trigger=None):
  folder,module,entry,owner=C['PLATFORMS'][platform];path=self.root/'staging/mouse'/folder;path.mkdir(parents=True)
  value={'version':'6.0.35','ready':ready,'source':None,'run':None,'packages':{'package':{'size':None,'sha256':None}}};(path/'pin.json').write_text(json.dumps(value))
  if trigger is not None:(path/'PUBLISH_OWNER').write_text(owner if trigger is True else trigger)
  return path,value
 def loader(self,path):
  module=Path(path).name
  platform=next(key for key,value in C['PLATFORMS'].items() if value[1]==module);entry=C['PLATFORMS'][platform][2]
  return {entry:lambda:self.validated.append(platform)}
 def ready(self,platform):
  return C['publication_ready'](platform,root=self.root,load=self.loader)
 def test_only_mac_job_is_eligible_when_other_platforms_remain_unready(self):
  self.stage('macos-arm64',True,True);self.stage('windows-x64');self.stage('linux-x64')
  self.assertEqual({platform:self.ready(platform) for platform in C['PLATFORMS']},{'macos-arm64':True,'windows-x64':False,'linux-x64':False})
  self.assertEqual(self.validated,['macos-arm64'])
 def test_mac_selection_never_requires_sibling_platform_files_or_readiness(self):
  self.stage('macos-arm64',True,True);self.assertTrue(self.ready('macos-arm64'));self.assertEqual(self.validated,['macos-arm64'])
 def test_false_ready_never_calls_validator_or_authorizes_a_runner(self):
  self.stage('windows-x64');self.assertFalse(self.ready('windows-x64'));self.assertEqual(self.validated,[])
 def test_trigger_and_boolean_must_match_the_selected_platform(self):
  for platform in C['PLATFORMS']:
   with self.subTest(platform=platform):
    folder=C['PLATFORMS'][platform][0];path=self.root/'staging/mouse'/folder;path.mkdir(parents=True,exist_ok=True)
    for ready,trigger in [(False,True),(True,None),(True,'another platform'),('true',True)]:
     (path/'pin.json').write_text(json.dumps({'version':'6.0.35','ready':ready,'packages':{'package':{'size':None,'sha256':None}}}))
     owner=path/'PUBLISH_OWNER';owner.unlink(missing_ok=True)
     if trigger is not None:owner.write_text(C['PLATFORMS'][platform][3] if trigger is True else trigger)
     with self.assertRaises(ValueError):self.ready(platform)
  self.assertEqual(self.validated,[])
 def test_unready_stage_cannot_sneak_in_source_or_package_claims(self):
  path,value=self.stage('linux-x64')
  for mutate in [lambda p:p.__setitem__('source','a'*40),lambda p:p['packages']['package'].__setitem__('size',1),lambda p:p['packages']['package'].__setitem__('sha256','f'*64)]:
   broken=json.loads(json.dumps(value));mutate(broken);(path/'pin.json').write_text(json.dumps(broken))
   with self.assertRaises(ValueError):self.ready('linux-x64')
 def test_existing_full_pin_validator_failure_prevents_true_output(self):
  self.stage('macos-arm64',True,True)
  def loader(path):
   def failed():raise ValueError('actual immutable package pin invalid')
   return {'validate':failed}
  with self.assertRaisesRegex(ValueError,'immutable package'):C['publication_ready']('macos-arm64',root=self.root,load=loader)
 def test_all_workflows_gate_publish_on_their_own_checked_output(self):
  for suffix,platform,job in [('', 'macos-arm64','mouse-release'),('-windows','windows-x64','publish-windows'),('-linux','linux-x64','publish-linux')]:
   text=(ROOT/'.github/workflows'/('publish-mouse635'+suffix+'.yml')).read_text()
   contract,publish=text.split('  '+job+':',1)
   self.assertIn('publish: ${{ steps.publish_plan.outputs.publish }}',contract)
   self.assertIn('id: publish_plan',contract);self.assertIn('python3 tools/mouse635-publish-plan.py '+platform+' >> "$GITHUB_OUTPUT"',contract)
   self.assertIn("if: github.event_name != 'pull_request' && needs.contract.outputs.publish == 'true'",publish)
   self.assertIn('needs: contract',publish);self.assertIn('tools/test_mouse635_publish_plan.py -v',contract)
 def test_checked_in_deferred_platforms_remain_unready_without_owner_trigger(self):
  for platform in ('windows-x64','linux-x64'):
   stage=ROOT/'staging/mouse'/C['PLATFORMS'][platform][0];pin=json.loads((stage/'pin.json').read_text())
   if pin['ready'] is False:self.assertFalse(C['publication_ready'](platform));self.assertFalse((stage/'PUBLISH_OWNER').exists())


if __name__=='__main__':unittest.main()
