# v1.133: Basic Pitch shadow mode: records the (fake) mic while playing, analyses at the end, report gets bp columns.
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--autoplay-policy=no-user-gesture-required','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--use-file-for-fake-audio-capture=/tmp/fakemic.wav'])
  ctx=b.new_context(permissions=['microphone'],service_workers='block',viewport={'width':900,'height':460});pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(1200)
  import sys
  if len(sys.argv)>1:pg.evaluate("window.__bpBackend='%s'"%sys.argv[1])
  pg.evaluate("settings.bpShadow=true;openLesson(COURSES.core.flat[8])");pg.wait_for_timeout(800)
  pg.evaluate("document.querySelector('#intro').classList.remove('show')")
  pg.evaluate("document.querySelector('#btnPlay').onclick()");pg.wait_for_timeout(9000)
  print('state while playing',pg.evaluate("[G.playing,bpRec.on,bpRec.n,G.bpState]"))
  pg.evaluate("finish()");pg.wait_for_timeout(500)
  for i in range(40):
    st=pg.evaluate("G.bpState")
    if st in('done','failed'):break
    pg.wait_for_timeout(1500)
  print('state',pg.evaluate("[G.bpState,G.bpInfo,G.bpErr]"))
  rep=pg.evaluate("diagReport()").split('\n');print('\n'.join(rep[:6])[:900])
  w=pg.evaluate("(async()=>{const b=bpWavBlob();const a=new Uint8Array(await b.arrayBuffer());return [b.size,String.fromCharCode(...a.slice(0,4)),String.fromCharCode(...a.slice(8,12)),bpRec.n*2+44]})()")
  print('wav',w,'ok' if w[0]==w[3] and w[1]=='RIFF' and w[2]=='WAVE' else 'BAD')
  print('btn',pg.evaluate("[...document.querySelectorAll('#rReport button')].map(b=>b.textContent)"))
  print('rows',[r for r in rep if r.startswith('#0 ') or r.startswith('Audio')][:2])
  print('errors',errs[:3]);b.close()
