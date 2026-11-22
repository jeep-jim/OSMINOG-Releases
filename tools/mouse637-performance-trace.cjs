'use strict';
// Nonpublishing diagnostic. Only the exact installed CI stress module is adapted.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {connect,sha}=require('./mouse637-feature-readiness.cjs');
const {probeListener}=require('./mouse637-guest-input-observer.cjs');
const CONTRACT=Object.freeze({schema:1,source:'0021084ccb9537e657d21e6f0c8e812dee6b461f',version:'6.0.37',
 originalSha256:'d3b4797b42d63c364462dcb01c6bad4316c91d5b3cbb64065f12b571a5655ebf',originalGitBlob:'ec3d20f157e2ae74e86bf665344f63c326a8eee5',adaptedSha256:'9df01af3b89a27026590557a5a47ea49fecce9763b15aae66024ae77e61bdbaf',
 parentSha256:'2c35d8c9d77ea761712e5fc54a8b22b1e18cdf6b3d048cd9c6b0e5dc316cc208',parentGitBlob:'aef2796e206bbbc5d13754b4744ca81ceab81e06',
 mainSha256:'f3c9ba7794cb5c659c75fdc981faeda6b45851ceb0e70b61291128a04387914f',
 flag:'--mouse-631-smoke',phase:'performance-trace',profile:'task-stress-631',
 categories:['toplevel','devtools.timeline','blink.user_timing','mojom','mojom.flow'],
 limits:{eventBufferKiB:16384,maxOutputBytes:67108864,readBytes:262144,maxReads:257,activeMs:20000,setupMs:10000,drainMs:15000,apiRows:300,bufferEvents:32},
 scope:'Diagnostic shell/main and available GPU trace; no release acceptance or promised coverage of every guest renderer'});

// Serialized into the CI fixture. No product function, native driver or original
// workload operation is replaced. All additional awaits are outside its loop.
function createTrace({ctx,fixture,debug,config},dependencies={}){
 const a=require('node:assert/strict'),f=require('node:fs/promises'),p=require('node:path'),c=require('node:crypto');
 const now=dependencies.now||(()=>performance.now()),clock=dependencies.clock||(()=>Date.now());
 const setTimer=dependencies.setTimeout||setTimeout,clearTimer=dependencies.clearTimeout||clearTimeout;
 const write=dependencies.write||((file,bytes)=>f.writeFile(file,bytes,{flag:'wx',mode:0o600}));
 const digest=bytes=>c.createHash('sha256').update(bytes).digest('hex');
 const limits=config.limits,categories=config.categories;
 const report={schema:1,kind:'mouse637-nonpublishing-performance-trace',diagnosticOnly:true,releaseAcceptance:false,
  source:config.source,publisherSHA:config.publisherSHA,pid:process.pid,nonce:config.nonce,
  originalSha256:config.originalSha256,adaptedSha256:config.adaptedSha256,
  versions:{...process.versions},limits,categories,coverage:config.scope,
  originalStressBudgetMs:200000,fixtureStartedAt:fixture.started,fixtureDeadline:fixture.deadline,
  clock:'main.performance.now',api:[],bufferUsage:[],errors:[],marks:[],reads:[],ok:false,
  listenerAttached:false,listenerRemoved:false,activeCapExceeded:false,outputCapExceeded:false,
  streamClosed:false,streamEOF:false,readCount:0,outputBytes:0,loopCompleted:false};
 let started=false,startWaitFailed=false,ended=false,stream=null,activeTimer=null,endWork=null,endDeadline=null,completion=null,disposed=false,cleanedMarks=false;
 let resolveComplete;const completed=new Promise(resolve=>{resolveComplete=resolve;});
 const error=(where,cause)=>{try{if(report.errors.length<16)report.errors.push({where,message:String(cause?.message||cause).slice(0,1024),at:now()});}catch{}};
 const remaining=deadline=>{const left=Math.min(deadline,fixture.deadline)-now();a.ok(left>0,'Original stress deadline or diagnostic phase cap exceeded');return left;};
 async function bounded(operation,deadline,label){
  let timer;try{return await Promise.race([Promise.resolve(operation),new Promise((_,reject)=>{timer=setTimer(()=>{const failure=Error(label+' deadline exceeded');failure.code='MOUSE_TRACE_DEADLINE';reject(failure);},remaining(deadline));})]);}
  finally{clearTimer(timer);}
 }
 async function command(method,params,deadline,acknowledged,rejected){
  a.ok(report.api.length<limits.apiRows,'Diagnostic API receipt cap');remaining(deadline);
  const row={sequence:report.api.length+1,method,params:structuredClone(params||{}),startedAt:now()};report.api.push(row);
  try{
   let operation;
   try{if(method==='Tracing.start')report.startSubmitted=true;operation=debug.sendCommand(method,params||{});}
   catch(cause){rejected?.(cause);throw cause;}
   const observed=acknowledged?Promise.resolve(operation).then(value=>{acknowledged();return value;},cause=>{rejected?.(cause);throw cause;}):operation;
   const result=await bounded(observed,deadline,method);row.ok=true;return result;
  }
  catch(cause){row.ok=false;row.error=String(cause.message).slice(0,1024);row.timedOut=cause.code==='MOUSE_TRACE_DEADLINE';throw cause;}
  finally{row.endedAt=now();}
 }
 const message=(_event,method,params,sessionId)=>{
  if(sessionId)return;
  try{
   if(['Tracing.bufferUsage','Tracing.tracingComplete','Tracing.dataCollected'].includes(method)&&!started){
    error('unowned-tracing-event',method);return;
   }
   if(method==='Tracing.bufferUsage'){
    a.ok(report.bufferUsage.length<limits.bufferEvents,'Buffer event cap');
    const row={at:now()};for(const key of ['percentFull','eventCount','value']){
     if(params[key]!==undefined){a.ok(Number.isFinite(params[key])&&params[key]>=0);if(key!=='eventCount')a.ok(params[key]<=1);row[key]=params[key];}
    }
    report.bufferUsage.push(row);
   }else if(method==='Tracing.tracingComplete'){
    a.equal(completion,null,'Duplicate tracingComplete');a.equal(typeof params.dataLossOccurred,'boolean');
    a.equal(typeof params.stream,'string');a.ok(params.stream.length>0&&params.stream.length<=256);
    if(params.traceFormat!==undefined)a.equal(params.traceFormat,'json');
    if(params.streamCompression!==undefined)a.equal(params.streamCompression,'none');
    completion={at:now(),dataLossOccurred:params.dataLossOccurred,stream:params.stream,
     traceFormat:params.traceFormat??null,streamCompression:params.streamCompression??null};
    stream=params.stream;report.completion=completion;resolveComplete(completion);
   }else if(method==='Tracing.dataCollected')throw Error('Unexpected ReportEvents transport');
  }catch(cause){error('message',cause);resolveComplete(null);}
 };
 const detached=(_event,reason)=>{report.detached={at:now(),reason:String(reason).slice(0,256)};error('debugger-detached','Original debugger detached during trace');resolveComplete(null);};
 debug.on('message',message);debug.on('detach',detached);report.listenerAttached=true;
 const names={begin:'mouse637-trace-'+config.nonce+'-begin',end:'mouse637-trace-'+config.nonce+'-end'};
 async function mark(kind,deadline){
  const name=names[kind];
  const expression='(()=>{const name='+JSON.stringify(name)+';performance.mark(name);const entries=performance.getEntriesByName(name,"mark");if(entries.length!==1)throw Error("Diagnostic mark collision");return{name,startTime:entries[0].startTime,timeOrigin:performance.timeOrigin,now:performance.now()};})()';
  const value=await command('Runtime.evaluate',{expression,returnByValue:true},deadline);
  a.equal(value.exceptionDetails,undefined);const result=value.result?.value;
  a.equal(result?.name,name);for(const key of ['startTime','timeOrigin','now'])a.ok(Number.isFinite(result[key]));
  report.marks.push({kind,...result,clock:'renderer.performance.now'});return result;
 }
 function end(reason){
  if(endWork)return endWork;
  a.equal(started,true,'Cannot stop a trace without our acknowledged start');
  ended=true;clearTimer(activeTimer);activeTimer=null;endDeadline??=Math.min(fixture.deadline,now()+limits.drainMs);
  report.endReason=reason;report.endRequestedAt=now();
  endWork=command('Tracing.end',{},endDeadline);endWork.catch(cause=>error('end',cause));return endWork;
 }
 async function closeStream(){
  if(stream===null||report.streamClosed)return;
  try{await command('IO.close',{handle:stream},endDeadline??Math.min(fixture.deadline,now()+limits.drainMs));report.streamClosed=true;}
  catch(cause){error('close-stream',cause);}
 }
 async function clearMarks(deadline){
  if(cleanedMarks)return;cleanedMarks=true;
   try{const result=await command('Runtime.evaluate',{expression:'(()=>{for(const name of '+JSON.stringify(Object.values(names))+')performance.clearMarks(name);return true;})()',returnByValue:true},deadline);
    a.equal(result.exceptionDetails,undefined);a.equal(result.result?.value,true);report.marksCleared=true;}
  catch(cause){error('clear-marks',cause);report.marksCleared=false;}
 }
 async function start(row){
  const deadline=Math.min(fixture.deadline,now()+limits.setupMs);
  try{
   a.equal(started,false);a.equal(row.ownedPageCount,20);a.equal(row.switchCount,5);a.equal(debug.isAttached(),true);
   report.mainPid=process.pid;report.shellWebContentsId=fixture.win.webContents.id;report.shellPid=fixture.win.webContents.getOSProcessId();
   a.ok(Number.isSafeInteger(report.shellPid)&&report.shellPid>0&&report.shellPid!==process.pid);
   report.browserVersion=await command('Browser.getVersion',{},deadline);a.ok(Buffer.byteLength(JSON.stringify(report.browserVersion))<=4096);
   report.supported=await command('Tracing.getCategories',{},deadline);a.ok(Buffer.byteLength(JSON.stringify(report.supported))<=1048576);
   a.ok(Array.isArray(report.supported.categories)&&report.supported.categories.length>0&&report.supported.categories.length<=4096);
   a.ok(report.supported.categories.every(x=>typeof x==='string'&&x.length>0&&x.length<=256));
   for(const name of categories)a.ok(report.supported.categories.includes(name),'Required runtime category missing: '+name);
   report.startParams={transferMode:'ReturnAsStream',streamFormat:'json',streamCompression:'none',bufferUsageReportingInterval:1000,
    traceConfig:{recordMode:'recordUntilFull',traceBufferSizeInKb:limits.eventBufferKiB,enableSampling:false,enableSystrace:false,includedCategories:categories}};
   report.startRequestedAt=now();
   await command('Tracing.start',report.startParams,deadline,()=>{
    started=true;report.startAcknowledged=true;report.startedAt=now();
    if(startWaitFailed){report.lateStartAcknowledgment=true;if(!disposed)void end('late-start-ack').catch(()=>{});}
   },cause=>{report.startRejected=true;report.startRejectedAt=now();report.startRejection=String(cause.message).slice(0,1024);});
   activeTimer=setTimer(()=>{report.activeCapExceeded=true;void end('active-cap').catch(()=>{});},Math.min(limits.activeMs,remaining(fixture.deadline)));activeTimer?.unref?.();
   await mark('begin',deadline);report.loopReadyAt=now();return true;
  }catch(cause){startWaitFailed=true;report.startWaitTimedOut=cause.code==='MOUSE_TRACE_DEADLINE';error('start',cause);return false;}
 }
 async function stop(row,{loopCompleted=true}={}){
  if(!started)return false;
  const chunks=[];
  async function saveChunks(){
   if(report.trace||!report.outputBytes)return;remaining(endDeadline);
   const bytes=Buffer.concat(chunks,report.outputBytes),filename='mouse-637-performance-trace-data.json';
   await bounded(write(p.join(config.output,filename),bytes),endDeadline,'Write collected trace');
   report.trace={filename,size:bytes.length,sha256:digest(bytes)};
  }
  try{
   report.loopCompleted=loopCompleted;report.loopReturnAt=now();
   report.switches=(row?.switches||[]).map(v=>({sequence:v.sequence,elapsedMs:v.elapsedMs,slide:structuredClone(v.slide)}));
   if(loopCompleted){a.equal(row.ownedPageCount,20);a.equal(row.switchCount,5);a.equal(row.switches.length,5);}
   const deadline=endDeadline??=Math.min(fixture.deadline,now()+limits.drainMs);
   if(!ended)await mark('end',deadline);
   await end(loopCompleted?'loop-complete':'original-workload-error');
   const done=await bounded(completed,endDeadline,'Tracing.tracingComplete');a.ok(done,'Tracing completion is malformed');
   for(let i=0;i<limits.maxReads;i++){
    const size=Math.min(limits.readBytes,Math.max(1,limits.maxOutputBytes-report.outputBytes));
    const data=await command('IO.read',{handle:stream,size},endDeadline);report.readCount++;
    a.equal(typeof data.data,'string');a.equal(typeof data.eof,'boolean');
    if(data.base64Encoded!==undefined)a.equal(typeof data.base64Encoded,'boolean');
    let bytes;if(data.base64Encoded){a.match(data.data,/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/);bytes=Buffer.from(data.data,'base64');a.equal(bytes.toString('base64'),data.data);}else bytes=Buffer.from(data.data,'utf8');
    report.reads.push({apiSequence:report.api.at(-1).sequence,requestedSize:size,base64Encoded:data.base64Encoded===true,eof:data.eof,
     decodedBytes:bytes.length,returnedDataUTF8Bytes:Buffer.byteLength(data.data),returnedDataSHA256:digest(Buffer.from(data.data)),decodedSHA256:digest(bytes)});
    a.ok(bytes.length<=size,'IO.read exceeded the requested chunk bound');
    if(report.outputBytes+bytes.length>limits.maxOutputBytes){report.outputCapExceeded=true;throw Error('Trace output cap');}
    report.outputBytes+=bytes.length;chunks.push(bytes);
    if(data.eof){report.streamEOF=true;break;}
    a.ok(bytes.length>0,'Empty non-EOF stream chunk');
   }
   a.equal(report.streamEOF,true,'Bounded stream did not reach EOF');a.ok(report.outputBytes>0);
   await saveChunks();
   a.equal(done.dataLossOccurred,false,'Trace reports discarded/overwritten/lost packets');
   a.equal(report.activeCapExceeded,false,'Active trace time cap exceeded');
   a.ok(report.bufferUsage.every(v=>(v.percentFull??v.value??0)<1),'Event buffer reached capacity');
   report.collected=true;return true;
  }catch(cause){error('stop',cause);return false;}
  finally{
   try{await saveChunks();}catch(cause){error('save-partial-trace',cause);}
   await closeStream();await clearMarks(endDeadline??Math.min(fixture.deadline,now()+limits.drainMs));
  }
 }
 async function dispose(){
  if(disposed)return;disposed=true;
  try{if(started&&!ended)await stop(null,{loopCompleted:false});else if(stream!==null)await closeStream();}
  catch(cause){error('dispose',cause);}
  finally{
   try{clearTimer(activeTimer);activeTimer=null;}catch(cause){error('clear-timer',cause);}
   let removed=0;
   for(const[type,listener]of [['message',message],['detach',detached]])try{debug.removeListener(type,listener);removed++;}catch(cause){error('remove-listener-'+type,cause);}
   report.listenerRemoved=removed===2;
   try{report.finishedAt=now();report.finishedEpochMs=clock();}catch(cause){error('receipt-clock',cause);}
   report.startPendingAtDisposal=report.startSubmitted===true&&!report.startAcknowledged&&!report.startRejected;
   report.ok=report.collected===true&&report.loopCompleted&&report.streamEOF&&report.streamClosed&&report.marksCleared===true&&report.errors.length===0&&!report.detached;
   try{const deadline=Math.min(fixture.deadline,now()+1000);remaining(deadline);
    await bounded(write(p.join(config.output,'mouse-637-performance-trace-session.json'),JSON.stringify(report,null,2)+'\n'),deadline,'Diagnostic receipt write');}
   catch(cause){error('save-receipt',cause);try{console.error('MOUSE_637_DIAGNOSTIC_TRACE_SAVE_FAILED '+String(cause.message));}catch{}}
  }
 }
 return{start,stop,dispose,report};
}

function transform(original,{verifyAdapted=true}={}){
 assert.equal(sha(original),CONTRACT.originalSha256,'Unexpected exact002 stress module');
 const edits=[];const add=(from,to)=>edits.push({from,to});
 add("const distribution=values=>",'const __mouse637TraceConfig=module.__mouse637TraceConfig;delete module.__mouse637TraceConfig;\nconst __mouse637CreateTrace='+createTrace.toString()+';\nconst distribution=values=>');
 add(" let fixture,server,verificationError,cleanupError,currentStage='setup'"," let __mouse637Trace;\n let fixture,server,verificationError,cleanupError,currentStage='setup'");
 add("  facts.motionMedia.normal=await fixture.js",'  __mouse637Trace=__mouse637CreateTrace({ctx,fixture,debug:motionDebug,config:__mouse637TraceConfig});\n  facts.motionMedia.normal=await fixture.js');
 add('   for(let n=0;n<switchCount;n++){','   if(target===20)await __mouse637Trace.start(row);\n   for(let n=0;n<switchCount;n++){');
 add("   operation='nora';await fixture.js",'   if(target===20)await __mouse637Trace.stop(row);\n   operation=\'nora\';await fixture.js');
 add(' finally{\n  clearInterval(interval);',' finally{\n  await __mouse637Trace?.dispose().catch(()=>{});\n  clearInterval(interval);');
 let adapted=original;
 for(const{from,to}of edits){assert.equal(adapted.split(from).length-1,1);adapted=adapted.replace(from,to);}
 let reverted=adapted;for(const{from,to}of [...edits].reverse()){assert.equal(reverted.split(to).length-1,1);reverted=reverted.replace(to,from);}assert.equal(reverted,original);
 if(verifyAdapted)assert.equal(sha(adapted),CONTRACT.adaptedSha256,'Adapted trace module changed');return adapted;
}

function installOwnedHook(load,config,contract,adapted){
 const a=load('node:assert/strict'),f=load('node:fs'),p=load('node:path'),c=load('node:crypto');
 const electron=load('electron'),Module=load('node:module'),inspector=load('node:inspector');
 const digest=value=>c.createHash('sha256').update(value).digest('hex'),exact=value=>f.realpathSync(value);
 a.equal(process.env.CI,'true');a.equal(process.platform,'darwin');a.equal(process.arch,'arm64');
 a.equal(process.pid,config.pid);a.equal(process.env.MOUSE_637_PERFORMANCE_TRACE_NONCE,config.nonce);
 a.equal(exact(process.execPath),config.executable);a.equal(exact(electron.app.getAppPath()),config.appPath);
 a.equal(electron.app.isPackaged,true);a.equal(electron.app.getVersion(),contract.version);
 a.equal(process.env.MOUSE_TEST_PROFILE,config.profile);a.equal(config.phase,contract.phase);a.equal(config.flag,contract.flag);
 a.equal(process.argv[0],config.executable);
 a.deepEqual(process.argv.filter(x=>x.startsWith('--mouse-')&&!x.startsWith('--mouse-profile')),[contract.flag]);
 const fullRuntimeIdentity={pid:process.pid,execPath:process.execPath,argv:[...process.argv],platform:process.platform,
  arch:process.arch,CI:process.env.CI,profile:process.env.MOUSE_TEST_PROFILE,nonce:process.env.MOUSE_637_PERFORMANCE_TRACE_NONCE};
 const parent=p.join(config.appPath,'mouse-631-smoke.cjs'),target=p.join(config.appPath,'mouse-631-stress-smoke.cjs');
 a.equal(digest(f.readFileSync(p.join(config.appPath,'mouse-main.cjs'))),contract.mainSha256);
 a.equal(digest(f.readFileSync(parent)),contract.parentSha256);a.equal(digest(f.readFileSync(target)),contract.originalSha256);
 a.equal(digest(adapted),contract.adaptedSha256);
 for(const filename of [parent,target]){a.equal(load.resolve(filename),filename);a.equal(load.cache[filename],undefined);}
 for(const filename of [config.receipt,config.moduleReceipt]){a.equal(f.existsSync(filename),false);a.equal(p.dirname(filename),config.output);}
 const previous=Module._extensions['.js'];a.equal(typeof previous,'function');let parentLoads=0,applications=0,closedAt=null;
 const write=(filename,value)=>{const temporary=filename+'.tmp-'+config.nonce;f.writeFileSync(temporary,JSON.stringify(value,null,2)+'\n',{flag:'wx',mode:0o600});try{f.linkSync(temporary,filename);}finally{f.unlinkSync(temporary);}};
 const restore=()=>{if(Module._extensions['.js']===ownedFixture)Module._extensions['.js']=previous;};
 function ownedFixture(module,filename){
  if(filename!==parent&&filename!==target)return previous.call(this,module,filename);
  try{
   a.equal(Module._extensions['.js'],ownedFixture);a.equal(electron.app.isReady(),true);
   a.equal(p.resolve(electron.app.getPath('userData')),config.profile);a.equal(electron.app.getName(),'Mouse Browser');
   if(filename===parent){
    a.equal(++parentLoads,1);a.equal(applications,0);a.equal(digest(f.readFileSync(filename)),contract.parentSha256);
    // This unchanged parent starts taskOnly before it requires stress. Close the
    // Inspector before delegating parent compilation or invoking any CI fixture.
    inspector.close();a.equal(inspector.url(),undefined);closedAt=Date.now();const parentCompileStartedAt=Date.now();
    const result=previous.call(this,module,filename);a.equal(typeof module.exports,'function');
    a.equal(digest(f.readFileSync(filename)),contract.parentSha256);a.equal(applications,0);
    const receipt={schema:1,kind:'mouse637-performance-trace-bootstrap',diagnosticOnly:true,releaseAcceptance:false,
     source:contract.source,publisherSHA:config.publisherSHA,phase:config.phase,flag:config.flag,pid:process.pid,
     controllerPid:config.controllerPid,nonce:config.nonce,executable:config.executable,appPath:config.appPath,
     profile:config.profile,parent,target,versions:{...process.versions},fullRuntimeIdentity,
     mainSha256:contract.mainSha256,parentSha256:contract.parentSha256,originalSha256:contract.originalSha256,
     adaptedSha256:contract.adaptedSha256,parentLoads,parentBytesDelegated:true,parentCompileStartedAt,
     parentCompileFinishedAt:Date.now(),inspectorClosed:true,inspectorUrl:null,closedAt,
     stressStillDeferred:true,loaderStillPending:true,receiptBeforeParentInvocation:true};
    write(config.receipt,receipt);return result;
   }
   a.equal(parentLoads,1,'Stress must load after the original native parent');a.equal(++applications,1);
   a.equal(inspector.url(),undefined);restore();a.equal(Module._extensions['.js'],previous);
   const original=f.readFileSync(filename);a.equal(digest(original),contract.originalSha256);
   for(const[name,bytes]of [['original',original],['adapted',adapted],['parent',f.readFileSync(parent)]])
    f.writeFileSync(p.join(config.output,'mouse-637-performance-trace-'+name+'.cjs'),bytes,{flag:'wx',mode:0o600});
   module.__mouse637TraceConfig={source:contract.source,publisherSHA:config.publisherSHA,pid:process.pid,nonce:config.nonce,
    output:config.output,originalSha256:contract.originalSha256,adaptedSha256:contract.adaptedSha256,
    categories:contract.categories,limits:contract.limits,scope:contract.scope};
   const compileStartedAt=Date.now();module._compile(adapted,filename);a.equal(typeof module.exports,'function');
   a.equal(module.__mouse637TraceConfig,undefined);a.equal(Module._extensions['.js'],previous);
   a.equal(digest(f.readFileSync(filename)),contract.originalSha256);
   write(config.moduleReceipt,{schema:1,kind:'mouse637-performance-trace-module',diagnosticOnly:true,releaseAcceptance:false,
    source:contract.source,publisherSHA:config.publisherSHA,pid:process.pid,nonce:config.nonce,parent,target,
    parentSha256:contract.parentSha256,originalSha256:contract.originalSha256,originalGitBlob:contract.originalGitBlob,
    adaptedSha256:contract.adaptedSha256,applications,parentLoads,loaderRestored:true,inspectorClosed:true,
    closedAt,compileStartedAt,compiledAt:Date.now(),receiptBeforeStressInvocation:true});
  }catch(error){restore();throw error;}
 }
 Module._extensions['.js']=ownedFixture;
 return{pid:process.pid,nonce:config.nonce,parent,target,installed:true,fullRuntimeIdentity};
}

const RUNTIME_EXPRESSION='({availability:{pid:typeof process.pid,execPath:typeof process.execPath,argv:typeof process.argv},pid:typeof process.pid==="undefined"?null:process.pid,execPath:typeof process.execPath==="undefined"?null:process.execPath,argv:typeof process.argv==="undefined"?null:process.argv,platform:process.platform,arch:process.arch,CI:process.env?.CI,profile:process.env?.MOUSE_TEST_PROFILE,nonce:process.env?.MOUSE_637_PERFORMANCE_TRACE_NONCE})';
function assertRuntimeIdentity(value,config,{platform='darwin',arch='arm64',early=false}={}){
 assert.ok(value&&typeof value==='object');assert.equal(value.platform,platform);assert.equal(value.arch,arch);
 assert.equal(value.CI,'true');assert.equal(value.profile,config.profile);assert.equal(value.nonce,config.nonce);
 for(const[key,type]of Object.entries({pid:'number',execPath:'string',argv:'object'})){
  if(early&&value.availability?.[key]==='undefined'){assert.equal(value[key],null);continue;}
  if(early)assert.equal(value.availability?.[key],type);
  if(key==='pid')assert.equal(value.pid,config.pid);
  if(key==='execPath')assert.equal(value.execPath,config.executable);
  if(key==='argv'){assert.ok(Array.isArray(value.argv));assert.ok(value.argv.every(v=>typeof v==='string'));assert.equal(value.argv[0],config.executable);
   assert.deepEqual(value.argv.filter(v=>v.startsWith('--mouse-')&&!v.startsWith('--mouse-profile')),[CONTRACT.flag]);}
 }
 return value;
}
function validateConfig(config){
 assert.equal(config.schema,1);assert.equal(config.phase,CONTRACT.phase);assert.equal(config.flag,CONTRACT.flag);
 assert.match(config.nonce,/^[a-f0-9]{64}$/);assert.match(config.publisherSHA,/^[a-f0-9]{40}$/);
 assert.ok(Number.isSafeInteger(config.pid)&&config.pid>0);assert.ok(Number.isInteger(config.port)&&config.port>0&&config.port<65536);
 for(const key of ['executable','appPath','profile','output','receipt','moduleReceipt','controllerReceipt','listenerReceipt'])assert.ok(path.isAbsolute(config[key]),key);
 assert.equal(config.appPath,path.join(path.dirname(path.dirname(config.executable)),'Resources','app.asar'));
 assert.equal(path.basename(config.profile),CONTRACT.profile);
 for(const[key,suffix]of Object.entries({receipt:'bootstrap',moduleReceipt:'module',controllerReceipt:'controller',listenerReceipt:'listener'}))
  assert.equal(config[key],path.join(config.output,'mouse-637-performance-trace-'+suffix+'.json'));
 assert.ok(Number.isFinite(config.deadlineEpochMs)&&config.deadlineEpochMs>Date.now());return config;
}
async function control(config){
 validateConfig(config);config={...config,controllerPid:process.pid};
 const startedAt=Date.now(),remaining=()=>{const left=config.deadlineEpochMs-Date.now();assert.ok(left>0,'Owned trace bootstrap deadline');return left;};
 const wait=async check=>{for(;;){remaining();const value=await check();if(value)return value;await new Promise(resolve=>setTimeout(resolve,Math.min(25,remaining())));}};
 let client;
 try{
  const endpoint='http://127.0.0.1:'+config.port+'/json/list';
  const target=await wait(async()=>{try{const response=await fetch(endpoint,{signal:AbortSignal.timeout(Math.min(500,remaining()))});assert.equal(response.ok,true);const rows=await response.json();assert.equal(rows.length,1);return rows[0];}catch(error){if(error.name==='AssertionError')throw error;return null;}});
  const url=new URL(target.webSocketDebuggerUrl);assert.equal(url.protocol,'ws:');assert.equal(url.hostname,'127.0.0.1');assert.equal(Number(url.port),config.port);
  client=await connect(url.href,remaining);
  const listenerIdentity=probeListener(config,remaining);
  const early=await client.send('Runtime.evaluate',{expression:RUNTIME_EXPRESSION,returnByValue:true});assert.equal(early.exceptionDetails,undefined);
  const earlyRuntimeIdentity=assertRuntimeIdentity(early.result.value,config,{early:true});
  await client.send('Debugger.enable');
  const main=path.join(config.appPath,'mouse-main.cjs'),escape=value=>value.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  const breakpoint=await client.send('Debugger.setBreakpointByUrl',{lineNumber:0,urlRegex:'^(?:'+escape(main)+'|'+escape(pathToFileURL(main).href)+')$'});
  await client.send('Runtime.runIfWaitingForDebugger');let paused=await client.event('Debugger.paused');
  const owned=frame=>client.scriptURL(frame)===main||client.scriptURL(frame)===pathToFileURL(main).href;
  if(!paused.callFrames.some(owned)){await client.send('Debugger.resume');paused=await client.event('Debugger.paused');}
  const frame=paused.callFrames.find(owned);assert.ok(frame,'Exact installed main frame required');
  const original=fs.readFileSync(path.join(__dirname,'fixtures/mouse637-performance-002-stress.cjs'),'utf8'),adapted=transform(original);
  const result=await client.send('Debugger.evaluateOnCallFrame',{callFrameId:frame.callFrameId,
   expression:'('+installOwnedHook.toString()+')(require,'+JSON.stringify(config)+','+JSON.stringify(CONTRACT)+','+JSON.stringify(adapted)+')',returnByValue:true});
  assert.equal(result.exceptionDetails,undefined,JSON.stringify(result.exceptionDetails));
  const fullRuntimeIdentity=assertRuntimeIdentity(result.result.value.fullRuntimeIdentity,config);
  assert.deepEqual(result.result.value,{pid:config.pid,nonce:config.nonce,parent:path.join(config.appPath,'mouse-631-smoke.cjs'),target:path.join(config.appPath,'mouse-631-stress-smoke.cjs'),installed:true,fullRuntimeIdentity});
  await client.send('Debugger.removeBreakpoint',{breakpointId:breakpoint.breakpointId});
  await client.send('Debugger.resume');await client.close();client=null;
  const receipt=await wait(()=>fs.existsSync(config.receipt)?JSON.parse(fs.readFileSync(config.receipt,'utf8')):null);
  assert.equal(receipt.pid,config.pid);assert.equal(receipt.controllerPid,process.pid);assert.equal(receipt.nonce,config.nonce);assert.equal(receipt.inspectorClosed,true);
  assert.equal(receipt.parentBytesDelegated,true);assert.equal(receipt.receiptBeforeParentInvocation,true);
  let refused=false;try{await fetch(endpoint,{signal:AbortSignal.timeout(Math.min(500,remaining()))});}catch{refused=true;}
  assert.equal(refused,true,'Inspector server remains reachable');
  const proof={schema:1,kind:'mouse637-performance-trace-controller',diagnosticOnly:true,releaseAcceptance:false,ok:true,
   source:CONTRACT.source,publisherSHA:config.publisherSHA,pid:config.pid,controllerPid:process.pid,nonce:config.nonce,
   host:'127.0.0.1',port:config.port,startedAt,finishedAt:Date.now(),earlyRuntimeIdentity,fullRuntimeIdentity,
   listenerReceiptSha256:sha(fs.readFileSync(config.listenerReceipt)),ownershipBeforeResume:true,serverUnavailable:true,
   receiptSha256:sha(fs.readFileSync(config.receipt)),controllerSha256:sha(fs.readFileSync(__filename))};
  fs.writeFileSync(config.controllerReceipt,JSON.stringify(proof,null,2)+'\n',{flag:'wx',mode:0o600});return proof;
 }finally{if(client)await client.close().catch(()=>{});}
}
module.exports={CONTRACT,createTrace,transform,installOwnedHook,RUNTIME_EXPRESSION,assertRuntimeIdentity,validateConfig,control};
if(require.main===module){
 if(process.argv.length!==4||process.argv[2]!=='control')throw Error('Expected control <owned-config.json>');
 control(JSON.parse(fs.readFileSync(process.argv[3],'utf8'))).catch(error=>{console.error(error);process.exitCode=1;});
}
