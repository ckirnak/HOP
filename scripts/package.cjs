// Explicit allowlist: exclude Git history and runtime data.
const fs = require('fs'), path = require('path'), crypto = require('crypto'), cp = require('child_process');
process.chdir(path.join(__dirname, '..'));
const version = fs.readFileSync('VERSION', 'utf8').trim();
if (!/^\d+\.\d+\.\d+$/.test(version)) throw Error('Invalid VERSION');
cp.execFileSync(process.execPath, ['backend/build-live.cjs']);
const files = ['README.md','LICENSE','VERSION','AGENTS.md','.gitignore','install.sh',
 ...['index.html','app.js','operator.css'].map(n=>'dist/'+n),
 ...['server.py','refresh_metadata.py','gateway.php','hop.service','hop-stream.conf','install.py','setup.py','update.py','test_update.py','test_server.py','test_setup.py','build-live.cjs','live.html','live.js','live-cards.css','operator.css','README.md','CHANGELOG.md'].map(n=>'backend/'+n),
 ...['ARCHITECTURE.md','INSTALL.md','RELEASING.md','VALIDATION.md'].map(n=>'docs/'+n),'scripts/package.cjs'];
const patterns = [
 /\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b/,
 /-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----/,
 /\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b/,
 /(?:password|secret)\s*=\s*['"][A-Za-z0-9+/_=-]{8,}['"]/i,
 /\b(?:90[235]\d{9}|0[235]\d{9})\b/,
 /appgprj_[a-z0-9]+/i
];
const findings = files.filter(file=>patterns.some(p=>p.test(fs.readFileSync(file,'utf8'))));
if(findings.length) throw Error('Review possible private data in: '+findings.join(', '));
if(!fs.readFileSync('backend/live.html','utf8').includes('HOP v'+version)) throw Error('Footer version mismatch');
const changelog=fs.readFileSync('backend/CHANGELOG.md','utf8');
const start=changelog.indexOf('## '+version+' — ');
if(start<0) throw Error('Missing dated changelog entry');
let end=changelog.indexOf('\n## ',start+1);
if(end<0) end=changelog.length;
const out=path.resolve('release','hop-'+version);
if(fs.existsSync(out)) throw Error('Output exists; retain or rename before rebuilding: '+out);
fs.mkdirSync(out,{recursive:true});
const sums=[];
for(const file of files){
 const dest=path.join(out,file);fs.mkdirSync(path.dirname(dest),{recursive:true});fs.copyFileSync(file,dest);
 sums.push(crypto.createHash('sha256').update(fs.readFileSync(dest)).digest('hex')+'  '+file);
}
fs.writeFileSync(path.join(out,'SHA256SUMS'),sums.join('\n')+'\n');
fs.writeFileSync(path.resolve('release','hop-'+version+'-notes.md'),changelog.slice(start,end).trim()+'\n');
console.log('Clean source package: '+out+'\nFiles: '+files.length+'\nNo Git history or runtime credentials included.');
