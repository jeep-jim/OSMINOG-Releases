'use strict';
(function(root){
 const LIMIT=12,clamp=(n,a,b)=>Math.min(b,Math.max(a,n));
 function leaves(t){return t.id?[t.id]:[...leaves(t.a),...leaves(t.b)]}
 function preset(count=1){
  const n=clamp(Math.floor(Number(count)||1),1,LIMIT);let next=0;
  const column=k=>k===1?{id:'p'+(++next)}:{axis:'y',ratio:1/k,a:{id:'p'+(++next)},b:column(k-1)};
  const cols=n<=3?n:Math.ceil(Math.sqrt(n));
  function columns(left,c){const rows=Math.ceil(left/c);return c===1?column(left):{axis:'x',ratio:1/c,a:column(rows),b:columns(left-rows,c-1)}}
  return columns(n,cols);
 }
 function validate(value){
  let nodes=0;const ids=new Set();
  function read(t){if(!t||typeof t!=='object'||++nodes>LIMIT*2-1)throw Error('Invalid layout');if(typeof t.id==='string'){if(!/^p[0-9]{1,8}$/.test(t.id)||ids.has(t.id))throw Error('Invalid pane');ids.add(t.id);return{id:t.id}}if(!['x','y'].includes(t.axis)||!Number.isFinite(t.ratio))throw Error('Invalid split');return{axis:t.axis,ratio:clamp(t.ratio,.08,.92),a:read(t.a),b:read(t.b)}}
  const result=read(value);if(!ids.size||ids.size>LIMIT)throw Error('Too many panes');return result;
 }
 function at(tree,path){let t=tree;for(const key of path){if(!['a','b'].includes(key)||t.id)throw Error('Invalid split path');t=t[key]}return t}
 function ratio(tree,path,value){const t=at(tree,path);if(t.id||!Number.isFinite(value))throw Error('Invalid ratio');t.ratio=clamp(value,.08,.92);return tree}
 function split(tree,id,axis){
  if(!['x','y'].includes(axis))throw Error('Invalid split axis');const all=leaves(tree);if(all.length>=LIMIT)throw Error('Максимум 12 окон');if(!all.includes(id))throw Error('Окно не найдено');
  const newId='p'+(Math.max(...all.map(x=>Number(x.slice(1))))+1);
  function visit(t){return t.id?(t.id===id?{axis,ratio:.5,a:{id},b:{id:newId}}:t):{...t,a:visit(t.a),b:visit(t.b)}}
  return{tree:visit(tree),id:newId};
 }
 function remove(tree,id){if(tree.id)return tree.id===id?null:tree;const a=remove(tree.a,id),b=remove(tree.b,id);return a&&b?{...tree,a,b}:a||b}
 // A deliberate drop changes placement. Temporary single-page viewing never
 // calls this function. Validate a complete candidate before touching a model.
 function place(value,tabId,pane,edge=''){
  if(typeof tabId!=='string'||!tabId||tabId.length>100||!['','left','right','top','bottom'].includes(edge))throw Error('Некорректное размещение вкладки');
  let tree=validate(value.tree);const all=leaves(tree),slots={...value.slots},source=all.find(id=>slots[id]===tabId);
  if(!all.includes(pane))throw Error('Окно больше недоступно');
  if(source===pane)return{tree,slots,active:pane};
  const locked=pins(value);if(Object.hasOwn(locked,pane)||source&&Object.hasOwn(locked,source))throw Error('Сначала открепите окно, чтобы переместить вкладку');
  if(!edge){if(source)slots[source]=slots[pane]||'';slots[pane]=tabId;const next={tree,slots,active:pane};assertPins(value,next);return next;}
  let inserted=source;
  if(source){tree=remove(tree,source);delete slots[source];}
  else{if(all.length>=LIMIT)throw Error('Максимум 12 окон. Перетащите вкладку в существующее окно.');inserted='p'+(Math.max(...all.map(id=>Number(id.slice(1))))+1);}
  const axis=['left','right'].includes(edge)?'x':'y',before=['left','top'].includes(edge);
  function visit(node){if(node.id)return node.id===pane?{axis,ratio:.5,a:{id:before?inserted:pane},b:{id:before?pane:inserted}}:node;return{...node,a:visit(node.a),b:visit(node.b)};}
  tree=visit(tree);slots[inserted]=tabId;const next={tree:validate(tree),slots,active:inserted};assertPins(value,next);return next;
 }
 function minimum(tree,axis,gap=6){if(tree.id)return axis==='x'?140:100;return tree.axis===axis?minimum(tree.a,axis,gap)+minimum(tree.b,axis,gap)+gap:Math.max(minimum(tree.a,axis,gap),minimum(tree.b,axis,gap))}
 // Native WebContentsView bounds use integer device-independent pixels. Give
 // the DOM the same partition before native placement instead of rounding
 // each page independently after fractional flex layout. Ratios stay intact.
 function pixelLayout(tree,width,height,gap=6){
  if(![width,height,gap].every(Number.isFinite)||width<0||height<0||gap<0)throw Error('Invalid pixel layout');
  const branches=[],panes=[],seam=Math.round(gap);
  function visit(node,x,y,w,h,path){
   if(node.id){panes.push({id:node.id,x,y,width:w,height:h});return;}
   const size=node.axis==='x'?w:h,space=Math.min(size,seam),available=size-space,a=Math.round(available*clamp(node.ratio,.08,.92)),b=available-a;
   branches.push({path,axis:node.axis,a,b,gap:space});
   if(node.axis==='x'){visit(node.a,x,y,a,h,path+'a');visit(node.b,x+a+space,y,b,h,path+'b');}
   else{visit(node.a,x,y,w,a,path+'a');visit(node.b,x,y+a+space,w,b,path+'b');}
  }
  visit(tree,0,0,Math.round(width),Math.round(height),'');return{branches,panes};
 }
 function previewRatio(value){return Number.isFinite(value)?clamp(value,.1,.9):.5;}
 function currentPreset(tree){
  if(!tree)return null;const count=leaves(tree).length;if(![1,2,3,4,6,8,9,12].includes(count))return null;
  const expected=preset(count);if(count===2&&tree.axis==='y')expected.axis='y';
  const same=(a,b)=>a?.id?!!b?.id:!!a&&!!b&&!b.id&&a.axis===b.axis&&Math.abs(a.ratio-b.ratio)<1e-8&&same(a.a,b.a)&&same(a.b,b.b);
  return same(tree,expected)?{count,...(count===2?{axis:tree.axis}:{})}:null;
 }
 // Pins are optional metadata on one desktop. A pin keeps both its live tab
 // identity and every ancestor split; free sibling subtrees remain editable.
 function pins(value){
  const result={},all=new Set(value?.tree?leaves(value.tree):[]),saved=value?.pinnedPanes;
  if(saved&&typeof saved==='object'&&!Array.isArray(saved))for(const id of all)if(Object.hasOwn(saved,id)&&typeof saved[id]==='string'&&saved[id].length<=100&&saved[id]===(value.slots?.[id]||''))result[id]=saved[id];
  return result;
 }
 function pinPath(tree,id,path=[]){if(tree.id)return tree.id===id?path:null;return pinPath(tree.a,id,[...path,[tree.axis,tree.ratio,'a']])||pinPath(tree.b,id,[...path,[tree.axis,tree.ratio,'b']]);}
 function preservesPins(before,after){
  for(const [id,tab]of Object.entries(pins(before))){const path=after?.tree&&pinPath(after.tree,id);if(!path||tab!==(after.slots?.[id]||'')||JSON.stringify(path)!==JSON.stringify(pinPath(before.tree,id)))return false;}return true;
 }
 function assertPins(before,after){if(!preservesPins(before,after))throw Error('Сначала открепите окно: его вкладка, размер и положение закреплены.');}
 function resizeLocked(value,path){const node=at(value.tree,path),locked=pins(value);return leaves(node).some(id=>Object.hasOwn(locked,id));}
 const api={LIMIT,clamp,leaves,preset,validate,at,ratio,split,remove,place,minimum,pixelLayout,previewRatio,currentPreset,pins,preservesPins,assertPins,resizeLocked};if(typeof module==='object'&&module.exports)module.exports=api;else root.MouseLayout=Object.freeze(api);
})(globalThis);
