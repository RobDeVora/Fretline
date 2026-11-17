// Copies the web app into www/ (a bundled fallback copy; the app itself loads the live site).
const fs=require('fs'),path=require('path');const root=path.join(__dirname,'..');const www=path.join(__dirname,'www');
fs.rmSync(www,{recursive:true,force:true});fs.mkdirSync(www,{recursive:true});
for(const f of ['index.html','sw.js','manifest.webmanifest','icon-192.png','icon-512.png','icon-maskable-512.png','apple-touch-icon.png'])fs.copyFileSync(path.join(root,f),path.join(www,f));
