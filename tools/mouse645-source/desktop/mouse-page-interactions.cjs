'use strict';

// Serialized into the isolated preload. There is no page-visible bridge and no
// polling, DOM observer, network call or persisted gesture state.
function createPageInteractionTools(){
 const MIME='application/x-mouse-pane',MAX_URL=8192;
 const CONTROLS=new Set(['INPUT','TEXTAREA','BUTTON','SELECT','OPTION','LABEL','FORM','FIELDSET','SUMMARY','DETAILS']);
 const MEDIA=new Set(['IMG','PICTURE','VIDEO','AUDIO','CANVAS','SVG','OBJECT','EMBED','IFRAME','MAP','AREA','PROGRESS','METER']);
 const ROLES=new Set(['button','checkbox','radio','slider','spinbutton','tab','textbox','combobox','listbox','menu','menubar','menuitem','menuitemcheckbox','menuitemradio','scrollbar','switch','tree','treeitem','option','grid','gridcell']);
 function webURL(value,base){
  if(typeof value!=='string'||!value.trim()||value.length>MAX_URL||/[\x00-\x1f\x7f\\]/.test(value))return '';
  try{const url=new URL(value,base);return['http:','https:'].includes(url.protocol)&&!url.username&&!url.password?url.href:'';}catch{return '';}
 }
 // A normal click within the current site must remain in its live WebContents.
 // Match exact hosts and their parent/child subdomains; never compare only a
 // final public suffix (for example two unrelated .co.uk hosts).
 function sameSite(target,current){
  try{
   const a=new URL(target).hostname.replace(/\.$/,'').toLowerCase(),b=new URL(current).hostname.replace(/\.$/,'').toLowerCase();
   if(a===b)return true;
   if(!a.includes('.')||!b.includes('.')||/^\d+(?:\.\d+){3}$/.test(a)||/^\d+(?:\.\d+){3}$/.test(b))return false;
   return a.endsWith('.'+b)||b.endsWith('.'+a);
  }catch{return false;}
 }
 function eventPath(event){
  try{const path=event.composedPath?.();if(Array.isArray(path)&&path.length)return path.slice(0,80);}catch{}
  const path=[];for(let node=event.target;node&&path.length<80;node=node.parentElement||node.host)path.push(node);return path;
 }
 const element=node=>node&&node.nodeType===1;
 function interactive(node,{anchor=false,ownDrag=null}={}){
  if(!element(node))return false;
  const tag=String(node.tagName||'').toUpperCase(),roles=String(node.getAttribute?.('role')||'').toLowerCase().split(/\s+/);
  if(CONTROLS.has(tag)||node.isContentEditable||roles.some(role=>ROLES.has(role)))return true;
  if(!anchor&&['onclick','onmousedown','onpointerdown'].some(name=>node.hasAttribute?.(name)||typeof node[name]==='function'))return true;
  if(!anchor&&(tag==='A'||MEDIA.has(tag)||tag.includes('-')||roles.includes('link')||node.tabIndex>=0))return true;
  if(!anchor&&node!==ownDrag&&(node.draggable===true||node.getAttribute?.('draggable')==='true'))return true;
  if(!anchor&&node.hasAttribute?.('aria-haspopup')&&node.getAttribute('aria-haspopup')!=='false')return true;
  return false;
 }
 function ordinary(event){return event?.isTrusted===true&&!event.defaultPrevented&&event.button===0&&!event.ctrlKey&&!event.metaKey&&!event.shiftKey&&!event.altKey;}
 function linkURL(event,document,window){
  if(!ordinary(event))return '';
  const path=eventPath(event),anchor=path.find(node=>element(node)&&String(node.tagName).toUpperCase()==='A');
  if(!anchor||anchor.hasAttribute?.('download')||path.some(node=>interactive(node,{anchor:true})))return '';
  const raw=anchor.getAttribute?.('href');if(typeof raw!=='string'||!raw.trim())return '';
  const current=window.location?.href||document.URL||'',url=webURL(raw,document.baseURI||current);if(!url)return '';
  if(sameSite(url,current))return '';
  return url;
 }
 const inside=(x,y,rect)=>rect&&Number.isFinite(rect.left)&&Number.isFinite(rect.top)&&Number.isFinite(rect.right)&&Number.isFinite(rect.bottom)&&x>=rect.left&&x<rect.right&&y>=rect.top&&y<rect.bottom;
 function textAtPoint(document,target,x,y){
  let node,offset;
  try{const caret=document.caretPositionFromPoint?.(x,y);if(caret){node=caret.offsetNode;offset=caret.offset;}
   if(!node){const range=document.caretRangeFromPoint?.(x,y);if(range){node=range.startContainer;offset=range.startOffset;}}
   if(node?.nodeType===3&&node.length&&typeof document.createRange==='function'){
    const range=document.createRange(),start=Math.max(0,Math.min(node.length-1,Number(offset)||0)-1),end=Math.min(node.length,start+3);range.setStart(node,start);range.setEnd(node,end);
    const hit=[...range.getClientRects()].some(rect=>inside(x,y,rect));range.detach?.();return hit;
   }
   if(node)return false;
  }catch{return true;}
  // Without native caret geometry, a nonempty target is not evidence of free
  // space. Empty backgrounds remain draggable; text selection stays intact.
  return!!String(target?.textContent||'').trim();
 }
 function blankTarget(event,{document,window,ownDrag=null}){
  if(!ordinary(event)||event.pointerType&&event.pointerType!=='mouse'||event.buttons!==undefined&&event.buttons!==1)return null;
  const x=event.clientX,y=event.clientY;if(!Number.isFinite(x)||!Number.isFinite(y)||x<0||y<0||x>=window.innerWidth||y>=window.innerHeight)return null;
  const path=eventPath(event),target=path.find(element);if(!target||target.isConnected===false||path.some(node=>interactive(node,{ownDrag})))return null;
  try{
   const selection=window.getSelection?.();if(selection?.isCollapsed===false||String(selection||''))return null;
   for(const node of path.filter(element)){
    const style=window.getComputedStyle?.(node),cursor=String(style?.cursor||'auto');
    if(!['auto','default',''].includes(cursor)||style?.touchAction==='none')return null;
   }
   if(textAtPoint(document,target,x,y))return null;
  }catch{return null;}
  return target;
 }
 function nonce(crypto){
  if(typeof crypto?.randomUUID==='function')return crypto.randomUUID();
  if(typeof crypto?.getRandomValues!=='function')throw Error('Cryptographic randomness is unavailable');
  const bytes=crypto.getRandomValues(new Uint8Array(16));bytes[6]=(bytes[6]&15)|64;bytes[8]=(bytes[8]&63)|128;
  const hex=[...bytes].map(byte=>byte.toString(16).padStart(2,'0')).join('');return hex.slice(0,8)+'-'+hex.slice(8,12)+'-'+hex.slice(12,16)+'-'+hex.slice(16,20)+'-'+hex.slice(20);
 }
 function listen({document,window,send}){
  let candidate=null,active=null,disposed=false;
  const subscriptions=[],on=(target,name,fn)=>{target.addEventListener(name,fn,true);subscriptions.push([target,name,fn]);};
  function restore(){const saved=candidate;candidate=null;if(!saved)return;try{if(saved.node.getAttribute('draggable')==='true'){if(saved.attribute===null)saved.node.removeAttribute('draggable');else saved.node.setAttribute('draggable',saved.attribute);}}catch{}}
  function finish(phase){const drag=active;active=null;restore();drag?.image?.remove?.();if(drag)try{send('mouse:page-arrange-source',{phase,token:drag.token});}catch{}}
  const click=event=>{if(disposed||active)return;const url=linkURL(event,document,window);if(!url)return;event.preventDefault();event.stopImmediatePropagation();try{send('mouse:page-link',{url});}catch{}};
  const down=event=>{
   if(disposed||active)return;restore();const node=blankTarget(event,{document,window});if(!node)return;
   candidate={node,attribute:node.getAttribute('draggable')};try{node.setAttribute('draggable','true');}catch{candidate=null;}
  };
  const dragstart=event=>{
   if(disposed||active||!candidate||event.isTrusted!==true)return;
   const saved=candidate,target=eventPath(event).find(element);
   if(event.defaultPrevented||target!==saved.node||!event.dataTransfer||blankTarget(event,{document,window,ownDrag:saved.node})!==saved.node){if(target===saved.node)event.preventDefault();restore();return;}
   try{
    const token=nonce(window.crypto),image=document.createElement('canvas');image.width=1;image.height=1;image.setAttribute('aria-hidden','true');image.style.cssText='position:fixed;left:0;top:0;width:1px;height:1px;pointer-events:none;opacity:0';document.documentElement.append(image);
    active={token,image};event.dataTransfer.clearData();event.dataTransfer.setData(MIME,token);event.dataTransfer.effectAllowed='move';event.dataTransfer.setDragImage(image,0,0);
    event.stopImmediatePropagation();send('mouse:page-arrange-source',{phase:'begin',token,x:event.clientX,y:event.clientY});
   }catch{event.preventDefault();finish('cancel');}
  };
  const end=event=>{if(event.isTrusted===true)finish('end');};
  // Chromium emits pointercancel when a native HTML drag takes over. Restore
  // our temporary attribute, but keep the nonce alive until dragend/drop.
  on(window,'click',click);on(window,'pointerdown',down);on(window,'pointerup',restore);on(window,'pointercancel',restore);on(window,'dragstart',dragstart);on(window,'dragend',end);on(window,'pagehide',()=>finish('cancel'));
  return{dispose(){if(disposed)return;disposed=true;finish('cancel');for(const [target,name,fn]of subscriptions)target.removeEventListener(name,fn,true);}};
 }
 return{MIME,webURL,sameSite,eventPath,linkURL,textAtPoint,blankTarget,nonce,listen};
}
function bundlePagePreload(source){return"'use strict';\nconst MousePageInteractions=("+createPageInteractionTools.toString()+")();\n"+source;}
module.exports={createPageInteractionTools,bundlePagePreload};
