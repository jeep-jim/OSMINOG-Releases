'use strict';
// Runs against the unpacked release package in an isolated Chrome profile.
// GitHub responses and tokens are fixtures; no owner credentials are used.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {createHmac} = require('node:crypto');
const {chromium} = require('playwright');
const root = path.resolve(process.argv[2] || 'work/package');
function otp(secret, time = Date.now()) {
  let bits = '';
  for (const c of secret) bits += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'.indexOf(c).toString(2).padStart(5, '0');
  const key = Buffer.from((bits.match(/.{8}/g) || []).map(x => parseInt(x, 2)));
  const counter = Buffer.alloc(8);
  counter.writeBigUInt64BE(BigInt(Math.floor(time / 30000)));
  const mac = createHmac('sha1', key).update(counter).digest();
  return String((mac.readUInt32BE(mac[19] & 15) & 0x7fffffff) % 1000000).padStart(6, '0');
}
(async () => {
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'osminog-owner-auth-'));
  // Temporary test harness only; it is deleted before packaging.
  const harness = path.join(root, 'owner-auth-ci.html');
  fs.writeFileSync(harness, '<!doctype html><html><body><script src="osminog-owner-guard.js"></script></body></html>');
  let context;
  try {
    context = await chromium.launchPersistentContext(profile, {
      headless: false,
      args: ['--no-sandbox', `--disable-extensions-except=${root}`, `--load-extension=${root}`]
    });
    const worker = context.serviceWorkers()[0] || await context.waitForEvent('serviceworker');
    const id = new URL(worker.url()).host;
    const page = await context.newPage();
    async function open(p) {
      await p.goto(`chrome-extension://${id}/owner-auth-ci.html`);
      await p.evaluate(() => {
        globalThis.__ownerReject = false;
        chrome.runtime.sendMessage = async message => {
          if (message?.type !== 'BC_MODULE_TEST') throw new Error('Unexpected test message');
          return {ok: true, name: 'owner-ci-fixture', owner: {ok: !globalThis.__ownerReject}};
        };
        globalThis.__ownerResult = 'pending';
      });
    }
    async function start(p) {
      await p.evaluate(() => {
        globalThis.__ownerResult = 'pending';
        OSMINOGOwnerGuard.require('CI owner auth').then(value => globalThis.__ownerResult = value);
      });
      await p.waitForFunction(() => {
        const m = document.querySelector('#osminogOwnerGate');
        return m && !m.hidden && !m.querySelector('[data-owner-submit]').disabled;
      });
    }
    async function input(p, code) {
      await p.locator('[data-owner-code]').fill(code);
      await p.locator('[data-owner-submit]').click();
    }
    await open(page);
    await page.evaluate(async () => {
      await chrome.storage.local.remove(['osminogOwnerAuthV1', 'osminogOwnerEnrollmentV1', 'osminogOwnerGrantV1']);
      await chrome.storage.local.set({briefCraftModulesV1: {github: {token: 'fixture-only'}}});
    });
    await start(page);
    const secret = await page.locator('[data-owner-secret]').textContent();
    assert.match(secret, /^[A-Z2-7]{32}$/);
    await page.locator('[data-owner-cancel]').click();
    await page.waitForFunction(() => __ownerResult === false);
    await start(page);
    assert.equal(await page.locator('[data-owner-secret]').textContent(), secret);
    // A complete page reload uses the same previously displayed key.
    await open(page);
    await start(page);
    assert.equal(await page.locator('[data-owner-secret]').textContent(), secret);
    // Two callers receive one promise; neither can silently replace the key.
    assert.equal(await page.evaluate(() => OSMINOGOwnerGuard.require('a') === OSMINOGOwnerGuard.require('b')), true);
    const second = await context.newPage();
    await open(second);
    await start(second);
    assert.equal(await second.locator('[data-owner-secret]').textContent(), secret);
    // Guaranteed stale fixture code is outside the preserved +/-30 s window.
    await input(page, otp(secret, Date.now() - 600000));
    await page.waitForFunction(() => document.querySelector('[data-owner-error]').textContent.includes('Неверный код'));
    assert.equal(await page.evaluate(() => OSMINOGOwnerGuard.isUnlocked()), false);
    assert.equal(await page.evaluate(async () => !!(await chrome.storage.local.get('osminogOwnerAuthV1')).osminogOwnerAuthV1), false);
    // A valid OTP must not enroll when GitHub rejects the owner.
    await page.evaluate(() => globalThis.__ownerReject = true);
    await input(page, otp(secret));
    await page.waitForFunction(() => document.querySelector('[data-owner-error]').textContent.includes('write-доступ'));
    assert.equal(await page.evaluate(() => OSMINOGOwnerGuard.isUnlocked()), false);
    assert.equal(await page.evaluate(async () => !!(await chrome.storage.local.get('osminogOwnerAuthV1')).osminogOwnerAuthV1), false);
    await page.evaluate(() => globalThis.__ownerReject = false);
    // Real DOM paste handler strips the Authenticator grouping space before maxlength.
    const currentCode = otp(secret);
    await page.evaluate(code => {
      const data = new DataTransfer();
      data.setData('text', code.slice(0, 3) + '\u00a0' + code.slice(3));
      document.querySelector('[data-owner-code]').dispatchEvent(new ClipboardEvent('paste', {clipboardData: data, bubbles: true, cancelable: true}));
    }, currentCode);
    assert.equal(await page.locator('[data-owner-code]').inputValue(), currentCode);
    await page.locator('[data-owner-submit]').click();
    await page.waitForFunction(() => __ownerResult === true);
    assert.equal(await page.evaluate(() => OSMINOGOwnerGuard.isUnlocked()), true);
    // The other open tab still accepts the same key, now committed by the first tab.
    await input(second, otp(secret));
    await second.waitForFunction(() => __ownerResult === true);
    await open(page);
    await start(page);
    assert.equal(await page.locator('[data-owner-setup-step]').evaluate(el => el.hidden), true);
    await input(page, otp(secret));
    await page.waitForFunction(() => __ownerResult === true);
    assert.equal(await page.evaluate(async () => (await chrome.storage.local.get('osminogOwnerAuthV1')).osminogOwnerAuthV1.totpSecret), secret);
    console.log('OWNER_AUTH_REAL_CHROME_PASS: stable key, reload, shared requests/tabs, invalid code, GitHub rejection, grouped paste, enrollment and subsequent login');
  } finally {
    if (context) await context.close();
    fs.rmSync(harness, {force: true});
    fs.rmSync(profile, {recursive: true, force: true});
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
