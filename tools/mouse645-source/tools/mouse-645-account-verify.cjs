#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const fsp = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const http = require('node:http');
const {spawn, execFile} = require('node:child_process');
const {promisify} = require('node:util');
const {createHash, generateKeyPairSync, randomBytes} = require('node:crypto');
const assert = require('node:assert/strict');
const smoke = require('../desktop/mouse-645-account-smoke.cjs');
const {VERSION, FLAG, STAGE_FILE, STAGES, FIXTURES, PASSWORDS} = smoke.constants;
const {reportName} = smoke;
const {validateSyncState} = require('../desktop/mouse-sync-schema.cjs');
const {verifyAccountCertificate} = require('../desktop/mouse-account-proof.cjs');
const {leaves} = require('../desktop/mouse/layout.js');
const {writePrivateJSON} = require('../desktop/mouse-profile-context.cjs');
const execute = promisify(execFile);
const sha = value => createHash('sha256').update(value).digest('hex');
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const PROCESS_REPORT = 'mouse-645-account-processes.json';
const SERVER_REPORT = 'mouse-645-account-server.json';
const ACCEPTANCE = 'mouse-645-account-acceptance.json';
const CHECKS = Object.freeze(['real-http-sqlite-identity-and-native-avatar',
  'installed-profile-relaunch-and-os-protected-credentials', 'clean-guest-after-logout',
  'separate-native-cookie-and-local-storage-partitions', 'two-device-lightweight-workspace-sync',
  'immediate-logout-final-settings-upload', 'missing-credential-startup-guard-before-window']);

function need(value, message) { if (!value) throw Error('Mouse645 account: ' + message); }
function loopback(origin) {
  let u; try { u = new URL(origin); } catch { return false; }
  return u.protocol === 'http:' && u.hostname === '127.0.0.1' && !!u.port && u.origin === origin;
}
function inside(base, value) {
  if (typeof value !== 'string') return false;
  const relative = path.relative(base, value);
  return relative !== '' && relative !== '..' && !relative.startsWith('..' + path.sep) && !path.isAbsolute(relative);
}
function parseProcess(raw, expectedPid, executable) {
  const match = /^\s*(\d+)\s+(\d+)\s+(.+?)\s*$/.exec(raw);
  need(match && Number(match[1]) === expectedPid && Number(match[2]) > 0 && match[3] === executable,
    'the observed PID is not the installed executable');
  return {pid: Number(match[1]), ppid: Number(match[2]), executable: match[3]};
}
async function observeProcess(pid, executable) {
  need(Number.isSafeInteger(pid) && pid > 0, 'invalid process id');
  const {stdout} = await execute('/bin/ps', ['-p', String(pid), '-o', 'pid=', '-o', 'ppid=', '-o', 'comm=', '-ww'],
    {timeout: 5000, maxBuffer: 8192});
  return {...parseProcess(stdout, pid, executable), source: 'ps', raw: stdout, observedAt: Date.now()};
}
async function maybeJSON(filename) {
  try { return JSON.parse(await fsp.readFile(filename, 'utf8')); }
  catch (error) { if (error.code === 'ENOENT') return null; throw error; }
}
function workspace(value, runId) {
  need(value && value.rendererMatchesNative === true, 'native/renderer workspace agreement is missing');
  const valid = validateSyncState(value.state); assert.deepEqual(valid, value.state);
  const desk = valid.desktops.items.find(row => row.id === valid.desktops.active);
  need(value.theme === valid.preferences.theme && value.paneCount === leaves(desk.layout.tree).length
    && value.desktopName === desk.name, 'workspace summary differs from the actual metadata');
  assert.deepEqual(value.placedTabIds, leaves(desk.layout.tree).map(pane => desk.layout.slots[pane] || '').filter(Boolean),
    'placed native pages differ from the persisted layout');
  need(!JSON.stringify(valid).includes(runId), 'device-local content entered the sync payload');
  return valid;
}
function local(row, expected, origin, label) {
  need(row && row.cookie === expected && row.localStorage === expected && row.url === origin + '/page/' + label + '/'
    && typeof row.pageId === 'string' && Number.isSafeInteger(row.webContentsId) && row.webContentsId > 0,
  'cookie/localStorage profile isolation failed');
}
function marker(row, expected) {
  need(row && row.store === expected && row.file === expected, 'device-local store/file isolation failed');
}
function absent(record) {
  need(record?.present === false && record.registrationPresent === false, 'logout retained a local account credential');
}
function protectedCredentials(record, id) {
  need(record?.present === true && record.storage === 'os' && record.permission === '0600'
    && record.realSafeStorage === true && record.plaintextSecretsAbsent === true
    && record.protectedSessionMatches === true && record.accountId === id,
  'real OS-protected native credentials are missing');
}

function verify(read) {
  const processes = JSON.parse(read(PROCESS_REPORT));
  const server = JSON.parse(read(SERVER_REPORT));
  need(processes.schema === 1 && processes.version === VERSION && processes.platform === 'darwin'
    && processes.arch === 'arm64' && processes.fixtureOnly === true && processes.physicalUserDeviceVerified === false
    && processes.completed === true && /^[a-f0-9]{32}$/.test(processes.runId), 'incomplete installed-process coordinator');
  const runId = processes.runId, executable = processes.executable;
  need(path.isAbsolute(executable) && /^[a-f0-9]{64}$/.test(processes.executableSha256), 'installed executable binding missing');
  need(loopback(processes.identityOrigin) && loopback(processes.browserOrigin)
    && processes.identityOrigin !== processes.browserOrigin, 'an account fixture used a non-loopback origin');
  need(server.schema === 1 && server.version === VERSION && server.runId === runId && server.fixtureOnly === true
    && server.productionAccountsUsed === false && server.identityOrigin === processes.identityOrigin
    && server.browserOrigin === processes.browserOrigin && sha(server.serverPublicKey) === processes.issuerSha256,
  'real fixture service / issuer binding differs');
  need(Array.isArray(processes.profiles) && processes.profiles.length === 2
    && processes.profiles.every(value => path.isAbsolute(value)) && processes.profiles[0] !== processes.profiles[1],
  'two distinct owned device directories are required');
  const reports = [], pids = new Set(), partitions = new Map();
  for (const spec of STAGES) {
    const row = JSON.parse(read(reportName(spec.index))), entered = JSON.parse(read(reportName(spec.index, '-entry'))),
      observed = JSON.parse(read(reportName(spec.index, '-observed'))), ended = JSON.parse(read(reportName(spec.index, '-exit')));
    const profileBase = processes.profiles[spec.device - 1];
    const guestIsolated = spec.profile !== null || ![0, 7].includes(spec.index);
    need(guestIsolated ? /^[a-f0-9]{32}$/.test(row.guestGeneration) : row.guestGeneration === null,
      'fresh guest generation is missing');
    const guestDirectory = guestIsolated ? path.join(profileBase, 'mouse-guests', row.guestGeneration) : profileBase;
    const userData = spec.profile !== null ? path.join(profileBase, 'mouse-accounts', String(spec.profile))
      : guestDirectory;
    need(row.schema === 1 && row.version === VERSION && row.runId === runId && row.index === spec.index
      && row.label === spec.label && row.device === spec.device && row.platform === 'darwin' && row.arch === 'arm64'
      && row.packaged === true && row.fixtureOnly === true && row.physicalUserDeviceVerified === false
      && row.profileBase === profileBase && row.userData === userData && row.guestIsolated === guestIsolated
      && row.guestDirectory === guestDirectory
      && row.executable === executable && row.executableSha256 === processes.executableSha256
      && row.identityOrigin === processes.identityOrigin && row.browserOrigin === processes.browserOrigin
      && row.issuerSha256 === processes.issuerSha256 && inside(userData, row.sessionStoragePath),
    'native stage does not belong to the selected installed profile');
    need(row.completed === true && !row.error && row.operation === spec.operation
      && row.transitionRequested === (spec.operation !== 'finish')
      && (spec.operation === 'finish' || row.next === spec.next), 'an account transition did not finish');
    for (const key of ['schema', 'runId', 'index', 'device', 'pid', 'executable', 'executableSha256', 'profileBase', 'userData',
      'sessionStoragePath', 'guestGeneration', 'guestDirectory', 'startedAt']) need(entered[key] === row[key], 'native stage identity changed after OS observation');
    need(entered.completed === false && entered.phase === 'coordinator', 'OS acknowledgement skipped the native startup barrier');
    need(Number.isSafeInteger(row.pid) && row.pid > 0 && !pids.has(row.pid), 'a claimed restart reused a native process'); pids.add(row.pid);
    need(observed.runId === runId && observed.index === spec.index && observed.source === 'ps'
      && observed.pid === row.pid && observed.executable === executable
      && observed.entrySha256 === sha(read(reportName(spec.index, '-entry'))), 'actual installed PID observation is missing');
    parseProcess(observed.raw, row.pid, executable);
    need(ended.schema === 1 && ended.runId === runId && ended.index === spec.index && ended.pid === row.pid
      && ended.code === 0 && ended.failed === false && ended.completed === true
      && ended.transitionRequested === row.transitionRequested && ended.executableSha256 === row.executableSha256
      && row.startedAt <= observed.observedAt && observed.observedAt <= row.completedAt
      && row.completedAt <= ended.endedAt && ended.endedAt - row.startedAt <= 120000,
    'native stage/exit timing or code does not match its proof');
    need(row.account?.available === true && row.account.accountId === spec.profile
      && row.account.phase === (spec.profile === null ? 'guest' : 'authenticated')
      && row.account.recoveryPending === false && row.account.touchIdEnabled === false,
    'account state differs from the selected profile');
    if (spec.profile === null) absent(row.credentials);
    else {
      protectedCredentials(row.credentials, spec.profile);
      const verified = verifyAccountCertificate({certificate: row.certificate, serverPublicKey: server.serverPublicKey,
        deviceId: row.certificate?.claims?.deviceId, now: row.startedAt});
      need(verified.ok === true && verified.accountId === spec.profile && row.profile?.verified === true
        && row.profile.mouseId === spec.profile && row.profile.name === row.certificate.claims.name
        && row.profile.avatarSha256 === row.certificate.claims.avatarHash, 'native profile does not have its pinned account certificate');
    }
    if (partitions.has(userData)) need(partitions.get(userData) === row.sessionStoragePath, 'the same profile moved cookie partitions');
    else { need(![...partitions.values()].includes(row.sessionStoragePath), 'two profiles share a cookie partition'); partitions.set(userData, row.sessionStoragePath); }
    reports.push(row);
  }
  need(Array.isArray(processes.launches) && processes.launches.length === 3, 'missing real installed executable launches');
  for (let i = 0; i < 3; i++) {
    const launch = processes.launches[i], first = [0, 7, 10][i], last = [6, 9, 12][i];
    need(launch.first === first && launch.last === last && launch.pid === reports[first].pid && launch.exitCode === 0
      && launch.executable === executable && launch.flag === FLAG && launch.elapsedMs > 0 && launch.elapsedMs <= 900000,
    'real process spawn or exit receipt is incomplete');
    need(launch.log === 'mouse-645-account-run-' + i + '.log' && launch.logSha256 === sha(read(launch.log)), 'account launch log changed');
  }
  for (const [label, index] of [['G', 0], ['A', 1], ['B', 3]]) {
    const written = reports[index].written, spec = FIXTURES[label], value = workspace(written?.workspace, runId);
    smoke.assertDesktopSelection(reports[index].desktopSelection, {pid: reports[index].pid,
      startedAt: reports[index].startedAt, completedAt: reports[index].completedAt, target: value.desktops.active});
    need(written.workspace.theme === (label === 'A' ? 'light' : spec.theme) && written.workspace.paneCount === spec.panes
      && value.appearance.whiteTone === spec.tone && written.workspace.desktopName === spec.name + ' desktop', 'fixture layout/theme disappeared');
    const desk = value.desktops.items.find(row => row.id === value.desktops.active);
    need(value.tabs.find(row => row.id === desk.layout.slots.p1)?.url === processes.browserOrigin + '/page/' + label + '/',
      'the owned HTTP page was never placed in its actual native grid');
    assert.deepEqual(value.bookmarks.map(row => [row.url, row.title]), label === 'A'
      ? [[processes.browserOrigin + '/bookmark/A-final', spec.name + ' final bookmark'],
        [processes.browserOrigin + '/bookmark/A', spec.name + ' bookmark']]
      : [[processes.browserOrigin + '/bookmark/' + label, spec.name + ' bookmark']]);
    local(written.local, 'fixture-' + label, processes.browserOrigin, label);
    marker(written.privateMarker, 'private-fixture:' + runId + ':' + label);
    if (label !== 'G') { need(reports[index].sync?.phase === 'synced' && reports[index].sync.revision > 0, 'native sync did not complete');
      assert.deepEqual(reports[index].sync.state, label === 'A' ? reports[index].logoutEdit?.previous?.state : value); }
  }
  const finalEdit = reports[1].logoutEdit;
  need(finalEdit?.syncInvokedAfterEdit === false && finalEdit.previous.theme === 'dark'
    && finalEdit.editedAt <= reports[1].completedAt, 'last-moment native settings change was not exercised');
  assert.deepEqual(finalEdit.remoteBeforeLogout.state, finalEdit.previous.state);
  assert.notDeepEqual(finalEdit.remoteBeforeLogout.state, reports[1].written.workspace.state);
  const finalPush = server.immediateLogoutSync;
  need(finalPush?.index === 1 && finalPush.accountId === 2 && finalPush.revision > finalEdit.remoteBeforeLogout.revision
    && finalPush.observedAt >= reports[1].completedAt && finalPush.observedAt <= reports[2].startedAt + 18000,
    'final logout changes were not observed in SQLite before another account login');
  assert.deepEqual(finalPush.state, reports[1].written.workspace.state);
  for (const [index, id] of [[0, 2], [2, 3]]) {
    const created = reports[index].registration;
    need(created?.account?.phase === 'authenticated' && created.account.accountId === id
      && created.account.recoveryPending === true && created.recoveryShown === true && created.recoveryLength === 43,
    'registration/recovery acknowledgement was bypassed'); protectedCredentials(created.credentials, id);
  }
  const avatar = reports[0].avatar, avatarBytes = read(avatar?.filename);
  need(avatar?.filename === 'mouse-645-account-avatar.png' && avatar.encoder === 'electron.nativeImage.toPNG'
    && avatar.width === 256 && avatar.height === 256 && avatar.bytes === avatarBytes.length && avatar.sha256 === sha(avatarBytes),
  'native avatar encoder evidence is missing');
  const parsedAvatar = require('../services/mouse-identity/avatar.cjs').avatar('data:image/png;base64,' + avatarBytes.toString('base64'));
  need(parsedAvatar.avatarHash === avatar.sha256, 'the real server PNG validator rejected the native avatar');
  for (const index of [1, 5, 8, 11]) need(reports[index].profile.avatarSha256 === avatar.sha256, 'avatar failed account/device restoration');
  need(reports[3].profile.avatarSha256 === null, 'account B inherited another account avatar');
  assert.deepEqual(reports[1].seeded.workspace, reports[0].written.workspace);
  local(reports[1].seeded.local, null, processes.browserOrigin, 'G'); marker(reports[1].seeded.privateMarker, null);
  for (const index of [2, 4, 6, 9, 12]) {
    const clean = reports[index].cleanGuest, before = workspace(clean?.before, runId);
    workspace(clean?.workspace, runId);
    need(clean.inheritedAccountMetadata === false && before.bookmarks.length === 0
      && !before.tabs.some(row => row.url.startsWith(processes.browserOrigin)), 'logout showed previous account or legacy guest metadata');
    local(clean.local, null, processes.browserOrigin, 'C'); marker(clean.privateMarker, null);
  }
  assert.deepEqual(reports[3].seeded.workspace, reports[2].cleanGuest.workspace);
  local(reports[3].seeded.local, null, processes.browserOrigin, 'C'); marker(reports[3].seeded.privateMarker, null);
  local(reports[2].dirtyGuest?.local, 'fixture-C', processes.browserOrigin, 'C');
  marker(reports[2].dirtyGuest.privateMarker, 'private-fixture:' + runId + ':C');
  need(inside(reports[2].sessionStoragePath, reports[2].dirtyGuest.cookieStoreFile), 'guest cookie fixture was not stored in Chromium');
  need(new Set([2, 4, 6, 9, 12].map(index => reports[index].userData)).size === 5, 'logout reused a previous guest directory');
  need(reports[10].userData === reports[6].userData, 'ordinary guest restart unnecessarily replaced its own profile');
  assert.deepEqual(reports[10].restored.workspace, reports[6].cleanGuest.workspace);
  local(reports[10].restored.local, null, processes.browserOrigin, 'C'); marker(reports[10].restored.privateMarker, null);
  for (const index of [4, 6, 10, 12]) {
    const retired = reports[index].retiredGuest;
    need(retired?.previousDirectory === reports[2].userData && retired.privateFilePreserved === true
      && retired.cookieStorePreserved === true && retired.activeDirectoryIsDifferent === true,
    'a previous guest directory was deleted or exposed on another logout');
  }
  for (const index of [2, 4, 6, 10, 12]) {
    need(reports[index].legacy?.workspacePreserved === true && reports[index].legacy.privateFilePreserved === true
      && reports[index].legacy.cookieStorePreserved === true && reports[index].legacy.activeDirectoryIsDifferent === true,
    'legacy user data were deleted or exposed as the signed-out guest');
  }
  for (const index of [5, 8, 11]) {
    assert.deepEqual(reports[index].restored.workspace, reports[1].written.workspace);
    const remote = index === 8;
    local(reports[index].restored.local, remote ? null : 'fixture-A', processes.browserOrigin, 'A');
    marker(reports[index].restored.privateMarker, remote ? null : 'private-fixture:' + runId + ':A');
    assert.deepEqual(reports[index].sync.state, reports[1].written.workspace.state);
  }
  need(reports[7].emptyGuest?.cookiesAbsent === true, 'the second device reused a local cookie partition');
  marker(reports[7].emptyGuest.privateMarker, null);
  need(Array.isArray(reports[8].devices) && reports[8].devices.length === 2
    && new Set(reports[8].devices.map(row => row.deviceId)).size === 2
    && reports[8].devices.filter(row => row.current).length === 1, 'two authenticated devices were not registered');
  need(reports[1].certificate.claims.deviceId !== reports[8].certificate.claims.deviceId, 'logical devices reused the same signing key');
  const lost = reports[11].credentialLoss;
  need(lost?.ownedFixtureOnly === true && lost.activeAccountId === 2 && lost.markerStillSelectsAccount === true, 'missing-credential startup was not exercised'); absent(lost.credentials);
  const guard = JSON.parse(read(reportName(12, '-guard'))), guardObserved = JSON.parse(read(reportName(12, '-guard-observed'))),
    guardEntry = JSON.parse(read(reportName(12, '-guard-entry'))), guardExit = JSON.parse(read(reportName(12, '-guard-exit')));
  assert.deepEqual(guard, guardEntry);
  need(guard.schema === 1 && guard.version === VERSION && guard.runId === runId && guard.index === 12
    && guard.platform === 'darwin' && guard.arch === 'arm64' && guard.packaged === true
    && guard.profileBase === processes.profiles[0] && guard.executable === executable
    && guard.executableSha256 === processes.executableSha256 && !pids.has(guard.pid)
    && guard.blockedAccountId === 2 && guard.selectedAccountId === null && guard.guestIsolated === true
    && guard.guestGeneration === reports[12].guestGeneration && guard.guestDirectory === reports[12].userData
    && guard.phase === 'guest' && guard.accountId === null && guard.credentialsPresent === false && guard.windowCount === 0,
  'missing credentials exposed an account window before guest fallback');
  need(guardObserved.runId === runId && guardObserved.pid === guard.pid && guardObserved.source === 'ps'
    && guardObserved.entrySha256 === sha(read(reportName(12, '-guard-entry'))), 'startup guard was not externally observed');
  parseProcess(guardObserved.raw, guard.pid, executable);
  need(guardExit.code === 0 && guardExit.pid === guard.pid && guardExit.runId === runId
    && guardExit.executableSha256 === processes.executableSha256 && guard.startedAt <= guardObserved.observedAt
    && guardObserved.observedAt <= guardExit.endedAt && guardExit.endedAt - guard.startedAt <= 25000,
  'startup guard did not exit its real pre-window process');
  need(server.ownerReserved === true && server.database === 'sqlite' && server.passwordHasher === 'scrypt', 'fixture service bypassed real account storage');
  assert.deepEqual(server.accounts.map(row => row.id), [2, 3]);
  for (const row of server.accounts) need(row.status === 'active' && row.passwordProtected === true && row.recoveryProtected === true, 'service stored unprotected account credentials');
  need(server.accounts[0].avatarHash === avatar.sha256 && server.accounts[1].avatarHash === null, 'server avatar records differ');
  assert.deepEqual(server.devices.map(row => [row.accountId, row.count]), [[2, 2], [3, 1]]);
  need(server.normalLogout.activeSessions === 0 && server.normalLogout.revokedSessions >= 3,
    'ordinary native logout did not revoke its real server sessions');
  // Removing a local credential cannot revoke a token it no longer has. This
  // last scenario belongs exclusively to the disposable fixture service.
  need(server.afterCredentialLoss.activeSessions === 1 && server.afterCredentialLoss.activeAccounts.length === 1
    && server.afterCredentialLoss.activeAccounts[0] === 2 && server.disposedFixtureOnly === true,
  'unexpected server session after the owned credential-loss scenario');
  for (const [id, index] of [[2, 1], [3, 3]]) {
    const cloud = server.cloud.find(row => row.accountId === id);
    need(cloud && cloud.revision >= 1 && cloud.bytes <= 2 * 1024 * 1024, 'real SQLite configuration missing or unbounded');
    assert.deepEqual(validateSyncState(cloud.state), cloud.state); assert.deepEqual(cloud.state, reports[index].written.workspace.state);
    need(!JSON.stringify(cloud.state).includes(runId), 'server received a private local marker');
  }
  need(Array.isArray(server.requests) && server.requests.filter(row => row.method === 'POST'
    && row.pathname === '/v1/accounts/register' && row.status === 200).length === 2,
  'real HTTP registrations were not exercised');
  need(server.requests.filter(row => row.method === 'POST' && row.pathname === '/v1/accounts/login' && row.status === 200).length >= 3,
    'real HTTP cross-device login was not exercised');
  return {schema: 1, version: VERSION, status: 'PASS', platform: 'darwin', arch: 'arm64', fixtureOnly: true,
    physicalUserDeviceVerified: false, logicalDevices: 2, installedProcesses: STAGES.length + 1,
    checks: [...CHECKS], report: PROCESS_REPORT, server: SERVER_REPORT};
}

function finalize(directory) {
  directory = path.resolve(directory); const artifacts = new Map();
  const read = name => {
    need(typeof name === 'string' && /^mouse-645-account-[a-z0-9.-]+$/.test(name)
      && !name.includes('..') && name !== ACCEPTANCE, 'unsafe evidence filename');
    const file = path.join(directory, name), stat = fs.lstatSync(file);
    need(stat.isFile() && !stat.isSymbolicLink(), 'missing or linked account evidence');
    const raw = fs.readFileSync(file);
    need(![PASSWORDS.A, PASSWORDS.B].some(password => raw.includes(Buffer.from(password))), 'a fixture password escaped into evidence');
    const item = {file: name, bytes: raw.length, sha256: sha(raw)};
    if (artifacts.has(name)) assert.deepEqual(artifacts.get(name), item, 'evidence changed while being verified');
    artifacts.set(name, item); return raw;
  };
  const result = verify(read); result.artifacts = [...artifacts.values()].sort((a, b) => a.file.localeCompare(b.file));
  fs.writeFileSync(path.join(directory, ACCEPTANCE), JSON.stringify(result, null, 2) + '\n', {mode: 0o600});
  console.log('MOUSE_645_ACCOUNT_ACCEPTANCE_PASS'); return result;
}

async function serviceFixture() {
  const directory = await fsp.realpath(await fsp.mkdtemp(path.join(os.tmpdir(), 'mouse-645-identity-')));
  const {IdentityService} = require('../services/mouse-identity/service.cjs');
  const service = new IdentityService({directory, issuerPrivateKey: generateKeyPairSync('ed25519').privateKey,
    ownerBootstrapSecret: randomBytes(32).toString('base64url')});
  const identity = require('../services/mouse-identity/http.cjs').createIdentityServer({service, allowInsecureLoopback: true});
  const requests = [];
  identity.on('request', (req, res) => {
    res.once('finish', () => requests.push({method: req.method, pathname: new URL(req.url, 'http://127.0.0.1').pathname,
      status: res.statusCode, at: Date.now()}));
  });
  const pages = http.createServer((req, res) => {
    const u = new URL(req.url, 'http://127.0.0.1');
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    if (!/^\/(?:page\/[GABC]\/|bookmark\/[GABC](?:-final)?)$/.test(u.pathname)) { res.writeHead(404); res.end('Owned Mouse fixture only'); return; }
    res.end('<!doctype html><meta charset="utf-8"><title>Mouse645 owned account fixture</title>'
      + '<style>body{font:24px system-ui;padding:40px;background:#eef3fa;color:#25354a}</style>'
      + '<h1>Mouse645 local account fixture</h1><p>Owned loopback page. No external content.</p>'
      + '<script>globalThis.mouse645AccountFixture=true;</script>');
  });
  await Promise.all([new Promise(resolve => identity.listen(0, '127.0.0.1', resolve)),
    new Promise(resolve => pages.listen(0, '127.0.0.1', resolve))]);
  const sessionCounts = () => ({activeSessions: service.get('SELECT count(*) AS n FROM sessions WHERE revoked_at IS NULL').n,
    revokedSessions: service.get('SELECT count(*) AS n FROM sessions WHERE revoked_at IS NOT NULL').n,
    activeAccounts: service.all('SELECT DISTINCT account_id AS id FROM sessions WHERE revoked_at IS NULL ORDER BY account_id').map(row => row.id)});
  return {service, requests, sessionCounts, identityOrigin: 'http://127.0.0.1:' + identity.address().port,
    browserOrigin: 'http://127.0.0.1:' + pages.address().port,
    async close() { for (const server of [identity, pages]) { server.closeAllConnections(); await new Promise(resolve => server.close(resolve)); }
      service.close(); await fsp.rm(directory, {recursive: true, force: true}); }};
}

async function run({executable, output, profile, env = process.env}) {
  need(process.platform === 'darwin', 'the installed-app runner requires macOS');
  executable = await fsp.realpath(path.resolve(executable)); output = path.resolve(output); profile = path.resolve(profile);
  const profiles = [profile, profile + '-second-device'];
  need((await fsp.stat(executable)).isFile(), 'installed executable missing');
  await fsp.mkdir(output, {recursive: true, mode: 0o700});
  output = await fsp.realpath(output);
  const evidenceName = /^mouse-645-account-(?:\d{2}(?:-[a-z-]+)?\.json|run-\d\.log|processes\.json|server\.json|acceptance\.json|avatar\.png)$/;
  need(!(await fsp.readdir(output)).some(name => evidenceName.test(name)), 'fresh account evidence directory required');
  for (const [index, current] of profiles.entries()) {
    await fsp.mkdir(current, {recursive: true, mode: 0o700});
    need((await fsp.readdir(current)).length === 0 && !(await fsp.lstat(current)).isSymbolicLink(), 'fresh owned device profile required');
    profiles[index] = await fsp.realpath(current);
  }
  const fixture = await serviceFixture(), runId = randomBytes(16).toString('hex'), tracked = new Set();
  const processes = {schema: 1, version: VERSION, platform: 'darwin', arch: 'arm64', fixtureOnly: true,
    physicalUserDeviceVerified: false, completed: false, executable, executableSha256: sha(await fsp.readFile(executable)),
    runId, profiles, identityOrigin: fixture.identityOrigin, browserOrigin: fixture.browserOrigin,
    issuerSha256: sha(fixture.service.serverPublicKey), launches: []};
  const saveProcesses = () => writePrivateJSON(path.join(output, PROCESS_REPORT), processes);
  async function observe(index, guard = false) {
    const suffix = guard ? '-guard' : '', name = reportName(index, suffix), row = await maybeJSON(path.join(output, name));
    if (!row) return false;
    need(row.runId === runId && row.index === index && row.executable === executable
      && row.executableSha256 === processes.executableSha256, 'native stage belongs to another run');
    need(!row.error, 'native stage ' + index + ' failed: ' + String(row.error?.message || row.label).slice(0, 2000));
    const acknowledged = reportName(index, suffix + '-observed');
    if (!fs.existsSync(path.join(output, acknowledged))) {
      const found = await observeProcess(row.pid, executable); tracked.add(row.pid);
      const entryName = reportName(index, suffix + '-entry'), bytes = await fsp.readFile(path.join(output, name));
      await fsp.writeFile(path.join(output, entryName), bytes, {mode: 0o600});
      await writePrivateJSON(path.join(output, acknowledged), {...found, index, runId, entrySha256: sha(bytes)});
    }
    return row;
  }
  let normalLogout, immediateLogoutSync;
  try {
    for (const [launchIndex, [device, first, last]] of [[1, 0, 6], [2, 7, 9], [1, 10, 12]].entries()) {
      const selected = profiles[device - 1];
      await writePrivateJSON(path.join(selected, STAGE_FILE), {schema: 1, fixtureOnly: true, runId, device,
        index: first, output, identityOrigin: fixture.identityOrigin, browserOrigin: fixture.browserOrigin,
        issuerSha256: processes.issuerSha256});
      const logName = 'mouse-645-account-run-' + launchIndex + '.log', descriptor = fs.openSync(path.join(output, logName), 'wx', 0o600);
      const environment = {...env, CI: 'true', MOUSE_TEST_PROFILE: selected, MOUSE_645_ACCOUNT_OUTPUT: output,
        MOUSE_ACCOUNT_ORIGIN: fixture.identityOrigin, MOUSE_ACCOUNT_PUBLIC_KEY: fixture.service.serverPublicKey};
      const began = Date.now(), child = spawn(executable, [FLAG], {cwd: output, env: environment,
        stdio: ['ignore', descriptor, descriptor], detached: true});
      fs.closeSync(descriptor); tracked.add(child.pid);
      let exitCode = null, spawnError = null;
      child.once('exit', code => { exitCode = code; }); child.once('error', error => { spawnError = error; });
      const launch = {device, first, last, pid: child.pid, executable, flag: FLAG, log: logName};
      processes.launches.push(launch); await saveProcesses();
      for (let index = first; index <= last; index++) {
        const deadline = Date.now() + 150000; let complete = false;
        do {
          if (spawnError) throw spawnError;
          if (exitCode !== null && exitCode !== 0) throw Error('Initial installed account process failed with code ' + exitCode);
          if (index === 12) await observe(12, true);
          const row = await observe(index);
          if (row) {
            need(!row.error, 'native account stage failed: ' + (row.error?.message || row.label));
            const ended = await maybeJSON(path.join(output, reportName(index, '-exit')));
            if (ended) {
              need(row.completed === true && ended.code === 0 && ended.failed === false, 'native account process did not complete');
              if (index === first) need(row.pid === child.pid, 'initial native PID differs from the process spawned by the runner');
              if (index === 1) {
                const cloud = fixture.service.get('SELECT revision,document FROM settings WHERE account_id=2');
                need(cloud, 'last-moment settings were not uploaded before native logout');
                immediateLogoutSync = {index: 1, accountId: 2, revision: cloud.revision,
                  state: JSON.parse(cloud.document), observedAt: Date.now()};
                assert.deepEqual(immediateLogoutSync.state, row.written.workspace.state,
                  'final settings were not saved to the server before logout');
              }
              complete = true; break;
            }
          }
          await sleep(100);
        } while (Date.now() < deadline);
        need(complete, 'native account stage timed out: ' + index);
      }
      const exitDeadline = Date.now() + 10000;
      while (exitCode === null && !spawnError && Date.now() < exitDeadline) await sleep(40);
      need(exitCode === 0 && !spawnError, 'initial account child did not exit cleanly');
      launch.exitCode = exitCode; launch.elapsedMs = Date.now() - began;
      launch.logSha256 = sha(await fsp.readFile(path.join(output, logName))); await saveProcesses();
      if (last === 9) {
        const deadline = Date.now() + 10000;
        while (fixture.sessionCounts().activeSessions !== 0 && Date.now() < deadline) await sleep(50);
        normalLogout = fixture.sessionCounts();
        need(normalLogout.activeSessions === 0, 'normal logout left an authenticated server session');
      }
    }
    const service = fixture.service;
    const accounts = service.all("SELECT id,status,name,avatar_hash,password_salt,password_hash,recovery_hash FROM accounts WHERE status='active' ORDER BY id")
      .map(row => ({id: row.id, status: row.status, name: row.name, avatarHash: row.avatar_hash,
        passwordProtected: row.password_salt?.length > 0 && row.password_hash?.length > 0,
        recoveryProtected: typeof row.recovery_hash === 'string' && row.recovery_hash.length > 0}));
    const cloud = service.all('SELECT account_id,revision,document FROM settings ORDER BY account_id')
      .map(row => ({accountId: row.account_id, revision: row.revision, state: JSON.parse(row.document), bytes: Buffer.byteLength(row.document)}));
    const summary = {schema: 1, version: VERSION, runId, fixtureOnly: true, productionAccountsUsed: false,
      identityOrigin: fixture.identityOrigin, browserOrigin: fixture.browserOrigin, serverPublicKey: service.serverPublicKey,
      database: 'sqlite', passwordHasher: 'scrypt', ownerReserved: service.get('SELECT status FROM accounts WHERE id=1').status === 'reserved',
      accounts, cloud, devices: service.all('SELECT account_id AS accountId,count(*) AS count FROM devices WHERE revoked_at IS NULL GROUP BY account_id ORDER BY account_id'),
      normalLogout, immediateLogoutSync, afterCredentialLoss: fixture.sessionCounts(), disposedFixtureOnly: true, requests: fixture.requests};
    await writePrivateJSON(path.join(output, SERVER_REPORT), summary);
    need(sha(await fsp.readFile(executable)) === processes.executableSha256, 'installed binary changed during the account gate');
    processes.completed = true; await saveProcesses();
  } catch (error) {
    processes.error = {message: String(error.message).slice(0, 2000)}; await saveProcesses(); throw error;
  } finally {
    for (const pid of tracked) {
      try { await observeProcess(pid, executable); process.kill(pid, 'SIGTERM'); } catch {}
    }
    await fixture.close();
  }
  return finalize(output);
}

module.exports = {run, finalize, verify, parseProcess, loopback, serviceFixture, CHECKS};
if (require.main === module) {
  (async () => {
    const args = process.argv.slice(2), options = {};
    for (let i = 0; i < args.length; i++) {
      if (args[i] === '--verify-only') { options.verifyOnly = true; continue; }
      need(['--executable', '--output', '--profile'].includes(args[i]) && args[i + 1], 'unknown or incomplete argument');
      options[args[i].slice(2)] = args[++i];
    }
    need(options.output, '--output is required');
    if (options.verifyOnly) finalize(options.output);
    else { need(options.executable && options.profile, '--executable and --profile are required'); await run(options); }
  })().catch(error => { console.error('MOUSE_645_ACCOUNT_ACCEPTANCE_FAIL: ' + error.message); process.exitCode = 1; });
}
