'use strict';
// Independent archive reader for release evidence, using Chromium's CRX3
// signed-data wire format. It imports no installed-app extension code.
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const GOOGLE='61f7f2a6bfcf74cd0bc1fe2497cc9b04254c658f79f2145392867ea8366367cf';
const digest=data=>crypto.createHash('sha256').update(data).digest('hex');
const asId=hex=>[...hex].map(c=>String.fromCharCode(97+parseInt(c,16))).join('');
function protobuf(data){
 let offset=0,seen=0;const fields=[];
 function integer(){let value=0;for(let shift=0;shift<56;shift+=7){assert.ok(offset<data.length,'Truncated protobuf integer');const byte=data[offset++];value+=(byte&127)*2**shift;assert.ok(Number.isSafeInteger(value));if(!(byte&128))return value;}throw Error('Oversized protobuf integer');}
 while(offset<data.length){assert.ok(++seen<=128);const tag=integer(),number=Math.floor(tag/8),type=tag&7;assert.ok(number>0);if(type===0){integer();continue;}if(type===1||type===5){offset+=type===1?8:4;assert.ok(offset<=data.length);continue;}assert.equal(type,2);const length=integer();assert.ok(length<=data.length-offset);fields.push([number,data.subarray(offset,offset+length)]);offset+=length;}
 return fields;
}
function only(fields,number){const values=fields.filter(f=>f[0]===number);assert.equal(values.length,1,'Required CRX3 field must occur exactly once');return values[0][1];}
function verify(bytes,id){
 assert.match(id,/^[a-p]{32}$/);assert.ok(Buffer.isBuffer(bytes)&&bytes.length>=34&&bytes.length<=64*1024*1024);assert.equal(bytes.toString('ascii',0,4),'Cr24');assert.equal(bytes.readUInt32LE(4),3);
 const size=bytes.readUInt32LE(8),offset=12+size;assert.ok(size>0&&size<=1024*1024&&offset<bytes.length);
 const header=protobuf(bytes.subarray(12,offset)),signed=only(header,10000),declared=only(protobuf(signed),1);assert.equal(declared.length,16);assert.equal(asId(declared.toString('hex')),id);
 const length=Buffer.alloc(4);length.writeUInt32LE(signed.length);const message=Buffer.concat([Buffer.from('CRX3 SignedData\0'),length,signed,bytes.subarray(offset)]),proofs=[];
 for(const [field,blob]of header){if(![2,3].includes(field))continue;assert.ok(proofs.length<16);const values=protobuf(blob),der=only(values,1),signature=only(values,2);assert.ok(der.length<=8192&&signature.length<=8192);
  const key=crypto.createPublicKey({key:der,format:'der',type:'spki'});assert.equal(key.asymmetricKeyType,field===2?'rsa':'ec');assert.equal(crypto.verify('sha256',message,key,signature),true,'Actual archived CRX3 signature is invalid');const sha=digest(der);proofs.push({keySha256:sha,algorithm:field===2?'RSA-PKCS1-SHA256':'ECDSA-SHA256',developer:asId(sha.slice(0,32))===id,publisher:sha===GOOGLE});}
 assert.ok(proofs.some(p=>p.developer),'Developer signature for the selected Store ID is missing');assert.ok(proofs.some(p=>p.publisher),'Chrome Web Store publisher signature is missing');
 return{format:'CRX3',id,sha256:digest(bytes),bytes:bytes.length,archiveOffset:offset,developerVerified:true,publisherVerified:true,proofs};
}
if(require.main===module){const chunks=[];let size=0;process.stdin.on('data',chunk=>{size+=chunk.length;if(size>64*1024*1024)throw Error('CRX evidence exceeds size limit');chunks.push(chunk);});process.stdin.on('end',()=>{assert.equal(process.argv[2],'--id');assert.equal(process.argv.length,4);console.log(JSON.stringify(verify(Buffer.concat(chunks),process.argv[3])));});}
module.exports={verify};
