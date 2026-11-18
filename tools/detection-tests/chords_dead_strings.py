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
    await pg.goto('file://'+sys.argv[1]+'/index.html');await pg.wait_for_timeout(500)
    r=await pg.evaluate("""async()=>{await ensureAudio();await loadSound('rec/acoustic');const sr=44100;
      // [chord, what actually happens]
      const plan=[['G',{}],['C',{dead:4}],['D',{ring:0}],['Em',{}],['Am',{dead:2}],['G',{}],['C',{}],['C',{dead:3}],['D',{}],['G',{}]];
      const gap=1.0,T0=0.3;const off=new OfflineAudioContext(1,Math.round(sr*(T0+plan.length*gap+1)),sr);const an=off.createAnalyser();an.fftSize=4096;an.smoothingTimeConstant=0;
      const ring={};
      plan.forEach(([name,o],i)=>{const sh=chordShape(name);const t=T0+i*gap;let k=0;
        for(let s=0;s<6;s++){let f=sh[s];if(o.ring===s)f=0;if(f<0||o.dead===s){if(ring[s]){ring[s].stop(t);delete ring[s];}continue;}
          const m=OPEN[s]+f;const key=Object.keys(sampler.buffers).map(Number).reduce((a,b)=>Math.abs(b-m)<Math.abs(a-m)?b:a);const src=off.createBufferSource();src.buffer=sampler.buffers[key];src.playbackRate.value=Math.pow(2,(m-key)/12);
          const g=off.createGain();g.gain.value=0.3;src.connect(g);g.connect(an);const ts=t+(k++)*0.012;if(ring[s])ring[s].stop(ts);src.start(ts);ring[s]=src;}});
      const realA=actx;actx=off;analyser=an;timeBuf=new Float32Array(4096);freqBuf=new Float32Array(2048);
      det.onsetAt=-1e9;det.stableMidi=null;det.hist=[];det.armed=true;det.lastRms=0;muteUntil=0;settings.latency=0;settings.deadStrings=true;settings.fx='off';settings.backing=false;
      const evs=plan.map(([name],i)=>strumEvent(name,i,gap,'D'));evs.forEach(e=>e.notes=[]);
      G.song={bpm:60,bpb:4,events:evs,length:plan.length};G.speed=1;G.mode='play';G.state=new Uint8Array(evs.length);G.scan=0;G.playing=true;G.listen=false;G.hits=0;G.misses=0;G.streak=0;G.pops=[];
      G.lastHitAt=-1;G.usedOnset=-1;G.ignoreOnsetUntil=0;G.cc=null;G.ccHist={};G.deadStats=null;G.band=null;
      const out=plan.map(()=>({pops:[],fb:''}));let lastPops=0,lastFb=null;const step=1/60;
      for(let t=0.2;t<T0+plan.length*gap+0.6;t+=step){off.suspend(t).then(()=>{const now=t*1000;detectFrame(now);G.clock=(t-T0)-step;update(step,now);
          const idx=Math.max(0,Math.min(plan.length-1,Math.floor((t-T0+0.05)/gap)));
          while(G.pops.length>lastPops){out[idx].pops.push(G.pops[lastPops].text);lastPops++;}if(G.pops.length<lastPops)lastPops=G.pops.length;
          if(G.strFb&&G.strFb!==lastFb){lastFb=G.strFb;out[idx].fb=G.strFb.res.map(x=>x.st==='ok'?'✓':x.st==='dead'?'✕':x.st==='ring'?'!':'·').join('');}
          off.resume();});}
      await off.startRendering();actx=realA;analyser=null;
      return plan.map(([n,o],i)=>n+(o.dead!=null?' (dead '+SNAME[o.dead]+')':'')+(o.ring!=null?' ('+SNAME[o.ring]+' rings)':'')+' → strings E-A-D-G-B-e: '+(out[i].fb||'-')+'  '+out[i].pops.filter(x=>!/Perfect|Good|streak/.test(x)).join(', ')+(G.state[i]===1?'  [hit]':'  [not hit]')).join('\\n');}""")
    print(r);print(errs);await b.close()
asyncio.run(main())
