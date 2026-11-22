'use strict';

// One isolated installed-app process for the new owner regressions. Retained
// native/profile/update suites run separately with their original deadlines.
const assert=require('node:assert/strict'),fs=require('node:fs/promises'),path=require('node:path');
const {bounded}=require('./mouse-lifecycle.cjs');
module.exports=async ctx=>{
 const {app,win}=ctx,exit=require('./mouse-smoke-exit.cjs')({app,win});
 const report={ok:false,version:app.getVersion(),platform:process.platform,arch:process.arch,pid:process.pid,
  startedAt:new Date().toISOString(),budgetMs:350000,physicalUserDeviceVerified:false,liveExternalAccountsVerified:false,stages:[]};
 let current='identity';const started=performance.now();
 const save=()=>fs.writeFile('mouse-631-native.json',JSON.stringify(report,null,2)+'\n');
 const watchdog=setTimeout(()=>{report.error={stage:current,message:'Isolated Mouse631 native process exceeded its 350 second budget'};void save().finally(()=>exit(1));},350000);
 try{
  assert.equal(process.env.CI,'true');assert.ok(path.isAbsolute(process.env.MOUSE_TEST_PROFILE||''));
  assert.equal(path.resolve(app.getPath('userData')),path.resolve(process.env.MOUSE_TEST_PROFILE));
  assert.equal(app.isPackaged,true);assert.equal(app.getVersion(),'6.0.37');assert.equal(app.getName(),'Mouse Browser');
  assert.ok((['win32','linux'].includes(process.platform)&&process.arch==='x64')||(process.platform==='darwin'&&process.arch==='arm64'));
  assert.equal(win.isVisible(),true);assert.equal(await win.webContents.executeJavaScript('document.documentElement.dataset.mouseReady'),'true');
  const shared={...ctx,nativeInput:process.platform==='win32'?require('./mouse-windows-input.cjs').createWindowsInput():process.platform==='linux'?require('./mouse-linux-input.cjs').createLinuxInput():require('./mouse-native-menu.node')};
  for(const [stage,file]of [['taskOnly','./mouse-631-task-smoke.cjs'],['fiftyTabs','./mouse-631-stress-smoke.cjs'],['stationaryMedia','./mouse-632-media-smoke.cjs']]){
   current=stage;const began=performance.now();await require(file)(shared);
   report.stages.push({name:stage,ok:true,elapsedMs:performance.now()-began});await save();
  }
  report.ok=true;report.elapsedMs=performance.now()-started;await save();
  console.log('MOUSE_631_INSTALLED_TASK_STRESS_PASS');clearTimeout(watchdog);exit(0);
 }catch(error){
  report.elapsedMs=performance.now()-started;report.error={stage:current,message:error.message,stack:error.stack};
  console.error(error);await save().catch(()=>{});
  await bounded(win.capturePage(),2000,'Mouse631 failure frame').then(image=>fs.writeFile('mouse-631-failure.png',image.toPNG())).catch(()=>{});
  clearTimeout(watchdog);exit(1);
 }
};
