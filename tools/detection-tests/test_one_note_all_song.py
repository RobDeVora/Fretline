import asyncio,sys,re,json
from playwright.async_api import async_playwright
import os
S=os.environ.get('SAMPLES','/tmp/samp/package/')
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/usr/bin/google-chrome');errs=[]
    pg=await b.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
    async def route(r):await r.fulfill(path=S+r.request.url.split('/')[-1],content_type='audio/mpeg')
    await pg.route(re.compile(r'.*(jsdelivr|unpkg).*tonejs.*'),route)
    await pg.add_init_script('window.__play='+(__import__('os').environ.get('PLAY') or 'null')+';window.__anyOct='+('true' if __import__('os').environ.get('ANYOCT') else 'false')+';');await pg.goto('file://'+sys.argv[1]+'/index.html');await pg.wait_for_timeout(500)
    r=await pg.evaluate("""async()=>{await ensureAudio();await loadSound('rec/acoustic');const sr=44100;
      // [chord, what actually happens]
      const seq=[[55,1],[60,2],[64,3],[67,3],[69,4],[67,3],[69,4],[74,5],[72,4],[74,5],[76,5],[72,4],[69,4],[62,2],[69,4],[69,4],[69,4],[62,2],[57,1],[52,0],[50,0],[50,0],[57,1],[60,2],[67,3],[74,5],[67,3],[69,4],[64,3],[67,3],[64,3],[72,4],[76,5],[74,5]];const plan=seq;
      const gap=window.__gap||0.5,T0=0.3;const off=new OfflineAudioContext(1,Math.round(sr*(T0+plan.length*gap+1)),sr);const an=off.createAnalyser();an.fftSize=4096;an.smoothingTimeConstant=0;
      const ring={};
      seq.forEach(([m0,st],i)=>{const m=window.__play||m0;const t=T0+i*gap;const key=Object.keys(sampler.buffers).map(Number).reduce((a,b)=>Math.abs(b-m)<Math.abs(a-m)?b:a);const src=off.createBufferSource();src.buffer=sampler.buffers[key];src.playbackRate.value=Math.pow(2,(m-key)/12);const g=off.createGain();g.gain.value=window.__gain||0.5;src.connect(g);g.connect(an);if(ring[st])ring[st].stop(t);src.start(t);ring[st]=src;});
      {const nb=off.createBuffer(1,off.length,sr);const nd=nb.getChannelData(0);for(let i=0;i<nd.length;i++)nd[i]=(Math.random()-0.5)*(window.__noise||0.0015);const ns=off.createBufferSource();ns.buffer=nb;ns.connect(an);ns.start(0);}
      const realA=actx;actx=off;analyser=an;timeBuf=new Float32Array(4096);freqBuf=new Float32Array(2048);
      det.onsetAt=-1e9;det.stableMidi=null;det.hist=[];det.armed=true;det.lastRms=0;muteUntil=0;settings.latency=0;settings.anyOctave=!!window.__anyOct;settings.headphones=true;settings.deadStrings=true;settings.fx='off';settings.backing=false;
      const evs=seq.map(([m,st],i)=>({t:i,d:1,notes:[{s:st,f:m-OPEN[st],midi:m}]}));
      G.song={bpm:60/gap,bpb:4,events:evs,length:plan.length};G.speed=1;G.mode='play';G.state=new Uint8Array(evs.length);G.scan=0;G.playing=true;G.listen=false;G.hits=0;G.misses=0;G.streak=0;G.pops=[];
      G.lastHitAt=-1;G.usedOnset=-1;G.ignoreOnsetUntil=0;G.cc=null;G.ccHist={};G.deadStats=null;G.band=null;
      const out=plan.map(()=>({pops:[],fb:''}));let lastPops=0,lastFb=null;const step=1/60;
      for(let t=0.2;t<T0+plan.length*gap+0.6;t+=step){off.suspend(t).then(()=>{const now=t*1000;detectFrame(now);G.clock=(t-T0)/gap-step/gap;update(step,now);
          const idx=0;
          while(G.pops.length>lastPops){out[idx].pops.push(G.pops[lastPops].text);lastPops++;}if(G.pops.length<lastPops)lastPops=G.pops.length;
          if(G.strFb&&G.strFb!==lastFb){lastFb=G.strFb;out[idx].fb=G.strFb.res.map(x=>x.st==='ok'?'✓':x.st==='dead'?'✕':x.st==='ring'?'!':'·').join('');}
          off.resume();});}
      await off.startRendering();actx=realA;analyser=null;
      const o=(G.offs||[]).slice().sort((a,b)=>a-b);G.def={title:'sim'};return diagReport().split(String.fromCharCode(10)).join(' ;; ')+' || hits '+G.hits+'/'+evs.length+' ['+evs.map((e,i)=>G.state[i]===1?'✓':'✗').join('')+'] · timing readout (median) '+Math.round(o[Math.floor(o.length/2)])+' ms · all: '+o.map(Math.round).join(' ');}""")
    print(r);print(errs);await b.close()
asyncio.run(main())
