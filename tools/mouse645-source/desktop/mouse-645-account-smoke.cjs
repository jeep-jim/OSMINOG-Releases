'use strict';

// Installed-app acceptance fixture. A separate Node process owns the real
// HTTP/SQLite account service, so every app.relaunch uses the normal startup
// path while the fixture server and its pinned issuer remain alive.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const fsp = require('node:fs/promises');
const path = require('node:path');
const {createHash} = require('node:crypto');

const VERSION = '6.0.45';
const FLAG = '--mouse-645-account-smoke';
const STAGE_FILE = 'mouse-645-account-stage.json';
const COOKIE = 'mouse645_profile';
const LOCAL_KEY = 'mouse645_profile';
const PRIVATE_KEY = 'mouse645PrivateFixture';
const PRIVATE_FILE = 'mouse-645-private-fixture.txt';
const PASSWORDS = Object.freeze({A: 'Mouse645 local fixture password for Alice', B: 'Mouse645 local fixture password for Boris'});
const FIXTURES = Object.freeze({
  G: {accountId: null, name: 'Mouse645 guest', theme: 'light', panes: 2, tone: 41, index: 1},
  A: {accountId: 2, name: 'Mouse645 Alice', theme: 'dark', panes: 4, tone: 67, index: 2},
  B: {accountId: 3, name: 'Mouse645 Boris', theme: 'light', panes: 6, tone: 83, index: 3}
});
const STAGES = Object.freeze([
  {index: 0, device: 1, label: 'guest-register-a', profile: null, operation: 'ack-recovery', next: 1},
  {index: 1, device: 1, label: 'account-a-write', profile: 2, operation: 'logout', next: 2},
  {index: 2, device: 1, label: 'guest-register-b', profile: null, operation: 'ack-recovery', next: 3},
  {index: 3, device: 1, label: 'account-b-write', profile: 3, operation: 'logout', next: 4},
  {index: 4, device: 1, label: 'guest-login-a', profile: null, operation: 'login', next: 5},
  {index: 5, device: 1, label: 'account-a-return', profile: 2, operation: 'logout', next: 6},
  {index: 6, device: 1, label: 'guest-final', profile: null, operation: 'finish', next: null},
  {index: 7, device: 2, label: 'second-device-login-a', profile: null, operation: 'login', next: 8},
  {index: 8, device: 2, label: 'second-device-cloud-read', profile: 2, operation: 'logout', next: 9},
  {index: 9, device: 2, label: 'second-device-guest-final', profile: null, operation: 'finish', next: null},
  {index: 10, device: 1, label: 'credential-loss-login-a', profile: null, operation: 'login', next: 11},
  {index: 11, device: 1, label: 'credential-loss-restart', profile: 2, operation: 'credential-loss-restart', next: 12},
  {index: 12, device: 1, label: 'credential-loss-clean-guest', profile: null, operation: 'finish', next: null}
]);
const sha = value => createHash('sha256').update(value).digest('hex');
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
function inside(base, value) {
  const relative = path.relative(base, value);
  return relative !== '' && relative !== '..' && !relative.startsWith('..' + path.sep) && !path.isAbsolute(relative);
}
function reportName(index, suffix = '') { return 'mouse-645-account-' + String(index).padStart(2, '0') + suffix + '.json'; }
function slotOccupancy(tree, slots = {}) {
  const leaves = require('./mouse/layout.js').leaves(tree);
  assert.ok(slots && typeof slots === 'object' && !Array.isArray(slots));
  for (const [pane, id] of Object.entries(slots)) {
    assert.ok(leaves.includes(pane), 'A slot belongs to a pane outside the actual layout');
    assert.equal(typeof id, 'string', 'A pane assignment must be a string');
  }
  // DesktopBank.liveLayout removes empty entries; renderer reconciliation
  // represents the same empty pane with ''. Compare every actual pane, while
  // preserving strict equality for all real tab assignments.
  return Object.fromEntries(leaves.map(pane => [pane, slots[pane] || '']));
}
function stateSummary(value) {
  return {available: value.available, phase: value.phase, accountId: value.accountId, name: value.name,
    recoveryPending: value.recoveryPending, touchIdAvailable: value.touchIdAvailable,
    touchIdReason: value.touchIdReason || '', touchIdEnabled: value.touchIdEnabled};
}
function pageReadback() {
  return {fixture: globalThis.mouse645AccountFixture === true, url: location.href,
    local: localStorage.getItem('mouse645_profile')};
}
function presentationReadback(scope = globalThis) {
  const model = scope.MouseTest?.model, transition = scope.MouseDesktopSlide?.last;
  const size = element => element ? Object.fromEntries(['clientWidth', 'clientHeight', 'scrollWidth', 'scrollHeight'].map(key => [key, element[key]])) : null;
  const region = selector => {
    const element = scope.document.querySelector(selector); if (!element) return null;
    const rect = element.getBoundingClientRect(), css = scope.getComputedStyle(element);
    return {bounds: Object.fromEntries(['x', 'y', 'width', 'height'].map(key => [key, rect[key]])),
      display: css.display, visibility: css.visibility, opacity: css.opacity};
  };
  const visual = scope.visualViewport, newTab = scope.document.querySelector('#new-tab');
  const before = newTab ? scope.getComputedStyle(newTab, '::before') : null;
  return {visible: scope.document.visibilityState, focused: scope.document.hasFocus(),
    rootTheme: scope.document.documentElement.dataset.theme || '',
    viewport: {innerWidth: scope.innerWidth, innerHeight: scope.innerHeight,
      visualViewport: visual ? Object.fromEntries(['width', 'height', 'offsetLeft', 'offsetTop', 'pageLeft', 'pageTop', 'scale'].map(key => [key, visual[key]])) : null},
    documentSize: size(scope.document.documentElement), bodySize: size(scope.document.body),
    regions: {toolbar: region('.toolbar'), workspace: region('#workspace'), statusbar: region('#statusbar')},
    newTab: {region: region('#new-tab'), before: before ? Object.fromEntries(['display', 'position', 'width', 'height'].map(key => [key, before[key]])) : null},
    ready: model?.ready === true, markerReady: scope.document.documentElement.dataset.mouseReady === 'true',
    switching: !!model?.switching, desktopSliding: !!model?.desktopSliding,
    desktopId: model?.desktopId || '', stateDesktopId: model?.state?.desktopId || '',
    transition: transition ? Object.fromEntries(['strategy', 'phase', 'presented', 'startedAt', 'selectedAt', 'layoutAt', 'totalDurationMs', 'layoutCalls', 'snapshotCaptures', 'borrowedHold', 'error'].map(key => [key, transition[key]])) : null,
    trayOpen: scope.document.querySelector('#desktop-tray')?.open === true,
    holdsNative: scope.MouseTest?.desktopUI?.holdsNative === true,
    trace: scope.__mouse645PresentationTrace?.read() || [],
    longTasks: scope.__mouse645PresentationTrace?.longTasks?.() || {supported: false, entries: []}};
}
function installPresentationTrace(scope = globalThis) {
  const previous = scope.__mouse631Frames, events = [], longTasks = [];
  let observer = null, supported = false;
  function observeLongTasks(entries) {
    for (const entry of entries) {
      if (longTasks.length >= 64) break;
      if (entry.entryType === 'longtask' && Number.isFinite(entry.startTime) && Number.isFinite(entry.duration)) {
        longTasks.push({startTime: entry.startTime, duration: entry.duration});
      }
    }
    if (longTasks.length >= 64) { try { observer?.disconnect(); } catch {} }
  }
  try {
    if (typeof scope.PerformanceObserver === 'function' && scope.PerformanceObserver.supportedEntryTypes?.includes('longtask')) {
      observer = new scope.PerformanceObserver(list => { try { observeLongTasks(list.getEntries()); } catch {} });
      observer.observe({type: 'longtask', buffered: false}); supported = true;
    }
  } catch { try { observer?.disconnect(); } catch {} observer = null; }
  const collector = {...previous, switchTrace: {record(phase, frameTime) {
    if (typeof phase !== 'string' || phase.length > 80) return;
    events.push({phase, at: scope.performance.now(), ...(Number.isFinite(frameTime) ? {frameTime} : {})});
    if (events.length > 256) events.shift();
  }}};
  scope.__mouse631Frames = collector;
  scope.__mouse645PresentationTrace = {read: () => events.slice(), longTasks() {
    try { if (observer) observeLongTasks(observer.takeRecords()); } catch {}
    return {supported, entries: longTasks.slice()};
  }, dispose() {
    try { observer?.disconnect(); } catch {}
    if (scope.__mouse631Frames === collector) {
      if (previous === undefined) delete scope.__mouse631Frames; else scope.__mouse631Frames = previous;
    }
    delete scope.__mouse645PresentationTrace;
  }};
  return true;
}
async function prepareAccountWindow({app, win, screen, readState, nativeDesktopId, until, frame, presentsWorkspace, report, persist}) {
  const {fixtureWindowBounds, containsRect} = require('./mouse-631-smoke-helpers.cjs');
  report.initial = {...await readState(), nativeDesktopId: nativeDesktopId()};
  if (win.isFullScreen()) { win.setFullScreen(false); await until(() => !win.isFullScreen(), 'account fixture leaves fullscreen'); }
  if (win.isMaximized()) win.unmaximize();
  if (win.isMinimized()) win.restore();
  const display = screen.getDisplayMatching(win.getBounds());
  report.geometry = {display: {id: display.id, bounds: display.bounds, workArea: display.workArea, scaleFactor: display.scaleFactor},
    minimumSize: win.getMinimumSize(), before: {window: win.getBounds(), content: win.getContentBounds()}};
  await persist();
  report.geometry.requestedBounds = fixtureWindowBounds(display.workArea, report.geometry.minimumSize);
  win.setBounds(report.geometry.requestedBounds);
  app.focus({steal: true}); win.show(); win.focus(); win.webContents.focus();
  await until(() => win.isVisible() && win.isFocused() && win.webContents.isFocused(), 'visible native account window');
  report.geometry.after = {window: win.getBounds(), content: win.getContentBounds()};
  report.geometry.zoomFactor = win.webContents.getZoomFactor();
  assert.ok(Number.isFinite(report.geometry.zoomFactor) && report.geometry.zoomFactor > 0, 'Actual shell zoom is finite and positive');
  report.geometry.expectedViewport = {innerWidth: report.geometry.after.content.width / report.geometry.zoomFactor,
    innerHeight: report.geometry.after.content.height / report.geometry.zoomFactor};
  assert.ok(containsRect(display.workArea, report.geometry.after.window) && containsRect(display.workArea, report.geometry.after.content),
    'Actual account fixture window and content fit the display work area');
  await until(async () => { report.settled = {...await readState(), nativeDesktopId: nativeDesktopId()};
    const value = report.settled;
    // CSSOM viewport sizes are integers. At the default zoom of 1 this is exact;
    // a fractional page zoom can round a native DIP size to either adjacent CSS pixel.
    const matchingViewport = ['innerWidth', 'innerHeight'].every(key => Number.isInteger(value.viewport?.[key])
      && value.viewport[key] >= Math.floor(report.geometry.expectedViewport[key])
      && value.viewport[key] <= Math.ceil(report.geometry.expectedViewport[key]));
    return value.ready && value.markerReady && !value.switching && !value.desktopSliding
      && value.desktopId === value.nativeDesktopId && value.stateDesktopId === value.nativeDesktopId
      && matchingViewport;
  }, 'ready renderer, native desktop selection and matching viewport');
  if (presentsWorkspace) await frame();
  Object.assign(report, await readState(), {frameBoundary: presentsWorkspace});
  assert.equal(report.visible, 'visible'); assert.equal(report.focused, true);
  await persist();
}
async function observeNativePresentation({probe, operation, report, timers = {setInterval, clearInterval}, now = Date.now}) {
  const maximum = 16, intervalMs = 125;
  Object.assign(report, {diagnosticOnly: true, maximum, intervalMs, samples: []});
  function sample(phase) {
    if (report.samples.length >= maximum) return false;
    const row = {phase, at: now()};
    try { row.native = probe(); } catch (error) { row.error = String(error.message || error).slice(0, 300); }
    report.samples.push(row); return true;
  }
  sample('before');
  const timer = timers.setInterval(() => { if (!sample('during')) timers.clearInterval(timer); }, intervalMs);
  try { return await operation(); }
  finally { timers.clearInterval(timer); sample('after'); }
}
function desktopSelectionSelector(target) {
  assert.match(target, /^[a-zA-Z0-9_-]{1,100}$/);
  return '.desktop-card[data-desk="' + target + '"] .desk-open';
}
function assertDesktopSelection(value, {pid, startedAt, completedAt, target}) {
  assert.equal(value?.target, target);
  assert.equal(value.before.desktopId, value.before.nativeDesktopId);
  assert.notEqual(value.before.desktopId, target);
  assert.equal(value.before.trayOpen, false);
  assert.equal(value.before.holdsNative, false);
  const selectors = ['#desktops-button', desktopSelectionSelector(target)];
  assert.equal(value.nativeInputs?.length, 2, 'Exactly two native clicks select an existing desktop');
  let previousAt = startedAt;
  for (let i = 0; i < selectors.length; i++) {
    const input = value.nativeInputs[i];
    assert.equal(input.selector, selectors[i]); assert.equal(input.action, 'click');
    assert.equal(input.source, 'CGEvent'); assert.equal(input.pid, pid); assert.equal(input.posted, true);
    assert.ok(Number.isSafeInteger(input.webContentsId) && input.webContentsId > 0);
    assert.equal(input.webContentsId, value.nativeInputs[0].webContentsId);
    assert.ok(Number.isFinite(input.at) && input.at >= previousAt && input.observedAt >= input.at && input.observedAt <= completedAt);
    previousAt = input.observedAt;
    assert.ok(Number.isFinite(input.zoom) && input.zoom > 0);
    for (const key of ['x', 'y']) {
      assert.ok(Number.isFinite(input.clientPoint[key]) && Number.isInteger(input.point[key]));
      assert.equal(input.point[key], Math.round(input.contentBounds[key] + input.clientPoint[key] * input.zoom));
    }
    assert.ok(input.clientPoint.x >= 0 && input.clientPoint.y >= 0
      && input.clientPoint.x * input.zoom < input.contentBounds.width
      && input.clientPoint.y * input.zoom < input.contentBounds.height);
    const clicks = input.events.filter(event => event.type === 'click');
    assert.equal(clicks.length, 1, 'One posted native click produces one observed click');
    const event = clicks[0];
    assert.equal(event.trusted, true); assert.equal(event.matches, true); assert.equal(event.selector, selectors[i]);
    assert.ok(event.at >= input.at && event.at <= input.observedAt);
    assert.ok(Math.abs(event.x - input.clientPoint.x) <= 2 && Math.abs(event.y - input.clientPoint.y) <= 2);
  }
  assert.equal(value.nora?.ready, true);
  for (const key of ['open', 'isOpen', 'holdsNative', 'settled']) assert.equal(value.nora[key], true);
  for (const key of ['hidden', 'inert', 'preparing']) assert.equal(value.nora[key], false);
  assert.equal(value.nora.phase, 'open');
  const after = value.after, transition = after?.transition;
  for (const key of ['desktopId', 'stateDesktopId', 'nativeDesktopId']) assert.equal(after?.[key], target);
  for (const key of ['switching', 'desktopSliding', 'trayOpen', 'holdsNative']) assert.equal(after[key], false);
  assert.equal(transition?.strategy, 'live'); assert.equal(transition.phase, 'complete');
  assert.equal(transition.presented, true); assert.equal(transition.borrowedHold, false);
  assert.equal(transition.snapshotCaptures, 0); assert.equal(transition.layoutCalls, 1);
  assert.ok(!transition.error && Number.isFinite(transition.startedAt)
    && transition.startedAt > (value.before.transition?.startedAt ?? -1)
    && transition.selectedAt >= transition.startedAt && transition.layoutAt >= transition.selectedAt
    && transition.totalDurationMs > 0);
  const frames = after.trace.filter(event => event.at >= transition.startedAt && /^present\.raf[12]$/.test(event.phase));
  assert.deepEqual(frames.map(event => event.phase), ['present.raf1', 'present.raf2']);
  assert.ok(frames[0].at >= transition.layoutAt && frames[1].at >= frames[0].at
    && frames[1].at - transition.layoutAt <= 1500
    && frames[1].at <= transition.startedAt + transition.totalDurationMs
    && Number.isFinite(frames[0].frameTime) && frames[1].frameTime > frames[0].frameTime,
  'The completed ordinary transition contains both actual animation callbacks');
  return true;
}
async function postNativeClick({selector, win, nativeInput, js, until, ledger, now = Date.now}) {
  // Reuse the retained hit-test and passive observer. Never dispatch DOM input
  // or repeat a failed click; the CGEvent must reach this exact exposed target.
  const {nativeHitTarget} = require('./mouse-smoke-hit-target.cjs');
  let hit;
  await until(async () => { hit = await js('(' + nativeHitTarget.toString() + ')(document.querySelector(' + JSON.stringify(selector) + '))');
    return hit.ready; }, 'account native hit target ' + selector);
  await js('__mouse633Input.begin(' + JSON.stringify(selector) + ')');
  const contentBounds = win.getContentBounds(), zoom = win.webContents.getZoomFactor();
  assert.ok(Number.isFinite(zoom) && zoom > 0);
  const clientPoint = {x: hit.x, y: hit.y};
  const point = {x: Math.round(contentBounds.x + hit.x * zoom), y: Math.round(contentBounds.y + hit.y * zoom)};
  const row = {selector, source: 'CGEvent', action: 'click', pid: process.pid, webContentsId: win.webContents.id,
    point, clientPoint, contentBounds, zoom, at: now(), events: [], posted: false};
  ledger.push(row);
  row.posted = await nativeInput.testClick(point.x, point.y);
  assert.equal(row.posted, true, 'A single native account-fixture click was posted');
  await until(async () => { row.events = await js('__mouse633Input.read()');
    return row.events.some(event => event.type === 'click' && event.trusted && event.matches && event.selector === selector);
  }, 'account trusted native click ' + selector);
  row.observedAt = now(); return row;
}
async function selectNativeDesktop({target, win, nativeInput, js, until, nativeDesktopId, probe, report}) {
  const {installInputProbe} = require('./mouse-633-smoke-helpers.cjs');
  const {noraReadback} = require('./mouse-639-adblock-smoke.cjs').fixtures;
  report.nativeInputs = [];
  const click = selector => postNativeClick({selector, win, nativeInput, js, until, ledger: report.nativeInputs});
  await js('(' + installInputProbe.toString() + ')()');
  try {
    await click('#desktops-button');
    await until(async () => { report.nora = await js('(' + noraReadback.toString() + ')()'); return report.nora.ready; }, 'account Nora fully open');
    report.nativePresentation = {};
    await observeNativePresentation({probe, report: report.nativePresentation, operation: async () => {
      await click(desktopSelectionSelector(target));
      await until(async () => {
        report.after = {...await js('(' + presentationReadback.toString() + ')()'), nativeDesktopId: nativeDesktopId()};
        const state = report.after, transition = state.transition;
        const fresh = transition && transition.startedAt > (report.before.transition?.startedAt ?? -1);
        // choose() reports failures through the normal status UI. Preserve that
        // failure here; a selected model/native ID alone is not presentation.
        if (fresh && transition.phase === 'failed') throw Error(transition.error || 'Native desktop presentation failed');
        return fresh && transition.phase === 'complete' && !state.switching && !state.desktopSliding
          && state.desktopId === target && state.nativeDesktopId === target && !state.trayOpen && !state.holdsNative;
      }, 'account native desktop selection');
    }});
  } finally { await js('globalThis.__mouse633Input?.dispose();true'); }
}
async function captureWriterFailure({failed, index, globalCapture, win, screen, nativeImage, output}) {
  if (!failed || ![0, 1, 3].includes(index)) return null;
  // This function is called only after the isolated installed fixture failed.
  // A display snapshot is diagnostic; it cannot satisfy presentation or retry
  // the original switch. Keep both acquisition and private output bounded.
  const {bounded} = require('./mouse-631-smoke-helpers.cjs');
  const {screenCropGeometry} = require('./mouse-628-ui-smoke.cjs');
  assert.ok(path.isAbsolute(output));
  const display = screen.getDisplayMatching(win.getBounds()), contentBounds = win.getContentBounds();
  const frame = await bounded(globalCapture.acquire(display), 4500, '645 account failure OS display');
  assert.equal(frame.kind, 'screen'); assert.ok(frame.backend);
  assert.ok(typeof frame.base === 'string' && frame.base.startsWith('data:image/png;base64,'));
  const full = Buffer.from(frame.base.slice(frame.base.indexOf(',') + 1), 'base64');
  const screenPixelSize = {width: full.readUInt32BE(16), height: full.readUInt32BE(20)};
  assert.deepEqual(win.getContentBounds(), contentBounds, 'The failed fixture did not move during display capture');
  const geometry = screenCropGeometry(display.bounds, contentBounds, screenPixelSize);
  const png = nativeImage.createFromBuffer(full).crop(geometry.cropPixels).toPNG({scaleFactor: 1});
  const pixelSize = {width: png.readUInt32BE(16), height: png.readUInt32BE(20)};
  assert.deepEqual(pixelSize, {width: geometry.cropPixels.width, height: geometry.cropPixels.height});
  const filename = 'mouse-645-account-' + String(index).padStart(2, '0') + '-failure.png';
  const displayFilename = filename.replace(/\.png$/, '-display.png');
  await bounded(Promise.all([fsp.writeFile(path.join(output, filename), png, {mode: 0o600, flag: 'wx'}),
    fsp.writeFile(path.join(output, displayFilename), full, {mode: 0o600, flag: 'wx'})]), 2500, '645 account failure PNG output');
  return {diagnosticOnly: true, afterFailure: true, source: 'globalCapture.acquire(display)', kind: frame.kind,
    backend: frame.backend, filename, displayFilename, sha256: sha(png), displaySha256: sha(full),
    screenPixelSize, pixelSize, contentBounds, capturedAt: Date.now(),
    display: {id: display.id, bounds: display.bounds, workArea: display.workArea, scaleFactor: display.scaleFactor}, ...geometry};
}

async function recordStartupGuard({app, profileContext, accountState}) {
  if (process.env.CI !== 'true' || !path.isAbsolute(process.env.MOUSE_TEST_PROFILE || '')
    || !process.argv.includes(FLAG)) return;
  const {readPrivateJSON, writePrivateJSON} = require('./mouse-profile-context.cjs');
  const staged = await readPrivateJSON(path.join(profileContext.base, STAGE_FILE), 8192);
  if (!staged || staged.index !== 12 || staged.device !== 1 || !staged.fixtureOnly) {
    throw Error('Unexpected account startup guard in the installed fixture');
  }
  const output = path.resolve(process.env.MOUSE_645_ACCOUNT_OUTPUT || '');
  assert.equal(output, staged.output); assert.ok(path.isAbsolute(staged.output));
  const marker = await readPrivateJSON(profileContext.marker, 4096);
  const value = {schema: 1, runId: staged.runId, index: 12, pid: process.pid,
    version: app.getVersion(), platform: process.platform, arch: process.arch, packaged: app.isPackaged,
    executable: process.execPath, executableSha256: sha(await fsp.readFile(process.execPath)),
    profileBase: path.resolve(profileContext.base), blockedAccountId: profileContext.active,
    selectedAccountId: marker.accountId, guestIsolated: marker.guestIsolated,
    guestGeneration: marker.guestGeneration, guestDirectory: profileContext.directoryFor(null),
    phase: accountState.phase, accountId: accountState.accountId,
    windowCount: require('electron').BrowserWindow.getAllWindows().length,
    credentialsPresent: fs.existsSync(path.join(profileContext.control, 'session.json')),
    startedAt: Date.now()};
  assert.equal(value.version, VERSION); assert.equal(value.packaged, true);
  assert.equal(value.blockedAccountId, 2); assert.equal(value.selectedAccountId, null);
  assert.equal(value.guestIsolated, true); assert.equal(value.phase, 'guest');
  assert.match(value.guestGeneration, /^[a-f0-9]{32}$/);
  assert.equal(value.guestDirectory, path.join(value.profileBase, 'mouse-guests', value.guestGeneration));
  assert.equal(value.accountId, null); assert.equal(value.windowCount, 0); assert.equal(value.credentialsPresent, false);
  process.once('exit', code => {
    try { fs.writeFileSync(path.join(output, reportName(12, '-guard-exit')), JSON.stringify({schema: 1,
      runId: staged.runId, index: 12, pid: process.pid, code, endedAt: Date.now(),
      executableSha256: value.executableSha256}) + '\n', {mode: 0o600}); } catch {}
  });
  await writePrivateJSON(path.join(output, reportName(12, '-guard')), value);
  const end = Date.now() + 18000;
  while (Date.now() < end) {
    const observed = await readPrivateJSON(path.join(output, reportName(12, '-guard-observed')), 4096);
    if (observed?.pid === process.pid && observed.runId === staged.runId) return;
    await sleep(40);
  }
  throw Error('The external coordinator did not observe the account startup guard');
}

async function smoke(ctx) {
  const {app, win, browser, store, libraryService, desktopService, profileService, accountService, accountSync, profileContext, globalCapture} = ctx;
  const {safeStorage, nativeImage, screen} = require('electron');
  const {readPrivateJSON, writePrivateJSON} = require('./mouse-profile-context.cjs');
  const {exportWorkspace} = require('./mouse-config-sync.cjs');
  const {leaves} = require('./mouse/layout.js');
  assert.equal(process.env.CI, 'true');
  assert.ok(process.argv.includes(FLAG));
  assert.equal(process.platform, 'darwin');
  assert.equal(process.arch, 'arm64');
  assert.equal(app.isPackaged, true);
  assert.equal(app.getVersion(), VERSION);
  const base = path.resolve(process.env.MOUSE_TEST_PROFILE || '');
  assert.ok(path.isAbsolute(process.env.MOUSE_TEST_PROFILE || ''));
  assert.equal(base, path.resolve(profileContext.base));
  const staged = await readPrivateJSON(path.join(base, STAGE_FILE), 8192);
  assert.ok(staged && staged.schema === 1 && staged.fixtureOnly === true && /^[a-f0-9]{32}$/.test(staged.runId));
  const spec = STAGES[staged.index];
  assert.ok(spec && spec.index === staged.index && spec.device === staged.device);
  const output = path.resolve(process.env.MOUSE_645_ACCOUNT_OUTPUT || '');
  assert.ok(path.isAbsolute(process.env.MOUSE_645_ACCOUNT_OUTPUT || ''));
  assert.equal(output, staged.output);
  for (const origin of [staged.identityOrigin, staged.browserOrigin]) {
    const u = new URL(origin);
    assert.equal(u.protocol, 'http:'); assert.equal(u.hostname, '127.0.0.1');
    assert.ok(u.port); assert.equal(u.origin, origin);
  }
  assert.equal(accountService.origin, staged.identityOrigin);
  assert.equal(sha(accountService.serverPublicKey), staged.issuerSha256);
  assert.equal(accountService.allowLoopback, true);
  const filename = path.join(output, reportName(spec.index));
  assert.equal(fs.existsSync(filename), false, 'A completed fixture stage must never run twice');
  const began = Date.now();
  const facts = {schema: 1, version: VERSION, fixtureOnly: true, physicalUserDeviceVerified: false,
    runId: staged.runId, index: spec.index, label: spec.label, device: spec.device, pid: process.pid,
    ppid: process.ppid, platform: process.platform, arch: process.arch, packaged: app.isPackaged,
    executable: process.execPath, executableSha256: sha(await fsp.readFile(process.execPath)),
    profileBase: base, userData: path.resolve(app.getPath('userData')),
    sessionStoragePath: browser.session.storagePath, guestIsolated: profileContext.guestIsolated,
    guestGeneration: profileContext.guestGeneration, guestDirectory: profileContext.directoryFor(null),
    identityOrigin: staged.identityOrigin,
    browserOrigin: staged.browserOrigin, issuerSha256: staged.issuerSha256,
    startedAt: began, completed: false, transitionRequested: false, phase: 'coordinator'};
  const save = () => writePrivateJSON(filename, facts);
  process.once('exit', code => {
    const receipt = {schema: 1, runId: facts.runId, index: spec.index, pid: process.pid, code,
      completed: facts.completed, transitionRequested: facts.transitionRequested,
      failed: !!facts.error, endedAt: Date.now(), executableSha256: facts.executableSha256};
    try { fs.writeFileSync(path.join(output, reportName(spec.index, '-exit')), JSON.stringify(receipt) + '\n', {mode: 0o600}); } catch {}
  });
  let failing = false;
  function nativePresentation() { return {...require('./mouse-native-menu.node').testWindowPresentation(), backgroundThrottling: win.webContents.getBackgroundThrottling()}; }
  async function fail(error) {
    if (failing) return; failing = true;
    // Native account errors are sanitized; assertions here never compare or
    // print a token, password, keychain secret or recovery code.
    facts.error = {phase: facts.phase, message: String(error.message || error).slice(0, 2000)};
    try { facts.presentationFailure = await js('(' + presentationReadback.toString() + ')()');
      facts.presentationFailure.native = {visible: win.isVisible(), focused: win.isFocused(), window: win.getBounds(), content: win.getContentBounds(), zoomFactor: win.webContents.getZoomFactor(), desktopId: desktopService.bank.active};
      await js('globalThis.__mouse645PresentationTrace?.dispose();true');
    } catch {}
    try { facts.nativePresentationFailure = nativePresentation(); }
    catch (cause) { facts.nativePresentationError = String(cause.message || cause).slice(0, 300); }
    try { const capture = await captureWriterFailure({failed: true, index: spec.index, globalCapture, win, screen, nativeImage, output});
      if (capture) facts.failureCapture = capture;
    } catch (cause) { facts.failureCaptureError = String(cause.message || cause).slice(0, 300); }
    facts.completed = false;
    try { await save(); } finally { console.error('MOUSE_645_ACCOUNT_NATIVE_FAIL ' + spec.label); app.exit(1); }
  }
  const watchdog = setTimeout(() => void fail(Error('Installed account stage exceeded 120 seconds')), 120000);
  async function until(check, label, maximum = 12000) {
    const end = Math.min(began + 115000, Date.now() + maximum);
    do { const result = await check(); if (result) return result; await sleep(40); } while (Date.now() < end);
    throw Error('Account fixture timeout: ' + label);
  }
  async function js(source) {
    let timeout;
    try { return await Promise.race([win.webContents.executeJavaScript(source), new Promise((_, reject) => {
      timeout = setTimeout(() => reject(Error('Account renderer request timed out')), 20000);
    })]); } finally { clearTimeout(timeout); }
  }
  const call = (action, payload = {}) => js('MouseNative.account(' + JSON.stringify(action) + ',' + JSON.stringify(payload) + ')');
  async function flush() {
    await js('MouseFlush().then(()=>true)');
    await browser.save(); await browser.saveQueue; await libraryService.flush(); await desktopService.flush();
    await browser.session.cookies.flushStore(); browser.session.flushStorageData(); await store.queue;
  }
  async function credentials(expected) {
    const file = path.join(profileContext.control, 'session.json');
    const registrationFile = path.join(profileContext.control, 'registration.json');
    if (!expected) {
      assert.equal(fs.existsSync(file), false, 'Logout must remove the native account session');
      assert.equal(fs.existsSync(registrationFile), false, 'Logout must remove unfinished registration');
      return {present: false, registrationPresent: false};
    }
    assert.equal(safeStorage.isEncryptionAvailable(), true, 'Real macOS safeStorage is required for this gate');
    const raw = await fsp.readFile(file, 'utf8'), record = JSON.parse(raw), stat = await fsp.stat(file);
    assert.equal(record.storage, 'os'); assert.equal(stat.mode & 0o777, 0o600);
    assert.equal(record.account.id, expected);
    assert.ok(typeof record.ciphertext === 'string' && record.ciphertext.length > 40);
    const secrets = [PASSWORDS.A, PASSWORDS.B, accountService.tokens?.accessToken,
      accountService.tokens?.refreshToken, accountService.recoveryKey].filter(Boolean);
    assert.ok(secrets.every(value => !raw.includes(value)), 'A secret appeared in plaintext on disk');
    const protectedValue = JSON.parse(safeStorage.decryptString(Buffer.from(record.ciphertext, 'base64')));
    assert.ok(protectedValue.accessToken === accountService.tokens?.accessToken
      && protectedValue.refreshToken === accountService.tokens?.refreshToken,
    'The real OS-protected record must restore the authenticated session');
    return {present: true, storage: 'os', permission: '0600', realSafeStorage: true,
      plaintextSecretsAbsent: true, protectedSessionMatches: true, accountId: expected,
      registrationPresent: fs.existsSync(registrationFile)};
  }
  async function page(url) {
    return until(async () => {
      const current = [...browser.tabs.values()].find(value => value.view.webContents.getURL() === url);
      if (!current || current.loading || current.error) return null;
      try { return (await current.view.webContents.executeJavaScript('globalThis.mouse645AccountFixture===true')) ? current : null; } catch { return null; }
    }, 'owned HTTP page', 18000);
  }
  async function local(expected, url) {
    const cookies = await browser.session.cookies.get({url: staged.browserOrigin, name: COOKIE});
    assert.equal(cookies.length, expected ? 1 : 0, 'Cookie partitions must remain distinct');
    if (expected) assert.equal(cookies[0].value, expected);
    const loaded = await page(url);
    const state = await loaded.view.webContents.executeJavaScript('(' + pageReadback.toString() + ')()');
    assert.equal(state.fixture, true); assert.equal(state.local, expected);
    return {cookie: cookies[0]?.value || null, localStorage: state.local,
      pageId: loaded.id, webContentsId: loaded.view.webContents.id, url: state.url};
  }
  async function privateMarker(expected) {
    const stored = (await store.get(PRIVATE_KEY))[PRIVATE_KEY] ?? null;
    const file = path.join(facts.userData, PRIVATE_FILE);
    const contents = fs.existsSync(file) ? await fsp.readFile(file, 'utf8') : null;
    assert.equal(stored, expected); assert.equal(contents, expected);
    return {store: stored, file: contents};
  }
  async function workspace() {
    await flush();
    const value = exportWorkspace(await store.get(null));
    const ui = await js('({theme:MouseTest.model.theme,appearance:MouseTest.model.appearance,preferences:MouseTest.prefs(),desktops:MouseTest.model.state.desktops})');
    assert.equal(ui.theme, value.preferences.theme);
    assert.deepEqual(ui.appearance, value.appearance);
    const desk = value.desktops.items.find(row => row.id === value.desktops.active);
    assert.deepEqual(ui.preferences.tree, desk.layout.tree);
    const occupancy = slotOccupancy(desk.layout.tree, desk.layout.slots);
    assert.deepEqual(slotOccupancy(ui.preferences.tree, ui.preferences.slots), occupancy);
    assert.equal(ui.preferences.desktopId, value.desktops.active);
    assert.ok(!JSON.stringify(value).includes(staged.runId), 'Device-local fixture content entered the sync metadata');
    return {state: value, theme: ui.theme, paneCount: leaves(desk.layout.tree).length,
      desktopName: desk.name, placedTabIds: Object.values(occupancy).filter(Boolean), rendererMatchesNative: true};
  }
  const baseline = async index => JSON.parse(await fsp.readFile(path.join(output, reportName(index)), 'utf8'));
  async function writeWorkspace(label) {
    const choice = FIXTURES[label], bank = desktopService.bank;
    const target = bank.items[choice.index].id, url = staged.browserOrigin + '/page/' + label + '/';
    facts.desktopSelection = {target, before: {...await js('(' + presentationReadback.toString() + ')()'), nativeDesktopId: bank.active}};
    await save();
    await selectNativeDesktop({target, win, nativeInput: require('./mouse-native-menu.node'), js, until,
      nativeDesktopId: () => bank.active, probe: nativePresentation, report: facts.desktopSelection});
    assertDesktopSelection(facts.desktopSelection, {pid: process.pid, startedAt: began, completedAt: Date.now(), target});
    await js('MouseNative.desktops("rename",{id:' + JSON.stringify(target) + ',name:' + JSON.stringify(choice.name + ' desktop') + '})');
    await js('MouseTest.openPage(' + JSON.stringify(url) + ',"p1")');
    const loaded = await page(url);
    const appearance = {paneMode: label === 'B' ? 'rounded' : 'square', whiteTone: choice.tone,
      tones: {whiteTemperature: choice.index * 7, blackTone: 29 + choice.index, blackTemperature: -choice.index * 4},
      surfaces: {dark: {top: {mode: 'solid', color: '#28485A', endColor: '#28485A', opacity: 100, angle: 0}}}};
    await js('(async()=>{MouseTest.changeLayout(' + choice.panes + ');MouseTest.setAppearance(' + JSON.stringify(appearance)
      + ');await MouseTest.setTheme(' + JSON.stringify(choice.theme) + ');await MouseFlush();return true;})()');
    libraryService.library.clear('bookmarks');
    libraryService.library.bookmark(staged.browserOrigin + '/bookmark/' + label, choice.name + ' bookmark');
    const value = 'fixture-' + label;
    await browser.session.cookies.set({url: staged.browserOrigin, name: COOKIE, value, path: '/',
      sameSite: 'lax', expirationDate: Math.floor(Date.now() / 1000) + 3600});
    await loaded.view.webContents.executeJavaScript('localStorage.setItem(' + JSON.stringify(LOCAL_KEY) + ',' + JSON.stringify(value) + ');true');
    const marker = 'private-fixture:' + staged.runId + ':' + label;
    await store.set({[PRIVATE_KEY]: marker}); await fsp.writeFile(path.join(facts.userData, PRIVATE_FILE), marker, {mode: 0o600});
    const result = await workspace();
    assert.equal(result.theme, choice.theme); assert.equal(result.paneCount, choice.panes);
    assert.equal(result.desktopName, choice.name + ' desktop');
    assert.equal(result.state.appearance.whiteTone, choice.tone);
    assert.deepEqual(result.state.bookmarks.map(row => [row.url, row.title]),
      [[staged.browserOrigin + '/bookmark/' + label, choice.name + ' bookmark']]);
    return {workspace: result, local: await local(value, url), privateMarker: await privateMarker(marker)};
  }
  async function verifyWorkspace(index, label, foreign = false) {
    const earlier = await baseline(index), value = await workspace();
    assert.deepEqual(value, earlier.written.workspace, 'Native settings changed across an account/profile restart');
    const expected = foreign ? null : 'fixture-' + label;
    const deviceLocal = await local(expected, staged.browserOrigin + '/page/' + label + '/');
    const marker = await privateMarker(foreign ? null : 'private-fixture:' + staged.runId + ':' + label);
    return {workspace: value, local: deviceLocal, privateMarker: marker, comparedWith: index, foreignDevice: foreign};
  }
  async function legacyPreserved() {
    const first = await baseline(0), legacy = new (require('./storage.cjs').Store)(base);
    assert.deepEqual(exportWorkspace(await legacy.get(null)), first.written.workspace.state);
    assert.equal(await fsp.readFile(path.join(base, PRIVATE_FILE), 'utf8'), first.written.privateMarker.file);
    assert.ok(typeof first.cookieStoreFile === 'string' && inside(first.sessionStoragePath, first.cookieStoreFile));
    assert.equal(fs.existsSync(first.cookieStoreFile), true);
    assert.notEqual(facts.userData, base);
    return {workspacePreserved: true, privateFilePreserved: true, cookieStorePreserved: true,
      activeDirectoryIsDifferent: true};
  }
  async function freshGuest() {
    const before = await workspace();
    assert.equal(before.state.bookmarks.length, 0);
    assert.equal(before.state.tabs.some(row => row.url.startsWith(staged.browserOrigin)), false);
    assert.equal((await browser.session.cookies.get({url: staged.browserOrigin, name: COOKIE})).length, 0);
    const marker = await privateMarker(null), url = staged.browserOrigin + '/page/C/';
    await js('MouseTest.openPage(' + JSON.stringify(url) + ')');
    return {before, workspace: await workspace(), local: await local(null, url), privateMarker: marker,
      inheritedAccountMetadata: false};
  }
  async function cleanGuest(index = 2) {
    const earlier = await baseline(index), value = await workspace();
    assert.deepEqual(value, earlier.cleanGuest.workspace);
    return {workspace: value, local: await local(null, staged.browserOrigin + '/page/C/'),
      privateMarker: await privateMarker(null), comparedWith: index};
  }
  async function dirtyGuest() {
    const loaded = await page(staged.browserOrigin + '/page/C/');
    await browser.session.cookies.set({url: staged.browserOrigin, name: COOKIE, value: 'fixture-C', path: '/',
      sameSite: 'lax', expirationDate: Math.floor(Date.now() / 1000) + 3600});
    await loaded.view.webContents.executeJavaScript('localStorage.setItem("mouse645_profile","fixture-C");true');
    const marker = 'private-fixture:' + staged.runId + ':C';
    await store.set({[PRIVATE_KEY]: marker}); await fsp.writeFile(path.join(facts.userData, PRIVATE_FILE), marker, {mode: 0o600});
    await flush();
    const cookieStoreFile = [path.join(facts.sessionStoragePath, 'Cookies'), path.join(facts.sessionStoragePath, 'Network', 'Cookies')]
      .find(file => fs.existsSync(file));
    assert.ok(cookieStoreFile && (await fsp.stat(cookieStoreFile)).size > 0);
    return {local: await local('fixture-C', staged.browserOrigin + '/page/C/'), privateMarker: await privateMarker(marker), cookieStoreFile};
  }
  async function retiredGuestPreserved() {
    const earlier = await baseline(2);
    assert.notEqual(facts.userData, earlier.userData);
    assert.equal(await fsp.readFile(path.join(earlier.userData, PRIVATE_FILE), 'utf8'), earlier.dirtyGuest.privateMarker.file);
    assert.ok(inside(earlier.sessionStoragePath, earlier.dirtyGuest.cookieStoreFile));
    assert.equal(fs.existsSync(earlier.dirtyGuest.cookieStoreFile), true);
    return {previousDirectory: earlier.userData, privateFilePreserved: true, cookieStorePreserved: true,
      activeDirectoryIsDifferent: true};
  }
  async function register(label) {
    const result = await call('register', {name: FIXTURES[label].name, password: PASSWORDS[label]});
    assert.equal(result.state.accountId, FIXTURES[label].accountId);
    assert.equal(result.state.phase, 'authenticated'); assert.equal(result.state.recoveryPending, true);
    assert.ok(typeof result.recoveryKey === 'string' && /^[A-Za-z0-9_-]{43}$/.test(result.recoveryKey));
    facts.registration = {account: stateSummary(result.state), recoveryShown: true,
      recoveryLength: result.recoveryKey.length, credentials: await credentials(FIXTURES[label].accountId)};
    // Do not store the generated recovery code in receipts or renderer storage.
    result.recoveryKey = ''; if (result.state.recoveryKey) result.state.recoveryKey = '';
  }
  async function sync() {
    await flush();
    const result = await call('sync-now');
    assert.equal(result.phase, 'authenticated');
    assert.equal(accountSync.state().phase, 'synced');
    const remote = await accountService.request('GET', '/sync');
    assert.deepEqual(remote.state, exportWorkspace(await store.get(null)));
    return {phase: accountSync.state().phase, revision: remote.revision, state: remote.state};
  }
  async function transition(payload = {}) {
    facts.presentationResult = await js('(' + presentationReadback.toString() + ')()');
    await js('globalThis.__mouse645PresentationTrace?.dispose();true');
    facts.completed = true; facts.transitionRequested = true; facts.operation = spec.operation;
    facts.next = spec.next; facts.completedAt = Date.now();
    await save();
    await writePrivateJSON(path.join(base, STAGE_FILE), {...staged, index: spec.next, previousPid: process.pid});
    console.log('MOUSE_645_ACCOUNT_TRANSITION ' + spec.index + ' ' + spec.operation);
    if (spec.operation === 'credential-loss-restart') {
      await accountSync.stop();
      await fsp.unlink(path.join(profileContext.control, 'session.json'));
      facts.credentialLoss = {ownedFixtureOnly: true, activeAccountId: profileContext.active,
        markerStillSelectsAccount: (await readPrivateJSON(profileContext.marker)).accountId === 2,
        credentials: await credentials(null)};
      await save();
      app.relaunch(); app.quit();
      return new Promise(() => {});
    }
    // onActivate/onLogout use the real app.relaunch path and may destroy the
    // requesting renderer before its IPC Promise can settle.
    void call(spec.operation, payload).catch(error => {
      if (!win.isDestroyed() && !win.webContents.isDestroyed()) void fail(error);
    });
    return new Promise(() => {});
  }
  try {
    await save();
    const acknowledgement = path.join(output, reportName(spec.index, '-observed'));
    await until(async () => {
      const value = await readPrivateJSON(acknowledgement, 4096);
      return value?.runId === facts.runId && value.pid === process.pid && value.index === spec.index;
    }, 'external coordinator observed the installed process', 18000);
    // Use the same measured work-area fit as the retained installed UI tests.
    // The default 960px app height can exceed the actual CI display work area.
    facts.presentation = {};
    // Only the three workspace writers invoke the desktop presentation path.
    // Account/state-only stages require foreground visibility, not animation.
    const presentsWorkspace = [0, 1, 3].includes(spec.index);
    await prepareAccountWindow({app, win, screen, until, report: facts.presentation, persist: save, presentsWorkspace,
      readState: () => js('(' + presentationReadback.toString() + ')()'), nativeDesktopId: () => desktopService.bank.active,
      frame: () => js('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')});
    await js('(' + installPresentationTrace.toString() + ')()');
    await save();
    facts.phase = 'verify-profile';
    assert.equal(profileContext.active, spec.profile);
    const isolatedGuest = spec.profile === null && ![0, 7].includes(spec.index);
    const expectedDirectory = spec.profile === null ? profileContext.directoryFor(null)
      : path.join(base, 'mouse-accounts', String(spec.profile));
    assert.equal(profileContext.guestIsolated, spec.profile !== null || isolatedGuest);
    if (profileContext.guestIsolated) {
      assert.match(profileContext.guestGeneration, /^[a-f0-9]{32}$/);
      assert.equal(profileContext.directoryFor(null), path.join(base, 'mouse-guests', profileContext.guestGeneration));
    } else assert.equal(profileContext.directoryFor(null), base);
    assert.equal(facts.userData, expectedDirectory); assert.equal(store.file, path.join(expectedDirectory, 'workspace.json'));
    assert.ok(typeof facts.sessionStoragePath === 'string' && inside(expectedDirectory, facts.sessionStoragePath));
    assert.equal(browser.session.isPersistent(), true);
    const state = await call('state');
    facts.account = stateSummary(state); facts.credentials = await credentials(spec.profile);
    assert.equal(state.available, true); assert.equal(state.accountId, spec.profile);
    assert.equal(state.phase, spec.profile === null ? 'guest' : 'authenticated');
    assert.equal(state.recoveryPending, false); assert.equal(state.touchIdEnabled, false);
    if (spec.profile !== null) {
      const current = accountService.snapshot();
      assert.equal(current.accountId, spec.profile);
      facts.certificate = current.certificate;
      const presentation = await profileService.state();
      assert.equal(presentation.verified, true); assert.equal(presentation.mouseId, spec.profile);
      const avatarSha256 = require('./mouse-profile.cjs').avatarHash(presentation.avatar);
      assert.equal(avatarSha256, current.certificate.claims.avatarHash);
      facts.profile = {name: presentation.name, mouseId: presentation.mouseId, verified: true, avatarSha256};
    }
    facts.phase = spec.label;
    if (spec.index === 0) {
      facts.written = await writeWorkspace('G');
      facts.cookieStoreFile = [path.join(facts.sessionStoragePath, 'Cookies'),
        path.join(facts.sessionStoragePath, 'Network', 'Cookies')].find(file => fs.existsSync(file));
      assert.ok(facts.cookieStoreFile && (await fsp.stat(facts.cookieStoreFile)).size > 0,
        'Real Chromium cookie storage must exist after its durable flush');
      const bitmap = Buffer.alloc(256 * 256 * 4);
      for (let y = 0; y < 256; y++) for (let x = 0; x < 256; x++) {
        const i = (y * 256 + x) * 4; bitmap[i] = x; bitmap[i + 1] = y;
        bitmap[i + 2] = (x + y) % 256; bitmap[i + 3] = 255;
      }
      const native = nativeImage.createFromBitmap(bitmap, {width: 256, height: 256, scaleFactor: 1});
      assert.deepEqual(native.getSize(), {width: 256, height: 256});
      const png = native.toPNG();
      const avatar = 'data:image/png;base64,' + png.toString('base64');
      await profileService.save({avatar}, profileService.epoch);
      const avatarFile = 'mouse-645-account-avatar.png';
      await fsp.writeFile(path.join(output, avatarFile), png, {mode: 0o600});
      facts.avatar = {filename: avatarFile, bytes: png.length, sha256: sha(png), width: 256, height: 256,
        encoder: 'electron.nativeImage.toPNG'};
      await register('A');
    } else if (spec.index === 1 || spec.index === 3) {
      // Registration imports only lightweight guest settings. Its Chromium
      // cookies, localStorage and files stay exclusively in the guest profile.
      facts.seeded = spec.index === 1 ? await verifyWorkspace(0, 'G', true) : await cleanGuest();
      facts.written = await writeWorkspace(spec.index === 1 ? 'A' : 'B');
      facts.sync = await sync();
      if (spec.index === 1) {
        const previous = facts.written.workspace;
        libraryService.library.bookmark(staged.browserOrigin + '/bookmark/A-final', FIXTURES.A.name + ' final bookmark');
        await js('MouseTest.setTheme("light")');
        facts.written.workspace = await workspace();
        const remote = await accountService.request('GET', '/sync');
        assert.deepEqual(remote.state, previous.state);
        assert.notDeepEqual(remote.state, facts.written.workspace.state);
        facts.logoutEdit = {editedAt: Date.now(), syncInvokedAfterEdit: false, previous,
          remoteBeforeLogout: {revision: remote.revision, state: remote.state}};
      }
    } else if (spec.index === 2) {
      facts.cleanGuest = await freshGuest(); facts.legacy = await legacyPreserved();
      facts.dirtyGuest = await dirtyGuest();
      await register('B');
    } else if ([4, 6, 12].includes(spec.index)) {
      facts.cleanGuest = await freshGuest(); facts.legacy = await legacyPreserved();
      facts.retiredGuest = await retiredGuestPreserved();
    } else if (spec.index === 10) {
      facts.restored = await cleanGuest(6); facts.legacy = await legacyPreserved();
      facts.retiredGuest = await retiredGuestPreserved();
    } else if (spec.index === 5 || spec.index === 11) {
      facts.restored = await verifyWorkspace(1, 'A');
      facts.sync = await sync();
    } else if (spec.index === 7) {
      const all = await browser.session.cookies.get({url: staged.browserOrigin, name: COOKIE});
      assert.equal(all.length, 0); facts.emptyGuest = {cookiesAbsent: true, privateMarker: await privateMarker(null)};
      facts.guestWorkspace = await workspace();
    } else if (spec.index === 8) {
      facts.restored = await verifyWorkspace(1, 'A', true);
      facts.sync = await sync();
      const devices = await call('devices');
      facts.devices = devices.devices.map(row => ({deviceId: row.deviceId, name: row.name, current: row.current === true}));
      assert.equal(facts.devices.length, 2); assert.equal(new Set(facts.devices.map(row => row.deviceId)).size, 2);
    } else if (spec.index === 9) {
      facts.cleanGuest = await freshGuest();
    }
    await flush();
    if (spec.operation !== 'finish') return await transition(spec.operation === 'login' ? {accountId: 2, password: PASSWORDS.A} : {});
    facts.presentationResult = await js('(' + presentationReadback.toString() + ')()');
    await js('globalThis.__mouse645PresentationTrace?.dispose();true');
    facts.completed = true; facts.operation = 'finish'; facts.completedAt = Date.now(); await save();
    clearTimeout(watchdog);
    console.log('MOUSE_645_ACCOUNT_DEVICE_PASS ' + spec.device);
    app.exit(0);
  } catch (error) { clearTimeout(watchdog); await fail(error); }
}

module.exports = smoke;
module.exports.constants = {VERSION, FLAG, STAGE_FILE, COOKIE, PRIVATE_KEY, PRIVATE_FILE, PASSWORDS, FIXTURES, STAGES};
module.exports.reportName = reportName;
module.exports.stateSummary = stateSummary;
module.exports.pageReadback = pageReadback;
module.exports.recordStartupGuard = recordStartupGuard;
module.exports.slotOccupancy = slotOccupancy;
module.exports.prepareAccountWindow = prepareAccountWindow;
module.exports.presentationReadback = presentationReadback;
module.exports.installPresentationTrace = installPresentationTrace;
module.exports.observeNativePresentation = observeNativePresentation;
module.exports.captureWriterFailure = captureWriterFailure;
module.exports.desktopSelectionSelector = desktopSelectionSelector;
module.exports.assertDesktopSelection = assertDesktopSelection;
module.exports.postNativeClick = postNativeClick;
module.exports.selectNativeDesktop = selectNativeDesktop;
