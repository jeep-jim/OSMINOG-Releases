import base64,hashlib,json,pathlib,re,zipfile
root=pathlib.Path('staging/android')
versions=[p.parent for p in root.glob('*/ASSEMBLE') if re.fullmatch(r'\d+\.\d+\.\d+-preview',p.parent.name)]
folder=max(versions,key=lambda p:tuple(map(int,p.name.split('-')[0].split('.'))))
meta=json.loads((folder/'release.json').read_text())
assert meta['version']==folder.name
assert re.fullmatch('[0-9a-f]{40}',meta['source'])
parts=sorted((folder/'parts').glob('part-*.b64'))
assert [p.name for p in parts]==[f'part-{i:04}.b64' for i in range(len(parts))]
raw=base64.b64decode(''.join(p.read_text() for p in parts),validate=True)
assert len(raw)==meta['size'] and 0<len(raw)<100*1024*1024
assert hashlib.sha256(raw).hexdigest()==meta['sha256']
out=pathlib.Path('android-build');out.mkdir(exist_ok=True)
name='OSMINOG-Android-'+meta['version']+'.apk'
(out/name).write_bytes(raw)
with zipfile.ZipFile(out/name) as z: assert 'AndroidManifest.xml' in z.namelist() and 'classes.dex' in z.namelist()
(out/'SHA256SUMS.txt').write_text(meta['sha256']+'  '+name+'\n')
(out/'tag.txt').write_text('android-v'+meta['version'])
(out/'notes.txt').write_text(meta['notes']+'\n\nSource: https://github.com/jeep-jim/OSMINOG/commit/'+meta['source']+'\nCI: '+meta['ci']+'\nSHA-256: '+meta['sha256']+'\n')
print('ANDROID_APK_HASH_AND_CONTAINER_PASS',name,meta['size'])
