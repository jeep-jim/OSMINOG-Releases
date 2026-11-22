'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),os=require('node:os'),cp=require('node:child_process');
const A=require('./mouse637-feature-readiness.cjs');
const fixture=name=>fs.readFileSync(path.join(__dirname,'fixtures','mouse637-readiness-002-'+name),'utf8');
const source=fixture('features.cjs'),adapted=A.transform(source),shared=fixture('fixture.cjs'),ui=fixture('extensions.js');
const untilSource=shared.slice(shared.indexOf(' async function until('),shared.indexOf('\n const frame=',shared.indexOf(' async function until(')));
const copy=value=>JSON.parse(JSON.stringify(value));

// Minimal DOM executes the actual frozen extensions renderer; timing is an
// unresolved IPC response, not a fabricated button inserted by the test helper.
class Element{
 constructor(tag,id=''){this.tagName=tag.toUpperCase();this.id=id;this.children=[];this.dataset={};this.attributes={};this.disabled=false;this.open=false;this.isConnected=true;this._text='';this.className='';}
 set textContent(v){this._text=v;this.children=[];}get textContent(){return this._text+this.children.map(x=>x.textContent).join('');}
 append(...rows){this.children.push(...rows);}replaceChildren(...rows){this._text='';this.children=[...rows];}
 setAttribute(k,v){this.attributes[k]=v;}addEventListener(){}focus(){}close(){this.open=false;}cloneNode(){return new Element(this.tagName);}
 querySelector(selector){return selector==='svg'?new Element('svg'):this.querySelectorAll(selector)[0]||null;}
 querySelectorAll(selector){const out=[];const walk=e=>{for(const child of e.children){if(selector==='button'&&child.tagName==='BUTTON'||selector.startsWith('.')&&child.className.split(' ').includes(selector.slice(1)))out.push(child);walk(child);}};walk(this);return out;}
}
async function scene(options={}){
 let clock=0,dead=options.deadline??150,clicked=0,pending=null;const receipt={kind:'synthetic-unit-click',trusted:true};
 const ids=['mouse-extensions-tray','mouse-extensions-button','mouse-extensions-pins','mouse-extensions-dialog','mouse-extensions-list','mouse-extensions-install','mouse-extensions-status','mouse-extensions-title','mouse-extensions-note'];
 const elements=Object.fromEntries(ids.map(id=>[id,new Element(id.includes('button')||id.endsWith('install')?'button':'div',id)]));elements['mouse-extensions-dialog'].open=true;
 const entry={id:'owned-extension',name:'Fixture',version:'1.0',enabled:true,pinned:false,actionPopup:true};
 const rows=()=>elements['mouse-extensions-list'].children.filter(x=>x.className==='mouse-extension-row');
 const query=selector=>{
  if(selector==='#mouse-extensions-pins .mouse-extension-pin')return elements['mouse-extensions-pins'].children.filter(x=>x.className==='mouse-extension-pin');
  const match=/^\.mouse-extension-row\[data-id="([^"]+)"\] \.mouse-extension-actions>button(?::nth-child\((\d+)\))?$/.exec(selector);
  if(!match)throw Error('Unexpected actual serialized selector '+selector);
  const row=rows().find(x=>x.dataset.id===match[1]),buttons=row?.children.find(x=>x.className==='mouse-extension-actions')?.children||[];
  return match[2]?(buttons[Number(match[2])-1]?[buttons[Number(match[2])-1]]:[]):buttons;
 };
 const document={documentElement:{lang:'ru',dataset:{}},getElementById:id=>elements[id],createElement:tag=>new Element(tag),querySelectorAll:query};
 const renderer=vm.createContext({document,MutationObserver:class{observe(){}},console});vm.runInContext(ui,renderer);
 const service={extensions:async(action,args)=>{
  if(action==='state')return options.preReady?[copy(entry)]:[];
  if(action==='install')return new Promise(resolve=>{pending={at:options.preDelay??50,resolve,value:[copy(entry)]};});
  if(action==='set-pinned'){assert.equal(args.id,entry.id);assert.equal(args.value,true);return new Promise(resolve=>{pending={at:clock+(options.postDelay??50),resolve,value:options.postRows??[{...copy(entry),pinned:true}]};});}
  if(action==='remove')return[];
  throw Error(action);
 }};
 renderer.createMouseExtensionsUI({N:service,showDialog:async d=>{d.open=true},placeTab:async()=>{}});
 for(let i=0;elements['mouse-extensions-install'].disabled&&i<10;i++)await Promise.resolve();
 assert.equal(elements['mouse-extensions-install'].disabled,false,'Initial actual renderer state response settled');
 if(!options.preReady){elements['mouse-extensions-install'].onclick();await Promise.resolve();}
 const harness=vm.createContext({assert,fixture:null,click:null,performance:{now:()=>clock},deadline:dead,name:'readiness-unit',sleep:async ms=>{
  clock+=ms;if(pending&&clock>=pending.at){const event=pending;pending=null;event.resolve(event.value);}await Promise.resolve();await Promise.resolve();
 }});
 const js=async text=>{if(options.readbackError)throw Error('actual renderer read rejected');return copy(vm.runInContext(text,renderer));};
 const fixtureApi={js,until:vm.runInContext('('+untilSource+')',harness)};
 harness.fixture=fixtureApi;harness.click=async selector=>{
  clicked++;if(options.clickError)throw Error(options.clickError);
  const button=query(selector)[0];assert.ok(button);assert.equal(button.disabled,false);button.onclick();await Promise.resolve();return receipt;
 };
 const call=(old=false,id=entry.id,label='Закрепить')=>vm.runInContext('('+(old?A.ORIGINAL.trimStart():A.REPLACEMENT.trimStart())+')',harness)(id,label);
 return{call,fixture:fixtureApi,receipt,get clicked(){return clicked},get clock(){return clock},pins:()=>query('#mouse-extensions-pins .mouse-extension-pin').length,entry,renderer};
}

test('exact source and single nested-function transform retain all other bytes',()=>{
 assert.equal(A.sha(source),A.CONTRACT.originalSha256);assert.equal(A.sha(adapted),A.CONTRACT.adaptedSha256);
 assert.equal(A.sha(A.ORIGINAL),'1d781585ba41ce2fc25156aa87bc72e97aa03c1435fd0a94790395f1610ed0bf');
 assert.equal(adapted.replace(A.REPLACEMENT,A.ORIGINAL),source);
 for(const changed of [source+'\n',source.replace('BUDGET=240000','BUDGET=240001'),source.replace(A.ORIGINAL,'')])assert.throws(()=>A.transform(changed));
 assert.ok(source.includes('await extensionButton(entry.id,\'Закрепить\');await fixture.until(()=>extensions.state().find(e=>e.id===entry.id)?.pinned,\'persisted extension pin\');'));
 assert.ok(adapted.includes('assert.equal(await fixture.js(\'document.querySelectorAll("#mouse-extensions-pins .mouse-extension-pin").length\'),1);'));
});
test('RED original one-shot lookup fails while actual renderer IPC is pending; GREEN awaits exact row',async()=>{
 const red=await scene();await assert.rejects(()=>red.call(true),/Extension action Закрепить/);assert.equal(red.clicked,0);
 const green=await scene();assert.equal(await green.call(),green.receipt);assert.equal(green.clicked,1);assert.equal(green.pins(),1);assert.equal(green.clock,100);
});
test('RED original returns before actual pin render and original count assertion fails; GREEN awaits same-row unpin plus one pin',async()=>{
 const red=await scene({preReady:true});assert.equal(await red.call(true),red.receipt);assert.throws(()=>assert.equal(red.pins(),1));assert.equal(red.clicked,1);
 const green=await scene({preReady:true});assert.equal(await green.call(),green.receipt);assert.equal(green.pins(),1);assert.equal(green.clicked,1);assert.equal(green.clock,50);
});
test('missing or wrong exact ID/label times out without a native input',async()=>{
 for(const values of [{preDelay:1000},{preReady:true,id:'wrong-id'},{preReady:true,label:'wrong-label'}]){
  const x=await scene({...values,deadline:100});await assert.rejects(()=>x.call(false,values.id||x.entry.id,values.label||'Закрепить'),/timeout: Extension action/);assert.equal(x.clicked,0);assert.equal(x.clock,100);
 }
});
test('missing/wrong owned post-pin row or zero/two pins fails without a second click',async()=>{
 for(const postRows of [[],[{id:'wrong-id',enabled:true,pinned:true}],[{id:'owned-extension',enabled:true,pinned:false}],
   [{id:'owned-extension',enabled:true,pinned:true},{id:'other',enabled:true,pinned:true}]]){
  const x=await scene({preReady:true,postRows});await assert.rejects(()=>x.call(),/timeout: Extension pin renderer/);assert.equal(x.clicked,1);
 }
});
test('renderer read failures and original native click failures propagate',async()=>{
 const read=await scene({preReady:true,readbackError:true});await assert.rejects(()=>read.call(),/renderer read rejected/);assert.equal(read.clicked,0);
 for(const clickError of ['native input rejected','637 trusted click absent']){
  const x=await scene({preReady:true,clickError});await assert.rejects(()=>x.call(),new RegExp(clickError));assert.equal(x.clicked,1);
 }
});
test('pre and post waits share original global deadline; ordinary remove adds no post-pin wait',async()=>{
 const x=await scene({preDelay:50,postDelay:75,deadline:100});await assert.rejects(()=>x.call(),/timeout: Extension pin renderer/);assert.equal(x.clock,100);assert.equal(x.clicked,1);
 const remove=await scene({preReady:true});assert.equal(await remove.call(false,remove.entry.id,'Убрать из Mouse'),remove.receipt);assert.equal(remove.clock,0);assert.equal(remove.clicked,1);
});

function bootstrapFixture(change={}){
 const appPath='/owned/Mouse Browser.app/Contents/Resources/app.asar',executable='/owned/Mouse Browser.app/Contents/MacOS/Mouse Browser',profile='/owned/profiles/features637',output='/owned/evidence';
 const config={schema:1,phase:'write',flag:'--mouse-637-features-smoke',pid:41177,controllerPid:41178,nonce:'a'.repeat(64),port:41237,executable,appPath,profile,output,receipt:output+'/mouse-637-feature-readiness-write.json',controllerReceipt:output+'/mouse-637-feature-readiness-controller-write.json',deadlineEpochMs:Date.now()+10000};
 const files=new Map([[appPath+'/mouse-main.cjs',fixture('main.cjs')],[appPath+'/mouse-637-features-smoke.cjs',source]]),order=[];
 let active=true,compiles=0;const previous=()=>{order.push('original-other-module');};const modules={_extensions:{'.js':previous}};
 const nativeProcess={pid:41177,execPath:executable,platform:'darwin',arch:'arm64',versions:{electron:'44.5.0',node:'unit'},env:{CI:'true',MOUSE_TEST_PROFILE:profile,MOUSE_637_FEATURE_READINESS_NONCE:config.nonce},argv:[executable,config.flag]};
 const nodefs={realpathSync:value=>value,readFileSync:(name,encoding)=>{assert.ok(files.has(name),name);return encoding?files.get(name):Buffer.from(files.get(name));},existsSync:name=>files.has(name),writeFileSync:(name,value,options)=>{assert.equal(options.flag,'wx');assert.equal(files.has(name),false);files.set(name,value);order.push('write:'+path.basename(name));}};
 nodefs.linkSync=(from,to)=>{assert.equal(files.has(to),false);assert.ok(files.has(from));files.set(to,files.get(from));order.push('atomic-receipt');};
 nodefs.unlinkSync=name=>{assert.equal(files.delete(name),true);};
 const electron={app:{isPackaged:true,getAppPath:()=>appPath,getVersion:()=> '6.0.37',isReady:()=>true,getPath:()=>profile,getName:()=> 'Mouse Browser'}};
 const inspector={close(){active=false;order.push('inspector-close')},url(){return active?'ws://127.0.0.1':undefined}};
 const load=name=>({'node:assert/strict':assert,'node:fs':nodefs,'node:path':path,'node:crypto':require('node:crypto'),'electron':electron,'node:module':modules,'node:inspector':inspector}[name]);load.resolve=x=>x;load.cache={};
 change.mutate?.({config,files,nativeProcess,electron,inspector,load});
 const context=vm.createContext({load,config,contract:A.CONTRACT,original:A.ORIGINAL,replacement:A.REPLACEMENT,processJSON:JSON.stringify(nativeProcess),console:{log(){order.push('receipt-log')}}});vm.runInContext('globalThis.process=JSON.parse(processJSON)',context);
 const install=()=>vm.runInContext('('+A.installOwnedHook.toString()+')(load,config,contract,original,replacement)',context);
 const module={exports:null,_compile(bytes,filename){assert.equal(modules._extensions['.js'],previous);assert.equal(active,false);assert.equal(A.sha(bytes),A.CONTRACT.adaptedSha256);assert.equal(filename,appPath+'/mouse-637-features-smoke.cjs');compiles++;order.push('compile');this.exports=async()=>{};}};
 return{install,modules,previous,module,config,files,order,get compiles(){return compiles}};
}
test('bootstrap defers fixture load, restores exact loader and closes server before compilation/input',()=>{
 const x=bootstrapFixture();assert.equal(x.install().installed,true);assert.equal(x.compiles,0);
 x.modules._extensions['.js']({},'/owned/product.cjs');assert.deepEqual(x.order,['original-other-module']);
 x.modules._extensions['.js'](x.module,x.config.appPath+'/mouse-637-features-smoke.cjs');
 assert.equal(x.modules._extensions['.js'],x.previous);assert.equal(x.compiles,1);assert.ok(x.order.indexOf('inspector-close')<x.order.indexOf('compile'));
 const r=JSON.parse(x.files.get(x.config.receipt));assert.equal(r.pid,41177);assert.equal(r.nonce,x.config.nonce);assert.equal(r.applications,1);assert.equal(r.inspectorClosed,true);assert.equal(r.loaderRestored,true);
});
test('bootstrap fails closed for wrong runtime/phase/PID/nonce/executable/source or existing cache',()=>{
 const mutations=[x=>x.nativeProcess.pid++,x=>x.nativeProcess.platform='linux',x=>x.nativeProcess.env.CI='false',x=>x.nativeProcess.env.MOUSE_637_FEATURE_READINESS_NONCE='b'.repeat(64),
  x=>x.nativeProcess.execPath='/other/exe',x=>x.config.phase='read',x=>x.nativeProcess.env.MOUSE_TEST_PROFILE='/other/profile',x=>x.electron.app.isPackaged=false,
  x=>x.files.set(x.config.appPath+'/mouse-637-features-smoke.cjs',source+'\n'),x=>x.files.set(x.config.appPath+'/mouse-main.cjs','other'),
  x=>x.load.cache[x.config.appPath+'/mouse-637-features-smoke.cjs']={}];
 for(const mutate of mutations){const x=bootstrapFixture({mutate});assert.throws(x.install);assert.equal(x.modules._extensions['.js'],x.previous);assert.equal(x.compiles,0);}
});
test('hook rejects changed target bytes and a server that did not close without compiling',()=>{
 for(const kind of ['bytes','inspector']){
  const x=bootstrapFixture({mutate:kind==='inspector'?x=>{x.inspector.close=()=>{}}:undefined});x.install();if(kind==='bytes')x.files.set(x.config.appPath+'/mouse-637-features-smoke.cjs',source+'\n');
  assert.throws(()=>x.modules._extensions['.js'](x.module,x.config.appPath+'/mouse-637-features-smoke.cjs'));assert.equal(x.compiles,0);assert.equal(x.modules._extensions['.js'],x.previous);
 }
});
test('paused-frame identity requires a known parsed script and rejects conflicting direct URLs',()=>{
 const owned='file:///owned/app.asar/mouse-main.cjs',scripts=new Map([['1',owned],['2','file:///unowned.cjs']]);
 assert.equal(A.frameURL({location:{scriptId:'1'},url:''},scripts),owned);
 assert.equal(A.frameURL({location:{scriptId:'unknown'},url:owned},scripts),undefined);
 assert.equal(A.frameURL({location:{scriptId:'2'},url:''},scripts),'file:///unowned.cjs');
 assert.throws(()=>A.frameURL({location:{scriptId:'2'},url:owned},scripts),/disagrees/);
 assert.throws(()=>A.frameURL({location:{scriptId:'1'},url:'file:///wrong.cjs'},scripts),/disagrees/);
});

test('actual Node Inspector transport observes owned paused main frame and actual child PID',async()=>{
 const directory=fs.mkdtempSync(path.join(os.tmpdir(),'mouse637-readiness-inspector-'));
 const installed=path.join(directory,'Установка Mouse','Mouse Browser.app','Contents','Resources','app.asar');fs.mkdirSync(installed,{recursive:true});
 const main=path.join(installed,'mouse-main.cjs');fs.writeFileSync(main,'setImmediate(()=>require("node:inspector").close());setInterval(()=>{},1000);\n');
 const child=cp.spawn(process.execPath,['--inspect-brk=127.0.0.1:0',main],{stdio:['ignore','pipe','pipe']});let client;
 try{
  const deadline=Date.now()+8000,remaining=()=>{assert.ok(Date.now()<deadline);return deadline-Date.now()};
  const url=await new Promise((resolve,reject)=>{let text='';const timer=setTimeout(()=>reject(Error('Node inspector start')),5000);child.stderr.on('data',data=>{text+=data;const match=text.match(/ws:\/\/127\.0\.0\.1:\d+\/[\w-]+/);if(match){clearTimeout(timer);resolve(match[0]);}});child.once('error',reject);});
  client=await A.connect(url,remaining);await client.send('Debugger.enable');await client.send('Runtime.runIfWaitingForDebugger');const paused=await client.event('Debugger.paused');
  const frame=paused.callFrames.find(f=>client.scriptURL(f)===require('node:url').pathToFileURL(main).href);assert.ok(frame);
  const result=await client.send('Debugger.evaluateOnCallFrame',{callFrameId:frame.callFrameId,expression:'process.pid',returnByValue:true});assert.equal(result.result.value,child.pid);
  await client.send('Debugger.resume');await client.close();client=null;
  const endpoint=url.replace('ws:','http:').replace(/\/[\w-]+$/,'/json/list');let refused=false;
  while(!refused){remaining();try{await fetch(endpoint,{signal:AbortSignal.timeout(100)});}catch{refused=true;}}
  assert.equal(child.exitCode,null,'Inspector server closes while the owned process remains alive');
 }finally{if(client)await client.close().catch(()=>{});child.kill();await new Promise(resolve=>child.once('exit',resolve));fs.rmSync(directory,{recursive:true,force:true});}
});
