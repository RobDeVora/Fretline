# v1.98: "Open with Fretline": a MIDI opened on the main screen lands in the Lab's first sheet box;
# a second MIDI goes to the second box; a song file (audio) goes into the song box; files arriving while the Lab shows work too.
import base64,json,struct,io,wave
from playwright.sync_api import sync_playwright
mid=base64.b64encode(open('/tmp/tysk.mid','rb').read()).decode();mid2=base64.b64encode(open('/tmp/tysk_chords.mid','rb').read()).decode()
buf=io.BytesIO();w=wave.open(buf,'wb');w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000);w.writeframes(b'\0\0'*8000);w.close();wav=base64.b64encode(buf.getvalue()).decode()
def mock(first):
  return "window.__h=null;window.Capacitor={isNativePlatform:()=>true,isPluginAvailable:n=>n==='Incoming',Plugins:{Incoming:{getPending:async()=>{if(sessionStorage.getItem('sent'))return {};sessionStorage.setItem('sent','1');return {item:%s};},addListener:async(n,h)=>{window.__h=h;return {remove(){}}}}}};" % json.dumps(first)
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');ctx=b.new_context(service_workers='block');errs=[]
  pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
  # the item is only delivered once (like the real plugin)
  pg.add_init_script(mock({'name':'Thought You Should Know.mid','data':mid}))
  pg.goto('http://localhost:8769/index.html');pg.wait_for_url('**/lab/stems.html',timeout=15000);pg.wait_for_timeout(2500)
  print('after MIDI on main:',pg.evaluate("[location.pathname.slice(-14),$('status').textContent,!!SHEETFILE,SHEETFILE&&SHEETFILE.name,SHEETFILE2&&SHEETFILE2.name]"))
  # a second MIDI while the Lab shows -> second box
  pg.evaluate("(d)=>window.__h({name:'chords.mid',data:d})",mid2);pg.wait_for_timeout(2500)
  print('second MIDI:',pg.evaluate("[$('status').textContent,SHEETFILE&&SHEETFILE.name,SHEETFILE2&&SHEETFILE2.name]"))
  # an audio file -> the song box, and the Split button wakes up
  pg.evaluate("(d)=>window.__h({name:'My Song_demo.wav',data:d})",wav);pg.wait_for_timeout(1500)
  print('audio:',pg.evaluate("[$('status').textContent,$('file').files[0]&&$('file').files[0].name,$('ttl').value,$('go').disabled]"))
  print('errors',errs);b.close()
