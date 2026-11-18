import asyncio,sys,re,json
from playwright.async_api import async_playwright
import os
S=os.environ.get('SAMPLES','/tmp/samp/package/')
site,string,gain=sys.argv[1],int(sys.argv[2]),float(sys.argv[3])
JS="""async([string,gain])=>{await ensureAudio();await loadSound('rec/acoustic');const sr=44100;
  // each target note (this string, frets 0-17) comes after a note on the neighbouring string, which keeps ringing
  const adj=string<5?string+1:string-1;const seq=[];
  for(let f=0;f<=17;f++){const fa=Math.max(0,Math.min(17,f+(f%3)-1));seq.push([OPEN[adj]+fa,adj,false]);seq.push([OPEN[string]+f+(window.__wrong||0),string,true]);}
  const gap=0.6,T0=4.3;const off=new OfflineAudioContext(1,Math.round(sr*(T0+seq.length*gap+1)),sr);const an=off.createAnalyser();an.fftSize=4096;an.smoothingTimeConstant=0;
  {const nb=off.createBuffer(1,off.length,sr);const nd=nb.getChannelData(0);for(let i=0;i<nd.length;i++)nd[i]=(Math.random()-0.5)*0.0006;const ns=off.createBufferSource();ns.buffer=nb;ns.connect(an);ns.start(0);}
  const keys=Object.keys(sampler.buffers).map(Number);const ring={};
  seq.forEach(([m,st],i)=>{const t=T0+i*gap;const key=keys.reduce((a,b)=>Math.abs(b-m)<Math.abs(a-m)?b:a);const src=off.createBufferSource();src.buffer=sampler.buffers[key];src.playbackRate.value=Math.pow(2,(m-key)/12);
    const g=off.createGain();g.gain.value=gain;src.connect(g);g.connect(an);if(ring[st])ring[st].stop(t);src.start(t);ring[st]=src;});
  const realA=actx;actx=off;master=null;analyser=an;timeBuf=new Float32Array(4096);freqBuf=new Float32Array(2048);
  for(const k of ['hist','nfL','hfHist'])det[k]=[];det.onsetAt=-1e9;det.stableMidi=null;det.armed=true;det.hfArmed=true;det.lastRms=0;det.noise=0;det.pitchOnsetAt=null;muteUntil=0;
  settings.latency=0;settings.headphones=true;settings.fx='miss';settings.backing=false;settings.anyOctave=true;settings.sens=5;
  const evs=seq.map(([m,st,tg],i)=>{const mm=tg?m-(window.__wrong||0):m;return {t:i,d:1,notes:[{s:st,f:mm-OPEN[st],midi:mm}]};});
  G.song={bpm:60/gap,bpb:4,events:evs,length:evs.length};G.speed=1;G.mode='play';G.state=new Uint8Array(evs.length);G.scan=0;G.playing=true;G.listen=false;G.hits=0;G.misses=0;G.streak=0;G.pops=[];
  G.lastHitAt=-1;G.lastHitKey=null;G.usedOnset=-1;G.ignoreOnsetUntil=0;G.wrongOnset=-1;G.wrongAt=0;G.cc=null;G.band=null;G.diag={};G.offs=[];G.capo=0;
  const credit=evs.map(()=>null),wrong=evs.map(()=>0);let lastPops=0;const step=1/60;
  for(let t=0.2;t<T0+seq.length*gap+0.6;t+=step){off.suspend(t).then(()=>{const now=t*1000;detectFrame(now);G.clock=(t-T0)/gap-step/gap;update(step,now);
      evs.forEach((e,i)=>{if(G.state[i]===1&&credit[i]===null)credit[i]=(G.clock-e.t)*gap;});
      // count "Wrong note/string" pops against the note being waited for
      const cur=G.scan<evs.length?G.scan:evs.length-1;
      while(G.pops.length>lastPops){const p=G.pops[lastPops++];if(/Wrong/.test(p.text))wrong[cur]++;}if(G.pops.length<lastPops)lastPops=G.pops.length;
      off.resume();});}
  await off.startRendering();actx=realA;master=null;analyser=null;
  const tg=evs.map((e,i)=>i).filter(i=>seq[i][2]);
  return {string:STRING_LABELS[string],gain,cutoff:+(gate()*1000).toFixed(1),hits:tg.filter(i=>G.state[i]===1).length+'/'+tg.length,
    perFret:tg.map(i=>G.state[i]===1?(credit[i]<-0.02?'E':'✓'):'✗').join(''),
    early:tg.filter(i=>credit[i]!==null&&credit[i]<-0.02).map(i=>evs[i].notes[0].f),
    wrongOnTargets:tg.filter(i=>wrong[i]).map(i=>evs[i].notes[0].f),
    misses:tg.filter(i=>G.state[i]!==1).map(i=>{const d=G.diag[i];return 'fret '+evs[i].notes[0].f+' ('+midiToName(evs[i].notes[0].midi)+'): heard '+(d&&d.heard.length?d.heard.map(midiToName).join('>'):'nothing')+' picks '+(d?d.picks+'/'+(d.pp||0):'-')+' note '+(d?d.ts.toFixed(2):'-')+' level '+(d?(d.lv*1000).toFixed(1)+'/'+(d.gt*1000).toFixed(1):'-');}),
    otherHits:evs.map((e,i)=>i).filter(i=>!seq[i][2]&&G.state[i]===1).length+'/'+evs.length/2,
    rep:tg.map(i=>{const d=G.diag[i];return 'f'+evs[i].notes[0].f+' '+(G.state[i]===1?'COUNTED':'ok')+' heard '+(d&&d.heard.length?d.heard.map(midiToName).join('>'):'-')+' picks '+(d?d.picks+'/'+(d.pp||0):'-')+' note '+(d?d.ts.toFixed(2):'-')+(d&&d.notes.length?' '+d.notes.join(','):'')+' wrongPops '+wrong[i];}),
    delayMedian:Math.round(1000*tg.map(i=>credit[i]).filter(x=>x!==null).sort((a,b)=>a-b)[Math.floor(tg.length/2)]||0)};
}"""
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/usr/bin/google-chrome');errs=[]
    pg=await b.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
    async def route(r):await r.fulfill(path=S+r.request.url.split('/')[-1],content_type='audio/mpeg')
    await pg.route(re.compile(r'.*(jsdelivr|unpkg).*tonejs.*'),route)
    await pg.add_init_script('window.__wrong=-1');await pg.goto('file://'+site+'/index.html');await pg.wait_for_timeout(500)
    r=await pg.evaluate(JS,[string,gain]);print(json.dumps(r,ensure_ascii=False));
    if errs:print(errs)
    await b.close()
asyncio.run(main())
