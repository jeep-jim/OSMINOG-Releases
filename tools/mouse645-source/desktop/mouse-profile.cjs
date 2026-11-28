'use strict';
// Local presentation data is a draft. A Mouse ID comes only from a pinned, signed account certificate.
const fs = require('node:fs/promises');
const {constants} = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {randomBytes, createHash} = require('node:crypto');
const MAX_AVATAR_BYTES = 512 * 1024;
const MAX_PICK_BYTES = 4 * 1024 * 1024;
const MAX_PROFILE_BYTES = 1024 * 1024;
const PNG_PREFIX = 'data:image/png;base64,';
const PNG_MAGIC = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
function need(value, message) { if (!value) throw new Error(message); }
function profileName(value, allowEmpty = false) {
  need(typeof value === 'string' && Buffer.byteLength(value) <= 512, 'Имя слишком длинное.');
  const name = value.trim().normalize('NFC');
  need(!/[\x00-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069]/.test(name) && Array.from(name).length <= 80 && (allowEmpty || name.length > 0), 'Введите имя длиной от 1 до 80 символов.');
  return name;
}
function avatarBytes(value) {
  if (value === null) return null;
  need(typeof value === 'string' && value.startsWith(PNG_PREFIX) && value.length <= PNG_PREFIX.length + Math.ceil(MAX_AVATAR_BYTES / 3) * 4, 'Недопустимое фото профиля.');
  const encoded = value.slice(PNG_PREFIX.length), bytes = Buffer.from(encoded, 'base64');
  need(bytes.length >= 33 && bytes.length <= MAX_AVATAR_BYTES && bytes.toString('base64') === encoded && bytes.subarray(0, 8).equals(PNG_MAGIC)
    && bytes.readUInt32BE(8) === 13 && bytes.toString('ascii', 12, 16) === 'IHDR', 'Недопустимое фото профиля.');
  need(bytes.readUInt32BE(16) > 0 && bytes.readUInt32BE(16) <= 256 && bytes.readUInt32BE(20) > 0 && bytes.readUInt32BE(20) <= 256, 'Фото профиля должно быть не больше 256 × 256.');
  return bytes;
}
function avatarHash(value) { const bytes = avatarBytes(value); return bytes ? createHash('sha256').update(bytes).digest('hex') : null; }
class MouseProfile {
  constructor({directory, electron, window, canUse = () => true, getIdentity, serverPublicKey = null, flashAvailable = () => false}) {
    need(path.isAbsolute(directory), 'Absolute profile directory required');
    this.directory = directory; this.e = electron; this.window = window; this.canUse = canUse; this.getIdentity = getIdentity;
    this.serverPublicKey = serverPublicKey; this.flashAvailable = flashAvailable;
    this.value = {v: 1, name: '', avatar: null, certificate: null}; this.epoch = 0; this.picker = false; this.activeAvatarIO = new Set();
    this.queue = Promise.resolve(); this.lastWrite = this.queue; this.ready = this.initialize(); this.ready.catch(() => {});
  }
  async initialize() {
    await fs.mkdir(this.directory, {recursive: true, mode: 0o700});
    const stat = await fs.lstat(this.directory); need(stat.isDirectory() && !stat.isSymbolicLink(), 'Unsafe profile directory');
    this.directory = await fs.realpath(this.directory); this.filename = path.join(this.directory, 'profile.json');
    let handle;
    try { handle = await fs.open(this.filename, constants.O_RDONLY | (constants.O_NOFOLLOW || 0)); }
    catch (error) { if (error.code === 'ENOENT') return; throw error; }
    try {
      const stat = await handle.stat(); need(stat.isFile() && stat.size <= MAX_PROFILE_BYTES, 'Invalid saved profile');
      const saved = JSON.parse(await handle.readFile('utf8')); need(saved?.v === 1, 'Unsupported profile data');
      this.value = {v: 1, name: profileName(saved.name, true), avatar: saved.avatar ?? null, certificate: saved.certificate ?? null};
      avatarBytes(this.value.avatar);
    } finally { await handle.close(); }
  }
  check(epoch = this.epoch) { need(this.canUse() && epoch === this.epoch, 'Профиль недоступен в этом режиме браузера.'); }
  cancelPending() { this.epoch++; }
  async state() {
    const epoch = this.epoch; this.check(epoch); await this.ready; await this.queue; this.check(epoch);
    // The identity lookup may yield while another profile edit is committed.
    // Display data and its certificate must come from the same snapshot.
    const value = this.value;
    const result = {name: value.name, avatar: value.avatar, mouseId: null, verified: false,
      deviceName: os.hostname().replace(/[\x00-\x1f\x7f]/g, '').slice(0, 100) || 'Mouse', flashAvailable: !!this.flashAvailable()};
    if (value.certificate && this.serverPublicKey && this.getIdentity) {
      try {
        const device = await this.getIdentity(); this.check(epoch);
        const verified = require('./mouse-account-proof.cjs').verifyAccountCertificate({certificate: value.certificate, serverPublicKey: this.serverPublicKey, deviceId: device.identity.deviceId});
        if (verified.ok && verified.claims.name === value.name && verified.claims.avatarHash === avatarHash(value.avatar)) {
          result.mouseId = verified.accountId; result.verified = true;
        }
      } catch { /* A draft or invalid/expired certificate never becomes a public Mouse ID. */ }
    }
    this.check(epoch); return result;
  }
  async save(change, epoch) {
    await this.ready; this.check(epoch);
    const operation = this.queue.then(async () => {
      this.check(epoch); const next = {...this.value, ...change};
      const text = JSON.stringify(next); need(Buffer.byteLength(text) <= MAX_PROFILE_BYTES, 'Profile record is too large');
      const temporary = path.join(this.directory, '.profile-' + randomBytes(12).toString('hex') + '.tmp');
      let handle;
      try {
        handle = await fs.open(temporary, 'wx', 0o600); await handle.writeFile(text); await handle.sync(); await handle.close(); handle = null;
        this.check(epoch); await fs.rename(temporary, this.filename); this.value = next;
      } finally { if (handle) await handle.close(); await fs.unlink(temporary).catch(error => { if (error.code !== 'ENOENT') throw error; }); }
    });
    this.lastWrite = operation; this.queue = operation.catch(() => {}); await operation; return this.state();
  }
  async call(action, payload = {}) {
    const epoch = this.epoch; this.check(epoch); await this.ready; this.check(epoch);
    need(payload && typeof payload === 'object' && !Array.isArray(payload), 'Invalid profile request');
    if (action === 'state') return this.state();
    if (action === 'set') {
      need(Object.keys(payload).length === 1 && Object.hasOwn(payload, 'name'), 'Через настройки можно изменить только имя.');
      return this.save({name: profileName(payload.name)}, epoch);
    }
    if (action === 'remove-avatar') return this.save({avatar: null}, epoch);
    if (action === 'choose-avatar') {
      need(!this.picker, 'Выбор фотографии уже открыт.'); this.picker = true;
      try {
        const selected = await this.e.dialog.showOpenDialog(this.window, {title: 'Фото профиля Mouse', buttonLabel: 'Выбрать фото',
          properties: ['openFile', 'dontAddToRecent'], filters: [{name: 'Изображения', extensions: ['png', 'jpg', 'jpeg', 'webp']}]});
        this.check(epoch);
        if (selected.canceled || selected.filePaths?.length !== 1) return {...await this.state(), canceled: true};
        const filename = selected.filePaths[0];
        // Track only work after a native path has been selected. Register the
        // promise before its first I/O; privacy/quit must not await an open
        // dialog, but must drain any metadata read, thumbnail or save in flight.
        const io = Promise.resolve().then(async () => {
          this.check(epoch); const stat = await fs.lstat(filename); this.check(epoch);
          need(stat.isFile() && !stat.isSymbolicLink() && stat.size > 0 && stat.size <= MAX_PICK_BYTES, 'Выберите PNG, JPEG или WebP размером до 4 МБ.');
          const thumbnail = await this.e.nativeImage.createThumbnailFromPath(filename, {width: 256, height: 256}); this.check(epoch);
          need(!thumbnail.isEmpty(), 'Не удалось прочитать фотографию.');
          const data = thumbnail.toPNG(); need(data.length <= MAX_AVATAR_BYTES, 'Фотография после обработки слишком большая.');
          const avatar = PNG_PREFIX + data.toString('base64'); avatarBytes(avatar);
          return this.save({avatar}, epoch);
        });
        this.activeAvatarIO.add(io);
        try { return await io; } finally { this.activeAvatarIO.delete(io); }
      } finally { this.picker = false; }
    }
    throw new Error('Unsupported profile action');
  }
  // Reserved for a trusted account transport. This is deliberately not an IPC action.
  async acceptCertificate(certificate) {
    const epoch = this.epoch; this.check(epoch); await this.ready;
    need(this.serverPublicKey && this.getIdentity, 'Account service is not configured');
    const device = await this.getIdentity(); this.check(epoch);
    const verified = require('./mouse-account-proof.cjs').verifyAccountCertificate({certificate, serverPublicKey: this.serverPublicKey, deviceId: device.identity.deviceId});
    need(verified.claims.name === this.value.name && verified.claims.avatarHash === avatarHash(this.value.avatar), 'Account certificate does not match this profile');
    return this.save({certificate}, epoch);
  }
  async flush() {
    await this.ready.catch(() => {});
    while (this.activeAvatarIO.size) await Promise.allSettled([...this.activeAvatarIO]);
    await this.queue;
  }
}
module.exports = {MouseProfile, profileName, avatarBytes, avatarHash, MAX_AVATAR_BYTES};
