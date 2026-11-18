import sys
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('file://'+sys.argv[1]+'/index.html');pg.wait_for_timeout(500)
  print(pg.evaluate("""()=>{const e={t:0,d:1,notes:[{s:3,f:2,midi:57}]};const out={};
   const setup=()=>{G.pops=[];G.wp=null;G.diag={0:{notes:[]}};G.state=new Uint8Array(1);settings.fx='miss';det.onsetAt=1000;};
   // 1: right note credited 100 ms later -> cancelled
   setup();wrongSuspect(e,0,1140,'wrong:C#4','Wrong note');wrongSettle(1200);G.state[0]=1;wrongSettle(1240);wrongSettle(1500);out.hitAfter=[G.pops.map(p=>p.text),G.diag[0].notes];
   // 2: nothing else happens -> reported after 250 ms
   setup();wrongSuspect(e,0,1140,'wrong:C#4','Wrong note');wrongSettle(1300);const early=G.pops.length;wrongSettle(1400);out.noHit=[early,G.pops.map(p=>p.text),G.diag[0].notes];
   // 3: a new pick arrives -> dropped (the new pick is judged on its own)
   setup();wrongSuspect(e,0,1140,'wrong:absent','Wrong note');det.onsetAt=1250;wrongSettle(1260);out.newPick=[G.pops.map(p=>p.text),G.diag[0].notes];
   // 4: timing grades
   settings.timing=1;out.grades=[0,-40,70,-90,130,-200].map(o=>timingGrade(o).text);settings.timing=1.5;out.relaxed=[70,130,160].map(o=>timingGrade(o).text);settings.timing=1;
   return JSON.stringify(out);}"""));print(errs);b.close()
