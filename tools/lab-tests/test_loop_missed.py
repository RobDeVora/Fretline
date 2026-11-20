# v1.129: Loop button wraps the clock, most-missed bars + practise button, slow-down offer, share-as-file button.
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--autoplay-policy=no-user-gesture-required','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream']);pg=b.new_page(service_workers='block',viewport={'width':800,'height':400});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(1200)
  pg.evaluate("()=>{const d=LIB.find(x=>x.kind!=='chords')||LIB[0];openSong(d);}");pg.wait_for_timeout(800)
  bpb=pg.evaluate("G.song.bpb")
  pg.evaluate("G.clock=%d+0.5"%(bpb*2));pg.click('#loopBtn')
  print('loop',pg.evaluate("G.loop"),pg.inner_text('#loopBtn'))
  pg.click('#loopBtn');print('loop 4',pg.evaluate("G.loop"));pg.click('#loopBtn');pg.click('#loopBtn');print('off after 8->0',pg.evaluate("G.loop"),pg.inner_text('#loopBtn'))
  pg.click('#loopBtn')  # back to 2 bars at bar 3
  pg.evaluate("G.playing=true;G.listen=false;G.clock=G.loop.b+0.1")
  pg.wait_for_timeout(400);print('wrapped clock',round(pg.evaluate("G.clock"),2),'loop a',pg.evaluate("G.loop.a"),'(clock should be near a)')
  pg.evaluate("G.playing=false;G.loop=null;loopLabel()")
  # fake a finished run with misses in bars 2 and 5
  pg.evaluate("""()=>{resetRun();G.mode='play';const S=G.song,bpb=S.bpb;S.events.forEach((e,i)=>{const bar=Math.floor(e.t/bpb+1e-6);G.state[i]=(bar===1||bar===4)?2:1;});G.diag={0:{}};finish();}""")
  print('missed buttons',pg.evaluate("[...document.querySelectorAll('#rMissed button')].map(b=>b.textContent)"))
  print('share btn',pg.evaluate("[...document.querySelectorAll('#rReport button')].map(b=>b.textContent)"))
  pg.evaluate("document.querySelector('#rMissed button').click()");pg.wait_for_timeout(300)
  print('after practise: loop',pg.evaluate("G.loop"),'speed',pg.evaluate("G.speed"),'playing',pg.evaluate("G.playing"),'results shown',pg.evaluate("document.querySelector('#results').classList.contains('show')"))
  pg.evaluate("G.playing=false;G.speed=1;G.loop=null;G.mode='play'");
  for i in range(4):pg.evaluate("slowCheck()")
  print('slow offer shown',pg.evaluate("document.querySelector('#slowOffer').style.display"));pg.click('#soSlow');print('speed',pg.evaluate("G.speed"))
  print('errors',errs);b.close()
