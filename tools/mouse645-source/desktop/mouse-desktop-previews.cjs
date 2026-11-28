'use strict';
// Desktop thumbnails never leave RAM. Hidden pages are represented by their last
// visible capture, not woken or navigated just to paint a preview.
const L=require('./mouse/layout.js');
const MAX_IMAGES=60,MAX_BYTES=256*1024,MAX_EDGE=400,MAX_CACHE_BYTES=16*1024*1024,MIN_CAPTURE_INTERVAL=750,MAX_CAPTURES=2,MAX_CAPTURE_QUEUE=12;
const site=url=>{try{return new URL(url).hostname||'Новая вкладка';}catch{return'';}};
class DesktopPreviews{
 constructor({browser,bank,state,now=Date.now,fromBitmap=(bitmap,size)=>require('electron').nativeImage.createFromBitmap(bitmap,size)}){Object.assign(this,{browser,bank,state,now,fromBitmap});this.cache=new Map();this.pending=new Map();this.attempts=new Map();this.captureWaiters=[];this.activeCaptures=0;this.generation=0;this.disposed=false;this.locked=false;this.diagnostic=null;}
 enableDiagnostics(){this.diagnostic={captures:0,resizes:0,bitmapCopies:0,jpegEncodes:0,cacheHits:0,resizeMs:0,jpegMs:0};}
 diagnostics(){return this.diagnostic?{enabled:true,...this.diagnostic,entries:this.cache.size,retainedBitmaps:[...this.cache.values()].filter(e=>e.bitmap).length,retainedBytes:this.cacheBytes(),activeCaptures:this.activeCaptures,queued:this.captureWaiters.length,pending:this.pending.size,generation:this.generation,locked:this.locked,disposed:this.disposed}:{enabled:false};}
 cacheBytes(){return[...this.cache.values()].reduce((bytes,entry)=>bytes+entry.bytes,0);}
 trim(){let bytes=this.cacheBytes();while(this.cache.size>MAX_IMAGES||bytes>MAX_CACHE_BYTES){const [id,entry]=this.cache.entries().next().value;bytes-=entry.bytes;this.cache.delete(id);}}
 clear(){this.generation++;this.cache.clear();this.pending.clear();this.attempts.clear();for(const resolve of this.captureWaiters.splice(0))resolve(null);}
 drop(id){this.cache.delete(id);this.attempts.delete(id);}
 lock(){this.locked=true;this.clear();}
 unlock(){this.locked=false;}
 dispose(){this.disposed=true;this.clear();}
 live(id){const t=this.browser.tabs.get(id),wc=t?.view?.webContents;return t&&wc&&!wc.isDestroyed?.()?{t,wc}:null;}
 valid(id,entry){const live=this.live(id);return live&&live.t===entry.page&&(live.t.navigationEpoch||0)===entry.epoch&&(live.wc.getURL?.()||live.t.url||'')===entry.url&&this.bank.members[id]===entry.desk;}
 rememberImage(id,image,pin){
  if(this.disposed||this.locked||this.browser.disposed||pin.desk!==this.bank.active||!this.valid(id,pin)||image.isEmpty?.())return;
  const at=this.now(),previous=this.cache.get(id);if(previous&&this.valid(id,previous)&&at-previous.capturedAt<MIN_CAPTURE_INTERVAL){if(this.diagnostic)this.diagnostic.cacheHits++;return;}
  const size=image.getSize(1);if(!size||!['width','height'].every(key=>Number.isSafeInteger(size[key])&&size[key]>0))return;
  const ratio=Math.min(1,MAX_EDGE/size.width,MAX_EDGE/size.height),width=Math.max(1,Math.floor(size.width*ratio)),height=Math.max(1,Math.floor(size.height*ratio)),trace=this.diagnostic,started=trace?performance.now():0;
  // A resized NativeImage can retain its source for further scale factors.
  // Keep only this small copied bitmap, never the full captured viewport.
  // JPEG is made lazily when a thumbnail is actually requested, outside the
  // outgoing/incoming PNG preparation on the desktop transition's path.
  if(trace)trace.resizes++;const reduced=image.resize({width,height});
  if(trace)trace.bitmapCopies++;const bitmap=reduced.toBitmap({scaleFactor:1});if(trace)trace.resizeMs+=performance.now()-started;
  if(!Buffer.isBuffer(bitmap)||bitmap.length!==width*height*4)return;
  this.attempts.delete(id);this.attempts.set(id,{page:pin.page,epoch:pin.epoch,url:pin.url,desk:pin.desk,at});this.cache.delete(id);this.cache.set(id,{page:pin.page,epoch:pin.epoch,url:pin.url,desk:pin.desk,bitmap,width,height,bytes:bitmap.length,src:'',capturedAt:at});
  while(this.attempts.size>MAX_IMAGES)this.attempts.delete(this.attempts.keys().next().value);this.trim();
 }
 imageSource(id,entry){
  if(!entry||this.disposed||this.locked||this.browser.disposed||!this.valid(id,entry))return'';
  if(entry.src)return entry.src;
  if(!entry.bitmap)return'';
  const trace=this.diagnostic,started=trace?performance.now():0;
  try{
   if(trace)trace.jpegEncodes++;const bytes=this.fromBitmap(entry.bitmap,{width:entry.width,height:entry.height,scaleFactor:1}).toJPEG(70);
   if(!Buffer.isBuffer(bytes)||!bytes.length||bytes.length>MAX_BYTES){this.cache.delete(id);return'';}
   entry.src='data:image/jpeg;base64,'+bytes.toString('base64');entry.bytes=entry.src.length*2;delete entry.bitmap;this.trim();return entry.src;
  }catch{this.cache.delete(id);return'';}finally{if(trace)trace.jpegMs+=performance.now()-started;}
 }
 takeCaptureSlot(){
  const release=()=>{const next=this.captureWaiters.shift();if(next)next(release);else this.activeCaptures--;};
  if(this.activeCaptures<MAX_CAPTURES){this.activeCaptures++;return Promise.resolve(release);}
  if(this.captureWaiters.length>=MAX_CAPTURE_QUEUE)return Promise.resolve(null);
  return new Promise(resolve=>this.captureWaiters.push(resolve));
 }
 async captureOne(id){
  if(this.disposed||this.locked||this.browser.disposed||this.pending.has(id))return this.pending.get(id);
  const live=this.live(id);if(!live||!live.t.visible||this.bank.members[id]!==this.bank.active)return;
  const {t,wc}=live,desk=this.bank.active,generation=this.generation,epoch=t.navigationEpoch||0,url=wc.getURL?.()||t.url||'';
  const previous=this.attempts.get(id);if(previous&&this.valid(id,previous)&&this.now()-previous.at<MIN_CAPTURE_INTERVAL){if(this.diagnostic)this.diagnostic.cacheHits++;return;}
  const work=(async()=>{const release=await this.takeCaptureSlot();try{
   if(!release||this.disposed||this.locked||this.browser.disposed||generation!==this.generation||desk!==this.bank.active||!t.visible||!this.valid(id,{page:t,epoch,url,desk}))return;
   this.attempts.delete(id);this.attempts.set(id,{page:t,epoch,url,desk,at:this.now()});while(this.attempts.size>MAX_IMAGES)this.attempts.delete(this.attempts.keys().next().value);
   // A preview can finish after Nora has acquired its native hold. Never let
   // that in-flight readback wake a guest above the shell's modal surface.
   if(this.diagnostic)this.diagnostic.captures++;const image=await wc.capturePage(undefined,{stayHidden:true,stayAwake:false});
   if(this.disposed||this.locked||this.browser.disposed||generation!==this.generation||desk!==this.bank.active||!t.visible||!this.valid(id,{page:t,epoch,url,desk})||image.isEmpty?.())return;
   this.rememberImage(id,image,{page:t,epoch,url,desk});
  }catch{}finally{release?.();if(this.pending.get(id)===work)this.pending.delete(id);}})();
  this.pending.set(id,work);return work;
 }
 async capture(){
  if(this.disposed||this.locked)return;
  const ids=this.state().tabs.filter(t=>!t.internal&&this.bank.members[t.id]===this.bank.active&&this.live(t.id)?.t.visible).slice(0,12).map(t=>t.id);
  let timeout;try{await Promise.race([Promise.all(ids.map(id=>this.captureOne(id))),new Promise(resolve=>{timeout=setTimeout(resolve,250);})]);}finally{clearTimeout(timeout);}
 }
 async thumbnail(id){
  const generation=this.generation,desk=this.bank.active,live=this.live(id);
  if(this.disposed||this.locked||!live?.t.visible||this.bank.members[id]!==desk)return{src:''};
  let timeout;try{await Promise.race([this.captureOne(id),new Promise(resolve=>{timeout=setTimeout(resolve,250);})]);}finally{clearTimeout(timeout);}
  const entry=this.cache.get(id);
  return{src:!this.disposed&&!this.locked&&generation===this.generation&&desk===this.bank.active&&live.t.visible?this.imageSource(id,entry):''};
 }
 snapshot(){
  const tabs=this.state().tabs,liveIds=new Set(tabs.map(t=>t.id));for(const [id,entry]of this.cache)if(!liveIds.has(id)||!this.valid(id,entry))this.cache.delete(id);
  const described=this.bank.describe(tabs);
  return{...described,items:described.items.map(d=>{
   const desk=this.bank.items.find(x=>x.id===d.id),own=this.bank.ordered(d.id,tabs),byId=new Map(own.map(t=>[t.id,t]));
   const info=(id,includeImage=true)=>{const t=byId.get(id);if(!t)return{id:'',title:'Свободное окно',url:'',site:'',favicon:'',internal:false,lane:'main',src:'',capturedAt:0};const image=includeImage&&!this.locked&&!this.disposed&&!t.internal?this.cache.get(id):null;return{id:t.id,title:String(t.title||t.url||'Новая вкладка').slice(0,1000),url:String(t.url||'').slice(0,8192),site:site(t.url),favicon:String(t.favicon||'').slice(0,200000),internal:!!t.internal,lane:t.lane||'main',src:this.imageSource(id,image),capturedAt:image?.capturedAt||0};};
   const panes=L.leaves(desk.layout.tree).map(pane=>({pane,...info(desk.layout.slots[pane])}));
   if(desk.layout.aiOpen&&desk.layout.aiId){panes.push({pane:'ai',...info(desk.layout.aiId)});const preview=own.find(t=>t.previewOf===desk.layout.aiId);if(preview)panes.push({pane:'ai-preview',...info(preview.id)});}
   const used=new Set(panes.map(p=>p.id)),ordered=own.map(t=>{const {src,capturedAt,...rest}=info(t.id,false);return{...rest,placed:used.has(t.id)};}),extraTabs=ordered.filter(t=>!t.placed);
   return{...d,slots:{...desk.layout.slots},aiOpen:desk.layout.aiOpen,aiId:desk.layout.aiId,preview:{panes,tabs:ordered,extraTabs,capturedAt:Math.max(0,...panes.map(p=>p.capturedAt))}};
  })};
 }
}
module.exports={DesktopPreviews,MAX_IMAGES,MAX_BYTES,MAX_EDGE,MAX_CACHE_BYTES,MIN_CAPTURE_INTERVAL,MAX_CAPTURES};
