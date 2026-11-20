# v1.130: every new chord lesson builds, in the written order, with real shapes.
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page(service_workers='block');errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(1200)
  r=pg.evaluate("""()=>COURSE.flatMap(u=>u.lessons).filter(l=>/^c6b|^c10b|^c10-1/.test(l.id)).map(l=>{const m=l.make(1);const ev=m.events;return l.id+' '+l.title+' | '+ev.length+' steps | '+ev.slice(0,12).map(e=>e.chord||e.label).join(' ')+' | shapes '+ev.slice(0,3).map(e=>(e.shape||[]).join('')).join(',');})""")
  print('\n'.join(r));print('units',pg.evaluate("COURSE.map(u=>u.title+':'+u.lessons.length).join(' · ')"));print('errors',errs);b.close()
