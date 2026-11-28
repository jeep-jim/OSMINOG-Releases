'use strict';
(function(root){
 // A native page can have a larger viewport than its visible clip. Preserve
 // that viewport when drawing; cropping must never stretch its pixels. The
 // host supplies the same bottom-corner policy as the native composition.
 function layerGeometry(layer){
  const keys=['x','y','width','height'],bounds=Object.fromEntries(keys.map(key=>[key,layer?.[key]]));
  if(!keys.every(key=>Number.isFinite(bounds[key]))||bounds.width<=0||bounds.height<=0)throw Error('Invalid capture layer bounds');
  const requested=layer.clip||bounds;
  if(!keys.every(key=>Number.isFinite(requested[key]))||requested.width<=0||requested.height<=0)throw Error('Invalid capture layer clip');
  const x=Math.max(bounds.x,requested.x),y=Math.max(bounds.y,requested.y),right=Math.min(bounds.x+bounds.width,requested.x+requested.width),bottom=Math.min(bounds.y+bounds.height,requested.y+requested.height);
  if(right<=x||bottom<=y)return null;
  const clip={x,y,width:right-x,height:bottom-y},roundBottom=layer.roundBottom===12&&bottom===bounds.y+bounds.height?12:0;
  return{bounds,clip,...(layer.roundTop===12?{roundTop:y===bounds.y?12:0}:{}),roundBottom};
 }
 function drawLayer(ctx,image,layer,scaleX=1,scaleY=1){
  if(![scaleX,scaleY].every(value=>Number.isFinite(value)&&value>0))throw Error('Invalid capture image scale');
  const geometry=layerGeometry(layer);if(!geometry)return false;
  const {bounds:b,clip:c,roundBottom:r,roundTop:top=0}=geometry;
  ctx.save();try{ctx.scale(scaleX,scaleY);ctx.beginPath();ctx.roundRect(c.x,c.y,c.width,c.height,[top,top,r,r]);ctx.clip();ctx.drawImage(image,b.x,b.y,b.width,b.height);}finally{ctx.restore();}
  return true;
 }
 function rect(a,b,w,h){const clamp=(n,max)=>Math.max(0,Math.min(max,n));const x=clamp(Math.min(a.x,b.x),w),y=clamp(Math.min(a.y,b.y),h);return{x:Math.floor(x),y:Math.floor(y),width:Math.max(0,Math.floor(clamp(Math.max(a.x,b.x),w)-x)),height:Math.max(0,Math.floor(clamp(Math.max(a.y,b.y),h)-y))}}
 function draw(ctx,op){
  ctx.save();ctx.strokeStyle=op.color;ctx.fillStyle=op.color;ctx.lineWidth=op.width;ctx.lineCap='round';ctx.lineJoin='round';
  const a=op.points[0],b=op.points[op.points.length-1];ctx.beginPath();
  if(op.tool==='text'){ctx.font=`${op.font||24}px -apple-system,Arial,sans-serif`;ctx.textBaseline='top';String(op.text||'').split('\n').slice(0,20).forEach((s,i)=>ctx.fillText(s.slice(0,200),a.x,a.y+i*(op.font||24)*1.2));}
  else if(op.tool==='rect')ctx.strokeRect(a.x,a.y,b.x-a.x,b.y-a.y);
  else if(op.tool==='ellipse'){ctx.ellipse((a.x+b.x)/2,(a.y+b.y)/2,Math.abs(b.x-a.x)/2,Math.abs(b.y-a.y)/2,0,0,Math.PI*2);ctx.stroke()}
  else{
   if(op.tool==='marker'){ctx.globalAlpha=.3;ctx.lineWidth=op.width*4;ctx.lineCap='square'}
   ctx.moveTo(a.x,a.y);for(const p of op.points)ctx.lineTo(p.x,p.y);ctx.stroke();
   if(op.tool==='arrow'){const angle=Math.atan2(b.y-a.y,b.x-a.x),len=Math.max(12,op.width*4);ctx.beginPath();ctx.moveTo(b.x-len*Math.cos(angle-.45),b.y-len*Math.sin(angle-.45));ctx.lineTo(b.x,b.y);ctx.lineTo(b.x-len*Math.cos(angle+.45),b.y-len*Math.sin(angle+.45));ctx.stroke()}
  }
  ctx.restore();
 }

 function bounds(op,measure){
  if(!op?.points?.length)return null;
  const pad=Math.max(3,(op.width||1)*(op.tool==='marker'?2:1));
  if(op.tool==='text'){
   const font=op.font||24,lines=String(op.text||'').split('\n').slice(0,20),width=Math.max(8,...lines.map(s=>measure?measure(s.slice(0,200),font):s.length*font*.65));
   return{x:op.points[0].x-pad,y:op.points[0].y-pad,width:width+pad*2,height:lines.length*font*1.2+pad*2};
  }
  const xs=op.points.map(p=>p.x),ys=op.points.map(p=>p.y);
  return{x:Math.min(...xs)-pad,y:Math.min(...ys)-pad,width:Math.max(...xs)-Math.min(...xs)+pad*2,height:Math.max(...ys)-Math.min(...ys)+pad*2};
 }
 function hit(ops,p,tolerance=6,measure){
  for(let i=ops.length-1;i>=0;i--){const b=bounds(ops[i],measure);if(b&&p.x>=b.x-tolerance&&p.x<=b.x+b.width+tolerance&&p.y>=b.y-tolerance&&p.y<=b.y+b.height+tolerance)return i;}
  return -1;
 }
 function translate(op,dx,dy){if(!Number.isFinite(dx)||!Number.isFinite(dy))throw Error('Invalid annotation movement');return{...op,points:op.points.map(p=>({x:p.x+dx,y:p.y+dy}))};}
 function normalizeColor(value){if(typeof value!=='string')return null;let v=value.trim().toLowerCase();if(/^[0-9a-f]{3}$|^[0-9a-f]{6}$/.test(v))v='#'+v;if(/^#[0-9a-f]{3}$/.test(v))v='#'+[...v.slice(1)].map(n=>n+n).join('');return /^#[0-9a-f]{6}$/.test(v)?v:null;}
 function colorToHSV(value,fallbackHue=0){const hex=normalizeColor(value);if(!hex)throw Error('Invalid color');const [r,g,b]=[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255),v=Math.max(r,g,b),delta=v-Math.min(r,g,b);let h=fallbackHue;if(delta){h=v===r?(g-b)/delta+(g<b?6:0):v===g?(b-r)/delta+2:(r-g)/delta+4;h*=60;}return{h,s:v?delta/v:0,v};}
 function colorFromHSV({h,s,v}){if(![h,s,v].every(Number.isFinite))throw Error('Invalid color');h=((h%360)+360)%360;s=Math.max(0,Math.min(1,s));v=Math.max(0,Math.min(1,v));const chroma=v*s,x=chroma*(1-Math.abs((h/60)%2-1)),m=v-chroma,rgb=h<60?[chroma,x,0]:h<120?[x,chroma,0]:h<180?[0,chroma,x]:h<240?[0,x,chroma]:h<300?[x,0,chroma]:[chroma,0,x];return'#'+rgb.map(n=>Math.round((n+m)*255).toString(16).padStart(2,'0')).join('');}
 const api={rect,draw,bounds,hit,translate,normalizeColor,colorToHSV,colorFromHSV,layerGeometry,drawLayer};if(typeof module!=='undefined')module.exports=api;else root.MouseCaptureCore=api;
})(globalThis);
