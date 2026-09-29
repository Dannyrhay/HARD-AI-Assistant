const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('dist/app.js','utf8');
const code=source.slice(source.indexOf('function chatKeydown('),source.indexOf('function chatPanel('));
let submitted=0,prevented=0;const send={disabled:false},state={busy:false,data:{ai:{configured:true}}};
const ctx=vm.createContext({s:state});vm.runInContext(code,ctx);
const input={value:'Hello',form:{querySelector(){return send},requestSubmit(button){assert.equal(button,send);submitted++}}};
function press(props={}){ctx.chatKeydown({key:'Enter',currentTarget:input,preventDefault(){prevented++},...props})}
press();assert.equal(submitted,1);press({ctrlKey:true});assert.equal(submitted,2);
for(const props of [{shiftKey:true},{altKey:true},{isComposing:true},{keyCode:229},{key:'a'}])press(props);
assert.equal(submitted,2);assert.equal(prevented,2);
press({repeat:true});state.busy=true;press();state.busy=false;send.disabled=true;press();send.disabled=false;
input.value='  ';press();input.value='Hello';state.data.ai.configured=false;press();assert.equal(submitted,3);
assert(source.includes('onkeydown=chatKeydown'));assert(source.includes('aria-describedby="chat-shortcuts"'));
console.log('Enter/Ctrl+Enter submit; multiline, IME, repeats, busy, empty guards and local requests without AI passed.');
