const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
let source=fs.readFileSync('dist/app.js','utf8');source=source.slice(0,source.lastIndexOf('document.documentElement.style.fontSize=preference()'));
const context=vm.createContext({document:{addEventListener:()=>{},querySelector:()=>({}),getElementById:()=>null},console});
vm.runInContext(source+`;globalThis.test={paged,pages,pageLists,s,files,documents,settings,history};`,context);
const t=context.test;
for(const n of [0,1,10,11,17,20,21,101]){
 const data=Array.from({length:n},(_,i)=>({id:i}));
 for(let page=1;page<=Math.max(1,Math.ceil(n/10));page++){
  t.pages.sample=page;const html=t.paged('sample',data,x=>'<article>'+x.id+'</article>');
  assert.equal((html.match(/<article>/g)||[]).length,Math.min(10,Math.max(0,n-(page-1)*10)));
  if(n>10){assert(html.includes('Page <strong>'+page+'</strong> of '+Math.ceil(n/10)));}
 }
 t.pages.sample=99;t.paged('sample',data,x=>'');assert.equal(t.pages.sample,Math.max(1,Math.ceil(n/10)));
}
const rows=Array.from({length:27},(_,i)=>({id:'row'+i,name:'Doc '+i,suffix:'.pdf',created:1,modified:1,label:'Work',path:'C:/Work/a.pdf',email:'a@example.com',detail:'Activity '+i,status:'draft'}));
t.s.files=rows;t.s.data={documents:rows,contacts:rows,folders:rows,drafts:rows,events:rows,accounts:{gmail:{},outlook:{}}};
for(const [view,keys] of [['files',['files']],['documents',['documents']],['settings',['folders','contacts']],['history',['drafts','events']]]){
 let html=t[view]();for(const key of keys){assert(html.includes('id="list-'+key+'"'));assert.equal(t.pageLists[key].items.length,27);t.pages[key]=3;}
 html=t[view]();for(const key of keys)assert(html.includes('21-27 of 27'));
}
console.log('Pagination boundaries, last-page clamping, and all collection views passed.');
