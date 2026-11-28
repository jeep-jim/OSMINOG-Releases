'use strict';
// Synthetic receipts for rejection tests only. These do not run Electron and
// must never be used as an installed-app acceptance artifact.
const {generateKeyPairSync, randomUUID, randomBytes, createHash, sign} = require('node:crypto');
const {deflateSync} = require('node:zlib');
const path = require('node:path');
const {exportWorkspace} = require('../mouse645-source/desktop/mouse-config-sync.cjs');
const {validateSyncState} = require('../mouse645-source/desktop/mouse-sync-schema.cjs');
const L = require('../mouse645-source/desktop/mouse/layout.js');
const proof = require('../mouse645-source/desktop/mouse-account-proof.cjs');
const {constants: {VERSION, FLAG, STAGES, FIXTURES}, reportName} = require('../mouse645-source/desktop/mouse-645-account-smoke.cjs');
const sha = value => createHash('sha256').update(value).digest('hex');
const bytes = value => Buffer.from(JSON.stringify(value));
function png() {
  function crc(raw) { let n = 0xffffffff; for (const byte of raw) { n ^= byte; for (let i = 0; i < 8; i++) n = (n >>> 1) ^ ((n & 1) ? 0xedb88320 : 0); } return (n ^ 0xffffffff) >>> 0; }
  function chunk(kind, payload) { const kindBytes = Buffer.from(kind), size = Buffer.alloc(4), check = Buffer.alloc(4); size.writeUInt32BE(payload.length); check.writeUInt32BE(crc(Buffer.concat([kindBytes, payload]))); return Buffer.concat([size, kindBytes, payload, check]); }
  const header = Buffer.alloc(13); header.writeUInt32BE(256, 0); header.writeUInt32BE(256, 4); header[8] = 8; header[9] = 6;
  const rows = Buffer.alloc((256 * 4 + 1) * 256);
  for (let y = 0; y < 256; y++) for (let x = 0; x < 256; x++) { const i = y * 1025 + 1 + x * 4; rows[i] = x; rows[i + 1] = y; rows[i + 2] = 80; rows[i + 3] = 255; }
  return Buffer.concat([Buffer.from('89504e470d0a1a0a', 'hex'), chunk('IHDR', header), chunk('IDAT', deflateSync(rows)), chunk('IEND', Buffer.alloc(0))]);
}

function envelope() {
  const files = new Map(), runId = randomBytes(16).toString('hex'), origin = 'http://127.0.0.1:39002';
  const executable = '/Applications/Mouse.app/Contents/MacOS/Mouse', executableSha256 = sha('unit binary only');
  const profiles = ['/owned/device-one', '/owned/device-two'], started = Date.now(), issuer = generateKeyPairSync('ed25519');
  const serverPublicKey = issuer.publicKey.export({type: 'spki', format: 'der'}).toString('base64'), registryId = randomBytes(32).toString('base64url');
  const avatar = png(), avatarHash = sha(avatar); files.set('mouse-645-account-avatar.png', avatar);
  const devices = [1, 2].map(index => {
    const pair = generateKeyPairSync('ed25519'), encryption = generateKeyPairSync('x25519');
    const publicKey = pair.publicKey.export({type: 'spki', format: 'der'}).toString('base64');
    return {deviceId: proof.publicKey(publicKey).keyId.slice(0, 32), publicKey,
      encryptionKey: encryption.publicKey.export({type: 'spki', format: 'der'}).toString('base64'), name: 'Synthetic device ' + index};
  });
  function certificate(accountId, device) {
    const claims = proof.certificateClaims({v: 2, issuerKeyId: proof.publicKey(serverPublicKey).keyId, registryId,
      accountId, deviceId: devices[device - 1].deviceId, publicKey: devices[device - 1].publicKey,
      encryptionKey: devices[device - 1].encryptionKey, name: accountId === 2 ? FIXTURES.A.name : FIXTURES.B.name,
      avatarHash: accountId === 2 ? avatarHash : null, issuedAt: started - 1000, expiresAt: started + 3600000});
    return {claims, signature: sign(null, proof.certificateSigningBytes(claims), issuer.privateKey).toString('base64')};
  }
  function workspace(label) {
    const value = exportWorkspace({}), fixture = FIXTURES[label];
    if (label) {
      const desk = value.desktops.items[fixture?.index || 0], tabId = randomUUID(), panes = fixture?.panes || 4;
      desk.name = fixture ? fixture.name + ' desktop' : desk.name;
      desk.layout.tree = L.preset(panes); desk.layout.slots = Object.fromEntries(L.leaves(desk.layout.tree).map((key, index) => [key, index ? '' : tabId]));
      desk.layout.active = 'p1'; desk.layout.tabOrder = [tabId]; value.desktops.active = desk.id;
      value.desktops.members = {[tabId]: desk.id}; value.tabs = [{id: tabId, url: origin + '/page/' + label + '/', lane: 'main'}];
      if (fixture) {
        value.preferences.theme = fixture.theme; value.appearance = {paneMode: 'square', whiteTone: fixture.tone};
        value.bookmarks = [{id: 'bookmark-' + label, url: origin + '/bookmark/' + label, title: fixture.name + ' bookmark', at: 1}];
      }
    }
    const state = validateSyncState(value), desk = state.desktops.items.find(row => row.id === state.desktops.active);
    return {state, theme: state.preferences.theme, paneCount: L.leaves(desk.layout.tree).length,
      desktopName: desk.name, placedTabIds: L.leaves(desk.layout.tree).map(pane => desk.layout.slots[pane] || '').filter(Boolean),
      rendererMatchesNative: true};
  }
  const work = {G: workspace('G'), A: workspace('A'), B: workspace('B'), C: workspace('C'), empty: workspace(null)};
  const previousA = structuredClone(work.A);
  work.A.theme = 'light'; work.A.state.preferences.theme = 'light';
  work.A.state.bookmarks.unshift({id: 'bookmark-A-final', url: origin + '/bookmark/A-final', title: FIXTURES.A.name + ' final bookmark', at: 2});
  const local = (label, value) => ({cookie: value, localStorage: value, pageId: 'synthetic-' + label,
    webContentsId: 11, url: origin + '/page/' + label + '/'});
  const marker = label => ({store: label ? 'private-fixture:' + runId + ':' + label : null,
    file: label ? 'private-fixture:' + runId + ':' + label : null});
  const absent = () => ({present: false, registrationPresent: false});
  const credentials = id => ({present: true, storage: 'os', permission: '0600', realSafeStorage: true,
    plaintextSecretsAbsent: true, protectedSessionMatches: true, accountId: id, registrationPresent: false});
  const summary = id => ({available: true, phase: id ? 'authenticated' : 'guest', accountId: id,
    recoveryPending: false, touchIdAvailable: false, touchIdReason: 'MOUSE_TOUCH_ID_UNAVAILABLE', touchIdEnabled: false});
  const written = label => ({workspace: work[label], local: local(label, 'fixture-' + label), privateMarker: marker(label)});
  const clean = () => ({before: work.empty, workspace: work.C, local: local('C', null), privateMarker: marker(null), inheritedAccountMetadata: false});
  const restored = (label, foreign = false) => ({workspace: work[label], local: local(label, foreign ? null : 'fixture-' + label), privateMarker: marker(foreign ? null : label)});
  const restoreClean = () => ({workspace: work.C, local: local('C', null), privateMarker: marker(null)});
  const legacy = () => ({workspacePreserved: true, privateFilePreserved: true, cookieStorePreserved: true, activeDirectoryIsDifferent: true});
  const rows = STAGES.map(spec => {
    const guestIsolated = spec.profile !== null || ![0, 7].includes(spec.index), profileBase = profiles[spec.device - 1];
    const group = [null, 1, 2, 2, 4, 4, 6, null, 8, 9, 6, 6, 12][spec.index];
    const guestGeneration = group === null ? null : group.toString(16).repeat(32);
    const guestDirectory = guestGeneration ? path.join(profileBase, 'mouse-guests', guestGeneration) : profileBase;
    const userData = spec.profile !== null ? path.join(profileBase, 'mouse-accounts', String(spec.profile))
      : guestDirectory;
    const row = {schema: 1, version: VERSION, fixtureOnly: true, physicalUserDeviceVerified: false, runId,
      index: spec.index, label: spec.label, device: spec.device, pid: 1000 + spec.index, ppid: 999,
      platform: 'darwin', arch: 'arm64', packaged: true, executable, executableSha256,
      profileBase, userData, sessionStoragePath: path.join(userData, 'Partitions', 'osminog-browser'), guestIsolated,
      guestGeneration, guestDirectory,
      identityOrigin: 'http://127.0.0.1:39001', browserOrigin: origin, issuerSha256: sha(serverPublicKey),
      startedAt: started + spec.index * 1000, completedAt: started + spec.index * 1000 + 100,
      completed: true, phase: spec.label, transitionRequested: spec.operation !== 'finish', operation: spec.operation,
      next: spec.next, account: summary(spec.profile), credentials: spec.profile ? credentials(spec.profile) : absent()};
    if (spec.profile) {
      row.certificate = certificate(spec.profile, spec.device);
      row.profile = {name: row.certificate.claims.name, mouseId: spec.profile, verified: true, avatarSha256: row.certificate.claims.avatarHash};
    }
    return row;
  });
  for (const [index, label] of [[0, 'G'], [1, 'A'], [3, 'B']]) {
    const row = rows[index], target = work[label].state.desktops.active, previous = target === 'desk-1' ? 'desk-2' : 'desk-1';
    row.written = written(label);
    const inputs = ['#desktops-button', '.desktop-card[data-desk="' + target + '"] .desk-open'].map((selector, i) => {
      const at = row.startedAt + 5 + i * 10, clientPoint = {x: 100 + i * 100, y: 700 - i * 100};
      return {selector, action: 'click', source: 'CGEvent', pid: row.pid, webContentsId: 400 + index, posted: true,
        at, observedAt: at + 2, contentBounds: {x: 4, y: 29, width: 1200, height: 794}, zoom: 1,
        clientPoint, point: {x: clientPoint.x + 4, y: clientPoint.y + 29},
        events: [{type: 'click', trusted: true, matches: true, selector, at: at + 1, x: clientPoint.x, y: clientPoint.y}]};
    });
    row.desktopSelection = {target, before: {desktopId: previous, nativeDesktopId: previous, trayOpen: false, holdsNative: false, transition: null},
      nativeInputs: inputs, nora: {ready: true, open: true, hidden: false, phase: 'open', inert: false,
        isOpen: true, preparing: false, holdsNative: true, settled: true},
      after: {desktopId: target, stateDesktopId: target, nativeDesktopId: target, switching: false,
        desktopSliding: false, trayOpen: false, holdsNative: false,
        transition: {strategy: 'live', phase: 'complete', presented: true, startedAt: 200, selectedAt: 220, layoutAt: 230,
          totalDurationMs: 60, snapshotCaptures: 0, borrowedHold: false, layoutCalls: 1},
        trace: [{phase: 'present.raf1', at: 238, frameTime: 237}, {phase: 'present.raf2', at: 254, frameTime: 253}]}};
  }
  for (const [index, id] of [[0, 2], [2, 3]]) rows[index].registration = {account: {...summary(id), recoveryPending: true},
    recoveryShown: true, recoveryLength: 43, credentials: credentials(id)};
  rows[0].avatar = {filename: 'mouse-645-account-avatar.png', bytes: avatar.length, sha256: avatarHash,
    width: 256, height: 256, encoder: 'electron.nativeImage.toPNG'};
  rows[0].cookieStoreFile = path.join(rows[0].sessionStoragePath, 'Cookies');
  rows[1].seeded = restored('G', true); rows[3].seeded = restoreClean();
  for (const index of [2, 4, 6, 9, 12]) rows[index].cleanGuest = clean();
  rows[2].dirtyGuest = {local: local('C', 'fixture-C'), privateMarker: marker('C'),
    cookieStoreFile: path.join(rows[2].sessionStoragePath, 'Cookies')};
  for (const index of [2, 4, 6, 10, 12]) rows[index].legacy = legacy();
  rows[10].restored = restoreClean();
  for (const index of [4, 6, 10, 12]) rows[index].retiredGuest = {previousDirectory: rows[2].userData,
    privateFilePreserved: true, cookieStorePreserved: true, activeDirectoryIsDifferent: true};
  for (const index of [5, 8, 11]) rows[index].restored = restored('A', index === 8);
  for (const [index, label] of [[1, 'A'], [3, 'B'], [5, 'A'], [8, 'A'], [11, 'A']]) rows[index].sync = {phase: 'synced', revision: 2, state: work[label].state};
  rows[1].sync.state = previousA.state;
  rows[1].logoutEdit = {editedAt: rows[1].completedAt - 1, syncInvokedAfterEdit: false, previous: previousA,
    remoteBeforeLogout: {revision: 2, state: previousA.state}};
  rows[7].emptyGuest = {cookiesAbsent: true, privateMarker: marker(null)}; rows[7].guestWorkspace = work.empty;
  rows[8].devices = devices.map((value, index) => ({deviceId: value.deviceId, name: value.name, current: index === 1}));
  rows[11].credentialLoss = {ownedFixtureOnly: true, activeAccountId: 2, markerStillSelectsAccount: true, credentials: absent()};
  for (const row of rows) {
    const entered = {...row, completed: false, phase: 'coordinator'}, entry = bytes(entered);
    files.set(reportName(row.index), bytes(row)); files.set(reportName(row.index, '-entry'), entry);
    files.set(reportName(row.index, '-observed'), bytes({runId, index: row.index, pid: row.pid, ppid: 999,
      executable, source: 'ps', raw: ' ' + row.pid + ' 999 ' + executable + '\n', observedAt: row.startedAt + 50, entrySha256: sha(entry)}));
    files.set(reportName(row.index, '-exit'), bytes({schema: 1, runId, index: row.index, pid: row.pid, code: 0,
      failed: false, completed: true, transitionRequested: row.transitionRequested, endedAt: row.completedAt + 50, executableSha256}));
  }
  const guard = {schema: 1, version: VERSION, runId, index: 12, pid: 2000, platform: 'darwin', arch: 'arm64', packaged: true,
    profileBase: profiles[0], executable, executableSha256, blockedAccountId: 2, selectedAccountId: null, guestIsolated: true,
    guestGeneration: rows[12].guestGeneration, guestDirectory: rows[12].userData,
    phase: 'guest', accountId: null, credentialsPresent: false, windowCount: 0, startedAt: started + 11500};
  const guardBytes = bytes(guard); files.set(reportName(12, '-guard'), guardBytes); files.set(reportName(12, '-guard-entry'), guardBytes);
  files.set(reportName(12, '-guard-observed'), bytes({runId, index: 12, pid: guard.pid, source: 'ps', executable,
    raw: ' ' + guard.pid + ' 999 ' + executable + '\n', entrySha256: sha(guardBytes), observedAt: guard.startedAt + 50}));
  files.set(reportName(12, '-guard-exit'), bytes({schema: 1, runId, index: 12, pid: guard.pid, code: 0,
    executableSha256, endedAt: guard.startedAt + 100}));
  const launches = [[0, 6], [7, 9], [10, 12]].map(([first, last], index) => {
    const log = 'mouse-645-account-run-' + index + '.log', raw = Buffer.from('Synthetic unit receipt only\n'); files.set(log, raw);
    return {first, last, pid: rows[first].pid, exitCode: 0, executable, flag: FLAG, elapsedMs: 1000, log, logSha256: sha(raw)};
  });
  files.set('mouse-645-account-processes.json', bytes({schema: 1, version: VERSION, platform: 'darwin', arch: 'arm64',
    fixtureOnly: true, physicalUserDeviceVerified: false, completed: true, runId, executable, executableSha256, profiles,
    identityOrigin: rows[0].identityOrigin, browserOrigin: origin, issuerSha256: sha(serverPublicKey), launches}));
  files.set('mouse-645-account-server.json', bytes({schema: 1, version: VERSION, runId, fixtureOnly: true, productionAccountsUsed: false,
    identityOrigin: rows[0].identityOrigin, browserOrigin: origin, serverPublicKey, database: 'sqlite', passwordHasher: 'scrypt', ownerReserved: true,
    accounts: [2, 3].map(id => ({id, status: 'active', passwordProtected: true, recoveryProtected: true, avatarHash: id === 2 ? avatarHash : null})),
    devices: [{accountId: 2, count: 2}, {accountId: 3, count: 1}], normalLogout: {activeSessions: 0, revokedSessions: 3},
    immediateLogoutSync: {index: 1, accountId: 2, revision: 3, state: work.A.state, observedAt: rows[1].completedAt + 100},
    afterCredentialLoss: {activeSessions: 1, activeAccounts: [2]}, disposedFixtureOnly: true,
    cloud: [['A', 2], ['B', 3]].map(([label, accountId]) => ({accountId, revision: 2, bytes: Buffer.byteLength(JSON.stringify(work[label].state)), state: work[label].state})),
    requests: [...Array.from({length: 2}, () => ({method: 'POST', pathname: '/v1/accounts/register', status: 200})),
      ...Array.from({length: 3}, () => ({method: 'POST', pathname: '/v1/accounts/login', status: 200}))]}));
  return {files, rows, runId, read: name => { if (!files.has(name)) throw Error('Missing synthetic receipt: ' + name); return files.get(name); },
    edit(name, callback) { const value = JSON.parse(files.get(name)); callback(value); files.set(name, bytes(value)); }};
}
module.exports = {envelope, png};
