# Lab with a stand-in for the APK's NativeSeparator plugin (window.Capacitor.Plugins.NativeSeparator).
# The fake returns guitar = 0.3 × input and band = 0.7 × input as base64 float32, like the real plugin, and checks
# the page picks "Phone app, all cores" by default, downloads/loads through the plugin, never loads the web runtime,
# and blends the parts exactly. Optional arg: "fail" makes load() reject, to check the fallback to the web runtime.
import sys
from playwright.sync_api import sync_playwright
FAKE = """
(()=>{const mode=%r;const L={};let loaded=false,have=0;window.__nsCalls=[];
const b2f=b=>{const s=atob(b),u=new Uint8Array(s.length);for(let i=0;i<s.length;i++)u[i]=s.charCodeAt(i);return new Float32Array(u.buffer);};
const f2b=a=>{const u=new Uint8Array(a.buffer);let s='';for(let i=0;i<u.length;i+=0x8000)s+=String.fromCharCode.apply(null,u.subarray(i,i+0x8000));return btoa(s);};
const NS={
 status:async()=>{__nsCalls.push('status');return {available:true,cores:8,modelBytes:have,loaded,threads:0};},
 addListener:async(ev,fn)=>{L[ev]=fn;return {remove(){delete L[ev];}};},
 prepareModel:async o=>{__nsCalls.push('prepare:'+o.url+':'+o.expectBytes);for(let g=0;g<=o.expectBytes;g+=60e6){L.progress&&L.progress({phase:'download',got:g,total:o.expectBytes});await new Promise(r=>setTimeout(r,20));}have=o.expectBytes;return {path:'/data/models/htdemucs_6s.onnx',bytes:have,downloaded:true};},
 load:async o=>{__nsCalls.push('load');if(mode==='fail')throw new Error('fake load failure');loaded=true;return {ms:1234,threads:7,input:'mix',outputs:'sources'};},
 run:async o=>{__nsCalls.push('run');const m=b2f(o.mix);if(m.length!==2*o.n)throw new Error('bad length '+m.length);const g=new Float32Array(m.length),b=new Float32Array(m.length);for(let i=0;i<m.length;i++){g[i]=0.3*m[i];b[i]=0.7*m[i];}return {guitar:f2b(g),band:f2b(b),ms:500};}};
window.Capacitor={isNativePlatform:()=>true,isPluginAvailable:n=>n==='NativeSeparator',Plugins:{NativeSeparator:NS}};})();
"""
mode = sys.argv[2] if len(sys.argv) > 2 else 'ok'
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome')
    ctx = b.new_context(viewport={'width': 412, 'height': 900}, service_workers='block')
    ctx.add_init_script(FAKE % mode)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://localhost:8769/lab/stems.html?ortbase=http://localhost:8771/&modelurl=http://localhost:8771/dummy.onnx'); pg.wait_for_timeout(1500)
    print('default run-on:', pg.eval_on_selector('#be', 'e=>e.value'))
    pg.set_input_files('#file', sys.argv[1]); pg.select_option('#secs', '30'); pg.uncheck('#mk'); pg.click('#go')
    pg.wait_for_function('window.__labDone', timeout=600000)
    print(pg.evaluate('window.__labDone'))
    calls = pg.evaluate('window.__nsCalls'); print('plugin calls:', calls[:4], '…', len([c for c in calls if c == 'run']), 'runs')
    print('web runtime loaded:', pg.evaluate('!!window.ort'))
    err = pg.evaluate("""()=>{const B=window.__labBufs;if(!B)return null;const N=B.L.length;let mean=0;for(let i=0;i<N;i++)mean+=(B.L[i]+B.Rc[i])/2;mean/=N;
      let e1=0,e2=0;for(let i=0;i<N;i++){e1=Math.max(e1,Math.abs(B.gL[i]-(0.3*(B.L[i]-mean)+mean)),Math.abs(B.gR[i]-(0.3*(B.Rc[i]-mean)+mean)));
        e2=Math.max(e2,Math.abs(B.rL[i]-(0.7*(B.L[i]-mean)+5*mean)));}return [e1,e2];}""")
    print('max error guitar / band:', err)
    t = pg.text_content('#log'); print('\n'.join(l for l in t.split('\n') if l.startswith(('native', 'done', 'ERROR', 'part 1/', 'runtime', 'model: native'))))
    print('errors', errs); b.close()
