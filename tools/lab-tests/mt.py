import sys
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page(viewport={'width':412,'height':900});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/lab/stems.html?ortbase=http://localhost:8771/&modelurl=http://localhost:8771/dummy.onnx');pg.wait_for_timeout(4000)
  print('isolated:',pg.evaluate('self.crossOriginIsolated'),'controlled:',pg.evaluate('!!navigator.serviceWorker.controller'))
  pg.set_input_files('#file',sys.argv[1]);pg.select_option('#secs','30');pg.select_option('#be','wasm');pg.click('#go');pg.wait_for_function('window.__labDone',timeout=600000)
  print(pg.evaluate('window.__labDone'));t=pg.text_content('#log');print('\n'.join(l for l in t.split('\n') if 'thread' in l or 'done' in l or 'ERROR' in l))
  print('errors',errs);b.close()
