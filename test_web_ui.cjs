const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const {JSDOM}=require('jsdom');
const source=fs.readFileSync('dist/app.js','utf8');
const s={data:{ai:{configured:true,provider:'openrouter',endpoint:'https://openrouter.ai/api/v1/chat/completions',model:'test',label:'OpenRouter'},profile:{name:'Test'}},chatMessages:[],chatFiles:[],chatInput:''};
const ctx=vm.createContext({s,e:x=>String(x??'').replaceAll('&','&amp;').replaceAll('"','&quot;').replaceAll('<','&lt;'),hardFormat:x=>x,isOpenRouter:ai=>ai.provider==='openrouter'});
vm.runInContext(source.slice(source.indexOf('function chatPanel(){'),source.indexOf('\n',source.indexOf('function chatPanel(){'))),ctx);
function page(){return new JSDOM(ctx.chatPanel()).window.document}
assert.equal(page().querySelector('#chat-web').getAttribute('aria-pressed'),'false');
s.webSearch=true;assert.equal(page().querySelector('#chat-web').getAttribute('aria-pressed'),'true');assert(page().querySelector('.web-notice').textContent.includes('Extra charges'));
s.chatMessages=[{role:'assistant',content:'Answer',web:{enabled:true,sources:[{url:'https://example.com',title:'Example'},{url:'javascript:alert(1)',title:'Bad'}]}}];
assert.equal(page().querySelectorAll('.web-sources a').length,1);assert.equal(page().querySelector('.web-sources a').rel,'noopener noreferrer');
s.chatMessages[0].web.sources=[];assert(page().querySelector('.web-sources').textContent.includes('No source links'));
s.data.ai.provider='gemini';assert.equal(page().querySelector('#chat-web'),null);
console.log('Web UI: opt-in, disclosure, safe source links, missing evidence and provider visibility passed.');
