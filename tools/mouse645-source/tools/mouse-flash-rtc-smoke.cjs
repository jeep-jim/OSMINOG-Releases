'use strict';
// macOS Electron acceptance: two real sandboxed production Flash windows, no mocked RTC channel.
const electron = require('electron');
const {app} = electron;
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const {FlashService} = require('../desktop/mouse-flash.cjs');
const {loadIdentity} = require('../desktop/mouse-flash-identity.cjs');
const {createFlashBroker} = require('./mouse-flash-broker.cjs');
const {startStunService} = require('./mouse-flash-stun-service.cjs');
const root = path.resolve(process.env.MOUSE_FLASH_SMOKE_ROOT || path.join(os.tmpdir(), 'mouse-flash-rtc-' + crypto.randomBytes(6).toString('hex')));
const evidence = path.resolve(process.env.MOUSE_FLASH_EVIDENCE || path.join(root, 'evidence'));
app.setPath('userData', path.join(root, 'electron-profile'));
// Reopening both devices is part of this test; only main() decides the exit status.
app.on('window-all-closed', () => {});
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const testKey = crypto.randomBytes(32); // Only test identities use this ephemeral test protector.
const protect = text => { const iv = crypto.randomBytes(12), cipher = crypto.createCipheriv('aes-256-gcm', testKey, iv); return Buffer.concat([iv, cipher.update(text, 'utf8'), cipher.final(), cipher.getAuthTag()]); };
const unprotect = bytes => { const decipher = crypto.createDecipheriv('aes-256-gcm', testKey, bytes.subarray(0, 12)); decipher.setAuthTag(bytes.subarray(-16)); return Buffer.concat([decipher.update(bytes.subarray(12, -16)), decipher.final()]).toString('utf8'); };
let broker, stun, origin, host, join, savedFolder, totalBytes, manifest, sourceIdentity, joinIdentity;
const receipt = {schema: 1, platform: process.platform, architecture: process.arch, electron: process.versions.electron,
  realRTCDataChannel: true, sandbox: true, nodeIntegration: false, contextIsolation: true, noRelay: true,
  fixture: '48 MiB + 173 bytes, a text file, an empty file and empty directory; not a terabyte test', checks: []};
const check = (name, detail = {}) => { receipt.checks.push({name, ...detail}); console.log('PASS ' + name); };
function bounded(promise, label, milliseconds = 15000) {
  let timer; const expiry = new Promise((_resolve, reject) => { timer = setTimeout(() => reject(new Error(label + ' timed out')), milliseconds); });
  return Promise.race([promise, expiry]).finally(() => clearTimeout(timer));
}
const run = (service, code) => bounded(service.window.webContents.executeJavaScript(code, true), 'Renderer test command');
async function waitFor(label, test, timeout = 45000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) { const value = await test(); if (value) return value; await delay(50); }
  const errors = await Promise.all([host, join].map(async service => service?.window && !service.window.isDestroyed() ? run(service, "document.getElementById('error').hidden?'':document.getElementById('error').textContent").catch(() => '') : ''));
  throw new Error(label + ' timed out. ' + errors.filter(Boolean).join(' / ').slice(0, 600));
}
async function click(service, id) { return run(service, `document.getElementById(${JSON.stringify(id)}).click()`); }
async function checked(service, id) { return run(service, `document.getElementById(${JSON.stringify(id)}).checked=true;document.getElementById(${JSON.stringify(id)}).dispatchEvent(new Event('change',{bubbles:true}))`); }
async function revealConnection(service) {
  await run(service, "(async()=>{const panel=document.getElementById('connection-panel');panel.scrollIntoView({block:'start',behavior:'instant'});await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));const r=panel.getBoundingClientRect();if(panel.hidden||r.top < -1||r.top > innerHeight-40)throw Error('Connection result is outside the captured viewport');})()");
}
const observeRTC = `(()=>{
 const Original=globalThis.RTCPeerConnection;globalThis.__flashRTC={pcs:[],channels:[],sentBinaryBytes:0,maxMessageBytes:0,maxBufferedBytes:0};
 function observe(channel){if(globalThis.__flashRTC.channels.includes(channel))return;globalThis.__flashRTC.channels.push(channel);const send=channel.send.bind(channel);channel.send=value=>{const size=typeof value==='string'?new TextEncoder().encode(value).length:value.byteLength;globalThis.__flashRTC.maxMessageBytes=Math.max(globalThis.__flashRTC.maxMessageBytes,size);if(typeof value!=='string')globalThis.__flashRTC.sentBinaryBytes+=size;send(value);globalThis.__flashRTC.maxBufferedBytes=Math.max(globalThis.__flashRTC.maxBufferedBytes,channel.bufferedAmount);};}
 globalThis.RTCPeerConnection=class extends Original{constructor(...args){super(...args);globalThis.__flashRTC.pcs.push(this);this.addEventListener('datachannel',event=>observe(event.channel));}createDataChannel(...args){const channel=super.createDataChannel(...args);observe(channel);return channel;}};
})();`;
async function makeService(role) {
  console.log('PHASE open ' + role + ' window');
  const directory = path.join(root, role);
  const identity = await loadIdentity({directory: path.join(directory, 'identity'), name: role === 'host' ? 'Mac отправителя (тест)' : 'Mac получателя (тест)', protect, unprotect});
  const service = new FlashService({electron, directory, broker: origin, stunServers: [stun.url], allowLoopback: true, identity,
    choosePaths: async kind => ({canceled: false, filePaths: kind === 'source' ? [path.join(root, 'source', 'Photos')] : [savedFolder || path.join(root, 'received')]}),
    beforeLoad: async win => {
      const preferences = win.webContents.getLastWebPreferences();
      assert.equal(preferences.sandbox, true); assert.equal(preferences.nodeIntegration, false); assert.equal(preferences.contextIsolation, true);
      // CDP commands need a live initial frame. Awaiting Page.enable before the first navigation can stall Electron.
      await bounded(win.loadURL('about:blank'), 'Initial observation frame');
      win.webContents.debugger.attach('1.3');
      await bounded(win.webContents.debugger.sendCommand('Page.enable'), 'Enable RTC observation');
      await bounded(win.webContents.debugger.sendCommand('Page.addScriptToEvaluateOnNewDocument', {source: observeRTC}), 'Install RTC observation');
    }
  });
  await service.open();
  console.log('PHASE loaded ' + role + ' window');
  service.testCounts = {readBytes: 0, committedBytes: 0, offsets: []};
  const files = service.context.files;
  const read = files.readBlock.bind(files); files.readBlock = async args => { const value = await read(args); service.testCounts.readBytes += value.data.length; service.testCounts.offsets.push({id: args.fileId, offset: args.offset}); return value; };
  const write = files.writeBlock.bind(files); files.writeBlock = async args => { await delay(20); const value = await write(args); service.testCounts.committedBytes += args.data.length; return value; };
  await waitFor(role + ' UI ready', () => run(service, "!!document.getElementById('local-device').textContent && !document.getElementById('choose-source').disabled"));
  console.log('PHASE ready ' + role + ' window');
  return service;
}
async function connect(resume) {
  console.log('PHASE connect ' + (resume ? 'resume' : 'initial'));
  if (resume) await run(host, "document.querySelector('#resumable-list button').click()");
  else await click(host, 'choose-source');
  await waitFor('source selection', () => run(host, "!document.getElementById('source-summary').hidden && !document.getElementById('create-invite').disabled"));
  const source = [...host.context.files.sources.values()][0];
  if (!manifest) manifest = source.manifest; else assert.equal(source.manifest.transferId, manifest.transferId);
  await click(host, 'create-invite');
  const invitation = await waitFor('one-time invitation', () => run(host, "document.getElementById('invite-text').value"));
  await click(join, 'receive-mode');
  await run(join, `document.getElementById('join-text').value=${JSON.stringify(invitation)};document.getElementById('join-text').dispatchEvent(new Event('input',{bubbles:true}))`);
  await click(join, 'join');
  await waitFor('mutual authenticated RTC handshake', async () => (await run(host, "!document.getElementById('peer-panel').hidden")) && (await run(join, "!document.getElementById('peer-panel').hidden")));
  const a = await run(host, "document.getElementById('sas').textContent"), b = await run(join, "document.getElementById('sas').textContent");
  assert.ok(a.length >= 16); assert.equal(a, b);
  assert.equal(host.testCounts.readBytes, 0); assert.equal(join.testCounts.committedBytes, 0);
  assert.equal(await run(join, "document.getElementById('incoming-panel').hidden"), true);
  const stats = await run(host, `(async()=>{const result=[];for(const pc of __flashRTC.pcs){const stats=await pc.getStats();for(const item of stats.values())if(item.type==='candidate-pair'&&item.state==='succeeded'&&item.nominated){result.push({local:stats.get(item.localCandidateId)?.candidateType,remote:stats.get(item.remoteCandidateId)?.candidateType,state:pc.connectionState});}}return result;})()`);
  assert.ok(stats.length > 0); assert.ok(stats.every(item => item.state === 'connected' && item.local && item.remote && item.local !== 'relay' && item.remote !== 'relay'));
  check(resume ? 'fresh handshake after reopening both device stores' : 'actual RTC handshake, matching code, device proofs, direct candidate pair', {candidateTypes: stats});
  await checked(host, 'confirm-code'); await click(host, 'approve-host');
  await waitFor('receiver manifest approval', () => run(join, "!document.getElementById('incoming-panel').hidden"));
  assert.equal(host.testCounts.readBytes, 0); assert.equal(join.testCounts.committedBytes, 0);
  check('no file contents before receiver approval', {resume});
}
async function accept(resume) {
  if (resume) { assert.equal(await run(join, "document.getElementById('resume-option').hidden"), false); await checked(join, 'resume-receive'); }
  await checked(join, 'confirm-code'); await click(join, 'approve-receiver');
}
async function makeFixture() {
  await fs.mkdir(path.join(root, 'source', 'Photos', 'nested', 'empty'), {recursive: true}); await fs.mkdir(path.join(root, 'received'), {recursive: true}); await fs.mkdir(evidence, {recursive: true});
  const file = await fs.open(path.join(root, 'source', 'Photos', 'gallery.bin'), 'wx');
  const block = crypto.randomBytes(1048576);
  try { for (let i = 0; i < 48; i++) await file.write(block); await file.write(block.subarray(0, 173)); await file.sync(); } finally { await file.close(); }
  await fs.writeFile(path.join(root, 'source', 'Photos', 'nested', 'note.txt'), 'Mouse Flash — проверка прямой передачи\n');
  await fs.writeFile(path.join(root, 'source', 'Photos', 'empty.bin'), '');
  totalBytes = 48 * 1048576 + 173 + Buffer.byteLength('Mouse Flash — проверка прямой передачи\n');
}
async function sha(filename) { const handle = await fs.open(filename); const hash = crypto.createHash('sha256'); try { for await (const chunk of handle.createReadStream()) hash.update(chunk); return hash.digest('hex'); } finally { await handle.close(); } }
async function main() {
  assert.equal(process.platform, 'darwin', 'This acceptance must run on a real macOS runner.');
  await makeFixture(); broker = createFlashBroker(); origin = await broker.listen({port: 0, host: '127.0.0.1'});
  const discovery = await startStunService({hosts: ['127.0.0.1'], port: 0});
  stun = {url: discovery.urls[0], close: discovery.close}; receipt.discoveryImplementation = 'production bounded STUN Binding, loopback binding for this test';
  console.log('PHASE bounded STUN and local broker ready');
  host = await makeService('host'); join = await makeService('join');
  sourceIdentity = host.context.identity.identity.deviceId; joinIdentity = join.context.identity.identity.deviceId;
  await connect(false); await accept(false);
  console.log('PHASE accepted initial transfer');
  await waitFor('at least four durable MiB', () => join.testCounts.committedBytes >= 4 * 1048576);
  savedFolder = [...join.context.files.receivers.values()][0].folder;
  await revealConnection(join);
  await fs.writeFile(path.join(evidence, 'flash-receiving.png'), (await bounded(join.window.webContents.capturePage(), 'Receiving screenshot')).toPNG());
  await click(host, 'pause');
  await waitFor('both UI sessions paused', async () => !host.context.files.sources.size && !join.context.files.receivers.size);
  const saved = JSON.parse(await fs.readFile(path.join(root, 'join', 'transfers', manifest.transferId + '.receive.json'), 'utf8'));
  const rows = (await fs.readFile(path.join(saved.folder, '.mouse-flash-partials', 'blocks.jsonl'), 'utf8')).trim().split('\n').filter(Boolean).map(JSON.parse);
  const durableBytes = rows.filter(row => row.type === 'block').reduce((sum, row) => sum + row.length, 0);
  assert.ok(durableBytes >= 4 * 1048576 && durableBytes < totalBytes);
  const firstStats = await run(host, '({sentBinaryBytes:__flashRTC.sentBinaryBytes,maxMessageBytes:__flashRTC.maxMessageBytes,maxBufferedBytes:__flashRTC.maxBufferedBytes})');
  await host.dispose(); await join.dispose();
  check('interrupted transfer preserves durable progress', {durableBytes, totalBytes});
  host = await makeService('host'); join = await makeService('join');
  assert.equal(host.context.identity.identity.deviceId, sourceIdentity); assert.equal(join.context.identity.identity.deviceId, joinIdentity);
  await connect(true);
  // Once both peers have authenticated, rendezvous is no longer required for the data stream.
  await broker.close();
  await stun.close(); receipt.stunClosedBeforeResumedPayload = true;
  console.log('PHASE rendezvous and STUN offline; accepting resume');
  await accept(true);
  await waitFor('resumed transfer completes', async () => (await run(host, "document.getElementById('connection-status').textContent==='Передача завершена'")) && (await run(join, "document.getElementById('connection-status').textContent==='Передача завершена'")), 120000);
  assert.equal(host.testCounts.readBytes, totalBytes - durableBytes);
  assert.equal(join.testCounts.committedBytes, totalBytes - durableBytes);
  for (const file of manifest.files) {
    const original = path.join(root, 'source', ...file.path.split('/')), received = path.join(savedFolder, ...file.path.split('/'));
    assert.equal((await fs.stat(received)).size, file.size); assert.equal(await sha(original), await sha(received));
  }
  assert.ok((await fs.stat(path.join(savedFolder, 'Photos', 'nested', 'empty'))).isDirectory());
  await assert.rejects(fs.access(path.join(savedFolder, '.mouse-flash-partials')));
  assert.deepEqual(await host.context.files.listResumable(), {send: [], receive: []}); assert.deepEqual(await join.context.files.listResumable(), {send: [], receive: []});
  const secondStats = await run(host, '({sentBinaryBytes:__flashRTC.sentBinaryBytes,maxMessageBytes:__flashRTC.maxMessageBytes,maxBufferedBytes:__flashRTC.maxBufferedBytes})');
  for (const stats of [firstStats, secondStats]) { assert.ok(stats.sentBinaryBytes > 0); assert.ok(stats.maxMessageBytes <= 16384); assert.ok(stats.maxBufferedBytes <= 4 * 1048576); }
  receipt.payloadBytes = totalBytes; receipt.durableBeforeResume = durableBytes; receipt.payloadBytesAfterResume = host.testCounts.readBytes; receipt.firstConnection = firstStats; receipt.resumedConnection = secondStats;
  check('resume transmits only missing payload, final hashes match, rendezvous offline');
  await waitFor('data channels close after success', () => run(join, '__flashRTC.channels.every(channel=>channel.readyState===\'closed\')'));
  check('one-time session closes and completed checkpoints are removed');
  await revealConnection(join);
  await fs.writeFile(path.join(evidence, 'flash-complete.png'), (await bounded(join.window.webContents.capturePage(), 'Completed screenshot')).toPNG());
  receipt.status = 'PASS'; await fs.writeFile(path.join(evidence, 'mouse-flash-rtc.json'), JSON.stringify(receipt, null, 2) + '\n');
  console.log('MOUSE_FLASH_REAL_RTC_PASS');
}
app.whenReady().then(main).then(async () => { await host?.dispose(); await join?.dispose(); await broker?.close(); await stun?.close(); app.exit(0); }).catch(async error => {
  console.error('MOUSE_FLASH_REAL_RTC_FAIL ' + error.stack);
  await fs.mkdir(evidence, {recursive: true}).catch(() => {});
  for (const [name, service] of [['host', host], ['join', join]]) {
    if (service?.window && !service.window.isDestroyed()) {
      // Invitations contain secrets, so failure screenshots mask their fields before capture.
      await run(service, "for(const id of ['invite-text','join-text'])document.getElementById(id).value='[hidden test invitation]'").catch(() => {});
      try { await fs.writeFile(path.join(evidence, name + '-failure.png'), (await bounded(service.window.webContents.capturePage(), 'Failure screenshot')).toPNG()); } catch {}
    }
  }
  await host?.dispose().catch(() => {}); await join?.dispose().catch(() => {}); await broker?.close().catch(() => {}); await stun?.close().catch(() => {}); app.exit(1);
});
setTimeout(() => { console.error('MOUSE_FLASH_REAL_RTC_GLOBAL_TIMEOUT'); app.exit(2); }, 240000).unref();
