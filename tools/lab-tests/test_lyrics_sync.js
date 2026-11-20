// Synthetic check of lyric alignment: builds a vocal loudness envelope from known syllable times (with held words, breaths, uneven delivery)
// and measures how far each aligned word start is from the truth. Usage: node test_lyrics_sync.js
const fs=require('fs');const h=fs.readFileSync(__dirname+'/../../lab/stems.html','utf8');
const a=h.indexOf('function sylCount'),b=h.indexOf('function lyrBeats');
const src=h.slice(a,b)+';return {alignLyrics,alignLyricsOld,lyrLines};';
const F=new Function(src)();
let seed=7;const rnd=()=>{seed=(seed*1664525+1013904223)%4294967296;return seed/4294967296;};
const words='the long road goes on and on beyond the hills where we were born singing softly through the night oh hold me closer tonight until morning'.split(' ');
function run(){
  const lines=[];let t=1.0;const truth=[];const env=new Float32Array(100*400);
  for(let l=0;l<30;l++){const n=3+Math.floor(rnd()*4);const ws=[];for(let k=0;k<n;k++)ws.push(words[Math.floor(rnd()*words.length)]);
    const lt=[];for(const w of ws){let sy=F.lyrLines(w)[0].syl[0];lt.push(t);if(process.env.HARD&&rnd()<0.1)sy=Math.max(1,sy+(rnd()<0.5?-1:1));
      for(let s=0;s<sy;s++){const held=rnd()<0.15?1.2:0;const merge=process.env.HARD&&rnd()<0.08;const d=0.18+rnd()*0.3+held;const i0=Math.round(t*100),i1=Math.round((t+d*0.9)*100);
        for(let i=i0;i<Math.min(i1,env.length);i++){const x=(i-i0)/(i1-i0);env[i]=merge?0.7+0.03*rnd():0.2+0.8*Math.min(1,x*8)*(1-0.3*x)+0.03*rnd();}if(process.env.HARD&&rnd()<0.1){const m=Math.round((t+d*0.45)*100);for(let i=m-3;i<m+3;i++)env[i]=Math.max(0.15,env[i]*0.35);}
        t+=d;}}
    lines.push(ws.join(' '));truth.push(lt);t+=0.3+(rnd()<0.5?0.6:0);}
  return {text:lines.join('\n'),env,truth};
}
function score(fn,d){const r=fn(d.text,d.env,120,0);if(!r)return null;const errs=[];r.sec.forEach((ln,i)=>ln.segs.forEach((w,k)=>errs.push(Math.abs(w.t-d.truth[i][k]))));
  errs.sort((x,y)=>x-y);return {med:errs[errs.length>>1],p90:errs[Math.floor(errs.length*0.9)],within250:errs.filter(e=>e<0.25).length/errs.length};}
let tot={n:{med:0,p90:0,w:0},o:{med:0,p90:0,w:0}};const R=5;
for(let r=0;r<R;r++){const d=run();const n=score(F.alignLyrics,d),o=score(F.alignLyricsOld,d);
  console.log('run',r,'new',JSON.stringify(n),'old',JSON.stringify(o));
  for(const [k,v] of [['n',n],['o',o]]){tot[k].med+=v.med/R;tot[k].p90+=v.p90/R;tot[k].w+=v.within250/R;}}
console.log('MEAN new',tot.n,'old',tot.o);
if(process.env.DBG){const d=run();const r=F.alignLyrics(d.text,d.env,120,0);for(let i=0;i<4;i++)console.log(d.truth[i].map(x=>x.toFixed(2)).join(' '),'|',r.sec[i].segs.map(w=>w.t.toFixed(2)).join(' '));console.log(r.phrases,r.onsets,r.n);}
if(process.env.DBG2){const G=new Function(h.slice(a,b)+';return {vocalOnsets,vocalPhrases};')();const d=run();const sg=G.vocalPhrases(d.env).segs;const on=G.vocalOnsets(d.env,sg);
console.log('segs',sg.slice(0,5).map(s=>s.map(x=>x.toFixed(2)).join('-')).join(' '));console.log('on',on.slice(0,16).map(o=>o.t.toFixed(2)+'/'+o.s.toFixed(1)).join(' '));console.log('truth',d.truth.slice(0,2).flat().map(x=>x.toFixed(2)).join(' '));}
if(process.env.DBG3){const G=new Function(h.slice(a,b)+';return {vocalOnsets,vocalPhrases};')();const d=run();const sg=G.vocalPhrases(d.env).segs;const on=G.vocalOnsets(d.env,sg);
console.log('line3 truth',d.truth[3].map(x=>x.toFixed(2)).join(' '),'text',d.text.split('\n')[3]);console.log('on',on.filter(o=>o.t>12&&o.t<18).map(o=>o.t.toFixed(2)).join(' '));}
if(process.env.DBG4){const G=new Function(h.slice(a,b)+';return {vocalOnsets,vocalPhrases,alignLyrics};')();const d=run();const r=G.alignLyrics(d.text,d.env,120,0);const sg=G.vocalPhrases(d.env).segs;const on=G.vocalOnsets(d.env,sg);
console.log('text',d.text.split('\n').slice(0,4).join(' / '));console.log('truth',d.truth.slice(0,4).flat().map(x=>x.toFixed(2)).join(' '));console.log('got  ',r.sec.slice(0,4).flatMap(l=>l.segs.map(w=>w.t.toFixed(2))).join(' '));console.log('on',on.filter(o=>o.t<14).map(o=>o.t.toFixed(2)).join(' '));}
if(process.env.DBG5){const G=new Function(h.slice(a,b)+';return {vocalOnsets,vocalPhrases,lyrLines};')();const d=run();const sg=G.vocalPhrases(d.env).segs;const on=G.vocalOnsets(d.env,sg);const L=G.lyrLines(d.text);let S=0;L.forEach(l=>l.syl.forEach(x=>S+=x));console.log('S',S,'onsets',on.length,'segs',sg.length,'lines',L.length);}
if(process.env.DBG6){let code=h.slice(a,b).replace("if(bi<0)return alignLyricsOld","globalThis.__D={dp,onsets,prior,cand,bi,bj,bc,syl};if(bi<0)return alignLyricsOld")+';return {alignLyrics};';const G=new Function(code)();const d=run();G.alignLyrics(d.text,d.env,120,0);const D=globalThis.__D;
console.log('end',D.bi,D.bj,D.bc.toFixed(1),'S',D.syl.length);for(const i of [12,13,14,15]){console.log(i,'prior',D.prior[i].toFixed(2),'cand',D.cand[i].map(j=>D.onsets[j].t.toFixed(2)).join(','),'dp',[...D.dp[i]].map(([j,s])=>D.onsets[j].t.toFixed(2)+':'+s.c.toFixed(1)).join(' '));}}
if(process.env.DBG7){let code=h.slice(a,b).replace("if(bi<0)return alignLyricsOld","globalThis.__D={dp,onsets,prior,cand,bi,bj,bc,syl};if(bi<0)return alignLyricsOld")+';return {alignLyrics};';const G=new Function(code)();const d=run();G.alignLyrics(d.text,d.env,120,0);const D=globalThis.__D;let ci=D.bi,cj=D.bj;const ch=[];while(ci>=0){ch.push([ci,D.onsets[cj].t.toFixed(2)]);const f=D.dp[ci].get(cj).from;if(!f)break;ci=f[0];cj=f[1];}
console.log(ch.reverse().slice(0,25).map(x=>x.join(':')).join(' '));}
if(process.env.DBG8){let code=h.slice(a,b).replace("if(bi<0)return alignLyricsOld","globalThis.__D={dp,onsets,prior,cand,bi,bj,bc,syl,segs};if(bi<0)return alignLyricsOld")+';return {alignLyrics,lyrLines};';const G=new Function(code)();const d=run();const r=G.alignLyrics(d.text,d.env,120,0);const D=globalThis.__D;
const got=r.sec.flatMap(l=>l.segs.map(w=>w.t)),tr=d.truth.flat();let k=0;while(k<got.length&&Math.abs(got[k]-tr[k])<0.25)k++;console.log('first bad word',k,'of',got.length);
console.log('truth',tr.slice(k-2,k+6).map(x=>x.toFixed(2)).join(' '));console.log('got  ',got.slice(k-2,k+6).map(x=>x.toFixed(2)).join(' '));console.log('onsets',D.onsets.filter(o=>o.t>tr[k-1]-0.1&&o.t<tr[k+5]).map(o=>o.t.toFixed(2)+'/'+o.pre.toFixed(2)).join(' '));console.log('S',D.syl.length,'on',D.onsets.length,'segs',D.segs.length);}
if(process.env.DBG9){let code=h.slice(a,b).replace("if(bi<0)return alignLyricsOld","globalThis.__D={dp,onsets,prior,cand,bi,bj,bc,syl,edge};if(bi<0)return alignLyricsOld")+';return {alignLyrics};';const G=new Function(code)();const d=run();G.alignLyrics(d.text,d.env,120,0);const D=globalThis.__D;
let c=0,pj=-1;for(let i=0;i<D.syl.length;i++){c+=D.edge(i,i,i-1,pj);pj=i;}console.log('identity',c.toFixed(2),'chosen',D.bc.toFixed(2),'identity in cand?',D.syl.every((_,i)=>D.cand[i].includes(i)));}
