import base64,json
from playwright.sync_api import sync_playwright
data=base64.b64encode(open(__import__('sys').argv[1],'rb').read()).decode()
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream']);pg=b.new_page(viewport={'width':844,'height':390},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(600)
  out=pg.evaluate("""async(b64)=>{const bytes=Uint8Array.from(atob(b64),c=>c.charCodeAt(0));const res=[];
    // the user's path: rhythm part with a pattern chosen in the import box, then Lead + rhythm when opening
    openImport();await loadImportFile(new File([bytes],'Marlboro_Man_Test'));$('#impTitle').value='MM';$('#impPart').value='0';$('#impPart').onchange();await new Promise(r=>setTimeout(r,30));
    $('#impStrum').value='D-DUD-DU';$('#impStrum').dispatchEvent(new Event('change'));$('#impSave').onclick();await new Promise(r=>setTimeout(r,200));
    document.querySelectorAll('.overlay.show').forEach(o=>o.classList.remove('show'));
    const d=G.def;pickPart(d,()=>openSong(d));document.querySelector('#msgBody .partPick[data-v=combo]').click();await new Promise(r=>setTimeout(r,200));
    const bpb=d.bpb,ev=G.song.events;const bars={};for(const e of ev){const k=Math.floor(e.t/bpb+1e-6);(bars[k]=bars[k]||new Set()).add(e.strum?'strum':e.ld?'lead':'chord');}
    res.push({strum:$('#strumSel').value,n:ev.length,trim:d.trim,first:ev[0].t,bars:Object.entries(bars).map(([k,s])=>k+':'+[...s].join('+')).join(' ')});
    for(const v of [...$('#strumSel').options].map(o=>o.value).filter(v=>v!=='__edit')){$('#strumSel').value=v;$('#strumSel').dispatchEvent(new Event('change'));
      const e2=G.song.events;res.push([v||'(as written)',e2.length,'lead',e2.filter(e=>e.ld).length,'strums',e2.filter(e=>e.strum).length,'strum in lead bars',e2.filter(e=>e.strum&&e.t<16).length]);}
    $('#strumSel').value='D-DUD-DU';$('#strumSel').dispatchEvent(new Event('change'));return res;}""",data)
  for x in out:print(x)
  for c in [0.5,17]:
    pg.evaluate(f"()=>{{G.clock={c};resizeCanvas();draw(performance.now());}}");pg.wait_for_timeout(150);pg.screenshot(path=f'/tmp/combo_{int(c)}.png')
  print(errs);b.close()
