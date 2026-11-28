'use strict';

const {createHash} = require('node:crypto');
const {inflateSync} = require('node:zlib');
const {fail} = require('./errors.cjs');
const MAX_AVATAR_BYTES = 512 * 1024;
const CRC = Array.from({length: 256}, (_, index) => {
  let value = index;
  for (let i = 0; i < 8; i++) value = (value >>> 1) ^ (value & 1 ? 0xedb88320 : 0);
  return value >>> 0;
});
function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) crc = (crc >>> 8) ^ CRC[(crc ^ byte) & 255];
  return (crc ^ 0xffffffff) >>> 0;
}
function avatar(value) {
  if (value === null) return {avatar: null, avatarHash: null};
  const prefix = 'data:image/png;base64,';
  if (typeof value !== 'string' || !value.startsWith(prefix) || value.length > prefix.length + Math.ceil(MAX_AVATAR_BYTES / 3) * 4) fail('AVATAR_INVALID');
  const encoded = value.slice(prefix.length), bytes = Buffer.from(encoded, 'base64');
  if (bytes.length < 57 || bytes.length > MAX_AVATAR_BYTES || bytes.toString('base64') !== encoded
    || !bytes.subarray(0, 8).equals(Buffer.from('89504e470d0a1a0a', 'hex'))) fail('AVATAR_INVALID');
  let offset = 8, width, height, channels, ended = false, idatEnded = false;
  const compressed = [], seen = new Set();
  while (offset < bytes.length) {
    if (offset + 12 > bytes.length) fail('AVATAR_INVALID');
    const size = bytes.readUInt32BE(offset), type = bytes.toString('latin1', offset + 4, offset + 8), end = offset + size + 12;
    if (end > bytes.length || crc32(bytes.subarray(offset + 4, end - 4)) !== bytes.readUInt32BE(end - 4)) fail('AVATAR_INVALID');
    const data = bytes.subarray(offset + 8, end - 4);
    if (offset === 8 && type !== 'IHDR') fail('AVATAR_INVALID');
    if (type === 'IHDR') {
      if (width !== undefined || size !== 13) fail('AVATAR_INVALID');
      width = data.readUInt32BE(0); height = data.readUInt32BE(4);
      channels = {0: 1, 2: 3, 4: 2, 6: 4}[data[9]];
      if (width < 1 || height < 1 || width > 256 || height > 256 || !channels || data[8] !== 8
        || data[10] !== 0 || data[11] !== 0 || data[12] !== 0) fail('AVATAR_INVALID');
    } else if (type === 'IDAT') {
      if (idatEnded || ended || !width) fail('AVATAR_INVALID');
      compressed.push(data);
    } else if (type === 'IEND') {
      if (size !== 0 || !compressed.length || end !== bytes.length) fail('AVATAR_INVALID');
      ended = true;
    } else {
      // Native thumbnails may include colour/density information, never text,
      // EXIF, arbitrary ancillary blobs or animation frames.
      const sizes = {sRGB: 1, gAMA: 4, cHRM: 32, pHYs: 9};
      if (sizes[type] !== size || ended || seen.has(type)) fail('AVATAR_INVALID');
      seen.add(type);
      if (compressed.length) idatEnded = true;
    }
    offset = end;
  }
  if (!ended) fail('AVATAR_INVALID');
  const stride = width * channels + 1, expected = stride * height;
  let pixels;
  const stream = Buffer.concat(compressed);
  try {
    const inflated = inflateSync(stream, {maxOutputLength: expected, info: true});
    if (inflated.engine.bytesWritten !== stream.length) fail('AVATAR_INVALID');
    pixels = inflated.buffer;
  } catch { fail('AVATAR_INVALID'); }
  if (pixels.length !== expected) fail('AVATAR_INVALID');
  for (let i = 0; i < pixels.length; i += stride) if (pixels[i] > 4) fail('AVATAR_INVALID');
  return {avatar: value, avatarHash: createHash('sha256').update(bytes).digest('hex')};
}
module.exports = {avatar, MAX_AVATAR_BYTES};
