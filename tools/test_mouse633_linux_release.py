#!/usr/bin/env python3
"""Synthetic publisher policy fixtures only; no package/native/publication claims."""
import base64
import copy
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

P = runpy.run_path(str(Path(__file__).with_name('mouse633-linux-release.py')))


def fixture():
    return {'version':'6.0.33','ready':True,'sourceBranch':'main','previous':None,
            'source':'1'*40,'sourceMerge':'2'*40,'sourcePR':1,'run':2,'attempt':1,'job':3,
            'artifact':4,'artifactSHA256':'a'*64,'verificationArtifact':5,'verificationSHA256':'b'*64,
            'packages':{name:{'size':100*1024**2,'sha256':digest*64}
                        for name,digest in zip(P['PACKAGES'],('c','d'))}}


class LinuxPins(unittest.TestCase):
    def invoke(self, value, owner='Publish verified Mouse Browser 6.0.33 Linux x64'):
        with tempfile.TemporaryDirectory(prefix='mouse633-linux-pin-fixture-') as directory:
            stage=Path(directory)
            (stage/'pin.json').write_text(json.dumps(value))
            (stage/'RELEASE_NOTES.md').write_text('# Mouse Browser 6.0.33\nSynthetic unit fixture\n')
            if owner is not None: (stage/'PUBLISH_OWNER').write_text(owner)
            with patch.dict(P['pin'].__globals__,STAGE=stage):return P['pin']()

    def test_exact_complete_synthetic_pin_is_accepted(self):
        self.assertEqual(self.invoke(fixture()),fixture())

    def test_unknown_source_provenance_cannot_publish(self):
        for name in ('source','sourceMerge','sourcePR','run','attempt','job','artifact','artifactSHA256','verificationArtifact','verificationSHA256'):
            value=fixture();value[name]=None
            with self.subTest(name=name),self.assertRaises(ValueError):self.invoke(value)

    def test_linux_has_no_invented_prior_release(self):
        for prior in ({},'6.0.32',{'version':'6.0.32','platform':'win32'}):
            value=fixture();value['previous']=prior
            with self.subTest(prior=prior),self.assertRaisesRegex(ValueError,'no invented baseline'):self.invoke(value)

    def test_missing_and_wrong_owner_cannot_publish(self):
        for owner in ('', 'Publish verified Mouse Browser 6.0.33 Windows x64',None):
            with self.subTest(owner=owner),self.assertRaises((ValueError,FileNotFoundError)):self.invoke(fixture(),owner)

    def test_both_formats_and_exact_names_are_required(self):
        for name in P['PACKAGES']:
            value=fixture();value['packages'].pop(name)
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'both Linux'):self.invoke(value)
        value=fixture();value['packages']['invented.rpm']=value['packages'].pop(P['DEB'])
        with self.assertRaisesRegex(ValueError,'both Linux'):self.invoke(value)

    def test_unready_template_cannot_contain_owner_or_provenance(self):
        root=P['ROOT'];value=json.loads((root/'staging/mouse/6.0.33-linux-x64/pin.json').read_text())
        if value['ready'] is False:
            self.assertTrue(all(value.get(key) is None for key in ('source','sourceMerge','artifact','job')))
            with self.assertRaisesRegex(ValueError,'not ready'):self.invoke(value,None)
        value=fixture();value['ready']=False
        with self.assertRaisesRegex(ValueError,'unready provenance'):self.invoke(value,None)


class LinuxSourceProvenance(unittest.TestCase):
    def setUp(self):
        self.pin=fixture();p=self.pin
        self.run={'head_sha':p['source'],'path':'.github/workflows/mouse-linux.yml','run_attempt':1,'status':'completed','conclusion':'success'}
        names=['Run retained and Linux Mouse contracts','Build Linux AppImage and deb',
               'Verify installed Linux packages and native behavior','Bind verified Linux packages to source evidence']
        self.job={'id':3,'name':'mouse-linux-x64','run_id':2,'run_attempt':1,'head_sha':p['source'],'status':'completed','conclusion':'success',
                  'started_at':'2020-01-01T00:00:00Z','completed_at':'2020-01-01T00:30:00Z',
                  'steps':[{'name':name,'status':'completed','conclusion':'success'} for name in names]}
        self.pr={'merged':True,'head':{'sha':p['source']},'base':{'ref':'main'},'merge_commit_sha':p['sourceMerge']}
        self.ancestry={'status':'ahead','behind_by':0}

    def invoke(self):
        def api(repo,path):
            self.assertEqual(repo,'jeep-jim/OSMINOG')
            if path=='actions/runs/2':return self.run
            if path=='actions/runs/2/attempts/1/jobs?per_page=100':return {'jobs':[self.job]}
            if path=='pulls/1':return self.pr
            return self.ancestry
        with patch.dict(P['verify_source'].__globals__,api=api):return P['verify_source'](self.pin)

    def test_exact_successful_linux_source_job_is_required(self):self.assertEqual(self.invoke(),self.job)

    def test_another_os_run_or_other_attempt_cannot_supply_linux(self):
        for key,value in [('path','.github/workflows/mouse-windows.yml'),('run_attempt',2),('head_sha','9'*40),('conclusion','failure'),('status','in_progress')]:
            original=self.run[key];self.run[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.invoke()
            self.run[key]=original

    def test_missing_installed_step_or_unfinished_job_is_rejected(self):
        for index in range(4):
            self.job['steps'][index]['conclusion']='skipped'
            with self.subTest(index=index),self.assertRaisesRegex(ValueError,'native gates'):self.invoke()
            self.job['steps'][index]['conclusion']='success'
        self.job['run_attempt']=2
        with self.assertRaisesRegex(ValueError,'provenance'):self.invoke()

    def test_merged_source_and_main_ancestry_are_mandatory(self):
        self.pr['merged']=False
        with self.assertRaisesRegex(ValueError,'merged'):self.invoke()
        self.pr['merged']=True;self.ancestry['behind_by']=1
        with self.assertRaisesRegex(ValueError,'ancestor'):self.invoke()

    def test_artifact_must_belong_to_exact_source_attempt_window(self):
        item={'workflow_run':{'id':2,'head_sha':self.pin['source']},'created_at':'2020-01-01T00:20:00Z'}
        P['artifact_from_job'](item,self.pin,self.job)
        item['created_at']='2020-01-01T01:00:00Z'
        with self.assertRaisesRegex(ValueError,'outside'):P['artifact_from_job'](item,self.pin,self.job)
        item['created_at']='2020-01-01T00:20:00Z';item['workflow_run']['head_sha']='8'*40
        with self.assertRaisesRegex(ValueError,'source/run'):P['artifact_from_job'](item,self.pin,self.job)


class LinuxFinalBytes(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='mouse633-linux-bytes-fixture-');self.addCleanup(self.temp.cleanup)
        self.out=Path(self.temp.name);self.pin=fixture()
        for name in P['PACKAGES']:
            raw=('synthetic-'+name).encode();(self.out/name).write_bytes(raw)
            self.pin['packages'][name]={'size':len(raw),'sha256':P['sha'](raw)}
        (self.out/'SHA256SUMS.txt').write_text(''.join(self.pin['packages'][n]['sha256']+'  '+n+'\n' for n in P['PACKAGES']))

    def test_same_size_modified_bytes_fail_before_any_public_operation(self):
        for command in ('publish','channel'):
            for name in P['PACKAGES']:
                raw=(self.out/name).read_bytes();(self.out/name).write_bytes(b'X'+raw[1:])
                with self.subTest(command=command,name=name),patch.dict(P[command].__globals__,OUT=self.out,pin=lambda:self.pin,api=lambda *a,**k:self.fail('public API called before byte gate'),find_release=lambda p:self.fail('release lookup before bytes')):
                    with self.assertRaisesRegex(ValueError,'package bytes'):P[command]()
                (self.out/name).write_bytes(raw)

    def test_declared_checksum_cannot_omit_the_deb(self):
        (self.out/'SHA256SUMS.txt').write_text(self.pin['packages'][P['APPIMAGE']]['sha256']+'  '+P['APPIMAGE']+'\n')
        with patch.dict(P['verify_packages'].__globals__,OUT=self.out),self.assertRaisesRegex(ValueError,'checksums'):
            P['verify_packages'](self.pin)

    def test_same_version_metadata_and_downgrades_cannot_be_overwritten(self):
        for previous in ({'version':'6.0.33','url':'old'},{'version':'6.0.34','url':'old'}):
            calls=[]
            def api(repo,path,method='GET',payload=None,missing=False):
                calls.append(method);return {'sha':'old','content':base64.b64encode(json.dumps(previous).encode()).decode()}
            with patch.dict(P['put_json'].__globals__,api=api),self.assertRaises(ValueError):
                P['put_json']('platforms/linux/mouse-x64/latest.json',{'version':'6.0.33','url':'new'})
            self.assertEqual(calls,['GET'])

    def test_public_channel_paths_are_platform_isolated(self):
        self.assertEqual(P['CHANNEL_PATH'],'platforms/linux/mouse-x64/latest.json')
        workflow=(P['ROOT']/'.github/workflows/publish-mouse633-linux.yml').read_text()
        self.assertIn('branches: [main]',workflow)
        self.assertIn("paths: ['staging/mouse/6.0.33-linux-x64/PUBLISH_OWNER', '.github/workflows/publish-mouse633-linux.yml']",workflow)
        self.assertIn('needs: contract',workflow)
        self.assertIn('cancel-in-progress: false',workflow)
        self.assertIn('dbus-run-session -- xvfb-run',workflow)
        self.assertNotIn('--no-sandbox',workflow)


if __name__=='__main__':unittest.main()
