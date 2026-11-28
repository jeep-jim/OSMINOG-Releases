'use strict';

class IdentityError extends Error {
  constructor(code, status = 400) { super(code); this.name = 'IdentityError'; this.code = code; this.status = status; }
}
function fail(code, status = 400) { throw new IdentityError(code, status); }
function record(value, required = [], optional = []) {
  if (!value || typeof value !== 'object' || Array.isArray(value)
    || ![Object.prototype, null].includes(Object.getPrototypeOf(value))
    || required.some(key => !Object.hasOwn(value, key))
    || Object.keys(value).some(key => !required.includes(key) && !optional.includes(key))) fail('INVALID_REQUEST');
  return value;
}
function integer(value, min = 1, max = Number.MAX_SAFE_INTEGER) {
  if (!Number.isSafeInteger(value) || value < min || value > max) fail('INVALID_REQUEST');
  return value;
}
module.exports = {IdentityError, fail, record, integer};
