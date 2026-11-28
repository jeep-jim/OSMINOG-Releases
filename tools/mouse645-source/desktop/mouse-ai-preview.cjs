'use strict';
const {sameSite}=require('./mouse-page-interactions.cjs').createPageInteractionTools();

// A right-hand chat owns one lower preview. The native pages and their session
// remain independent; following another link reuses the same preview page.
function outboundNavigation(parent, next) {
 if (parent?.lane !== 'side' || parent.previewOf || parent.provider) return false;
 try {
  const target = new URL(next), current = new URL(parent.view.webContents.getURL() || parent.url);
  return ['http:', 'https:'].includes(target.protocol) && !sameSite(target.href,current.href);
 } catch { return false; }
}

function createPreviewRouter({ browser, bank, open, navigate, discard, persist }) {
 const pending = new Map();
 const valid = page => !browser.disposed && browser.tabs.get(page?.id) === page &&
  !!bank.members[page.id] && !page.view.webContents.isDestroyed?.();
 async function route(parent, url) {
  if (!valid(parent)) return null;
  const source = parent.previewOf ? browser.tabs.get(parent.previewOf) : parent;
  const currentSource = () => valid(source) && source.lane === 'side' && !source.previewOf &&
   valid(parent) && (parent === source || parent.previewOf === source.id && parent.lane === 'side') &&
   bank.members[parent.id] === bank.members[source.id];
  if (!currentSource()) return null;
  const previous = pending.get(source.id) || Promise.resolve();
  const work = previous.catch(() => {}).then(async () => {
   if (!currentSource()) return null;
   const desk = bank.members[source.id];
   let preview = [...browser.tabs.values()].find(page => page.previewOf === source.id &&
    bank.members[page.id] === desk && valid(page));
   let created = null;
   const currentPair = () => currentSource() && valid(preview) && preview.lane === 'side' &&
    preview.previewOf === source.id && bank.members[preview.id] === bank.members[source.id];
   const cancel = async () => {
    // Never close an existing page or one the user has detached while this
    // asynchronous request was in flight. Only this request's new child is ours.
    if (created && !browser.disposed && browser.tabs.get(created.id) === created &&
     created.previewOf === source.id && created.lane === 'side') {
     await discard(created.id);
     await persist();
    }
    return null;
   };
   try {
    if (preview) await navigate(preview.id, url);
    else {
     const result = await open(desk, { url, lane: 'side', previewOf: source.id });
     preview = browser.tabs.get(result?.id);created = preview;
    }
    if (!currentPair()) return cancel();
    await persist();
    if (!currentPair()) return cancel();
    browser.emit();
    return { id: preview.id, sourceId: source.id, desk: bank.members[source.id] };
   } catch (error) {
    if (!currentSource() || preview && !currentPair()) return cancel();
    throw error;
   }
  });
  pending.set(source.id, work);
  try { return await work; }
  finally { if (pending.get(source.id) === work) pending.delete(source.id); }
 }
 return { route, outboundNavigation };
}

module.exports = { createPreviewRouter, outboundNavigation };
