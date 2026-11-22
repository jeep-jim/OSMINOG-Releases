'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const http=require('node:http');
const {createHash}=require('node:crypto');
const {createFixture,pageHTML,bounded,sleep}=require('./mouse-631-smoke-helpers.cjs');
const distribution=values=>{const sorted=values.slice().sort((a,b)=>a-b);return{count:values.length,min:sorted[0]??0,p50:sorted[Math.floor((sorted.length-1)*.5)]??0,p95:sorted[Math.floor((sorted.length-1)*.95)]??0,max:sorted.at(-1)??0};};

// Optional diagnostics for synchronous main-process calls in the existing
// measured switch only. Parent spans include their children: do not sum them.
// These times do not measure renderer DOM work or isolate IPC queue latency.
function createSwitchTimings(now=()=>performance.now()){
 let active=null,parentId=null;
 return{
  begin(stage,switchSequence){parentId=null;return active={schema:1,clock:'main.performance.now',stage,switchSequence,calls:[]};},
  end(endedAt){if(active)active.endedAt=endedAt;active=null;parentId=null;},
  call(method,original,receiver,args,pageIndex,describe){
   if(!active)return original.apply(receiver,args);
   const calls=active.calls,parent=parentId,row={id:calls.length+1,parentId:parent,method};
   if(pageIndex!==undefined)row.pageIndex=pageIndex;
   if(describe)try{row.context=describe();}catch(error){row.contextError=String(error?.message||error).slice(0,256);}
   calls.push(row);parentId=row.id;row.startedAt=now();
   try{return original.apply(receiver,args);}
   catch(error){row.threw=true;throw error;}
   finally{row.elapsedMs=now()-row.startedAt;parentId=parent;}
  }
 };
}

// Serialized into the existing installed-renderer monitor. These optional
// observations use its existing callbacks and never request another frame.
function rendererMonitorInPage(start){
 if(start){
  const diagnostics={schema:1,clock:'renderer.performance.now',frameTimeSource:'requestAnimationFrame callback timestamp',frameIntervals:[],droppedFrameIntervals:0,longAnimationFrames:{supported:false,observeError:null,entries:[],truncated:{frames:0,scripts:0,strings:0}}};
  const s=globalThis.__mouse631Frames={running:true,count:0,gaps:[],max:0,longTasks:[],diagnostics};let last;
  const tick=t=>{
   if(!s.running)return;
   if(last!==undefined){
    const gap=t-last;s.gaps.push(gap);if(s.gaps.length>4096)s.gaps.shift();s.max=Math.max(s.max,gap);
    const row={startTime:last,endTime:t,duration:gap};
    if(diagnostics.frameIntervals.length<4096)diagnostics.frameIntervals.push(row);
    else{diagnostics.frameIntervals[4095]=row;diagnostics.droppedFrameIntervals++;}
   }
   last=t;s.count++;s.raf=requestAnimationFrame(tick);
  };
  s.raf=requestAnimationFrame(tick);
  s.observer=new PerformanceObserver(list=>{for(const task of list.getEntries()){s.longTasks.push({startTime:task.startTime,duration:task.duration});if(s.longTasks.length>128)s.longTasks.shift();}});
  s.observer.observe({type:'longtask',buffered:false});
  // Two fully populated stages must fit the existing 8 MiB raw-report reader,
  // including pretty JSON, six-byte escaped UTF-16 units and legacy evidence.
  const maxLoafFrames=64,maxLoafScripts=8,maxLoafText=64;
  const loaf=diagnostics.longAnimationFrames,number=value=>typeof value==='number'&&Number.isFinite(value)?value:null;
  loaf.textTruncation={strategy:'head+ellipsis+tail',maxUTF16Units:maxLoafText};
  const text=value=>{if(typeof value!=='string')return null;if(value.length<=maxLoafText)return value;loaf.truncated.strings++;const head=Math.floor((maxLoafText-1)/2);return value.slice(0,head)+'…'+value.slice(-(maxLoafText-1-head));};
  const record=entries=>{
   try{for(const entry of entries){
    const row={};for(const key of ['startTime','duration','renderStart','styleAndLayoutStart','blockingDuration'])row[key]=number(entry[key]);
    const scripts=entry.scripts,amount=Number.isSafeInteger(scripts?.length)&&scripts.length>=0?scripts.length:0;row.scripts=[];loaf.truncated.scripts+=Math.max(0,amount-maxLoafScripts);
    for(let i=0;i<Math.min(amount,maxLoafScripts);i++){
     const script=scripts[i],value={};
     for(const key of ['startTime','duration','executionStart','forcedStyleAndLayoutDuration','sourceCharPosition'])value[key]=number(script[key]);
     for(const key of ['invokerType','invoker','sourceURL','sourceFunctionName','windowAttribution'])value[key]=text(script[key]);
     row.scripts.push(value);
    }
    if(loaf.entries.length<maxLoafFrames)loaf.entries.push(row);else{loaf.entries[maxLoafFrames-1]=row;loaf.truncated.frames++;}
   }}catch(error){loaf.observeError=String(error?.message||error).slice(0,512);}
  };
  try{
   loaf.supported=Array.isArray(PerformanceObserver.supportedEntryTypes)&&PerformanceObserver.supportedEntryTypes.includes('long-animation-frame');
   if(loaf.supported){s.loafObserver=new PerformanceObserver(list=>record(list.getEntries()));s.loafObserver.observe({type:'long-animation-frame',buffered:false});s.recordLoaf=record;}
  }catch(error){loaf.observeError=String(error?.message||error).slice(0,512);try{s.loafObserver?.disconnect();}catch{}s.loafObserver=null;}
  return true;
 }
 const s=globalThis.__mouse631Frames;s.running=false;cancelAnimationFrame(s.raf);s.observer.disconnect();
 if(s.loafObserver){
  try{s.recordLoaf(s.loafObserver.takeRecords());}catch(error){s.diagnostics.longAnimationFrames.observeError=String(error?.message||error).slice(0,512);}
  finally{try{s.loafObserver.disconnect();}catch(error){s.diagnostics.longAnimationFrames.observeError=String(error?.message||error).slice(0,512);}}
 }
 return{frames:s.count,gaps:s.gaps,maxGapMs:s.max,longTasks:s.longTasks,diagnostics:s.diagnostics};
}

module.exports=async ctx=>{
 const facts={version:ctx.app.getVersion(),platform:process.platform,arch:process.arch,source:'installed native pages and local HTTP streams',budgetMs:200000,stages:[],captures:[],renderFailures:[],restored:false,ok:false,baselineComparison:{performed:false,reason:'This process records candidate timings only. The separate mouse-636-performance.json binds both installed runs and compares their raw workloads.'}};
 const save=()=>fs.writeFile('mouse-631-stress.json',JSON.stringify(facts,null,2)+'\n');
 let fixture,server,verificationError,cleanupError,currentStage='setup',operation='setup',interval,frameMonitorStarted=false,motionDebug,motionAttached=false;
 const requests=[],streams=new Map(),restorers=[],captureCalls=[],counts={capturePage:0,getVisible:0,setVisible:0,setBounds:0,nativeCorners:0,state:0},mainGaps=[];
 const switchTimings=createSwitchTimings();
 let lastTick=performance.now();
 function wrap(object,name,wrapper){const original=object[name];assert.equal(typeof original,'function',name+' is callable');object[name]=wrapper(original);restorers.push(()=>{object[name]=original;});}
 function instrument(record){
  const wc=record.page.view.webContents;
  wrap(wc,'capturePage',original=>function(...args){counts.capturePage++;return original.apply(this,args);});
  for(const name of ['getVisible','setVisible','setBounds'])wrap(record.page.view,name,original=>function(...args){counts[name]++;return switchTimings.call(name,original,this,args,record.index);});
  const failure=(_event,details)=>facts.renderFailures.push({tabId:record.id,index:record.index,event:'render-process-gone',details,stage:currentStage});wc.on('render-process-gone',failure);restorers.push(()=>wc.removeListener('render-process-gone',failure));
 }
 async function readAll(records){return Promise.all(records.map(record=>fixture.identity(record)));}
 async function progressUI(){
  return fixture.js(`(()=>{const rect=e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height};};return{desk:MouseTest.model.desktopId,panes:[...document.querySelectorAll('.pane')].map(p=>{const dock=p.querySelector('.mouse-pane-progress');return{pane:p.dataset.pane,tabId:MouseTest.model.slots[p.dataset.pane]||'',header:rect(p.querySelector('.pane-head')),slot:rect(p.querySelector('.page-slot')),dock:dock?{hidden:dock.hidden,bounds:rect(dock)}:null,pills:dock?[...dock.querySelectorAll('.mouse-progress-pill')].filter(e=>!dock.hidden&&!e.hidden&&e.getBoundingClientRect().width>0&&e.getBoundingClientRect().height>0).map(e=>({id:e.dataset.progressId,taskId:e.dataset.taskId,tabId:e.dataset.tabId,desk:e.dataset.desk,phase:e.dataset.phase,kind:e.dataset.kind,indeterminate:e.dataset.indeterminate,value:e.querySelector('.mouse-progress-value').textContent,bounds:rect(e)})):[]};})};})()`);
 }
 async function switchProgress(total,owner,running,visible,entry){
  const state=await fixture.js('MouseNative.progress("state")'),ui=await progressUI();
  entry.progress={streamId:owner.id,state,ui};
  assert.equal(ui.desk,owner.desk);assert.equal(state.tasks.length,5,'Exactly the five real HTTP stream tasks remain running');
  for(const stream of running){const found=state.tasks.filter(task=>task.tabId===stream.tabId&&task.taskId==='stream-'+stream.id);assert.equal(found.length,1);assert.equal(found[0].phase,'running');assert.equal(found[0].desk,stream.desk);}
  assert.deepEqual(ui.panes.map(p=>p.tabId).sort(),visible.map(record=>record.id).sort());
  const pills=ui.panes.flatMap(pane=>pane.pills.map(pill=>({pane,pill}))),regions=[];
  assert.equal(pills.length,total===20?1:0,'Only a visible stream owner may display its task pill');
  if(total===20){
   const {pane,pill}=pills[0],task=state.tasks.find(task=>task.tabId===owner.tabId&&task.taskId==='stream-'+owner.id),native=fixture.nativeState(visible.find(record=>record.id===owner.tabId));
   assert.equal(pane.tabId,owner.tabId);assert.equal(pill.tabId,owner.tabId);assert.equal(pill.id,task.id);assert.equal(pill.taskId,task.taskId);assert.equal(pill.desk,owner.desk);assert.equal(pill.phase,'running');assert.equal(pill.indeterminate,'true');assert.equal(pill.value,'…');
   assert.equal(pane.dock.hidden,false);const box=pill.bounds,dock=pane.dock.bounds;
   assert.ok(box.width>0&&box.height>0&&box.x>=dock.x&&box.y>=dock.y&&box.x+box.width<=dock.x+dock.width&&box.y+box.height<=dock.y+dock.height,'The complete task pill belongs to its actual dock');
   assert.ok(Math.abs(dock.y-(pane.header.y+pane.header.height))<=1&&Math.abs(pane.slot.y-(dock.y+dock.height))<=1,'The task dock is between its own address row and page');
   assert.ok(Math.abs(native.bounds.y-pane.slot.y)<=1&&native.bounds.y>=box.y+box.height-1,'The actual native page cannot cover its task pill');
   regions.push({label:'Actual running HTTP stream task '+owner.id,bounds:box});
  }
  return{evidence:{streamId:owner.id,state,ui},regions};
 }
 async function rendererMonitor(start){
  if(start){await fixture.js(`(${rendererMonitorInPage.toString()})(true)`);frameMonitorStarted=true;return;}
  const result=await fixture.js(`(${rendererMonitorInPage.toString()})(false)`);frameMonitorStarted=false;result.gapDistribution=distribution(result.gaps);return result;
 }
 async function startStream(record,id){
  await fixture.pageJS(record,`void mouse631Stream(${JSON.stringify(id)});true`);
  await fixture.until(async()=>{const state=await fixture.pageJS(record,'mouse631.stream');return state&&state.chunks.length>=2&&!state.error;},'actual HTTP stream '+id+' begins');
  return{id,tabId:record.id,index:record.index,desk:record.desk,before:await fixture.pageJS(record,'mouse631.stream')};
 }
 async function finishStreams(records){
  const expected=[];
  for(const record of records){const stream=streams.get(record.id);assert.ok(stream&&!stream.closed);clearInterval(stream.timer);stream.done=true;stream.res.end(JSON.stringify({done:true,count:stream.values.length})+'\n');expected.push({id:record.id,requestCount:stream.requests,values:stream.values.slice(),sentAt:stream.sentAt.slice(),digest:createHash('sha256').update(stream.values.join('\n')).digest('hex')});}
  const result=[];
  for(let i=0;i<records.length;i++){
   const owner=fixture.created.find(page=>page.id===records[i].tabId);let actual;
   await fixture.until(async()=>{actual=await fixture.pageJS(owner,'mouse631.stream');return actual.done||actual.error;},'background HTTP stream '+records[i].id+' completes',10000);
   assert.equal(actual.error,null);assert.equal(actual.done,true);assert.equal(actual.requests,1);assert.deepEqual(actual.chunks,expected[i].values);assert.ok(actual.chunks.length>records[i].before.chunks.length);
   assert.equal(createHash('sha256').update(actual.chunks.join('\n')).digest('hex'),expected[i].digest);
   result.push({...records[i],server:expected[i],after:actual});
  }
  return result;
 }
 try{
  fixture=await createFixture(ctx,'stress',facts.budgetMs);
  // The inherited accessibility preference may intentionally bypass a slide.
  // Keep the predecessor fixture preference identical; only the retained Nora uses a snapshot animation in 6.0.36.
  facts.motionMedia={before:await fixture.js('matchMedia("(prefers-reduced-motion:reduce)").matches')};
  motionDebug=fixture.win.webContents.debugger;assert.equal(motionDebug.isAttached(),false);motionDebug.attach('1.3');motionAttached=true;
  await bounded(motionDebug.sendCommand('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'no-preference'}]}),3000,'Enable stress fixture motion');
  facts.motionMedia.normal=await fixture.js('matchMedia("(prefers-reduced-motion:reduce)").matches');assert.equal(facts.motionMedia.normal,false);
  const {browser,win,bank}=fixture,desks=bank.items.map(item=>item.id);assert.equal(desks.length,5);facts.desks=desks;
  server=http.createServer((req,res)=>{
   const url=new URL(req.url,'http://localhost');
   if(url.pathname==='/favicon.ico'){res.writeHead(204);res.end();return;}
   const page=url.pathname.match(/^\/page\/(\d+)\/$/);
   if(page){requests.push({path:url.pathname,index:Number(page[1]),at:performance.now(),stage:currentStage});res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});res.end(pageHTML(Number(page[1])));return;}
   const stream=url.pathname.match(/^\/stream\/([a-z0-9-]+)$/);
   if(stream){
    const id=stream[1];if(streams.has(id)){streams.get(id).requests++;res.writeHead(409);res.end('No stream restart');return;}
    res.writeHead(200,{'Content-Type':'application/x-ndjson','Cache-Control':'no-store'});res.flushHeaders();
    const state={id,res,requests:1,values:[],sentAt:[],timer:null,done:false,closed:false};streams.set(id,state);
    const send=()=>{const value=id+'-chunk-'+state.values.length+'-данные';state.values.push(value);state.sentAt.push({at:performance.now(),activeDesk:bank.active,noraHeld:!!browser.mouseSurfaceHold});res.write(JSON.stringify({value})+'\n');};send();state.timer=setInterval(send,200);res.on('close',()=>{state.closed=true;clearInterval(state.timer);});return;
   }
   res.writeHead(404);res.end();
  });await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const base='http://127.0.0.1:'+server.address().port;
  const surfaces=browser.mouseDesktops.surfaces,previews=browser.mouseDesktops.previews;surfaces.enableDiagnostics();previews.enableDiagnostics();
  wrap(surfaces,'capture',original=>async function(...args){const start=performance.now(),stage=currentStage,kind=operation;let result,error;try{result=await original.apply(this,args);return result;}catch(reason){error=String(reason.message);throw reason;}finally{captureCalls.push({stage,operation:kind,args:structuredClone(args),startedAt:start,elapsedMs:performance.now()-start,error:error||null,diagnostics:surfaces.diagnostics()});}});
  wrap(browser,'state',original=>function(...args){counts.state++;return switchTimings.call('browser.state',original,this,args);});
  wrap(browser,'layout',original=>function(...args){return switchTimings.call('browser.layout',original,this,args,undefined,()=>({activeDesk:bank.active,requestedPanelIds:Array.isArray(args[0])?args[0].slice(0,100).map(panel=>typeof panel?.id==='string'?panel.id:''):[]}));});
  if(browser.mouseCornerMask)wrap(browser,'mouseCornerMask',original=>function(...args){counts.nativeCorners++;return switchTimings.call('nativeCorners',original,this,args);});
  const shellGone=(_event,details)=>facts.renderFailures.push({event:'shell-render-process-gone',details,stage:currentStage});win.webContents.on('render-process-gone',shellGone);restorers.push(()=>win.webContents.removeListener('render-process-gone',shellGone));
  const groups=desks.map(()=>[]);let nextIndex=0;
  for(let d=0;d<5;d++){
   await fixture.switchDesk(desks[d]);const indices=Array.from({length:4},()=>nextIndex++);
   const added=await Promise.all(indices.map(index=>fixture.open(base+'/page/'+index+'/',index)));for(const record of added)instrument(record);groups[d].push(...added);await fixture.setLayout(groups[d].slice(0,4));
  }
  for(const [target,switchCount]of [[20,5],[50,10]]){
   if(target===50){currentStage='setup50';for(let d=0;d<5;d++){await fixture.switchDesk(desks[d]);const indices=Array.from({length:6},()=>nextIndex++);const added=await Promise.all(indices.map(index=>fixture.open(base+'/page/'+index+'/',index)));for(const record of added)instrument(record);groups[d].push(...added);await fixture.setLayout(groups[d].slice(0,4));}}
   currentStage=String(target);operation='prepare';await fixture.switchDesk(desks[0]);
   const owned=fixture.created.slice().sort((a,b)=>a.index-b.index);assert.equal(owned.length,target);assert.equal(new Set(owned.map(record=>record.page.view.webContents.id)).size,target);
   assert.ok(owned.every(record=>!record.page.view.webContents.isDestroyed()));
   const row={ownedPageCount:target,totalBrowserPages:browser.tabs.size,deskCount:5,pagesPerDesk:groups.map(group=>group.length),switchCount,switches:[],beforePages:await readAll(owned),layoutCallsBefore:browser.mouseLayoutCalls||0,countsBefore:{...counts},previewsBefore:previews.diagnostics(),memoryBefore:process.memoryUsage(),processesBefore:ctx.app.getAppMetrics(),startedAt:performance.now()};facts.stages.push(row);await save();
   await Promise.all(owned.map(record=>fixture.pageJS(record,`mouse631.metadataTicks=0;mouse631.metadataTimer=setInterval(()=>{document.title='Mouse631 page ${record.index} · '+(++mouse631.metadataTicks);},250);true`)));
   const running=[];for(let d=0;d<5;d++)running.push(await startStream(groups[d][target===20?0:4],'stage'+target+'-desk'+d));
   row.streamsBefore=running;await rendererMonitor(true);mainGaps.length=0;lastTick=performance.now();interval=setInterval(()=>{const now=performance.now();mainGaps.push(now-lastTick);lastTick=now;},25);
   for(let n=0;n<switchCount;n++){
    const d=(n+1)%5,id=desks[d],callsBefore=captureCalls.length,countsBefore={...counts},layoutBefore=browser.mouseLayoutCalls||0,mainCallTimings=switchTimings.begin(target,n+1),start=performance.now();operation='switch-'+n;mainCallTimings.startedAt=start;
    let elapsedMs;
    try{await fixture.switchDesk(id);elapsedMs=performance.now()-start;}
    catch(error){row.failedSwitchMainCallTimings=mainCallTimings;throw error;}
    finally{switchTimings.end(elapsedMs===undefined?performance.now():start+elapsedMs);}
    assert.ok(elapsedMs<12000);
    const slide=await fixture.js('structuredClone(MouseDesktopSlide.last)');assert.equal(slide.phase,'complete');
    if(Number(ctx.app.getVersion().split('.')[2])>=36){assert.equal(slide.strategy,'live');assert.equal(slide.presented,true);assert.equal(slide.snapshotCaptures,0);assert.equal(slide.animated,false);assert.equal(slide.decoded,false);assert.equal(captureCalls.length,callsBefore);assert.equal(counts.capturePage,countsBefore.capturePage,'A normal switch performs no native image readback');}
    else{assert.equal(slide.animated,true);assert.equal(slide.decoded,true);}
    const visible=groups[d].slice(0,4),entry={sequence:n+1,from:desks[n%5],to:id,elapsedMs,slide,mainCallTimings,counts:Object.fromEntries(Object.keys(counts).map(key=>[key,counts[key]-countsBefore[key]])),layoutCalls:(browser.mouseLayoutCalls||0)-layoutBefore,surfaceCalls:captureCalls.slice(callsBefore),visiblePageIds:visible.map(record=>record.id)};row.switches.push(entry);
    const progress=await switchProgress(target,running[d],running,visible,entry);
    entry.capture=await fixture.captureContent('mouse-631-stress-'+target+'-switch-'+(n+1)+'.png',visible,{shellRegions:progress.regions});facts.captures.push(entry.capture.filename);await save();
   }
   operation='nora';await fixture.js('MouseTest.desktopUI.open()');await fixture.until(()=>fixture.js('MouseTest.desktopUI.isOpen&&MouseTest.desktopUI.holdsNative&&!MouseTest.desktopUI.isPreparing'),'Nora opens over live background streams');
   const noraBefore=await Promise.all(running.map(stream=>fixture.pageJS(owned.find(record=>record.id===stream.tabId),'mouse631.stream.chunks.length')));await sleep(650);
   const noraAfter=await Promise.all(running.map(stream=>fixture.pageJS(owned.find(record=>record.id===stream.tabId),'mouse631.stream.chunks.length')));assert.ok(noraAfter.every((value,i)=>value>noraBefore[i]),'Every HTTP consumer advances while Nora holds the native pages');
   row.nora={before:noraBefore,after:noraAfter,held:!!browser.mouseSurfaceHold,diagnostics:surfaces.diagnostics()};assert.equal(row.nora.held,true);assert.equal(row.nora.diagnostics.lastCapture.paintProof,true);assert.equal(row.nora.diagnostics.lastPaint.ready,true);
   await fixture.js('MouseTest.desktopUI.close({immediate:true})');await fixture.until(()=>!browser.mouseSurfaceHold,'Nora releases the original native pages');
   row.afterNoraCapture=await fixture.captureContent('mouse-631-stress-'+target+'-after-nora.png',groups[0].slice(0,4));facts.captures.push(row.afterNoraCapture.filename);
   operation='complete-streams';row.streams=await finishStreams(running);
   row.afterPages=await readAll(owned);for(let i=0;i<row.beforePages.length;i++)fixture.assertIdentity(row.beforePages[i],row.afterPages[i]);
   assert.equal(facts.renderFailures.length,0,'No guest or shell renderer was replaced or crashed');
   clearInterval(interval);interval=null;row.mainEventLoopSamplesMs=mainGaps.slice();row.mainEventLoop=distribution(mainGaps);const {diagnostics,...renderer}=await rendererMonitor(false);row.renderer=renderer;row.rendererDiagnostics=diagnostics;assert.ok(row.renderer.frames>=2,'The real shell renderer continued presenting frames');
   row.layoutCalls=(browser.mouseLayoutCalls||0)-row.layoutCallsBefore;row.counts=Object.fromEntries(Object.keys(counts).map(key=>[key,counts[key]-row.countsBefore[key]]));row.previewsAfter=previews.diagnostics();row.surfaces=surfaces.diagnostics();row.memoryAfter=process.memoryUsage();row.processesAfter=ctx.app.getAppMetrics();row.elapsedMs=performance.now()-row.startedAt;row.switchLatencyMs=distribution(row.switches.map(item=>item.elapsedMs));
   row.metadata=await Promise.all(owned.map(record=>fixture.pageJS(record,'clearInterval(mouse631.metadataTimer);({index:mouse631.index,updates:mouse631.metadataTicks})')));assert.ok(row.metadata.every(item=>item.updates>0),'Every live page produced real title metadata');
   row.requests=requests.filter(request=>owned.some(record=>record.index===request.index));for(const record of owned)assert.equal(row.requests.filter(request=>request.index===record.index).length,1,'Each live document was loaded exactly once');
   await save();
  }
  facts.surfaceCalls=captureCalls;facts.elapsedMs=performance.now()-fixture.started;
 }catch(error){verificationError=error;facts.error={message:error.message,stack:error.stack};if(error.capture)facts.failureCapture=error.capture;facts.surfaceCalls=captureCalls;await save();}
 finally{
  clearInterval(interval);for(const stream of streams.values()){clearInterval(stream.timer);if(!stream.res.writableEnded)stream.res.end();}
  if(frameMonitorStarted&&fixture)await rendererMonitor(false).catch(error=>{facts.rendererCleanupError=error.message;});
  for(const restore of restorers.reverse())try{restore();}catch(error){facts.wrapperCleanupError=error.message;}
  if(fixture)try{facts.cleanup=await bounded(fixture.cleanup(),22000,'stress cleanup');facts.restored=true;}catch(error){cleanupError=error;facts.cleanupError={message:error.message,stack:error.stack};}
  if(motionAttached)try{
   try{await bounded(motionDebug.sendCommand('Emulation.setEmulatedMedia',{media:'',features:[]}),3000,'Restore stress fixture motion');}finally{motionDebug.detach();motionAttached=false;}
   facts.motionMedia.restored=await fixture.js('matchMedia("(prefers-reduced-motion:reduce)").matches');assert.equal(facts.motionMedia.restored,facts.motionMedia.before,'Stress fixture restores the inherited motion preference');
  }catch(error){cleanupError??=error;facts.motionCleanupError={message:error.message,stack:error.stack};}
  if(server){server.closeAllConnections();await bounded(new Promise(resolve=>server.close(resolve)),2000,'fixture HTTP shutdown').catch(error=>{cleanupError??=error;facts.serverCleanupError=error.message;});}
  facts.ok=!verificationError&&!cleanupError&&facts.restored;await save();
 }
 if(verificationError)throw verificationError;if(cleanupError)throw cleanupError;
 console.log('MOUSE_631_FIFTY_TABS_FIVE_DESKTOPS_NATIVE_PASS');return facts;
};
