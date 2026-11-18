import base64
from playwright.sync_api import sync_playwright
data=base64.b64encode(open(__import__('sys').argv[1],'rb').read()).decode()
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream']);pg=b.new_page(viewport={'width':390,'height':844},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(600)
  r=pg.evaluate("""async(d)=>{const bytes=Uint8Array.from(atob(d),c=>c.charCodeAt(0));const f=new File([bytes],'Marlboro_Man_Test');
    await loadImportFile(f);const out={file:$('#impFileName').textContent,bpm:$('#impBpm').value,bpb:impFile&&impFile.bpb,vocal:impFile&&impFile.vocal&&impFile.vocal.label,parts:[]};
    const sel=$('#impPart');for(let i=0;i<sel.options.length;i++){sel.value=i;sel.onchange();await new Promise(r=>setTimeout(r,50));
      const modes=[...document.querySelectorAll('#impMode option, [name=impMode]')].map(o=>o.value||o.textContent);
      out.parts.push({part:sel.options[i].textContent,preview:$('#impPreview').textContent.slice(0,260),modes});}
    return out;}""",data)
  import json;print(json.dumps(r,indent=1));print(errs)
  b.close()
