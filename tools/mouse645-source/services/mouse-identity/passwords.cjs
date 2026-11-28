'use strict';

const {randomBytes, scrypt, timingSafeEqual} = require('node:crypto');
const {fail} = require('./errors.cjs');
// OWASP's 32 MiB scrypt configuration. The queue is global to this process,
// including unknown-account comparisons, so password traffic cannot multiply RAM.
const PARAMETERS = Object.freeze({N: 32768, r: 8, p: 3, maxmem: 40 * 1024 * 1024});
const COMMON = new Set(['passwordpassword', 'password123456789', '123456789012345', '1234567890123456',
  'qwertyuiopasdfgh', 'qwertyuiopasdfghjkl', 'парольпарольпароль', 'iloveyouiloveyou', 'letmeinletmein123',
  'adminadminadmin', 'mousemousemouse', 'correcthorsebatterystaple']);

function passwordBytes(value, {newPassword = false} = {}) {
  if (typeof value !== 'string' || value.length > 256 || /[\ud800-\udbff](?![\udc00-\udfff])|(?<![\ud800-\udbff])[\udc00-\udfff]/u.test(value)) fail('PASSWORD_POLICY');
  const normalized = value.normalize('NFC');
  const length = [...normalized].length;
  if (length < 15 || length > 128 || Buffer.byteLength(normalized, 'utf8') > 512 || /\u0000/u.test(normalized)) fail('PASSWORD_POLICY');
  if (newPassword) {
    const comparable = normalized.toLowerCase().replace(/[\s_-]+/gu, '');
    if (COMMON.has(comparable) || /^(.{1,4})\1+$/u.test(comparable) || /^(?:0123456789|1234567890){1,13}\d*$/u.test(comparable)) {
      fail('PASSWORD_TOO_COMMON');
    }
  }
  return Buffer.from(normalized, 'utf8');
}

class PasswordHasher {
  constructor({maxQueue = 8} = {}) { this.maxQueue = maxQueue; this.queue = []; this.active = false; this.closed = false; }
  derive(password, salt) {
    if (this.closed || (this.active && this.queue.length >= this.maxQueue)) {
      password.fill(0); fail('AUTH_BUSY', 503);
    }
    return new Promise((resolve, reject) => {
      this.queue.push({password, salt, resolve, reject}); this.run();
    });
  }
  run() {
    if (this.active || !this.queue.length) return;
    this.active = true;
    const job = this.queue.shift();
    scrypt(job.password, job.salt, 32, PARAMETERS, (error, result) => {
      job.password.fill(0); this.active = false;
      if (error) job.reject(Object.assign(new Error('AUTH_UNAVAILABLE'), {code: 'AUTH_UNAVAILABLE', status: 503}));
      else job.resolve(result);
      this.run();
    });
  }
  async hash(value) {
    const password = passwordBytes(value, {newPassword: true}), salt = randomBytes(16);
    const digest = await this.derive(password, salt);
    return {salt, digest};
  }
  async verify(value, stored) {
    let bytes, validInput = true;
    try { bytes = passwordBytes(value); } catch { validInput = false; bytes = Buffer.from('invalid password comparison value'); }
    const salt = stored ? Buffer.from(stored.password_salt) : Buffer.alloc(16, 0x53);
    const expected = stored ? Buffer.from(stored.password_hash) : Buffer.alloc(32);
    const actual = await this.derive(bytes, salt);
    const valid = expected.length === actual.length && timingSafeEqual(expected, actual);
    actual.fill(0);
    return Boolean(stored && validInput && valid);
  }
  close() {
    this.closed = true;
    for (const job of this.queue.splice(0)) {
      job.password.fill(0); job.reject(Object.assign(new Error('AUTH_UNAVAILABLE'), {code: 'AUTH_UNAVAILABLE', status: 503}));
    }
  }
}
module.exports = {PasswordHasher, passwordBytes, PARAMETERS};
