'use strict';
// Shared declarative presets. A preset opens ordinary web pages; it does not
// connect accounts or change permissions.
(function(root){
 const pane=n=>({id:'p'+n}),split=(axis,ratio,a,b)=>({axis,ratio,a,b});
 const col=(...n)=>n.length===1?pane(n[0]):split('y',1/n.length,pane(n[0]),col(...n.slice(1)));
 const columns=(...trees)=>trees.length===1?trees[0]:split('x',1/trees.length,trees[0],columns(...trees.slice(1)));
 const modes=[
  {id:'trader',name:'Трейдер',hint:'Большой график слева · календарь, скринер и крипторынок справа',icon:'M3 17l5-6 4 3 8-10 M15 4h5v5 M4 20h16',tree:split('x',.66,pane(1),col(2,3,4)),sites:['https://www.tradingview.com/chart/','https://www.investing.com/economic-calendar/','https://finviz.com/','https://coinmarketcap.com/']},
  {id:'support',name:'Мессенджеры и поддержка',hint:'4 веб-мессенджера слева · Google Карты справа',icon:'M4 4h16v11H9l-5 5V4 M8 8h8 M8 11h5',tree:split('x',.64,split('x',.5,col(1,2),col(3,4)),pane(5)),sites:['https://web.telegram.org/k/','https://web.whatsapp.com/','https://web.max.ru/','https://web.wechat.com/','https://www.google.com/maps/']},
  {id:'design',name:'Разработка и дизайн',hint:'Макет, репозиторий, документация и поиск',icon:'M8 5L2 12l6 7 M16 5l6 7-6 7 M14 3l-4 18',tree:split('x',.64,split('y',.66,pane(1),split('x',.5,pane(2),pane(3))),col(4,5)),sites:['https://www.figma.com/','https://github.com/','https://developer.mozilla.org/','https://stackoverflow.com/','https://www.google.com/']},
  // Column-major order matches the supplied six-column, two-row workspace.
  {id:'content',name:'Контент и соцсети',hint:'12 сайтов · 6 колонок и 2 ряда',icon:'M4 5h16v14H4z M9 8l6 4-6 4V8 M2 2h5 M17 22h5',tree:columns(col(1,2),col(3,4),col(5,6),col(7,8),col(9,10),col(11,12)),sites:['https://www.instagram.com/explore/','https://www.twitch.tv/','https://www.tiktok.com/explore','https://www.youtube.com/','https://x.com/','https://www.facebook.com/','https://www.reddit.com/','https://www.threads.com/','https://web.telegram.org/k/','https://web.wechat.com/','https://web.whatsapp.com/','https://web.max.ru/']},
 ];
 function get(id){const m=modes.find(x=>x.id===id);if(!m)throw Error('Неизвестный режим рабочего стола');return JSON.parse(JSON.stringify(m));}
 const leaves=t=>t.id?[t.id]:[...leaves(t.a),...leaves(t.b)];
 function order(tabs,previous){
  const main=tabs.filter(t=>t.lane!=='side'),valid=new Set(main.map(t=>t.id)),seen=new Set();
  return[...Object.values(previous.slots||{}),...(Array.isArray(previous.tabOrder)?previous.tabOrder:[]),...main.map(t=>t.id)].filter(id=>valid.has(id)&&!seen.has(id)&&seen.add(id));
 }
 function urlKey(value){
  if(value==='mouse://start')return value;
  try{const url=new URL(value);if(!['http:','https:'].includes(url.protocol)||url.username||url.password)return'';url.hash='';return url.href.replace(/\/$/,'');}catch{return'';}
 }
 function selections(spec,tabs,previous){
  const pages=new Map(tabs.filter(t=>t.lane!=='side'&&!t.documentId).map(t=>[t.id,t])),ordered=order(tabs,previous),used=new Set(),remembered=previous.presetTabs?.[spec.id];
  return spec.sites.map((url,index)=>{
   const saved=Array.isArray(remembered)?remembered[index]:'';
   const reusable=candidate=>pages.has(candidate)&&!used.has(candidate)&&!pages.get(candidate).internal;
   let id=reusable(saved)?saved:'';
   // Shared services (for example Telegram in Support and Content) keep their
   // existing identity even after an authentication redirect changed the URL.
   if(!id)for(const mode of modes){
    const saved=previous.presetTabs?.[mode.id];if(!Array.isArray(saved))continue;
    const index=mode.sites.findIndex(site=>urlKey(site)===urlKey(url));if(index>=0&&reusable(saved[index])){id=saved[index];break;}
   }
   if(!id)id=ordered.find(candidate=>reusable(candidate)&&urlKey(pages.get(candidate).url)===urlKey(url))||'';
   if(id)used.add(id);return id;
  });
 }
 function arranged(id,tabs,previous={},options={}){
  const spec=get(id),ordered=order(tabs,previous),valid=new Set(tabs.filter(t=>t.lane!=='side'&&!t.documentId).map(t=>t.id)),selected=options.selectedIds===undefined?selections(spec,tabs,previous):options.selectedIds;
  if(!Array.isArray(selected)||selected.length!==spec.sites.length)throw Error('Неполный набор страниц режима');
  const used=new Set();for(const tab of selected){if(tab!==''&&(!valid.has(tab)||used.has(tab)||tabs.find(page=>page.id===tab)?.internal))throw Error('Страница режима недоступна');if(tab)used.add(tab);}
  const ids=leaves(spec.tree),slots=Object.fromEntries(ids.map((pane,index)=>[pane,selected[index]||''])),presetTabs={};
  for(const mode of modes){const saved=previous.presetTabs?.[mode.id];if(Array.isArray(saved))presetTabs[mode.id]=mode.sites.map((_,index)=>valid.has(saved[index])?saved[index]:'');}
  presetTabs[id]=[...selected];
  const active=ids.find(pane=>previous.slots?.[previous.active]&&slots[pane]===previous.slots[previous.active])||ids[0];
  // Older profiles may still carry the removed panel keys at this boundary.
  const {agentOpen,agentPreviewId,...kept}=previous;
  return{...kept,mode:id,tree:spec.tree,slots,active,tabOrder:[...new Set([...selected.filter(Boolean),...ordered])],aiOpen:false,presetTabs};
 }
 function plan(id,tabs,previous={}){
  const spec=get(id),selectedIds=selections(spec,tabs,previous),sites=spec.sites.map((url,index)=>({index,url,id:selectedIds[index]}));
  return{sites,selectedIds,missing:sites.filter(site=>!site.id).map(({index,url})=>({index,url})),layout:arranged(id,tabs,previous,{selectedIds})};
 }
 const api={modes,get,plan,arranged};if(typeof module==='object'&&module.exports)module.exports=api;else root.MouseModes=api;
})(globalThis);
