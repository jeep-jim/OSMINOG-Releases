'use strict';
// Retained installed acceptance for 636: downloads, AI preview, capture and focus.
// Tile search was removed by the owner; its historical 634/635 gates remain in their release history.
const assert=require('node:assert/strict'),fs=require('node:fs/promises'),path=require('node:path'),http=require('node:http');
const {screen,nativeImage,webContents}=require('electron');
const {createFixture,pageHTML,bounded,sha256}=require('./mouse-631-smoke-helpers.cjs');
const {screenCropGeometry}=require('./mouse-628-ui-smoke.cjs');
const {nativeHitTarget}=require('./mouse-smoke-hit-target.cjs');
const {installInputProbe}=require('./mouse-633-smoke-helpers.cjs');
const {ownerPage,aiReadback,assertSplit,observeChatNavigation,assertCanceledChatNavigation}=require('./mouse-634-smoke-helpers.cjs');
const {withinCaptureDeadline}=require('./mouse-634-capture-corners.cjs');
const {guestInputReadback,nativeGuestInputState,observeGuestClick}=require('./mouse-636-guest-input-diagnostics.cjs');
const {focusNativeInputWindow}=require('./mouse-636-native-input-focus.cjs');

module.exports=async ctx=>{
 const {app,win,browser,store,libraryService,globalCapture,overlayGate}=ctx;
 const started=Date.now(),budgetMs=240000,exit=require('./mouse-smoke-exit.cjs')({app,win});
 const facts={schema:1,version:app.getVersion(),platform:process.platform,arch:process.arch,pid:process.pid,budgetMs,packaged:app.isPackaged,profileIsolated:false,physicalUserDeviceVerified:false,liveExternalAccountsVerified:false,source:'Installed app, native pointer input, owned HTTP/download fixtures and actual composed/OS pixels',removedFeatures:['tile-search'],stage:'identity',ok:false,restored:false,nativeInputs:[],guestClickAttempts:[],captures:[]};
 const save=()=>fs.writeFile('mouse-636-retained-owner-feedback.json',JSON.stringify(facts,null,2)+'\n');
 const watchdog=setTimeout(()=>{facts.error={stage:facts.stage,message:'Mouse636 retained fixed 240000 ms native budget exceeded'};void save().finally(()=>exit(1));},budgetMs);
 let fixture,nativeInput,ownedFolder,originalLibrary,originalZoom,downloadListener,error,cleanupError,base='',previewBase='';
 const streams=new Map(),downloads=new Map(),timers=new Set(),servers=[],requests=[];
 const inputSource=()=>process.platform==='darwin'?'CGEvent':process.platform==='win32'?'User32':'XTest';
 const stage=async(name,work)=>{facts.stage=name;await save();console.log('MOUSE_636_RETAINED_STAGE '+name);return work();};
 async function shellReady(){await fixture.until(()=>fixture.js('document.documentElement.dataset.mouseReady==="true"&&!!globalThis.MouseTest').catch(()=>false),'634 ready shell',15000);await fixture.js(`(${installInputProbe.toString()})()`);}
 async function focus(){return focusNativeInputWindow({app,win,until:fixture.until});}
 async function click(selector,{navigates=false,xFraction=.5,yFraction=.5}={}){
  await focus();await fixture.js(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'nearest',inline:'nearest'});true`);await fixture.frame();let hit;
  await fixture.until(async()=>{hit=await fixture.js(`(${nativeHitTarget.toString()})(document.querySelector(${JSON.stringify(selector)}),${JSON.stringify({xFraction,yFraction})})`);return hit.ready;},'634 native target '+selector);
  await fixture.js(`__mouse633Input.begin(${JSON.stringify(selector)})`);const origin=win.getContentBounds(),point={x:Math.round(origin.x+hit.x),y:Math.round(origin.y+hit.y)};
  assert.equal(await nativeInput.testClick(point.x,point.y),true);const result={selector,source:inputSource(),point,at:Date.now(),navigates};facts.nativeInputs.push(result);
  if(!navigates){await fixture.until(async()=>{result.events=await fixture.js('__mouse633Input.read()');return result.events.some(event=>event.type==='click'&&event.trusted&&event.matches);},'634 trusted click '+selector);await fixture.frame();}
  return result;
 }
 async function guestClick(record,selector){
  const focusReadiness=await focus();let hit;
  await fixture.until(async()=>{hit=await fixture.pageJS(record,`(${nativeHitTarget.toString()})(document.querySelector(${JSON.stringify(selector)}))`);return hit.ready;},'634 guest target '+selector);
  const factor=record.page.view.webContents.getZoomFactor(),origin=win.getContentBounds(),bounds=record.page.bounds,point={x:Math.round(origin.x+bounds.x+hit.x*factor),y:Math.round(origin.y+bounds.y+hit.y*factor)},beforeGuest=await fixture.pageJS(record,'('+guestInputReadback.toString()+')()'),count=beforeGuest.count;
  const details={selector,source:inputSource(),point,tabId:record.id,webContentsId:record.page.view.webContents.id,hit,factor,contentBounds:{...origin},pageBounds:{...bounds},beforeCount:count,beforeGuest,focusReadiness};
  const events=await observeGuestClick({attempts:facts.guestClickAttempts,details,readNative:()=>nativeGuestInputState({win,page:record.page,screen,webContents}),post:()=>nativeInput.testClick(point.x,point.y),readEvents:()=>fixture.pageJS(record,'mouse634.clicks.slice('+count+')'),accept:events=>events.some(event=>event.id===selector.slice(1)&&event.trusted),waitFor:fixture.until,label:'634 trusted guest link '+selector,save});
  const result={selector,source:inputSource(),point,tabId:record.id,webContentsId:record.page.view.webContents.id,events};facts.nativeInputs.push(result);return result;
 }
 async function screenCapture(filename,kind,{deadline}={}){
  const acquire=async live=>{
  await fixture.frame();live();const display=screen.getDisplayMatching(win.getBounds()),contentBounds=win.getContentBounds(),remaining=Number.isFinite(deadline)?Math.min(4500,deadline-performance.now()):4500;
  live();const frame=await bounded(globalCapture.acquire(display),remaining,'634 actual OS pixels');live();assert.equal(frame.kind,'screen');
  const full=Buffer.from(frame.base.slice(frame.base.indexOf(',')+1),'base64'),screenPixelSize={width:full.readUInt32BE(16),height:full.readUInt32BE(20)},geometry=screenCropGeometry(display.bounds,contentBounds,screenPixelSize),image=nativeImage.createFromBuffer(full).crop(geometry.cropPixels),png=image.toPNG({scaleFactor:1});
  live();await fs.writeFile(filename,png);live();const displayFilename=filename.replace(/\.png$/,'-display.png');await fs.writeFile(displayFilename,full);live();
  const capture={filename,displayFilename,displaySha256:sha256(full),screenPixelSize,kind,source:'globalCapture.acquire(display)',backend:frame.backend,sha256:sha256(png),bytes:png.length,pixelSize:{width:png.readUInt32BE(16),height:png.readUInt32BE(20)},contentBounds,display:{id:display.id,bounds:display.bounds,workArea:display.workArea,scaleFactor:display.scaleFactor},cropPixels:geometry.cropPixels,mapping:geometry.mapping};facts.captures.push(capture);return capture;
  };return Number.isFinite(deadline)?withinCaptureDeadline(deadline,acquire):acquire(()=>{});
 }
 function serve(req,res){
  const url=new URL(req.url,'http://localhost'),page=url.pathname.match(/^\/page\/(\d+)\/$/),download=url.pathname.match(/^\/download\/(a|b|chat|preview)$/);res.setHeader('Cache-Control','no-store');
  if(page){const index=Number(page[1]);requests.push({index,at:Date.now()});res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});res.end(ownerPage(pageHTML(index),index,{base,previewBase}));return;}
  if(download){
   const name=download[1];if(streams.has(name)){streams.get(name).requests++;res.writeHead(409);res.end();return;}
   const data=Buffer.alloc(524288,65+['a','b','chat','preview'].indexOf(name)),stream={name,res,data,sent:0,cap:65536,requests:1,done:false};streams.set(name,stream);
   res.writeHead(200,{'Content-Type':'application/octet-stream','Content-Length':data.length,'Content-Disposition':'attachment; filename="mouse634-'+name+'.bin"'});res.flushHeaders();
   const timer=setInterval(()=>{if(res.destroyed){clearInterval(timer);timers.delete(timer);return;}if(stream.sent<Math.min(stream.cap,data.length)){const end=Math.min(stream.sent+16384,stream.cap,data.length);res.write(data.subarray(stream.sent,end));stream.sent=end;}if(stream.sent===data.length){stream.done=true;res.end();clearInterval(timer);timers.delete(timer);}},35);timers.add(timer);return;
  }
  res.writeHead(204);res.end();
 }
 async function listen(){const server=http.createServer(serve);servers.push(server);await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});return'http://127.0.0.1:'+server.address().port;}
 async function registeredPreview(chat,index){
  let page;await fixture.until(()=>{page=[...browser.tabs.values()].find(t=>t.previewOf===chat.id);return page&&!page.loading&&!page.error&&page.visible;},'634 lower native preview appears',15000);
  const record={id:page.id,index,desk:fixture.bank.active,page};if(!fixture.created.some(item=>item.id===record.id))fixture.created.push(record);
  await fixture.preparePage(record);await fixture.until(()=>fixture.js(`MouseTest.model.aiPreviewId===${JSON.stringify(record.id)}`),'634 renderer preview owner');await fixture.frame();return record;
 }
 try{
  assert.equal(process.env.CI,'true');assert.ok(path.isAbsolute(process.env.MOUSE_TEST_PROFILE||''));assert.equal(path.resolve(app.getPath('userData')),path.resolve(process.env.MOUSE_TEST_PROFILE));assert.equal(app.isPackaged,true);assert.ok(['6.0.36','6.0.37'].includes(app.getVersion()),'Retained636 acceptance requires636 or637');assert.equal(app.getName(),'Mouse Browser');facts.profileIsolated=true;
  nativeInput=ctx.nativeInput||(process.platform==='darwin'?require('./mouse-native-menu.node'):process.platform==='win32'?require('./mouse-windows-input.cjs').createWindowsInput():require('./mouse-linux-input.cjs').createLinuxInput());facts.nativeInputSource=inputSource();
  fixture=await createFixture({...ctx,nativeInput},'owner636-retained',budgetMs);await shellReady();originalLibrary=structuredClone(libraryService.library.data);originalZoom=await fixture.js('MouseNative.zoom("state")');ownedFolder=await fs.mkdtemp(path.join(app.getPath('userData'),'mouse634-owned-'));base=await listen();previewBase=await listen();facts.fixtureOrigins=[base,previewBase];facts.requests=requests;
  downloadListener=(_event,item,wc)=>{const match=new URL(item.getURL()).pathname.match(/^\/download\/(a|b|chat|preview)$/);if(!match)return;const name=match[1],file=path.join(ownedFolder,'mouse634-'+name+'.bin'),row={name,item,path:file,events:[],webContentsId:wc?.id,done:false};item.setSavePath(file);downloads.set(name,row);const observe=(event,state)=>row.events.push({event,type:event,state,received:item.getReceivedBytes(),total:item.getTotalBytes(),at:Date.now()});observe('start',item.getState());item.on('updated',(_e,state)=>observe('updated',state));item.once('done',(_e,state)=>{observe('done',state);row.done=state;});};browser.session.prependListener('will-download',downloadListener);
  fixture.records=[];for(let i=0;i<2;i++)fixture.records.push(await fixture.open(base+'/page/'+i+'/',i));const mains=[...fixture.records];await fixture.setLayout(mains);await fixture.js('MouseNative.zoom("set",{factor:1})');
  facts.downloads=await stage('pane-download-widgets',()=>require('./mouse-634-download-widget-smoke.cjs')({fixture,browser,win,libraryService,guestClick,screenCapture,streams,downloads,base}));
  await stage('ai-link-preview',async()=>{
   const chat=await fixture.open(base+'/page/2/',2);await browser.command('move-lane',{id:chat.id,lane:'side'});
   await fixture.js(`Object.assign(MouseTest.model,{aiOpen:true,aiWidth:380,aiId:${JSON.stringify(chat.id)},aiSessions:{[${JSON.stringify(base+'/page/2/')}]:${JSON.stringify(chat.id)}}});MouseTest.renderAISites();MouseTest.applySide();MouseTest.save()`);
   await fixture.until(()=>chat.page.visible&&chat.page.bounds.height>250,'634 visible chat');await fixture.frame();
   const before=await fixture.js(`(${aiReadback.toString()})()`),chatBefore=await fixture.identity(chat),mainBefore=await Promise.all(mains.map(fixture.identity)),totalBefore=browser.tabs.size,chatHeightBefore=chat.page.bounds.height;
   const ai=facts.aiPreview={ok:false,before,chatBefore,mainBefore};await save();
   ai.blankClick=await guestClick(chat,'#link-blank');let preview=await registeredPreview(chat,3);
   ai.first=await fixture.js(`(${aiReadback.toString()})()`);ai.chatAfterBlank=await fixture.identity(chat);await save();
   assertSplit(ai.first,{chatId:chat.id,previewId:preview.id,mainSlots:before.mainSlots});assert.equal(browser.tabs.size,totalBefore+1);assert.equal(preview.page.view.webContents.getURL(),previewBase+'/page/3/');fixture.assertIdentity(chatBefore,ai.chatAfterBlank);
   ai.native=[chat,preview].map(fixture.nativeState);assert.ok(ai.native.every(t=>t.visible&&t.attached&&t.parentVisible));await screenCapture('mouse-634-ai-preview-new-window.png','native target blank link opens below its chat');
   const previewId=preview.id,observation=observeChatNavigation(chat.page,previewBase+'/page/4/');ai.chatNavigation=observation.witness;
   try{
    ai.sameClick=await guestClick(chat,'#link-same');await fixture.until(()=>preview.page.view.webContents.getURL()===previewBase+'/page/4/'&&!preview.page.loading,'634 same-window URL loads below chat');preview.index=4;await fixture.preparePage(preview);
    ai.second=await fixture.js(`(${aiReadback.toString()})()`);ai.chatAfterSame=await fixture.identity(chat);ai.mainAfterSame=await Promise.all(mains.map(fixture.identity));await save();
    assertSplit(ai.second,{chatId:chat.id,previewId,mainSlots:before.mainSlots});assert.equal(browser.tabs.size,totalBefore+1);assertCanceledChatNavigation(ai.chatAfterBlank,ai.chatAfterSame,ai.chatNavigation,fixture.assertIdentity);for(let i=0;i<mains.length;i++)fixture.assertIdentity(mainBefore[i],ai.mainAfterSame[i]);
   }finally{observation.dispose();}
   ai.closeClick=await click('[data-action="close-ai-preview"]');await fixture.until(()=>!browser.tabs.has(previewId)&&chat.page.bounds.height===chatHeightBefore,'634 close restores full chat height');ai.closed=await fixture.js(`(${aiReadback.toString()})()`);ai.chatAfterClose=await fixture.identity(chat);await save();assert.equal(ai.closed.preview.hidden,true);assert.equal(ai.closed.previewId,'');assert.equal(browser.tabs.size,totalBefore);fixture.assertIdentity(ai.chatAfterSame,ai.chatAfterClose);
   await guestClick(chat,'#link-blank');preview=await registeredPreview(chat,3);ai.reopened=await fixture.js(`(${aiReadback.toString()})()`);ai.chatAfter=await fixture.identity(chat);ai.mainAfter=await Promise.all(mains.map(fixture.identity));await save();assertSplit(ai.reopened,{chatId:chat.id,previewId:preview.id,mainSlots:before.mainSlots});fixture.assertIdentity(ai.chatAfterSame,ai.chatAfter);for(let i=0;i<mains.length;i++)fixture.assertIdentity(mainBefore[i],ai.mainAfter[i]);
   fixture.records=[...mains,chat,preview];Object.assign(ai,{ok:true,mainTabsUnchanged:true,previewReused:true,chatRestored:true});await save();
   facts.aiPreview.downloads=await require('./mouse-634-download-widget-smoke.cjs')({fixture,browser,win,libraryService,guestClick,screenCapture,streams,downloads,base,records:[chat,preview],names:['chat','preview'],downloadOrigins:[base,previewBase],filePrefix:'mouse-634-ai-download-widget'});
   const targets=[...mains.map((record,i)=>({id:record.id,role:'main',slotSelector:'.pane[data-pane="p'+(i+1)+'"] .page-slot',paneSelector:'.pane[data-pane="p'+(i+1)+'"]',backgroundRGB:[243,240,232]})),{id:chat.id,role:'ai-chat',slotSelector:'#ai-slot',paneSelector:'#ai-chat-pane',backgroundRGB:[243,240,232]},{id:preview.id,role:'ai-preview',slotSelector:'#ai-preview-slot',paneSelector:'#ai-preview-pane',backgroundRGB:[243,240,232]}];
   facts.captureCorners=await stage('capture-rounded-corners',()=>require('./mouse-634-capture-corners.cjs')({win,browser,globalCapture,overlayGate,fixture,click,screenCapture,targets}));
  });
  facts.focusedChrome=await stage('focused-chrome',()=>require('./mouse-634-focused-chrome-smoke.cjs')({fixture,browser,win,click,screenCapture}));
  facts.requests=requests;facts.elapsedMs=Date.now()-started;
 }catch(cause){error=cause;facts.error={stage:facts.stage,message:cause.message,stack:cause.stack};await save();try{if(fixture)await bounded(screenCapture('mouse-636-retained-owner-feedback-failure.png','failure '+facts.stage),5000,'634 failure OS snapshot');}catch(captureError){facts.failureCaptureError=captureError.message;await save();}}
 finally{
  const restore=async(label,operation)=>{try{return await operation();}catch(cause){cleanupError||=cause;(facts.cleanupErrors||=[]).push({stage:label,message:cause.message});facts.cleanupError={message:cleanupError.message,stack:cleanupError.stack};await save();}};
  try{
   if(downloadListener)browser.session.removeListener('will-download',downloadListener);for(const row of downloads.values())if(!row.done)row.item.cancel();for(const timer of timers)clearInterval(timer);timers.clear();
   for(const server of servers){server.closeAllConnections();await bounded(new Promise(resolve=>server.close(resolve)),2000,'634 fixture HTTP close');}
   if(fixture){
    await restore('renderer cleanup',()=>bounded(fixture.js('globalThis.__mouse633Input?.dispose();document.querySelector("#capture-dialog")?.close();MouseTest.browsing.close();MouseTest.desktopUI.close({immediate:true})'),2000,'634 renderer cleanup'));
    if(originalZoom)await restore('zoom restoration',()=>bounded(fixture.js(`MouseNative.zoom('set',{factor:${originalZoom.factor}})`),2000,'634 zoom restoration'));
    facts.cleanup=await restore('workspace restoration',()=>bounded(fixture.cleanup(),22000,'634 workspace restoration'));
    if(originalLibrary)await restore('library restoration',async()=>{libraryService.library.data=originalLibrary;libraryService.library.changed();await libraryService.flush();});
    libraryService.activity.clear();facts.restored=facts.cleanup?.restored===true;
   }
   if(ownedFolder)await fs.rm(ownedFolder,{recursive:true,force:true});
  }catch(cause){cleanupError||=cause;(facts.cleanupErrors||=[]).push({stage:'outer cleanup',message:cause.message});facts.cleanupError={message:cleanupError.message,stack:cleanupError.stack};}
  facts.ok=!error&&!cleanupError&&facts.restored;facts.elapsedMs=Date.now()-started;facts.stage=facts.ok?'complete':'failed';await save();clearTimeout(watchdog);
 }
 if(facts.ok){console.log('MOUSE_636_RETAINED_OWNER_FEEDBACK_PASS');exit(0);}else{console.error('MOUSE_636_RETAINED_OWNER_FEEDBACK_FAILED '+facts.error?.message+' '+(facts.cleanupError?.message||''));exit(1);}
};
