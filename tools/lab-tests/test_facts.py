# v1.106: the Facts page. Every control in the app (buttons, inputs, selects) must be covered by an item in facts.js,
# the page renders and searches, and the disclaimer appears on the Facts page only.
import json,re
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page(service_workers='block',viewport={'width':915,'height':412});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(1500)
  r=pg.evaluate("""async()=>{await factsLoad();const cov=new Set();FACTS.sections.forEach(s=>s.items.forEach(i=>(i.ids||[]).forEach(x=>cov.add(x))));
    const own=id=>/^facts/.test(id);
    const missing=[...document.querySelectorAll('button[id],input[id],select[id],textarea[id]')].map(e=>e.id).filter(id=>!cov.has(id)&&!own(id));
    $('#btnFacts').onclick&&await $('#btnFacts').onclick();await new Promise(r=>setTimeout(r,300));
    const o={screen:curScreen,missing,sections:FACTS.sections.length,items:FACTS.sections.reduce((a,s)=>a+s.items.length,0),warn:!!document.querySelector('.factsWarn'),h3:document.querySelectorAll('#factsDoc h3').length};
    $('#factsFind').value='capo';$('#factsFind').oninput({target:$('#factsFind')});o.capo=[document.querySelectorAll('#factsDoc b').length,!!document.querySelector('.factsWarn')];
    $('#factsFind').value='zzzz';$('#factsFind').oninput({target:$('#factsFind')});o.none=$('#factsDoc').textContent;
    $('#factsFind').value='';$('#factsFind').oninput({target:$('#factsFind')});return o;}""")
  print(json.dumps(r));pg.screenshot(path='/tmp/facts.png')
  html=open('/home/claude/fretline/index.html').read()+open('/home/claude/fretline/lab/stems.html').read()
  print('disclaimer text outside facts.js:',len(re.findall(r'not responsible for any injury',html)))
  print('errors',errs);b.close()
