"""Replay a recorded lesson (the .wav from 'Share lesson audio' + its report) through the app's own detector.
Usage: python3 replay_run.py AUDIO.wav REPORT.txt OUT_PREFIX [REPO_URL]   (needs a static server on REPO_URL, default http://localhost:8769/)
1. Basic Pitch finds where each step's target note really starts in the audio; a straight line through the confident matches
   gives the recording's clock drift (the phone's recording axis runs ~0.4% off the step clock), and the audio is time-warped back to wall time.
2. The lesson is rebuilt from the report title/seed (generated lessons only: 'Arpeggios in D major · 2:00 #158181'), the page's getUserMedia returns the warped audio
   (started the moment the app starts its recording), the lesson is played in real time with the settings from the report header.
3. Prints how often this replay's HIT/MISS agrees with the real run and writes OUT_PREFIX.txt (the replay's own report)."""
import sys,re,json,base64,time,warnings
warnings.filterwarnings('ignore')
import numpy as np,soundfile as sf
from playwright.sync_api import sync_playwright
wav,rep,outp=sys.argv[1:4];URL=sys.argv[4] if len(sys.argv)>4 else 'http://localhost:8769/'
FR=22050/256;names=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
def midi(n):
    m=re.match(r'([A-G]#?)(\d)',n);return 12*(int(m.group(2))+1)+names.index(m.group(1))
L=open(rep).read().split('\n');head=L[0]
S=[]
for l in L:
    m=re.match(r'#(\d+) (\S+) \S+ · (HIT|MISS).*?@([\d.]+)s',l)
    if m and re.match(r'[A-G]#?\d$',m.group(2)):S.append((int(m.group(1)),midi(m.group(2)),m.group(3),float(m.group(4))))
    elif m:S.append((int(m.group(1)),None,m.group(3),float(m.group(4))))
real={int(re.match(r'#(\d+)',l).group(1)):('HIT' in l.split('·')[1]) for l in L if re.match(r'#\d+ ',l) and ('HIT' in l.split('·')[1] or 'MISS' in l.split('·')[1])}
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
out,_,_=predict(wav,ICASSP_2022_MODEL_PATH);on=out['onset']
pts=[]
for i,m,st,t in S:
    if m is None:continue
    a=max(0,int((t-0.7)*FR));b=min(len(on),int((t+0.7)*FR)+1);seg=on[a:b,m-21];f=seg.argmax()
    if seg[f]>=0.8 and abs((a+f)/FR-t)<0.65:pts.append((t,(a+f)/FR-t))
x=np.array([p[0] for p in pts]);y=np.array([p[1] for p in pts])
sl=[(y[j]-y[i])/(x[j]-x[i]) for i in range(len(x)) for j in range(i+1,len(x)) if x[j]-x[i]>5];s=float(np.median(sl));ic=float(np.median(y-s*x))
print('drift %.0f ms/min, offset %.0f ms, %d matches'%(s*60000,ic*1000,len(pts)))
d,sr=sf.read(wav,dtype='float32');T=len(d)/sr;n=int(T*sr);tw=np.arange(n)/sr
PAD=float(__import__('os').environ.get('PAD','0.243'))  # the phone's mic delay is already inside the recording; the injected stream has none, so delay the audio by what the app subtracts (setting latency) plus the start lag
warped=np.interp((tw-PAD)*(1+s)+ic,np.arange(len(d))/sr,d,left=0,right=0).astype('float32')
sf.write('/tmp/replay_warped.wav',warped,sr)
b64=base64.b64encode(open('/tmp/replay_warped.wav','rb').read()).decode()
title=re.search(r'report · (.*?) · \d+ BPM',head).group(1);bpm=int(re.search(r'· (\d+) BPM',head).group(1))
seed=int(re.search(r'#(\d+)$',title).group(1));kind=title.split(' in ')[0];key=title.split(' in ')[1].split(' · ')[0].split(' ')[0]
lat=int(re.search(r'latency (\d+)',head).group(1));sd=re.search(r'sound delay (\w+)',head).group(1);sens=int(re.search(r'sensitivity (\d+)',head).group(1))
print(title,bpm,'latency',lat,'sound delay',sd,'sens',sens)
INIT="""window.__wavB64='%s';window.__started=false;
navigator.mediaDevices.getUserMedia=async function(c){
  while(typeof actx==='undefined'||!actx)await new Promise(r=>setTimeout(r,20));
  const ab=await actx.decodeAudioData(Uint8Array.from(atob(window.__wavB64),c=>c.charCodeAt(0)).buffer);
  const dest=actx.createMediaStreamDestination();window.__src=actx.createBufferSource();window.__src.buffer=ab;window.__src.connect(dest);
  window.__startSrc=()=>{if(window.__started)return;window.__started=true;window.__src.start();};
  return dest.stream;};"""%b64
with sync_playwright() as p:
    br=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--autoplay-policy=no-user-gesture-required'])
    pg=br.new_context(service_workers='block',viewport={'width':900,'height':460}).new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.add_init_script(INIT)
    pg.goto(URL+'index.html');pg.wait_for_timeout(1200)
    kmap={'C':0,'C#':1,'D':2,'D#':3,'E':4,'F':5,'F#':6,'G':7,'G#':8,'A':9,'A#':10,'B':11}
    pg.evaluate("""([seed,bpm,key,lat,sens,sd])=>{settings.latency=lat;settings.sens=sens;settings.headphones=true;settings.backing=false;settings.fx='off';settings.bpShadow=false;settings.soundDelay=sd==='auto'?-10:+sd;
      const d=makeGen({styles:['arp'],key,scale:'major',diff:1,bars:40,bpm,seed});G.lastGen=d;openSong(d);
      window.__bpRecStart0=bpRecStart;bpRecStart=function(){window.__startSrc&&window.__startSrc();return window.__bpRecStart0.apply(this,arguments);};settings.bpShadow=true;}""",[seed,bpm,kmap[key],lat,sens,sd])
    pg.wait_for_timeout(800);pg.evaluate("document.querySelector('#intro').classList.remove('show')")
    pg.evaluate("document.querySelector('#btnPlay').onclick()")
    t0=time.time()
    while time.time()-t0<200:
        if pg.evaluate("G.finished"):break
        pg.wait_for_timeout(1000)
        if int(time.time()-t0)%30==0:print('t',int(time.time()-t0),pg.evaluate('[G.playing,G.finished,Math.round(G.clock*10)/10,bpRec.on]'),flush=True)
    rp=pg.evaluate("diagReport()");open(outp+'.txt','w').write(rp);print('errors',errs[:3]);br.close()
mine={int(re.match(r'#(\d+)',l).group(1)):('HIT' in l.split('·')[1]) for l in rp.split('\n') if re.match(r'#\d+ ',l) and ('HIT' in l.split('·')[1] or 'MISS' in l.split('·')[1])}
ids=sorted(set(real)&set(mine));agree=sum(real[i]==mine[i] for i in ids)
print('steps',len(ids),'agree',agree,'real hits',sum(real[i] for i in ids),'replay hits',sum(mine[i] for i in ids))
print('real HIT -> replay MISS:',[i for i in ids if real[i] and not mine[i]]);print('real MISS -> replay HIT:',[i for i in ids if not real[i] and mine[i]])
