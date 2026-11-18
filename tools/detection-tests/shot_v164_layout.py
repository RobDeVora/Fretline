import base64,json
from playwright.sync_api import sync_playwright
data=base64.b64encode(open('/tmp/mm/mm.mid','rb').read()).decode()
FAKE="""window.Capacitor={isNativePlatform:()=>true,Plugins:{NativeMic:{_l:{},addListener(n,f){this._l[n]=f;return Promise.resolve({remove(){}});},
 outputRoute(){return Promise.resolve({route:'bluetooth',name:'Galaxy Buds'});},listInputs(){return Promise.resolve({inputs:[]});},start(){return Promise.reject(new Error('test'));},stop(){return Promise.resolve();}}}};"""
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])
  # 2) hand size on a 838x312-ish app screen (status bar shown) and 891x411 full screen
  for name,vp in [('full',{'width':891,'height':411}),('port',{'width':411,'height':891})]:
    pg=b.new_page(viewport=vp,device_scale_factor=2);pg.on('pageerror',lambda e:print('ERR',name,e));pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(600)
    pg.evaluate("""async(b64)=>{settings.fretboard=false;const bytes=Uint8Array.from(atob(b64),c=>c.charCodeAt(0));
      openImport();await loadImportFile(new File([bytes],'MM'));$('#impTitle').value='MM';$('#impPart').value='0';$('#impPart').onchange();await new Promise(r=>setTimeout(r,30));
      $('#impSave').onclick();await new Promise(r=>setTimeout(r,200));document.querySelectorAll('.overlay.show').forEach(o=>o.classList.remove('show'));const d=G.def;usePart(d,'combo');openSong(d);
      G.mode='play';G.speed=0.0001;G.clock=15.95;G.playing=true;syncFocus();await new Promise(r=>setTimeout(r,600));}""",data)
    pg.wait_for_timeout(150);pg.screenshot(path=f'/tmp/mm/v164_{name}.png');print(name,pg.evaluate("[CW,CH]"));pg.close()
  pg=b.new_page(viewport={'width':891,'height':411},device_scale_factor=2);pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(600)
  pg.evaluate('''async()=>{settings.fretboard=false;settings.sing=true;openSong({id:'m-ly',cat:'mine',title:'Grace',bpm:80,bpb:3,kind:'chords',cb:3,src:"A[G]mazing [G7]grace, how [C]sweet the [G]sound\\nThat [G]saved a [Em]wretch like [D]me",capo:0,strum:'D-DUDU'});
    document.querySelectorAll('.overlay.show').forEach(o=>o.classList.remove('show'));G.mode='play';G.speed=0.0001;G.clock=2.9;G.playing=true;syncFocus();await new Promise(r=>setTimeout(r,600));}''')
  pg.wait_for_timeout(150);pg.screenshot(path='/tmp/mm/v164_lyrics.png');print('lyrics',pg.evaluate("[CW,CH,G._Z,G._ctrlH]"));pg.close()
  b.close()
