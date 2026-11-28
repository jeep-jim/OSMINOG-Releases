'use strict';

const {isDeepStrictEqual:equal}=require('node:util');
const {randomUUID,createHash}=require('node:crypto');
const {validateSyncState,maybeURL,SETTINGS}=require('./mouse-sync-schema.cjs');
const {DesktopBank}=require('./mouse-desktops.cjs');
const A=require('./mouse/appearance.js');
const Controls=require('./mouse-settings.cjs');
const L=require('./mouse/layout.js');
const clone=x=>x===undefined?undefined:structuredClone(x);
const tabID=x=>typeof x==='string'&&/^[a-f0-9-]{36}$/.test(x);
const PROJECT='trader-os-main',CACHE='mouseAccountSyncV1';
const SYNC_STORE_KEYS=['mouseDesktopsV1','quadroPreferences','browserSessions','quadroStartTabs','quadroLibrary',
 'mouseAppearance','mouseControlSettings','mouseSyncLayoutAlternatives','quadroStartPage','mouseSearch','mouseGlobalZoom'];
const SYNC_PREF_KEYS=new Set(['theme','locale','libraryWidth','settingsWidth','flashWidth','aiSites','appearance','desktopId',
 'tree','slots','pinnedPanes','active','tabOrder','aiOpen','aiWidth','aiPreviewRatio','aiId','aiSessions','mode','presetTabs','agentOpen','agentPreviewId']);

function exportWorkspace(data){
 const p=data.quadroPreferences||{},bank=new DesktopBank(data.mouseDesktopsV1,p);
 const sessions=Array.isArray(data.browserSessions?.[PROJECT])?data.browserSessions[PROJECT]:[];
 const sources=[...sessions.filter(t=>!t.provider),...(Array.isArray(data.quadroStartTabs)?data.quadroStartTabs:[]).map(t=>({id:t.id,url:'mouse://start',lane:'main'}))];
 const tabs=[],seen=new Set();
 for(const t of sources){const url=maybeURL(t.url,true);if(!tabID(t.id)||!url||seen.has(t.id))continue;seen.add(t.id);tabs.push({id:t.id,url,lane:t.lane==='side'?'side':'main'});}
 const members={},desks=new Set(bank.items.map(x=>x.id));
 for(const t of tabs)members[t.id]=desks.has(bank.members[t.id])?bank.members[t.id]:bank.active;
 const items=bank.items.map(d=>{
  const v=d.layout,own=id=>!!id&&members[id]===d.id,slots={},pinnedPanes={},aiSessions={},presetTabs={};
  for(const [pane,id]of Object.entries(v.slots))slots[pane]=own(id)?id:'';
  for(const [pane,id]of Object.entries(v.pinnedPanes||{}))if(!id||own(id))pinnedPanes[pane]=id;
  for(const [url,id]of Object.entries(v.aiSessions||{})){const safe=maybeURL(url);if(safe&&own(id))aiSessions[safe]=id;}
  for(const [mode,ids]of Object.entries(v.presetTabs||{}))presetTabs[mode]=ids.map(id=>own(id)?id:'');
  const layout={tree:L.validate(v.tree),slots,active:v.active,tabOrder:v.tabOrder.filter(own),aiOpen:v.aiOpen===true,aiWidth:v.aiWidth,aiPreviewRatio:L.previewRatio(v.aiPreviewRatio),aiId:own(v.aiId)?v.aiId:'',aiSessions,mode:v.mode};
  if(Object.keys(pinnedPanes).length)layout.pinnedPanes=pinnedPanes;if(Object.keys(presetTabs).length)layout.presetTabs=presetTabs;
  return{id:d.id,name:d.name,layout};
 });
 const bookmarks=[],bookmarkIDs=new Set();
 for(const b of data.quadroLibrary?.bookmarks||[]){const url=maybeURL(b.url);if(!url||typeof b.id!=='string'||!/^[a-zA-Z0-9_-]{1,100}$/.test(b.id)||bookmarkIDs.has(b.id))continue;bookmarkIDs.add(b.id);bookmarks.push({id:b.id,url,title:String(b.title||url).replace(/[\u0000-\u001f\u007f]/g,'').slice(0,500),at:Number.isSafeInteger(b.at)&&b.at>=0?b.at:0});}
 const aiSites=[];for(const s of Array.isArray(p.aiSites)?p.aiSites:[]){const url=maybeURL(s?.url),name=String(s?.name||'').replace(/[\u0000-\u001f\u007f]/g,'').trim().slice(0,100);if(url&&name)aiSites.push({name,url});}
 const width=(x,min,fallback)=>Math.max(min,Math.min(1600,Number(x)||fallback));
 return validateSyncState({schema:1,desktops:{active:bank.active,items,members},tabs,bookmarks,
  preferences:{theme:p.theme==='dark'?'dark':'light',locale:p.locale==='en'?'en':'ru',libraryWidth:width(p.libraryWidth,300,380),settingsWidth:width(p.settingsWidth,340,760),flashWidth:width(p.flashWidth,300,420),aiSites:aiSites.slice(0,12)},
  appearance:A.normalize(data.mouseAppearance||p.appearance),settings:Controls.normalize(data.mouseControlSettings),
  start:{background:['dusk','sea','aurora','plain'].includes(data.quadroStartPage?.background)?data.quadroStartPage.background:'dusk',showRecent:data.quadroStartPage?.showRecent!==false},
  search:{engine:require('./mouse-search.cjs').ENGINES.some(e=>e.id===data.mouseSearch?.engine)?data.mouseSearch.engine:'google'},
  zoom:Math.max(.25,Math.min(5,Number(data.mouseGlobalZoom)||1)),...(Array.isArray(data.mouseSyncLayoutAlternatives)&&data.mouseSyncLayoutAlternatives.length?{layoutAlternatives:clone(data.mouseSyncLayoutAlternatives)}:{})});
}

function importWorkspace(data,raw){
 const state=validateSyncState(raw),out=clone(data),byId=new Map((data.mouseDesktopsV1?.items||[]).map(x=>[x.id,x]));
 const items=state.desktops.items.map(d=>({...clone(d),...(equal(byId.get(d.id)?.layout,d.layout)&&byId.get(d.id)?.history?{history:clone(byId.get(d.id).history)}:{})}));
 for(const item of items){const alternatives=(state.layoutAlternatives||[]).filter(x=>x.desktopId===item.id);if(alternatives.length){item.history||={schema:1,current:{id:randomUUID(),createdAt:Date.now(),reason:'sync'},past:[],future:[]};const seen=new Set([...item.history.past,...item.history.future].map(x=>x.id));for(const alt of alternatives)if(!seen.has(alt.id))item.history.past.push({id:alt.id,createdAt:Date.now(),reason:'Другой вариант с устройства',layout:clone(alt.layout)});item.history.past=item.history.past.slice(-30);}}
 const localTabs=(data.browserSessions?.[PROJECT]||[]).filter(t=>tabID(t.id)&&(t.provider||!maybeURL(t.url,true))),localIDs=new Set(localTabs.map(t=>t.id));
 const members={...state.desktops.members},deskIDs=new Set(items.map(d=>d.id));
 // A local document, auth callback or unsupported URL never enters cloud state,
 // but receiving a theme/grid update must not delete that local tab either.
 for(const t of localTabs){const old=data.mouseDesktopsV1?.members?.[t.id];members[t.id]=deskIDs.has(old)?old:state.desktops.active;const desk=items.find(d=>d.id===members[t.id]);if(t.lane!=='side'&&!desk.layout.tabOrder.includes(t.id))desk.layout.tabOrder.push(t.id);}
 out.mouseDesktopsV1={schema:2,active:state.desktops.active,items,members};
 const current=items.find(d=>d.id===state.desktops.active);
 const localPreferences=Object.fromEntries(Object.entries(data.quadroPreferences||{}).filter(([key])=>!SYNC_PREF_KEYS.has(key)));
 out.quadroPreferences={...localPreferences,...state.preferences,...clone(current.layout),desktopId:current.id,appearance:clone(state.appearance)};
 out.browserSessions={...(out.browserSessions||{}),[PROJECT]:[...state.tabs.filter(t=>t.url!=='mouse://start'&&!localIDs.has(t.id)).map(t=>({...t})),...clone(localTabs)]};
 out.quadroStartTabs=state.tabs.filter(t=>t.url==='mouse://start').map(t=>({id:t.id}));
 // Downloads, history, captured text, credentials and files never enter state.
 // Keep all existing local stores while replacing only the approved settings.
 const localOnly=(data.quadroLibrary?.bookmarks||[]).filter(b=>!maybeURL(b.url)),localBookmarkIDs=new Set(localOnly.map(b=>b.id));
 out.quadroLibrary={...(out.quadroLibrary||{}),bookmarks:[...clone(state.bookmarks.filter(b=>!localBookmarkIDs.has(b.id))),...localOnly]};
 out.mouseAppearance=clone(state.appearance);out.mouseControlSettings={...(data.mouseControlSettings||{}),...state.settings};
 out.mouseSyncLayoutAlternatives=clone(state.layoutAlternatives||[]);
 if(state.start)out.quadroStartPage={...state.start,...(data.quadroStartPage?.background==='custom'&&state.start.background==='dusk'?{background:'custom'}:{})};
 if(state.search)out.mouseSearch={...state.search};if(state.zoom!==undefined)out.mouseGlobalZoom=state.zoom;
 return out;
}

// Apply local changes relative to the last local observation to the newest
// cloud state. Unchanged local fields must never overwrite another device.
// Conflicting content edits are retained explicitly; deletions only win when
// the opposite device has not edited the deleted item in the meantime.
function mergeValue(base,local,remote){
 if(equal(local,base))return clone(remote);if(equal(remote,base)||equal(local,remote))return clone(local);
 if(base&&local&&remote&&![base,local,remote].some(Array.isArray)&&[base,local,remote].every(x=>typeof x==='object')){
  const out={};for(const k of new Set([...Object.keys(base),...Object.keys(local),...Object.keys(remote)])){const v=mergeValue(base[k],local[k],remote[k]);if(v!==undefined)out[k]=v;}return out;
 }
 return clone(local===undefined?remote:local);
}
function mergeRows(base,local,remote,{duplicate=false,newestFirst=false}={}){
 // Preserve a single writer's array order exactly. Walking the remote IDs
 // first used to move a freshly prepended local bookmark behind older rows.
 if(equal(local,base))return clone(remote);if(equal(remote,base)||equal(local,remote))return clone(local);
 const bm=new Map((base||[]).map(x=>[x.id,x])),lm=new Map(local.map(x=>[x.id,x])),rm=new Map(remote.map(x=>[x.id,x])),out=[];
 for(const key of new Set([...remote.map(x=>x.id),...local.map(x=>x.id)])){
  const b=bm.get(key),l=lm.get(key),r=rm.get(key);if(l===undefined&&equal(r,b)||r===undefined&&equal(l,b))continue;
  if(duplicate&&b&&l&&r&&!equal(l,b)&&!equal(r,b)&&!equal(l,r)){out.push(clone(l),{...clone(r),id:randomUUID(),title:(String(r.title||'')+' · с другого устройства').slice(0,500)});continue;}
  const v=mergeValue(b,l,r);if(v!==undefined)out.push(v);
 }
 // Concurrent bookmark additions have no shared insertion order. Match the
 // native library's newest-first convention with a deterministic ID tie break
 // so both devices converge; never reorder untouched/imported collections.
 if(newestFirst)out.sort((a,b)=>b.at-a.at||(a.id<b.id?-1:a.id>b.id?1:0));return out;
}
function mergeWorkspace(base,local,remote){
 local=validateSyncState(local);if(!remote)return local;remote=validateSyncState(remote);if(!base)return remote;base=validateSyncState(base);
 const out=mergeValue(base,local,remote);
 out.bookmarks=mergeRows(base.bookmarks,local.bookmarks,remote.bookmarks,{duplicate:true,newestFirst:true});
 out.tabs=mergeRows(base.tabs,local.tabs,remote.tabs);
 out.desktops.items=mergeRows(base.desktops.items,local.desktops.items,remote.desktops.items);
 const alternatives=new Map([...(remote.layoutAlternatives||[]),...(local.layoutAlternatives||[])].map(x=>[x.id,clone(x)]));
 // Arrays such as a grid are a single coherent edit. Keep the local edited
 // layout; concurrently-created tabs from the remote device remain on that
 // desk in tabOrder rather than disappearing from the merged workspace.
 const ids=new Set(out.tabs.map(t=>t.id)),desks=new Set(out.desktops.items.map(d=>d.id));
 if(!desks.has(out.desktops.active))out.desktops.active=out.desktops.items[0].id;
 out.desktops.members=Object.fromEntries(Object.entries(out.desktops.members||{}).filter(([id,desk])=>ids.has(id)&&desks.has(desk)));
 for(const t of out.tabs)if(!out.desktops.members[t.id])out.desktops.members[t.id]=out.desktops.active;
 for(const d of out.desktops.items){
  // A split-tree is indivisible; recursively merging branches can create
  // duplicate panes. Select one full layout and preserve the other local
  // history on disk when it has not changed.
  const b=base.desktops.items.find(x=>x.id===d.id),l=local.desktops.items.find(x=>x.id===d.id),r=remote.desktops.items.find(x=>x.id===d.id);
  if(b&&l&&r&&!equal(l.layout,b.layout)&&!equal(r.layout,b.layout)&&!equal(l.layout,r.layout)){const id='sync-'+createHash('sha256').update(d.id+JSON.stringify(r.layout)).digest('hex').slice(0,32);alternatives.set(id,{id,desktopId:d.id,layout:clone(r.layout)});}
  d.layout=clone(equal(l?.layout,b?.layout)?r?.layout||l?.layout:l?.layout||r?.layout);
  const v=d.layout,own=id=>out.desktops.members[id]===d.id;
  v.slots=Object.fromEntries(Object.entries(v.slots).map(([p,id])=>[p,own(id)?id:'']));
  v.tabOrder=[...new Set([...v.tabOrder.filter(own),...out.tabs.filter(t=>own(t.id)&&t.lane==='main').map(t=>t.id)])];
  if(v.pinnedPanes)v.pinnedPanes=Object.fromEntries(Object.entries(v.pinnedPanes).filter(([p,id])=>!id||own(id)&&v.slots[p]===id));
  if(!own(v.aiId))v.aiId='';v.aiSessions=Object.fromEntries(Object.entries(v.aiSessions).filter(([,id])=>own(id)));
  if(v.presetTabs)for(const key of Object.keys(v.presetTabs))v.presetTabs[key]=v.presetTabs[key].map(id=>own(id)?id:'');
 }
 if(alternatives.size)out.layoutAlternatives=[...alternatives.values()].filter(x=>desks.has(x.desktopId)).slice(-30);
 return validateSyncState(out);
}

class MouseConfigSync{
 constructor({store,account,onState=()=>{},beforeRead=async()=>{},canSync=()=>true,now=Date.now}){Object.assign(this,{store,account,onState,beforeRead,canSync,now});this.timer=null;this.work=null;this.controller=null;this.generation=0;this.closed=false;this.phase='idle';this.lastSyncedAt=null;this.error='';this.pendingRemote=false;}
 state(){return{phase:this.phase,lastSyncedAt:this.lastSyncedAt,error:this.error,pendingRemote:this.pendingRemote};}
 emit(){this.onState(this.state());}
 async tick({apply=false}={}){
  if(this.work)return this.work;if(this.closed||!this.canSync())return this.state();
  const identity=this.account.snapshot();if(!identity)return this.state();
  const accountId=identity.accountId,accountEpoch=this.account.epoch,generation=this.generation,controller=new AbortController();this.controller=controller;
  const current=()=>!this.closed&&generation===this.generation&&!controller.signal.aborted&&this.canSync()&&this.account.snapshot()?.accountId===accountId&&this.account.epoch===accountEpoch;
  const guard=()=>{if(!current())throw Object.assign(Error('Account changed'),{code:'SYNC_CANCELLED'});};
  const request=async(method,route,body)=>{guard();const value=await this.account.request(method,route,body,{expectedAccountId:accountId,signal:controller.signal});guard();return value;};
  const revision=value=>{if(!value||!Number.isSafeInteger(value.revision)||value.revision<0||value.updatedAt!==undefined&&value.updatedAt!==null&&(!Number.isSafeInteger(value.updatedAt)||value.updatedAt<0))throw Object.assign(Error('Invalid sync revision'),{code:'SYNC_FORMAT'});return value;};
  this.work=(async()=>{
   this.phase='syncing';this.error='';this.emit();guard();await this.beforeRead();guard();
   const data=await this.store.get(null);guard();const local=exportWorkspace(data),cache=data[CACHE];
   if(cache&&cache.accountId!==accountId)throw Object.assign(Error('Profile belongs to another account'),{code:'SYNC_ACCOUNT_MISMATCH'});
   const baseline=cache?.local?validateSyncState(cache.local):exportWorkspace({});
   let result;const stamp=revision(await request('GET','/sync/revision'));
   if(cache&&Number.isSafeInteger(cache.revision)&&cache.revision===stamp.revision&&Object.hasOwn(cache,'cloud'))result={...stamp,state:cache.cloud};
   else result=revision(await request('GET','/sync'));
   const remote=result.state?validateSyncState(result.state):null;
   // An unseen account profile starts from an empty logical workspace. A new
   // login seed is empty too, so cloud settings win; a new registration or an
   // offline-edited account retains its actual local additions on first sync.
   const merged=remote?mergeWorkspace(baseline,local,remote):local;
   let nextRevision=result.revision,cloud=remote;
   if(!remote||!equal(merged,remote)){
    try{const written=revision(await request('PUT','/sync',{revision:nextRevision,state:merged}));nextRevision=written.revision;cloud=validateSyncState(written.state||merged);}
    catch(error){if(error.status===409){this.phase='retry';this.emit();return this.state();}throw error;}
   }
   // Only startup/login imports into a live browser profile. Polling never
   // closes a page with unfinished input just because another device changed.
   guard();let observed=local;const syncedAt=this.now();
   if(!apply&&cache?.revision===nextRevision&&equal(cache.local,local)&&equal(cache.cloud,cloud)){
    this.pendingRemote=!equal(cloud,local);this.phase=this.pendingRemote?'pending':'synced';this.lastSyncedAt=syncedAt;this.emit();return this.state();
   }
   const changesFor=fresh=>{
    guard();if(fresh[CACHE]&&fresh[CACHE].accountId!==accountId)throw Object.assign(Error('Profile belongs to another account'),{code:'SYNC_ACCOUNT_MISMATCH'});
    const freshLocal=exportWorkspace(fresh);
    const imported=apply?mergeWorkspace(local,freshLocal,cloud):freshLocal;observed=imported;
    const all=apply?importWorkspace(fresh,imported):{};
    const changes=Object.fromEntries(SYNC_STORE_KEYS.filter(key=>Object.hasOwn(all,key)).map(key=>[key,all[key]]));
    changes[CACHE]={schema:1,accountId,revision:nextRevision,local:apply?cloud:local,cloud,lastSyncedAt:syncedAt};
    return changes;
   };
   if(typeof this.store.mutate==='function')await this.store.mutate(fresh=>{const changes=changesFor(fresh),events={};for(const [key,value]of Object.entries(changes)){events[key]={oldValue:fresh[key],newValue:value};fresh[key]=value;}return events;});
   else{const fresh=await this.store.get(null);guard();await this.store.set(changesFor(fresh));}
   guard();this.pendingRemote=!equal(cloud,observed);this.phase=this.pendingRemote?'pending':'synced';this.lastSyncedAt=syncedAt;this.emit();return this.state();
  })().catch(error=>{if(!current()){if(generation===this.generation&&!this.closed){this.phase='idle';this.error='';this.emit();}return this.state();}this.phase='error';this.error=error.code==='SYNC_FORMAT'?'Рабочее пространство превышает лимит синхронизации или содержит недопустимое поле.':'Синхронизация временно недоступна. Локальные настройки сохранены.';this.emit();return this.state();}).finally(()=>{if(this.controller===controller)this.controller=null;this.work=null;});return this.work;
 }
 start(){if(this.timer)return;this.closed=false;this.generation++;this.timer=setInterval(()=>void this.tick(),30000);this.timer.unref?.();}
 async flush(){return this.tick();}
 async stop(){this.closed=true;this.generation++;this.controller?.abort();clearInterval(this.timer);this.timer=null;this.phase='idle';this.emit();await this.work;}
}
module.exports={exportWorkspace,importWorkspace,mergeWorkspace,MouseConfigSync,CACHE,PROJECT};
