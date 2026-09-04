from pathlib import Path
import json
import re
import sys

root = Path(sys.argv[1])


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"{label} target missing")
    return text.replace(old, new, 1)

# 1) Shared Vision Context for every OSMINOG provider + external Presence.
p = root / "gpt-presence.js"
s = p.read_text(encoding="utf-8")
marker = '  async function maybeVisual(prompt,ctx,pinsOverride=null){'
if marker not in s:
    raise SystemExit("gpt presence visual marker missing")
start = s.index(marker)
end = s.index('\n  async function maybeProjectOverview(ctx)', start)
new_visual = r'''  /* OSMINOG 3.19.12 · SHARED VISION CONTEXT */
  async function visionSnapshotForContext(ctx,pinsOverride=null){
    if(!ctx?.intent?.visual&&!ctx?.intent?.whole)return null;
    try{
      const pins=Array.isArray(pinsOverride)?pinsOverride:pinnedContexts,pinned=pins[0],selected=ctx.selectedIds||[];
      const tool=ctx.intent.whole?"capture_canvas_overview_image":pinned?"capture_object_image":selected.length?"capture_selection_image":"capture_viewport_image";
      const args=pinned&&!ctx.intent.whole?{id:pinned.id}:{};
      if(pinned&&!pinsOverride)ghostLookAt(pinned.id,"Смотрю на закреплённый объект");
      const r=await B.executeTool?.(tool,args);
      if(!r?.image?.data)return null;
      const revision=ctx.revision||B.canvasStatus?.()?.revision||0;
      const image={kind:"image",name:ctx.intent.whole?`canvas-overview-rev-${revision}.png`:pinned?`${pinned.name||pinned.id}.png`:selected.length?`selection-rev-${revision}.png`:`viewport-rev-${revision}.png`,type:r.image.mimeType||"image/png",size:0,dataUrl:`data:${r.image.mimeType||"image/png"};base64,${r.image.data}`,auto:true};
      ctx.contextPolicy={...(ctx.contextPolicy||{}),preload:true,visionAttached:true};
      ctx.vision={protocol:"osminog.vision_context/v1",revision,source:ctx.intent.whole?"overview":pinned?"object":selected.length?"selection":"viewport",imageAttached:true,sameRevision:true,instruction:"A fresh OSMINOG canvas image from this exact project revision is attached to this user turn. Treat the image plus projectMap/viewport/selection as one visual source of truth."};
      return image;
    }catch{return null}
  }
  async function maybeVisual(prompt,ctx,pinsOverride=null){return visionSnapshotForContext(ctx,pinsOverride)}
  async function prepareExternalVisionTurn(text){
    const ctx=contextForPrompt(text,activeThread(),pinnedContexts),image=await visionSnapshotForContext(ctx,pinnedContexts);
    if(ctx?.intent?.canvas&&!ctx.vision){
      const revision=ctx.revision||B.canvasStatus?.()?.revision||0;
      ctx.contextPolicy={...(ctx.contextPolicy||{}),preload:true,visionAttached:false};
      ctx.vision={protocol:"osminog.vision_context/v1",revision,source:"structured",imageAttached:false,sameRevision:true,instruction:"Structured canvas context is attached. If pixel detail is required, request the appropriate capture tool."};
    }
    return{ok:true,context:ctx,imageDataUrl:image?.dataUrl||"",imageName:image?.name||"",vision:ctx.vision||null}
  }
  globalThis.OSMINOGVisionContext={prepare:prepareExternalVisionTurn};'''
s = s[:start] + new_visual + s[end:]
old_listener = 'chrome.runtime.onMessage.addListener((m)=>{if(m?.type==="BC_LITE_FROM_GPT")handleResult(m.payload||{});if(m?.type==="BC_LITE_EXTERNAL_USER"){const t=String(m.payload?.text||"").trim();if(t)add("user",t)}if(m?.type==="BC_PROVIDER_TAB_AVAILABLE")'
new_listener = '''chrome.runtime.onMessage.addListener((m,_sender,sendResponse)=>{if(m?.type==="BC_LITE_FROM_GPT"){handleResult(m.payload||{});return}if(m?.type==="BC_LITE_EXTERNAL_USER"){const t=String(m.payload?.text||"").trim();if(t)add("user",t);if(m.payload?.prepare===true){prepareExternalVisionTurn(t).then(r=>sendResponse?.(r)).catch(e=>sendResponse?.({ok:false,error:e?.message||String(e)}));return true}return}if(m?.type==="BC_PROVIDER_TAB_AVAILABLE")'''
s = replace_once(s, old_listener, new_listener, "external user listener")
p.write_text(s, encoding="utf-8")

# 2) External ChatGPT tab: pause the real send, ask OSMINOG for same-revision visual context,
# attach the fresh image, then send exactly once. Machine hops stay hidden.
p = root / "chatgpt-lite-bridge.js"
s = p.read_text(encoding="utf-8")
old_compact = '''  function compactContextBlock(context,requestId){\n    const payload={...context,requestId};\n    return `\\n\\n\\`\\`\\`json\\n${CTX_MARK}\\n${JSON.stringify(payload)}\\n\\`\\`\\``;\n  }'''
new_compact = '''  function compactContextBlock(context,requestId){\n    const payload={...context,requestId,assistantInstruction:machineInstructions(context)};\n    return `\\n\\n\\`\\`\\`json\\n${CTX_MARK}\\n${JSON.stringify(payload)}\\n\\`\\`\\``;\n  }'''
s = replace_once(s, old_compact, new_compact, "compact context")
old_tool = '    const safe={protocol:"osminog.tool_result/v1",requestId,result};'
new_tool = '    const safe={protocol:"osminog.tool_result/v1",requestId,result,instruction:"Continue the original user task immediately. If it is not complete, request the next OSMINOG tool hop; otherwise answer the user. Never stop at a plan or ask the user to resend the request."};'
s = replace_once(s, old_tool, new_tool, "tool result envelope")
old_decorate = '  function decoratePrompt(text,context,requestId){return `${text}\\n\\n${machineInstructions(context)}${compactContextBlock(context,requestId)}`}'
new_decorate = '  function decoratePrompt(text,context,requestId){return `${text}${compactContextBlock(context,requestId)}`}'
s = replace_once(s, old_decorate, new_decorate, "prompt decorator")
start = s.index('  function interceptManualSend(event){')
end = s.index('  document.addEventListener("keydown",interceptManualSend,true);', start)
new_intercept = r'''  /* OSMINOG 3.19.12 · SEAMLESS EXTERNAL VISION PREFLIGHT */
  async function prepareAndSendManual(composer,current){
    internalSending=true;const requestId=makeId();pendingRequestId=requestId;toolHopCount=0;setPill("busy","смотрю на OSMINOG…");
    try{
      const prep=await chrome.runtime.sendMessage({type:"BC_LITE_EXTERNAL_USER",payload:{requestId,text:current,url:location.href,prepare:true}}).catch(()=>null),ctx=prep?.context||latestContext||{};
      latestContext=ctx;setComposerText(composer,decoratePrompt(current,ctx,requestId));
      if(prep?.imageDataUrl)await attachImage(prep.imageDataUrl);
      pendingAssistantBaseline=currentAssistantHash();stableAssistantHash="";stableAssistantSince=0;sawStreamingSignal=false;requestSentAt=Date.now();
      const send=await waitSendButton();if(!send){setPill("off","не найдена кнопка отправки");return}
      send.click();setPill("busy",prep?.imageDataUrl?"холст приложен":"контекст готов");
    }finally{setTimeout(()=>{internalSending=false},450)}
  }
  function interceptManualSend(event){
    if(!enabled||!autoInject||internalSending||!latestContext)return;
    const composer=findFirst(COMPOSERS);if(!composer)return;
    const isEnter=event.type==="keydown"&&event.key==="Enter"&&!event.shiftKey;
    const send=findFirst(SENDS);const isClick=event.type==="click"&&send&&(event.target===send||send.contains(event.target));
    if(!isEnter&&!isClick)return;
    const current=composerText(composer).trim();if(!current||current.includes(CTX_MARK))return;
    event.preventDefault();event.stopImmediatePropagation();prepareAndSendManual(composer,current);
  }
'''
s = s[:start] + new_intercept + s[end:]
old_tool_send = '''      const text=`OSMINOG вернул результат инструментов. Продолжи исходную задачу немедленно. Если действие ещё не завершено фактическим изменением — запроси следующий tool hop; если завершено — дай проверенный итог. Не останавливайся на плане, обещании или фразе «начинаю» и не жди нового сообщения пользователя. Показывай только краткие этапы, без скрытых рассуждений.\\n\\n${toolResultBlock(payload.result||{},pendingRequestId)}`;'''
new_tool_send = '''      const text=toolResultBlock(payload.result||{},pendingRequestId);'''
s = replace_once(s, old_tool_send, new_tool_send, "silent tool hop")
p.write_text(s, encoding="utf-8")

# 3) Background forwards manual user-turn preflight to the live OSMINOG editor and waits for its vision payload.
p = root / "background.js"
s = p.read_text(encoding="utf-8")
old = '  if(message.type==="BC_LITE_EXTERNAL_USER"&&_sender?.tab?.id&&_sender.tab.id===bcExternalTabId){chrome.runtime.sendMessage({type:"BC_LITE_EXTERNAL_USER",payload:message.payload||{}}).catch(()=>{});sendResponse?.({ok:true});return;}'
new = '  if(message.type==="BC_LITE_EXTERNAL_USER"&&_sender?.tab?.id&&_sender.tab.id===bcExternalTabId){(async()=>{try{const prep=await chrome.runtime.sendMessage({type:"BC_LITE_EXTERNAL_USER",payload:{...(message.payload||{}),prepare:true}}).catch(()=>null);sendResponse?.(prep&&typeof prep==="object"?prep:{ok:true})}catch(e){sendResponse?.({ok:false,error:e?.message||String(e)})}})();return true;}'
s = replace_once(s, old, new, "background external preflight")
p.write_text(s, encoding="utf-8")

# 4) Browser Presence now carries a real revision heartbeat and silently reconnects to the same existing ChatGPT tab after prior opt-in.
p = root / "bridge.js"
s = p.read_text(encoding="utf-8")
s = replace_once(s, '  const STORE_KEY="briefCraftPresenceV2";', '  const STORE_KEY="briefCraftPresenceV2";\n  const EXTERNAL_AUTO_KEY="osminogExternalPresenceAutoV1";', "presence auto key")
s = replace_once(s, '    const got=await storageGet([STORE_KEY,"briefCraftPendingPatchV1","briefCraftModulesV1","osminogOwnerGrantV1"]);', '    const got=await storageGet([STORE_KEY,"briefCraftPendingPatchV1","briefCraftModulesV1","osminogOwnerGrantV1",EXTERNAL_AUTO_KEY]);', "presence storage load")
s = replace_once(s, '    store.connected=false;\n  }', '    store.connected=false;\n    const ext=got[EXTERNAL_AUTO_KEY]||{};if(ext.enabled)setTimeout(()=>reconnectExternalChatGPT(ext.role||"edit"),260);\n  }', "presence startup reconnect")
start = s.index('  function externalContext(){')
end = s.index('\n  async function pushExternalContext', start)
new_external_context = r'''  function externalContext(){
    const status=canvasStatus?.()||{},revision=status.revision||refreshMirror()?.revision||0;
    return{protocol:"osminog.browser_presence/v1",project:status.project||null,revision,selectedIds:status.selectedIds||[],view:status.view||null,counts:status.counts||{},connector:{connected:true,automatic:true,canvasContextIncluded:false,seamlessVision:true},capabilities:capabilityManifest(),externalAccess:{role:externalPresence.role||"edit",canEdit:(externalPresence.role||"edit")==="edit",canComment:true,mode:globalThis.OSMINOGOwnerGuard?.isUnlocked?.()===true?"owner-max":"interactive-edit"},contextPolicy:{preload:false,visionOnNaturalLanguage:true,instruction:"Do not guess canvas pixels. For each external user turn OSMINOG performs a preflight. When the request refers to the canvas/project/desktop/selection or asks what you see, use the same-revision structured context and attached OSMINOG vision image. If pixels are still missing, request a capture tool automatically; never ask the user to take a screenshot."},visionPolicy:{protocol:"osminog.vision_context/v1",automatic:true,sameRevision:true,triggers:["look at canvas","what do you see","посмотри на холст","что видишь","смотри на холст"],fallbackTool:"capture_viewport_image"},policy:{sourceOfTruth:"OSMINOG canvas",neverInventExistingIds:true,fullBodiesOnRequest:true,editsViaPatch:true,neverClaimEditWithoutPatch:true}}
  }'''
s = s[:start] + new_external_context + s[end:]
start = s.index('  async function connectExternalChatGPT(role="edit"){')
end = s.index('\n  async function handleExternalAssistant', start)
new_connect = r'''  async function activateExternalChatGPT(role="edit",requestPermission=false){
    const origins=["https://chatgpt.com/*","https://chat.openai.com/*"];let granted=await chrome.permissions.contains({origins}).catch(()=>false);
    if(!granted&&requestPermission)granted=await chrome.permissions.request({origins}).catch(()=>false);
    if(!granted)return{ok:false,error:"Нужно один раз разрешить OSMINOG доступ к выбранной вкладке ChatGPT."};
    externalPresence.role=["view","comment","edit"].includes(role)?role:"edit";const ctx=externalContext(),r=await chrome.runtime.sendMessage({type:"BC_EXTERNAL_CONNECT_CHATGPT",role:externalPresence.role,context:ctx}).catch(e=>({ok:false,error:e?.message||String(e)}));if(!r?.ok)return r;
    clearInterval(externalPresence.timer);externalPresence={...externalPresence,connected:true,tabId:r.tabId,lastRevision:ctx.revision};externalPresence.timer=setInterval(()=>pushExternalContext(false),850);
    await storageSet({[EXTERNAL_AUTO_KEY]:{enabled:true,role:externalPresence.role,tabId:r.tabId||null,updated:Date.now()}}).catch(()=>{});
    const detail={connected:true,role:externalPresence.role,tabId:r.tabId||null};document.dispatchEvent(new CustomEvent("osminog:external-presence",{detail}));return{...r,...detail}
  }
  async function reconnectExternalChatGPT(role="edit"){return activateExternalChatGPT(role,false)}
  async function connectExternalChatGPT(role="edit"){return activateExternalChatGPT(role,true)}'''
s = s[:start] + new_connect + s[end:]
p.write_text(s, encoding="utf-8")

# 5) Version metadata.
p = root / "manifest.json"
m = json.loads(p.read_text(encoding="utf-8"))
m["version"] = "3.19.12"
m["version_name"] = "3.19.12"
p.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

p = root / "OSMINOG_BUILD.json"
b = json.loads(p.read_text(encoding="utf-8"))
b.update({
    "version":"3.19.12","versionName":"3.19.12","build":"3.19.12",
    "codename":"SEAMLESS SHARED VISION","baseVersion":"3.19.11",
    "artifact":"OSMINOG-Chrome-3.19.12-SEAMLESS-SHARED-VISION.zip",
    "manifestVersion":"3.19.12","release":"SEAMLESS-SHARED-VISION",
    "notes":"One shared same-revision Vision Context is used by OSMINOG providers. External ChatGPT Presence preflights natural canvas requests, attaches a fresh viewport/selection/object/overview image before the turn is sent, keeps machine context/tool hops hidden, and silently reconnects to an existing previously-authorized ChatGPT tab."
})
p.write_text(json.dumps(b, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
