# v1.101: songs live in IndexedDB. Old localStorage songs move over once; adding, editing and deleting persist across
# reloads; the Lab and the main page share the same list; 12 MB of songs (more than localStorage could ever hold) work.
import json
from playwright.sync_api import sync_playwright
old=[{'id':'m-a','cat':'mine','kind':'gen','title':'Old A','bpm':90,'bpb':4,'events':[]},{'id':'m-b','cat':'mine','kind':'gen','title':'Old B','bpm':90,'bpb':4,'events':[]}]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');ctx=b.new_context(service_workers='block');pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!localStorage.getItem('seeded')){localStorage.setItem('seeded','1');localStorage.setItem('fretline:songs',%s);}"%json.dumps(json.dumps(old)))
  pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(1500)
  print('migrated:',pg.evaluate("[mySongs.map(x=>x.title).join(),localStorage.getItem('fretline:songs'),SongDB.ok]"))
  # add a 12 MB pile of songs (80 x 150 KB), delete one, reload
  pg.evaluate("""async()=>{const big='n'.repeat(150000);for(let i=0;i<80;i++)mySongs.unshift({id:'m-big'+i,cat:'mine',kind:'gen',title:'Big '+i,bpm:90,bpb:4,events:[],pad:big});
    mySongs=mySongs.filter(x=>x.id!=='m-b');await SongDB.save(mySongs);}""")
  pg.reload();pg.wait_for_timeout(2000)
  print('after reload:',pg.evaluate("[mySongs.length,mySongs[0].title,mySongs.some(x=>x.id==='m-b'),mySongs.some(x=>x.id==='m-a'),document.querySelectorAll('#list .song, #list li').length]"))
  # edit one song (tempo) and persist
  pg.evaluate("async()=>{mySongs[3].bpm=123;store.set('songs',mySongs);await SongDB.save(mySongs);}");pg.reload();pg.wait_for_timeout(1800)
  print('edit kept:',pg.evaluate("mySongs[3].bpm"))
  # Lab: reads the same list and adds a song that the main page then shows
  lab=ctx.new_page();lab.on('pageerror',lambda e:errs.append('lab '+str(e)));lab.goto('http://localhost:8769/lab/stems.html');lab.wait_for_timeout(1500)
  print('lab:',lab.evaluate("""async()=>{await SongDB.load();const n=SongDB.songs().length;const z=new Float32Array(2000);await saveRecSong({bpm:90,recOffset:0,events:[{t:0,d:1,notes:[{s:1,f:1,midi:60}]}]},z,z,z,z,null);return [n,SongDB.songs().length,SongDB.songs()[0].title,$('songOut').style.display]}"""))
  pg.reload();pg.wait_for_timeout(1800)
  print('main sees lab song:',pg.evaluate("[mySongs.length,mySongs[0].title]"))
  pg.screenshot(path='/tmp/songdb.png')
  print('storage line:',pg.evaluate("async()=>{syncSettingsUI();await new Promise(r=>setTimeout(r,400));return $('#sStoreMsg').textContent}"))
  print('errors',errs);b.close()
