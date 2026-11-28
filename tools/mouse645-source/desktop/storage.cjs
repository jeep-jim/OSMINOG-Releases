'use strict';
const fs=require('node:fs/promises'),path=require('node:path');
class Store {
  constructor(dir){this.file=path.join(dir,'workspace.json');this.queue=Promise.resolve();this.cache=new Map();this.cacheBytes=0;this.signature='';}
  async read(){try{return JSON.parse(await fs.readFile(this.file,'utf8'))}catch(e){if(e.code==='ENOENT')return{};throw e}}
  async stamp(){try{const s=await fs.stat(this.file,{bigint:true});return `${s.ino}:${s.size}:${s.mtimeNs}:${s.ctimeNs}`}catch(e){if(e.code==='ENOENT')return 'missing';throw e}}
  clearCache(){this.cache.clear();this.cacheBytes=0;}
  remember(key,value){
    // Bound retained metadata; never retain a second copy of project images/code.
    const pending=[value];let bytes=key.length*2+32,visited=0;
    while(pending.length){const v=pending.pop();if(++visited>1000)return;if(typeof v==='string')bytes+=v.length*2;else if(v&&typeof v==='object'){for(const k of Object.keys(v)){bytes+=k.length*2+16;pending.push(v[k]);if(pending.length>1000)return}}else bytes+=16;if(bytes>65536)return}
    if(this.cache.has(key)){this.cacheBytes-=this.cache.get(key).bytes;this.cache.delete(key)}
    while(this.cacheBytes+bytes>1048576){const first=this.cache.keys().next().value;this.cacheBytes-=this.cache.get(first).bytes;this.cache.delete(first)}
    this.cache.set(key,{value:structuredClone(value),bytes});this.cacheBytes+=bytes;
  }
  async get(keys){
    await this.queue;if(keys==null)return this.read();
    const signature=await this.stamp();if(signature!==this.signature){this.clearCache();this.signature=signature}
    const names=typeof keys==='string'?[keys]:Array.isArray(keys)?keys:Object.keys(keys);
    let data;if(names.some(key=>!this.cache.has(key))){data=await this.read();for(const key of names)this.remember(key,data[key]);}
    const out={};for(const key of names){const value=data?data[key]:structuredClone(this.cache.get(key).value);Object.defineProperty(out,key,{value:value??(typeof keys==='object'&&!Array.isArray(keys)?keys[key]:undefined),enumerable:true,writable:true,configurable:true})}return out;
  }
  mutate(operation){const task=this.queue.then(async()=>{const data=await this.read();const result=operation(data);await fs.mkdir(path.dirname(this.file),{recursive:true});try{await fs.copyFile(this.file,this.file+'.bak')}catch(e){if(e.code!=='ENOENT')throw e}await fs.writeFile(this.file+'.next',JSON.stringify(data),'utf8');await fs.rename(this.file+'.next',this.file);this.clearCache();this.signature=await this.stamp();for(const [key,change] of Object.entries(result))this.remember(key,change.newValue);return result});this.queue=task.catch(()=>{});return task;}
  set(values){return this.mutate(data=>{const changes={};for(const [k,v] of Object.entries(values)){if(['__proto__','constructor','prototype'].includes(k))throw Error('Invalid storage key');changes[k]={oldValue:data[k],newValue:v};data[k]=v}return changes})}
  remove(keys){return this.mutate(data=>{const changes={};for(const k of typeof keys==='string'?[keys]:keys){changes[k]={oldValue:data[k]};delete data[k]}return changes})}
}
module.exports={Store};

