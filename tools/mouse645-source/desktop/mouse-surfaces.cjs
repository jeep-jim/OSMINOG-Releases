'use strict';
// Short-lived, exact-viewport page pixels for shell transitions. Normal and
// private instances keep their own RAM only; nothing is written to a profile.
const {randomUUID}=require('node:crypto');
const {layerGeometry}=require('./mouse/capture-core.js');
// One preparation budget covers the whole queue, including native readback
// and encoding. Guest and shell readbacks share both count and pixel limits.
const MAX_PAGES=16,MAX_PNG_BYTES=32*1024*1024,MAX_PIXELS=16*1024*1024,MAX_CAPTURES=4,CAPTURE_MS=2500,HOLD_MS=5000,PAINT_MS=1500,PAINT_ATTEMPTS=8,PAINT_TOLERANCE=4;
const CAPTURE_ATTEMPTS=8,CAPTURE_RETRY_MS=Object.freeze([16,32,64,128,256,256,256]);
const rect=r=>r&&['x','y','width','height'].every(k=>Number.isFinite(r[k]))&&r.width>0&&r.height>0?{x:r.x,y:r.y,width:r.width,height:r.height}:null;
const same=(a,b)=>!!a&&!!b&&['x','y','width','height'].every(k=>a[k]===b[k]);
const pixelReservation=(width,height,scale)=>{const pixels=Math.ceil(width*scale)*Math.ceil(height*scale);return [width,height,scale].every(value=>Number.isFinite(value)&&value>0)&&Number.isSafeInteger(pixels)&&pixels>0&&pixels<=MAX_PIXELS?pixels:0;};
function representation(image,scaleLimit){
 if(image.isEmpty?.())return null;
 const scales=image.getScaleFactors?.();
 if(!Array.isArray(scales)||!scales.length||scales.some(value=>!Number.isFinite(value)||value<=0))return null;
 const scaleFactor=Math.max(...scales),size=image.getSize?.(scaleFactor);
 if(scaleFactor>scaleLimit||!size||!['width','height'].every(key=>Number.isSafeInteger(size[key])&&size[key]>0)||!Number.isSafeInteger(size.width*size.height))return null;
 return{scaleFactor,width:size.width,height:size.height};
}
// A decoded PNG and two renderer RAFs do not prove that its GPU upload has
// finished. Keep only nine small interior colour-region summaries per page,
// never another full image. Means over the same DIP regions tolerate texture
// interpolation at fractional/Retina scales without accepting blank slots.
function regionMean(bitmap,pixelWidth,pixelHeight,region,box){
 const sx=pixelWidth/box.width,sy=pixelHeight/box.height;
 const left=Math.max(0,Math.floor((region.x-box.x)*sx)),top=Math.max(0,Math.floor((region.y-box.y)*sy));
 const right=Math.min(pixelWidth,Math.ceil((region.x+region.width-box.x)*sx)),bottom=Math.min(pixelHeight,Math.ceil((region.y+region.height-box.y)*sy));
 if(right<=left||bottom<=top)return null;
 const sum=[0,0,0,0];let count=0;
 for(let y=top;y<bottom;y++)for(let x=left;x<right;x++){const i=(y*pixelWidth+x)*4;sum[0]+=bitmap[i+2];sum[1]+=bitmap[i+1];sum[2]+=bitmap[i];sum[3]+=bitmap[i+3];count++;}
 return sum.map(value=>value/count);
}
function imageRegions(image,pixelWidth,pixelHeight,scaleFactor,bounds){
 const bitmap=image.toBitmap({scaleFactor});if(bitmap.length!==pixelWidth*pixelHeight*4)throw Error('Invalid surface paint bitmap');
 const width=Math.min(12,bounds.width/8),height=Math.min(12,bounds.height/8),regions=[];
 for(const fy of [.25,.5,.75])for(const fx of [.25,.5,.75]){
  const region={x:bounds.x+bounds.width*fx-width/2,y:bounds.y+bounds.height*fy-height/2,width,height};
  const rgba=regionMean(bitmap,pixelWidth,pixelHeight,region,bounds);
  // Transparent source pixels have no independent visible colour to prove.
  // Native page snapshots are normally opaque; no artificial marker is added.
  if(rgba&&rgba[3]>=254)regions.push({...region,rgba});
 }
 return regions;
}
function matchesPaint(image,size,regions){
 if(image.isEmpty?.())return false;
 const scales=image.getScaleFactors?.().filter(v=>Number.isFinite(v)&&v>0)||[1],scaleFactor=Math.max(...scales),pixels=image.getSize(scaleFactor);
 if(!Number.isFinite(scaleFactor)||!pixels||!['width','height'].every(key=>Number.isInteger(pixels[key])&&pixels[key]>0)||pixels.width*pixels.height>MAX_PIXELS)return false;
 const bitmap=image.toBitmap({scaleFactor});if(bitmap.length!==pixels.width*pixels.height*4)return false;
 if(Math.abs(pixels.width/size[0]-pixels.height/size[1])>.02)return false;
 const box={x:0,y:0,width:size[0],height:size[1]};
 return regions.every(region=>{const mean=regionMean(bitmap,pixels.width,pixels.height,region,box);return mean&&mean.every((value,i)=>Math.abs(value-region.rgba[i])<=PAINT_TOLERANCE);});
}
class DesktopSurfaces{
 constructor({browser,bank,win,screen,onImage,now=Date.now,budgetNow=()=>performance.now(),captureMs=CAPTURE_MS,holdMs=HOLD_MS,paintMs=PAINT_MS}){
  Object.assign(this,{browser,bank,win,screen,onImage,now,budgetNow,captureMs,holdMs,paintMs});this.generation=0;this.records=new Map();this.activeCaptures=0;this.reservedPixels=0;this.capacityWaiters=new Set();this.busy=false;this.painting=false;this.held=null;this.locked=false;this.disposed=false;this.watchers=[];
  // BrowserWindow.webContents is a native getter: after 'closed' it throws.
  // Retain the emitter now so disposal can continue into closing every page.
  this.shellContents=win?.webContents;
  this.diagnostic=null;
  this.resize=()=>this.clear(true);this.navigation=(_event,_url,inPlace,isMainFrame)=>{if(isMainFrame&&!inPlace)this.clear(false);};
  win?.on?.('resize',this.resize);this.shellContents?.on?.('did-start-navigation',this.navigation);
 }
 enableDiagnostics(){this.diagnostic={sequence:0,lastCapture:null,lastPaint:null,events:[]};}
 diagnostics(){const trace=this.diagnostic;return trace?structuredClone({enabled:true,busy:this.busy,activeCaptures:this.activeCaptures,reservedPixels:this.reservedPixels,generation:this.generation,held:!!this.held,locked:this.locked,disposed:this.disposed,lastCapture:trace.lastCapture,lastPaint:trace.lastPaint,events:trace.events}):{enabled:false};}
 recordDiagnostic(trace,phase,detail={}){if(!trace||trace!==this.diagnostic)return;trace.events.push({phase,at:performance.now(),...detail});if(trace.events.length>32)trace.events.shift();}
 scaleFactor(){
  // Reserve for the largest real connected display, including a window moved
  // between displays during readback. Missing screen data is never a 1x guess.
  try{const displays=this.screen?.getAllDisplays?.();if(!Array.isArray(displays)||!displays.length||displays.some(display=>!Number.isFinite(display?.scaleFactor)||display.scaleFactor<=0))return 0;return Math.max(1,...displays.map(display=>display.scaleFactor));}catch{return 0;}
 }
 reserveCapture(pixels){
  if(!Number.isSafeInteger(pixels)||pixels<=0||pixels>MAX_PIXELS||this.activeCaptures>=MAX_CAPTURES||this.reservedPixels+pixels>MAX_PIXELS)return null;
  this.activeCaptures++;this.reservedPixels+=pixels;let released=false;
  return()=>{if(released)return;released=true;this.activeCaptures--;this.reservedPixels-=pixels;this.wakeCapacity();};
 }
 wakeCapacity(){for(const wake of [...this.capacityWaiters])wake();}
 waitCapture(pixels,current,waiting){
  return new Promise(resolve=>{
   let done=false;const finish=release=>{if(done)return;done=true;this.capacityWaiters.delete(wake);waiting.delete(cancel);resolve(release);};
   const cancel=()=>finish(null),wake=()=>{if(done)return;if(!current())return finish(null);const release=this.reserveCapture(pixels);if(release)finish(release);};
   this.capacityWaiters.add(wake);waiting.add(cancel);wake();
  });
 }
 waitRetry(ms,current,waiting){
  return new Promise(resolve=>{
   let done=false,timer;const finish=completed=>{if(done)return;done=true;clearTimeout(timer);this.capacityWaiters.delete(wake);waiting.delete(cancel);resolve(completed);};
   const cancel=()=>finish(false),wake=()=>{if(!current())finish(false);};
   this.capacityWaiters.add(wake);waiting.add(cancel);timer=setTimeout(()=>finish(current()),ms);timer.unref?.();wake();
  });
 }
 shape(){const size=this.win?.getContentSize?.();return Array.isArray(size)?size.join('x'):'';}
 live(id,hold){
  const page=this.browser.tabs.get(id),wc=page?.view?.webContents;
  if(this.disposed||this.locked||this.browser.disposed||this.win?.isDestroyed?.()||!page||!wc||wc.isDestroyed?.()||page.provider||page.ephemeral||this.bank.members[id]!==this.bank.active)return null;
  const prepared=!!hold&&this.held?.token===hold&&this.browser.mouseSurfaceHold===hold&&(this.browser.panels||[]).some(p=>p.id===id);
  if(!page.visible&&!prepared)return null;
  const bounds=rect(page.bounds),viewport=rect(page.view.getBounds?.()||page.bounds);if(!bounds||!viewport)return null;
  const geometry=layerGeometry({...bounds,...page.captureGeometry});if(!geometry)return null;
  return{page,wc,id,desk:this.bank.active,epoch:page.navigationEpoch||0,url:wc.getURL?.()||page.url||'',bounds,viewport,geometry};
 }
 valid(pin,hold){const live=this.live(pin.id,hold);return !!live&&live.page===pin.page&&live.wc===pin.wc&&live.desk===pin.desk&&live.epoch===pin.epoch&&live.url===pin.url&&same(live.bounds,pin.bounds)&&same(live.viewport,pin.viewport)&&same(live.geometry.clip,pin.geometry.clip)&&live.geometry.roundBottom===pin.geometry.roundBottom;}
 empty(){return{desk:this.bank.active,surfaces:[],complete:false,generation:this.generation,token:''};}
 async capture(args={}){
  if(!Array.isArray(args.ids)||args.ids.length>MAX_PAGES||args.ids.some(id=>typeof id!=='string'||!id||id.length>100)||new Set(args.ids).size!==args.ids.length)throw Error('Invalid surface page identities');
  if(args.paintProof!==undefined&&typeof args.paintProof!=='boolean')throw Error('Invalid surface paint proof option');
  const paintProof=args.paintProof!==false;
  const deadlineAt=this.budgetNow()+this.captureMs;
  const trace=this.diagnostic,observed=trace?{sequence:++trace.sequence,startedAt:performance.now(),requestedIds:args.ids.slice(),paintProof,generation:this.generation,reason:'pending',complete:false,completedIds:[],pngBytes:0,pixels:0,peakActiveCaptures:0,peakReservedPixels:0,pages:[]}:null;
  if(trace){trace.lastCapture=observed;this.recordDiagnostic(trace,'capture-start',{sequence:observed.sequence,ids:observed.requestedIds,activeCaptures:this.activeCaptures,reservedPixels:this.reservedPixels,busy:this.busy,held:!!this.held});}
  const resultDiagnostic=(reason,complete)=>{if(observed){observed.reason=reason;observed.complete=complete;observed.elapsedMs=performance.now()-observed.startedAt;this.recordDiagnostic(trace,'capture-result',{sequence:observed.sequence,reason,complete,elapsedMs:observed.elapsedMs,activeCaptures:this.activeCaptures});}};
  const incomplete=reason=>{resultDiagnostic(reason,false);return this.empty();};
  if(this.busy||this.disposed||this.locked||this.browser.disposed||this.held&&args.hold!==this.held.token||args.hold&&!this.held)return incomplete(this.busy?'busy':this.disposed?'disposed':this.locked?'locked':this.browser.disposed?'workspace-disposed':this.held?'different-hold':'hold-ended');
  const pins=args.ids.map(id=>this.live(id,args.hold));if(pins.some(p=>!p)){if(observed)observed.invalidIds=args.ids.filter((_id,i)=>!pins[i]);return incomplete('invalid-initial-pins');}
  const scaleFactor=this.scaleFactor();if(!scaleFactor&&pins.length)return incomplete('scale-unavailable');if(observed)observed.scaleFactor=scaleFactor;
  // Do not leave the largest selected viewport behind every small capture.
  // Stable sorting preserves request order for equal areas; limits stay shared.
  pins.sort((a,b)=>b.viewport.width*b.viewport.height-a.viewport.width*a.viewport.height);
  const generation=this.generation,desk=this.bank.active,shape=this.shape(),surfaces=[],regions=[],waiting=new Set();let index=0,bytes=0,pixels=0,cancelled=false,deadline=false,timer;
  const expire=()=>{if(deadline)return;cancelled=true;deadline=true;if(observed)this.recordDiagnostic(trace,'capture-deadline',{sequence:observed.sequence,elapsedMs:performance.now()-observed.startedAt,completedIds:surfaces.map(surface=>surface.id),activeCaptures:this.activeCaptures});};
  // A settled native promise can run before an overdue timer callback. Check
  // the same monotonic deadline before starting or retrying any native work.
  const current=()=>{if(!cancelled&&this.budgetNow()>=deadlineAt)expire();const scale=this.scaleFactor();return!cancelled&&!this.disposed&&!this.locked&&!this.browser.disposed&&generation===this.generation&&desk===this.bank.active&&shape===this.shape()&&(!pins.length||scale>0&&scale<=scaleFactor);};
  this.busy=true;
  const worker=async()=>{
   while(index<pins.length&&current()){
    const pin=pins[index++],row=observed?{id:pin.id,webContentsId:pin.wc.id,bounds:{...pin.bounds},viewport:{width:pin.viewport.width,height:pin.viewport.height},state:'starting',queueMs:null,nativeStartedAt:null,captureMs:null,pngMs:null,proofMs:null,bitmapReadouts:0,base64Ms:null,previewMs:null,attempts:[],backoffs:[]}:null;let stageStarted;
    if(row)observed.pages.push(row);
    const pageDiagnostic=state=>{if(row){row.state=state;this.recordDiagnostic(trace,'page',{sequence:observed.sequence,...row,attempts:row.attempts.map(attempt=>({...attempt})),backoffs:row.backoffs.map(backoff=>({...backoff}))});}};
    if(!this.valid(pin,args.hold)){pageDiagnostic('invalid-before-capture');continue;}
    const reservedPixels=pixelReservation(pin.viewport.width,pin.viewport.height,scaleFactor);
    if(!reservedPixels){pageDiagnostic('capture-pixel-budget');continue;}
    if(row){row.reservedPixels=reservedPixels;row.scaleFactor=scaleFactor;}
    const width=pin.viewport.width,height=pin.viewport.height;
    let release=null,image,png,actual,pixelWidth,pixelHeight,area,acquired=false;
    const paceRetry=async(attempt,reason)=>{
     release?.();release=null;
     if(!current()||!this.valid(pin,args.hold)){pageDiagnostic(deadline?'late-after-deadline':'capture-invalidated');return false;}
     const remaining=deadlineAt-this.budgetNow();if(remaining<=0){expire();pageDiagnostic('late-after-deadline');return false;}
     const delayMs=Math.min(CAPTURE_RETRY_MS[attempt],remaining),backoff=row?{afterAttempt:attempt+1,reason,scheduledAt:performance.now(),delayMs}:null;if(backoff)row.backoffs.push(backoff);pageDiagnostic('retry-wait');
     const completed=await this.waitRetry(delayMs,()=>current()&&this.valid(pin,args.hold),waiting);
     if(backoff){backoff.finishedAt=performance.now();backoff.elapsedMs=backoff.finishedAt-backoff.scheduledAt;backoff.completed=completed;}
     if(!completed)pageDiagnostic(deadline?'late-after-deadline':'capture-invalidated');return completed;
    };
    try{
     for(let attempt=0;attempt<CAPTURE_ATTEMPTS;attempt++){
      if(!current()||!this.valid(pin,args.hold)){pageDiagnostic('invalid-before-capture');break;}
      if(row)row.state='capacity';release=this.reserveCapture(reservedPixels);if(!release)release=await this.waitCapture(reservedPixels,()=>current()&&this.valid(pin,args.hold),waiting);
      if(!release){pageDiagnostic(deadline?'late-after-deadline':'capture-invalidated');break;}
      if(observed){observed.peakActiveCaptures=Math.max(observed.peakActiveCaptures,this.activeCaptures);observed.peakReservedPixels=Math.max(observed.peakReservedPixels,this.reservedPixels);}
      if(!current()||!this.valid(pin,args.hold)){pageDiagnostic('invalid-before-capture');break;}
      // Capturing an incoming desk under its owned hold must not show hidden
      // pages or keep the computer awake. Every retry uses the same options.
      let nativeAttempt;if(row){row.state='capturing';stageStarted=performance.now();row.nativeStartedAt=stageStarted;row.queueMs=stageStarted-observed.startedAt;row.captureMs=null;nativeAttempt={attempt:attempt+1,nativeStartedAt:stageStarted,queueMs:row.queueMs};row.attempts.push(nativeAttempt);}
      try{image=await pin.wc.capturePage(undefined,{stayHidden:true,stayAwake:false});}
      catch(error){
       if(nativeAttempt){const finishedAt=performance.now();Object.assign(nativeAttempt,{finishedAt,elapsedMs:finishedAt-stageStarted,outcome:'rejected',message:String(error?.message||error).slice(0,512)});}
       // Viz can reject a copy request before returning any pixels. Pace only
       // this exact native rejection, within the original preparation budget;
       // a timer is not readiness evidence and no image fallback is accepted.
       if(error?.message!=='UnknownVizError'||attempt+1>=CAPTURE_ATTEMPTS)throw error;
       if(!await paceRetry(attempt,'UnknownVizError'))break;
       continue;
      }
      if(nativeAttempt){const finishedAt=performance.now();Object.assign(nativeAttempt,{finishedAt,elapsedMs:finishedAt-stageStarted,outcome:'captured'});row.captureMs=nativeAttempt.elapsedMs;pageDiagnostic('captured');}
      if(!current()){pageDiagnostic(deadline?'late-after-deadline':'capture-invalidated');break;}
      if(!this.valid(pin,args.hold)){pageDiagnostic('pin-changed-after-capture');break;}
      if(image.isEmpty?.()){pageDiagnostic('empty-image');break;}
      // Preserve the sharpest representation the compositor actually supplied.
      // NativeImage.toPNG defaults to 1x even when the original frame is Retina.
      actual=representation(image,scaleFactor);
      if(row)row.imageRepresentation=actual?{...actual}:null;
      if(nativeAttempt)nativeAttempt.imageRepresentation=actual?{...actual}:null;
      if(!actual||actual.width*actual.height>MAX_PIXELS){pageDiagnostic('scale-or-pixel-budget');break;}
      if(actual.width*actual.height>reservedPixels){
       // A previous larger viewport may exceed this request's reservation.
       // Its valid scale/size are metadata only: discard it before allocating
       // PNG or bitmap output, without enlarging the shared pixel reservation.
       if(nativeAttempt){nativeAttempt.outcome='wrong-viewport';nativeAttempt.rejectedBeforeEncoding=true;}pageDiagnostic('native-viewport-dimensions');
       image=null;actual=null;
       if(attempt+1>=CAPTURE_ATTEMPTS||!await paceRetry(attempt,'viewport-mismatch'))break;
       continue;
      }
      if(pixels+actual.width*actual.height>MAX_PIXELS){pageDiagnostic('scale-or-pixel-budget');break;}
      if(row){row.state='png';stageStarted=performance.now();}
      png=image.toPNG({scaleFactor:actual.scaleFactor});
      if(row)row.pngMs=performance.now()-stageStarted;
      if(!Buffer.isBuffer(png)||png.length<24||!png.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))){pageDiagnostic('invalid-png');break;}
      pixelWidth=png.readUInt32BE(16);pixelHeight=png.readUInt32BE(20);area=pixelWidth*pixelHeight;
      if(row){row.pngBytes=png.length;row.pixelWidth=pixelWidth;row.pixelHeight=pixelHeight;}
      if(nativeAttempt)nativeAttempt.png={width:pixelWidth,height:pixelHeight,bytes:png.length};
      if(bytes+png.length>MAX_PNG_BYTES||pixels+area>MAX_PIXELS){pageDiagnostic(bytes+png.length>MAX_PNG_BYTES?'png-byte-budget':'png-pixel-budget');break;}
      if(pixelWidth!==actual.width||pixelHeight!==actual.height){pageDiagnostic('png-dimensions');break;}
      if(pixelWidth<width-1||pixelHeight<height-1||Math.abs(pixelWidth/width-pixelHeight/height)>.02){
       // A resized hidden view can still return its previous compositor size.
       // Never stretch or accept that image. Request fresh pixels under the
       // same identity pins, capacity, attempt count and original deadline.
       if(nativeAttempt)nativeAttempt.outcome='wrong-viewport';pageDiagnostic('png-dimensions');
       image=null;png=null;actual=null;
       if(attempt+1>=CAPTURE_ATTEMPTS||!await paceRetry(attempt,'viewport-mismatch'))break;
       continue;
      }
      acquired=true;break;
     }
     if(!acquired)continue;
     if(!current()){pageDiagnostic(deadline?'late-after-deadline':'capture-invalidated');continue;}
     if(!this.valid(pin,args.hold)){pageDiagnostic('pin-changed-after-capture');continue;}
     // Nora verifies these regions against an actual shell readback before it
     // hides native guests. A normal desktop slide has no such consumer and
     // must not copy a full viewport bitmap merely to discard nine summaries.
     if(paintProof){if(row){row.state='proof';stageStarted=performance.now();row.bitmapReadouts++;}regions.push(...imageRegions(image,pixelWidth,pixelHeight,actual.scaleFactor,pin.bounds));if(row)row.proofMs=performance.now()-stageStarted;}
     bytes+=png.length;pixels+=area;
     if(row){row.state='base64';stageStarted=performance.now();}const src='data:image/png;base64,'+png.toString('base64');if(row)row.base64Ms=performance.now()-stageStarted;
     surfaces.push({id:pin.id,src,width,height,pixelWidth,pixelHeight,epoch:pin.epoch,webContentsId:pin.wc.id,bounds:{...pin.bounds},clip:{...pin.geometry.clip},roundBottom:pin.geometry.roundBottom});
     if(row){row.state='preview';stageStarted=performance.now();}
     try{this.onImage?.(pin.id,image,pin);}catch(error){if(row)row.previewError=String(error?.message||error).slice(0,512);}
     if(row){row.previewMs=performance.now()-stageStarted;row.pngBytes=png.length;row.pixelWidth=pixelWidth;row.pixelHeight=pixelHeight;pageDiagnostic('complete');}
    }catch(error){if(row){row.errorStage=row.state;row.message=String(error?.message||error).slice(0,512);pageDiagnostic('error');}}finally{release?.();}
   }
  };
  try{
   const deadlineWait=new Promise(resolve=>{timer=setTimeout(()=>{expire();resolve();},Math.max(0,deadlineAt-this.budgetNow()));timer.unref?.();});
   await Promise.race([Promise.all(Array.from({length:Math.min(MAX_CAPTURES,pins.length)},worker)),deadlineWait]);
   if(observed){observed.completedIds=surfaces.map(surface=>surface.id);observed.pngBytes=bytes;observed.pixels=pixels;}
   if(!current())return incomplete(deadline?'deadline':this.disposed?'disposed':this.locked?'locked':this.browser.disposed?'workspace-disposed':generation!==this.generation?'generation-changed':desk!==this.bank.active?'desktop-changed':shape!==this.shape()?'window-size-changed':'display-scale-changed');
   if(surfaces.length!==pins.length)return incomplete('incomplete-pages');
   if(pins.some(pin=>!this.valid(pin,args.hold)))return incomplete('pins-changed');
   const token=randomUUID();this.records.set(token,{generation,desk,shape,scaleFactor,pins,regions,paintProof,at:this.now()});while(this.records.size>2)this.records.delete(this.records.keys().next().value);
   // Once the selected incoming desk has a complete validated frame, pages
   // from a previous desk no longer own the long-lived Nora hold. Background
   // navigation there must not close Nora after a successful desk switch.
   if(args.hold)this.watch(pins,true);
   resultDiagnostic('complete',true);
   // The capture record and the hold have separate identities. A renderer
   // borrowing Nora's hold can verify that this frame belongs to its lease
   // without treating the new capture token as a replacement hold.
   return{desk,surfaces,complete:true,generation,token,holdToken:args.hold||''};
  }finally{cancelled=true;clearTimeout(timer);for(const cancel of [...waiting])cancel();this.busy=false;}
 }
 async present(args={}){
  if(typeof args.token!=='string'||!args.token||args.token.length>100||args.holdToken!==undefined&&(typeof args.holdToken!=='string'||!args.holdToken||args.holdToken.length>100))throw Error('Invalid surface paint identity');
  const record=this.records.get(args.token),trace=this.diagnostic,started=performance.now(),scaleFactor=this.scaleFactor();
  const current=()=>{const scale=this.scaleFactor();return record&&this.records.get(args.token)===record&&!this.disposed&&!this.locked&&!this.browser.disposed&&!this.win?.isDestroyed?.()&&!this.shellContents?.isDestroyed?.()&&record.generation===this.generation&&record.desk===this.bank.active&&record.shape===this.shape()&&scale>0&&scale<=scaleFactor&&(!record.pins.length||scale<=record.scaleFactor)&&this.now()-record.at<=HOLD_MS&&(args.holdToken?this.held?.token===args.holdToken&&this.browser.mouseSurfaceHold===args.holdToken:!this.held)&&record.pins.every(pin=>this.valid(pin,args.holdToken));};
  const observed={startedAt:started,attempts:0,regions:record?.regions.length||0,held:!!args.holdToken,ready:false,reason:'pending'};
  if(trace)trace.lastPaint=observed;
  const finish=(ready,reason)=>{Object.assign(observed,{ready,reason,elapsedMs:performance.now()-started});this.recordDiagnostic(trace,'paint-result',observed);return{ready,reason,attempts:observed.attempts,regions:observed.regions};};
  if(!scaleFactor)return finish(false,'scale-unavailable');
  if(!current())return finish(false,'stale');
  if(!record.paintProof)return finish(false,'proof-unavailable');
  if(this.painting||typeof this.shellContents?.capturePage!=='function')return finish(false,'unavailable');
  const size=this.win.getContentSize(),reservedPixels=pixelReservation(size[0],size[1],scaleFactor),waiting=new Set();if(!reservedPixels)return finish(false,'pixel-budget');
  Object.assign(observed,{scaleFactor,reservedPixels,peakActiveCaptures:0,peakReservedPixels:0});
  let cancelled=false,timer;this.painting=true;this.recordDiagnostic(trace,'paint-start',{held:observed.held,regions:observed.regions});
  const work=(async()=>{
   try{
    for(let attempt=0;attempt<PAINT_ATTEMPTS&&!cancelled;attempt++){
     if(!current())return finish(false,'stale');
     let release=this.reserveCapture(reservedPixels);if(!release)release=await this.waitCapture(reservedPixels,()=>!cancelled&&current(),waiting);
     if(!release)return cancelled?null:finish(false,'stale');
     observed.peakActiveCaptures=Math.max(observed.peakActiveCaptures,this.activeCaptures);observed.peakReservedPixels=Math.max(observed.peakReservedPixels,this.reservedPixels);
     try{
      if(cancelled)return null;if(!current())return finish(false,'stale');
      observed.attempts++;const image=await this.shellContents.capturePage(undefined,{stayHidden:true,stayAwake:false});
      if(cancelled)return null;
      if(!current())return finish(false,'stale');
      const actual=representation(image,scaleFactor);if(!actual||actual.width*actual.height>reservedPixels)return finish(false,'pixel-budget');
      if(matchesPaint(image,size,record.regions))return finish(true,'painted');
     }finally{release();}
    }
    if(!cancelled)return finish(false,'mismatch');
   }catch(error){if(!cancelled){this.recordDiagnostic(trace,'paint-error',{message:String(error?.message||error).slice(0,512)});return finish(false,'readback-error');}}
   finally{this.painting=false;}
  })();
  try{return await Promise.race([work,new Promise(resolve=>{timer=setTimeout(()=>{cancelled=true;resolve(finish(false,'deadline'));},this.paintMs);timer.unref?.();})]);}
  finally{cancelled=true;clearTimeout(timer);for(const cancel of [...waiting])cancel();}
 }
 watch(pins,replace=false){
  if(replace){const selected=new Set(pins.map(pin=>pin.wc));for(const w of this.watchers)if(!selected.has(w.wc)){w.wc.removeListener?.('destroyed',w.clear);w.wc.removeListener?.('did-start-navigation',w.nav);}this.watchers=this.watchers.filter(w=>selected.has(w.wc));}
  for(const pin of pins){if(this.watchers.some(w=>w.wc===pin.wc))continue;const clear=()=>this.clear(true),nav=(_event,_url,_inPlace,isMainFrame)=>{if(isMainFrame)this.clear(true);};pin.wc.on?.('destroyed',clear);pin.wc.on?.('did-start-navigation',nav);this.watchers.push({wc:pin.wc,clear,nav});}
 }
 begin(token,purpose='transition'){
  if(!['transition','popover'].includes(purpose))throw Error('Invalid surface hold purpose');
  const record=this.records.get(token);
  if(this.held||!record||purpose==='popover'&&!record.paintProof||this.disposed||this.locked||record.generation!==this.generation||record.desk!==this.bank.active||record.shape!==this.shape()||this.now()-record.at>HOLD_MS||record.pins.some(pin=>!this.valid(pin)))return{held:false,token:''};
  this.held={token,generation:this.generation,purpose};this.browser.mouseSurfaceHold=token;this.watch(record.pins);
  if(purpose==='transition'){this.timer=setTimeout(()=>this.clear(true),this.holdMs);this.timer.unref?.();}
  try{this.browser.layout(this.browser.panels||[]);}catch(error){this.clear(false);throw error;}
  return{held:true,token};
 }
 end(token){if(!this.held||this.held.token!==token)return{released:false};this.clear(false);return{released:true};}
 clear(notify=false){
  this.generation++;this.records.clear();clearTimeout(this.timer);this.timer=null;
  for(const w of this.watchers){w.wc.removeListener?.('destroyed',w.clear);w.wc.removeListener?.('did-start-navigation',w.nav);}this.watchers=[];
  const held=this.held;this.held=null;
  if(held&&this.browser.mouseSurfaceHold===held.token){this.browser.mouseSurfaceHold=null;if(!this.disposed&&!this.browser.disposed&&!this.win?.isDestroyed?.())this.browser.layout(this.browser.panels||[]);}
  this.wakeCapacity();
  if(notify&&!this.disposed&&!this.win?.isDestroyed?.()){try{this.win.webContents.send('mouse:previews-cleared');}catch{}}
 }
 lock(){this.locked=true;this.clear(true);}
 unlock(){this.locked=false;}
 dispose(){if(this.disposed)return;this.disposed=true;this.clear(false);this.win?.removeListener?.('resize',this.resize);this.shellContents?.removeListener?.('did-start-navigation',this.navigation);}
}
module.exports={DesktopSurfaces,MAX_PAGES,MAX_PNG_BYTES,MAX_PIXELS,MAX_CAPTURES,CAPTURE_MS,CAPTURE_ATTEMPTS,CAPTURE_RETRY_MS,HOLD_MS,PAINT_MS,PAINT_ATTEMPTS,PAINT_TOLERANCE};
