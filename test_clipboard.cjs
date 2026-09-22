const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('dist/app.js','utf8');let added=[],notice='',prevented=0;const state={busy:false,chatFiles:[]};
const ctx=vm.createContext({s:state,say:t=>notice=t,run:fn=>fn(),addChatFiles:f=>added.push(f),File:class{constructor(parts,name,options){this.parts=parts;this.name=name;this.type=options.type}}});
vm.runInContext(source.slice(source.indexOf('function pasteChatImage('),source.indexOf('async function addChatFiles(')),ctx);
const paste=(files,items=[])=>ctx.pasteChatImage({clipboardData:{files,items},preventDefault(){prevented++}});
paste([]);assert.equal(prevented,0);paste([{type:'image/png'}]);assert.equal(prevented,1);assert.equal(added[0][0].name,'Pasted image 1.png');
paste([],[{kind:'file',getAsFile:()=>({type:'image/jpeg'})}]);assert.equal(added[1][0].type,'image/jpeg');
state.busy=true;paste([{type:'image/png'}]);assert.equal(added.length,2);assert(notice.includes('busy'));state.busy=false;
paste([{type:'image/gif'}]);assert.equal(added.length,2);assert(notice.includes('PNG'));
paste([{type:'application/pdf'}]);assert.equal(prevented,4);
assert(!source.includes('message-edit-tools'));assert(source.includes('onpaste=pasteChatImage'));
assert(source.includes('selected.length+s.chatFiles.length>3'));assert(source.includes('12*1024*1024'));
console.log('Image paste, clipboard item fallback, text defaults, unsupported formats and busy guards passed.');

const {JSDOM}=require('./.ui-deps/node_modules/jsdom');
const dom=new JSDOM('<textarea id="request"></textarea>',{url:'http://localhost',runScripts:'outside-only'}),w=dom.window;
let previews=0;w.s={chatFiles:[]};w.$=id=>w.document.getElementById(id);w.render=()=>{};w.api=async(path,body)=>{assert.equal(path,'/api/attachment-preview');assert(body.data);previews++;return {images:[{mime:'image/jpeg',data:'fixture'}]}};
w.eval(source.slice(source.indexOf('async function addChatFiles('),source.indexOf('function chatKeydown(')));
(async()=>{await w.addChatFiles([new w.File(['image data'],'Pasted image 1.png',{type:'image/png'})]);assert.equal(w.s.chatFiles.length,1);assert.equal(previews,1);assert.equal(w.s.chatFiles[0].preview.images.length,1);await assert.rejects(()=>w.addChatFiles(Array(3).fill({size:1})),/three files/);await assert.rejects(()=>w.addChatFiles([{size:13*1024*1024}]),/12 MB/);dom.window.close();console.log('Pasted file runs through encoding, preview and attachment limits.');})().catch(e=>{console.error(e);process.exitCode=1});
