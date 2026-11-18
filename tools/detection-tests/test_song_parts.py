import base64,json,sys
from playwright.sync_api import sync_playwright
data=base64.b64encode(open(sys.argv[1],'rb').read()).decode()
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream']);pg=b.new_page(viewport={'width':390,'height':844},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(600)
  r=pg.evaluate("""async(b64)=>{const out={};const bytes=Uint8Array.from(atob(b64),c=>c.charCodeAt(0));
    openImport&&openImport();await loadImportFile(new File([bytes],'Marlboro_Man_Test'));$('#impTitle').value='Marlboro Man Test';
    $('#impPart').value='1';$('#impPart').onchange();await new Promise(r=>setTimeout(r,50)); // pick the lead in the import box
    out.importPick=$('#impPart').selectedOptions[0].textContent;
    $('#impSave').onclick();await new Promise(r=>setTimeout(r,300));
    const d=mySongs[mySongs.length-1];out.saved={parts:d.parts&&d.parts.map(p=>p.label+' '+p.events.length),partSel:d.partSel,bpb:d.bpb,first:d.parts&&d.parts.map(p=>p.events[0]&&p.events[0].t)};
    out.afterImport={btn:$('#partBtn').style.display,text:$('#partBtn').textContent,events:G.song.events.length};
    // open from the list -> chooser
    document.querySelectorAll('.overlay.show').forEach(o=>o.classList.remove('show'));
    const ch=partChoices(d);out.choices=ch.map(c=>c.label+' — '+c.sub);
    pickPart(d,()=>openSong(d));out.msgShown=$('#msg').classList.contains('show');out.buttons=[...document.querySelectorAll('#msgBody .partPick')].map(x=>x.dataset.v+(x.classList.contains('primary')?'*':''));
    document.querySelector('#msgBody .partPick[data-v=combo]').click();await new Promise(r=>setTimeout(r,200));
    const bpb=d.bpb,ev=G.song.events;const bars={};for(const e of ev){const k=Math.floor(e.t/bpb+1e-6);(bars[k]=bars[k]||new Set()).add(e.notes&&e.notes.length>=2||e.chord?'chord':'note');}
    out.combo={btn:$('#partBtn').textContent,events:ev.length,bars:Object.entries(bars).map(([k,s])=>k+':'+[...s].join('+')).join(' '),saved:d.partSel};
    // switch to rhythm via the player button
    $('#partBtn').onclick();document.querySelector('#msgBody .partPick[data-v="0"]').click();await new Promise(r=>setTimeout(r,200));
    out.rhythm={btn:$('#partBtn').textContent,events:G.song.events.length,firstT:G.song.events[0].t};
    // a song with one part shows no chooser/button
    openSong({id:'m-x',cat:'mine',title:'X',bpm:90,bpb:4,kind:'chords',cb:4,src:'G C D G',capo:0,strum:''});out.single=$('#partBtn').style.display;
    return out;}""",data)
  print(json.dumps(r,indent=1));print('errors',errs);b.close()
