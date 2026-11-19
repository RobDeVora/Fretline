# v1.97: every song folder gets .mid files (one per version) that read back to the same notes.
import json
from playwright.sync_api import sync_playwright
d=json.load(open('/tmp/tysk_merge.json'));d['id']='m-rec-t';d['title']='TYSK: both/versions'
MOCK="window.__w=[];window.Capacitor={isNativePlatform:()=>true,isPluginAvailable:n=>n==='SongFiles',Plugins:{SongFiles:{write:async o=>{window.__w.push(o);return {path:'x'}},removeDir:async o=>({removed:1})}}};"
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page(service_workers='block');errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script(MOCK+"localStorage.setItem('fretline:songs',"+json.dumps(json.dumps([d]))+");")
  pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(6500)
  print(pg.evaluate("""()=>{const out=[];const names=__w.map(o=>o.name);const song=mySongs[0];
    for(const o of __w){if(!/\\.mid$/.test(o.name))continue;const u=Uint8Array.from(atob(o.data),c=>c.charCodeAt(0));const info=parseMidi(u);const parts=info.parts||[];
      const nn=parts.reduce((a,q)=>a+(q.count||0),0);out.push(o.name+' '+u.length+' B, bpm '+Math.round(info.bpm)+', notes read back '+nn);}
    const want=song.parts.map(q=>q.events.reduce((a,e)=>a+e.notes.length,0));return JSON.stringify({names,out,want});}"""));print(errs);b.close()
