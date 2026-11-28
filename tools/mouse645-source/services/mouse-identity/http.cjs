'use strict';

const http = require('node:http');
const https = require('node:https');
const {isIP} = require('node:net');
const {IdentityError, fail} = require('./errors.cjs');
const {cleanError} = require('./service.cjs');
const {RateLimiter} = require('./limits.cjs');

const DEFAULT_BODY_LIMIT = 16 * 1024;
const AVATAR_BODY_LIMIT = 704 * 1024;
const SYNC_BODY_LIMIT = 2 * 1024 * 1024 + 256;
const GLOBAL_BODY_LIMIT = 8 * 1024 * 1024;
const MAX_ACTIVE = 32;
function loopback(value) { return value === '127.0.0.1' || value === '::1' || value === '::ffff:127.0.0.1'; }
function oneHeader(req, name) {
  let count = 0;
  for (let i = 0; i < req.rawHeaders.length; i += 2) if (req.rawHeaders[i].toLowerCase() === name) count++;
  if (count > 1) fail('INVALID_REQUEST');
  return req.headers[name];
}
function clientContext(req, {trustLoopbackProxy, allowInsecureLoopback}) {
  const directIP = req.socket.remoteAddress || '';
  if (!isIP(directIP)) fail('HTTPS_REQUIRED', 400);
  let ip = directIP, secure = req.socket.encrypted === true;
  const forwardedProto = oneHeader(req, 'x-forwarded-proto');
  const realIP = oneHeader(req, 'x-real-ip');
  const forwardedIP = oneHeader(req, 'x-forwarded-for');
  if (trustLoopbackProxy && loopback(directIP) && forwardedProto !== undefined) {
    if (forwardedProto !== 'https' || typeof realIP !== 'string' || !isIP(realIP)
      || forwardedIP !== undefined && forwardedIP !== realIP) fail('INVALID_PROXY', 400);
    secure = true; ip = realIP;
  } else if (forwardedProto !== undefined || realIP !== undefined || forwardedIP !== undefined) fail('INVALID_PROXY', 400);
  if (!secure && !(allowInsecureLoopback && loopback(directIP)) && !(loopback(directIP) && req.method === 'GET' && req.url === '/health')) {
    fail('HTTPS_REQUIRED', 400);
  }
  return {ip, secure};
}
function bodyLimit(route) {
  if (route === 'PUT /v1/accounts/sync') return SYNC_BODY_LIMIT;
  if (['POST /v1/accounts/register', 'POST /v1/accounts/claim-owner', 'PUT /v1/accounts/profile'].includes(route)) return AVATAR_BODY_LIMIT;
  if (route === 'POST /v1/accounts/flash/invitations') return 20 * 1024;
  return DEFAULT_BODY_LIMIT;
}
function readJSON(req, maximum, memory) {
  if (oneHeader(req, 'content-type') !== 'application/json') fail('JSON_REQUIRED', 415);
  const encoding = oneHeader(req, 'content-encoding');
  if (encoding !== undefined && encoding !== 'identity') fail('ENCODING_UNSUPPORTED', 415);
  const lengthHeader = oneHeader(req, 'content-length');
  if (lengthHeader !== undefined && (!/^\d{1,10}$/.test(lengthHeader) || Number(lengthHeader) > maximum)) fail('BODY_TOO_LARGE', 413);
  return new Promise((resolve, reject) => {
    const parts = []; let size = 0, settled = false;
    const timer = setTimeout(() => finish(new IdentityError('REQUEST_TIMEOUT', 408)), 10000); timer.unref();
    function finish(error) {
      if (settled) return; settled = true; clearTimeout(timer);
      req.off('data', data); req.off('end', end); req.off('aborted', aborted); req.off('error', aborted);
      memory.bytes -= size;
      if (error) { parts.length = 0; reject(error); return; }
      let result;
      try { result = JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(Buffer.concat(parts, size))); }
      catch { reject(new IdentityError('INVALID_JSON')); return; }
      if (!result || typeof result !== 'object' || Array.isArray(result)) { reject(new IdentityError('INVALID_REQUEST')); return; }
      resolve(result);
    }
    function data(bytes) {
      if (size + bytes.length > maximum) { finish(new IdentityError('BODY_TOO_LARGE', 413)); return; }
      if (memory.bytes + bytes.length > GLOBAL_BODY_LIMIT) { finish(new IdentityError('SERVICE_BUSY', 503)); return; }
      size += bytes.length; memory.bytes += bytes.length; parts.push(bytes);
    }
    function end() { finish(); }
    function aborted() { finish(new IdentityError('REQUEST_ABORTED', 400)); }
    req.on('data', data); req.on('end', end); req.on('aborted', aborted); req.on('error', aborted);
  });
}
function response(res, status, value, {close = false} = {}) {
  if (res.writableEnded || res.destroyed) return;
  res.statusCode = status;
  if (close) res.setHeader('Connection', 'close');
  if (status === 429 || status === 503) res.setHeader('Retry-After', '60');
  if (status === 204) { res.end(); return; }
  const bytes = Buffer.from(JSON.stringify(value));
  res.setHeader('Content-Type', 'application/json; charset=utf-8'); res.setHeader('Content-Length', bytes.length); res.end(bytes);
}
function headers(res) {
  res.setHeader('Cache-Control', 'no-store'); res.setHeader('Pragma', 'no-cache');
  res.setHeader('X-Content-Type-Options', 'nosniff'); res.setHeader('Referrer-Policy', 'no-referrer');
  res.setHeader('Content-Security-Policy', "default-src 'none'; frame-ancestors 'none'");
  res.setHeader('Cross-Origin-Resource-Policy', 'same-origin');
  res.setHeader('X-Frame-Options', 'DENY');
}
async function dispatch(service, route, req, body, context) {
  switch (route) {
    case 'GET /health': return {ok: true, service: 'mouse-identity', schema: 1};
    case 'GET /v1/accounts/info': return service.info();
    case 'POST /v1/accounts/challenge': return service.challenge(body, context);
    case 'POST /v1/accounts/register': return service.register(body, context);
    case 'POST /v1/accounts/claim-owner': return service.register(body, context, {owner: true});
    case 'POST /v1/accounts/login': return service.login(body, context);
    case 'POST /v1/accounts/recover': return service.recover(body, context);
    case 'POST /v1/accounts/refresh': return service.refresh(body, context);
    default: break;
  }
  const authorization = oneHeader(req, 'authorization');
  if (typeof authorization !== 'string' || !/^Bearer [A-Za-z0-9_-]{43}$/.test(authorization)) fail('AUTH_REQUIRED', 401);
  const auth = service.authenticate(authorization.slice(7), context);
  switch (route) {
    case 'GET /v1/accounts/me': return service.me(auth);
    case 'PUT /v1/accounts/profile': return service.updateProfile(auth, body);
    case 'GET /v1/accounts/devices': return service.devices(auth);
    case 'POST /v1/accounts/logout': if (Object.keys(body).length) fail('INVALID_REQUEST'); return service.logout(auth);
    case 'POST /v1/accounts/password': return service.changePassword(auth, body, context);
    case 'POST /v1/accounts/recovery-code': return service.rotateRecoveryCode(auth, body, context);
    case 'GET /v1/accounts/sync': return service.syncGet(auth);
    case 'GET /v1/accounts/sync/revision': return service.syncRevision(auth);
    case 'PUT /v1/accounts/sync': return service.syncPut(auth, body);
    case 'PUT /v1/accounts/flash/presence': return service.flashPresence(auth, body);
    case 'POST /v1/accounts/flash/invitations': return service.flashSend(auth, body);
    case 'GET /v1/accounts/flash/invitations': return service.flashInbox(auth);
    default: {
      let match;
      if ((match = /^DELETE \/v1\/accounts\/devices\/([a-f0-9]{32})$/.exec(route))) return service.revokeDevice(auth, match[1]);
      if ((match = /^GET \/v1\/accounts\/flash\/devices\/([1-9]\d{0,14})$/.exec(route))) return service.flashDevices(auth, Number(match[1]));
      fail('NOT_FOUND', 404);
    }
  }
}
function createIdentityServer({service, tls, trustLoopbackProxy = false, allowInsecureLoopback = false,
  allowedOrigins = [], allowedHosts = ['mouse.black', 'localhost', '127.0.0.1', '[::1]']} = {}) {
  if (!service) throw new TypeError('A Mouse identity service is required.');
  const origins = new Set(allowedOrigins), hosts = new Set(allowedHosts), memory = {bytes: 0};
  const limits = new RateLimiter({maxKeys: 4096}); let active = 0;
  const listener = async (req, res) => {
    headers(res);
    if (active >= MAX_ACTIVE) { response(res, 503, {error: 'SERVICE_BUSY'}, {close: true}); return; }
    active++;
    let released = false;
    const release = () => { if (!released) { released = true; active--; } };
    // A slow reader still occupies an admission slot while its response is
    // buffered. Counting only handler work would allow pipelined large sync
    // responses to escape the process-wide memory bound.
    res.once('finish', release); res.once('close', release);
    try {
      const host = oneHeader(req, 'host');
      if (typeof host !== 'string' || !hosts.has(host.replace(/:\d{1,5}$/, ''))) fail('HOST_INVALID', 400);
      if (typeof req.url !== 'string' || req.url.length > 256 || !/^(?:\/health|\/v1\/accounts\/[A-Za-z0-9/-]+)$/.test(req.url)) fail('NOT_FOUND', 404);
      const context = clientContext(req, {trustLoopbackProxy, allowInsecureLoopback});
      limits.take('http-global', '*', 3000, 60000); limits.take('http-ip', context.ip, 600, 60000);
      if (context.secure) res.setHeader('Strict-Transport-Security', 'max-age=31536000');
      const origin = oneHeader(req, 'origin');
      if (origin !== undefined) {
        if (!origins.has(origin)) fail('ORIGIN_DENIED', 403);
        res.setHeader('Access-Control-Allow-Origin', origin); res.setHeader('Vary', 'Origin');
      }
      if (req.method === 'OPTIONS') {
        if (!origin || !['GET', 'POST', 'PUT', 'DELETE'].includes(req.headers['access-control-request-method'])) fail('INVALID_REQUEST');
        const requested = (req.headers['access-control-request-headers'] || '').split(',').map(value => value.trim().toLowerCase()).filter(Boolean);
        if (requested.some(value => !['content-type', 'authorization'].includes(value))) fail('ORIGIN_DENIED', 403);
        res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
        response(res, 204); return;
      }
      if (!['GET', 'POST', 'PUT', 'DELETE'].includes(req.method)) fail('METHOD_NOT_ALLOWED', 405);
      const route = req.method + ' ' + req.url;
      let body;
      if (['POST', 'PUT'].includes(req.method)) body = await readJSON(req, bodyLimit(route), memory);
      else if (req.headers['transfer-encoding'] !== undefined || Number(req.headers['content-length'] || 0) > 0) fail('INVALID_REQUEST');
      const result = await dispatch(service, route, req, body, context);
      response(res, 200, result);
    } catch (failure) {
      const error = cleanError(failure);
      let status = error instanceof IdentityError ? error.status : 503;
      let code = error instanceof IdentityError ? error.code : 'SERVICE_UNAVAILABLE';
      if (failure?.code === 'ERR_SQLITE_ERROR' && /full/i.test(failure.message)) { status = 503; code = 'ACCOUNT_CAPACITY'; }
      response(res, status, {error: code, ...(error.conflict ? error.conflict : {})}, {close: status >= 400});
    }
  };
  const server = tls ? https.createServer({minVersion: 'TLSv1.2', ...tls, maxHeaderSize: 8192}, listener)
    : http.createServer({maxHeaderSize: 8192}, listener);
  server.requestTimeout = 15000; server.headersTimeout = 10000; server.keepAliveTimeout = 5000;
  server.timeout = 20000; server.maxHeadersCount = 32; server.maxRequestsPerSocket = 100; server.maxConnections = 128;
  server.on('clientError', (_error, socket) => { if (socket.writable) socket.end('HTTP/1.1 400 Bad Request\r\nConnection: close\r\nContent-Length: 0\r\n\r\n'); });
  return server;
}

module.exports = {createIdentityServer, clientContext, readJSON, DEFAULT_BODY_LIMIT, SYNC_BODY_LIMIT, GLOBAL_BODY_LIMIT};
