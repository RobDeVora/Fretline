/* v1.121: align known lyrics to a recording with a speech model (NeMo Conformer-CTC small, English, int8).
   The model hears the recording and says, for every 40 ms, how likely each word-piece is; a forced alignment then finds the best
   path through those that spells out EXACTLY the lyric text, in order. Instrumental parts and unsung stretches fall on the "blank". */
const CTC={BLANK:1024};
CTC.loadTokens=function(txt){const t=[];for(const l of txt.split('\n')){const p=l.trim().split(/\s+/);if(p.length>=2&&/^\d+$/.test(p[p.length-1]))t[+p[p.length-1]]=p.slice(0,-1).join(' ');}
  const set=new Map();t.forEach((s,i)=>{if(s!=null&&i<1024)set.set(s,i);});CTC.vocab=set;CTC.maxLen=Math.max(...[...set.keys()].map(s=>s.length));return set;};
/* words -> word-piece ids (greedy longest match; every word starts with the "▁" marker) */
CTC.pieces=function(word){const w=word.toLowerCase().replace(/[’‘]/g,"'").replace(/[^a-z']/g,'');if(!w)return [];const out=[];let rest='▁'+w;
  while(rest.length){let done=false;for(let L=Math.min(CTC.maxLen,rest.length);L>=1;L--){const s=rest.slice(0,L);if(CTC.vocab.has(s)){out.push(CTC.vocab.get(s));rest=rest.slice(L);done=true;break;}}
    if(!done)rest=rest.slice(1);}return out;};
/* lp: Float32Array T*V of log-probabilities; ids: token ids. Returns the first frame of every token, or null. */
CTC.force=function(lp,T,V,ids){const L=ids.length;if(!L||T<L)return null;const S=2*L+1,NEG=-1e30;let prev=new Float32Array(S).fill(NEG),cur=new Float32Array(S);const bp=new Uint8Array(T*S);
  const lab=s=>(s&1)?ids[(s-1)>>1]:CTC.BLANK;prev[0]=lp[CTC.BLANK];if(S>1)prev[1]=lp[ids[0]];
  for(let t=1;t<T;t++){const row=t*V;for(let s=0;s<S;s++){let b=prev[s],k=0;if(s>=1&&prev[s-1]>b){b=prev[s-1];k=1;}
      if(s>=2&&(s&1)&&ids[(s-1)>>1]!==ids[(s-3)>>1]&&prev[s-2]>b){b=prev[s-2];k=2;}cur[s]=b+lp[row+lab(s)];bp[t*S+s]=k;}
    const tmp=prev;prev=cur;cur=tmp;}
  let s=S-1;if(S>1&&prev[S-2]>prev[S-1])s=S-2;const first=new Int32Array(L).fill(-1),last=new Int32Array(L).fill(-1);
  for(let t=T-1;t>=0;t--){if(s&1){const i=(s-1)>>1;if(last[i]<0)last[i]=t;first[i]=t;}s-=bp[t*S+s];if(s<0)s=0;}
  /* how well the model heard each token: best log-probability of that very piece anywhere in its frames */
  const conf=new Float32Array(L);for(let i=0;i<L;i++){let m=-1e9;for(let t=first[i];t>=0&&t<=last[i];t++){const v=lp[t*V+ids[i]];if(v>m)m=v;}conf[i]=m;}
  return {first,last,conf};};
/* lines = [{words:[..]}] (from lyrLines). Returns [[{t,d}...]] seconds per word, frame length 0.04 s. */
CTC.alignLines=function(lines,lp,T,V){const ids=[],own=[];lines.forEach((l,li)=>l.words.forEach((w,wi)=>{const p=CTC.pieces(w);own.push({li,wi,a:ids.length,n:p.length});for(const x of p)ids.push(x);}));
  const r=CTC.force(lp,T,V,ids);if(!r)return null;const FR=0.04;const out=lines.map(l=>l.words.map(()=>null));
  own.forEach(o=>{if(!o.n)return;let c=0;for(let k=0;k<o.n;k++)c+=r.conf[o.a+k];out[o.li][o.wi]={t:r.first[o.a]*FR,e:(r.last[o.a+o.n-1]+1)*FR,c:c/o.n};});return out;};
if(typeof module!=='undefined')module.exports=CTC;
