import sys, subprocess, time
from playwright.sync_api import sync_playwright
repo=sys.argv[1]
srv=subprocess.Popen([sys.executable,'-m','http.server','8765','-d',repo],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1)
FAKE="""
window.__mode = %s;
window.Capacitor={isNativePlatform:()=>true,Plugins:{NativeMic:{
  _l:null,_t:null,
  addListener(ev,fn){this._l=fn;return Promise.resolve({remove:()=>{this._l=null;}});},
  start(o){ if(window.__mode==='fail') return Promise.reject(new Error('busy'));
    const sr=44100,f=220;let ph=0,n=0;
    this._t=setInterval(()=>{ // bursty: 3 chunks of 10 ms every 30 ms
      for(let c=0;c<3;c++){const x=new Float32Array(441);for(let i=0;i<441;i++){x[i]=0.3*Math.sin(ph)+0.1*Math.sin(2*ph);ph+=2*Math.PI*f/sr;}
        const u=new Uint8Array(x.buffer);let s='';for(const b of u)s+=String.fromCharCode(b);this._l&&this._l({d:btoa(s)});}},30);
    return Promise.resolve({sampleRate:sr,source:'unprocessed',encoding:'float',device:'built-in mic (test)',builtin:true});},
  stop(){clearInterval(this._t);return Promise.resolve();}
}}};
"""
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--autoplay-policy=no-user-gesture-required','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])
  for mode in ["'ok'","'fail'"]:
    pg=b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.add_init_script(FAKE%mode)
    pg.goto('http://localhost:8765/index.html');pg.wait_for_timeout(1500)
    r=pg.evaluate("""async()=>{const ok=await enableMic();await new Promise(r=>setTimeout(r,1500));
      analyser.getFloatTimeDomainData(timeBuf);let rms=0;for(const v of timeBuf)rms+=v*v;rms=Math.sqrt(rms/timeBuf.length);
      const f=yin(timeBuf.subarray(timeBuf.length-2048),actx.sampleRate);
      await fillMicList();const opts=[...document.querySelectorAll('#sMic option')].map(o=>o.textContent);
      return {ok,rate:actx.sampleRate,rms:+rms.toFixed(3),pitch:f>0?+(actx.sampleRate/f).toFixed(1):f,info:micInfo(),opts,hint:document.querySelector('#sMicHint').textContent.slice(0,60)};}""")
    # restart path (switch setting and back)
    r2=pg.evaluate("""async()=>{settings.micId='web';await restartMic();const a=micInfo();settings.micId='';await restartMic();await new Promise(r=>setTimeout(r,500));return [a,micInfo()];}""")
    print(mode,r,r2,'errors:',errs)
    pg.close()
  b.close()
srv.terminate()
