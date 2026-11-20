#!/usr/bin/env python3
"""Linux634 publication with immutable633 gates and actual633 baseline."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name('mouse634-reuse.py')))
_retained=_reuse['load']('mouse633-linux-release.py',namespace=globals())
globals().update({key:value for key,value in _retained.items() if not key.startswith('__')})
_current634=runpy.run_path(str(Path(__file__).with_name('mouse634-current.py')))
_upgrade634=runpy.run_path(str(Path(__file__).with_name('mouse634-upgrade-evidence.py')))
PREVIOUS={'version':'6.0.33','source':'0a3f8aab08356297b3b8982a081debbfa65d826d','updaterBlobSHA':'91ab363f926774825caf8055b2d3d81bf0d51264','packages':{item['name']:{'size':item['size'],'sha256':item['sha256']} for item in _upgrade634['BASELINES']['linux'].values()}}


def validate_template():
 p=json.loads((STAGE/'pin.json').read_text())
 need(p.get('version')==VERSION and type(p.get('ready')) is bool,'invalid template identity')
 need(p.get('sourceBranch')=='main' and p.get('previous')==PREVIOUS,'actual published633 Linux baseline differs')
 need(set(p.get('packages',{}))==set(PACKAGES),'both Linux formats must be pinned')
 need((STAGE/'RELEASE_NOTES.md').read_text().startswith('# Mouse Browser '+VERSION),'release notes identity')
 if p['ready'] is False:
  for key in ('source','sourceMerge','sourcePR','run','attempt','job','artifact','artifactSHA256','verificationArtifact','verificationSHA256'): need(p.get(key) is None,'unready provenance must be null: '+key)
  need(all(value=={'size':None,'sha256':None} for value in p['packages'].values()),'unready package claims must be null')
  need(not (STAGE/'PUBLISH_OWNER').exists(),'unready template has a publication trigger')
 return p


_import634_preserved=import_candidate

def import_candidate():
 _import634_preserved()
 p=pin();_current634['fetch_helpers'](api,SOURCE,p['source'],OUT)
 value=api(SOURCE,'contents/desktop/mouse-update.cjs?ref='+PREVIOUS['source']);raw=base64.b64decode(value['content'])
 need(value.get('sha')==PREVIOUS['updaterBlobSHA'] and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==PREVIOUS['updaterBlobSHA'],'actual published633 updater bytes differ')
 (OUT/'legacy633-update.cjs').write_bytes(raw)


def channel():
 p=pin();verify_packages(p);release=verify_public_assets(find_release(p),p)
 need(release['draft'] is False and release.get('published_at'),'channel requires public packages')
 packages={}
 for format_,name in [('appimage',APPIMAGE),('deb',DEB)]:
  asset=next(item for item in release['assets'] if item['name']==name);url=f'https://github.com/{REPO}/releases/download/{TAG}/{name}'
  need(asset.get('browser_download_url')==url,'public package URL differs');packages[format_]={'url':url,'size':asset['size'],'digest':asset['digest']}
 raw=(OUT/'legacy633-update.cjs').read_bytes()
 need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==PREVIOUS['updaterBlobSHA'],'published633 updater changed before channel write')
 data={'schema':1,'version':VERSION,'platform':'linux','arch':'x64',**packages['appimage'],'packages':packages,'publishedAt':release['published_at']}
 put_json('platforms/linux/mouse-x64/releases/'+VERSION+'.json',data);put_json(CHANNEL_PATH,data)
 observations=[]
 for attempt in range(72):
  try:
   with urllib.request.urlopen(CHANNEL,timeout=30) as response: observed=json.load(response)
   observations.append({'attempt':attempt+1,'version':observed.get('version'),'matches':observed==data})
   if observed==data: break
  except Exception as error: observations.append({'attempt':attempt+1,'error':str(error)[:300]})
  time.sleep(5)
 else:
  (OUT/'linux-channel-observations.json').write_bytes(json_bytes(observations));raise ValueError('Anonymous Linux channel did not expose the exact public metadata')
 (OUT/'linux-channel-observations.json').write_bytes(json_bytes(observations));(OUT/'linux-channel-expected.json').write_bytes(json_bytes(data))
 environment={key:value for key,value in os.environ.items() if key not in ('GH_TOKEN','GITHUB_TOKEN')}
 script=r"""
const assert=require('node:assert/strict'),fs=require('node:fs/promises'),os=require('node:os');
const {MouseUpdates,LINUX_CHANNEL}=require('./mouse-update.cjs');
const {MouseUpdates:Previous}=require('./legacy633-update.cjs');
(async()=>{
 const expected=JSON.parse(await fs.readFile('linux-channel-expected.json','utf8')),downloads={};
 assert.equal(LINUX_CHANNEL,'https://raw.githubusercontent.com/jeep-jim/OSMINOG-Releases/main/platforms/linux/mouse-x64/latest.json');
 for(const format of ['appimage','deb']){
  const target={platform:'linux',arch:'x64',format};
  const current=new MouseUpdates({app:{getVersion:()=> '6.0.34'},shell:{},target});
  assert.equal((await current.run('check')).phase,'current');assert.equal(current.state.channel,'static');
  const previous=new Previous({app:{getVersion:()=> '6.0.33',getPath:()=>os.tmpdir()},shell:{},target});
  assert.equal((await previous.run('check')).phase,'available');assert.equal(previous.state.channel,'static');
  assert.equal(previous.candidate.version,'6.0.34');assert.equal(previous.candidate.url,expected.packages[format].url);
  assert.equal(previous.candidate.hash,expected.packages[format].digest.slice(7));assert.equal(previous.candidate.size,expected.packages[format].size);
  assert.equal((await previous.run('download')).phase,'ready');await previous.verified();
  downloads[format]={size:previous.candidate.size,sha256:previous.candidate.hash,verified:true,currentVersionCheck:true};
 }
 await fs.writeFile('linux-channel-verification.json',JSON.stringify({ok:true,version:'6.0.34',platform:'linux',arch:'x64',channel:LINUX_CHANNEL,
  anonymous:true,previousVersion:'6.0.33',firstLinuxRelease:false,comparisonVersionIsFixture:false,
  actualOldModuleVersion:'6.0.33',olderReleasedLinuxUpdaterVerified:true,downloads},null,2));
})().catch(error=>{console.error(error);process.exit(1)});
"""
 subprocess.run(['node','-e',script],cwd=OUT,env=environment,check=True,timeout=900)
 print('MOUSE634_LINUX_ANONYMOUS_CHANNEL_PACKAGES_PASS',flush=True)


if __name__=='__main__':
 actions={'validate-template':validate_template,'import':import_candidate,'verify':verify_installed,'publish':publish,'channel':channel}
 if len(sys.argv)!=2 or sys.argv[1] not in actions: raise SystemExit('Expected validate-template, import, verify, publish or channel')
 actions[sys.argv[1]]()
