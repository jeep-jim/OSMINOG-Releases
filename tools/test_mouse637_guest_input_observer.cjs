'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),os=require('node:os'),cp=require('node:child_process'),{EventEmitter}=require('node:events');
const A=require('./mouse637-guest-input-observer.cjs'),transport=require('./mouse637-feature-readiness.cjs');
const original=fs.readFileSync(path.join(__dirname,'fixtures/mouse637-retained-002.cjs'),'utf8');
const shared=fs.readFileSync(path.join(__dirname,'fixtures/mouse637-readiness-002-fixture.cjs'),'utf8');
const guest=require('./fixtures/mouse637-retained-002-guest-input.cjs');
const untilSource=shared.slice(shared.indexOf(' async function until('),shared.indexOf('\n const frame=',shared.indexOf(' async function until(')));
const clone=value=>JSON.parse(JSON.stringify(value));
function environment(){
 const session={},app=new EventEmitter(),shell=new EventEmitter(),win=new EventEmitter(),browser={session,tabs:new Map()};
 Object.assign(shell,{id:1,session,mainFrame:{url:'file:///owned/index.html'},getURL(){return this.mainFrame.url;}});
 Object.assign(win,{id:1,webContents:shell});
 const config={source:A.CONTRACT.source,publisherSHA:'a'.repeat(40),nonce:'b'.repeat(64),originalSha256:A.CONTRACT.originalSha256,adaptedSha256:A.CONTRACT.adaptedSha256};
 const observer=A.createObserver({app,win,browser},config,A.installDOM.toString(),()=>['http://127.0.0.1:3000']);
 const addGuest=(id=2)=>{const wc=new EventEmitter();Object.assign(wc,{id,session,mainFrame:{url:'http://127.0.0.1:3000/page/'+id+'/'}});app.emit('web-contents-created',{},wc);browser.tabs.set('tab-'+id,{id:'tab-'+id,view:{webContents:wc}});return wc;};
 return{app,win,browser,shell,config,observer,addGuest};
}
function domEnvironment(options={}){
 const documentListeners=new Map(),windowListeners=new Map(),messages=[];
 const document={hasFocus:()=>true,addEventListener(type,fn,opt){assert.equal(opt.capture,true);assert.equal(opt.passive,true);documentListeners.set(type,fn);},removeEventListener(type,fn){assert.equal(documentListeners.get(type),fn);documentListeners.delete(type);}};
 const context=vm.createContext({document,performance:{timeOrigin:1000,now:()=>25},Date:{now:()=>1025},crypto:{randomUUID:()=>options.id||'owned-document'},location:{origin:'http://127.0.0.1:3000'},console:{debug:line=>messages.push(JSON.parse(line.slice('MOUSE_637_GUEST_INPUT_OBSERVER_DOM '.length)))},
  addEventListener(type,fn,opt){assert.equal(opt.capture,true);assert.equal(opt.passive,true);windowListeners.set(type,fn);},removeEventListener(type,fn){assert.equal(windowListeners.get(type),fn);windowListeners.delete(type);}});
 vm.runInContext('('+A.installDOM.toString()+')('+JSON.stringify({nonce:'b'.repeat(64),role:'guest',index:2})+')',context);
 return{context,document,documentListeners,windowListeners,messages,fire(type,extra={}){const target={tagName:'A',id:'download-a',closest(){return this;}};documentListeners.get(type)({type,target,isTrusted:true,defaultPrevented:false,button:0,buttons:1,clientX:100,clientY:149,...extra});}};
}

test('one exact retained transform preserves helpers, budgets and original predicates',()=>{
 const adapted=A.transform(original);new vm.Script(adapted);
 assert.equal(transport.sha(original),A.CONTRACT.originalSha256);
 assert.throws(()=>A.transform(original+'\n',{verifyAdapted:false}));
 for(const text of ['budgetMs=240000','async function focus(){return focusNativeInputWindow({app,win,until:fixture.until});}',
  "readEvents:()=>fixture.pageJS(record,'mouse634.clicks.slice('+count+')')","accept:events=>events.some(event=>event.id===selector.slice(1)&&event.trusted)",
  'waitFor:fixture.until',"await fixture.until(async()=>{result.events=await fixture.js('__mouse633Input.read()');return result.events.some(event=>event.type==='click'&&event.trusted&&event.matches);},'634 trusted click '+selector)"]){
  assert.ok(original.includes(text),text);assert.ok(adapted.includes(text),text);
 }
 assert.equal((adapted.match(/__mouse637Delivery\.post\(nativeInput,point.x,point.y\)/g)||[]).length,2);
 assert.equal((original.match(/nativeInput\.testClick\(point.x,point.y\)/g)||[]).length,2);
});
test('observer calls original native receiver once and preserves booleans, promises and thrown identity',()=>{
 const x=environment();let calls=0,primaryCalls=0;const thrown=Error('native throw');
 for(const value of [true,false,Promise.resolve(true),thrown]){
  const driver={primaryDown(){primaryCalls++;throw Error('optional read');},testClick(a,b){assert.equal(this,driver);assert.equal(a,104);assert.equal(b,252);calls++;if(value===thrown)throw thrown;return value;}};
  if(value===thrown)assert.throws(()=>x.observer.post(driver,104,252),error=>error===thrown);
  else assert.equal(x.observer.post(driver,104,252),value);
 }
 assert.equal(calls,4);assert.equal(primaryCalls,8);assert.equal(x.observer.snapshot().posts.length,4);
 assert.ok(x.observer.snapshot().posts.every(p=>p.primaryBefore.error==='optional read'&&p.primaryAfter.error==='optional read'));
 const poisoned=Object.create(null,{name:{get(){throw Error('diagnostic getter failure');}}});
 assert.throws(()=>x.observer.post({testClick(){throw poisoned;}},104,252),error=>error===poisoned);
 assert.equal(x.observer.snapshot().stats.errors,1);
});
test('DOM capture is passive, preserves trust, observes Window focus once, and disposes symmetrically',()=>{
 const x=domEnvironment();x.fire('pointerdown');x.fire('pointercancel',{isTrusted:false});
 vm.runInContext('globalThis.__windowEvent={type:"focus",target:globalThis,isTrusted:true,defaultPrevented:false}',x.context);
 x.windowListeners.get('focus')(x.context.__windowEvent);
 x.windowListeners.get('focus')({type:'focus',target:{},isTrusted:true});
 assert.equal(x.messages.filter(m=>m.kind==='event').length,3);assert.equal(x.messages[2].trusted,false);
 assert.equal(x.messages[3].target.kind,'window');assert.equal(x.messages[3].type,'focus');
 vm.runInContext('__mouse637GuestInputObserver.dispose()',x.context);
 assert.equal(x.documentListeners.size,0);assert.equal(x.windowListeners.size,0);assert.equal(x.messages.at(-1).kind,'dispose');
});
test('DOM traffic and main storage are bounded, overflow is explicit, and unknown payload fields are discarded',()=>{
 const d=domEnvironment();for(let i=0;i<1000;i++)d.fire('mousedown');assert.equal(d.messages.length,257);assert.equal(d.messages.at(-1).kind,'overflow');
 const x=environment();x.observer.start();const wc=x.addGuest();
 const row=clone(d.messages[0]);row.document.extra={never:'retain'};row.documentFocused={never:'retain'};
 wc.emit('console-message',{message:'MOUSE_637_GUEST_INPUT_OBSERVER_DOM '+JSON.stringify(row),frame:wc.mainFrame});
 let state=x.observer.snapshot();assert.equal(state.documents.length,1);assert.equal(state.documents[0].extra,undefined);assert.equal(state.records[0].document.extra,undefined);assert.equal(state.records[0].documentFocused,null);
 for(let i=0;i<2100;i++)wc.emit('input-event',{}, {type:'mouseMove',x:i,y:1});
 state=x.observer.snapshot();assert.equal(state.records.length,2048);assert.ok(state.stats.dropped>0);
 for(let i=0;i<100;i++)x.observer.post({testClick:()=>true},0,0);
 assert.equal(x.observer.snapshot().posts.length,64);assert.equal(x.observer.snapshot().stats.postDropped,36);
 x.observer.dispose();assert.equal(x.observer.snapshot().disposed,true);
});
test('owned WC/main-frame/URL/nonce constraints reject foreign data and retain browser-side input observations',()=>{
 const x=environment();x.observer.start();const wc=x.addGuest();
 const base=domEnvironment().messages[0];
 for(const row of [{...base,nonce:'c'.repeat(64)},{...base,sequence:0},{...base,emitted:'huge'}])wc.emit('console-message',{message:'MOUSE_637_GUEST_INPUT_OBSERVER_DOM '+JSON.stringify(row),frame:wc.mainFrame});
 wc.emit('console-message',{message:'MOUSE_637_GUEST_INPUT_OBSERVER_DOM '+JSON.stringify(base),frame:{url:wc.mainFrame.url}});
 wc.mainFrame.url='https://unowned.invalid/page/2/';wc.emit('console-message',{message:'MOUSE_637_GUEST_INPUT_OBSERVER_DOM '+JSON.stringify(base),frame:wc.mainFrame});wc.mainFrame.url='http://127.0.0.1:3000/page/2/';
 wc.emit('before-mouse-event',{defaultPrevented:true},{type:'mouseDown',button:'left',x:1,y:2});
 wc.emit('input-event',{}, {type:'mouseUp',button:'left'});wc.emit('focus');x.win.emit('blur');
 const state=x.observer.snapshot();assert.equal(state.documents.length,0);assert.ok(state.stats.foreignMessages>=3);assert.ok(state.stats.malformedMessages>=2);
 assert.deepEqual(state.records.map(r=>r.event),['before-mouse-event','input-event','focus','blur']);assert.equal(state.records[0].defaultPrevented,true);
 x.observer.dispose();assert.equal(wc.listenerCount('input-event'),0);assert.equal(x.app.listenerCount('web-contents-created'),0);assert.equal(x.shell.listenerCount('console-message'),0);
});

test('actual Node Inspector binds OS listener and available runtime fields before any resume',async()=>{
 const directory=fs.mkdtempSync(path.join(os.tmpdir(),'mouse637-observer-pre-resume-')),main=path.join(directory,'Установка Mouse.cjs'),marker=path.join(directory,'ran');
 fs.writeFileSync(main,'require("node:fs").writeFileSync('+JSON.stringify(marker)+',"executed");setInterval(()=>{},1000);\n');
 const child=cp.spawn(process.execPath,['--inspect-brk=127.0.0.1:0',main,A.CONTRACT.flag],{stdio:['ignore','pipe','pipe'],env:{...process.env,CI:'true',MOUSE_TEST_PROFILE:'/owned/retained636',MOUSE_637_GUEST_INPUT_NONCE:'b'.repeat(64)}});let client;
 try{
  const deadline=Date.now()+8000,remaining=()=>{assert.ok(Date.now()<deadline);return deadline-Date.now();};
  const url=await new Promise((resolve,reject)=>{let output='';const timer=setTimeout(()=>reject(Error('inspector start')),5000);child.stderr.on('data',b=>{output+=b;const m=output.match(/ws:\/\/127\.0\.0\.1:\d+\/[\w-]+/);if(m){clearTimeout(timer);resolve(m[0]);}});child.once('error',reject);});
  client=await transport.connect(url,remaining);const commands=[];
  const wrapped={send(method,params){commands.push(method);return client.send(method,params);}};
  const config={pid:child.pid,port:Number(new URL(url).port),executable:process.execPath,profile:'/owned/retained636',nonce:'b'.repeat(64)};
  const listener=A.probeListener(config,remaining,{executable:process.platform==='darwin'?'/usr/sbin/lsof':'/usr/bin/lsof'});
  assert.equal(listener.ok,true);assert.equal(listener.parsed.pid,child.pid);assert.equal(listener.parsed.endpoint,'127.0.0.1:'+config.port);
  const observed=await A.probeRuntime(wrapped,config,{platform:process.platform,arch:process.arch});
  assert.equal(observed.nonce,'b'.repeat(64));
  if(observed.availability.pid==='undefined')assert.equal(observed.pid,null);else assert.equal(observed.pid,child.pid);
  await assert.rejects(()=>A.probeRuntime(wrapped,{...config,nonce:'c'.repeat(64)},{platform:process.platform,arch:process.arch}));
  assert.throws(()=>A.parseListener(listener.stdout,{...config,pid:child.pid+1}));
  assert.deepEqual(commands,['Runtime.evaluate','Runtime.evaluate']);assert.equal(fs.existsSync(marker),false);assert.equal(child.exitCode,null);
 }finally{if(client)await client.close().catch(()=>{});child.kill();if(child.exitCode===null)await new Promise(resolve=>child.once('exit',resolve));fs.rmSync(directory,{recursive:true,force:true});}
});

test('listener ownership rejects foreign, ambiguous, malformed, warning and failed probes',()=>{
 const config={pid:123,port:4567},good='p123\nf25\nPTCP\nn127.0.0.1:4567\nTST=LISTEN\n';
 assert.deepEqual(A.parseListener(good,config),{pid:123,fd:'25',protocol:'TCP',endpoint:'127.0.0.1:4567',state:'LISTEN'});
 for(const bad of [good.replace('p123','p124'),good+good,good+'f26\nPTCP\nn127.0.0.1:4567\nTST=LISTEN\n',
  good.replace('127.0.0.1','[::1]'),good.replace('127.0.0.1','*'),good.replace('4567','4568'),good.replace('PTCP','PUDP'),
  good.replace('LISTEN','ESTABLISHED'),good.replace('TST=LISTEN\n',''),good.replace('f25','f?'),good+'TST=LISTEN\n',
  good.replace('p123\n',''),good.replace('p123','pNaN'),''])assert.throws(()=>A.parseListener(bad,config));
 for(const alteration of [{status:1},{stderr:'warning: partial enumeration'},{signal:'SIGKILL'},{error:Error('missing command')}]){
  assert.throws(()=>A.probeListener(config,()=>50,{spawn(cmd,args,options){assert.equal(cmd,'/usr/sbin/lsof');assert.equal(options.shell,false);assert.equal(options.timeout,50);assert.equal(options.killSignal,'SIGKILL');assert.equal(args.includes('-p'),false);return{status:0,signal:null,stdout:good,stderr:'',...alteration};}}));
 }
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'mouse637-listener-failure-')),file=path.join(dir,'receipt.json');
 try{assert.throws(()=>A.probeListener({...config,listenerReceipt:file},()=>50,{spawn:()=>({status:1,signal:null,stdout:'',stderr:'failure'})}));
  const raw=JSON.parse(fs.readFileSync(file));assert.equal(raw.ok,false);assert.equal(raw.exitCode,1);assert.equal(raw.stderr,'failure');
 }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
test('early unavailable fields are explicit, while every available identity and full identity remain mandatory',()=>{
 const config={pid:123,executable:'/owned/Mouse Browser',profile:'/owned/retained636',nonce:'b'.repeat(64)};
 const full={pid:123,execPath:config.executable,argv:[config.executable,A.CONTRACT.flag],platform:'darwin',arch:'arm64',CI:'true',profile:config.profile,nonce:config.nonce};
 const early={...full,availability:{pid:'undefined',execPath:'undefined',argv:'undefined'},pid:null,execPath:null,argv:null};
 assert.equal(A.assertRuntimeIdentity(early,config,{early:true}),early);assert.equal(A.assertRuntimeIdentity(full,config),full);
 for(const mutate of [x=>x.nonce='wrong',x=>x.profile='/other',x=>x.CI='false',x=>x.platform='linux',x=>x.arch='x64',
  x=>x.pid=123,x=>x.availability.pid='number',x=>{x.availability.pid='number';x.pid=124;},
  x=>{x.availability.execPath='string';x.execPath='/wrong';},x=>{x.availability.argv='object';x.argv=[config.executable,'--mouse-wrong'];}]){
  const value=clone(early);mutate(value);assert.throws(()=>A.assertRuntimeIdentity(value,config,{early:true}));
 }
 assert.throws(()=>A.assertRuntimeIdentity(early,config));
});

function extractNested(source,name,next){const start=source.indexOf(' async function '+name+'(');assert.ok(start>=0);const end=source.indexOf('\n '+next,start);assert.ok(end>start);return source.slice(start,end);}
async function runNested(source,{shell=false,mode='delayed',nativeError=Error('native exact failure')}={}){
 let clock=0,posted=false,polls=0,calls=0,saves=0;const trace=[],facts={nativeInputs:[],guestClickAttempts:[]},observer=environment().observer;
 const accepted=shell?{type:'click',trusted:true,matches:true}:{id:'download-a',trusted:true};
 const events=()=>{trace.push('poll');polls++;if(!posted||mode==='missing'||polls<2)return[];
  if(mode==='untrusted')return[{...accepted,trusted:false}];if(mode==='wrong')return[shell?{...accepted,matches:false}:{...accepted,id:'other'}];return[accepted];};
 const wc={id:2,getZoomFactor:()=>1,isFocused:()=>false,getURL:()=>'http://owned/page/0/',isLoadingMainFrame:()=>false};
 const view={webContents:wc,getBounds:()=>({x:0,y:0,width:100,height:100}),getVisible:()=>true};
 const record={id:'owned',page:{view,bounds:{x:0,y:0,width:100,height:100},visible:true}};
 const win={getContentBounds:()=>({x:4,y:103,width:1200,height:800}),getBounds:()=>({x:4,y:80,width:1200,height:823}),isFocused:()=>true,webContents:{isFocused:()=>true},contentView:{children:[view]}};
 const nativeInput={testClick(x,y){trace.push('native');calls++;assert.equal(this,nativeInput);assert.equal(x,104);assert.equal(y,252);posted=true;if(mode==='throw')throw nativeError;return mode!=='false';}};
 const context=vm.createContext({assert,performance:{now:()=>clock},deadline:75,name:'observer-contract',sleep:async ms=>{trace.push('sleep:'+ms);clock+=ms;},Date,
  facts,win,nativeInput,__mouse637Delivery:observer,focus:async()=>{trace.push('focus');return{ready:true};},inputSource:()=>'CGEvent',
  nativeHitTarget:function nativeHitTarget(){},...guest,screen:{getCursorScreenPoint:()=>({x:104,y:252})},webContents:{getFocusedWebContents:()=>null},save:async()=>{trace.push('save');saves++;}});
 const until=vm.runInContext('('+untilSource.trim()+')',context);
 const fixture={until,frame:async()=>{trace.push('frame');},pageJS:async(_record,script)=>{
  if(script.includes('nativeHitTarget')){trace.push('target');return{ready:true,x:100,y:149};}
  if(script.startsWith('mouse634.clicks.slice'))return clone(events());trace.push('readback');return{count:0};
 },js:async script=>{
  if(script.includes('nativeHitTarget')){trace.push('target');return{ready:true,x:100,y:149};}
  if(script==='__mouse633Input.read()')return clone(events());trace.push(script.includes('.begin(')?'begin':'scroll');return true;
 }};
 context.fixture=fixture;
 const fn=vm.runInContext('('+extractNested(source,shell?'click':'guestClick',shell?'async function guestClick':'async function screenCapture').trim()+')',context);
 let result,error;try{result=await(shell?fn('#download-a'):fn(record,'#download-a'));}catch(cause){error=cause;}
 return{result:result&&clone(result),error,trace,clock,polls,calls,saves,facts,observer:observer.snapshot()};
}
test('actual original/adapted guestClick preserves trusted acceptance, failure identity and post-to-poll ordering',async()=>{
 const adapted=A.transform(original,{verifyAdapted:false});
 for(const mode of ['delayed','missing','untrusted','wrong','false','throw']){
  const nativeError=Error('native exact '+mode),before=await runNested(original,{mode,nativeError}),after=await runNested(adapted,{mode,nativeError});
  assert.deepEqual(after.trace,before.trace);assert.equal(after.calls,1);assert.equal(after.observer.posts.length,1);
  assert.equal(after.clock,before.clock);assert.equal(after.polls,before.polls);assert.equal(after.saves,before.saves);
  if(mode==='delayed'){assert.deepEqual(after.result,before.result);assert.equal(after.polls,2);assert.equal(after.error,undefined);assert.equal(after.saves,0);}
  else{assert.ok(after.error);assert.equal(after.error.message,before.error.message);if(mode==='throw')assert.equal(after.error,nativeError);}
  const index=after.trace.indexOf('native');if(!['throw','false'].includes(mode))assert.equal(after.trace[index+1],'poll');
  if(['missing','untrusted','wrong'].includes(mode)){assert.equal(after.clock,75);assert.equal(after.polls,3);}
 }
});
test('actual original/adapted shell click preserves one post and the existing trusted predicate',async()=>{
 const adapted=A.transform(original,{verifyAdapted:false});
 for(const mode of ['delayed','missing','untrusted','wrong','false','throw']){
  const nativeError=Error('shell exact '+mode),before=await runNested(original,{shell:true,mode,nativeError}),after=await runNested(adapted,{shell:true,mode,nativeError});
  assert.deepEqual(after.trace,before.trace);assert.equal(after.calls,1);assert.equal(after.observer.posts.length,1);assert.equal(after.clock,before.clock);
  if(mode==='delayed'){assert.equal(after.error,undefined);assert.deepEqual(after.result.events,before.result.events);}
  else{assert.ok(after.error);assert.equal(after.error.message,before.error.message);if(mode==='throw')assert.equal(after.error,nativeError);}
 }
});

function hookEnvironment(change=()=>{}){
 const adapted=A.transform(original,{verifyAdapted:false}),contract={...A.CONTRACT,adaptedSha256:transport.sha(adapted)};
 const appPath='/owned/Установка Mouse/Mouse Browser.app/Contents/Resources/app.asar',executable='/owned/Установка Mouse/Mouse Browser.app/Contents/MacOS/Mouse Browser';
 const config={pid:123,controllerPid:321,nonce:'b'.repeat(64),publisherSHA:'a'.repeat(40),phase:'retained',flag:contract.flag,executable,appPath,
  profile:'/owned/retained636',output:'/evidence',receipt:'/evidence/mouse-637-guest-input-observer-bootstrap.json'};
 const target=appPath+'/mouse-636-retained-smoke.cjs',main=fs.readFileSync(path.join(__dirname,'fixtures/mouse637-readiness-002-main.cjs'));
 const files=new Map([[target,Buffer.from(original)],[appPath+'/mouse-main.cjs',main]]),events=[];
 let closed=false;const previous=function(){events.push('unrelated-loader');};const Module={_extensions:{'.js':previous}};
 const fakeProcess={pid:123,execPath:executable,platform:'darwin',arch:'arm64',argv:[executable,contract.flag],versions:{node:process.versions.node},env:{CI:'true',MOUSE_TEST_PROFILE:config.profile,MOUSE_637_GUEST_INPUT_NONCE:config.nonce}};
 const electron={app:{getAppPath:()=>appPath,isPackaged:true,getVersion:()=>contract.version,isReady:()=>true,getPath:()=>config.profile,getName:()=>'Mouse Browser'}};
 const fakeFs={realpathSync:p=>p,readFileSync(p){assert.ok(files.has(p),p);return files.get(p);},existsSync:p=>files.has(p),writeFileSync(p,bytes,opt){assert.equal(opt.flag,'wx');assert.equal(files.has(p),false);files.set(p,Buffer.from(bytes));events.push('write:'+path.basename(p));},linkSync(a,b){assert.equal(files.has(b),false);files.set(b,files.get(a));},unlinkSync:p=>files.delete(p)};
 const load=id=>({electron,'node:module':Module,'node:fs':fakeFs,'node:inspector':{close(){closed=true;events.push('close');},url:()=>closed?undefined:'ws://127.0.0.1/owned'}}[id]||require(id));
 load.resolve=x=>x;load.cache={};
 const state={config,contract,adapted,target,files,events,Module,previous,fakeProcess,load,electron};change(state);
 const context=vm.createContext({process:fakeProcess,console:{log:line=>events.push('log:'+line)},Date});
 fakeProcess.argv=vm.runInContext(JSON.stringify(fakeProcess.argv),context);
 const hook=vm.runInContext('('+A.installOwnedHook.toString()+')',context);
 const install=()=>hook(load,config,contract,adapted);
 const compile=()=>{
  const module={exports:{},_compile(code,filename){assert.equal(Module._extensions['.js'],previous);assert.equal(closed,true);assert.equal(filename,target);events.push('compile');
   const requireFixture=id=>id==='electron'?{}:id.startsWith('./')?{}:require(id);
   vm.runInNewContext(code,{module:this,require:requireFixture,process:fakeProcess,console,URL,Buffer,Date,crypto:require('node:crypto')});
  }};
  Module._extensions['.js'](module,target);return module;
 };
 return{...state,install,compile};
}
test('actual one-shot hook validates full identity, restores loader and closes inspector before adapted compile',()=>{
 const state=hookEnvironment(),installed=state.install();assert.equal(installed.pid,123);assert.equal(installed.fullRuntimeIdentity.argv[1],A.CONTRACT.flag);
 const hook=state.Module._extensions['.js'];hook({},'/unrelated.cjs');assert.equal(state.events.at(-1),'unrelated-loader');
 const module=state.compile();assert.equal(typeof module.exports,'function');assert.equal(module.__mouse637DeliveryConfig,undefined);
 assert.equal(state.Module._extensions['.js'],state.previous);assert.ok(state.events.indexOf('close')<state.events.indexOf('compile'));
 const receipt=JSON.parse(state.files.get(state.config.receipt));assert.equal(receipt.loaderRestored,true);assert.equal(receipt.inspectorClosed,true);assert.equal(receipt.applications,1);
 assert.equal(receipt.fullRuntimeIdentity.pid,123);assert.equal(receipt.fullRuntimeIdentity.nonce,state.config.nonce);
 assert.equal(transport.sha(state.files.get(state.target)),A.CONTRACT.originalSha256);
 assert.throws(()=>hook({},state.target));
});
test('one-shot hook rejects wrong PID, nonce, executable, flag, original bytes, main bytes or preloaded fixture',()=>{
 for(const mutate of [x=>x.fakeProcess.pid++,x=>x.fakeProcess.env.MOUSE_637_GUEST_INPUT_NONCE='wrong',x=>x.fakeProcess.execPath='/wrong',
  x=>x.fakeProcess.argv=[x.config.executable,'--mouse-other'],x=>x.files.set(x.target,Buffer.from('wrong original')),
  x=>x.files.set(x.config.appPath+'/mouse-main.cjs',Buffer.from('wrong main')),x=>x.load.cache[x.target]={exports:()=>{}},
  x=>x.electron.app.isPackaged=false]){
  const state=hookEnvironment(mutate);assert.throws(state.install);assert.equal(state.Module._extensions['.js'],state.previous);
  assert.equal(state.events.includes('close'),false);assert.equal(state.events.includes('compile'),false);
 }
});
test('observer errors remain bounded and disposal is safe even before a fixture is assigned',()=>{
 const x=environment();x.observer.start();const wc=x.addGuest();
 wc.emit('console-message',{message:'MOUSE_637_GUEST_INPUT_OBSERVER_DOM {broken',frame:wc.mainFrame});
 let calls=0;const value=x.observer.post({testClick(){calls++;wc.emit('input-event',{}, {type:'mouseDown'});return true;}},104,252);
 assert.equal(value,true);assert.equal(calls,1);assert.equal(x.observer.snapshot().stats.errors,1);
 x.observer.dispose();x.observer.dispose();assert.equal(wc.listenerCount('console-message'),0);assert.equal(x.win.listenerCount('focus'),0);
 assert.equal(x.observer.snapshot().disposed,true);assert.equal(x.observer.snapshot().records.some(r=>r.source==='observer-error'),true);
});
test('destroyed WebContents uses its captured identity after native getters become unavailable',()=>{
 const x=environment();x.observer.start();const wc=x.addGuest();
 let reads=0;Object.defineProperty(wc,'id',{get(){reads++;throw Error('WebContents native pointer cleared');}});
 wc.emit('destroyed');
 const state=x.observer.snapshot();assert.equal(reads,0);assert.equal(state.stats.errors,0);
 assert.equal(state.registeredWebContents.find(row=>row.id===2).destroyed,true);
 x.observer.dispose();assert.equal(reads,0);assert.equal(wc.listenerCount('destroyed'),0);
});
