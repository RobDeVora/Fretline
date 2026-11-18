import json
from playwright.sync_api import sync_playwright
SHEETS={'valley':"""[G]Down in the [C]valley, the [G]valley so [D]low
[G]Hang your head [C]over, hear the [D]wind [G]blow""",
'grace-over':"""G              C          G
Amazing grace, how sweet the sound
G                   D
That saved a wretch like me
G             C          G
I once was lost but now am found
G         D        G
Was blind but now I see"""}
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8768/index.html');pg.wait_for_timeout(600)
  for k,s in SHEETS.items():
    r=pg.evaluate("""(src)=>{openSong({id:'m-'+src.length,cat:'mine',title:'T',bpm:90,bpb:4,kind:'chords',cb:4,src,capo:0,strum:''});const v=G.vox||[];
      const segs=chordSegments(G.song);const ch=t=>{let c=null;for(const g of segs)if(g.t<=t+1e-6)c=g;return c&&chordPcsOf(c.name,0).pcs;};
      return {n:v.length,range:[midiToName(Math.min(...v.map(x=>x.midi))),midiToName(Math.max(...v.map(x=>x.midi)))],distinct:new Set(v.map(x=>x.midi)).size,
        maxRepeat:v.reduce((a,x,i)=>{let r=1;while(i-r>=0&&v[i-r].midi===x.midi)r++;return Math.max(a,r);},0),maxLeap:Math.max(...v.slice(1).map((x,i)=>Math.abs(x.midi-v[i].midi))),
        downbeatChordTone:v.filter(x=>x.t%4===0).filter(x=>ch(x.t).includes(x.midi%12)).length+'/'+v.filter(x=>x.t%4===0).length,
        tune:v.map(x=>midiToName(x.midi)).join(' ')};}""",s)
    print(k,json.dumps(r))
  print(errs);b.close()
