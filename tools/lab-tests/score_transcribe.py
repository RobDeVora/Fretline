# v1.116: how good is the Lab's note-finding? Scores Basic Pitch + cleanNotes against known notes.
# Needs /tmp/score_gtr.f32 + /tmp/score_truth.json (make_score_audio.py), or DATA=tysk with /tmp/tysk_full_gtr.f32 + /tmp/tysk_full_song.json.
# Scores the first SECS seconds (default 60). Prints RAW (Basic Pitch) and CLEAN (after cleanNotes) as hit / precision / recall / F1.
# python3 score_transcribe.py [SECS] [json of cleanNotes overrides, e.g. '{"minStr":3}']
import json,sys,numpy as np
from playwright.sync_api import sync_playwright
SECS=float(sys.argv[1]) if len(sys.argv)>1 else 60
OVR=sys.argv[2] if len(sys.argv)>2 else '{}'
import os
DATA=os.environ.get('DATA','synth')  # synth = the Midland tab played by a synth; tysk = a real Demucs guitar stem with the verified tab as truth
if DATA=='tysk':
    sg=json.load(open('/tmp/tysk_full_song.json'));TR=[(sg['recEvT'][i],0.3,n['midi']) for i,e in enumerate(sg['events']) for n in e['notes']];AUD='tysk_full_gtr.f32'
else:
    TR=json.load(open('/tmp/score_truth.json'));AUD='score_gtr.f32'
truth=[(t,d,m) for t,d,m in TR if t<SECS-1]
def score(est,tol=0.05):
    est=sorted(est);tr=sorted(truth);used=set();tp=tpc=oct_=0
    for t,d,m in tr:
        best=None
        for j,(et,ed,em) in enumerate(est):
            if j in used:continue
            if abs(et-t)<=tol and em==m:best=j;break
        if best is not None:used.add(best);tp+=1
    # pitch-class matches among the rest (octave errors)
    for t,d,m in tr:
        for j,(et,ed,em) in enumerate(est):
            if j in used:continue
            if abs(et-t)<=tol and em%12==m%12:used.add(j);oct_+=1;break
    p=tp/max(1,len(est));r=tp/max(1,len(tr));f=2*p*r/max(1e-9,p+r)
    return dict(truth=len(tr),est=len(est),hit=tp,octave_err=oct_,precision=round(p,3),recall=round(r,3),F1=round(f,3))
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page(service_workers='block');errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('http://localhost:8769/lab/stems.html');pg.wait_for_timeout(800)
    r=pg.evaluate("""async([secs,ovr,aud])=>{const g=new Float32Array(await (await fetch('http://localhost:8771/'+aud)).arrayBuffer());
      const n=Math.min(g.length,Math.round(secs*44100));const gg=g.slice(0,n);R.length=0;window.CN_OVR=JSON.parse(ovr);
      const g22=await toRate([gg,gg],22050);const raw=await transcribe(g22);const cl=cleanNotes(raw,g22);
      return {raw:raw.map(x=>[x.t,x.d,x.midi]),clean:cl.map(x=>[x.t,x.d,x.midi]),log:R.join('\\n')}}""",[SECS,OVR,AUD])
    print('RAW   ',score(r['raw']));print('CLEAN ',score(r['clean']));print(errs)
    json.dump(r,open('/tmp/score_last.json','w'))
    b.close()
