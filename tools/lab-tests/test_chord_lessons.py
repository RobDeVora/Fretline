# v1.130: every new chord lesson builds, in the written order, with real shapes.
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page(service_workers='block');errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(1200)
  r=pg.evaluate("""()=>COURSE.flatMap(u=>u.lessons).filter(l=>/^c6b|^c10b|^c10-1/.test(l.id)).map(l=>{const m=l.make(1);const ev=m.events;return l.id+' '+l.title+' | '+ev.length+' steps | '+ev.slice(0,12).map(e=>e.chord||e.label).join(' ')+' | shapes '+ev.slice(0,3).map(e=>(e.shape||[]).join('')).join(',');})""")
  print('\n'.join(r))
  pg.evaluate("openLesson(findLesson('c10c-1'))");pg.wait_for_timeout(800)
  print('recall def',pg.evaluate("[G.def.recall,recallHide(),document.querySelector('#peekBtn').style.display]"))
  pg.evaluate("G.clock=1");pg.wait_for_timeout(300)
  px=pg.evaluate("(()=>{const c=document.querySelector('#cv');const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let n=0;for(let i=0;i<d.length;i+=4)if(d[i]>200&&d[i+1]>190&&d[i+2]>240)n++;return n})()")
  print('name pixels while hidden',px)
  pg.screenshot(path='/tmp/recall.png');pg.evaluate("document.querySelector('#peekBtn').click()");print('peek',pg.evaluate("[recallHide(),G.peeks]"))
  pg.evaluate("openLesson(findLesson('c10b-7'))");pg.wait_for_timeout(500);print('slash lesson',pg.evaluate("G.song.events.slice(0,4).map(e=>e.chord+':'+e.shape.join('')).join(' ')"))
  print('units',pg.evaluate("COURSE.map(u=>u.title+':'+u.lessons.length).join(' · ')"));print('errors',errs);b.close()
