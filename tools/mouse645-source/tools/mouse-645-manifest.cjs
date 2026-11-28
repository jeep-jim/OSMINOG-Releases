'use strict';
// Bind the independently verified installed-app proof and every byte it read.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const CHECKS=Object.freeze(['native-account-sidebar-and-lightweight-sync-disclosure','native-flash-sidebar-and-overlay-barrier','conditional-update-entry','native-appearance-distinct-process-roundtrip']);
const sha=raw=>crypto.createHash('sha256').update(raw).digest('hex');
function bind(directory,platform,arch){
 const file='mouse-645-acceptance.json',raw=fs.readFileSync(path.join(directory,file)),accepted=JSON.parse(raw);
 assert.equal(platform,'darwin');assert.equal(arch,'arm64');assert.equal(accepted.schema,1);assert.equal(accepted.version,'6.0.45');assert.equal(accepted.platform,platform);assert.equal(accepted.arch,arch);assert.equal(accepted.status,'PASS');assert.equal(accepted.physicalUserDeviceVerified,false);assert.deepEqual(accepted.checks,CHECKS);
 assert.ok(Array.isArray(accepted.artifacts)&&accepted.artifacts.length>=5,'Verified645 evidence inventory is missing');const seen=new Set();
 for(const item of accepted.artifacts){assert.match(item.file,/^mouse-645-[a-z0-9.-]+$/);assert.ok(!item.file.includes('..'));assert.notEqual(item.file,file);assert.ok(!seen.has(item.file));seen.add(item.file);const bytes=fs.readFileSync(path.join(directory,item.file));assert.equal(item.sha256,sha(bytes));assert.equal(item.bytes,bytes.length);}
 const report='mouse-645-ui.json',processes='mouse-645-processes.json';
 for(const name of [report,processes,'mouse-645-ui-write.json','mouse-645-write.log','mouse-645-read.log'])assert.ok(seen.has(name),'Required645 evidence is absent: '+name);
 const facts=JSON.parse(fs.readFileSync(path.join(directory,report)));
 assert.equal(facts.version,'6.0.45');assert.equal(facts.ok,true);assert.equal(facts.phase,'read');assert.equal(facts.packaged,true);assert.equal(facts.physicalUserDeviceVerified,false);
 assert.ok(Array.isArray(accepted.captures)&&accepted.captures.length===6);assert.ok(Array.isArray(facts.captures));assert.deepEqual(facts.captures.map(row=>row.filename).sort(),[...accepted.captures].sort());
 for(const capture of facts.captures){for(const name of [capture.filename,capture.displayFilename,capture.shell?.filename])assert.ok(seen.has(name),'Required645 screenshot is absent: '+name);if(capture.filename.includes('-flash-'))assert.ok(seen.has(capture.flash?.filename),'Native Flash reference is absent');}
 return{file,sha256:sha(raw),report:{file:report,sha256:sha(fs.readFileSync(path.join(directory,report)))},processes:{file:processes,sha256:sha(fs.readFileSync(path.join(directory,processes)))}};
}
module.exports={bind,CHECKS};
