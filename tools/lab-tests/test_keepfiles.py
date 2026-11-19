# v1.104: files picked in the Lab survive a page reload (what Android does while the file picker is open).
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');ctx=b.new_context(service_workers='block');pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/lab/stems.html');pg.wait_for_timeout(800)
  pg.set_input_files('#file','/tmp/midland_gtr.f32');pg.set_input_files('#sheetFile','/tmp/midland_tab.mid');pg.wait_for_timeout(1200);pg.set_input_files('#sheet2File','/tmp/midland_chords.mid');pg.wait_for_timeout(1200)
  pg.reload();pg.wait_for_timeout(2500)
  print('after reload:',pg.evaluate("[$('file').files[0]&&$('file').files[0].name,$('go').disabled,SHEETFILE&&SHEETFILE.name,SHEETFILE2&&SHEETFILE2.name,$('status').textContent]"))
  pg.evaluate("clearKept()");pg.reload();pg.wait_for_timeout(1500)
  print('after clear+reload:',pg.evaluate("[$('file').files.length,!!SHEETFILE]"),errs);b.close()
