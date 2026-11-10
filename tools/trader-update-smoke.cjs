'use strict';
// TRADER_UPDATE_HARNESS_V2: compatibility harness for the already-published 5.0.0 binary.
const assert=require('node:assert/strict');
module.exports=async function smoke({app,win,browser,autoUpdater,updates,store,verify=false}){
 await win.webContents.executeJavaScript("new Promise((resolve,reject)=>{const started=Date.now();const check=()=>document.documentElement.dataset.traderReady==='true'?resolve(true):document.documentElement.dataset.traderReady==='error'?reject(Error('Trader OS update verification failed to start')):Date.now()-started>30000?reject(Error('Trader OS update verification readiness timed out')):setTimeout(check,100);check()})");
 const expected=process.argv.find(a=>a.startsWith('--expect-version='))?.split('=')[1];
 if(verify){
  assert.equal(app.getVersion(),expected);
  const saved=await store.get('osminogUpdateSentinel');assert.equal(saved.osminogUpdateSentinel?.value,'keep-this-project','Local profile data was lost during update');
  const cookies=await browser.session.cookies.get({url:'http://127.0.0.1',name:'osminog-update-sentinel'});assert.equal(cookies[0]?.value,'keep-local-login');
  console.log('INSTALLED_UPDATE_SMOKE_PASS '+app.getVersion());app.exit(0);return;
 }
 const feed=process.argv.find(a=>a.startsWith('--test-feed='))?.slice('--test-feed='.length),url=new URL(feed);
 assert.equal(url.protocol,'http:');assert.equal(url.hostname,'127.0.0.1');assert(!url.username&&!url.password);
 autoUpdater.setFeedURL({provider:'generic',url:url.href});
 const stored=await win.webContents.executeJavaScript("(async()=>{try{await OSMINOGNative.set({osminogUpdateSentinel:{value:'keep-this-project'}});return{ok:true}}catch(e){return{ok:false,error:String(e?.message||e),stack:String(e?.stack||'')}}})()");
 assert.equal(stored?.ok,true,'Update sentinel write failed: '+stored?.error+'\n'+stored?.stack);
 console.log('UPDATE_SENTINEL_STORED');
 await browser.session.cookies.set({url:'http://127.0.0.1',name:'osminog-update-sentinel',value:'keep-local-login',expirationDate:Date.now()/1000+86400});await browser.session.cookies.flushStore();
 const driven=await win.webContents.executeJavaScript("(async()=>{try{const click=selector=>{const b=document.querySelector(selector);if(!b)throw Error('Update control missing: '+selector);b.click()};const wait=async phase=>{const deadline=Date.now()+60000;while(Date.now()<deadline){const s=await OSMINOGNative.updateState();if(s.phase==='error')throw Error(s.error);if(s.phase===phase)return s;await new Promise(r=>setTimeout(r,100))}throw Error('Update phase not reached: '+phase)};click('[data-action=updates]');await wait('available');click('[data-action=update-download]');await wait('ready');click('[data-action=update-install]');return{ok:true}}catch(e){return{ok:false,error:String(e?.message||e),stack:String(e?.stack||'')}}})()");
 assert.equal(driven?.ok,true,'Update UI path failed: '+driven?.error+'\n'+driven?.stack);
 console.log('UPDATE_UI_PATH_DRIVEN');
 const timer=setInterval(()=>{if(updates.state.phase==='error'){clearInterval(timer);console.error('UPDATE_SMOKE_FAIL '+updates.state.error);app.exit(1)}else if(updates.state.phase==='installing'){clearInterval(timer);console.log('UPDATE_INSTALL_STARTED')}},100);
 setTimeout(()=>{clearInterval(timer);console.error('UPDATE_SMOKE_TIMEOUT');app.exit(1)},90000).unref();
};
