'use strict';
// External publisher verifier. It adapts one CI fixture, never product modules.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {pathToFileURL} = require('node:url');

const CONTRACT = Object.freeze({
  schema: 1,
  source: '0021084ccb9537e657d21e6f0c8e812dee6b461f',
  version: '6.0.37',
  originalSha256: 'a87573de7ebf2c380dffeaf64246739d68d3b3d8308dca424a90512174e0fd7d',
  originalGitBlob: 'ad6301bbf4d873a199fed6d26b7cfb7861ff0a6f',
  mainSha256: 'f3c9ba7794cb5c659c75fdc981faeda6b45851ceb0e70b61291128a04387914f',
  // This digest is pinned after the exact-source regression derives the body.
  adaptedSha256: 'f51b604dcd72b48081b33932718f6a7e185d9bc4e3a13bb9e55718d0de3f7b07',
  observations: ['owned-id-and-requested-label-before-click', 'owned-id-unpin-label-and-original-one-pin-count-after-russian-pin']
});
const ORIGINAL = [
 ' async function extensionButton(id,label){',
 '  const selector=\'.mouse-extension-row[data-id="\'+id+\'"] .mouse-extension-actions>button\';',
 '  const index=await fixture.js(`[...document.querySelectorAll(${JSON.stringify(selector)})].findIndex(e=>e.textContent===${JSON.stringify(label)})`);assert.ok(index>=0,\'Extension action \'+label);return click(selector+\':nth-child(\'+(index+1)+\')\');',
 ' }'
].join('\n');

// Serialized into the exact existing lexical scope: fixture/click/assert remain
// the originals. Both waits use the existing global deadline and default poll.
async function extensionButton(id,label){
  const selector='.mouse-extension-row[data-id="'+id+'"] .mouse-extension-actions>button';
  let index=-1;
  await fixture.until(async()=>{
    index=await fixture.js('[...document.querySelectorAll('+JSON.stringify(selector)+')].findIndex(e=>e.textContent==='+JSON.stringify(label)+')');
    return Number.isInteger(index)&&index>=0;
  },'Extension action '+label);
  assert.ok(index>=0,'Extension action '+label);
  const input=await click(selector+':nth-child('+(index+1)+')');
  if(label==='Закрепить')await fixture.until(()=>fixture.js(
    '([...document.querySelectorAll('+JSON.stringify(selector)+')].some(e=>e.textContent==="Открепить")&&document.querySelectorAll("#mouse-extensions-pins .mouse-extension-pin").length===1)'
  ),'Extension pin renderer '+id);
  return input;
}
const REPLACEMENT = ' '+extensionButton.toString();
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
function transform(original, {verifyAdapted=true}={}) {
  assert.equal(sha(original),CONTRACT.originalSha256,'Exact packaged637 fixture bytes differ');
  assert.equal(original.split(ORIGINAL).length-1,1,'Exact fixture target count differs');
  const adapted=original.replace(ORIGINAL,REPLACEMENT);
  assert.equal(adapted.split(REPLACEMENT).length-1,1,'Adapter replacement count differs');
  assert.equal(adapted.replace(REPLACEMENT,ORIGINAL),original,'Non-target fixture bytes changed');
  if(verifyAdapted)assert.equal(sha(adapted),CONTRACT.adaptedSha256,'Adapted fixture bytes differ');
  return adapted;
}

// Evaluated only on the paused, exact installed mouse-main.cjs call frame.
// All arguments are data; only this reviewed function is executable injection.
function installOwnedHook(load,config,contract,originalBody,replacementBody){
  const a=load('node:assert/strict'),f=load('node:fs'),p=load('node:path'),c=load('node:crypto');
  const electron=load('electron'),Module=load('node:module'),inspector=load('node:inspector');
  const digest=value=>c.createHash('sha256').update(value).digest('hex');
  const exact=value=>f.realpathSync(value);
  a.equal(process.env.CI,'true');a.equal(process.platform,'darwin');a.equal(process.arch,'arm64');
  a.equal(process.pid,config.pid);a.match(config.nonce,/^[a-f0-9]{64}$/);
  a.equal(process.env.MOUSE_637_FEATURE_READINESS_NONCE,config.nonce);
  a.equal(exact(process.execPath),config.executable);a.equal(exact(electron.app.getAppPath()),config.appPath);
  a.equal(electron.app.isPackaged,true);a.equal(electron.app.getVersion(),contract.version);
  a.equal(process.env.MOUSE_TEST_PROFILE,config.profile);a.ok(p.isAbsolute(config.profile));
  const flag=config.phase==='write'?'--mouse-637-features-smoke':'--mouse-637-features-restore-read';
  a.ok(['write','read'].includes(config.phase));a.equal(config.flag,flag);
  a.deepEqual(process.argv.filter(x=>x==='--mouse-637-features-smoke'||x==='--mouse-637-features-restore-read'),[flag]);
  const target=p.join(config.appPath,'mouse-637-features-smoke.cjs');
  a.equal(digest(f.readFileSync(p.join(config.appPath,'mouse-main.cjs'))),contract.mainSha256);
  a.equal(digest(f.readFileSync(target)),contract.originalSha256);
  a.equal(load.resolve(target),target);a.equal(load.cache[target],undefined);
  a.equal(f.existsSync(config.receipt),false);a.equal(p.dirname(config.receipt),config.output);
  const previous=Module._extensions['.js'];a.equal(typeof previous,'function');
  let applications=0;
  function ownedFixture(module,filename){
    if(filename!==target)return previous.call(this,module,filename);
    a.equal(Module._extensions['.js'],ownedFixture);Module._extensions['.js']=previous;
    a.equal(++applications,1);a.equal(electron.app.isReady(),true);
    a.equal(p.resolve(electron.app.getPath('userData')),config.profile);a.equal(electron.app.getName(),'Mouse Browser');
    const original=f.readFileSync(filename,'utf8');a.equal(digest(original),contract.originalSha256);
    a.equal(original.split(originalBody).length-1,1);
    const adapted=original.replace(originalBody,replacementBody);
    a.equal(adapted.replace(replacementBody,originalBody),original);a.equal(digest(adapted),contract.adaptedSha256);
    for(const [name,bytes] of [['original',original],['adapted',adapted]]){
      const evidence=p.join(config.output,'mouse-637-feature-readiness-'+name+'.cjs');
      if(f.existsSync(evidence))a.equal(f.readFileSync(evidence,'utf8'),bytes);
      else f.writeFileSync(evidence,bytes,{flag:'wx',mode:0o600});
    }
    // The controller disconnects after resuming. close() deactivates the server,
    // not merely its socket, before this fixture can produce any input.
    inspector.close();a.equal(inspector.url(),undefined);
    const closedAt=Date.now();a.equal(Module._extensions['.js'],previous);
    module._compile(adapted,filename);a.equal(typeof module.exports,'function');
    a.equal(Module._extensions['.js'],previous);a.equal(digest(f.readFileSync(filename)),contract.originalSha256);
    const receipt={schema:1,kind:'mouse637-publisher-fixture-readiness',source:contract.source,version:contract.version,
      phase:config.phase,flag,pid:process.pid,controllerPid:config.controllerPid,nonce:config.nonce,
      executable:config.executable,appPath:config.appPath,profile:config.profile,target,platform:process.platform,arch:process.arch,
      versions:{...process.versions},originalSha256:contract.originalSha256,originalGitBlob:contract.originalGitBlob,
      adaptedSha256:contract.adaptedSha256,mainSha256:contract.mainSha256,applications,
      observations:contract.observations,loaderRestored:true,inspectorClosed:true,inspectorUrl:null,
      closedAt,compiledAt:Date.now(),receiptBeforeFixtureInvocation:true};
    const temporary=config.receipt+'.tmp-'+config.nonce;
    f.writeFileSync(temporary,JSON.stringify(receipt,null,2)+'\n',{flag:'wx',mode:0o600});
    try{f.linkSync(temporary,config.receipt);}finally{f.unlinkSync(temporary);}
    console.log('MOUSE_637_FEATURE_READINESS_ADAPTER '+JSON.stringify(receipt));
  }
  Module._extensions['.js']=ownedFixture;
  return{pid:process.pid,nonce:config.nonce,phase:config.phase,target,installed:true};
}

function bounded(promise,ms,label){
  let timer;return Promise.race([promise,new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error(label)),ms);})]).finally(()=>clearTimeout(timer));
}
function frameURL(frame,scripts){
  const mapped=scripts.get(frame.location?.scriptId);
  if(typeof mapped!=='string')return undefined;
  assert.ok(!frame.url||frame.url===mapped,'Paused-frame URL disagrees with its parsed script identity');
  return mapped;
}
async function connect(url,remaining){
  const socket=new WebSocket(url),pending=new Map(),events=[],waiters=[],scripts=new Map();let sequence=0;
  await bounded(new Promise((resolve,reject)=>{socket.addEventListener('open',resolve,{once:true});socket.addEventListener('error',()=>reject(Error('Owned inspector connection failed')),{once:true});}),remaining(),'Inspector connection deadline');
  socket.addEventListener('message',event=>{
    const message=JSON.parse(event.data);
    if(message.id){const waiter=pending.get(message.id);if(waiter){pending.delete(message.id);message.error?waiter.reject(Error(JSON.stringify(message.error))):waiter.resolve(message.result);}}
    else if(message.method==='Debugger.scriptParsed')scripts.set(message.params.scriptId,message.params.url);
    else if(message.method==='Debugger.paused'){const index=waiters.findIndex(x=>x.method===message.method);if(index>=0)waiters.splice(index,1)[0].resolve(message.params);else events.push(message);}
  });
  socket.addEventListener('close',()=>{for(const waiter of pending.values())waiter.reject(Error('Owned inspector disconnected'));pending.clear();});
  return{
    scriptURL(frame){return frameURL(frame,scripts);},
    send(method,params={}){return bounded(new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));}),remaining(),'Inspector command deadline '+method);},
    event(method){const index=events.findIndex(x=>x.method===method);if(index>=0)return Promise.resolve(events.splice(index,1)[0].params);return bounded(new Promise(resolve=>waiters.push({method,resolve})),remaining(),'Inspector event deadline '+method);},
    async close(){if(socket.readyState===WebSocket.CLOSED)return;await bounded(new Promise(resolve=>{socket.addEventListener('close',resolve,{once:true});socket.close();}),Math.min(2000,remaining()),'Inspector disconnect deadline');}
  };
}
function validateConfig(config){
  assert.equal(config.schema,1);assert.ok(['write','read'].includes(config.phase));
  assert.equal(config.flag,config.phase==='write'?'--mouse-637-features-smoke':'--mouse-637-features-restore-read');
  assert.match(config.nonce,/^[a-f0-9]{64}$/);assert.ok(Number.isSafeInteger(config.pid)&&config.pid>0);
  assert.ok(Number.isInteger(config.port)&&config.port>0&&config.port<65536);
  for(const key of ['executable','appPath','profile','output','receipt','controllerReceipt'])assert.ok(path.isAbsolute(config[key]),key);
  assert.equal(config.appPath,path.join(path.dirname(path.dirname(config.executable)),'Resources','app.asar'));
  assert.equal(path.dirname(config.receipt),config.output);assert.equal(path.dirname(config.controllerReceipt),config.output);
  assert.equal(path.basename(config.receipt),'mouse-637-feature-readiness-'+config.phase+'.json');
  assert.equal(path.basename(config.controllerReceipt),'mouse-637-feature-readiness-controller-'+config.phase+'.json');
  assert.ok(Number.isFinite(config.deadlineEpochMs)&&config.deadlineEpochMs>Date.now());
  return config;
}
async function control(config){
  validateConfig(config);config={...config,controllerPid:process.pid};
  const startedAt=Date.now(),remaining=()=>{const left=config.deadlineEpochMs-Date.now();assert.ok(left>0,'Owned inspector setup deadline');return left;};
  const wait=async(check,label)=>{for(;;){remaining();const value=await check();if(value)return value;await bounded(new Promise(resolve=>setTimeout(resolve,25)),remaining(),label);}};
  let client;
  try{
    const endpoint='http://127.0.0.1:'+config.port+'/json/list';
    const target=await wait(async()=>{try{const response=await fetch(endpoint,{signal:AbortSignal.timeout(Math.min(500,remaining()))});assert.equal(response.ok,true);const rows=await response.json();assert.equal(rows.length,1);return rows[0];}catch(error){if(error.name==='AssertionError')throw error;return null;}},'Owned inspector start');
    const u=new URL(target.webSocketDebuggerUrl);assert.equal(u.protocol,'ws:');assert.equal(u.hostname,'127.0.0.1');assert.equal(Number(u.port),config.port);
    client=await connect(u.href,remaining);await client.send('Debugger.enable');
    const main=path.join(config.appPath,'mouse-main.cjs'),escape=value=>value.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
    const breakpoint=await client.send('Debugger.setBreakpointByUrl',{lineNumber:0,urlRegex:'^(?:'+escape(main)+'|'+escape(pathToFileURL(main).href)+')$'});
    await client.send('Runtime.runIfWaitingForDebugger');let paused=await client.event('Debugger.paused');
    const owned=frame=>client.scriptURL(frame)===main||client.scriptURL(frame)===pathToFileURL(main).href;
    if(!paused.callFrames.some(owned)){await client.send('Debugger.resume');paused=await client.event('Debugger.paused');}
    const frame=paused.callFrames.find(owned);assert.ok(frame,'Expected paused exact installed Mouse main entry');
    const expression='('+installOwnedHook.toString()+')(require,'+JSON.stringify(config)+','+JSON.stringify(CONTRACT)+','+JSON.stringify(ORIGINAL)+','+JSON.stringify(REPLACEMENT)+')';
    const result=await client.send('Debugger.evaluateOnCallFrame',{callFrameId:frame.callFrameId,expression,returnByValue:true});
    assert.equal(result.exceptionDetails,undefined,JSON.stringify(result.exceptionDetails));
    assert.deepEqual(result.result.value,{pid:config.pid,nonce:config.nonce,phase:config.phase,target:path.join(config.appPath,'mouse-637-features-smoke.cjs'),installed:true});
    await client.send('Debugger.removeBreakpoint',{breakpointId:breakpoint.breakpointId});
    await client.send('Debugger.resume');await client.close();client=null;
    const receipt=await wait(()=>fs.existsSync(config.receipt)?JSON.parse(fs.readFileSync(config.receipt,'utf8')):null,'Owned fixture hook completion');
    assert.equal(receipt.pid,config.pid);assert.equal(receipt.controllerPid,process.pid);assert.equal(receipt.nonce,config.nonce);assert.equal(receipt.phase,config.phase);assert.equal(receipt.inspectorClosed,true);
    let refused=false;try{await fetch(endpoint,{signal:AbortSignal.timeout(Math.min(500,remaining()))});}catch{refused=true;}
    assert.equal(refused,true,'Inspector server remains reachable after fixture hook');
    const proof={schema:1,ok:true,phase:config.phase,pid:config.pid,controllerPid:process.pid,nonce:config.nonce,port:config.port,host:'127.0.0.1',startedAt,finishedAt:Date.now(),serverUnavailable:true,receiptSha256:sha(fs.readFileSync(config.receipt)),controllerSha256:sha(fs.readFileSync(__filename))};
    fs.writeFileSync(config.controllerReceipt,JSON.stringify(proof,null,2)+'\n',{flag:'wx',mode:0o600});return proof;
  }finally{if(client)await client.close().catch(()=>{});}
}
module.exports={CONTRACT,ORIGINAL,REPLACEMENT,extensionButton,transform,installOwnedHook,validateConfig,control,connect,frameURL,sha};
if(require.main===module){
  if(process.argv.length!==4||process.argv[2]!=='control')throw Error('Expected control <owned-config.json>');
  assert.equal(process.env.CI,'true');assert.equal(process.platform,'darwin');assert.equal(process.arch,'arm64');
  const config=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
  control(config).catch(error=>{console.error(error.stack||error);process.exitCode=1;});
}
