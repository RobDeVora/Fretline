import base64,json
from playwright.sync_api import sync_playwright
data=base64.b64encode(open(__import__('sys').argv[1],'rb').read()).decode()
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])
  for name,vp in [('land',{'width':915,'height':412}),('port',{'width':412,'height':915})]:
    pg=b.new_page(viewport=vp,device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(600)
    pg.evaluate("""async(b64)=>{const bytes=Uint8Array.from(atob(b64),c=>c.charCodeAt(0));
      openImport();await loadImportFile(new File([bytes],'Marlboro_Man_Test'));$('#impTitle').value='MM';$('#impPart').value='0';$('#impPart').onchange();await new Promise(r=>setTimeout(r,30));
      $('#impStrum').value='D-DUD-DU';$('#impStrum').dispatchEvent(new Event('change'));$('#impSave').onclick();await new Promise(r=>setTimeout(r,200));
      document.querySelectorAll('.overlay.show').forEach(o=>o.classList.remove('show'));const d=G.def;usePart(d,'combo');openSong(d);}""",data)
    for c,fb in [(0.5,True),(15.2,True),(0.5,False),(3.0,True)]:
      info=pg.evaluate(f"()=>{{settings.fretboard={str(fb).lower()};G.playing={str(c==3.0).lower()};syncFocus();G.clock={c};resizeCanvas();G.clock={c};draw(performance.now());const i=firstPending();const e=G.song.events[i];return {{i,hand:e.hand,f:(e.notes||[]).map(n=>'EADGBe'[n.s]+n.f+':'+n.fg).join(' '),shape:e.fgs&&e.fgs.join('')}};}}")
      pg.wait_for_timeout(100);fn=f'/tmp/mm/fg_{name}_{int(c)}_{"fb" if fb else "nofb"}.png';pg.screenshot(path=fn);print(fn,info)
    print(name,errs);pg.close()
  b.close()
