const {readdirSync}=require('node:fs');
const {spawnSync}=require('node:child_process');
const files=readdirSync('.').filter(f=>/^test_.*\.cjs$/.test(f)).sort();
if(!files.length)throw Error('No interface tests found');
for(const file of ['dist/app.js','dist/format.js']){
 const r=spawnSync(process.execPath,['--check',file],{stdio:'inherit'});
 if(r.error||r.status!==0)process.exit(1);
}
for(const file of files){
 console.log(`\nRunning ${file}`);
 const r=spawnSync(process.execPath,[file],{stdio:'inherit',timeout:60000});
 if(r.error||r.status!==0)process.exit(1);
}
console.log(`\nAll ${files.length} interface test files passed.`);
