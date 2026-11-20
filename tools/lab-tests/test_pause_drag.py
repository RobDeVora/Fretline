# v1.120: Listen can pause and resume; dragging the highway moves through the song and carries on from there.
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--autoplay-policy=no-user-gesture-required']);pg=b.new_page(service_workers='block',viewport={'width':800,'height':400});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(1200)
  pg.evaluate("()=>{const d=LIB.find(x=>x.kind!=='chords')||LIB[0];openSong(d);}");pg.wait_for_timeout(800)
  print('screen',pg.evaluate("curScreen"),pg.evaluate("G.song.events.length"))
  pg.click('#btnListen');pg.wait_for_timeout(2500)
  print('listening:',pg.evaluate("[G.listen,G.playing,$('btnListen')?0:document.querySelector('#btnListen').textContent,G.clock.toFixed(2)]"))
  pg.click('#btnListen');pg.wait_for_timeout(300);c1=pg.evaluate("G.clock");pg.wait_for_timeout(800)
  print('paused:',pg.evaluate("[G.listen,G.playing,document.querySelector('#btnListen').textContent,G.clock.toFixed(2)]"),'same clock',abs(pg.evaluate("G.clock")-c1)<1e-6)
  pg.click('#btnListen');pg.wait_for_timeout(1200)
  print('resumed:',pg.evaluate("[G.listen,G.playing,document.querySelector('#btnListen').textContent,G.clock.toFixed(2)]"))
  # drag the highway left by 300 px -> clock moves forward ~300/ppb beats; playing resumes
  box=pg.evaluate("(()=>{const r=document.querySelector('#cv').getBoundingClientRect();return [r.x,r.y,r.width,r.height]})()")
  c0=pg.evaluate("G.clock");x=box[0]+box[2]*0.6;y=box[1]+box[3]*0.5
  pg.mouse.move(x,y);pg.mouse.down();pg.mouse.move(x-150,y,steps=6);pg.wait_for_timeout(100)
  mid=pg.evaluate("[G.playing,G.clock]");pg.mouse.up();pg.wait_for_timeout(300)
  print('drag: clock',round(c0,2),'->',round(mid[1],2),'playing during drag',mid[0],'after',pg.evaluate("G.playing"),'ppb',pg.evaluate("ppb0"))
  pg.mouse.move(x,y);pg.mouse.down();pg.mouse.move(x+400,y,steps=6);pg.mouse.up();pg.wait_for_timeout(200)
  print('drag back: clock',round(pg.evaluate("G.clock"),2),'states ok',pg.evaluate("G.state.slice(0,5).join('')"))
  print('errors',errs);b.close()
