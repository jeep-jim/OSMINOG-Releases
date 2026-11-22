'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {EventEmitter}=require('node:events');
const {CONTRACT,createTrace,transform,installOwnedHook,assertRuntimeIdentity}=require('./mouse637-performance-trace.cjs');
const {sha}=require('./mouse637-feature-readiness.cjs');
const original=fs.readFileSync(path.join(__dirname,'fixtures/mouse637-performance-002-stress.cjs'),'utf8');
const parent=fs.readFileSync(path.join(__dirname,'fixtures/mouse637-performance-002-native.cjs'),'utf8');
const main=fs.readFileSync(path.join(__dirname,'fixtures/mouse637-readiness-002-main.cjs'),'utf8');
const clone=value=>structuredClone(value);

function timers(){
 let time=100;const pending=new Map();let sequence=0;
 return{now:()=>time,set(fn,ms){const h={id:++sequence,at:time+ms,ms,fn,unref(){}};pending.set(h.id,h);return h;},clear(h){if(h)pending.delete(h.id);},
  fireNext(){const h=[...pending.values()].sort((a,b)=>a.at-b.at)[0];assert.ok(h,'Expected pending diagnostic timeout');pending.delete(h.id);time=h.at;h.fn();},pending};
}
function harness(options={}){
 const timer=timers(),writes=new Map(),calls=[],debug=new EventEmitter();let attached=true,read=0;
 const config={...clone(CONTRACT),nonce:'a'.repeat(64),publisherSHA:'b'.repeat(40),output:'/owned/diagnostic',limits:{...CONTRACT.limits,...options.limits}};
 const bytes=Buffer.from(JSON.stringify({traceEvents:[{ph:'M',pid:process.pid,tid:1,name:'process_name',args:{name:'Browser'}},{ph:'X',pid:process.pid+1,tid:2,name:'Layout',ts:1000,dur:4,args:{text:'данные'}}]}));
 const chunks=[bytes.subarray(0,80),bytes.subarray(80),Buffer.alloc(0)];
 debug.isAttached=()=>attached;
 debug.detach=()=>{throw Error('Diagnostic must never detach the borrowed session');};
 debug.sendCommand=async(method,params)=>{
  calls.push({method,params:clone(params),at:timer.now()});
  if(options.command){const value=options.command(method,params,{debug,read,calls,timer});if(value!==undefined)return value;}
  if(method==='Browser.getVersion')return{protocolVersion:'1.3',product:'Chrome/152.0.7977.130',revision:'pinned',userAgent:'owned',jsVersion:'15.2'};
  if(method==='Tracing.getCategories')return{categories:clone(CONTRACT.categories)};
  if(method==='Tracing.start')return{};
  if(method==='Runtime.evaluate'){
   if(params.expression.includes('performance.mark')){
    const name=JSON.parse(params.expression.match(/const name=("[^"]+")/)[1]);
    return{result:{value:{name,startTime:name.endsWith('begin')?10:30,timeOrigin:1700000000000,now:name.endsWith('begin')?10.1:30.1}}};
   }
   return{result:{value:true}};
  }
  if(method==='Tracing.end'){
   // Complete can precede the command response; listener must already exist.
   debug.emit('message',{},'Tracing.tracingComplete',{dataLossOccurred:options.loss===true,stream:'stream-1',traceFormat:'json',streamCompression:'none'});
   return{};
  }
  if(method==='IO.read'){
   const chunk=chunks[read]??Buffer.alloc(0),base64=read===1;read++;
   return{data:base64?chunk.toString('base64'):chunk.toString('utf8'),base64Encoded:base64,eof:read>=chunks.length};
  }
  if(method==='IO.close')return{};
  throw Error('Unexpected command '+method);
 };
 const fixture={started:0,deadline:200000,win:{webContents:{id:1,getOSProcessId:()=>process.pid+1}}};
 const write=(file,data)=>{if(options.write){const result=options.write(file,data);if(result!==undefined)return result;}assert.equal(writes.has(file),false);writes.set(file,Buffer.isBuffer(data)?Buffer.from(data):Buffer.from(data));return Promise.resolve();};
 const trace=createTrace({ctx:{},fixture,debug,config},{now:timer.now,clock:()=>1700000000000+timer.now(),setTimeout:timer.set,clearTimeout:timer.clear,write});
 const row={ownedPageCount:20,switchCount:5,switches:Array.from({length:5},(_,i)=>({sequence:i+1,elapsedMs:50,slide:{startedAt:i*100,totalDurationMs:40}}))};
 return{trace,timer,writes,calls,debug,config,fixture,row,bytes,detach(){attached=false;debug.emit('detach',{},'unexpected');}};
}
async function ticks(n=12){for(let i=0;i<n;i++)await Promise.resolve();}

test('exact002 stress transform reverses and keeps the whole original five-switch loop and predicates unchanged',()=>{
 assert.equal(sha(original),CONTRACT.originalSha256);assert.equal(sha(parent),CONTRACT.parentSha256);
 const adapted=transform(original);new vm.Script(adapted);
 const from='   for(let n=0;n<switchCount;n++){',to="   operation='nora';";
 const before=original.slice(original.indexOf(from),original.indexOf(to));
 const after=adapted.slice(adapted.indexOf(from),adapted.indexOf('   if(target===20)await __mouse637Trace.stop(row);'));
 assert.equal(after,before);assert.equal((adapted.match(/if\(target===20\)await __mouse637Trace\./g)||[]).length,2);
 assert.ok(adapted.includes('budgetMs:200000'));assert.ok(parent.includes('budgetMs:350000'));
 assert.throws(()=>transform(original+'\n'),/Unexpected exact002/);
});

test('acknowledged stream keeps byte and encoding receipts, explicit EOF, own cleanup and zero eventCount',async()=>{
 const h=harness();assert.equal(await h.trace.start(h.row),true);
 h.debug.emit('message',{},'Tracing.bufferUsage',{percentFull:.1,eventCount:0,value:.1});
 const before=h.calls.length;for(let i=0;i<5;i++){/* original workload is unchanged in the fixture test above */}
 assert.equal(h.calls.length,before);
 assert.equal(await h.trace.stop(h.row),true);await h.trace.dispose();
 assert.equal(h.trace.report.ok,true);assert.equal(h.trace.report.startAcknowledged,true);
 assert.equal(h.trace.report.reads.length,3);assert.equal(h.trace.report.reads.at(-1).decodedBytes,0);assert.equal(h.trace.report.reads.at(-1).eof,true);
 assert.equal(h.trace.report.reads[1].base64Encoded,true);
 assert.deepEqual(h.writes.get('/owned/diagnostic/mouse-637-performance-trace-data.json'),h.bytes);
 assert.equal(h.debug.listenerCount('message'),0);assert.equal(h.debug.listenerCount('detach'),0);
 assert.equal(h.calls.filter(x=>x.method==='Tracing.start').length,1);assert.equal(h.calls.filter(x=>x.method==='Tracing.end').length,1);
 assert.equal(h.calls.filter(x=>x.method==='IO.close').length,1);
 assert.ok(!('excludedCategories'in h.trace.report.startParams.traceConfig));
 assert.deepEqual(h.trace.report.startParams.traceConfig.includedCategories,CONTRACT.categories);
});

test('missing required runtime category and rejected start never authorize End',async()=>{
 for(const command of [method=>method==='Tracing.getCategories'?{categories:['toplevel']}:undefined,
  method=>{if(method==='Tracing.start')return Promise.reject(Error('already owned by another session'));}]){
  const h=harness({command});assert.equal(await h.trace.start(h.row),false);await h.trace.dispose();
  assert.equal(h.calls.some(x=>x.method==='Tracing.end'),false);assert.equal(h.trace.report.ok,false);
  assert.equal(h.trace.report.startPendingAtDisposal,false);
  if(h.trace.report.startSubmitted)assert.equal(h.trace.report.startRejected,true);
 }
});

test('late start acknowledgment after bounded setup authorizes only owned cleanup, never a valid trace',async()=>{
 let acknowledge;const h=harness({command:method=>method==='Tracing.start'?new Promise(resolve=>{acknowledge=resolve;}):undefined});
 const start=h.trace.start(h.row);await ticks(40);assert.equal(typeof acknowledge,'function');h.timer.fireNext();assert.equal(await start,false);
 assert.equal(h.trace.report.startWaitTimedOut,true);assert.notEqual(h.trace.report.startRejected,true);
 assert.equal(h.calls.some(x=>x.method==='Tracing.end'),false);
 acknowledge({});await ticks(20);assert.equal(h.trace.report.startAcknowledged,true);assert.equal(h.trace.report.lateStartAcknowledgment,true);
 await h.trace.dispose();assert.equal(h.calls.filter(x=>x.method==='Tracing.end').length,1);assert.equal(h.trace.report.ok,false);
});

test('rejected start cannot adopt, read or close a foreign completion stream or buffer event',async()=>{
 const h=harness({command:method=>method==='Tracing.start'?Promise.reject(Error('another trace owns this session')):undefined});
 assert.equal(await h.trace.start(h.row),false);
 h.debug.emit('message',{},'Tracing.tracingComplete',{dataLossOccurred:false,stream:'foreign-stream'});
 h.debug.emit('message',{},'Tracing.bufferUsage',{percentFull:.5,eventCount:0});
 h.debug.emit('message',{},'Tracing.dataCollected',{value:[{name:'foreign'}]});
 await h.trace.dispose();
 assert.equal(h.trace.report.startRejected,true);assert.equal(h.trace.report.startPendingAtDisposal,false);
 assert.equal(h.trace.report.completion,undefined);assert.deepEqual(h.trace.report.bufferUsage,[]);
 assert.equal(h.trace.report.errors.filter(x=>x.where==='unowned-tracing-event').length,3);
 assert.equal(h.calls.some(x=>['Tracing.end','IO.read','IO.close'].includes(x.method)),false);
 assert.equal(h.trace.report.streamClosed,false);assert.equal(h.trace.report.ok,false);
});

test('known packet loss preserves raw bytes but rejects completeness',async()=>{
 const h=harness({loss:true});await h.trace.start(h.row);assert.equal(await h.trace.stop(h.row),false);await h.trace.dispose();
 assert.equal(h.trace.report.completion.dataLossOccurred,true);assert.equal(h.trace.report.streamClosed,true);assert.equal(h.trace.report.ok,false);
 assert.deepEqual(h.writes.get('/owned/diagnostic/mouse-637-performance-trace-data.json'),h.bytes);
});

test('IO malformed encoding, non-EOF empty chunk, cap and failure still close the owned stream',async()=>{
 const cases=[
  {command:m=>m==='IO.read'?{data:'???',base64Encoded:true,eof:true}:undefined},
  {command:m=>m==='IO.read'?{data:'',eof:false}:undefined},
  {limits:{maxOutputBytes:1},command:m=>m==='IO.read'?{data:'xx',eof:false}:undefined},
  {command:m=>m==='IO.read'?Promise.reject(Error('read failed')):undefined}
 ];
 for(const options of cases){const h=harness(options);await h.trace.start(h.row);assert.equal(await h.trace.stop(h.row),false);await h.trace.dispose();
  assert.equal(h.trace.report.ok,false);assert.equal(h.calls.filter(x=>x.method==='IO.close').length,1);assert.equal(h.debug.listenerCount('message'),0);}
});

test('active cap is incomplete and sends one End without replaying the original operations',async()=>{
 const h=harness();await h.trace.start(h.row);h.timer.fireNext();await ticks();
 assert.equal(h.trace.report.activeCapExceeded,true);assert.equal(await h.trace.stop(h.row),false);await h.trace.dispose();
 assert.equal(h.trace.report.ok,false);assert.equal(h.calls.filter(x=>x.method==='Tracing.end').length,1);assert.equal(h.trace.report.marks.length,1);
});

test('pending receipt and throwing listener cleanup are bounded and cannot escape disposal',async()=>{
 const h=harness({write:file=>file.endsWith('session.json')?new Promise(()=>{}):undefined});
 await h.trace.start(h.row);await h.trace.stop(h.row);
 const originalRemove=h.debug.removeListener.bind(h.debug);h.debug.removeListener=(type,fn)=>{if(type==='message')throw Error('remove failed');return originalRemove(type,fn);};
 const disposing=h.trace.dispose();await ticks(20);h.timer.fireNext();await disposing;
 assert.equal(h.trace.report.ok,false);assert.ok(h.trace.report.errors.some(x=>x.where==='remove-listener-message'));
 assert.ok(h.trace.report.errors.some(x=>x.where==='save-receipt'));
});

test('pending protocol read is bounded by existing fixture deadline and never detaches source debugger',async()=>{
 const h=harness({command:m=>m==='IO.read'?new Promise(()=>{}):undefined});await h.trace.start(h.row);
 h.fixture.deadline=h.timer.now()+7;const stop=h.trace.stop(h.row);await ticks(30);h.timer.fireNext();assert.equal(await stop,false);
 await h.trace.dispose();assert.equal(h.trace.report.ok,false);assert.equal(h.trace.report.streamClosed,false);
});

test('slow end mark and pending read share one15s drain deadline without reset',async()=>{
 const h=harness({command:(method,params,{timer})=>{
  if(method==='Runtime.evaluate'&&params.expression.includes('performance.mark')&&params.expression.includes('-end\"')){
   const name=JSON.parse(params.expression.match(/const name=(\"[^\"]+\")/)[1]);
   return new Promise(resolve=>timer.set(()=>resolve({result:{value:{name,startTime:30,timeOrigin:1700000000000,now:30.1}}}),14000));
  }
  if(method==='IO.read')return new Promise(()=>{});
 }});
 await h.trace.start(h.row);const phaseStarted=h.timer.now();
 const stopping=h.trace.stop(h.row);await ticks(20);h.timer.fireNext();await ticks(40);
 assert.equal(h.timer.now()-phaseStarted,14000);assert.ok(h.calls.some(x=>x.method==='IO.read'));
 h.timer.fireNext();assert.equal(await stopping,false);
 assert.equal(h.timer.now()-phaseStarted,15000);await h.trace.dispose();
 assert.equal(h.trace.report.ok,false);assert.equal(h.calls.filter(x=>x.method==='Tracing.end').length,1);
});

test('actual adapted finally preserves original thrown object when observation cleanup rejects',async()=>{
 const adapted=transform(original);const start=adapted.indexOf('\n finally{\n  await __mouse637Trace?.dispose()');
 assert.ok(start>0);const tail=adapted.slice(start,adapted.lastIndexOf('\n};'));
 const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
 const code='let fixture=null,interval=null,frameMonitorStarted=false,motionAttached=false,server=null,verificationError,cleanupError;const streams=new Map(),restorers=[],facts={},save=async()=>{};try{throw originalError;}catch(error){verificationError=error;}'+tail;
 const run=new AsyncFunction('originalError','__mouse637Trace',code),originalError=Error('original native failure');
 await assert.rejects(run(originalError,{dispose:async()=>{throw Error('observer cleanup');}}),error=>error===originalError);
});

function hookHarness(){
 const appPath='/owned/Установка Mouse/Mouse Browser.app/Contents/Resources/app.asar',executable='/owned/Установка Mouse/Mouse Browser.app/Contents/MacOS/Mouse Browser';
 const parentPath=appPath+'/mouse-631-smoke.cjs',target=appPath+'/mouse-631-stress-smoke.cjs',files=new Map([[parentPath,Buffer.from(parent)],[target,Buffer.from(original)],[appPath+'/mouse-main.cjs',Buffer.from(main)]]);
 const logs=[],Module={_extensions:{}},inspector={url:()=>inspector.open?'ws://owned':undefined,open:true,close(){logs.push('inspector-close');inspector.open=false;}};
 const f={readFileSync(file){assert.ok(files.has(file),'Missing file '+file);return files.get(file);},realpathSync:x=>x,existsSync:x=>files.has(x),
  writeFileSync(file,value){assert.equal(files.has(file),false);files.set(file,Buffer.from(value));},linkSync(from,to){assert.equal(files.has(to),false);files.set(to,files.get(from));},unlinkSync:file=>files.delete(file)};
 const fakeProcess={pid:1234,platform:'darwin',arch:'arm64',execPath:executable,argv:[executable,CONTRACT.flag],env:{CI:'true',MOUSE_TEST_PROFILE:'/owned/task-stress-631',MOUSE_637_PERFORMANCE_TRACE_NONCE:'a'.repeat(64)},versions:{electron:'44.5.0'}};
 const config={schema:1,phase:CONTRACT.phase,flag:CONTRACT.flag,pid:1234,controllerPid:55,nonce:'a'.repeat(64),publisherSHA:'b'.repeat(40),executable,appPath,profile:'/owned/task-stress-631',output:'/owned/output',receipt:'/owned/output/bootstrap.json',moduleReceipt:'/owned/output/module.json'};
 const electron={app:{getAppPath:()=>appPath,isPackaged:true,getVersion:()=>CONTRACT.version,isReady:()=>true,getPath:()=>config.profile,getName:()=> 'Mouse Browser'}};
 const requireFixture=name=>name.startsWith('node:')?require(name):name==='./mouse-lifecycle.cjs'?{bounded:async x=>x}:name==='./mouse-631-smoke-helpers.cjs'?{}:assert.fail('Unexpected fixture dependency '+name);
 function moduleFor(filename){return{exports:{},_compile(text,file){assert.equal(file,filename);logs.push(filename===parentPath?'parent-compile':'stress-compile');assert.equal(inspector.open,false);
   if(filename===target)assert.equal(Module._extensions['.js'],previous);new Function('require','module','exports',text)(requireFixture,this,this.exports);}};}
 function previous(module,filename){logs.push('delegate:'+filename);module._compile(files.get(filename).toString(),filename);return'delegated';}
 Module._extensions['.js']=previous;
 const load=name=>name==='node:fs'?f:name==='node:module'?Module:name==='node:inspector'?inspector:name==='electron'?electron:require(name);load.resolve=x=>x;load.cache={};
 const context=vm.createContext({Date});context.process=vm.runInContext('('+JSON.stringify(fakeProcess)+')',context);
 const hook=vm.runInContext('('+installOwnedHook.toString()+')',context);
 return{files,logs,Module,inspector,load,config,target,parentPath,previous,moduleFor,install:()=>hook(load,config,CONTRACT,transform(original))};
}

test('unchanged parent is delegated after Inspector close, stress stays deferred and restores loader before compile',()=>{
 const h=hookHarness();h.install();const installed=h.Module._extensions['.js'];
 assert.equal(h.Module._extensions['.js'](h.moduleFor(h.parentPath),h.parentPath),'delegated');
 assert.deepEqual(h.logs,['inspector-close','delegate:'+h.parentPath,'parent-compile']);assert.equal(h.Module._extensions['.js'],installed);
 assert.equal(h.files.has(h.config.moduleReceipt),false);
 h.Module._extensions['.js'](h.moduleFor(h.target),h.target);assert.equal(h.Module._extensions['.js'],h.previous);
 const receipt=JSON.parse(h.files.get(h.config.moduleReceipt));assert.equal(receipt.applications,1);assert.equal(receipt.loaderRestored,true);
 assert.equal(h.files.get(h.parentPath).toString(),parent);assert.equal(h.files.get(h.target).toString(),original);
 assert.throws(()=>installed(h.moduleFor(h.target),h.target));assert.equal(h.Module._extensions['.js'],h.previous);
});

test('wrong bytes, early target, nonce and late parent mutation reject and restore owned loader',()=>{
 {const h=hookHarness();h.files.set(h.target,Buffer.from('wrong'));assert.throws(()=>h.install());assert.equal(h.Module._extensions['.js'],h.previous);}
 {const h=hookHarness();h.config.nonce='c'.repeat(64);assert.throws(()=>h.install());assert.equal(h.Module._extensions['.js'],h.previous);}
 {const h=hookHarness();h.install();assert.throws(()=>h.Module._extensions['.js'](h.moduleFor(h.target),h.target));assert.equal(h.Module._extensions['.js'],h.previous);assert.equal(h.logs.length,0);}
 {const h=hookHarness();h.install();h.files.set(h.parentPath,Buffer.from('changed'));assert.throws(()=>h.Module._extensions['.js'](h.moduleFor(h.parentPath),h.parentPath));assert.equal(h.Module._extensions['.js'],h.previous);assert.equal(h.logs.length,0);}
});

test('early nullable runtime fields never waive available wrong identity or the exact original flag',()=>{
 const config={pid:12,nonce:'n',profile:'/p',executable:'/e'};
 const value={platform:'darwin',arch:'arm64',CI:'true',profile:'/p',nonce:'n',availability:{pid:'undefined',execPath:'undefined',argv:'undefined'},pid:null,execPath:null,argv:null};
 assert.equal(assertRuntimeIdentity(value,config,{early:true}),value);
 assert.throws(()=>assertRuntimeIdentity({...value,nonce:'other'},config,{early:true}));
 assert.throws(()=>assertRuntimeIdentity({...value,pid:13,availability:{...value.availability,pid:'number'}},config,{early:true}));
 const full={...value,pid:12,execPath:'/e',argv:['/e',CONTRACT.flag]};assert.equal(assertRuntimeIdentity(full,config),full);
 assert.throws(()=>assertRuntimeIdentity({...full,argv:['/e','--mouse-636-retained-smoke']},config));
});
