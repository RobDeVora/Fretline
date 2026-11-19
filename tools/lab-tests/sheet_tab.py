# v1.83: Lab with a pasted tab for the synthetic riff (riff100.wav). The tab's spacing is deliberately uneven, so
# the timing has to come from the recording. Checks every riff note lands on its beat, then retimes to half tempo.
import json,random
from playwright.sync_api import sync_playwright
riff=[(0,0),(0,0),(2,2),(0,0),(1,0),(1,0),(1,2),(2,0)]  # (string from low E, fret): E2 E2 E3 E2 A2 A2 B2 D3
random.seed(3);cols=[[] for _ in range(6)]
for bar in range(8):
  for s,f in riff:
    w=random.choice([1,2,3,4])
    for k in range(6):cols[k].append(('-'*w)+(str(f) if k==s else '-'*len(str(f))))
  for k in range(6):cols[k].append('|')
names='EADGBe'
tab='\n'.join(names[k]+'|'+''.join(cols[k]) for k in range(5,-1,-1))
truth={(m,b*4+i*0.5) for b in range(8) for i,m in enumerate([40,40,52,40,45,45,47,50])}
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');ctx=b.new_context(viewport={'width':412,'height':900},service_workers='block');pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/lab/stems.html?ortbase=http://localhost:8771/&modelurl=http://localhost:8771/dummy.onnx');pg.wait_for_timeout(1000)
  pg.set_input_files('#file',__import__('os').environ.get('RIFF','/tmp/stemtest/riff100_clean.wav'));pg.select_option('#secs','0');pg.select_option('#be','wasm');pg.fill('#ttl','Riff tab');pg.click('#sheetBox summary')
  if __import__('os').environ.get('MIDI'):pg.set_input_files('#sheetFile',__import__('os').environ['MIDI']);pg.wait_for_timeout(1500);print('file:',pg.text_content('#sheetFileName'),'· track',pg.eval_on_selector('#sheetPart','e=>e.options[e.selectedIndex].text'))
  else:pg.fill('#sheet',tab)
  pg.click('#go');pg.wait_for_function('window.__labDone',timeout=900000)
  print('\n'.join(l for l in pg.text_content('#log').split('\n') if l.startswith(('sheet','tempo','song','ERROR'))))
  d=pg.evaluate('window.__labSong');got={(n['midi'],e['t']) for e in d['events'] for n in e['notes']}
  # v1.85: steps keep their played time (1/48 beat), so match within 0.15 beat and report how far from the beat
  spb=60/d['bpm'];hit=0;dev=[]
  for (m,bt) in truth:
    c=[gb for (gm,gb) in got if gm==m and abs(gb-bt)<=0.15]
    if c:hit+=1;dev.append(min(abs(x-bt) for x in c)*spb*1000)
  print('bpm',d['bpm'],'steps',len(d['events']),'· riff notes on the right beat (±0.15):',hit,'/',len(truth),'· distance from the exact beat: median',int(sorted(dev)[len(dev)//2]) if dev else '-','ms, max',int(max(dev)) if dev else '-','ms')
  import numpy as np;T=np.array(d['recEvT']);i=np.arange(len(T));A=np.polyfit(i,T,1);res=(T-np.polyval(A,i))*1000
  P=np.array([d['recOffset']+e['t']*spb for e in d['events']]);res2=(P-np.polyval(A,i))*1000
  print('timing vs the evenly played riff: aligned median',int(np.median(abs(res))),'ms max',int(abs(res).max()),'ms · as placed on the highway: median',int(np.median(abs(res2))),'ms max',int(abs(res2).max()),'ms')
  pg.click('#tHalf');d2=pg.evaluate('window.__labSong')
  sec=lambda d:sorted(round(d['recOffset']+e['t']*60/d['bpm'],3) for e in d['events']);a,b2=sec(d),sec(d2);mx=max(abs(x-y) for x,y in zip(a,b2))
  print('half tempo',d2['bpm'],'· steps',len(d2['events']),'· largest move in the recording',int(mx*1000),'ms (grid',int(60/d2['bpm']/8*1000),'ms)')
  # main app: open it, Listen uses the real guitar, ♩ tempo halves it without moving notes
  pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(1500)
  print('app:',pg.evaluate("""async()=>{const d=mySongs.find(x=>x.title.startsWith('Riff tab'));openSong(d);document.querySelectorAll('.overlay.show').forEach(o=>o.classList.remove('show'));
    const out={events:G.song.events.length,first:G.song.events.slice(0,4).map(e=>e.t+':'+e.notes.map(n=>'s'+n.s+'f'+n.f).join('+'))};settings.backing=true;await $('#btnListen').onclick();await new Promise(r=>setTimeout(r,2500));
    out.realGuitar=!!RECB.gsrc;$('#btnListen').onclick();curCat='mine';renderList();
    const before=mySongs.find(x=>x.id===d.id);openTempoEd(d.id);$('#teDouble').click();$('#teSave').click();const a=mySongs.find(x=>x.id===d.id);
    const sec=x=>x.events.map(e=>x.recOffset+e.t*60/x.bpm);const A=sec(before),B=sec(a);let mx=0;for(let i=0;i<A.length;i++)mx=Math.max(mx,Math.abs(A[i]-B[i]));
    out.tempo=a.bpm;out.steps=a.events.length;out.maxMoveMs=Math.round(mx*1000);openSong(a);out.reopened=G.song.bpm+' bpm, '+G.song.events.length+' events';return JSON.stringify(out);}"""))
  print('errors',errs);b.close()
