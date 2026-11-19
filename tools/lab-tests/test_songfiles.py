# v1.94: song folders on the phone. A fake SongFiles plugin records what the app asks the phone to do.
import json,sys
from playwright.sync_api import sync_playwright
MOCK="""window.__w=[];window.__r=[];window.__fail=false;window.Capacitor={isNativePlatform:()=>true,isPluginAvailable:n=>n==='SongFiles',Plugins:{SongFiles:{
 write:async o=>{if(window.__fail)throw new Error('disk full');window.__w.push(o);return {path:'x'}},removeDir:async o=>{window.__r.push(o.dir);return {removed:1}}}}};"""
songs=[{'id':'m-1','cat':'mine','kind':'gen','title':'Same Name','bpm':90,'bpb':4,'events':[]},
       {'id':'m-2','cat':'mine','kind':'gen','title':'Same Name','bpm':90,'bpb':4,'events':[]},
       {'id':'m-3','cat':'mine','kind':'gen','title':'Slash/Colon: Test?','bpm':90,'bpb':4,'events':[],'dir':'Lab Song'}]
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page(service_workers='block');errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script(MOCK+"localStorage.setItem('fretline:songs',"+json.dumps(json.dumps(songs))+");")
  pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(6500)
  r={}
  r['first']=pg.evaluate("window.__w.map(o=>o.dir+' | '+o.name)")
  r['box']=pg.evaluate("document.querySelector('#sFilesBox').style.display+' checked='+document.querySelector('#sSaveFiles').checked")
  # nothing changes -> nothing written
  pg.evaluate("window.__w.length=0;sfSoon(50)");pg.wait_for_timeout(500);r['again']=pg.evaluate("window.__w.length")
  # tempo-like change: only that song is rewritten
  pg.evaluate("mySongs[0].bpm=100;store.set('songs',mySongs)");pg.wait_for_timeout(2500);r['changed']=pg.evaluate("window.__w.map(o=>o.dir)")
  # delete one: its folder goes
  pg.evaluate("window.__w.length=0;mySongs=mySongs.filter(x=>x.id!=='m-2');store.set('songs',mySongs)");pg.wait_for_timeout(2500);r['removed']=pg.evaluate("[window.__r.slice(),window.__w.length,Object.keys(store.get('songFiles',{}))]")
  # failure: not marked as saved, retried next time
  pg.evaluate("window.__fail=true;mySongs[0].bpm=110;store.set('songs',mySongs)");pg.wait_for_timeout(2500);r['fail']=pg.evaluate("[document.querySelector('#sFilesMsg').textContent, store.get('songFiles',{})['m-1'].hash]")
  pg.evaluate("window.__fail=false;window.__w.length=0;document.querySelector('#sFilesNow').click()");pg.wait_for_timeout(1500);r['retry']=pg.evaluate("[window.__w.length,document.querySelector('#sFilesMsg').textContent]")
  # switched off: no writes, no removals
  pg.evaluate("document.querySelector('#sSaveFiles').checked=false;document.querySelector('#sSaveFiles').onchange({target:{checked:false}});window.__w.length=0;window.__r.length=0;mySongs=mySongs.filter(x=>x.id!=='m-3');store.set('songs',mySongs)");pg.wait_for_timeout(2500);r['off']=pg.evaluate("[window.__w.length,window.__r.length]")
  print(json.dumps(r,indent=1));print('errors',errs)
  # Lab: sources saved next to the song
  pg2=b.new_page(service_workers='block');pg2.add_init_script(MOCK+"localStorage.setItem('fretline:songs',"+json.dumps(json.dumps(songs))+");")
  pg2.goto('http://localhost:8769/lab/stems.html');pg2.wait_for_timeout(1500)
  print(pg2.evaluate("""async()=>{SRCFILES=[{kind:'tab',name:'song_tab.mid',bytes:new Uint8Array([77,84,104,100,1,2,3])},{kind:'chords',name:'Chords.txt',text:'G D Em C'}];
    const d=pickSongDir('Same Name');await saveSources(d);return JSON.stringify([d,pickSongDir('Lab Song'),window.__w.map(o=>o.dir+' | '+o.name+' | '+(o.text||o.data))]);}"""))
  b.close()
