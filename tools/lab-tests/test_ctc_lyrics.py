# v1.121: lyrics timed by the speech model. Needs /tmp/mm.mp3 (any song with singing) served on :8771 and the lyrics below (for the owner's Marlboro Man test song).
import json,sys
from playwright.sync_api import sync_playwright
LYR="""That was me
A jaw like steel, a heart like stone
Leather tough to the bone
And always gone
I'm born to run
To anywhere than where I was
I'd leave it all in the dust
Just like us
Ain't much changed in all this time
Still leavin' everythin' I love behind
Too much pride to need a thing
But this hat, these boots, these worn-out
Mountains in the background, hell of a view
But all I see is me missin' you"""
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page(service_workers='block');errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));logs=[]
  pg.on('console',lambda m:logs.append(m.text) if m.type=='error' else None)
  pg.goto('http://localhost:8769/lab/stems.html?ortbase=http://localhost:8771/ortpkg/package/dist/');pg.wait_for_timeout(800)
  r=pg.evaluate("""async(t)=>{const f=new File([await (await fetch('http://localhost:8771/mm.mp3')).arrayBuffer()],'mm.mp3');const [L,R]=await decode(f,0);
    const s=performance.now();const vox=await toRate([L],16000);const r=await ctcLyrics(t,L,R,142.93,0.68,vox);return {ms:performance.now()-s,logtxt:document.getElementById('log')?document.getElementById('log').textContent.slice(-600):'',sec:r.sec.map(x=>[x.t0,x.segs.map(w=>w.text).join('').slice(0,30)]),log:R_()}}""".replace(",log:R_()",""),LYR)
  print('ms',round(r['ms']));print(r['logtxt'])
  for t,s in r['sec']:print('%d:%04.1f'%(t//60,t%60),s)
  print(errs,logs[:3]);b.close()
