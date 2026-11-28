'use strict';
// Revalidate the independent installed account proof and bind every byte read.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {verify, CHECKS} = require('./mouse-645-account-verify.cjs');
const sha = value => createHash('sha256').update(value).digest('hex');
function bind(directory, platform, arch) {
  assert.equal(platform, 'darwin'); assert.equal(arch, 'arm64');
  const file = 'mouse-645-account-acceptance.json', raw = fs.readFileSync(path.join(directory, file)), accepted = JSON.parse(raw);
  assert.equal(accepted.schema, 1); assert.equal(accepted.version, '6.0.45'); assert.equal(accepted.status, 'PASS');
  assert.equal(accepted.platform, platform); assert.equal(accepted.arch, arch); assert.equal(accepted.fixtureOnly, true);
  assert.equal(accepted.physicalUserDeviceVerified, false); assert.equal(accepted.logicalDevices, 2);
  assert.equal(accepted.installedProcesses, 14); assert.deepEqual(accepted.checks, CHECKS);
  assert.ok(Array.isArray(accepted.artifacts)); const inventory = new Map(), consumed = new Set();
  for (const item of accepted.artifacts) {
    assert.match(item.file, /^mouse-645-account-[a-z0-9.-]+$/); assert.ok(!item.file.includes('..'));
    assert.notEqual(item.file, file); assert.ok(!inventory.has(item.file)); inventory.set(item.file, item);
  }
  function read(name) {
    const expected = inventory.get(name); assert.ok(expected, 'Unbound account proof: ' + name);
    const target = path.join(directory, name), stat = fs.lstatSync(target);
    assert.ok(stat.isFile() && !stat.isSymbolicLink());
    const bytes = fs.readFileSync(target); assert.equal(bytes.length, expected.bytes); assert.equal(sha(bytes), expected.sha256);
    consumed.add(name); return bytes;
  }
  const proven = verify(read);
  for (const key of ['schema', 'version', 'status', 'platform', 'arch', 'fixtureOnly', 'physicalUserDeviceVerified',
    'logicalDevices', 'installedProcesses', 'report', 'server', 'checks']) assert.deepEqual(accepted[key], proven[key]);
  assert.equal(consumed.size, inventory.size, 'Account evidence inventory includes unverified artifacts');
  return {file, sha256: sha(raw), report: {file: accepted.report, sha256: sha(read(accepted.report))},
    server: {file: accepted.server, sha256: sha(read(accepted.server))},
    logicalDevices: 2, installedProcesses: 14, physicalUserDeviceVerified: false};
}
module.exports = {bind, CHECKS};
