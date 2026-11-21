"""Fretline's own detector vs Spotify Basic Pitch (ONNX) on real guitar (GuitarSet mic recordings), same questions:
 positive = an annotated note onset; negatives = the neighbouring semitone at that moment, and a pitch still ringing
 mid-note (no new pick). Prints accept rates for: Fretline now, Fretline before v1.126 (no fresh pick needed), Basic Pitch
 alone, and Fretline AND / OR Basic Pitch. Usage: python3 guitarset_compare.py GUITARSET_DIR REPO_DIR [N_FILES]"""
import sys,os,json,glob,random,re,base64,warnings,asyncio,tempfile
import soundfile as sf
warnings.filterwarnings('ignore')
import numpy as np
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
from playwright.async_api import async_playwright
D,REPO=sys.argv[1],sys.argv[2];N=int(sys.argv[3]) if len(sys.argv)>3 else 20
FR=22050/256;rng=random.Random(3)
files=sorted(glob.glob(os.path.join(D,'*_mic.wav')));rng.shuffle(files);files=files[:N]
JS="""async([b64,qs])=>{await ensureAudio();const bin=atob(b64),u=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);
  const ab=await new OfflineAudioContext(1,1,44100).decodeAudioData(u.buffer);const sr=44100;
  const off=new OfflineAudioContext(1,Math.min(ab.length,sr*40),sr);const an=off.createAnalyser();an.fftSize=4096;an.smoothingTimeConstant=0;
  const src=off.createBufferSource();src.buffer=ab;src.connect(an);src.start(0);
  const realA=actx;actx=off;analyser=an;timeBuf=new Float32Array(4096);freqBuf=new Float32Array(2048);
  det.onsetAt=-1e9;det.stableMidi=null;det.hist=[];det.armed=true;det.lastRms=0;det.pitchOnsetAt=-1e9;muteUntil=0;settings.latency=0;settings.headphones=true;settings.fx='off';settings.backing=false;
  const picks=[],pOn=[];let lo=-1e9,lp=-1e9;const res=qs.map(()=>({pick:false,pitchOn:false,sc:0,scPick:0,first:null}));
  const step=1/60,T=Math.min(ab.duration,40);const act=(t)=>qs.map((q,i)=>[i,q]).filter(([i,q])=>t>=q[0]-0.08&&t<=q[0]+0.12);
  for(let t=0.1;t<T-0.1;t+=step){off.suspend(t).then(()=>{const now=t*1000;detectFrame(now);
      if(det.onsetAt!==lo){lo=det.onsetAt;picks.push(lo);} if(det.pitchOnsetAt!==lp){lp=det.pitchOnsetAt;pOn.push([lp,det.pitchOnsetMidi]);}
      for(const [i,q] of act(t)){const r=res[i];const m=q[1];const sc=targetInfo({midi:m},0).score;r.sc=Math.max(r.sc,sc);
        const lastPick=Math.max(...picks.filter(p=>p<=now&&p>=(q[0]-0.08)*1000),-1);if(lastPick>=0){r.pick=true;if(sc>r.scPick)r.scPick=sc;}
        if(pOn.some(([p,mm])=>mm===m&&p>=(q[0]-0.08)*1000&&p<=now))r.pitchOn=true;}
      off.resume();});}
  await off.startRendering();actx=realA;analyser=null;return res;}"""
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=await b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('file://'+REPO+'/index.html');await pg.wait_for_timeout(500)
        rows=[]  # kind, fretline dict, bp onset score
        for wf in files:
            j=json.load(open(wf.replace('_mic.wav','.jams')));notes=[]
            for a in j['annotations']:
                if a['namespace']=='note_midi':
                    for d in a['data']:
                        v=d['value'] if not isinstance(d['value'],dict) else d['value'].get('value');notes.append((d['time'],d['duration'],int(round(v))))
            notes=[n for n in notes if n[0]<38 and 40<=n[2]<=88]
            out,_,_=predict(wf,ICASSP_2022_MODEL_PATH);on=out['onset']
            def bp(t,m):
                a=max(0,int((t-0.08)*FR));bb=min(len(on),int((t+0.12)*FR)+1);return float(on[a:bb,m-21].max()) if bb>a else 0.0
            onsets={}
            for t,d,m in notes:onsets.setdefault(m,[]).append(t)
            qs=[];kinds=[]
            for t,d,m in notes:
                qs.append([t,m]);kinds.append('pos')
                dm=rng.choice((-1,1))
                if 40<=m+dm<=88 and not any(abs(t-x)<0.2 for x in onsets.get(m+dm,[])):qs.append([t,m+dm]);kinds.append('neigh')
                if d>=0.7:
                    tm=t+0.5
                    if not any(abs(tm-x)<0.3 for x in onsets.get(m,[])):qs.append([tm,m]);kinds.append('ring')
            # causal Basic Pitch: only the 2 s that ended 0.25 s after the note (what the app could really have), on a sample of queries
            wav,wsr=sf.read(wf,dtype='float32')
            def causal(t,m):
                E=t+0.25;S=E-2.0;i0=int(S*wsr);i1=int(E*wsr);seg=wav[max(0,i0):i1]
                if i0<0:seg=np.concatenate([np.zeros(-i0,dtype='float32'),seg])
                tmp=tempfile.mktemp(suffix='.wav');sf.write(tmp,seg,wsr);o,_,_=predict(tmp,ICASSP_2022_MODEL_PATH);os.remove(tmp)
                o=o['onset'];a=max(0,int((2.0-0.25-0.08)*FR));bb=min(len(o),int((2.0-0.25+0.12)*FR)+1);return float(o[a:bb,m-21].max())
            r=await pg.evaluate(JS,[base64.b64encode(open(wf,'rb').read()).decode(),qs])
            cnt={'pos':0,'neigh':0,'ring':0}
            for q,k,f in zip(qs,kinds,r):
                cs=None
                if cnt[k]<(25 if k!='ring' else 10) and rng.random()<0.5:cnt[k]+=1;cs=causal(q[0],q[1])
                rows.append((k,f,bp(q[0],q[1]),cs))
            print(os.path.basename(wf),len(qs),'queries',flush=True)
        print('errors',errs[:2]);await b.close()
    TH=0.63
    json.dump([[k,f,s_,c] for k,f,s_,c in rows],open('/tmp/gs_rows.json','w'))
    def fnow(f):return f['pitchOn'] or (f['pick'] and f['scPick']>=TH)
    def fold(f):return f['pitchOn'] or f['sc']>=TH
    for th in (0.4,0.5):
        print('\nBasic Pitch onset threshold',th)
        print('%-34s %8s %10s %9s'%('method','recall','semitone%','ringing%'))
        M={'Fretline now (v1.126)':lambda f,s:fnow(f),'Fretline before (no fresh pick)':lambda f,s:fold(f),'Basic Pitch alone':lambda f,s:s>=th,
           'Fretline now AND Basic Pitch':lambda f,s:fnow(f) and s>=th,'Fretline now OR Basic Pitch':lambda f,s:fnow(f) or s>=th}
        for name,fn in M.items():
            rr={}
            for k in ('pos','neigh','ring'):
                v=[fn(f,s) for kk,f,s,_c in rows if kk==k];rr[k]=100*np.mean(v) if v else float('nan')
            print('%-34s %7.1f%% %9.1f%% %8.1f%%'%(name,rr['pos'],rr['neigh'],rr['ring']))
    print('\ncounts',{k:sum(1 for r in rows if r[0]==k) for k in ('pos','neigh','ring')})
asyncio.run(main())
