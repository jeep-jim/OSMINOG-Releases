'use strict';

// Public account proofs only. A server key must come from trusted application
// configuration, never from the received certificate or an editable profile.
const {createHash, createPublicKey, verify} = require('node:crypto');
const CHALLENGE_TTL_MS = 5 * 60 * 1000;
const CERTIFICATE_TTL_MS = 30 * 24 * 60 * 60 * 1000;
const DEVICE_CERTIFICATE_TTL_MS = 24 * 60 * 60 * 1000;
const CLOCK_SKEW_MS = 60 * 1000;
const HEX64 = /^[a-f0-9]{64}$/;
const DEVICE_ID = /^[a-f0-9]{32}$/;
const TOKEN = /^[A-Za-z0-9_-]{43}$/;

class MouseAccountError extends Error {
  constructor(code, message) { super(message); this.name = 'MouseAccountError'; this.code = code; }
}
function fail(code, message) { throw new MouseAccountError(code, message); }
function shape(value, required, optional = []) {
  if (!value || typeof value !== 'object' || Array.isArray(value)
    || required.some(key => !Object.hasOwn(value, key))
    || Object.keys(value).some(key => !required.includes(key) && !optional.includes(key))) {
    fail('ACCOUNT_FORMAT', 'Invalid account record shape.');
  }
}
function bytes64(value, length) {
  if (typeof value !== 'string' || value.length !== Math.ceil(length / 3) * 4) fail('ACCOUNT_FORMAT', 'Invalid account encoding.');
  const bytes = Buffer.from(value, 'base64');
  if (bytes.length !== length || bytes.toString('base64') !== value) fail('ACCOUNT_FORMAT', 'Invalid account encoding.');
  return bytes;
}
function publicKey(value) {
  const der = bytes64(value, 44);
  let key;
  try { key = createPublicKey({key: der, type: 'spki', format: 'der'}); }
  catch { fail('ACCOUNT_FORMAT', 'Invalid account public key.'); }
  if (key.asymmetricKeyType !== 'ed25519' || !key.export({type: 'spki', format: 'der'}).equals(der)) {
    fail('ACCOUNT_FORMAT', 'An Ed25519 account public key is required.');
  }
  return {key, keyId: createHash('sha256').update(der).digest('hex')};
}
function encryptionPublicKey(value) {
  const der = bytes64(value, 44);
  let key;
  try { key = createPublicKey({key: der, type: 'spki', format: 'der'}); }
  catch { fail('ACCOUNT_FORMAT', 'Invalid device encryption key.'); }
  if (key.asymmetricKeyType !== 'x25519' || !key.export({type: 'spki', format: 'der'}).equals(der)) {
    fail('ACCOUNT_FORMAT', 'An X25519 device encryption key is required.');
  }
  return key;
}
function timestamp(value) {
  if (!Number.isSafeInteger(value) || value < 0) fail('ACCOUNT_FORMAT', 'Invalid account timestamp.');
  return value;
}
function token(value) {
  if (typeof value !== 'string' || !TOKEN.test(value) || Buffer.from(value, 'base64url').toString('base64url') !== value) {
    fail('ACCOUNT_FORMAT', 'Invalid account challenge identifier.');
  }
  return value;
}
function normalizeAccountProfile(value) {
  shape(value, ['name'], ['avatarHash']);
  if (typeof value.name !== 'string') fail('ACCOUNT_FORMAT', 'Invalid account display name.');
  const name = value.name.trim().normalize('NFC');
  if (!name || [...name].length > 80 || Buffer.byteLength(name, 'utf8') > 320
    || /[\u0000-\u001f\u007f\u202a-\u202e\u2066-\u2069]/u.test(name)) {
    fail('ACCOUNT_FORMAT', 'Invalid account display name.');
  }
  const avatarHash = value.avatarHash === undefined ? null : value.avatarHash;
  if (avatarHash !== null && (typeof avatarHash !== 'string' || !HEX64.test(avatarHash))) {
    fail('ACCOUNT_FORMAT', 'The avatar must use a SHA-256 digest of its saved image bytes.');
  }
  return Object.freeze({name, avatarHash});
}
function readIdentity(value) {
  shape(value, ['deviceId', 'name', 'publicKey']);
  if (typeof value.deviceId !== 'string' || !DEVICE_ID.test(value.deviceId)
    || typeof value.name !== 'string' || !value.name.trim() || Buffer.byteLength(value.name, 'utf8') > 256
    || /[\u0000-\u001f\u007f]/u.test(value.name)) fail('ACCOUNT_FORMAT', 'Invalid account device identity.');
  const key = publicKey(value.publicKey);
  if (value.deviceId !== key.keyId.slice(0, 32)) fail('ACCOUNT_FORMAT', 'Device identity does not match its public key.');
  return Object.freeze({deviceId: value.deviceId, name: value.name, publicKey: value.publicKey});
}
function challengePayload(value) {
  shape(value, ['v', 'challengeId', 'action', 'registryId', 'issuerKeyId', 'identity', 'profile', 'issuedAt', 'expiresAt'], ['transcriptHash']);
  if (value.v !== 1 || !['register', 'claim-owner'].includes(value.action)
    || typeof value.issuerKeyId !== 'string' || !HEX64.test(value.issuerKeyId)) fail('ACCOUNT_FORMAT', 'Invalid account challenge.');
  const issuedAt = timestamp(value.issuedAt), expiresAt = timestamp(value.expiresAt);
  if (expiresAt <= issuedAt || expiresAt - issuedAt > CHALLENGE_TTL_MS) fail('ACCOUNT_FORMAT', 'Invalid account challenge lifetime.');
  const profile = normalizeAccountProfile(value.profile);
  if (profile.name !== value.profile.name || profile.avatarHash !== value.profile.avatarHash) fail('ACCOUNT_FORMAT', 'The challenge profile is not canonical.');
  return {v: 1, challengeId: token(value.challengeId), action: value.action, registryId: token(value.registryId),
    issuerKeyId: value.issuerKeyId, identity: readIdentity(value.identity), profile, issuedAt, expiresAt};
}
function accountChallengeTranscript(value) {
  const hash = createHash('sha256').update('MouseAccountChallenge:v1:' + JSON.stringify(challengePayload(value))).digest('hex');
  if (value.transcriptHash !== undefined && value.transcriptHash !== hash) fail('ACCOUNT_PROOF_INVALID', 'The account challenge transcript does not match.');
  return hash;
}
function authChallengeTranscript(value) {
  shape(value, ['v', 'challengeId', 'action', 'registryId', 'issuerKeyId', 'identity', 'encryptionKey',
    'accountId', 'registrationId', 'profile', 'issuedAt', 'expiresAt'], ['transcriptHash']);
  if (value.v !== 2 || !['register', 'claim-owner', 'login', 'recover', 'refresh'].includes(value.action)
    || typeof value.issuerKeyId !== 'string' || !HEX64.test(value.issuerKeyId)) fail('ACCOUNT_FORMAT', 'Invalid authentication challenge.');
  const registration = ['register', 'claim-owner'].includes(value.action);
  if (registration ? value.accountId !== null : !Number.isSafeInteger(value.accountId) || value.accountId < 1) {
    fail('ACCOUNT_FORMAT', 'Invalid authentication account.');
  }
  if (registration) token(value.registrationId);
  else if (value.registrationId !== null) fail('ACCOUNT_FORMAT', 'Invalid registration identifier.');
  const profile = registration ? normalizeAccountProfile(value.profile) : null;
  if (profile ? profile.name !== value.profile.name || profile.avatarHash !== value.profile.avatarHash : value.profile !== null) {
    fail('ACCOUNT_FORMAT', 'The authentication profile is not canonical.');
  }
  encryptionPublicKey(value.encryptionKey);
  const issuedAt = timestamp(value.issuedAt), expiresAt = timestamp(value.expiresAt);
  if (expiresAt <= issuedAt || expiresAt - issuedAt > CHALLENGE_TTL_MS) fail('ACCOUNT_FORMAT', 'Invalid authentication challenge lifetime.');
  const canonical = {v: 2, challengeId: token(value.challengeId), action: value.action, registryId: token(value.registryId),
    issuerKeyId: value.issuerKeyId, identity: readIdentity(value.identity), encryptionKey: value.encryptionKey,
    accountId: value.accountId, registrationId: value.registrationId, profile, issuedAt, expiresAt};
  const hash = createHash('sha256').update('MouseAccountChallenge:v2:' + JSON.stringify(canonical)).digest('hex');
  if (value.transcriptHash !== undefined && value.transcriptHash !== hash) fail('ACCOUNT_PROOF_INVALID', 'The authentication transcript does not match.');
  return hash;
}
function certificateClaims(value) {
  const v2 = value?.v === 2;
  shape(value, ['v', 'issuerKeyId', 'registryId', 'accountId', 'deviceId', 'publicKey', ...(v2 ? ['encryptionKey'] : []), 'name', 'avatarHash', 'issuedAt', 'expiresAt']);
  if (![1, 2].includes(value.v) || typeof value.issuerKeyId !== 'string' || !HEX64.test(value.issuerKeyId)
    || !Number.isSafeInteger(value.accountId) || value.accountId < 1
    || typeof value.deviceId !== 'string' || !DEVICE_ID.test(value.deviceId)) fail('ACCOUNT_FORMAT', 'Invalid account certificate claims.');
  if (publicKey(value.publicKey).keyId.slice(0, 32) !== value.deviceId) fail('ACCOUNT_FORMAT', 'Account certificate device key does not match.');
  if (v2) encryptionPublicKey(value.encryptionKey);
  const profile = normalizeAccountProfile({name: value.name, avatarHash: value.avatarHash});
  if (profile.name !== value.name || profile.avatarHash !== value.avatarHash) fail('ACCOUNT_FORMAT', 'The certificate profile is not canonical.');
  const issuedAt = timestamp(value.issuedAt), expiresAt = timestamp(value.expiresAt);
  if (expiresAt <= issuedAt || expiresAt - issuedAt > (v2 ? DEVICE_CERTIFICATE_TTL_MS : CERTIFICATE_TTL_MS)) fail('ACCOUNT_FORMAT', 'Invalid account certificate lifetime.');
  return Object.freeze({v: value.v, issuerKeyId: value.issuerKeyId, registryId: token(value.registryId), accountId: value.accountId,
    deviceId: value.deviceId, publicKey: value.publicKey, ...(v2 ? {encryptionKey: value.encryptionKey} : {}),
    name: profile.name, avatarHash: profile.avatarHash, issuedAt, expiresAt});
}
function certificateSigningBytes(claims) {
  const canonical = certificateClaims(claims);
  return Buffer.from('MouseAccountCertificate:v' + canonical.v + ':' + JSON.stringify(canonical), 'utf8');
}
function verifyAccountCertificate({certificate, serverPublicKey, deviceId, now = Date.now()} = {}) {
  if (!serverPublicKey) fail('ACCOUNT_NOT_CONFIGURED', 'A trusted account server public key is required.');
  const issuer = publicKey(serverPublicKey);
  shape(certificate, ['claims', 'signature']);
  const claims = certificateClaims(certificate.claims);
  if (typeof deviceId !== 'string' || !DEVICE_ID.test(deviceId) || claims.deviceId !== deviceId) {
    fail('ACCOUNT_DEVICE_MISMATCH', 'The account certificate belongs to another device.');
  }
  timestamp(now);
  if (claims.issuerKeyId !== issuer.keyId
    || !verify(null, certificateSigningBytes(claims), issuer.key, bytes64(certificate.signature, 64))) {
    fail('ACCOUNT_PROOF_INVALID', 'The account certificate is not signed by the trusted server.');
  }
  if (claims.expiresAt <= now || claims.issuedAt > now + CLOCK_SKEW_MS) fail('ACCOUNT_EXPIRED', 'The account certificate is outside its validity period.');
  return Object.freeze({ok: true, accountId: claims.accountId, claims});
}

module.exports = {verifyAccountCertificate, normalizeAccountProfile, accountChallengeTranscript, authChallengeTranscript,
  certificateSigningBytes, certificateClaims, readIdentity, publicKey, encryptionPublicKey, bytes64, shape, timestamp, token,
  MouseAccountError, CHALLENGE_TTL_MS, CERTIFICATE_TTL_MS, DEVICE_CERTIFICATE_TTL_MS, CLOCK_SKEW_MS};
