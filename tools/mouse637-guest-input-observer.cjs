'use strict';
// External CI observation only. The original retained input and predicates stay intact.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {pathToFileURL}=require('node:url');
const {spawnSync}=require('node:child_process');
const {connect,sha}=require('./mouse637-feature-readiness.cjs');
const CONTRACT=Object.freeze({schema:1,source:'0021084ccb9537e657d21e6f0c8e812dee6b461f',version:'6.0.37',
 originalSha256:'911a5759675d721414d2a4a98c722f634a1bdc9131ae2bf3882a79e9cbc0200d',originalGitBlob:'6548c72795a80a432f531065a5846c28ad5b549d',adaptedSha256:'bfe878dc295a978a6bdf9dcf13eceb15c291ee4af63ce5355e40e3cca3109096',
 mainSha256:'f3c9ba7794cb5c659c75fdc981faeda6b45851ceb0e70b61291128a04387914f',
 flag:'--mouse-636-retained-smoke',phase:'retained',
 scope:'Passive WebContents/window observations and owned DOM capture events; no DOM mousemove; input-event is not a delivery acknowledgment'});

function installDOM(config){
 const key='__mouse637GuestInputObserver',prefix='MOUSE_637_GUEST_INPUT_OBSERVER_DOM ';
 if(globalThis[key])return false;
 const cap=256,types=['pointerdown','pointerup','pointercancel','mousedown','mouseup','click','focus','blur'];
 let sequence=0,emitted=0,dropped=0,disposed=false,overflow=false;
 const id=typeof crypto?.randomUUID==='function'?crypto.randomUUID():String(performance.timeOrigin)+'-'+config.role+'-'+config.index;
 const documentIdentity={id,timeOrigin:performance.timeOrigin,role:config.role,index:config.index};
 const text=value=>typeof value==='string'?value.slice(0,96):'';
 const number=value=>Number.isFinite(value)?value:null;
 const send=(kind,data={})=>{
  if(disposed)return;
  if(emitted>=cap){dropped=Math.min(1000000,dropped+1);if(overflow)return;overflow=true;kind='overflow';data={};}
  emitted++;
  try{console.debug(prefix+JSON.stringify({schema:1,nonce:config.nonce,document:documentIdentity,sequence:++sequence,
   kind,emitted,dropped,at:Date.now(),time:performance.now(),...data}));}catch{}
 };
 const listener=event=>{
  try{
   const target=event.target,link=target?.closest?.('a');
   send('event',{type:event.type,trusted:event.isTrusted===true,defaultPrevented:event.defaultPrevented===true,
    target:{kind:target===globalThis?'window':target===document?'document':'element',tag:text(target?.tagName),id:text(target?.id),linkId:text(link?.id)},
    button:number(event.button),buttons:number(event.buttons),pointerId:number(event.pointerId),
    pointerType:text(event.pointerType),x:number(event.clientX),y:number(event.clientY),
    documentFocused:document.hasFocus()});
  }catch{send('error',{message:'DOM observer failed'});}
 };
 for(const type of types)document.addEventListener(type,listener,{capture:true,passive:true});
 const windowListener=event=>{if(event.target===globalThis)listener(event);};
 for(const type of ['focus','blur'])globalThis.addEventListener(type,windowListener,{capture:true,passive:true});
 globalThis[key]={nonce:config.nonce,dispose(){if(disposed)return;send('dispose');disposed=true;
  for(const type of types)document.removeEventListener(type,listener,{capture:true});
  for(const type of ['focus','blur'])globalThis.removeEventListener(type,windowListener,{capture:true});delete globalThis[key];}};
 send('ready',{types,cap,origin:location.origin});return true;
}

function createObserver(ctx,config,domSource,origins){
 const {app,win,browser}=ctx;
 const cap=2048,postCap=64,wcCap=32,records=[],posts=[],wcs=new Map(),listeners=[];
 const stats={dropped:0,postDropped:0,errors:0,foreignMessages:0,malformedMessages:0,unownedEvents:0,documents:0};
 const documents=new Map();let sequence=0,started=false,disposed=false;
 const text=value=>typeof value==='string'?value.slice(0,128):'';
 const number=value=>Number.isFinite(value)?value:null;
 const count=key=>{stats[key]=Math.min(1000000,stats[key]+1);};
 const record=data=>{if(records.length>=cap){count('dropped');return;}records.push({sequence:++sequence,at:Date.now(),...data});};
 const error=where=>{count('errors');record({source:'observer-error',where});};
 const guarded=(where,fn)=>(...args)=>{try{return fn(...args);}catch{try{error(where);}catch{}}};
 const owner=wc=>{
  if(wc===win.webContents)return{role:'shell',webContentsId:wc.id,tabId:null};
  if(wc.session!==browser.session)return null;
  for(const page of browser.tabs.values())if(page.view?.webContents===wc)return{role:'guest',webContentsId:wc.id,tabId:page.id};
  return null;
 };
 const add=(target,type,fn)=>{target.on(type,fn);listeners.push([target,type,fn]);};
 const dom=(wc,details)=>{
  const message=details?.message;if(typeof message!=='string'||!message.startsWith('MOUSE_637_GUEST_INPUT_OBSERVER_DOM '))return;
  const owned=owner(wc);if(!owned){count('foreignMessages');return;}
  if(message.length>8192){count('malformedMessages');return;}
  if(details.frame!==wc.mainFrame){count('foreignMessages');return;}
  const value=JSON.parse(message.slice('MOUSE_637_GUEST_INPUT_OBSERVER_DOM '.length));
  if(value?.schema!==1||value.nonce!==config.nonce){count('foreignMessages');return;}
  const d=value.document;
  if(!d||typeof d.id!=='string'||d.id.length<1||d.id.length>96||!Number.isFinite(d.timeOrigin)||d.role!==owned.role||
     !Number.isSafeInteger(d.index)||d.index< -1||d.index>10000||!Number.isSafeInteger(value.sequence)||value.sequence<1||value.sequence>257||
     !['ready','event','overflow','error','dispose'].includes(value.kind)||!Number.isFinite(value.at)||!Number.isFinite(value.time)||
     !Number.isSafeInteger(value.emitted)||value.emitted!==value.sequence||!Number.isSafeInteger(value.dropped)||value.dropped<0||value.dropped>1000000){
   count('malformedMessages');return;
  }
  if(owned.role==='guest'){
   const url=new URL(details.frame.url);
   if(!origins().includes(url.origin)||!/^\/page\/\d+\/$/.test(url.pathname)||Number(url.pathname.split('/')[2])!==d.index){count('foreignMessages');return;}
  }else if(d.index!==-1||details.frame.url!==win.webContents.getURL()){count('foreignMessages');return;}
  const identity={id:d.id,timeOrigin:d.timeOrigin,role:d.role,index:d.index};
  const key=wc.id+':'+d.id,previous=documents.get(key);
  if(!previous){if(value.kind!=='ready'||documents.size>=32){count('malformedMessages');return;}
   documents.set(key,{...identity,webContentsId:wc.id,lastSequence:0,cap:256});stats.documents=documents.size;
  }
  const document=documents.get(key);
  if(value.sequence!==document.lastSequence+1||document.timeOrigin!==d.timeOrigin){count('malformedMessages');return;}
  document.lastSequence=value.sequence;
  if(value.kind==='event'){
   if(!['pointerdown','pointerup','pointercancel','mousedown','mouseup','click','focus','blur'].includes(value.type)||
      typeof value.trusted!=='boolean'||typeof value.defaultPrevented!=='boolean'||typeof value.documentFocused!=='boolean'||!value.target||
      !['window','document','element'].includes(value.target.kind)||
      ['tag','id','linkId'].some(k=>typeof value.target[k]!=='string'||value.target[k].length>96)){
    count('malformedMessages');return;
   }
  }
  // Only fixed scalar fields cross into the retained report; never arbitrary page payloads.
  record({source:'dom',...owned,document:identity,kind:value.kind,domSequence:value.sequence,domAt:value.at,domTime:value.time,
   emitted:value.emitted,dropped:value.dropped,type:value.kind==='event'?value.type:null,trusted:typeof value.trusted==='boolean'?value.trusted:null,
   defaultPrevented:typeof value.defaultPrevented==='boolean'?value.defaultPrevented:null,target:value.kind==='event'?{kind:value.target.kind,tag:text(value.target.tag),id:text(value.target.id),linkId:text(value.target.linkId)}:null,
   button:number(value.button),buttons:number(value.buttons),pointerId:number(value.pointerId),pointerType:text(value.pointerType),
   x:number(value.x),y:number(value.y),documentFocused:typeof value.documentFocused==='boolean'?value.documentFocused:null});
 };
 const observeWC=wc=>{
  const id=wc.id;
  if(wcs.has(id)||disposed)return;
  if(wc!==win.webContents&&wc.session!==browser.session)return;
  if(wcs.size>=wcCap){count('errors');return;}
  wcs.set(id,{id,registeredAt:Date.now()});
  for(const type of ['before-mouse-event','input-event'])add(wc,type,guarded(type,(_event,input)=>{
   const owned=owner(wc);if(!owned){count('unownedEvents');return;}
   record({source:'webContents',event:type,...owned,defaultPrevented:_event?.defaultPrevented===true,input:{type:text(input?.type),x:number(input?.x),y:number(input?.y),
    movementX:number(input?.movementX),movementY:number(input?.movementY),button:text(input?.button),
    clickCount:number(input?.clickCount),modifiers:Array.isArray(input?.modifiers)?input.modifiers.slice(0,8).map(text):[]}});
  }));
  for(const type of ['focus','blur'])add(wc,type,guarded(type,()=>{const owned=owner(wc);if(owned)record({source:'webContents',event:type,...owned});else count('unownedEvents');}));
  add(wc,'console-message',guarded('console-message',details=>dom(wc,details)));
  add(wc,'destroyed',guarded('destroyed',()=>{const row=wcs.get(id);if(row)row.destroyed=true;}));
 };
 return{
  start(){if(started||disposed){error('duplicate-start');return;}started=true;
   try{observeWC(win.webContents);for(const page of browser.tabs.values())observeWC(page.view.webContents);
    add(app,'web-contents-created',guarded('web-contents-created',(_event,wc)=>observeWC(wc)));
    for(const type of ['focus','blur'])add(win,type,guarded('window-'+type,()=>record({source:'window',event:type,windowId:win.id})));
   }catch{error('start');}
  },
  script(role,index=-1){return '('+domSource+')('+JSON.stringify({schema:1,nonce:config.nonce,role,index})+');true';},
  html(html,index){try{if(html.split('</body>').length!==2)throw Error('body count');return html.replace('</body>','<script>'+this.script('guest',index)+'</script></body>');}catch{error('owned-html');return html;}},
  shellDispose(){return 'try{const o=globalThis.__mouse637GuestInputObserver;if(o?.nonce==='+JSON.stringify(config.nonce)+')o.dispose()}catch{};true';},
  post(driver,x,y){
   const primary=()=>{try{if(typeof driver.primaryDown!=='function')return{available:false};const value=driver.primaryDown();return typeof value==='boolean'?{available:true,value}:{available:true,value:null,unexpectedType:typeof value};}catch(cause){return{available:true,error:text(cause?.message)};}};
   let row=null;
   try{if(posts.length<postCap){row={id:posts.length+1,x:number(x),y:number(y),beforeSequence:sequence,beforeAt:Date.now(),primaryBefore:primary(),returned:false};posts.push(row);}else count('postDropped');}catch{try{error('before-post');}catch{}}
   try{const result=driver.testClick(x,y);try{if(row){row.returned=true;row.resultType=typeof result;row.result=typeof result==='boolean'?result:null;row.primaryAfter=primary();row.afterAt=Date.now();row.afterSequence=sequence;}}catch{try{error('after-post');}catch{}}return result;}
   catch(cause){try{if(row){row.threw=true;row.primaryAfter=primary();row.afterAt=Date.now();row.afterSequence=sequence;row.errorName=text(cause?.name);}}catch{try{error('failed-post');}catch{}}throw cause;}
  },
  snapshot(){return{schema:1,kind:'mouse637-passive-guest-input',source:config.source,publisherSHA:config.publisherSHA,
   pid:process.pid,nonce:config.nonce,originalSha256:config.originalSha256,adaptedSha256:config.adaptedSha256,
   started,disposed,caps:{records:cap,posts:postCap,webContents:wcCap,domPerDocument:256},stats:{...stats},
   registeredWebContents:[...wcs.values()].map(x=>({...x})),documents:[...documents.values()].map(x=>({...x})),
   records:records.map(x=>({...x})),posts:posts.map(x=>({...x})),
   semantics:'input-event observes browser-side processing, not delivery; DOM has separate clocks; no DOM mousemove'};},
  dispose(){if(disposed)return;disposed=true;
   for(const[target,type,fn]of listeners){try{target.removeListener(type,fn);}catch{error('dispose');}}listeners.length=0;
  }
 };
}

function transform(original,{verifyAdapted=true}={}){
 assert.equal(sha(original),CONTRACT.originalSha256,'Exact retained source002 differs');
 const edits=[];
 const add=(from,to,count=1)=>{assert.equal(original.split(from).length-1,count,'Original retained anchor count');edits.push({from,to,count});};
 add('module.exports=async ctx=>{',
  'const __mouse637DeliveryConfig=module.__mouse637DeliveryConfig;delete module.__mouse637DeliveryConfig;\n'+
  'const __mouse637DOMSource='+JSON.stringify(installDOM.toString())+';\n'+createObserver.toString()+'\nmodule.exports=async ctx=>{');
 const save=" const save=()=>fs.writeFile('mouse-636-retained-owner-feedback.json',JSON.stringify(facts,null,2)+'\\n');";
 add(save," const __mouse637Delivery=createObserver(ctx,__mouse637DeliveryConfig,__mouse637DOMSource,()=>facts.fixtureOrigins||[]);\n"+
  " const save=()=>{facts.guestInputObserver=__mouse637Delivery.snapshot();return fs.writeFile('mouse-636-retained-owner-feedback.json',JSON.stringify(facts,null,2)+'\\n');};");
 add('await fixture.js(`(${installInputProbe.toString()})()`);','await fixture.js(`(${installInputProbe.toString()})();`+__mouse637Delivery.script(\'shell\'));');
 add('nativeInput.testClick(point.x,point.y)','__mouse637Delivery.post(nativeInput,point.x,point.y)',2);
 add('res.end(ownerPage(pageHTML(index),index,{base,previewBase}));','res.end(__mouse637Delivery.html(ownerPage(pageHTML(index),index,{base,previewBase}),index));');
 add('facts.profileIsolated=true;','facts.profileIsolated=true;__mouse637Delivery.start();');
 add(' finally{\n  const restore=', ' finally{\n  __mouse637Delivery.dispose();\n  const restore=');
 const cleanup="fixture.js('globalThis.__mouse633Input?.dispose();document.querySelector(\"#capture-dialog\")?.close();MouseTest.browsing.close();MouseTest.desktopUI.close({immediate:true})')";
 add(cleanup,"fixture.js(__mouse637Delivery.shellDispose()+';globalThis.__mouse633Input?.dispose();document.querySelector(\"#capture-dialog\")?.close();MouseTest.browsing.close();MouseTest.desktopUI.close({immediate:true})')");
 let adapted=original;
 for(const{from,to,count}of edits){assert.equal(adapted.split(from).length-1,count);adapted=adapted.split(from).join(to);}
 let reverted=adapted;
 for(const{from,to,count}of [...edits].reverse()){assert.equal(reverted.split(to).length-1,count);reverted=reverted.split(to).join(from);}
 assert.equal(reverted,original,'Unrelated retained bytes changed');
 if(verifyAdapted)assert.equal(sha(adapted),CONTRACT.adaptedSha256,'Adapted observer bytes differ');
 return adapted;
}

function installOwnedHook(load,config,contract,adapted){
 const a=load('node:assert/strict'),f=load('node:fs'),p=load('node:path'),c=load('node:crypto');
 const electron=load('electron'),Module=load('node:module'),inspector=load('node:inspector');
 const digest=value=>c.createHash('sha256').update(value).digest('hex');
 const exact=value=>f.realpathSync(value);
 a.equal(process.env.CI,'true');a.equal(process.platform,'darwin');a.equal(process.arch,'arm64');
 a.equal(process.pid,config.pid);a.equal(process.env.MOUSE_637_GUEST_INPUT_NONCE,config.nonce);
 a.equal(exact(process.execPath),config.executable);a.equal(exact(electron.app.getAppPath()),config.appPath);
 a.equal(electron.app.isPackaged,true);a.equal(electron.app.getVersion(),contract.version);
 a.equal(process.env.MOUSE_TEST_PROFILE,config.profile);a.ok(p.isAbsolute(config.profile));
 a.equal(config.phase,contract.phase);a.equal(config.flag,contract.flag);
 a.equal(process.argv[0],config.executable);
 a.deepEqual(process.argv.filter(x=>x.startsWith('--mouse-')&&!x.startsWith('--mouse-profile')),[contract.flag]);
 const fullRuntimeIdentity={pid:process.pid,execPath:process.execPath,argv:[...process.argv],platform:process.platform,
  arch:process.arch,CI:process.env.CI,profile:process.env.MOUSE_TEST_PROFILE,nonce:process.env.MOUSE_637_GUEST_INPUT_NONCE};
 const target=p.join(config.appPath,'mouse-636-retained-smoke.cjs');
 a.equal(digest(f.readFileSync(p.join(config.appPath,'mouse-main.cjs'))),contract.mainSha256);
 a.equal(digest(f.readFileSync(target)),contract.originalSha256);a.equal(digest(adapted),contract.adaptedSha256);
 a.equal(load.resolve(target),target);a.equal(load.cache[target],undefined);
 a.equal(f.existsSync(config.receipt),false);a.equal(p.dirname(config.receipt),config.output);
 const previous=Module._extensions['.js'];a.equal(typeof previous,'function');
 let applications=0;
 function ownedFixture(module,filename){
  if(filename!==target)return previous.call(this,module,filename);
  a.equal(Module._extensions['.js'],ownedFixture);Module._extensions['.js']=previous;
  a.equal(++applications,1);a.equal(electron.app.isReady(),true);
  a.equal(p.resolve(electron.app.getPath('userData')),config.profile);a.equal(electron.app.getName(),'Mouse Browser');
  const original=f.readFileSync(filename);a.equal(digest(original),contract.originalSha256);
  for(const[name,bytes]of [['original',original],['adapted',adapted]]){
   const evidence=p.join(config.output,'mouse-637-guest-input-observer-'+name+'.cjs');
   f.writeFileSync(evidence,bytes,{flag:'wx',mode:0o600});
  }
  inspector.close();a.equal(inspector.url(),undefined);const closedAt=Date.now();
  a.equal(Module._extensions['.js'],previous);
  module.__mouse637DeliveryConfig={source:contract.source,publisherSHA:config.publisherSHA,pid:process.pid,nonce:config.nonce,
   originalSha256:contract.originalSha256,adaptedSha256:contract.adaptedSha256};
  module._compile(adapted,filename);a.equal(typeof module.exports,'function');
  a.equal(module.__mouse637DeliveryConfig,undefined);a.equal(Module._extensions['.js'],previous);
  a.equal(digest(f.readFileSync(filename)),contract.originalSha256);
  const receipt={schema:1,kind:'mouse637-passive-guest-input-bootstrap',source:contract.source,version:contract.version,
   publisherSHA:config.publisherSHA,phase:config.phase,flag:config.flag,pid:process.pid,controllerPid:config.controllerPid,nonce:config.nonce,
   executable:config.executable,appPath:config.appPath,profile:config.profile,target,platform:process.platform,arch:process.arch,
   versions:{...process.versions},fullRuntimeIdentity,originalSha256:contract.originalSha256,originalGitBlob:contract.originalGitBlob,
   adaptedSha256:contract.adaptedSha256,mainSha256:contract.mainSha256,applications,scope:contract.scope,
   loaderRestored:true,inspectorClosed:true,inspectorUrl:null,closedAt,compiledAt:Date.now(),receiptBeforeFixtureInvocation:true};
  const temporary=config.receipt+'.tmp-'+config.nonce;
  f.writeFileSync(temporary,JSON.stringify(receipt,null,2)+'\n',{flag:'wx',mode:0o600});
  try{f.linkSync(temporary,config.receipt);}finally{f.unlinkSync(temporary);}
  console.log('MOUSE_637_GUEST_INPUT_OBSERVER_BOOTSTRAP '+JSON.stringify(receipt));
 }
 Module._extensions['.js']=ownedFixture;
 return{pid:process.pid,nonce:config.nonce,target,installed:true,fullRuntimeIdentity};
}

// Node has not initialized pid/execPath/argv at the initial inspect-brk wait.
// An independent OS listener binding supplies the mandatory early PID proof.
const RUNTIME_EXPRESSION='({availability:{pid:typeof process.pid,execPath:typeof process.execPath,argv:typeof process.argv},pid:typeof process.pid==="undefined"?null:process.pid,execPath:typeof process.execPath==="undefined"?null:process.execPath,argv:typeof process.argv==="undefined"?null:process.argv,platform:process.platform,arch:process.arch,CI:process.env?.CI,profile:process.env?.MOUSE_TEST_PROFILE,nonce:process.env?.MOUSE_637_GUEST_INPUT_NONCE})';
function assertRuntimeIdentity(value,config,{platform='darwin',arch='arm64',early=false}={}){
 assert.ok(value&&typeof value==='object');
 assert.equal(value.platform,platform);assert.equal(value.arch,arch);assert.equal(value.CI,'true');
 assert.equal(value.profile,config.profile);assert.equal(value.nonce,config.nonce);
 const types={pid:'number',execPath:'string',argv:'object'};
 for(const key of Object.keys(types)){
  if(early&&value.availability?.[key]==='undefined'){assert.equal(value[key],null);continue;}
  if(early)assert.equal(value.availability?.[key],types[key]);
  if(key==='pid')assert.equal(value.pid,config.pid);
  if(key==='execPath')assert.equal(value.execPath,config.executable);
  if(key==='argv'){
   assert.ok(Array.isArray(value.argv));assert.equal(value.argv[0],config.executable);
   assert.ok(value.argv.every(x=>typeof x==='string'));
   assert.deepEqual(value.argv.filter(x=>x.startsWith('--mouse-')&&!x.startsWith('--mouse-profile')),[CONTRACT.flag]);
  }
 }
 return value;
}
async function probeRuntime(client,config,options={}){
 const result=await client.send('Runtime.evaluate',{expression:RUNTIME_EXPRESSION,returnByValue:true});
 assert.equal(result.exceptionDetails,undefined,'Runtime ownership read failed');
 return assertRuntimeIdentity(result.result.value,config,{...options,early:true});
}
function listenerCommand(port,executable='/usr/sbin/lsof'){
 assert.ok(Number.isInteger(port)&&port>0&&port<65536);
 // -F T enables all TCP fields; -Ts must follow it to select state only.
 return[executable,'-nP','-a','-iTCP:'+port,'-sTCP:LISTEN','-F','pfnPT','-Ts'];
}
function parseListener(stdout,config){
 assert.equal(typeof stdout,'string');assert.ok(stdout.length>0&&stdout.length<=65536);
 const rows=stdout.trimEnd().split('\n');let pid=null,entry=null;const sockets=[];
 for(const row of rows){
  assert.ok(row.length>1&&!row.includes('\r')&&!row.includes('\0'),'Malformed listener record');
  const field=row[0],value=row.slice(1);
  if(field==='p'){assert.equal(pid,null,'Multiple listener processes');assert.match(value,/^[1-9]\d*$/);pid=Number(value);assert.ok(Number.isSafeInteger(pid));}
  else if(field==='f'){assert.ok(pid!==null);assert.match(value,/^\d+$/);entry={pid,fd:value};sockets.push(entry);}
  else{assert.ok(entry,'Socket fields precede descriptor');
   const key={P:'protocol',n:'endpoint',T:'state'}[field];assert.ok(key,'Unexpected listener field');assert.equal(entry[key],undefined,'Duplicate listener field');
   if(field==='T'){assert.ok(value.startsWith('ST='));entry.state=value.slice(3);}else entry[key]=value;
  }
 }
 assert.equal(sockets.length,1,'Exactly one listening socket required');
 const result=sockets[0];assert.equal(result.pid,config.pid);assert.equal(result.protocol,'TCP');
 assert.equal(result.endpoint,'127.0.0.1:'+config.port);assert.equal(result.state,'LISTEN');
 return result;
}
function probeListener(config,remaining,{executable='/usr/sbin/lsof',spawn=spawnSync}={}){
 const command=listenerCommand(config.port,executable),startedAt=Date.now();
 const result=spawn(command[0],command.slice(1),{encoding:'utf8',timeout:Math.max(1,Math.floor(remaining())),killSignal:'SIGKILL',maxBuffer:65536,shell:false});
 const proof={schema:1,kind:'mouse637-inspector-listener',pid:config.pid,port:config.port,host:'127.0.0.1',
  command,startedAt,finishedAt:Date.now(),exitCode:result.status,signal:result.signal,
  stdout:typeof result.stdout==='string'?result.stdout:'',stderr:typeof result.stderr==='string'?result.stderr:'',ok:false};
 let error;
 try{assert.equal(result.error,undefined,result.error?.message);assert.equal(result.status,0);assert.equal(result.signal,null);assert.equal(proof.stderr.trim(),'','Listener query warning/error');
  proof.parsed=parseListener(proof.stdout,config);proof.ok=true;
 }catch(cause){error=cause;proof.error=String(cause.message).slice(0,2048);}
 if(config.listenerReceipt)fs.writeFileSync(config.listenerReceipt,JSON.stringify(proof,null,2)+'\n',{flag:'wx',mode:0o600});
 if(error)throw error;return proof;
}
function validateConfig(config){
 assert.equal(config.schema,1);assert.equal(config.phase,'retained');assert.equal(config.flag,CONTRACT.flag);
 assert.match(config.nonce,/^[a-f0-9]{64}$/);assert.match(config.publisherSHA,/^[a-f0-9]{40}$/);
 assert.ok(Number.isSafeInteger(config.pid)&&config.pid>0);assert.ok(Number.isInteger(config.port)&&config.port>0&&config.port<65536);
 for(const key of ['executable','appPath','profile','output','receipt','controllerReceipt','listenerReceipt'])assert.ok(path.isAbsolute(config[key]),key);
 assert.equal(config.appPath,path.join(path.dirname(path.dirname(config.executable)),'Resources','app.asar'));
 assert.equal(path.basename(config.profile),'retained636');
 assert.equal(config.receipt,path.join(config.output,'mouse-637-guest-input-observer-bootstrap.json'));
 assert.equal(config.controllerReceipt,path.join(config.output,'mouse-637-guest-input-observer-controller.json'));
 assert.equal(config.listenerReceipt,path.join(config.output,'mouse-637-guest-input-observer-listener.json'));
 assert.ok(Number.isFinite(config.deadlineEpochMs)&&config.deadlineEpochMs>Date.now());
 return config;
}
async function control(config){
 validateConfig(config);config={...config,controllerPid:process.pid};
 const startedAt=Date.now(),remaining=()=>{const left=config.deadlineEpochMs-Date.now();assert.ok(left>0,'Owned observer setup deadline');return left;};
 const wait=async(check)=>{for(;;){remaining();const value=await check();if(value)return value;await new Promise(resolve=>setTimeout(resolve,Math.min(25,remaining())));}};
 let client;
 try{
  const endpoint='http://127.0.0.1:'+config.port+'/json/list';
  const target=await wait(async()=>{try{const response=await fetch(endpoint,{signal:AbortSignal.timeout(Math.min(500,remaining()))});assert.equal(response.ok,true);const rows=await response.json();assert.equal(rows.length,1);return rows[0];}catch(error){if(error.name==='AssertionError')throw error;return null;}});
  const u=new URL(target.webSocketDebuggerUrl);assert.equal(u.protocol,'ws:');assert.equal(u.hostname,'127.0.0.1');assert.equal(Number(u.port),config.port);
  client=await connect(u.href,remaining);
  // Read ownership while the entry is still waiting, before any command resumes it.
  const listenerIdentity=probeListener(config,remaining);
  const earlyRuntimeIdentity=await probeRuntime(client,config);
  await client.send('Debugger.enable');
  const main=path.join(config.appPath,'mouse-main.cjs'),escape=value=>value.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  const breakpoint=await client.send('Debugger.setBreakpointByUrl',{lineNumber:0,urlRegex:'^(?:'+escape(main)+'|'+escape(pathToFileURL(main).href)+')$'});
  await client.send('Runtime.runIfWaitingForDebugger');let paused=await client.event('Debugger.paused');
  const owned=frame=>client.scriptURL(frame)===main||client.scriptURL(frame)===pathToFileURL(main).href;
  if(!paused.callFrames.some(owned)){await client.send('Debugger.resume');paused=await client.event('Debugger.paused');}
  const frame=paused.callFrames.find(owned);assert.ok(frame,'Expected paused exact installed Mouse main entry');
  const original=fs.readFileSync(path.join(__dirname,'fixtures/mouse637-retained-002.cjs'),'utf8'),adapted=transform(original);
  const expression='('+installOwnedHook.toString()+')(require,'+JSON.stringify(config)+','+JSON.stringify(CONTRACT)+','+JSON.stringify(adapted)+')';
  const result=await client.send('Debugger.evaluateOnCallFrame',{callFrameId:frame.callFrameId,expression,returnByValue:true});
  assert.equal(result.exceptionDetails,undefined,JSON.stringify(result.exceptionDetails));
  const fullRuntimeIdentity=assertRuntimeIdentity(result.result.value.fullRuntimeIdentity,config);
  assert.deepEqual(result.result.value,{pid:config.pid,nonce:config.nonce,target:path.join(config.appPath,'mouse-636-retained-smoke.cjs'),installed:true,fullRuntimeIdentity});
  await client.send('Debugger.removeBreakpoint',{breakpointId:breakpoint.breakpointId});
  await client.send('Debugger.resume');await client.close();client=null;
  const receipt=await wait(()=>fs.existsSync(config.receipt)?JSON.parse(fs.readFileSync(config.receipt,'utf8')):null);
  assert.equal(receipt.pid,config.pid);assert.equal(receipt.controllerPid,process.pid);assert.equal(receipt.nonce,config.nonce);assert.equal(receipt.inspectorClosed,true);
  let refused=false;try{await fetch(endpoint,{signal:AbortSignal.timeout(Math.min(500,remaining()))});}catch{refused=true;}
  assert.equal(refused,true,'Inspector server still reachable');
  const proof={schema:1,ok:true,phase:config.phase,pid:config.pid,controllerPid:process.pid,nonce:config.nonce,publisherSHA:config.publisherSHA,
   port:config.port,host:'127.0.0.1',startedAt,finishedAt:Date.now(),earlyRuntimeIdentity,fullRuntimeIdentity,
   listenerReceiptSha256:sha(fs.readFileSync(config.listenerReceipt)),ownershipBeforeResume:true,serverUnavailable:true,
   receiptSha256:sha(fs.readFileSync(config.receipt)),controllerSha256:sha(fs.readFileSync(__filename))};
  fs.writeFileSync(config.controllerReceipt,JSON.stringify(proof,null,2)+'\n',{flag:'wx',mode:0o600});return proof;
 }finally{if(client)await client.close().catch(()=>{});}
}
module.exports={CONTRACT,installDOM,createObserver,transform,installOwnedHook,RUNTIME_EXPRESSION,assertRuntimeIdentity,probeRuntime,listenerCommand,parseListener,probeListener,validateConfig,control};
if(require.main===module){
 if(process.argv.length!==4||process.argv[2]!=='control')throw Error('Expected control <owned-config.json>');
 assert.equal(process.env.CI,'true');assert.equal(process.platform,'darwin');assert.equal(process.arch,'arm64');
 control(JSON.parse(fs.readFileSync(process.argv[3],'utf8'))).catch(error=>{console.error(error.stack||error);process.exitCode=1;});
}
