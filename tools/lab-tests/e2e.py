import sys,json
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--autoplay-policy=no-user-gesture-required']);ctx=b.new_context(viewport={'width':412,'height':900});pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/lab/stems.html?ortbase=http://localhost:8771/&modelurl=http://localhost:8771/dummy.onnx');pg.wait_for_timeout(3500)
  pg.set_input_files('#file','/tmp/stemtest/riff100.wav');pg.select_option('#secs','0');pg.select_option('#be','wasm');pg.fill('#ttl','Riff test');pg.click('#go');pg.wait_for_function('window.__labDone',timeout=900000)
  t=pg.text_content('#log');print('\n'.join(l for l in t.split('\n') if l.startswith(('notes','tempo','song','ERROR'))))
  d=pg.evaluate('window.__labSong');print('bpm',d['bpm'],'offset',round(d['recOffset'],3))
  riff=[40,40,52,40,45,45,47,50];truth={(m,b*4+k*0.5) for b in range(8) for k,m in enumerate(riff)}
  got={(n['midi'],n['beat']) for n in d['recNotes']}
  ex=sorted([n for n in d['recNotes'] if (n['midi'],n['beat']) not in truth],key=lambda n:n['beat'])[:10];re_=sorted([n for n in d['recNotes'] if (n['midi'],n['beat']) in truth],key=lambda n:n['beat'])[:10]
  print('extras',[(n['midi'],n['ts'],n['v'],n['dur']) for n in ex]);print('real',[(n['midi'],n['ts'],n['v'],n['dur']) for n in re_])
  print('riff notes found at the right beat:',len(truth&got),'/',len(truth),'· extra notes:',len(got-truth),'· examples of extras:',sorted(got-truth,key=lambda x:x[1])[:8])
  # open in the main app and Listen with the backing
  pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(1500)
  r=pg.evaluate("""async()=>{const d=mySongs.find(x=>x.kind==='rec');if(!d)return 'not in My songs';settings.backing=true;settings.headphones=true;openSong(d);document.querySelectorAll('.overlay.show').forEach(o=>o.classList.remove('show'));
    const ev=G.song.events;await $('#btnListen').onclick();await new Promise(r=>setTimeout(r,3500));
    const ok=!!RECB.src&&!!RECB.buf;const pos=RECB.off+(actx.currentTime-RECB.t0)*RECB.rate;const want=(d.recOffset||0)+G.clock*60/G.song.bpm+soundDelay();
    const out={list:document.body.innerText.includes('From a recording'),events:ev.length,first:ev.slice(0,6).map(e=>e.t+':'+e.notes.map(n=>'s'+n.s+'f'+n.f).join('+')),band:!!G.band,backingPlaying:ok,syncErrorMs:Math.round((pos-want)*1000)};
    $('#btnListen').onclick();await new Promise(r=>setTimeout(r,300));out.stopped=!RECB.src;return JSON.stringify(out);}""")
  print(r);print('errors',errs);b.close()
