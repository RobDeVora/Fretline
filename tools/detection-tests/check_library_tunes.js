const fs=require('fs');const h=fs.readFileSync(process.argv[2],'utf8');
const core=h.match(/<script id="core">([\s\S]*?)<\/script>/)[1];
const f=new Function(core+';return {parseTune,nameToMidi,splitChord:typeof splitChord!=="undefined"?splitChord:null};')();
const lib=JSON.parse(fs.readFileSync(process.argv[3])).songs;const T=JSON.parse(fs.readFileSync('tunes.json'));
const PC={C:0,D:2,E:4,F:5,G:7,A:9,B:11};const tones=n=>{const m=/^([A-G])([#b]?)(m?)(7?)/.exec(n);let r=PC[m[1]]+(m[2]==='#'?1:m[2]==='b'?-1:0);const s=[r,(r+(m[3]?3:4))%12,(r+7)%12];if(m[4])s.push((r+10)%12);return s.map(x=>(x+12)%12);};
for(const [id,tu] of Object.entries(T)){const L=lib.find(x=>x.id===id);const bpb=L.bpb,cb=L.cb;const chords=L.src.split(/\s+/);
  // bar sums
  const bars=tu.notes.split('|').map(b=>b.trim().split(/\s+/).filter(x=>x&&x!=='//').reduce((a,t)=>a+parseFloat(t.split('/')[1]),0));
  const bad=bars.map((s,i)=>[i,s]).filter(([i,s])=>i>0&&Math.abs(s-bpb)>1e-6);
  const r=f.parseTune(tu.notes,tu.pickup);const end=Math.max(...r.vocal.map(n=>n.t+n.d));
  let ok=0,n=0;const miss=[];for(const v of r.vocal){if(v.t<0||(v.t%bpb)!==0)continue;const c=chords[Math.floor(v.t/cb)];if(!c)continue;n++;if(tones(c).includes(v.midi%12))ok++;else miss.push('bar'+(v.t/bpb+1)+':'+c+'/'+v.midi%12);}
  console.log(id,'| bars',bars.length-1,'want',chords.length*cb/bpb,'| pickup',bars[0],'| bad bars',JSON.stringify(bad),'| tune ends',end,'chords end',chords.length*cb,'| downbeat chord tones',ok+'/'+n,miss.join(' '));
  console.log('  lyrics:',r.lyrics.map(l=>l.segs.map(s=>s.text).join('')).join(' / '));}
