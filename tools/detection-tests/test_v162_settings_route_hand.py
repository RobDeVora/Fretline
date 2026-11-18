import base64,json
from playwright.sync_api import sync_playwright
data=base64.b64encode(open(__import__('sys').argv[1],'rb').read()).decode()
FAKE="""window.Capacitor={isNativePlatform:()=>true,Plugins:{NativeMic:{_l:{},addListener(n,f){this._l[n]=f;return Promise.resolve({remove(){}});},
 outputRoute(){return Promise.resolve({route:'bluetooth',name:'Galaxy Buds'});},listInputs(){return Promise.resolve({inputs:[]});},start(){return Promise.reject(new Error('test'));},stop(){return Promise.resolve();}}}};"""
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])
  # 1) settings tabs
  pg=b.new_page(viewport={'width':412,'height':915},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("localStorage.clear();"+FAKE)
  pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(800)
  r=pg.evaluate("""async()=>{const out={};settings.soundDelay=150;saveSettings();out.start={route:outRoute,delays:settings.soundDelays,phones:settings.headphones};
    const P=Capacitor.Plugins.NativeMic;P._l.route({route:'speaker',name:''});out.speaker={d:settings.soundDelay,ph:settings.headphones,hint:G.notice};
    settings.soundDelay=40;saveSettings();P._l.route({route:'bluetooth',name:'Galaxy Buds'});out.backBT={d:settings.soundDelay,ph:settings.headphones};
    P._l.route({route:'speaker',name:''});out.backSpk={d:settings.soundDelay,ph:settings.headphones};out.maps={d:settings.soundDelays,p:settings.phonesBy};
    $('#btnSettings').onclick();await new Promise(r=>setTimeout(r,300));out.tabs=[...document.querySelectorAll('#sTabs button')].map(b=>b.textContent+(b.classList.contains('on')?'*':''));
    out.visible=[...document.querySelectorAll('#settings .stab')].map(d=>d.dataset.t+':'+(getComputedStyle(d).display!=='none')+':'+d.querySelectorAll('.field').length);
    return out;}""")
  print(json.dumps(r,indent=1));pg.screenshot(path='/tmp/mm/settings_mic.png')
  pg.evaluate("settingsTab('disp')");pg.wait_for_timeout(150);pg.screenshot(path='/tmp/mm/settings_disp.png')
  pg.evaluate("settingsTab('col')");pg.wait_for_timeout(300);pg.screenshot(path='/tmp/mm/settings_col.png')
  print(errs);pg.close()
  # 2) hand size on a 838x312-ish app screen (status bar shown) and 891x411 full screen
  for name,vp in [('app_bars',{'width':838,'height':381}),('app_full',{'width':891,'height':411})]:
    pg=b.new_page(viewport=vp,device_scale_factor=2);pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(600)
    pg.evaluate("""async(b64)=>{settings.fretboard=false;const bytes=Uint8Array.from(atob(b64),c=>c.charCodeAt(0));
      openImport();await loadImportFile(new File([bytes],'MM'));$('#impTitle').value='MM';$('#impPart').value='0';$('#impPart').onchange();await new Promise(r=>setTimeout(r,30));
      $('#impSave').onclick();await new Promise(r=>setTimeout(r,200));document.querySelectorAll('.overlay.show').forEach(o=>o.classList.remove('show'));const d=G.def;usePart(d,'combo');openSong(d);
      G.mode='wait';G.clock=1.5;G.playing=true;syncFocus();await new Promise(r=>setTimeout(r,600));}""",data)
    pg.wait_for_timeout(150);pg.screenshot(path=f'/tmp/mm/{name}.png');print(name,pg.evaluate("[CW,CH]"));pg.close()
  b.close()
