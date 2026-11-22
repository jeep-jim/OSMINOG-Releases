'use strict';
// Passive retained-smoke evidence. Delivery is accepted only by the caller's
// existing trusted-event predicate; a driver return is never a delivered click.
const assert=require('node:assert/strict');

function errorFacts(error){return{message:error?.message||String(error),stack:error?.stack||null};}
function diagnostic(read){try{return structuredClone(read());}catch(error){return{diagnosticError:errorFacts(error)};}}

function guestInputReadback(){
 const count=mouse634.clicks.length;
 try{return{count,documentFocused:document.hasFocus(),activeElement:{tagName:document.activeElement?.tagName||'',id:document.activeElement?.id||''}};}
 catch(error){return{count,diagnosticError:{message:error?.message||String(error)}};}
}

function nativeGuestInputState({win,page,screen,webContents}){
 const wc=page.view.webContents;
 return{
  windowBounds:diagnostic(()=>win.getBounds()),contentBounds:diagnostic(()=>win.getContentBounds()),
  cursor:diagnostic(()=>screen.getCursorScreenPoint()),
  focus:{window:diagnostic(()=>win.isFocused()),shell:diagnostic(()=>win.webContents.isFocused()),
   guest:diagnostic(()=>wc.isFocused()),webContentsId:diagnostic(()=>webContents.getFocusedWebContents()?.id??null)},
  native:{cachedBounds:diagnostic(()=>page.bounds),viewBounds:diagnostic(()=>page.view.getBounds()),
   parentBounds:diagnostic(()=>page.clipView?.getBounds()||null),visible:diagnostic(()=>page.view.getVisible()),
   parentVisible:diagnostic(()=>page.clipView?.getVisible()??true),cachedVisible:diagnostic(()=>!!page.visible),
   attached:diagnostic(()=>win.contentView.children.includes(page.clipView||page.view))},
  url:diagnostic(()=>wc.getURL()),loading:diagnostic(()=>wc.isLoadingMainFrame())
 };
}

async function observeGuestClick({attempts,details,readNative,post,readEvents,accept,waitFor,label,save}){
 const attempt={...diagnostic(()=>details),before:{at:Date.now(),native:diagnostic(readNative)},posted:null,poll:null};
 attempts.push(attempt);
 try{
  const result=await post();
  attempt.posted={at:Date.now(),result,native:diagnostic(readNative)};
  assert.equal(result,true);
  let events;
  // No save/IPC/extra wait between the original driver call and original wait.
  await waitFor(async()=>{
   events=await readEvents();attempt.poll={at:Date.now(),events:diagnostic(()=>events)};
   return accept(events);
  },label);
  return events;
 }catch(error){
  attempt.error=errorFacts(error);attempt.failedNative={at:Date.now(),native:diagnostic(readNative)};
  try{await save();}catch(saveError){attempt.diagnosticSaveError=errorFacts(saveError);}
  throw error;
 }
}

module.exports={guestInputReadback,nativeGuestInputState,observeGuestClick};
