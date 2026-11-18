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
      async function strum(midis,at){const off=new OfflineAudioContext(1,Math.round(sr*0.8),sr);midis.forEach((m,i)=>{const key=Object.keys(sampler.buffers).map(Number).reduce((a,b)=>Math.abs(b-m)<Math.abs(a-m)?b:a);const src=off.createBufferSource();src.buffer=sampler.buffers[key];src.playbackRate.value=Math.pow(2,(m-key)/12);const g=off.createGain();g.gain.value=0.35;src.connect(g);g.connect(off.destination);src.start(0.05+i*0.012);});
        const d=(await off.startRendering()).getChannelData(0);const w=d.slice(Math.round(sr*at),Math.round(sr*at)+4096);for(let i=0;i<w.length;i++)w[i]+=(Math.random()-0.5)*0.002;return w;}
      const res=[];
      for(const name of ['G','C','D','Em','Am','E','A','Dm','F']){const sh=chordShape(name);const strs=[];sh.forEach((f,s)=>{if(f>=0)strs.push(s);});
        const full=strs.map(s=>OPEN[s]+sh[s]);
        // all strings ringing
        const w=await strum(full,0.2);const a=chordStrings(sh,0,w,sr);
        const row={name,shape:sh.map(f=>f<0?'x':f).join(''),all:a.map(x=>x.score==null?'?':x.score.toFixed(2)).join(' ')};
        // each played string dead in turn: does the analysis catch it, and keep the others?
        let caught=0,falseDead=0,judged=0;
        for(const ds of strs){const w2=await strum(strs.filter(s=>s!==ds).map(s=>OPEN[s]+sh[s]),0.2);const b2=chordStrings(sh,0,w2,sr);
          const me=b2.find(x=>x.s===ds);if(me.score!=null){judged++;if(me.score<0.5)caught++;}
          falseDead+=b2.filter(x=>x.s!==ds&&!x.muted&&x.score!=null&&x.score<0.5).length;}
        row.deadCaught=caught+'/'+judged+' (of '+strs.length+')';row.falseDeadOthers=falseDead;
        // muted strings left ringing open
        const mut=sh.map((f,s)=>f<0?s:-1).filter(s=>s>=0);let mc=0,mj=0;
        for(const ms of mut){const w3=await strum([OPEN[ms],...full],0.2);const c3=chordStrings(sh,0,w3,sr).find(x=>x.s===ms);if(c3.score!=null){mj++;if(c3.score>=0.65)mc++;}}
        const mutedClean=a.filter(x=>x.muted&&x.score!=null&&x.score>=0.65).length;
        row.mutedRinging=mc+'/'+mj;row.mutedFalseAlarm=mutedClean;res.push(row);}
      return res;}""")
    for x in r:print(json.dumps(x))
    print(errs);await b.close()
asyncio.run(main())
