'use strict';
globalThis.createMouseExtensionsUI=({N,showDialog,placeTab})=>{
 const $=id=>document.getElementById(id);
 const tray=$('mouse-extensions-tray'),toggle=$('mouse-extensions-button'),pins=$('mouse-extensions-pins');
 const modal=$('mouse-extensions-dialog'),list=$('mouse-extensions-list'),install=$('mouse-extensions-install'),status=$('mouse-extensions-status');
 let entries=[],busy=false,available=false,opener=null;
 const privateMode=()=>document.documentElement.dataset.private==='true';
 let observedLanguage=document.documentElement.lang,observedPrivate=privateMode();
 const copy=()=>document.documentElement.lang==='en'?{title:'Extensions',pins:'Pinned extensions',note:'Load an unpacked folder. Only compatible extensions; Chrome Web Store installation is unavailable.',install:'Load folder',empty:'No extensions installed',on:'Enable',off:'Disable',pin:'Pin',unpin:'Unpin',remove:'Remove from Mouse',error:'Could not complete the extension action.',restoreError:'Could not restore this extension. Remove it from Mouse and reinstall it from the original unpacked folder.',overflow:'More extensions'}:{title:'Расширения',pins:'Закреплённые расширения',note:'Загрузка из распакованной папки. Только совместимые расширения; установка из Chrome Web Store пока недоступна.',install:'Установить из папки',empty:'Расширений пока нет',on:'Включить',off:'Выключить',pin:'Закрепить',unpin:'Открепить',remove:'Убрать из Mouse',error:'Не удалось выполнить действие с расширением.',restoreError:'Не удалось восстановить расширение. Уберите его из Mouse и установите заново из исходной распакованной папки.',overflow:'Другие расширения'};
 const el=(tag,cls,label)=>{const x=document.createElement(tag);if(cls)x.className=cls;if(label)x.textContent=label;return x};
 const button=(text,fn)=>{const b=el('button','',text);b.type='button';b.onclick=fn;return b};
 async function run(action,args,focusId){
  if(busy||privateMode())return;busy=true;install.disabled=true;status.textContent='';
  try{const state=await N.extensions(action,args);if(privateMode())return;
   if(action==='open-page'){if(modal.open)modal.close();await placeTab?.(state);return;}
   entries=Array.isArray(state)?state:Array.isArray(state?.extensions)?state.extensions:[];
   available=true;render();if(focusId)list.querySelectorAll('.mouse-extension-row').forEach(row=>{if(row.dataset.id===focusId)row.focus()});
  }catch(e){if(!privateMode()&&action!=='state')status.textContent=copy().error;}
  finally{busy=false;install.disabled=false;}
 }
 function render(){
  const c=copy();toggle.title=c.title;toggle.setAttribute('aria-label',c.title);pins.setAttribute('aria-label',c.pins);
  $('mouse-extensions-title').textContent=c.title;$('mouse-extensions-note').textContent=c.note;install.textContent=c.install;
  tray.hidden=!available||privateMode();if(tray.hidden)return;
  pins.replaceChildren();list.replaceChildren();
  const pinned=entries.filter(e=>e.enabled&&e.pinned);
  for(const entry of pinned.slice(0,3)){
   const p=button('',()=>void (entry.actionPopup?run('open-page',{id:entry.id}):open(p,entry.id)));p.className='mouse-extension-pin';p.title=entry.name;p.setAttribute('aria-label',entry.name);
   if(typeof entry.icon==='string'&&entry.icon.length<32768&&/^data:image\/png;base64,[a-z\d+/=]+$/i.test(entry.icon)){
    const icon=el('img');icon.alt='';icon.src=entry.icon;p.append(icon);
   }else p.append(toggle.querySelector('svg').cloneNode(true));
   pins.append(p);
  }
  if(pinned.length>3){const b=button('+'+(pinned.length-3),()=>void open(b));b.title=c.overflow;pins.append(b);}
  if(!entries.length)list.append(el('p','',c.empty));
  for(const entry of entries){
   const row=el('div','mouse-extension-row');row.dataset.id=entry.id;row.dataset.state=entry.error==='load_failed'?'restore-error':entry.enabled?'enabled':'disabled';row.tabIndex=-1;
   row.append(el('strong','',entry.name+(entry.version?' · '+entry.version:'')));
   const actions=el('div','mouse-extension-actions');
   if(entry.enabled&&entry.actionPopup)actions.append(button(document.documentElement.lang==='en'?'Open page':'Открыть страницу',()=>void run('open-page',{id:entry.id})));
   actions.append(button(entry.enabled?c.off:c.on,()=>void run('set-enabled',{id:entry.id,value:!entry.enabled},entry.id)));
   const pin=button(entry.pinned?c.unpin:c.pin,()=>void run('set-pinned',{id:entry.id,value:!entry.pinned},entry.id));pin.disabled=!entry.enabled;
   actions.append(pin,button(c.remove,()=>void run('remove',{id:entry.id})));row.append(actions);
   if(row.dataset.state==='restore-error'){const message=el('p','mouse-extension-restore-error',c.restoreError);message.setAttribute('role','status');row.append(message);}
   list.append(row);
  }
 }
 async function open(from,id){
  if(!available||privateMode()||modal.open)return;opener=from;render();toggle.setAttribute('aria-expanded','true');
  try{await showDialog(modal);if(id)list.querySelectorAll('.mouse-extension-row').forEach(row=>{if(row.dataset.id===id)row.focus()});}
  catch{toggle.setAttribute('aria-expanded','false');}
 }
 toggle.onclick=()=>void open(toggle);install.onclick=()=>void run('install');
 modal.addEventListener('close',()=>{toggle.setAttribute('aria-expanded','false');(opener?.isConnected?opener:toggle).focus();opener=null;});
 new MutationObserver(()=>{
  const language=document.documentElement.lang,privateState=privateMode();
  if(language===observedLanguage&&privateState===observedPrivate)return;
  observedLanguage=language;observedPrivate=privateState;
  if(privateMode()){tray.hidden=true;if(modal.open)modal.close();}else if(available)render();else void run('state');
 }).observe(document.documentElement,{attributes:true,attributeFilter:['data-private','lang']});
 void run('state');
};
