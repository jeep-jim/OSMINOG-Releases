#!/usr/bin/env python3
"""Observe the anonymous public channel with the exact shipped636 updater."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

SOURCE = '7c09b6cb9885ce72be41e8f16a35d4c55c9ecde3'
BLOB = '91ab363f926774825caf8055b2d3d81bf0d51264'


def verify(output, pin, platform):
    raw = (output / 'legacy636-update.cjs').read_bytes()
    if hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() != BLOB:
        raise ValueError('Published636 updater bytes changed before anonymous discovery')
    if pin.get('version') != '6.0.37' or pin.get('ready') is not True:
        raise ValueError('Anonymous637 channel verification requires the exact ready candidate')
    if platform == 'darwin':
        target = {'platform': platform, 'arch': 'arm64'}
        names = {'dmg': 'Mouse-Browser-6.0.37-mac-arm64.dmg'}
        packages = {k: {'name': name, **pin['packages'][name]} for k, name in names.items()}
    elif platform == 'win32':
        target = {'platform': platform, 'arch': 'x64'}
        packages = {'exe': pin['package']}
    else:
        raise ValueError('Linux already performs its shipped636 module check for both package formats')
    expected = {'version': '6.0.37', 'target': target, 'packages': packages, 'previousSource': SOURCE, 'previousUpdaterBlob': BLOB}
    (output / 'mouse-637-public-channel-expected.json').write_text(json.dumps(expected, indent=2) + '\n', encoding='utf-8')
    script = r'''
const assert=require('node:assert/strict'),fs=require('node:fs/promises'),os=require('node:os'),path=require('node:path');
const {MouseUpdates:Previous}=require('./legacy636-update.cjs');
const {MouseUpdates,CHANNEL,WINDOWS_CHANNEL}=require('./mouse-update.cjs');
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
(async()=>{
 const expected=JSON.parse(await fs.readFile('mouse-637-public-channel-expected.json','utf8'));
 assert.equal(process.platform,expected.target.platform);assert.equal(process.arch,expected.target.arch);
 const channel=expected.target.platform==='darwin'?CHANNEL:WINDOWS_CHANNEL;
 assert.equal(channel,'https://raw.githubusercontent.com/jeep-jim/OSMINOG-Releases/main/'+(expected.target.platform==='darwin'?'channels/mouse/macos-arm64.json':'platforms/windows/mouse-x64/latest.json'));
 const cache=await fs.mkdtemp(path.join(os.tmpdir(),'mouse637-public-channel-')),observations=[],downloads={};
 try{
  for(const [format,bytes] of Object.entries(expected.packages)){
   let previous,error;
   for(let attempt=1;attempt<=48;attempt++){
    try{
     previous=new Previous({app:{getVersion:()=> '6.0.36',getPath:()=>cache},shell:{},target:expected.target});
     const state=await previous.run('check');observations.push({attempt,format,phase:state.phase,channel:state.channel,availableVersion:state.availableVersion});
     assert.equal(state.phase,'available');assert.equal(state.channel,'static');assert.equal(state.availableVersion,'6.0.37');
     const tag=expected.target.platform==='darwin'?'quadro-macos-v6.0.37-arm64':'mouse-windows-v6.0.37-x64';
     assert.equal(previous.candidate.url,'https://github.com/jeep-jim/OSMINOG-Releases/releases/download/'+tag+'/'+bytes.name);
     assert.equal(previous.candidate.hash,bytes.sha256);assert.equal(previous.candidate.size,bytes.size);error=null;break;
    }catch(cause){error=cause;observations.push({attempt,format,error:String(cause.message)});await sleep(5000)}
   }
   await fs.writeFile('mouse-637-public-channel-observations.json',JSON.stringify({channel,observations},null,2));if(error)throw error;
   assert.equal((await previous.run('download')).phase,'ready');await previous.verified();
   const current=new MouseUpdates({app:{getVersion:()=> '6.0.37'},shell:{},target:expected.target});
   assert.equal((await current.run('check')).phase,'current');assert.equal(current.state.channel,'static');
   downloads[format]={...bytes,verifiedDownload:true,currentVersionCheck:true};
  }
  await fs.writeFile('mouse-637-public-channel-verification.json',JSON.stringify({ok:true,version:'6.0.37',platform:process.platform,arch:process.arch,
   channel,anonymous:true,actualOldModuleVersion:'6.0.36',previousSource:expected.previousSource,previousUpdaterBlob:expected.previousUpdaterBlob,downloads},null,2));
  console.log('MOUSE_637_ACTUAL_636_UPDATER_STATIC_DISCOVERY_DOWNLOAD_PASS');
 }finally{await fs.rm(cache,{recursive:true,force:true})}
})().catch(error=>{console.error(error);process.exit(1)});
'''
    environment = {k: v for k, v in os.environ.items() if k not in ('GH_TOKEN', 'GITHUB_TOKEN')}
    with (output / 'mouse-637-public-channel.log').open('w', encoding='utf-8') as log:
        subprocess.run(['node', '-e', script], cwd=output, env=environment, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=900)
    print('MOUSE_637_ACTUAL_636_UPDATER_STATIC_DISCOVERY_DOWNLOAD_PASS', flush=True)
