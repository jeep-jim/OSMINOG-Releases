'use strict';

// Shared by the native client and the account service. This is deliberately a
// closed schema, not a backup of workspace.json or Chromium/localStorage.
const L = require('./mouse/layout.js');
const A = require('./mouse/appearance.js');
const {isDeepStrictEqual} = require('node:util');
const MAX_BYTES = 2 * 1024 * 1024;
const SETTINGS = ['showBrandName','showFavicons','desktopGestures','downloadBounce','downloadBadge','blockAds','syncWebsiteTheme'];
const ID = /^[a-zA-Z0-9_-]{1,100}$/;
const TAB = /^[a-f0-9-]{36}$/;
const plain = x => !!x && typeof x === 'object' && !Array.isArray(x) && [Object.prototype,null].includes(Object.getPrototypeOf(x));
function bad() { const e = Error('Недопустимые данные синхронизации Mouse'); e.code = 'SYNC_FORMAT'; throw e; }
function shape(value, required, optional = []) {
  if (!plain(value) || required.some(k => !Object.hasOwn(value,k)) || Object.keys(value).some(k => !required.includes(k) && !optional.includes(k))) bad();
}
function text(value, max, empty = false) {
  if (typeof value !== 'string' || value.length > max || (!empty && !value.trim()) || /[\u0000-\u001f\u007f]/.test(value)) bad();
  return value;
}
function id(value, tab = false) { if (!(tab ? TAB : ID).test(value) || typeof value !== 'string' || ['__proto__','constructor','prototype'].includes(value)) bad(); return value; }
function number(value, min, max) { if (!Number.isFinite(value) || value < min || value > max) bad(); return value; }
function bool(value) { if (typeof value !== 'boolean') bad(); return value; }
// OAuth responses and signed object URLs carry access in the URL itself:
// https://www.rfc-editor.org/rfc/rfc6749.html#section-4.1.2
// https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_sigv-authentication-methods.html
// https://cloud.google.com/storage/docs/access-control/signed-urls
// https://learn.microsoft.com/rest/api/storageservices/create-service-sas
const CREDENTIAL_PARAMETER=/^(?:access[_-]?token|refresh[_-]?token|id[_-]?token|token|bearer|password|passwd|secret|client[_-]?secret|authorization|auth[_-]?token|session[_-]?token|api[_-]?key|code[_-]?verifier|device[_-]?code|user[_-]?code|oauth[_-]?(?:token|verifier)|samlresponse|samlart|assertion|signature|sig|awsaccesskeyid|googleaccessid|x-amz-(?:credential|signature|security-token)|x-goog-(?:credential|signature))$/i;
function credentialURL(u) {
  const hash=u.hash.slice(1),question=hash.indexOf('?');
  const groups=[u.searchParams,new URLSearchParams(hash)];
  if(question>=0)groups.push(new URLSearchParams(hash.slice(question+1)));
  const keys=new Set(groups.flatMap(params=>[...params.keys()].map(key=>key.toLowerCase())));
  if([...keys].some(key=>CREDENTIAL_PARAMETER.test(key)))return true;
  let route=u.pathname+'/'+(question>=0?hash.slice(0,question):'');try{route=decodeURIComponent(route);}catch{}
  const callback=/(?:^|\/)(?:oauth2?|oidc|auth|authorize|authorization|callback|cb|login|signin(?:-oidc|-oauth)?)(?:\/|$)/i.test(route);
  return keys.has('code')&&(callback||['state','session_state','iss','client_id','redirect_uri'].some(key=>keys.has(key)));
}
function safeURL(value, internal = false) {
  text(value,8192);
  if (internal && ['about:blank','mouse://start'].includes(value)) return value;
  let u; try { u = new URL(value); } catch { bad(); }
  if (!['https:','http:'].includes(u.protocol) || u.username || u.password) bad();
  // Authentication callback URLs are device-local login material, not workspace
  // metadata. A normal URL remains intact; a known credential URL is excluded.
  if (credentialURL(u)) bad();
  return u.href;
}
function maybeURL(value, internal = false) { try { return safeURL(value,internal); } catch { return ''; } }
function list(value, limit) { if (!Array.isArray(value) || value.length > limit) bad(); return value; }
function unique(rows, key) { const seen = new Set(); for (const row of rows) { const v = key(row); if (seen.has(v)) bad(); seen.add(v); } return rows; }
function layout(value) {
  shape(value,['tree','slots','active','tabOrder','aiOpen','aiWidth','aiId','aiSessions','mode'],['pinnedPanes','aiPreviewRatio','presetTabs']);
  let tree; try { tree = L.validate(value.tree); } catch { bad(); }
  if (!isDeepStrictEqual(tree,value.tree)) bad();
  const panes = new Set(L.leaves(tree)), slots = {}, pinnedPanes = {}, aiSessions = {}, presetTabs = {};
  if (!plain(value.slots) || Object.keys(value.slots).length > 12) bad();
  for (const [pane,tab] of Object.entries(value.slots)) { if (!panes.has(pane)) bad(); slots[pane] = tab === '' ? '' : id(tab,true); }
  if (value.pinnedPanes !== undefined) {
    if (!plain(value.pinnedPanes) || Object.keys(value.pinnedPanes).length > 12) bad();
    for (const [pane,tab] of Object.entries(value.pinnedPanes)) { if (!panes.has(pane) || (slots[pane] || '') !== tab) bad(); pinnedPanes[pane] = tab === '' ? '' : id(tab,true); }
  }
  if (!panes.has(value.active)) bad();
  const tabOrder = unique(list(value.tabOrder,1000).map(x => id(x,true)),x => x);
  if (!plain(value.aiSessions) || Object.keys(value.aiSessions).length > 30) bad();
  for (const [url,tab] of Object.entries(value.aiSessions)) aiSessions[safeURL(url)] = id(tab,true);
  if (value.presetTabs !== undefined) {
    if (!plain(value.presetTabs) || Object.keys(value.presetTabs).length > 30) bad();
    for (const [mode,tabs] of Object.entries(value.presetTabs)) presetTabs[id(mode)] = list(tabs,12).map(x => x === '' ? '' : id(x,true));
  }
  const out = {tree,slots,active:value.active,tabOrder,aiOpen:bool(value.aiOpen),aiWidth:number(value.aiWidth,240,1600),aiId:value.aiId === '' ? '' : id(value.aiId,true),aiSessions,mode:text(value.mode,100,true)};
  if (Object.keys(pinnedPanes).length) out.pinnedPanes = pinnedPanes;
  if (value.aiPreviewRatio !== undefined) out.aiPreviewRatio = number(value.aiPreviewRatio,.1,.9);
  if (Object.keys(presetTabs).length) out.presetTabs = presetTabs;
  return out;
}
function appearance(value) {
  shape(value,['paneMode','whiteTone'],['surfaces','tones']);
  if (!['rounded','square'].includes(value.paneMode) || !Number.isInteger(value.whiteTone)) bad();
  number(value.whiteTone,0,100);
  if (value.tones !== undefined) {
    shape(value.tones,[],['whiteTemperature','blackTone','blackTemperature']);
    if (!A.validTones(value.tones)) bad();
  }
  if (value.surfaces !== undefined) {
    shape(value.surfaces,[],['light','dark']);
    for (const theme of Object.keys(value.surfaces)) {
      shape(value.surfaces[theme],[],['top','bottom','workspace']);
      for (const s of Object.values(value.surfaces[theme])) {
        shape(s,['mode','color','endColor','angle','opacity']);
        if (!['solid','gradient'].includes(s.mode) || !/^#[a-fA-F0-9]{6}$/.test(s.color) || !/^#[a-fA-F0-9]{6}$/.test(s.endColor) || !Number.isInteger(s.angle) || !Number.isInteger(s.opacity)) bad();
        number(s.angle,0,359); number(s.opacity,0,100);
      }
    }
  }
  return A.normalize(value);
}
function validateSyncState(value) {
  if (Buffer.byteLength(JSON.stringify(value),'utf8') > MAX_BYTES) bad();
  shape(value,['schema','desktops','tabs','bookmarks','preferences','appearance','settings'],['start','search','zoom','layoutAlternatives']);
  if (value.schema !== 1) bad();
  shape(value.desktops,['active','items','members']);
  const tabs = unique(list(value.tabs,1000).map(t => {
    shape(t,['id','url','lane']); if (!['main','side'].includes(t.lane)) bad();
    return {id:id(t.id,true),url:safeURL(t.url,true),lane:t.lane};
  }),t => t.id), tabIds = new Set(tabs.map(t => t.id));
  const items = unique(list(value.desktops.items,18).map(d => { shape(d,['id','name','layout']); return {id:id(d.id),name:text(d.name,60),layout:layout(d.layout)}; }),d => d.id);
  if (!items.length || !items.some(d => d.id === value.desktops.active)) bad();
  if (!plain(value.desktops.members) || Object.keys(value.desktops.members).length > 1000) bad();
  const members = {}, deskIds = new Set(items.map(d => d.id));
  for (const [tab,desk] of Object.entries(value.desktops.members)) { if (!tabIds.has(tab) || !deskIds.has(desk)) bad(); members[tab] = desk; }
  for (const tab of tabs) if (!members[tab.id]) bad();
  for (const d of items) {
    const assigned = tab => !tab || members[tab] === d.id;
    if (![...Object.values(d.layout.slots),...d.layout.tabOrder,d.layout.aiId,...Object.values(d.layout.aiSessions),...Object.values(d.layout.presetTabs || {}).flat()].every(assigned)) bad();
  }
  const bookmarks = unique(list(value.bookmarks,10000).map(b => {
    shape(b,['id','url','title','at']); if (!Number.isSafeInteger(b.at)) bad();
    return {id:id(b.id),url:safeURL(b.url),title:text(b.title,500,true),at:number(b.at,0,Number.MAX_SAFE_INTEGER)};
  }),b => b.id);
  shape(value.preferences,['theme','locale','libraryWidth','settingsWidth','aiSites'],['flashWidth']);
  const p=value.preferences; if (!['light','dark','system'].includes(p.theme) || !['ru','en'].includes(p.locale)) bad();
  const preferences={theme:p.theme,locale:p.locale,libraryWidth:number(p.libraryWidth,300,1600),settingsWidth:number(p.settingsWidth,340,1600),aiSites:list(p.aiSites,12).map(s => {shape(s,['name','url']);return {name:text(s.name,100),url:safeURL(s.url)};})};
  if (p.flashWidth !== undefined) preferences.flashWidth = number(p.flashWidth,300,1600);
  shape(value.settings,SETTINGS); const settings={}; for(const key of SETTINGS) settings[key]=bool(value.settings[key]);
  const out={schema:1,desktops:{active:value.desktops.active,items,members},tabs,bookmarks,preferences,appearance:appearance(value.appearance),settings};
  if(value.start !== undefined){shape(value.start,['background','showRecent']);if(!['dusk','sea','aurora','plain'].includes(value.start.background))bad();out.start={background:value.start.background,showRecent:bool(value.start.showRecent)};}
  if(value.search !== undefined){shape(value.search,['engine']);if(!['google','yandex','bing','duckduckgo'].includes(value.search.engine))bad();out.search={engine:value.search.engine};}
  if(value.zoom !== undefined)out.zoom=number(value.zoom,.25,5);
  if(value.layoutAlternatives!==undefined)out.layoutAlternatives=unique(list(value.layoutAlternatives,30).map(x=>{shape(x,['id','desktopId','layout']);if(!deskIds.has(x.desktopId))bad();return{id:id(x.id),desktopId:x.desktopId,layout:layout(x.layout)};}),x=>x.id);
  if(Buffer.byteLength(JSON.stringify(out),'utf8')>MAX_BYTES)bad();return out;
}
module.exports={MAX_BYTES,SETTINGS,validateSyncState,maybeURL,safeURL,layout,appearance};
