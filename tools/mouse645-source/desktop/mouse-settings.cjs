'use strict';
const KEY='mouseControlSettings';
const DEFAULTS=Object.freeze({showBrandName:true,showFavicons:true,desktopGestures:true,downloadBounce:true,downloadBadge:true,blockAds:false,syncWebsiteTheme:true});
function normalize(value){const out={...DEFAULTS};if(value&&typeof value==='object')for(const key of Object.keys(out))if(typeof value[key]==='boolean')out[key]=value[key];return out;}
function patch(value){if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).length===0)throw Error('Некорректные настройки');for(const [key,enabled]of Object.entries(value))if(!Object.hasOwn(DEFAULTS,key)||typeof enabled!=='boolean')throw Error('Неизвестная настройка');return{...value};}
async function install({store,win,ipcMain,trusted,isPrivate=()=>false,onChange}){
 let values=normalize((await store.get(KEY))[KEY]),queue=Promise.resolve();
 const state=()=>({...values,privateMode:!!isPrivate()});
 ipcMain.handle('mouse:settings',async(event,action,args)=>{
  trusted(event);if(action==='state')return state();if(action!=='set')throw Error('Неизвестная команда настроек');
  if(isPrivate())throw Error('Постоянные настройки меняются в обычном режиме');const changes=patch(args);
  const work=queue.catch(()=>{}).then(async()=>{
   if(isPrivate())throw Error('Режим приватности изменён');
   const next={...values,...changes};await store.set({[KEY]:next});values=next;
   // Persistence is already committed: an observer failure cannot roll it back.
   let applyFailed=false;try{await onChange?.({...values});}catch{applyFailed=true;}
   if(!win.isDestroyed()){
    win.webContents.send('mouse:settings-state',state());
    if(applyFailed)win.webContents.send('browser:error','Настройки сохранены, но не удалось применить их. Перезапустите Mouse Browser.');
   }
   return state();
  });queue=work.then(()=>{},()=>{});return work;
 });
 return{state,flush:()=>queue};
}
module.exports={KEY,DEFAULTS,normalize,patch,install};
