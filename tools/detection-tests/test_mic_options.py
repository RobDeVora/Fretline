import sys
from playwright.sync_api import sync_playwright
FAKE="""window.Capacitor={isNativePlatform:()=>true,Plugins:{NativeMic:{
 addListener(){return Promise.resolve({remove(){}});},
 %s
 start(o){window.__startArgs=o;return Promise.resolve({sampleRate:48000,source:o.type==='bluetooth'?'call mode':'voice recognition',encoding:'float',device:o.type==='bluetooth'?'Bluetooth headset mic (Buds)':'built-in mic (X)'});},
 stop(){return Promise.resolve();}}}};"""
LIST="listInputs(){return Promise.resolve({inputs:[{type:'builtin',name:'X'},{type:'builtin',name:'X'},{type:'bluetooth',name:'Galaxy Buds'}]});},"
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--autoplay-policy=no-user-gesture-required'])
  for name,extra in [('new app',LIST),('old app','')]:
    pg=b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.add_init_script(FAKE%extra);pg.goto(''+'http://localhost:8766/index.html');pg.wait_for_timeout(500)
    r=pg.evaluate("""async()=>{await ensureAudio();await enableMic();await fillMicList();
      const opts=[...document.querySelectorAll('#sMic option')].map(o=>(o.disabled?'[off] ':'')+o.value+'='+o.textContent);
      const s=document.querySelector('#sMic');s.value='n:bluetooth';s.dispatchEvent(new Event('change'));await new Promise(r=>setTimeout(r,300));
      return {opts,start:window.__startArgs,sel:s.value,info:micInfo(),hint:document.querySelector('#sMicHint').textContent.slice(0,70)};}""")
    print(name,r,errs);pg.close()
  b.close()
