'use strict';

// Mouse owns one preference for address-bar and start-page searches. Private
// workspaces receive its value at entry and keep any later choice in RAM only.
const DEFAULT='google';
const ENGINES=Object.freeze([
 Object.freeze({id:'google',name:'Google',home:'https://www.google.com/',search:'https://www.google.com/search?q='}),
 Object.freeze({id:'bing',name:'Bing',home:'https://www.bing.com/',search:'https://www.bing.com/search?q='}),
 Object.freeze({id:'duckduckgo',name:'DuckDuckGo',home:'https://duckduckgo.com/',search:'https://duckduckgo.com/?q='}),
 Object.freeze({id:'yandex',name:'Яндекс',home:'https://yandex.ru/',search:'https://yandex.ru/search/?text='})
]);
const known=id=>typeof id==='string'&&ENGINES.some(engine=>engine.id===id);
function engineFor(id){if(!known(id))throw Error('Неизвестный поисковик');return ENGINES.find(engine=>engine.id===id);}
function searchURL(query,id=DEFAULT){return new URL(engineFor(id).search+encodeURIComponent(query)).href;}
function resolve(value,id=DEFAULT){
 const engine=engineFor(id),input=String(value??'').trim();
 if(input.length>8192)throw Error('Адрес или запрос слишком длинный');
 if(!input)return engine.home;
 // Keep the shared browser's address rules; search changes only plain queries.
 const candidate=/^[a-z][a-z\d+.-]*:/i.test(input)?input:/^[^\s/]+\.[^\s]+/.test(input)?'https://'+input:searchURL(input,id);
 const url=new URL(candidate);
 if(!['http:','https:'].includes(url.protocol)||url.username||url.password)throw Error('Можно открыть только адрес HTTP или HTTPS без пароля');
 return url.href;
}
function isSearchURL(query,value){
 if(typeof query!=='string'||!query||query.length>8192||typeof value!=='string')return false;
 try{return ENGINES.some(engine=>value===searchURL(query,engine.id));}catch{return false;}
}
async function create({store,privateMode=false,inheritedEngine}={}){
 let engine=DEFAULT,queue=Promise.resolve();
 if(privateMode){if(known(inheritedEngine))engine=inheritedEngine;}
 else{
  const saved=await store.get(['mouseSearch','quadroStartPage','quadroPreferences']);
  // Retain a valid explicit choice if one was stored by a previous shell.
  engine=[saved.mouseSearch?.engine,saved.quadroStartPage?.searchEngine,saved.quadroPreferences?.searchEngine].find(known)||DEFAULT;
  if(!known(saved.mouseSearch?.engine)&&[saved.quadroStartPage?.searchEngine,saved.quadroPreferences?.searchEngine].some(known))await store.set({mouseSearch:{engine}});
 }
 const state=()=>({engine,name:engineFor(engine).name,engines:ENGINES.map(({id,name})=>({id,name})),private:privateMode});
 function set(id){
  engineFor(id);
  queue=queue.catch(()=>{}).then(async()=>{if(id!==engine){if(!privateMode)await store.set({mouseSearch:{engine:id}});engine=id;}return state();});
  return queue;
 }
 return{state,resolve:value=>resolve(value,engine),set,flush:()=>queue};
}
module.exports={DEFAULT,ENGINES,known,resolve,isSearchURL,create};
