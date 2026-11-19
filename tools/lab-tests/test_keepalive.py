# v1.95: the Lab starts the keep-alive notification when a run starts, shows progress, says when it is done.
import json
from playwright.sync_api import sync_playwright
MOCK="""window.__ka=[];window.Capacitor={isNativePlatform:()=>true,isPluginAvailable:n=>n==='KeepAlive',Plugins:{KeepAlive:{
 start:async o=>{__ka.push(['start',o.text])},update:async o=>{__ka.push(['update',o.text])},stop:async()=>{__ka.push(['stop'])},done:async o=>{__ka.push(['done',o.title])}}}};"""
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');errs=[]
  for ok in (True,False):
    pg=b.new_page(service_workers='block');pg.on('pageerror',lambda e:errs.append(str(e)));pg.add_init_script(MOCK)
    pg.goto('http://localhost:8769/lab/stems.html');pg.wait_for_timeout(1200)
    print(pg.evaluate("""async(ok)=>{const o={hint:document.getElementById('bgHint').style.display};
      window.runLab=async()=>{status('Splitting… part 1 of 4');await new Promise(r=>setTimeout(r,3000));status('Splitting… part 4 of 4');if(ok)window.__labDone={used:'native'};};
      await $('go').onclick();o.calls=__ka.map(x=>x.join(':'));return JSON.stringify(o);}""",ok))
  # without the plugin nothing changes
  pg=b.new_page(service_workers='block');pg.goto('http://localhost:8769/lab/stems.html');pg.wait_for_timeout(1200)
  print(pg.evaluate("""async()=>{window.runLab=async()=>{status('x');window.__labDone={};};await $('go').onclick();return JSON.stringify([document.getElementById('bgHint').style.display,$('status').textContent])}"""));print(errs);b.close()
