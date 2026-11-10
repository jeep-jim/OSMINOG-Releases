"""Publish only immutable binaries from the successful native Light matrix."""
import hashlib,json,pathlib,re,subprocess,sys,tempfile,zipfile,shutil,urllib.parse
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCE='jeep-jim/OSMINOG';REGISTRY='jeep-jim/OSMINOG-Releases';WORKFLOW=412858774

def api(path,repo=SOURCE):return json.loads(subprocess.check_output(['gh','api',f'repos/{repo}/{path}']))
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main(version):
 if not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('Invalid version')
 request=json.loads((ROOT/f'staging/desktop-light/{version}/publish.json').read_text())
 head=request['sourceCommit'];runid=int(request['sourceWorkflowRun']);run=api(f'actions/runs/{runid}')
 if run['head_sha']!=head or run['workflow_id']!=WORKFLOW or run['conclusion']!='success' or run['status']!='completed':raise ValueError('Native matrix not successful')
 comparison=api(f'compare/{head}...main')
 if comparison['behind_by']!=0 or comparison['status'] not in ('ahead','identical'):raise ValueError('Source not merged')
 jobs=api(f'actions/runs/{runid}/jobs')['jobs']
 expected={'extension','windows-extension','desktop (windows-latest)','desktop (macos-latest)'}
 if {j['name'] for j in jobs}!=expected or any(j['conclusion']!='success' for j in jobs):raise ValueError('Missing native job')
 with tempfile.TemporaryDirectory() as td:
  work=pathlib.Path(td);files=[]
  for platform,artifactid in request['artifacts'].items():
   if platform not in ('Windows','macOS'):raise ValueError('Unknown platform')
   info=api(f'actions/artifacts/{int(artifactid)}')
   if info['workflow_run']['id']!=runid or info['workflow_run']['head_sha']!=head or info['expired'] or info['name']!=f'OSMINOG-Light-{version}-{platform}':raise ValueError('Wrong artifact')
   outer=work/(platform+'.artifact.zip')
   with outer.open('wb') as out:subprocess.run(['gh','api',f'repos/{SOURCE}/actions/artifacts/{artifactid}/zip'],stdout=out,check=True)
   if 'sha256:'+sha(outer)!=info['digest']:raise ValueError('Artifact checksum mismatch')
   with zipfile.ZipFile(outer) as z:
    selected=[x for x in z.infolist() if pathlib.PurePosixPath(x.filename).suffix in ('.exe','.dmg','.zip')]
    if len(selected)!=(1 if platform=='Windows' else 2):raise ValueError('Wrong asset count')
    for entry in selected:
     name=pathlib.PurePosixPath(entry.filename).name
     if not name.startswith('OSMINOG-Light-'+version+'-') or entry.file_size>1024**3:raise ValueError('Unexpected binary')
     target=work/name
     with z.open(entry) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst,1024*1024)
     files.append((platform,target,sha(target)))
  tag='desktop-light-v'+version
  notes=work/'notes.md';notes.write_text('OSMINOG Light '+version+' — lightweight local text/media storage.\n\nWindows x64 installer; universal macOS DMG/ZIP (Intel and Apple Silicon). Native launch, storage/reload and packaged application launch passed in CI.\n\nThese builds are unsigned and macOS is not notarized. OS security warnings are expected. They are preview releases, not a signed public-store distribution. Previous desktop profiles remain untouched; automatic migration from the old desktop is not implemented.\n\nFree: 100 images/month, 3 desks. Pro proposal $6.99/month is prepared but not sold; no payments or subscriptions activated.\n\nSource verification: https://github.com/'+SOURCE+'/actions/runs/'+str(runid)+'\n')
  result=subprocess.run(['gh','release','view',tag,'--repo',REGISTRY],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  if result.returncode:subprocess.run(['gh','release','create',tag,'--repo',REGISTRY,'--prerelease','--title','OSMINOG Light '+version+' · Windows / macOS preview','--notes-file',str(notes)],check=True)
  release=api('releases/tags/'+tag,REGISTRY);existing={a['name']:a for a in release['assets']}
  for platform,p,digest in files:
   if p.name in existing:
    if existing[p.name].get('digest')!='sha256:'+digest or existing[p.name]['size']!=p.stat().st_size:raise ValueError('Refusing immutable asset replacement')
   else:subprocess.run(['gh','release','upload',tag,str(p),'--repo',REGISTRY],check=True)
  release=api('releases/tags/'+tag,REGISTRY);assets={a['name']:a for a in release['assets']};verified=[]
  for platform,p,digest in files:
   a=assets[p.name]
   if a.get('digest')!='sha256:'+digest or a['size']!=p.stat().st_size:raise ValueError('Remote asset mismatch')
   verified.append({'platform':platform,'file':p.name,'size':p.stat().st_size,'sha256':digest,'url':a['browser_download_url'],'signed':False,'notarized':False})
  feed={'schema':'osminog-desktop-light/v1','version':version,'status':'preview-unsigned','sourceCommit':head,'sourceWorkflowRun':runid,'releaseUrl':release['html_url'],'artifacts':verified}
  path=ROOT/'channels/desktop-light/dev.json';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(feed,indent=2)+'\n');print(json.dumps(feed))
if __name__=='__main__':main(sys.argv[1])
