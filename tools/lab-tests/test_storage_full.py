# v1.100: the Lab saves a song even when storage is nearly full (drops the raw note list), and says so plainly when it cannot.
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page(service_workers='block');errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/lab/stems.html');pg.wait_for_timeout(1000)
  print(pg.evaluate("""async()=>{const o={};const z=new Float32Array(2000);
    const fill=(left)=>{localStorage.clear();let n=1<<20;const junk='x'.repeat(1024);let i=0;while(true){try{localStorage.setItem('j'+i,junk.repeat(256));i++;}catch(e){break;}}
      // free a little: remove the last junk entries, then top up with small ones until `left` KB remain
      localStorage.removeItem('j'+(i-1));let k=0;while(true){try{localStorage.setItem('s'+k,'y'.repeat(1024));k++;}catch(e){break;}}
      for(let q=0;q<left;q++)localStorage.removeItem('s'+q);};
    const raw=Array.from({length:3000},(_,i)=>({midi:60,t:i,d:1,a:.5}));
    fill(150);R.length=0;await saveRecSong({recRaw:raw,bpm:90,recOffset:0,events:[{t:0,d:1,notes:[{s:1,f:1,midi:60}]}]},z,z,z,z,null).catch(e=>o.e1=String(e));
    o.a=[JSON.parse(localStorage.getItem('fretline:songs')||'[]').length,R.filter(x=>/storage/.test(x)).map(x=>x.slice(0,90))];
    fill(2);R.length=0;await saveRecSong({recRaw:raw,bpm:90,recOffset:0,events:Array.from({length:3000},(_,i)=>({t:i,d:1,notes:[{s:1,f:1,midi:60}]}))},z,z,z,z,null).catch(e=>o.e2=String(e));
    o.bl=R.filter(x=>/storage|ERROR/.test(x)).map(x=>x.slice(0,120));o.b=[JSON.parse(localStorage.getItem('fretline:songs')||'[]').length,$('songOut').style.display,$('songMsg').textContent.slice(0,80)];
    localStorage.clear();return JSON.stringify(o);}"""));print(errs);b.close()
