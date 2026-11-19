# v1.93: a recording song with versions (from real_files.py: /tmp/tysk_merge.json): the app lists them under 🎸,
# switching changes the steps and the real times, a tempo change keeps every version on its real times.
import json
from playwright.sync_api import sync_playwright
d=json.load(open('/tmp/tysk_merge.json'));d['id']='m-rec-v1';d['cat']='mine'
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page(viewport={'width':915,'height':412},device_scale_factor=2,service_workers='block');errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(700)
  r=pg.evaluate("""async(d)=>{const o={};mySongs=[d];store.set('songs',mySongs);applyTuning('eb');openSong(d);document.querySelectorAll('.overlay.show').forEach(x=>x.classList.remove('show'));
    o.start=[G.song.events.length,partLabel(d),$('#partBtn').style.display,$('#partBtn').textContent];
    $('#partBtn').onclick();await new Promise(r=>setTimeout(r,100));o.picker=[$('#msgTitle').textContent,[...document.querySelectorAll('#msgBody .partPick')].map(b=>b.textContent.replace(/\\s+/g,' ')).join(' || ')];
    const btns=[...document.querySelectorAll('#msgBody .partPick')];btns[1].onclick();await new Promise(r=>setTimeout(r,200));
    o.chords=[G.def.partSel,G.song.events.length,partLabel(G.def),G.def.recEvT.length,G.song.events.slice(0,3).map(e=>e.chord||e.label||'?').join()];
    $('#partBtn').onclick();await new Promise(r=>setTimeout(r,100));[...document.querySelectorAll('#msgBody .partPick')][2].onclick();await new Promise(r=>setTimeout(r,200));
    o.tab=[G.def.partSel,G.song.events.length,partLabel(G.def),G.def.recEvT.length];
    // real time of every step vs its recEvT, for every version, after a tempo change to 70 BPM
    const chk=(def)=>{const spb=60/def.bpm;const f=(ev,T)=>{let mx=0;ev.forEach((e,i)=>{mx=Math.max(mx,Math.abs(def.recOffset+e.t*spb-T[i]));});return Math.round(mx*1000);};
      return [f(def.events,def.recEvT),...def.parts.map(p=>p.events.length+':'+f(p.events,p.recEvT))].join(' ');};
    o.before=chk(G.def);const nd=recRetime(G.def,70);o.after70=nd.bpm+' bpm · max step-time error (ms) active / versions: '+chk(nd);
    const nd2=recRetime(nd,140);o.after140=chk(nd2);return JSON.stringify(o,null,1);}""",d)
  print(r);pg.evaluate("()=>{usePart(G.def,'0');openSong(G.def);}");pg.wait_for_timeout(300);pg.screenshot(path='/tmp/cv/ver.png');print(errs);b.close()
