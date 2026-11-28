'use strict';

const fs = require('node:fs');
const path = require('node:path');
const {DatabaseSync} = require('node:sqlite');
const {randomBytes, createHash, createPublicKey, sign, timingSafeEqual} = require('node:crypto');
const {IdentityError, fail, record, integer} = require('./errors.cjs');
const {PasswordHasher} = require('./passwords.cjs');
const {RateLimiter} = require('./limits.cjs');
const {avatar} = require('./avatar.cjs');
const proof = require('../../desktop/mouse-account-proof.cjs');
const {verify: verifyDevice} = require('../../desktop/mouse-flash-identity.cjs');

const ACCESS_TTL_MS = 10 * 60 * 1000;
const REFRESH_TTL_MS = 30 * 24 * 60 * 60 * 1000;
const INVITE_TTL_MS = 5 * 60 * 1000;
const PRESENCE_TTL_MS = 90 * 1000;
const MAX_CHALLENGES = 1024;
const MAX_DEVICES = 32;
const MAX_INVITATIONS = 512;
const MAX_INVITE_BYTES = 16 * 1024;
function token() { return randomBytes(32).toString('base64url'); }
function digest(namespace, value) { return createHash('sha256').update(namespace + ':' + value).digest('hex'); }
function equal(a, b) { return typeof a === 'string' && typeof b === 'string' && a.length === b.length && timingSafeEqual(Buffer.from(a), Buffer.from(b)); }
function privateDirectory(directory) {
  if (typeof directory !== 'string' || !path.isAbsolute(directory)) fail('STORAGE_UNAVAILABLE', 503);
  fs.mkdirSync(directory, {recursive: true, mode: 0o700});
  const info = fs.lstatSync(directory);
  if (!info.isDirectory() || info.isSymbolicLink() || fs.realpathSync(directory) !== path.resolve(directory)) fail('STORAGE_UNAVAILABLE', 503);
  fs.chmodSync(directory, 0o700);
}
function privateDatabase(directory) {
  privateDirectory(directory);
  const filename = path.join(directory, 'accounts.sqlite');
  for (const suffix of ['', '-wal', '-shm']) {
    const name = filename + suffix;
    try {
      const info = fs.lstatSync(name);
      if (!info.isFile() || info.isSymbolicLink() || info.nlink !== 1) fail('STORAGE_UNAVAILABLE', 503);
      fs.chmodSync(name, 0o600);
    } catch (error) { if (error.code !== 'ENOENT') throw error; }
  }
  const fd = fs.openSync(filename, fs.constants.O_CREAT | fs.constants.O_RDWR | (fs.constants.O_NOFOLLOW || 0), 0o600);
  fs.closeSync(fd);
  return filename;
}
function cleanError(error) {
  if (error instanceof IdentityError) return error;
  if (error?.name === 'MouseAccountError' || error?.name === 'FlashIdentityError') return new IdentityError('INVALID_PROOF');
  return error;
}

class IdentityService {
  constructor({directory, issuerPrivateKey, ownerBootstrapSecret, now = Date.now, maxAccounts = 4096,
    passwordHasher} = {}) {
    if (!issuerPrivateKey || issuerPrivateKey.type !== 'private' || issuerPrivateKey.asymmetricKeyType !== 'ed25519') fail('ISSUER_UNAVAILABLE', 503);
    this.now = now; this.signer = issuerPrivateKey; this.maxAccounts = integer(maxAccounts, 2, 1000000);
    this.serverPublicKey = createPublicKey(issuerPrivateKey).export({type: 'spki', format: 'der'}).toString('base64');
    this.issuerKeyId = proof.publicKey(this.serverPublicKey).keyId;
    this.passwords = passwordHasher || new PasswordHasher();
    this.rates = new RateLimiter({now}); this.challenges = new Map(); this.presence = new Map(); this.invitations = new Map(); this.closed = false;
    this.db = new DatabaseSync(privateDatabase(directory));
    this.statements = new Map();
    try {
      this.db.exec('PRAGMA foreign_keys=ON; PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; PRAGMA busy_timeout=1000; PRAGMA trusted_schema=OFF; PRAGMA wal_autocheckpoint=256; PRAGMA journal_size_limit=8388608;');
      const pageSize = integer(this.get('PRAGMA page_size').page_size, 512, 65536);
      this.db.exec('PRAGMA max_page_count=' + Math.floor(4 * 1024 * 1024 * 1024 / pageSize));
      this.db.exec(`
        CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL) STRICT;
        CREATE TABLE IF NOT EXISTS accounts (
          id INTEGER PRIMARY KEY AUTOINCREMENT, status TEXT NOT NULL CHECK(status IN ('reserved','active')),
          name TEXT NOT NULL DEFAULT '', avatar TEXT, avatar_hash TEXT,
          password_salt BLOB, password_hash BLOB, password_version INTEGER NOT NULL DEFAULT 1,
          recovery_hash TEXT, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL
        ) STRICT;
        CREATE TABLE IF NOT EXISTS devices (
          account_id INTEGER NOT NULL REFERENCES accounts(id), device_id TEXT NOT NULL,
          public_key TEXT NOT NULL, encryption_key TEXT NOT NULL, name TEXT NOT NULL,
          created_at INTEGER NOT NULL, last_seen_at INTEGER NOT NULL, revoked_at INTEGER,
          PRIMARY KEY(account_id, device_id)
        ) STRICT;
        CREATE TABLE IF NOT EXISTS registrations (
          request_hash TEXT PRIMARY KEY, account_id INTEGER NOT NULL UNIQUE REFERENCES accounts(id),
          device_id TEXT NOT NULL, public_key TEXT NOT NULL, encryption_key TEXT NOT NULL,
          profile_hash TEXT NOT NULL, owner INTEGER NOT NULL CHECK(owner IN (0,1))
        ) STRICT;
        CREATE TABLE IF NOT EXISTS sessions (
          id TEXT PRIMARY KEY, account_id INTEGER NOT NULL, device_id TEXT NOT NULL,
          access_hash TEXT NOT NULL UNIQUE, refresh_hash TEXT NOT NULL UNIQUE,
          access_expires INTEGER NOT NULL, refresh_expires INTEGER NOT NULL,
          created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL, revoked_at INTEGER, refresh_count INTEGER NOT NULL DEFAULT 0,
          FOREIGN KEY(account_id,device_id) REFERENCES devices(account_id,device_id)
        ) STRICT;
        CREATE INDEX IF NOT EXISTS sessions_account_device ON sessions(account_id,device_id);
        CREATE TABLE IF NOT EXISTS used_refresh (
          hash TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
          expires_at INTEGER NOT NULL
        ) STRICT;
        CREATE TABLE IF NOT EXISTS settings (
          account_id INTEGER PRIMARY KEY REFERENCES accounts(id), revision INTEGER NOT NULL,
          schema_version INTEGER NOT NULL, document TEXT NOT NULL, updated_at INTEGER NOT NULL,
          updated_by TEXT NOT NULL
        ) STRICT;
      `);
      this.transaction(() => {
        if (!this.all('PRAGMA table_info(sessions)').some(column => column.name === 'refresh_count')) {
          this.db.exec('ALTER TABLE sessions ADD COLUMN refresh_count INTEGER NOT NULL DEFAULT 0');
        }
        const version = this.get('SELECT value FROM meta WHERE key=?', 'schema_version');
        if (version && version.value !== '1') fail('STORAGE_SCHEMA_UNSUPPORTED', 503);
        if (!version) {
          if (!ownerBootstrapSecret) fail('BOOTSTRAP_UNAVAILABLE', 503);
          proof.token(ownerBootstrapSecret);
          const registryId = token();
          this.run('INSERT INTO meta(key,value) VALUES(?,?)', 'schema_version', '1');
          this.run('INSERT INTO meta(key,value) VALUES(?,?)', 'registry_id', registryId);
          this.run('INSERT INTO meta(key,value) VALUES(?,?)', 'issuer_key_id', this.issuerKeyId);
          this.run('INSERT INTO meta(key,value) VALUES(?,?)', 'bootstrap_hash', digest('MouseOwnerBootstrap:v1:' + registryId, ownerBootstrapSecret));
          this.run('INSERT INTO accounts(id,status,created_at,updated_at) VALUES(1,?,?,?)', 'reserved', this.now(), this.now());
        }
        if (this.get('SELECT value FROM meta WHERE key=?', 'issuer_key_id')?.value !== this.issuerKeyId) fail('ISSUER_MISMATCH', 503);
        this.registryId = proof.token(this.get('SELECT value FROM meta WHERE key=?', 'registry_id')?.value);
        const bootstrapHash = this.get('SELECT value FROM meta WHERE key=?', 'bootstrap_hash')?.value;
        if (bootstrapHash && ownerBootstrapSecret !== undefined
          && !equal(bootstrapHash, digest('MouseOwnerBootstrap:v1:' + this.registryId, proof.token(ownerBootstrapSecret)))) fail('BOOTSTRAP_MISMATCH', 503);
      });
      // SQLite creates sidecars using the database's permissions. Recheck now as
      // well as at open, independently of the process umask.
      privateDatabase(directory);
    } catch (error) { this.db.close(); throw cleanError(error); }
  }
  statement(sql) { let result = this.statements.get(sql); if (!result) { result = this.db.prepare(sql); this.statements.set(sql, result); } return result; }
  get(sql, ...args) { return this.statement(sql).get(...args); }
  all(sql, ...args) { return this.statement(sql).all(...args); }
  run(sql, ...args) { return this.statement(sql).run(...args); }
  transaction(callback) {
    this.db.exec('BEGIN IMMEDIATE');
    try { const result = callback(); this.db.exec('COMMIT'); return result; }
    catch (error) { this.db.exec('ROLLBACK'); throw error; }
  }
  available() { if (this.closed) fail('SERVICE_UNAVAILABLE', 503); }
  info() { return {v: 1, registryId: this.registryId, issuerKeyId: this.issuerKeyId, serverPublicKey: this.serverPublicKey}; }
  rate(context, operation, accountId) {
    const ip = context?.ip || 'internal';
    this.rates.take('requests', ip, 600, 60000);
    if (operation === 'auth') {
      this.rates.take('auth-ip', ip, 15, 15 * 60000);
      if (accountId !== undefined && accountId !== null) this.rates.take('auth-account', accountId, 10, 15 * 60000);
    }
    if (operation === 'register') this.rates.take('register-ip', ip, 3, 60 * 60000);
  }
  prune() {
    const now = this.now();
    for (const [key, value] of this.challenges) if (value.expiresAt <= now) this.challenges.delete(key);
    for (const [key, value] of this.presence) if (value.expiresAt <= now) this.presence.delete(key);
    for (const [key, value] of this.invitations) if (value.expiresAt <= now) this.invitations.delete(key);
    if (!this.lastPrune || now - this.lastPrune > 60000) {
      this.run('DELETE FROM used_refresh WHERE expires_at<=?', now);
      this.run('DELETE FROM sessions WHERE refresh_expires<=?', now);
      this.rates.prune(now); this.lastPrune = now;
    }
  }
  challenge(body, context) {
    this.available(); record(body, ['action', 'identity', 'encryptionKey'], ['accountId', 'registrationId', 'profile']);
    this.rate(context); this.rates.take('challenge-ip', context?.ip || 'internal', 30, 60000); this.prune();
    if (this.challenges.size >= MAX_CHALLENGES) fail('AUTH_BUSY', 503);
    const registration = ['register', 'claim-owner'].includes(body.action);
    const profile = registration ? proof.normalizeAccountProfile(body.profile) : null;
    if (registration && body.accountId !== undefined || !registration && (body.profile !== undefined || body.registrationId !== undefined)) fail('INVALID_REQUEST');
    const now = this.now();
    const value = {v: 2, challengeId: token(), action: body.action, registryId: this.registryId, issuerKeyId: this.issuerKeyId,
      identity: proof.readIdentity(body.identity), encryptionKey: body.encryptionKey,
      accountId: registration ? null : integer(body.accountId), registrationId: registration ? body.registrationId : null,
      profile, issuedAt: now, expiresAt: now + proof.CHALLENGE_TTL_MS};
    try { value.transcriptHash = proof.authChallengeTranscript(value); } catch (error) { throw cleanError(error); }
    this.challenges.set(value.challengeId, value);
    return {...value};
  }
  consumeChallenge(body, action) {
    let challengeId;
    try { challengeId = proof.token(body.challengeId); } catch { fail('AUTH_FAILED', 401); }
    const challenge = this.challenges.get(challengeId); this.challenges.delete(challengeId);
    if (!challenge || challenge.action !== action || challenge.expiresAt <= this.now()) fail('AUTH_FAILED', 401);
    try { verifyDevice({identity: challenge.identity, transcriptHash: proof.authChallengeTranscript(challenge), signature: body.signature}); }
    catch { fail('AUTH_FAILED', 401); }
    return challenge;
  }
  account(id) { return this.get("SELECT * FROM accounts WHERE id=? AND status='active'", id); }
  publicAccount(account) { return {id: account.id, name: account.name, avatar: account.avatar}; }
  device(accountId, deviceId) { return this.get('SELECT * FROM devices WHERE account_id=? AND device_id=? AND revoked_at IS NULL', accountId, deviceId); }
  putDevice(accountId, challenge) {
    const existing = this.get('SELECT * FROM devices WHERE account_id=? AND device_id=?', accountId, challenge.identity.deviceId);
    if (existing && existing.public_key !== challenge.identity.publicKey) fail('DEVICE_KEY_MISMATCH', 409);
    if ((!existing || existing.revoked_at !== null)
      && this.get('SELECT count(*) AS count FROM devices WHERE account_id=? AND revoked_at IS NULL', accountId).count >= MAX_DEVICES) fail('DEVICE_LIMIT', 409);
    if (!existing && this.get('SELECT count(*) AS count FROM devices WHERE account_id=?', accountId).count >= 256) fail('DEVICE_LIMIT', 409);
    const now = this.now();
    this.run(`INSERT INTO devices(account_id,device_id,public_key,encryption_key,name,created_at,last_seen_at,revoked_at)
      VALUES(?,?,?,?,?,?,?,NULL) ON CONFLICT(account_id,device_id) DO UPDATE SET
      encryption_key=excluded.encryption_key,name=excluded.name,last_seen_at=excluded.last_seen_at,revoked_at=NULL`,
    accountId, challenge.identity.deviceId, challenge.identity.publicKey, challenge.encryptionKey, challenge.identity.name, now, now);
    return this.device(accountId, challenge.identity.deviceId);
  }
  certificate(account, device) {
    const issuedAt = this.now();
    const claims = proof.certificateClaims({v: 2, issuerKeyId: this.issuerKeyId, registryId: this.registryId, accountId: account.id,
      deviceId: device.device_id, publicKey: device.public_key, encryptionKey: device.encryption_key,
      name: account.name, avatarHash: account.avatar_hash, issuedAt, expiresAt: issuedAt + proof.DEVICE_CERTIFICATE_TTL_MS});
    return {claims, signature: sign(null, proof.certificateSigningBytes(claims), this.signer).toString('base64')};
  }
  issueSession(account, device, recoveryCode) {
    const accessToken = token(), refreshToken = token(), now = this.now();
    // A fresh password login supersedes this device's old family. Its hashes
    // are no longer useful for replay detection once the entire family ends.
    this.run('DELETE FROM sessions WHERE account_id=? AND device_id=?', account.id, device.device_id);
    this.run(`INSERT INTO sessions(id,account_id,device_id,access_hash,refresh_hash,access_expires,refresh_expires,created_at,updated_at)
      VALUES(?,?,?,?,?,?,?,?,?)`, token(), account.id, device.device_id, digest('access', accessToken), digest('refresh', refreshToken),
    now + ACCESS_TTL_MS, now + REFRESH_TTL_MS, now, now);
    return {account: this.publicAccount(account), certificate: this.certificate(account, device), accessToken, refreshToken,
      accessExpiresAt: now + ACCESS_TTL_MS, refreshExpiresAt: now + REFRESH_TTL_MS, ...(recoveryCode ? {recoveryCode} : {})};
  }
  async register(body, context, {owner = false} = {}) {
    this.available(); record(body, ['challengeId', 'signature', 'password', 'avatar'], owner ? ['ownerBootstrapSecret'] : []);
    const challenge = this.consumeChallenge(body, owner ? 'claim-owner' : 'register'); this.rate(context, 'auth');
    const image = avatar(body.avatar);
    if (image.avatarHash !== challenge.profile.avatarHash) fail('AVATAR_MISMATCH');
    const requestHash = digest('registration', challenge.registrationId), profileHash = digest('registration-profile', JSON.stringify(challenge.profile));
    const registered = this.get('SELECT * FROM registrations WHERE request_hash=?', requestHash);
    if (registered) {
      if (registered.device_id !== challenge.identity.deviceId || registered.public_key !== challenge.identity.publicKey
        || registered.encryption_key !== challenge.encryptionKey || registered.profile_hash !== profileHash || registered.owner !== Number(owner)) fail('AUTH_FAILED', 401);
      const account = this.account(registered.account_id);
      if (!await this.passwords.verify(body.password, account)) fail('AUTH_FAILED', 401);
      this.available();
      const recoveryCode = token();
      return this.transaction(() => {
        const current = this.account(registered.account_id);
        if (!current || current.password_version !== account.password_version) fail('AUTH_FAILED', 401);
        this.run('UPDATE accounts SET recovery_hash=?,updated_at=? WHERE id=?', digest('recovery', recoveryCode), this.now(), current.id);
        return this.issueSession(this.account(current.id), this.putDevice(current.id, challenge), recoveryCode);
      });
    }
    this.rate(context, 'register');
    if (owner) {
      let supplied = '';
      try { supplied = digest('MouseOwnerBootstrap:v1:' + this.registryId, proof.token(body.ownerBootstrapSecret)); } catch {}
      const stored = this.get('SELECT value FROM meta WHERE key=?', 'bootstrap_hash')?.value;
      if (!stored || !equal(stored, supplied)) fail('AUTH_FAILED', 401);
    }
    const hashed = await this.passwords.hash(body.password); this.available();
    const recoveryCode = token(), now = this.now();
    try {
      return this.transaction(() => {
        if (this.get('SELECT request_hash FROM registrations WHERE request_hash=?', requestHash)) fail('REGISTRATION_RETRY', 409);
        let id;
        if (owner) {
          const stored = this.get('SELECT value FROM meta WHERE key=?', 'bootstrap_hash')?.value;
          if (!stored || !equal(stored, digest('MouseOwnerBootstrap:v1:' + this.registryId, body.ownerBootstrapSecret))) fail('AUTH_FAILED', 401);
          const result = this.run(`UPDATE accounts SET status='active',name=?,avatar=?,avatar_hash=?,password_salt=?,password_hash=?,
            recovery_hash=?,updated_at=? WHERE id=1 AND status='reserved'`, challenge.profile.name, image.avatar, image.avatarHash,
          hashed.salt, hashed.digest, digest('recovery', recoveryCode), now);
          if (result.changes !== 1) fail('AUTH_FAILED', 401);
          this.run('DELETE FROM meta WHERE key=?', 'bootstrap_hash'); id = 1;
        } else {
          if (this.get('SELECT count(*) AS count FROM accounts').count >= this.maxAccounts) fail('ACCOUNT_CAPACITY', 503);
          id = Number(this.run(`INSERT INTO accounts(status,name,avatar,avatar_hash,password_salt,password_hash,recovery_hash,created_at,updated_at)
            VALUES('active',?,?,?,?,?,?,?,?)`, challenge.profile.name, image.avatar, image.avatarHash, hashed.salt, hashed.digest,
          digest('recovery', recoveryCode), now, now).lastInsertRowid);
        }
        this.run('INSERT INTO registrations(request_hash,account_id,device_id,public_key,encryption_key,profile_hash,owner) VALUES(?,?,?,?,?,?,?)',
          requestHash, id, challenge.identity.deviceId, challenge.identity.publicKey, challenge.encryptionKey, profileHash, Number(owner));
        return this.issueSession(this.account(id), this.putDevice(id, challenge), recoveryCode);
      });
    } finally { hashed.digest.fill(0); hashed.salt.fill(0); }
  }
  async login(body, context) {
    this.available(); record(body, ['challengeId', 'signature', 'password']);
    const challenge = this.consumeChallenge(body, 'login'); this.rate(context, 'auth', challenge.accountId);
    const account = this.account(challenge.accountId);
    const valid = await this.passwords.verify(body.password, account); this.available();
    if (!valid) fail('AUTH_FAILED', 401);
    return this.transaction(() => {
      const current = this.account(account.id);
      if (!current || current.password_version !== account.password_version) fail('AUTH_FAILED', 401);
      return this.issueSession(current, this.putDevice(current.id, challenge));
    });
  }
  async recover(body, context) {
    this.available(); record(body, ['challengeId', 'signature', 'recoveryCode', 'newPassword']);
    const challenge = this.consumeChallenge(body, 'recover'); this.rate(context, 'auth', challenge.accountId);
    let supplied;
    try { supplied = digest('recovery', proof.token(body.recoveryCode)); } catch { fail('AUTH_FAILED', 401); }
    const account = this.account(challenge.accountId);
    if (!account || !equal(account.recovery_hash, supplied)) fail('AUTH_FAILED', 401);
    const hashed = await this.passwords.hash(body.newPassword); this.available();
    const recoveryCode = token(), now = this.now();
    try {
      const result = this.transaction(() => {
        const current = this.account(account.id);
        if (!current || !equal(current.recovery_hash, supplied) || current.password_version !== account.password_version) fail('AUTH_FAILED', 401);
        this.run('UPDATE accounts SET password_salt=?,password_hash=?,password_version=password_version+1,recovery_hash=?,updated_at=? WHERE id=?',
          hashed.salt, hashed.digest, digest('recovery', recoveryCode), now, account.id);
        this.run('UPDATE sessions SET revoked_at=? WHERE account_id=? AND revoked_at IS NULL', now, account.id);
        this.run('UPDATE devices SET revoked_at=? WHERE account_id=? AND revoked_at IS NULL', now, account.id);
        return this.issueSession(this.account(account.id), this.putDevice(account.id, challenge), recoveryCode);
      });
      this.clearAddressing(account.id); return result;
    } finally { hashed.digest.fill(0); hashed.salt.fill(0); }
  }
  authenticate(accessToken, context) {
    this.available(); this.rate(context);
    try { proof.token(accessToken); } catch { fail('AUTH_REQUIRED', 401); }
    const session = this.get('SELECT * FROM sessions WHERE access_hash=? AND revoked_at IS NULL AND access_expires>?', digest('access', accessToken), this.now());
    if (!session) fail('AUTH_REQUIRED', 401);
    const account = this.account(session.account_id), device = this.device(session.account_id, session.device_id);
    if (!account || !device) fail('AUTH_REQUIRED', 401);
    return {session, account, device};
  }
  current(auth) {
    this.available();
    const session = this.get('SELECT * FROM sessions WHERE id=? AND revoked_at IS NULL AND access_expires>?', auth?.session?.id || '', this.now());
    if (!session) fail('AUTH_REQUIRED', 401);
    const account = this.account(session.account_id), device = this.device(session.account_id, session.device_id);
    if (!account || !device) fail('AUTH_REQUIRED', 401);
    return {session, account, device};
  }
  refresh(body, context) {
    this.available(); record(body, ['challengeId', 'signature', 'refreshToken']);
    const challenge = this.consumeChallenge(body, 'refresh'); this.rate(context);
    this.rates.take('refresh-device', challenge.accountId + ':' + challenge.identity.deviceId, 30, 60000);
    try { proof.token(body.refreshToken); } catch { fail('AUTH_FAILED', 401); }
    const hash = digest('refresh', body.refreshToken), now = this.now();
    const session = this.get('SELECT * FROM sessions WHERE refresh_hash=?', hash);
    if (!session) {
      const used = this.get('SELECT s.* FROM used_refresh u JOIN sessions s ON s.id=u.session_id WHERE u.hash=? AND u.expires_at>?', hash, now);
      if (used && used.account_id === challenge.accountId && used.device_id === challenge.identity.deviceId) {
        this.run('UPDATE sessions SET revoked_at=? WHERE id=?', now, used.id); this.clearAddressing(used.account_id, used.device_id);
      }
      fail('AUTH_FAILED', 401);
    }
    const account = this.account(session.account_id), device = this.device(session.account_id, session.device_id);
    if (!account || !device || session.revoked_at !== null || session.refresh_expires <= now || session.account_id !== challenge.accountId
      || session.device_id !== challenge.identity.deviceId || device.public_key !== challenge.identity.publicKey
      || device.encryption_key !== challenge.encryptionKey || session.refresh_count >= 8192) fail('AUTH_FAILED', 401);
    const accessToken = token(), refreshToken = token();
    return this.transaction(() => {
      // Keep the original family expiry: rotating a dormant credential never
      // turns a thirty-day sign-in into an indefinitely valid credential.
      this.run('INSERT INTO used_refresh(hash,session_id,expires_at) VALUES(?,?,?)', hash, session.id, session.refresh_expires);
      this.run('UPDATE sessions SET access_hash=?,refresh_hash=?,access_expires=?,updated_at=?,refresh_count=refresh_count+1 WHERE id=? AND revoked_at IS NULL',
        digest('access', accessToken), digest('refresh', refreshToken), now + ACCESS_TTL_MS, now, session.id);
      this.run('UPDATE devices SET last_seen_at=? WHERE account_id=? AND device_id=?', now, account.id, device.device_id);
      return {account: this.publicAccount(account), certificate: this.certificate(account, device), accessToken, refreshToken,
        accessExpiresAt: now + ACCESS_TTL_MS, refreshExpiresAt: session.refresh_expires};
    });
  }
  me(auth) {
    const {account, device, session} = this.current(auth);
    return {account: this.publicAccount(account), certificate: this.certificate(account, device), accessExpiresAt: session.access_expires,
      refreshExpiresAt: session.refresh_expires};
  }
  updateProfile(auth, body) {
    const {account, device} = this.current(auth); record(body, ['name', 'avatar']);
    const image = avatar(body.avatar), profile = proof.normalizeAccountProfile({name: body.name, avatarHash: image.avatarHash});
    this.run('UPDATE accounts SET name=?,avatar=?,avatar_hash=?,updated_at=? WHERE id=?', profile.name, image.avatar, image.avatarHash, this.now(), account.id);
    const current = this.account(account.id);
    return {account: this.publicAccount(current), certificate: this.certificate(current, device)};
  }
  devices(auth) {
    const {account, device} = this.current(auth);
    return {devices: this.all('SELECT * FROM devices WHERE account_id=? AND revoked_at IS NULL ORDER BY created_at,device_id', account.id)
      .map(value => ({deviceId: value.device_id, name: value.name, createdAt: value.created_at, lastSeenAt: value.last_seen_at, current: device.device_id === value.device_id}))};
  }
  revokeDevice(auth, deviceId) {
    const {account} = this.current(auth);
    if (typeof deviceId !== 'string' || !/^[a-f0-9]{32}$/.test(deviceId)) fail('INVALID_REQUEST');
    const now = this.now();
    this.transaction(() => {
      this.run('UPDATE devices SET revoked_at=? WHERE account_id=? AND device_id=? AND revoked_at IS NULL', now, account.id, deviceId);
      this.run('UPDATE sessions SET revoked_at=? WHERE account_id=? AND device_id=? AND revoked_at IS NULL', now, account.id, deviceId);
    });
    this.clearAddressing(account.id, deviceId); return {ok: true};
  }
  logout(auth) {
    const {account, device, session} = this.current(auth);
    this.run('UPDATE sessions SET revoked_at=? WHERE id=?', this.now(), session.id);
    this.clearAddressing(account.id, device.device_id); return {ok: true};
  }
  async changePassword(auth, body, context) {
    const {account, device} = this.current(auth); record(body, ['password', 'newPassword']); this.rate(context, 'auth', account.id);
    if (!await this.passwords.verify(body.password, account)) fail('AUTH_FAILED', 401);
    const hashed = await this.passwords.hash(body.newPassword);
    try {
      const result = this.transaction(() => {
        const current = this.current(auth);
        if (current.account.password_version !== account.password_version) fail('AUTH_FAILED', 401);
        const now = this.now();
        this.run('UPDATE accounts SET password_salt=?,password_hash=?,password_version=password_version+1,updated_at=? WHERE id=?', hashed.salt, hashed.digest, now, account.id);
        this.run('UPDATE sessions SET revoked_at=? WHERE account_id=? AND revoked_at IS NULL', now, account.id);
        return this.issueSession(this.account(account.id), device);
      });
      this.clearAddressing(account.id); return result;
    } finally { hashed.digest.fill(0); hashed.salt.fill(0); }
  }
  async rotateRecoveryCode(auth, body, context) {
    const {account} = this.current(auth); record(body, ['password']); this.rate(context, 'auth', account.id);
    if (!await this.passwords.verify(body.password, account)) fail('AUTH_FAILED', 401);
    const current = this.current(auth);
    if (current.account.password_version !== account.password_version) fail('AUTH_FAILED', 401);
    const recoveryCode = token();
    this.run('UPDATE accounts SET recovery_hash=?,updated_at=? WHERE id=?', digest('recovery', recoveryCode), this.now(), account.id);
    return {recoveryCode};
  }
  syncGet(auth) {
    const {account} = this.current(auth);
    const row = this.get('SELECT * FROM settings WHERE account_id=?', account.id);
    return row ? {revision: row.revision, state: JSON.parse(row.document), updatedAt: row.updated_at}
      : {revision: 0, state: null, updatedAt: null};
  }
  syncRevision(auth) {
    const {account} = this.current(auth);
    const row = this.get('SELECT revision,updated_at FROM settings WHERE account_id=?', account.id);
    return row ? {revision: row.revision, updatedAt: row.updated_at} : {revision: 0, updatedAt: null};
  }
  syncPut(auth, body) {
    const {account, device} = this.current(auth); record(body, ['revision', 'state']); integer(body.revision, 0);
    this.rates.take('sync-write', account.id, 60, 60000);
    const {validateSyncState} = require('../../desktop/mouse-sync-schema.cjs');
    let document;
    try { document = validateSyncState(body.state); } catch { fail('SYNC_INVALID'); }
    const serialized = JSON.stringify(document);
    if (Buffer.byteLength(serialized, 'utf8') > 2 * 1024 * 1024) fail('SYNC_INVALID');
    const now = this.now();
    const result = this.transaction(() => {
      const row = this.get('SELECT revision FROM settings WHERE account_id=?', account.id);
      if ((row?.revision || 0) !== body.revision) {
        const error = new IdentityError('SYNC_CONFLICT', 409); error.conflict = this.syncGet(auth); throw error;
      }
      const revision = body.revision + 1; integer(revision);
      this.run(`INSERT INTO settings(account_id,revision,schema_version,document,updated_at,updated_by) VALUES(?,?,?,?,?,?)
        ON CONFLICT(account_id) DO UPDATE SET revision=excluded.revision,schema_version=excluded.schema_version,
        document=excluded.document,updated_at=excluded.updated_at,updated_by=excluded.updated_by`, account.id, revision, 1, serialized, now, device.device_id);
      return {revision, state: document, updatedAt: now};
    });
    return result;
  }
  clearAddressing(accountId, deviceId) {
    for (const [key, value] of this.presence) if (value.accountId === accountId && (!deviceId || value.deviceId === deviceId)) this.presence.delete(key);
    for (const [key, value] of this.invitations) {
      if ((value.fromAccountId === accountId && (!deviceId || value.fromDeviceId === deviceId))
        || (value.recipientAccountId === accountId && (!deviceId || value.recipientDeviceId === deviceId))) this.invitations.delete(key);
    }
  }
  flashPresence(auth, body) {
    const {account, device} = this.current(auth); record(body); this.prune();
    this.rates.take('presence', account.id + ':' + device.device_id, 6, 60000);
    const key = account.id + ':' + device.device_id;
    if (!this.presence.has(key) && this.presence.size >= 2048) fail('FLASH_BUSY', 503);
    const expiresAt = this.now() + PRESENCE_TTL_MS;
    this.presence.set(key, {accountId: account.id, deviceId: device.device_id, expiresAt});
    this.run('UPDATE devices SET last_seen_at=? WHERE account_id=? AND device_id=?', this.now(), account.id, device.device_id);
    return {expiresAt, certificate: this.certificate(account, device)};
  }
  flashDevices(auth, accountId) {
    const caller = this.current(auth); integer(accountId); this.prune();
    this.rates.take('flash-lookup', caller.account.id, 30, 60000);
    const account = this.account(accountId);
    if (!account) return {account: null, devices: []};
    const devices = [];
    for (const presence of this.presence.values()) {
      if (presence.accountId !== accountId) continue;
      const device = this.device(accountId, presence.deviceId);
      if (device) devices.push({deviceId: device.device_id, name: device.name, certificate: this.certificate(account, device), expiresAt: presence.expiresAt});
    }
    return {account: devices.length ? this.publicAccount(account) : null, devices};
  }
  flashSend(auth, body) {
    const {account, device} = this.current(auth); record(body, ['recipientAccountId', 'recipientDeviceId', 'envelope']);
    integer(body.recipientAccountId); this.prune();
    if (typeof body.recipientDeviceId !== 'string' || !/^[a-f0-9]{32}$/.test(body.recipientDeviceId)) fail('INVALID_REQUEST');
    record(body.envelope, ['v', 'ephemeralKey', 'nonce', 'ciphertext']);
    if (body.envelope.v !== 1 || JSON.stringify(body.envelope).length > MAX_INVITE_BYTES) fail('INVALID_REQUEST');
    try { proof.encryptionPublicKey(body.envelope.ephemeralKey); proof.bytes64(body.envelope.nonce, 12); } catch { fail('INVALID_REQUEST'); }
    const encoded = body.envelope.ciphertext;
    if (typeof encoded !== 'string' || encoded.length < 24 || encoded.length > MAX_INVITE_BYTES || Buffer.from(encoded, 'base64').toString('base64') !== encoded) fail('INVALID_REQUEST');
    this.rates.take('invite-sender', account.id, 12, 60000);
    this.rates.take('invite-target', body.recipientAccountId + ':' + body.recipientDeviceId, 20, 60000);
    const presence = this.presence.get(body.recipientAccountId + ':' + body.recipientDeviceId);
    if (!presence || presence.expiresAt <= this.now() || !this.device(body.recipientAccountId, body.recipientDeviceId)) fail('DEVICE_OFFLINE', 409);
    if (account.id === body.recipientAccountId && device.device_id === body.recipientDeviceId) fail('INVALID_REQUEST');
    const queued = [...this.invitations.values()].filter(value => value.recipientAccountId === body.recipientAccountId && value.recipientDeviceId === body.recipientDeviceId).length;
    if (this.invitations.size >= MAX_INVITATIONS || queued >= 10) fail('FLASH_BUSY', 503);
    const invitationId = token(), expiresAt = this.now() + INVITE_TTL_MS;
    this.invitations.set(invitationId, {invitationId, fromAccountId: account.id, fromDeviceId: device.device_id,
      recipientAccountId: body.recipientAccountId, recipientDeviceId: body.recipientDeviceId, envelope: structuredClone(body.envelope), expiresAt});
    return {invitationId, expiresAt};
  }
  flashInbox(auth) {
    const {account, device} = this.current(auth); this.prune();
    this.rates.take('inbox', account.id + ':' + device.device_id, 30, 60000);
    const invitations = [];
    for (const [key, value] of this.invitations) {
      if (value.recipientAccountId !== account.id || value.recipientDeviceId !== device.device_id) continue;
      this.invitations.delete(key);
      invitations.push({invitationId: value.invitationId, fromAccountId: value.fromAccountId, fromDeviceId: value.fromDeviceId,
        envelope: value.envelope, expiresAt: value.expiresAt});
      if (invitations.length === 10) break;
    }
    return {invitations};
  }
  close() {
    if (this.closed) return;
    this.closed = true; this.passwords.close(); this.challenges.clear(); this.presence.clear(); this.invitations.clear();
    this.db.close();
  }
}

module.exports = {IdentityService, IdentityError, cleanError, privateDirectory, token,
  ACCESS_TTL_MS, REFRESH_TTL_MS, INVITE_TTL_MS, PRESENCE_TTL_MS};
