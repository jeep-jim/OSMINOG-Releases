'use strict';

const {createHash} = require('node:crypto');
const {fail} = require('./errors.cjs');

// No attacker-controlled value survives here in plaintext. Full buckets expire;
// capacity rejects new buckets rather than evicting an attacker's previous limit.
class RateLimiter {
  constructor({now = Date.now, maxKeys = 10000} = {}) { this.now = now; this.maxKeys = maxKeys; this.buckets = new Map(); }
  take(namespace, value, limit, windowMs) {
    const now = this.now(), key = namespace + ':' + createHash('sha256').update(String(value)).digest('hex');
    let bucket = this.buckets.get(key);
    if (!bucket || bucket.expiresAt <= now) {
      this.prune(now);
      if (!this.buckets.has(key) && this.buckets.size >= this.maxKeys) fail('RATE_LIMITED', 429);
      bucket = {count: 0, expiresAt: now + windowMs}; this.buckets.set(key, bucket);
    }
    if (bucket.count >= limit) fail('RATE_LIMITED', 429);
    bucket.count += 1;
  }
  prune(now = this.now()) { for (const [key, bucket] of this.buckets) if (bucket.expiresAt <= now) this.buckets.delete(key); }
}
module.exports = {RateLimiter};
