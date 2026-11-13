"""Publish the verified Mac draft by numeric ID; never replace released assets."""
import hashlib, json, os, pathlib, subprocess, urllib.parse, urllib.request
REPO='jeep-jim/OSMINOG-Releases';TAG='macos-v5.0.3-arm64'
root=pathlib.Path('macos-release')
names=['Trader-OS-5.0.3-mac-arm64.dmg','Trader-OS-5.0.3-mac-arm64.zip','SHA256SUMS.txt','macos-build.json']
local={name:{'size':(root/name).stat().st_size,'digest':'sha256:'+hashlib.sha256((root/name).read_bytes()).hexdigest()} for name in names}
def api(path,method='GET',payload=None):
    cmd=['gh','api',f'repos/{REPO}/{path}','--method',method]
    if payload is not None:cmd+=['--input','-']
    return json.loads(subprocess.check_output(cmd,input=json.dumps(payload).encode() if payload is not None else None))
def verify(release):
    assets={x['name']:x for x in release['assets']}
    if set(assets)!=set(names):raise ValueError('Missing or unexpected remote assets')
    for name,value in local.items():
        remote=assets[name]
        if remote['state']!='uploaded' or remote['size']!=value['size'] or remote.get('digest')!=value['digest']:raise ValueError('Remote asset digest mismatch: '+name)
    return assets
# Tag lookup may return 404 for drafts. Read a draft from collection or POST response by ID.
existing=[x for x in api('releases?per_page=100') if x['tag_name']==TAG]
if len(existing)>1:raise ValueError('Ambiguous release')
if existing:
    release=api('releases/'+str(existing[0]['id']))
else:
    release=api('releases','POST',{'tag_name':TAG,'target_commitish':os.environ['GITHUB_SHA'],'name':'Trader OS 5.0.3 — Mac M1 Pro / Apple Silicon','body':(root/'RELEASE_NOTES.md').read_text(),'draft':True,'prerelease':True,'make_latest':'false'})
rid=release['id']
if release['draft']:
    assets={x['name']:x for x in release['assets']}
    for name in names:
        if name in assets:
            if assets[name]['size']!=local[name]['size'] or assets[name].get('digest')!=local[name]['digest']:raise ValueError('Existing draft contains different bytes; refusing overwrite')
            continue
        url=f'https://uploads.github.com/repos/{REPO}/releases/{rid}/assets?name='+urllib.parse.quote(name,safe='')
        req=urllib.request.Request(url,data=(root/name).read_bytes(),method='POST',headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Content-Type':'application/octet-stream','Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
        with urllib.request.urlopen(req,timeout=180) as response:json.load(response)
    release=api('releases/'+str(rid));verify(release)
    print('MAC_RELEASE_REMOTE_DIGESTS_PASS',flush=True)
    release=api('releases/'+str(rid),'PATCH',{'draft':False,'prerelease':True,'make_latest':'false','body':(root/'RELEASE_NOTES.md').read_text()})
release=api('releases/'+str(rid));assets=verify(release)
if release['draft'] or not release['published_at']:raise ValueError('Release remains unpublished')
result={'id':rid,'tag':TAG,'url':release['html_url'],'publishedAt':release['published_at'],'assets':[{k:a[k] for k in ['name','size','digest','browser_download_url']} for a in assets.values()]}
(root/'RELEASE_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));print('MAC_RELEASE_PUBLISHED_PASS',flush=True)
