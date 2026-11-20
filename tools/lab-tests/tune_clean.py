# v1.116: tunes cleanNotes' cut-offs (the P object in lab/stems.html) against two known-answer recordings:
# SYNTH (the Midland tab played by a synth, make_score_audio.py) and TYSK (a real Demucs guitar stem, verified tab as truth).
# Basic Pitch runs once per recording; then each setting is scored. Coordinate search, objective 0.6*F1(real)+0.4*F1(synth).
# python3 tune_clean.py [SECS]
import json,sys,numpy as np
from playwright.sync_api import sync_playwright
SECS=float(sys.argv[1]) if len(sys.argv)>1 else 60
def score(est,tr,tol=0.05):
    est=sorted(est);used=set();tp=0
    for t,d,m in tr:
        for j,(et,ed,em) in enumerate(est):
            if j not in used and abs(et-t)<=tol and em==m:used.add(j);tp+=1;break
    p=tp/max(1,len(est));r=tp/max(1,len(tr));return (2*p*r/max(1e-9,p+r),p,r,len(est))
sg=json.load(open('/tmp/tysk_full_song.json'))
DS={'tysk':('tysk_full_gtr.f32',[(sg['recEvT'][i],0.3,n['midi']) for i,e in enumerate(sg['events']) for n in e['notes']]),
    'synth':('score_gtr.f32',[tuple(x) for x in json.load(open('/tmp/score_truth.json'))])}
DS={k:(a,[x for x in tr if x[0]<SECS-1]) for k,(a,tr) in DS.items()}
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page(service_workers='block');errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('http://localhost:8769/lab/stems.html');pg.wait_for_timeout(800)
    for k,(aud,tr) in DS.items():
        pg.evaluate("""async([k,aud,secs])=>{const g=new Float32Array(await (await fetch('http://localhost:8771/'+aud)).arrayBuffer());const n=Math.min(g.length,Math.round(secs*44100));const gg=g.slice(0,n);
          const g22=await toRate([gg,gg],22050);window['G_'+k]={g22,raw:await transcribe(g22)};}""",[k,aud,SECS])
        print('transcribed',k,flush=True)
    def run(ovr):
        out={}
        for k,(aud,tr) in DS.items():
            est=pg.evaluate("([k,o])=>{window.CN_OVR=o;const d=window['G_'+k];return cleanNotes(d.raw,d.g22).map(x=>[x.t,x.d,x.midi])}",[k,ovr])
            out[k]=score(est,tr)
        return out,0.6*out['tysk'][0]+0.4*out['synth'][0]
    base,obj=run({});print('base',{k:[round(x,3) for x in v] for k,v in base.items()},round(obj,4),flush=True)
    grid={'minStr':[1,1.5,2,3,4,6],'minDur':[0.03,0.06,0.1,0.15,0.2],'loudAmp':[0.3,0.5,0.7],'loudStr':[2,4,6],'hiMidi':[76,79,84,90],'hiAmp':[0.3,0.5,0.7],'pickWin':[0.03,0.04,0.06,0.09],'maxPerPick':[1,2,3,4,6],'ampRatio':[0.4,0.5,0.6,0.7,0.8,0.9]}
    cur={};best=obj
    for rnd in range(2):
        for key,vals in grid.items():
            for v in vals:
                o={**cur,key:v};res,ob=run(o)
                if ob>best+1e-4:best=ob;cur=o;print('  better',key,v,{k:[round(x,3) for x in vv] for k,vv in res.items()},round(ob,4),flush=True)
    res,ob=run(cur);print('FINAL',json.dumps(cur),{k:[round(x,3) for x in vv] for k,vv in res.items()},round(ob,4));print(errs);b.close()
