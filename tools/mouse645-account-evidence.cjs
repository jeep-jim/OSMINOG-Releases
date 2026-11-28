#!/usr/bin/env node
'use strict';
// Independently recompute every account fact using the reviewed source graph.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const verifier = require('./mouse645-source/tools/mouse-645-account-verify.cjs');
const manifest = require('./mouse645-source/tools/mouse-645-account-manifest.cjs');
const sha = raw => createHash('sha256').update(raw).digest('hex');
function verify(directory) {
  const inventory = new Map(); let total = 0;
  function read(name) {
    assert.match(name, /^mouse-645-account-[a-z0-9.-]+$/); assert.ok(!name.includes('..'));
    assert.notEqual(name, 'mouse-645-account-acceptance.json');
    const file = path.join(directory, name), stat = fs.lstatSync(file);
    assert.ok(stat.isFile() && !stat.isSymbolicLink() && stat.size > 0 && stat.size <= 32 * 1024**2);
    const raw = fs.readFileSync(file), item = {file: name, bytes: raw.length, sha256: sha(raw)};
    if (inventory.has(name)) assert.deepEqual(inventory.get(name), item);
    else { total += raw.length; assert.ok(total <= 256 * 1024**2); inventory.set(name, item); }
    return raw;
  }
  const accepted = verifier.verify(read);
  accepted.artifacts = [...inventory.values()].sort((a, b) => a.file.localeCompare(b.file));
  const file = path.join(directory, 'mouse-645-account-acceptance.json'), stat = fs.lstatSync(file);
  assert.ok(stat.isFile() && !stat.isSymbolicLink() && stat.size <= 1024**2);
  assert.deepEqual(JSON.parse(fs.readFileSync(file, 'utf8')), accepted,
    'Account receipt differs from independently verified raw evidence');
  return {accepted, binding: manifest.bind(directory, 'darwin', 'arm64')};
}
module.exports = {verify};
if (require.main === module) {
  try {
    assert.equal(process.argv.length, 3);
    process.stdout.write(JSON.stringify(verify(path.resolve(process.argv[2]))) + '\n');
  } catch (error) { process.stderr.write('Mouse645 independent account rejection: ' + error.message + '\n'); process.exitCode = 1; }
}
