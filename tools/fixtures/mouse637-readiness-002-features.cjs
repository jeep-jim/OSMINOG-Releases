'use strict';
// Installed, two-process acceptance for the combined 6.0.37 interface features.
// Only the CI-owned profile, loopback PCM audio and a locally generated extension
// are used. Product commands still originate in the actual native shell/guest UI.
const assert=require('node:assert/strict'),fs=require('node:fs/promises'),path=require('node:path'),http=require('node:http');
const {screen,nativeImage}=require('electron');
const {createFixture,pageHTML,bounded,sha256,sleep}=require('./mouse-631-smoke-helpers.cjs');
const {screenCropGeometry}=require('./mouse-628-ui-smoke.cjs');
const {nativeHitTarget}=require('./mouse-smoke-hit-target.cjs');
const {installInputProbe}=require('./mouse-633-smoke-helpers.cjs');
const VERSION='6.0.37',REPORT='mouse-637-features.json',BUDGET=240000;

function ownedWave(frequency=440){
 const rate=8000,seconds=45,samples=rate*seconds,data=Buffer.alloc(44+samples*2);
 data.write('RIFF',0);data.writeUInt32LE(data.length-8,4);data.write('WAVEfmt ',8);data.writeUInt32LE(16,16);
 data.writeUInt16LE(1,20);data.writeUInt16LE(1,22);data.writeUInt32LE(rate,24);data.writeUInt32LE(rate*2,28);
 data.writeUInt16LE(2,32);data.writeUInt16LE(16,34);data.write('data',36);data.writeUInt32LE(samples*2,40);
 for(let i=0;i<samples;i++)data.writeInt16LE(Math.round(Math.sin(2*Math.PI*frequency*i/rate)*700),44+i*2);
 return data;
}
function ownedMediaPage(index){
 return pageHTML(index).replace('</body>',`<style>#media-controls{position:fixed;left:18px;top:172px;display:flex;gap:8px}#media-controls button{height:34px}#native-witness{position:fixed;left:20px;top:224px;width:76px;height:42px;background:rgb(43,164,99)}</style>
 <div id="media-controls"><button id="media-play">Play owned audio</button><button id="media-replace">Replace owned audio</button></div><div id="native-witness"></div>
 <audio id="audio-one" src="/audio/one.wav" preload="auto" loop></audio><audio id="audio-two" src="/audio/two.wav" preload="auto" loop></audio>
 <script>
 globalThis.mouse637Media={current:'audio-one',events:[],error:null};
 const metadata=title=>{if(navigator.mediaSession)navigator.mediaSession.metadata=new MediaMetadata({title,artist:'Mouse owned fixture'});};
 for(const audio of document.querySelectorAll('audio'))for(const type of ['play','playing','pause'])audio.addEventListener(type,event=>mouse637Media.events.push({id:audio.id,type,trusted:event.isTrusted,at:performance.now()}));
 document.querySelector('#media-play').onclick=async event=>{mouse637Media.playClickTrusted=event.isTrusted;try{metadata('Owned first track');await document.querySelector('#audio-one').play();}catch(error){mouse637Media.error=error.message;}};
 document.querySelector('#media-replace').onclick=async event=>{mouse637Media.replaceClickTrusted=event.isTrusted;try{const old=document.querySelector('#audio-one');old.pause();old.remove();mouse637Media.current='audio-two';metadata('Owned replacement track');document.querySelector('#native-witness').style.background='rgb(153,69,193)';await document.querySelector('#audio-two').play();}catch(error){mouse637Media.error=error.message;}};
 </script></body>`);
}
function ownedExtensionFiles(){
 return{
  'manifest.json':JSON.stringify({manifest_version:3,name:'Mouse 637 owned fixture',version:'1.0',action:{default_popup:'panel.html'}})+'\n',
  'panel.html':'<!doctype html><html><head><meta charset="utf-8"><title>Owned extension panel</title><style>body{font:16px system-ui;background:#eef3f8;color:#17242d;margin:20px}#native-witness{position:fixed;left:24px;top:160px;width:90px;height:44px;background:rgb(37,143,191)}button{height:38px}</style></head><body><h1>Owned unpacked extension</h1><button id="extension-action">Use extension page</button><output id="extension-result">Ready</output><div id="native-witness"></div><script src="panel.js"></script></body></html>',
  'panel.js':'globalThis.mouse637Extension={clicks:0,trusted:false,timeOrigin:performance.timeOrigin};document.querySelector("#extension-action").onclick=event=>{mouse637Extension.clicks++;mouse637Extension.trusted=event.isTrusted;document.querySelector("#extension-result").textContent="Action "+mouse637Extension.clicks;};'
 };
}
function languageReadback(){
 const dialog=document.querySelector('#choice-dialog'),rows=[...dialog.querySelectorAll('.language-chooser-row')];
 return{open:dialog.open,locale:document.documentElement.lang,query:dialog.querySelector('input')?.value,
  rows:rows.map(row=>({code:row.querySelector('bdi').lang,label:row.querySelector('bdi').textContent,selectable:row.tagName==='BUTTON',disabled:row.disabled===true})),note:dialog.querySelector('.language-chooser-note')?.textContent};
}
function widgetReadback(){
 const root=document.querySelector('#mouse-media-widget'),r=root.getBoundingClientRect(),css=getComputedStyle(root),rect=e=>{const b=e.getBoundingClientRect();return{x:b.x,y:b.y,width:b.width,height:b.height}};
 const visible=!root.hidden&&css.display!=='none'&&css.visibility==='visible'&&r.width>0&&r.height>0;
 const shown=selector=>{const e=root.querySelector(selector),b=e.getBoundingClientRect(),style=getComputedStyle(e);return visible&&!e.hidden&&style.display!=='none'&&style.visibility==='visible'&&Number(style.opacity)>0&&b.width>0&&b.height>0&&Math.min(b.right,r.right,innerWidth)>Math.max(b.left,r.left,0)&&Math.min(b.bottom,r.bottom,innerHeight)>Math.max(b.top,r.top,0)};
 return{hidden:root.hidden,mode:root.dataset.mode,room:root.dataset.room,visible:!root.hidden&&css.display!=='none'&&css.visibility==='visible'&&r.width>0&&r.height>0,
  title:root.querySelector('[data-media=title]').textContent,seekHidden:root.querySelector('[data-media=seek]').hidden,bounds:rect(root),
  roomPixels:parseFloat(root.style.getPropertyValue('--mouse-media-room')),titleVisible:shown('[data-media=title]'),seekVisible:shown('[data-media=seek]'),dismissVisible:shown('[data-media=dismiss]'),
  returnBounds:rect(root.querySelector('[data-media=return]')),desktopId:MouseTest.model.desktopId};
}
function mediaFixtureBounds(bounds,work,room){
 for(const value of [bounds,work])assert.ok(value&&['x','y','width','height'].every(key=>Number.isFinite(value[key]))&&value.width>0&&value.height>0,'Media fixture needs actual finite native geometry');
 assert.ok(Number.isFinite(room)&&room>=0,'Media fixture needs the measured footer space');
 const left=Math.ceil(work.x),top=Math.ceil(work.y),right=Math.floor(work.x+work.width),bottom=Math.floor(work.y+work.height);
 assert.ok(bounds.width<=right-left&&bounds.height<=bottom-top,'Current media fixture fits the actual display');
 // The production widget caps its full width at 287px. It is positioned after
 // the window midpoint, so each additional footer pixel needs two window pixels.
 // Keep the real window within its display even when that desired space is scarce;
 // the subsequent native hit checks must still prove every required control.
 const width=Math.min(right-left,Math.ceil(bounds.width+2*Math.max(0,287-room))),height=Math.ceil(bounds.height);
 return{x:Math.max(left,Math.min(Math.round(bounds.x),right-width)),y:Math.max(top,Math.min(Math.round(bounds.y),bottom-height)),width,height};
}
function interfaceReadback(){
 const rect=e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height}},root=getComputedStyle(document.documentElement);
 return{theme:document.documentElement.dataset.theme,muted:root.getPropertyValue('--muted').trim(),text:root.getPropertyValue('--text').trim(),
  seams:[...document.querySelectorAll('#stage .split,#stage .divider,#stage .pane')].map(e=>({className:e.className,color:getComputedStyle(e).backgroundColor})),
  panes:[...document.querySelectorAll('#stage .pane')].map(e=>{const h=e.querySelector('.pane-head'),a=e.querySelector('.pane-address input');return{id:e.dataset.pane,compact:e.hasAttribute('data-compact-head'),bounds:rect(e),header:rect(h),address:rect(a),addressColor:getComputedStyle(a).color,focused:a===document.activeElement}})};
}
function appearanceReadback(){
 const root=getComputedStyle(document.documentElement),rect=e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height}};
 return{model:{...MouseTest.model.appearance},stored:JSON.parse(localStorage.getItem('mouseAppearance')||'null'),theme:MouseTest.model.theme,
  primary:root.getPropertyValue('--text-primary').trim().toLowerCase(),textColor:getComputedStyle(document.body).color,
  gap:parseFloat(root.getPropertyValue('--workspace-gap')),radius:parseFloat(root.getPropertyValue('--pane-radius')),
  workspace:rect(document.querySelector('#workspace')),stage:rect(document.querySelector('#stage')),panes:[...document.querySelectorAll('#stage .pane')].map(e=>({id:e.dataset.pane,bounds:rect(e),topRadius:parseFloat(getComputedStyle(e).borderTopLeftRadius),bottomRadius:parseFloat(getComputedStyle(e).borderBottomLeftRadius)})),
  settings:{open:document.querySelector('#settings-dialog').open,square:document.querySelector('#settings-square-grid').checked,
   tone:Number(document.querySelector('#settings-white-tone').value),value:document.querySelector('#settings-white-tone-value').textContent}};
}
function assertAppearance(state,{mode,tone,theme,settings=false}){
 assert.deepEqual(state.model,{paneMode:mode,whiteTone:tone});assert.deepEqual(state.stored,state.model);
 assert.equal(state.theme,theme);const channel=Math.round(160+95*tone/100),color='#'+channel.toString(16).padStart(2,'0').repeat(3);
 assert.equal(state.primary,color);assert.equal(state.gap,mode==='square'?0:6);assert.equal(state.radius,mode==='square'?0:12);
 if(theme==='dark')assert.equal(state.textColor,`rgb(${channel}, ${channel}, ${channel})`);
 if(settings){assert.equal(state.settings.open,true);assert.equal(state.settings.square,mode==='square');assert.equal(state.settings.tone,tone)}
 for(const pane of state.panes){assert.equal(pane.topRadius,mode==='square'?0:12);assert.equal(pane.bottomRadius,mode==='square'?0:12)}
}
function assertSquareGeometry(state,native){
 assert.equal(state.panes.length,2);assert.equal(native.length,2);
 const panes=[...state.panes].sort((a,b)=>a.bounds.x-b.bounds.x),near=(a,b,label)=>assert.ok(Math.abs(a-b)<1.1,label+': '+a+' / '+b);
 near(panes[0].bounds.x,state.stage.x,'Square panes start at the stage edge');
 near(panes[1].bounds.x+panes[1].bounds.width,state.stage.x+state.stage.width,'Square panes fill the stage width');
 near(panes[0].bounds.x+panes[0].bounds.width,panes[1].bounds.x,'Square panes have no horizontal gap');
 near(state.stage.y,state.workspace.y,'Square workspace has no upper inset');near(state.stage.y+state.stage.height,state.workspace.y+state.workspace.height,'Square workspace has no lower inset');
 for(const p of panes){near(p.bounds.y,state.stage.y,'No upper stage inset');near(p.bounds.y+p.bounds.height,state.stage.y+state.stage.height,'No lower stage inset')}
 for(const p of native){assert.equal(p.roundBottom,0);assert.equal(p.visible,true);assert.equal(p.parentVisible,true);assert.equal(p.attached,true)}
}
function sampleWitnesses(bitmap,size,mapping,witnesses){
 assert.equal(bitmap.length,size.width*size.height*4);
 return witnesses.map(witness=>{
  const x=Math.floor(mapping.originX+witness.point.x*mapping.scaleX),y=Math.floor(mapping.originY+witness.point.y*mapping.scaleY);
  assert.ok(x>=0&&y>=0&&x<size.width&&y<size.height,'Owned OS witness lies inside the captured content');
  const at=(y*size.width+x)*4,actualRGBA=[bitmap[at+2],bitmap[at+1],bitmap[at],bitmap[at+3]];
  return{...witness,x,y,actualRGBA,tolerance:3,accepted:actualRGBA[3]===255&&witness.expectedRGB.every((value,i)=>Math.abs(actualRGBA[i]-value)<=3)};
 });
}

module.exports=async ctx=>{
 const {app,win,browser,store,extensions,dialog,globalCapture}=ctx,read=process.argv.includes('--mouse-637-features-restore-read'),started=Date.now(),phaseBudget=read?90000:BUDGET;
 const exit=require('./mouse-smoke-exit.cjs')({app,win});
 let facts={schema:1,version:app.getVersion(),platform:process.platform,arch:process.arch,pid:process.pid,writePid:process.pid,packaged:app.isPackaged,
  profileIsolated:false,budgetMs:BUDGET,physicalUserDeviceVerified:false,chromeWebStoreVerified:false,vkVerified:false,
  source:'Installed app, native input, owned loopback audio, real persistent-session extension and separate-process restoration',phase:'write',stage:'identity',ok:false,restored:false,nativeInputs:[],captures:[]};
 let fixture,nativeInput,server,ownedFolder,error,cleanupError,initialLocale,initialTheme,initialAppearance,originalDialog,heldRelease,restoreExecute;
 const ownedIds=new Set(),requests=[],extensionFiles=ownedExtensionFiles();
 const save=()=>bounded(fs.writeFile(REPORT,JSON.stringify(facts,null,2)+'\n'),2500,'637 evidence write');
 const diagnostic=async()=>{try{await save()}catch{}};
 const watchdog=setTimeout(()=>{facts.ok=false;facts.error={stage:facts.stage,message:'Mouse637 fixed native budget exceeded'};void diagnostic().finally(()=>exit(1));},phaseBudget);
 const stage=async(name,work)=>{facts.stage=name;await save();console.log('MOUSE_637_STAGE '+name);return work()};
 async function focus(wc=win.webContents){app.focus({steal:true});win.show();win.focus();wc.focus();await fixture.until(()=>win.isFocused(),'637 native window focus')}
 async function click(selector,record){
  const wc=record?.page.view.webContents||win.webContents,js=record?source=>fixture.pageJS(record,source):fixture.js;
  await focus(wc);await js(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'nearest',inline:'nearest'});true`);await fixture.frame();
  let hit;await fixture.until(async()=>{hit=await js(`(${nativeHitTarget.toString()})(document.querySelector(${JSON.stringify(selector)}),{})`);return hit.ready},'637 native target '+selector);
  await js(`if(!globalThis.__mouse633Input)(${installInputProbe.toString()})();__mouse633Input.begin(${JSON.stringify(selector)})`);
  const origin=win.getContentBounds(),offset=record?fixture.nativeState(record).bounds:{x:0,y:0},point={x:Math.round(origin.x+offset.x+hit.x),y:Math.round(origin.y+offset.y+hit.y)};
  assert.equal(await nativeInput.testClick(point.x,point.y),true);
  const entry={selector,tabId:record?.id||null,pid:process.pid,source:process.platform==='darwin'?'CGEvent':process.platform==='win32'?'User32':'XTest',point,at:Date.now()};facts.nativeInputs.push(entry);
  await fixture.until(async()=>{entry.events=await js('__mouse633Input.read()');return entry.events.some(e=>e.type==='click'&&e.trusted&&e.matches)},'637 trusted click '+selector);
  await fixture.frame();return entry;
 }
 async function key(keyCode,modifiers=[]){win.webContents.sendInputEvent({type:'keyDown',keyCode,modifiers});win.webContents.sendInputEvent({type:'keyUp',keyCode,modifiers});await fixture.frame()}
 async function text(selector,value){await click(selector);await key('A',[process.platform==='darwin'?'meta':'control']);await key('Backspace');if(value)await win.webContents.insertText(value);await fixture.until(()=>fixture.js(`document.querySelector(${JSON.stringify(selector)}).value===${JSON.stringify(value)}`),'637 text input');return{value,events:await fixture.js('__mouse633Input.read()')}}
 async function locale(code){
  if(await fixture.js('document.documentElement.lang')===code)return;
  await click('#language-select');await fixture.until(()=>fixture.js('document.querySelector("#choice-dialog").open'),'language chooser');
  await click('.language-chooser-row:has(bdi[lang="'+code+'"])');await fixture.until(()=>fixture.js(`document.documentElement.lang===${JSON.stringify(code)}&&!document.querySelector('#choice-dialog').open`),'locale '+code);
 }
 async function theme(value){if(await fixture.js('MouseTest.model.theme')!==value)await click('#theme-button');await fixture.until(()=>fixture.js(`MouseTest.model.theme===${JSON.stringify(value)}`),'theme '+value)}
 async function dragDivider(dx,dy,{square=false}={}){
  const selector='.divider[data-path=""]'+(square?' > .divider-hit':'');await focus();const hit=await fixture.js(`(()=>{const target=document.querySelector(${JSON.stringify(selector)});return (${nativeHitTarget.toString()})(target,{yFraction:${square?'10/Math.max(1,target.getBoundingClientRect().height)':'.5'}})})()`);assert.equal(hit.ready,true);
  await fixture.js(`(()=>{const target=document.querySelector(${JSON.stringify(selector)}),events=[];const listener=e=>events.push({type:e.type,trusted:e.isTrusted,matches:e.target===target||target.contains(e.target),at:Date.now()});for(const type of ['pointerdown','pointerup'])document.addEventListener(type,listener,true);globalThis.__mouse637Resize={events,dispose(){for(const type of ['pointerdown','pointerup'])document.removeEventListener(type,listener,true)}};})()`);
  const origin=win.getContentBounds(),from={x:Math.round(origin.x+hit.x),y:Math.round(origin.y+hit.y)},to={x:Math.round(from.x+dx),y:Math.round(from.y+dy)};
  try{assert.equal(await nativeInput.testMouse(from.x,from.y,0),true);for(let i=1;i<=8;i++){await nativeInput.testMouse(Math.round(from.x+dx*i/8),Math.round(from.y+dy*i/8),1);await sleep(15)}}
  finally{assert.equal(await nativeInput.testMouse(to.x,to.y,2),true)}
  await fixture.frame();const events=await fixture.js('__mouse637Resize.events');await fixture.js('__mouse637Resize.dispose();delete globalThis.__mouse637Resize');
  assert.ok(events.some(e=>e.type==='pointerdown'&&e.trusted&&e.matches));assert.ok(events.some(e=>e.type==='pointerup'&&e.trusted));
  const entry={selector,action:'drag',from,to,pid:process.pid,source:process.platform==='darwin'?'CGEvent':process.platform==='win32'?'User32':'XTest',events};facts.nativeInputs.push(entry);return entry;
 }
 async function witness(record){
  const local=await fixture.pageJS(record,`(()=>{const e=document.querySelector('#native-witness'),r=e.getBoundingClientRect();return{point:{x:r.x+r.width/2,y:r.y+r.height/2},color:getComputedStyle(e).backgroundColor}})()`),native=fixture.nativeState(record);
  assert.ok(native.visible&&native.parentVisible&&native.cachedVisible&&native.attached);const expectedRGB=local.color.match(/\d+/g).map(Number).slice(0,3);
  return{name:'owned native guest',tabId:record.id,webContentsId:native.webContentsId,point:{x:native.bounds.x+local.point.x,y:native.bounds.y+local.point.y},expectedRGB};
 }
 async function capture(filename,witnesses=[]){
  assert.match(filename,/^mouse-637-[a-z-]+\.png$/);await fixture.frame();const display=screen.getDisplayMatching(win.getBounds()),contentBounds=win.getContentBounds();
  let result,png,full;const attempts=[];
  for(let attempt=1;attempt<=6;attempt++){
   const frame=await bounded(globalCapture.acquire(display),4500,'637 real OS capture');assert.equal(frame.kind,'screen');assert.ok(frame.backend);
   full=Buffer.from(frame.base.slice(frame.base.indexOf(',')+1),'base64');const screenPixelSize={width:full.readUInt32BE(16),height:full.readUInt32BE(20)},geometry=screenCropGeometry(display.bounds,contentBounds,screenPixelSize),image=nativeImage.createFromBuffer(full).crop(geometry.cropPixels);
   png=image.toPNG({scaleFactor:1});const pixelSize={width:png.readUInt32BE(16),height:png.readUInt32BE(20)},probes=sampleWitnesses(image.toBitmap({scaleFactor:1}),pixelSize,geometry.mapping,witnesses);
   attempts.push({attempt,accepted:probes.every(p=>p.accepted)});result={filename,displayFilename:filename.replace(/\.png$/,'-display.png'),source:'globalCapture.acquire(display)',backend:frame.backend,kind:'screen',pid:process.pid,sha256:sha256(png),displaySha256:sha256(full),bytes:png.length,screenPixelSize,pixelSize,contentBounds,display:{id:display.id,bounds:display.bounds,workArea:display.workArea,scaleFactor:display.scaleFactor},...geometry,probes,attempts};
   if(attempts.at(-1).accepted)break;await sleep(50);
  }
  await fs.writeFile(filename,png);await fs.writeFile(result.displayFilename,full);facts.captures.push(result);await save();assert.ok(attempts.at(-1).accepted,'Actual OS pixels show the current owned guest');return result;
 }
 async function extensionButton(id,label){
  const selector='.mouse-extension-row[data-id="'+id+'"] .mouse-extension-actions>button';
  const index=await fixture.js(`[...document.querySelectorAll(${JSON.stringify(selector)})].findIndex(e=>e.textContent===${JSON.stringify(label)})`);assert.ok(index>=0,'Extension action '+label);return click(selector+':nth-child('+(index+1)+')');
 }
 async function openExtensions(){await click('#mouse-extensions-button');await fixture.until(()=>fixture.js('document.querySelector("#mouse-extensions-dialog").open'),'extensions dialog')}
 async function closeExtensions(){await click('#mouse-extensions-dialog [data-close-dialog]');await fixture.until(()=>fixture.js('!document.querySelector("#mouse-extensions-dialog").open'),'extensions dialog closes')}
 async function prepareDialogs(folder){
  originalDialog={showOpenDialog:dialog.showOpenDialog,showMessageBox:dialog.showMessageBox};const calls=[];
  dialog.showOpenDialog=async(_win,options)=>{assert.deepEqual(options.properties,['openDirectory']);calls.push({kind:'folder',selection:'owned unpacked fixture',at:Date.now()});return{canceled:false,filePaths:[folder]}};
  dialog.showMessageBox=async(_win,options)=>{assert.deepEqual(options.buttons,['Отмена','Установить']);assert.equal(options.defaultId,0);assert.match(options.message,/Mouse 637 owned fixture/);calls.push({kind:'consent',message:options.message,detail:options.detail,response:1,at:Date.now()});return{response:1}};
  return calls;
 }
 async function installExtension(){
  const before=new Set(extensions.state().map(e=>e.id));await click('#mouse-extensions-install');let entry;
  await fixture.until(()=>{entry=extensions.state().find(e=>!before.has(e.id));return entry?.enabled},'actual Electron extension loads');ownedIds.add(entry.id);return entry;
 }
 async function restorePreferences(){if(fixture){await fixture.js(`MouseTest.setLocale(${JSON.stringify(initialLocale)});MouseTest.setTheme(${JSON.stringify(initialTheme)});MouseFlush()`);if((read||error)&&initialAppearance)await fixture.js(`MouseTest.setAppearance(${JSON.stringify(initialAppearance)})`);await store.queue}}
 async function appearanceState(){return fixture.js(`(${appearanceReadback.toString()})()`)}
 async function openAppearance(){if(!await fixture.js('document.querySelector("#settings-dialog").open'))await click('#settings-button');await fixture.until(()=>fixture.js('document.querySelector("#settings-dialog").open'),'appearance settings open')}
 async function closeAppearance(){if(await fixture.js('document.querySelector("#settings-dialog").open'))await click('#settings-dialog [data-close-dialog]');await fixture.until(()=>fixture.js('!document.querySelector("#settings-dialog").open'),'appearance settings closed');await fixture.frame()}
 async function selectTone(endpoint){await click('#settings-white-tone');await key(endpoint==='min'?'Home':'End');await fixture.until(()=>fixture.js(`MouseTest.model.appearance.whiteTone===${endpoint==='min'?0:100}`),'native text tone '+endpoint)}
 try{
  assert.equal(process.env.CI,'true');assert.ok(path.isAbsolute(process.env.MOUSE_TEST_PROFILE||''));assert.equal(path.resolve(app.getPath('userData')),path.resolve(process.env.MOUSE_TEST_PROFILE));assert.equal(app.isPackaged,true);assert.equal(app.getVersion(),VERSION);assert.equal(app.getName(),'Mouse Browser');assert.ok(extensions&&dialog);
  assert.ok([['darwin','arm64'],['win32','x64'],['linux','x64']].some(([p,a])=>p===process.platform&&a===process.arch));
  if(read){
   facts=JSON.parse(await fs.readFile(REPORT,'utf8'));assert.equal(facts.version,VERSION);assert.equal(facts.platform,process.platform);assert.equal(facts.arch,process.arch);assert.equal(facts.writeComplete,true);assert.equal(facts.awaitingRestart,true);assert.notEqual(facts.writePid,process.pid);assert.equal(facts.profile,path.resolve(app.getPath('userData')));
   facts.phase='read';facts.restart={pid:process.pid,writePid:facts.writePid,processChanged:true,budgetMs:phaseBudget,startedAt:Date.now()};
   ownedFolder=facts.restoreFixture.ownedFolder;assert.equal(path.dirname(ownedFolder),path.resolve(app.getPath('userData')));assert.match(path.basename(ownedFolder),/^mouse637-owned-/);assert.equal((await fs.lstat(ownedFolder)).isSymbolicLink(),false);ownedIds.add(facts.restoreFixture.id);
  }
  facts.profileIsolated=true;facts.profile=path.resolve(app.getPath('userData'));
  nativeInput=ctx.nativeInput||(process.platform==='darwin'?require('./mouse-native-menu.node'):process.platform==='win32'?require('./mouse-windows-input.cjs').createWindowsInput():require('./mouse-linux-input.cjs').createLinuxInput());
  fixture=await createFixture({...ctx,nativeInput},read?'features637-read':'features637-write',phaseBudget);
  await fixture.until(()=>fixture.js('document.documentElement.dataset.mouseReady==="true"&&!!globalThis.MouseTest'),'637 shell ready',15000);
  await fixture.js(`(${installInputProbe.toString()})()`);initialLocale=await fixture.js('MouseTest.model.locale');initialTheme=await fixture.js('MouseTest.model.theme');
  initialAppearance=read?facts.appearance.initial:await fixture.js('({...MouseTest.model.appearance})');
  if(read){
   await stage('native-appearance-restart',async()=>{
    assert.equal(facts.appearance.writeVerified,true);const restored=await appearanceState();
    assertAppearance(restored,{mode:'square',tone:0,theme:initialTheme});
    await theme('dark');await openAppearance();const settings=await appearanceState();assertAppearance(settings,{mode:'square',tone:0,theme:'dark',settings:true});
    await capture('mouse-637-appearance-restored.png');
    await click('#settings-square-grid');await click('#settings-white-tone-reset');
    await fixture.until(()=>fixture.js('MouseTest.model.appearance.paneMode==="rounded"&&MouseTest.model.appearance.whiteTone===55'),'native appearance reset after restart');
    await closeAppearance();facts.appearance.restart={pid:process.pid,writePid:facts.writePid,restored,settings,verified:true};
   });
   await stage('restart-restore-error',async()=>{
    const entry=extensions.state().find(e=>e.id===facts.restoreFixture.id);assert.ok(entry);assert.equal(entry.enabled,false);assert.equal(entry.error,'load_failed');assert.equal(entry.pinned,true);
    const registry=JSON.parse(await fs.readFile(path.join(app.getPath('userData'),'mouse-local-extensions','registry.json'),'utf8'));assert.deepEqual(registry,facts.restoreFixture.registry,'Startup preserves the failed record and its exact saved content hash');
    const states=[];await locale('ru');
    for(const color of ['light','dark']){
     await theme(color);await openExtensions();
     const state=await fixture.js(`(()=>{const row=document.querySelector('.mouse-extension-row[data-id="${entry.id}"]');return{theme:document.documentElement.dataset.theme,state:row?.dataset.state,guidance:row?.querySelector('.mouse-extension-restore-error')?.textContent,pins:document.querySelector('#mouse-extensions-pins').children.length}})()`);
     assert.equal(state.state,'restore-error');assert.match(state.guidance,/Не удалось восстановить.*заново.*папки/);assert.equal(state.pins,0);states.push(state);
     if(color==='dark')await capture('mouse-637-extensions-restore-error.png');await closeExtensions();
    }
    facts.restart.restoreError={entry,states,registryPreserved:true};
    await locale('en');await openExtensions();
    const english=await fixture.js(`document.querySelector('.mouse-extension-row[data-id="${entry.id}"] .mouse-extension-restore-error').textContent`);assert.match(english,/Could not restore.*reinstall.*folder/);facts.restart.restoreError.englishGuidance=english;
    await extensionButton(entry.id,'Remove from Mouse');await fixture.until(()=>!extensions.state().some(e=>e.id===entry.id),'failed extension removed');facts.restart.removed=true;
    const folder=path.join(ownedFolder,'extension');for(const [name,bytes]of Object.entries(extensionFiles))assert.equal(await fs.readFile(path.join(folder,name),'utf8'),bytes,'Original owned source remains unchanged');
    facts.restart.dialogs=await prepareDialogs(folder);const reinstalled=await installExtension();assert.notEqual(reinstalled.id,entry.id);assert.equal(reinstalled.error,undefined);facts.restart.reinstalled=reinstalled;
    await extensionButton(reinstalled.id,'Remove from Mouse');await fixture.until(()=>extensions.state().length===0,'reinstalled fixture removed');await closeExtensions();
   });
  }else{
   assert.deepEqual(extensions.state(),[],'This dedicated isolated feature profile starts without extensions');
   ownedFolder=await fs.mkdtemp(path.join(app.getPath('userData'),'mouse637-owned-'));const folder=path.join(ownedFolder,'extension');await fs.mkdir(folder);for(const [name,bytes]of Object.entries(extensionFiles))await fs.writeFile(path.join(folder,name),bytes);
   const waves={one:ownedWave(440),two:ownedWave(554)};
   server=http.createServer((req,res)=>{
    const pathname=new URL(req.url,'http://localhost').pathname;requests.push({path:pathname,at:Date.now()});res.setHeader('Cache-Control','no-store');
    const page=pathname.match(/^\/page\/(\d+)\/$/),audio=pathname.match(/^\/audio\/(one|two)\.wav$/);
    if(page){res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});res.end(ownedMediaPage(Number(page[1])))}
    else if(audio){const bytes=waves[audio[1]];res.writeHead(200,{'Content-Type':'audio/wav','Content-Length':bytes.length,'Accept-Ranges':'none'});res.end(bytes)}
    else{res.writeHead(404);res.end()}
   });await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve)});
   const base='http://127.0.0.1:'+server.address().port;facts.fixtureOrigin=base;facts.audio={owned:true,format:'PCM16 mono WAV',files:Object.entries(waves).map(([name,bytes])=>({name,bytes:bytes.length,sha256:sha256(bytes)}))};
   const records=[];for(let i=0;i<2;i++)records.push(await fixture.open(base+'/page/'+i+'/',i));await fixture.setLayout(records);
   await stage('native-language-search',async()=>{
    const searches=[],selections=[],catalogs=[];
    for(const code of ['ru','en']){
     await locale(code);await click('#language-select');let state=await fixture.js(`(${languageReadback.toString()})()`);
     assert.equal(state.rows.length,72);assert.deepEqual(state.rows.filter(x=>x.selectable).map(x=>x.code),['ru','en']);catalogs.push({locale:code,rows:state.rows});
     await text('.language-chooser-search','КИТАЙСКИЙ');state=await fixture.js(`(${languageReadback.toString()})()`);assert.deepEqual(state.rows.map(x=>x.code),['zh-Hans','zh-Hant']);assert.ok(state.rows.every(x=>!x.selectable));searches.push({locale:code,query:'КИТАЙСКИЙ',rows:state.rows});
     await capture('mouse-637-language-'+code+'.png');await text('.language-chooser-search','японский');state=await fixture.js(`(${languageReadback.toString()})()`);assert.deepEqual(state.rows.map(x=>x.code),['ja']);searches.push({locale:code,query:'японский',rows:state.rows});
     await key('Escape');await fixture.until(()=>fixture.js('!document.querySelector("#choice-dialog").open'),'chooser Escape closes');selections.push({locale:code,actual:await fixture.js('MouseTest.model.locale')});
    }
    facts.language={catalogCount:72,catalogs,selectableCodes:['ru','en'],searches,selections,untranslatedSelectable:false};await locale('ru');
   });
   await stage('native-pane-interface',async()=>{
    const states=[];
    for(const color of ['light','dark']){
     await theme(color);await click('#native-witness',records[1]);
     const state=await fixture.js(`(${interfaceReadback.toString()})()`);assert.equal(state.panes.length,2);assert.ok(state.panes.every(p=>p.header.height>0&&p.header.height<=28));
     const first='.pane[data-pane="'+state.panes[0].id+'"] .pane-address input';await click(first);
     const focused=await fixture.js(`(${interfaceReadback.toString()})()`);assert.equal(focused.panes[0].focused,true);
     if(color==='dark')assert.notEqual(focused.panes[0].addressColor,state.panes[0].addressColor,'Focused dark address is more prominent than its resting text');
     const normalNative=records.map(fixture.nativeState);
     await fixture.js('MouseTest.model.tree={axis:"y",ratio:.5,a:{id:"p1"},b:{id:"p2"}};MouseTest.renderTree();MouseTest.requestLayout();MouseTest.save()');
     await fixture.frame();const divider=await fixture.js('(()=>{const p=document.querySelector(".pane[data-pane=p1]").getBoundingClientRect(),d=document.querySelector(".divider[data-path=\\"\\"]").getBoundingClientRect();return{distance:p.y+MouseLayout.minimum({id:"p1"},"y")-(d.y+d.height/2)}})()');
     await dragDivider(0,divider.distance);await click('#native-witness',records[1]);
     let compact;await fixture.until(async()=>{compact=await fixture.js(`(${interfaceReadback.toString()})()`);return compact.panes[0].compact&&compact.panes[0].header.height<=5.5},'real compact header strip');
     const compactNatives=records.map(fixture.nativeState),compactNative=compactNatives[0];await capture('mouse-637-interface-'+color+'.png',[await witness(records[1])]);
     const head=compact.panes[0].header,origin=win.getContentBounds();await nativeInput.testPointer(Math.round(origin.x+head.x+head.width/2),Math.round(origin.y+head.y+2));
     await fixture.until(()=>fixture.js('document.querySelector(".pane[data-pane=p1] .pane-head").getBoundingClientRect().height>=28'),'native hover expands compact header');await click('.pane[data-pane="p1"] .pane-address input');await key('Tab');await key('Tab',['shift']);
     const keyboard=await fixture.js(`(${interfaceReadback.toString()})()`);assert.equal(keyboard.panes[0].focused,true);assert.ok(keyboard.panes[0].header.height>=28);const expandedNative=fixture.nativeState(records[0]);assert.equal(expandedNative.webContentsId,compactNative.webContentsId);
     states.push({theme:color,resting:state,focused,native:normalNative,compact,compactNative,compactNatives,keyboard,expandedNative});await fixture.setLayout(records);
    }
    facts.interface={themes:states};
   });
   await stage('native-unpacked-extension',async()=>{
    facts.extensions={dialogs:await prepareDialogs(folder)};await openExtensions();const entry=await installExtension();facts.extensions.installed=entry;
    await extensionButton(entry.id,'Закрепить');await fixture.until(()=>extensions.state().find(e=>e.id===entry.id)?.pinned,'persisted extension pin');
    assert.equal(await fixture.js('document.querySelectorAll("#mouse-extensions-pins .mouse-extension-pin").length'),1);await capture('mouse-637-extensions-installed.png');await closeExtensions();
    const before=new Set(browser.tabs.keys());await click('#mouse-extensions-pins .mouse-extension-pin');let page;
    await fixture.until(()=>{page=[...browser.tabs.values()].find(p=>!before.has(p.id)&&p.managedExtension);return page},'real managed extension pane');
    const record={id:page.id,index:2,desk:fixture.bank.active,page};fixture.created.push(record);await fixture.setLayout([record,records[1]]);
    await fixture.until(()=>fixture.pageJS(record,'!!globalThis.mouse637Extension'),'extension JavaScript executes');await click('#extension-action',record);
    const beforeResize=fixture.nativeState(record),guestBefore=await fixture.pageJS(record,'({...mouse637Extension,url:location.href})');assert.equal(guestBefore.clicks,1);assert.equal(guestBefore.trusted,true);assert.match(guestBefore.url,/^chrome-extension:\/\/[a-p]{32}\/panel\.html$/);
    await dragDivider(60,0);
    await fixture.until(()=>Math.abs(record.page.bounds.width-beforeResize.bounds.width)>=20,'actual native extension pane resized');const afterResize=fixture.nativeState(record),guestAfter=await fixture.pageJS(record,'({...mouse637Extension,url:location.href})');
    assert.deepEqual(guestAfter,guestBefore);assert.equal(afterResize.webContentsId,beforeResize.webContentsId);
    facts.extensions.pane={beforeResize,afterResize,guestBefore,guestAfter,identityPreserved:true};facts.extensions.pinned=true;await capture('mouse-637-extensions-pane.png',[await witness(record)]);
    await fixture.setLayout(records);facts.restoreFixture={id:entry.id,ownedFolder,registry:JSON.parse(await fs.readFile(path.join(app.getPath('userData'),'mouse-local-extensions','registry.json'),'utf8'))};
   });
   await stage('native-media-widget',async()=>{
    const record=records[0],wc=record.page.view.webContents,nativeEvents=[];const playing=()=>nativeEvents.push({type:'media-started-playing',at:Date.now()});wc.on('media-started-playing',playing);
    try{
     await fixture.until(()=>fixture.pageJS(record,'[...document.querySelectorAll("audio")].every(e=>e.readyState>=2)'),'real PCM audio preloaded');await click('#media-play',record);
     const player=()=>fixture.js('MouseNative.mediaPlayer("state")');let state;
     await fixture.until(async()=>{state=await player();return state.player?.trackTitle==='Owned first track'&&!state.player.paused},'real native audio appears in widget');assert.ok(nativeEvents.length>0);
     const beforeBounds=win.getBounds(),workArea=screen.getDisplayMatching(beforeBounds).workArea,initialWidget=await fixture.js(`(${widgetReadback.toString()})()`),requestedBounds=mediaFixtureBounds(beforeBounds,workArea,initialWidget.roomPixels);
     facts.mediaGeometry={beforeBounds,workArea,initialWidget,requestedBounds};win.setBounds(requestedBounds);await fixture.frame();
     let fullControls;await fixture.until(async()=>{fullControls=await fixture.js(`Object.fromEntries(['toggle','title','seek','return','dismiss'].map(name=>[name,(${nativeHitTarget.toString()})(document.querySelector('#mouse-media-widget [data-media='+name+']'),{})]))`);return Object.values(fullControls).every(hit=>hit.ready)},'637 full media controls fit the actual native window');
     facts.mediaGeometry.appliedBounds=win.getBounds();facts.mediaGeometry.fullControls=fullControls;
     const full=await fixture.js(`(${widgetReadback.toString()})()`),nativeBefore=fixture.nativeState(record);assert.equal(full.mode,'full');assert.equal(full.visible,true);assert.equal(full.seekHidden,false);assert.equal(full.titleVisible,true);assert.equal(full.seekVisible,true);assert.equal(full.dismissVisible,true);await capture('mouse-637-media-full.png',[await witness(record)]);
     const origin=fixture.bank.active,other=fixture.bank.items.find(d=>d.id!==origin)?.id;assert.ok(other);await fixture.switchDesk(other);const compact=await fixture.js(`(${widgetReadback.toString()})()`);assert.equal(compact.mode,'compact');assert.equal(compact.visible,true);assert.equal(compact.seekHidden,true);assert.equal(compact.seekVisible,false);assert.equal(compact.dismissVisible,false);assert.equal((await player()).player.id,state.player.id);await capture('mouse-637-media-compact.png');
     await click('#mouse-media-widget [data-media=return]');await fixture.until(()=>fixture.bank.active===origin&&record.page.visible,'widget returns to actual source desktop');const returned=await fixture.js(`(${widgetReadback.toString()})()`);assert.equal(returned.mode,'full');
     const before=state.player,execute=wc.executeJavaScriptInIsolatedWorld.bind(wc);let held=false,heldAt;
     restoreExecute=()=>{wc.executeJavaScriptInIsolatedWorld=execute};
     wc.executeJavaScriptInIsolatedWorld=(...args)=>{
      if(!held&&args[0]===1294&&args[1][0].code.includes(')("read",')){held=true;heldAt=Date.now();return new Promise(resolve=>{heldRelease=()=>resolve(execute(...args))})}
      return execute(...args);
     };
     await fixture.until(()=>held,'actual production refresh pending',2500);const eventsBefore=nativeEvents.length;await click('#media-replace',record);
     await fixture.until(()=>nativeEvents.length>eventsBefore,'real replacement audio native play event',1200);assert.ok(Date.now()-heldAt<1700,'Replacement occurs inside the real pending read deadline');heldRelease();heldRelease=null;restoreExecute();restoreExecute=null;
     await fixture.until(async()=>{state=await player();return state.player?.trackTitle==='Owned replacement track'&&!state.player.paused&&state.player.id!==before.id},'widget retains replacement audio');
     const after=state.player,guest=await fixture.pageJS(record,'({...mouse637Media,audio:[...document.querySelectorAll("audio")].map(e=>({id:e.id,paused:e.paused,currentTime:e.currentTime}))})');assert.equal(guest.replaceClickTrusted,true);assert.equal(guest.error,null);assert.equal(guest.audio.length,1);assert.equal(guest.audio[0].id,'audio-two');
     await capture('mouse-637-media-replacement.png',[await witness(record)]);await click('#mouse-media-widget [data-media=toggle]');await fixture.until(()=>fixture.pageJS(record,'document.querySelector("#audio-two").paused'),'widget pauses replacement original element');
     await click('#mouse-media-widget [data-media=toggle]');await fixture.until(()=>fixture.pageJS(record,'!document.querySelector("#audio-two").paused'),'widget resumes replacement original element');
     const unrelated=await fixture.pageJS(records[1],'[...document.querySelectorAll("audio")].every(e=>e.paused)');assert.equal(unrelated,true);
     facts.media={full,compact,returned,nativeBefore,nativeAfter:fixture.nativeState(record),originDesktop:origin,otherDesktop:other,nativeEvents,before,after,replacement:{readPending:true,heldAt,distinctElement:true,distinctPlayerId:before.id!==after.id,guest},pauseResumeOriginal:true,unrelatedPaused:true};
     const dismissInput=await click('#mouse-media-widget [data-media=dismiss]');await fixture.until(()=>fixture.js('document.querySelector("#mouse-media-widget").hidden'),'native dismiss hides the media widget');assert.equal(await fixture.pageJS(record,'document.querySelector("#audio-two").paused'),false);facts.media.dismiss={input:dismissInput,hidden:true,audioStillPlaying:true};await fixture.pageJS(record,'document.querySelector("#audio-two").pause();true');
     win.setBounds(beforeBounds);await fixture.frame();facts.mediaGeometry.restoredBounds=win.getBounds();assert.deepEqual(facts.mediaGeometry.restoredBounds,beforeBounds);
    }finally{wc.removeListener('media-started-playing',playing);if(heldRelease){heldRelease();heldRelease=null}if(restoreExecute){restoreExecute();restoreExecute=null}}
   });
   facts.audio.requests=requests;assert.ok(requests.some(x=>x.path==='/audio/one.wav')&&requests.some(x=>x.path==='/audio/two.wav'));
   await stage('native-ai-preview-window',()=>require('./mouse-637-ai-preview-smoke.cjs')({app,win,browser,fixture,nativeInput,click,key,text,capture,theme,openAppearance,closeAppearance,facts,records}));
   const combinedContext={...ctx,fixture,nativeInput,click,key,text,capture,theme,openAppearance,closeAppearance,facts,records};
   await stage('native-populated-presets',()=>require('./mouse-637-presets-smoke.cjs')(combinedContext));
   await stage('native-sidebar-focus',()=>require('./mouse-637-sidebar-focus-smoke.cjs')(combinedContext));
   await stage('native-library-file-actions',()=>require('./mouse-637-library-actions-smoke.cjs')(combinedContext));
   await stage('native-appearance-settings',async()=>{
    await fixture.switchDesk(records[0].desk);await fixture.setLayout(records);
    const before=await Promise.all(records.map(fixture.identity));
    facts.appearance={initial:initialAppearance,range:{min:0,max:100,minimum:'#a0a0a0',maximum:'#ffffff',default:55,defaultColor:'#d4d4d4'},samples:[],writeVerified:false};
    assert.deepEqual(initialAppearance,{paneMode:'rounded',whiteTone:55},'Clean profile keeps the current geometry and starts with soft white');
    for(const color of ['light','dark']){
     await theme(color);await openAppearance();const initial=await appearanceState();
     await selectTone('min');const minimum=await appearanceState();assertAppearance(minimum,{mode:'rounded',tone:0,theme:color,settings:true});
     await selectTone('max');const maximum=await appearanceState();assertAppearance(maximum,{mode:'rounded',tone:100,theme:color,settings:true});
     if(color==='light'){assert.equal(minimum.textColor,initial.textColor);assert.equal(maximum.textColor,initial.textColor)}
     await click('#settings-white-tone-reset');await fixture.until(()=>fixture.js('MouseTest.model.appearance.whiteTone===55'),'default soft white');
     const reset=await appearanceState();assertAppearance(reset,{mode:'rounded',tone:55,theme:color,settings:true});
     await capture('mouse-637-appearance-controls-'+color+'.png');
     await click('#settings-square-grid');await closeAppearance();
     await fixture.until(()=>records.every(r=>r.page.captureGeometry?.roundBottom===0),'native square pane masks');
     const beforeResize=records.map(fixture.nativeState),resizeInput=await dragDivider(32,0,{square:true});
     await fixture.until(()=>Math.abs(records[0].page.bounds.width-beforeResize[0].bounds.width)>=16,'square grid native resize');
     const square=await appearanceState(),native=records.map(r=>({...fixture.nativeState(r),roundBottom:r.page.captureGeometry.roundBottom}));
     assertAppearance(square,{mode:'square',tone:55,theme:color});assertSquareGeometry(square,native);
     await capture('mouse-637-appearance-square-'+color+'.png',await Promise.all(records.map(witness)));
     await openAppearance();await click('#settings-square-grid');await closeAppearance();
     await fixture.until(()=>records.every(r=>r.page.captureGeometry?.roundBottom===12),'native rounded pane masks restored');
     const rounded=await appearanceState();assertAppearance(rounded,{mode:'rounded',tone:55,theme:color});
     facts.appearance.samples.push({theme:color,initial,minimum,maximum,reset,square,native,rounded,resize:{before:beforeResize,after:native,input:resizeInput}});
    }
    const after=await Promise.all(records.map(fixture.identity));for(let i=0;i<before.length;i++)fixture.assertIdentity(before[i],after[i]);
    facts.appearance.pages={before,after,identityPreserved:true};
    await openAppearance();await click('#settings-square-grid');await selectTone('min');await closeAppearance();
    const persisted=await appearanceState();assertAppearance(persisted,{mode:'square',tone:0,theme:'dark'});
    facts.appearance.persisted=persisted;facts.appearance.writeVerified=true;
   });
   await stage('native-update-burrow',()=>require('./mouse-637-update-ui-smoke.cjs')(combinedContext));
  }
 }catch(cause){error=cause;facts.error={stage:facts.stage,message:cause.message,stack:cause.stack};await diagnostic();if(fixture)try{await capture('mouse-637-features-failure.png')}catch(captureError){facts.failureCaptureError=captureError.message}}
 finally{
  const cleanup=async(label,work)=>{try{return await work()}catch(cause){cleanupError||=cause;(facts.cleanupErrors||=[]).push({label,message:cause.message});await diagnostic()}};
  if(heldRelease)heldRelease();if(restoreExecute)restoreExecute();if(originalDialog){dialog.showOpenDialog=originalDialog.showOpenDialog;dialog.showMessageBox=originalDialog.showMessageBox}
  if(fixture){await cleanup('close feature dialogs',()=>fixture.js('MouseTest.settingsUI.close();document.querySelector("#choice-dialog")?.close();document.querySelector("#mouse-extensions-dialog")?.close();globalThis.__mouse633Input?.dispose();true'));await cleanup('locale/theme restoration',restorePreferences);const workspace=await cleanup('workspace restoration',()=>bounded(fixture.cleanup(),22000,'637 workspace cleanup'));if(read)facts.restart.cleanup=workspace;else facts.writeCleanup=workspace;}
  if(server){server.closeAllConnections();await cleanup('owned server',()=>bounded(new Promise(resolve=>server.close(resolve)),2500,'637 server shutdown'))}
  if(read||error||cleanupError){
   for(const id of ownedIds)await cleanup('owned extension '+id,async()=>{if(extensions.state().some(e=>e.id===id))await extensions.remove(id);assert.match(id,/^[0-9a-f-]{36}$/i);await fs.rm(path.join(app.getPath('userData'),'mouse-local-extensions','packages',id),{recursive:true,force:true})});
   if(ownedFolder)await cleanup('owned source files',()=>fs.rm(ownedFolder,{recursive:true,force:true}));
  }else if(facts.restoreFixture){
   await cleanup('prepare restart-only damaged fixture',async()=>{const file=path.join(app.getPath('userData'),'mouse-local-extensions','packages',facts.restoreFixture.id,'panel.html'),before=await fs.readFile(file);await fs.appendFile(file,'\n<!-- owned restart checksum failure -->\n');facts.restoreFixture.beforeSha256=sha256(before);facts.restoreFixture.afterSha256=sha256(await fs.readFile(file));assert.notEqual(facts.restoreFixture.beforeSha256,facts.restoreFixture.afterSha256);facts.restoreFixture.persistedEnabled=facts.restoreFixture.registry[0].enabled;assert.equal(facts.restoreFixture.persistedEnabled,true)});
  }
  const phaseElapsedMs=Date.now()-started;if(read)facts.restart.elapsedMs=phaseElapsedMs;else facts.writeElapsedMs=phaseElapsedMs;
  facts.elapsedMs=(facts.elapsedMs||0)+phaseElapsedMs;
  if(read){facts.ok=!error&&!cleanupError&&facts.restart.cleanup?.restored===true;facts.restored=facts.ok;facts.awaitingRestart=false;facts.stage=facts.ok?'complete':'failed';facts.phase=facts.ok?'complete':'read'}
  else{facts.writeComplete=!error&&!cleanupError&&facts.writeCleanup?.restored===true;facts.awaitingRestart=facts.writeComplete;facts.stage=facts.writeComplete?'awaiting-restart':'failed'}
  try{await save()}catch(cause){error||=cause;facts.ok=false;facts.writeComplete=false;await diagnostic()}clearTimeout(watchdog);
 }
 const success=read?facts.ok:facts.writeComplete;
 if(success){console.log(read?'MOUSE_637_FEATURES_NATIVE_PASS':'MOUSE_637_FEATURES_WRITE_PASS');exit(0)}else{console.error('MOUSE_637_FEATURES_FAILED '+(facts.error?.message||cleanupError?.message||'verification incomplete'));exit(1)}
};
module.exports.fixtures={ownedWave,ownedMediaPage,ownedExtensionFiles,sampleWitnesses,assertAppearance,assertSquareGeometry,widgetReadback,mediaFixtureBounds};
