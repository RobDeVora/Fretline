"""How well does Spotify's Basic Pitch (ONNX) confirm real played notes and reject wrong / ringing ones?
Uses GuitarSet (Zenodo 3371780: audio_mono-mic + annotation). Usage: python3 guitarset_bp_eval.py DIR [N_FILES]
Positives: every annotated note onset (is there an onset of that pitch within -80..+120 ms?).
Negatives: (a) the neighbouring semitone at the same moment, (b) a pitch that is still ringing mid-note (no new pick).
"""
import sys,os,json,glob,random,warnings
warnings.filterwarnings('ignore')
import numpy as np
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
D=sys.argv[1];N=int(sys.argv[2]) if len(sys.argv)>2 else 40
FR=22050/256
files=sorted(glob.glob(os.path.join(D,'*_mic.wav')));random.Random(1).shuffle(files);files=files[:N]
pos=[];negN=[];negR=[];posNote=[];negRNote=[]
for wf in files:
    jf=wf.replace('_mic.wav','.jams')
    j=json.load(open(jf));notes=[]
    for a in j['annotations']:
        if a['namespace']=='note_midi':
            for d in a['data']:
                v=d['value'] if not isinstance(d['value'],dict) else d['value'].get('value')
                notes.append((d['time'],d['duration'],int(round(v))))
    out,_,_=predict(wf,ICASSP_2022_MODEL_PATH);on=out['onset'];nt=out['note']
    def score(arr,t,m):
        if m<21 or m>108:return None
        a=max(0,int((t-0.08)*FR));b=min(len(arr),int((t+0.12)*FR)+1)
        return float(arr[a:b,m-21].max()) if b>a else None
    onsets={}
    for t,d,m in notes:onsets.setdefault(m,[]).append(t)
    for t,d,m in notes:
        s=score(on,t,m)
        if s is not None:pos.append(s)
        for dm in (-1,1):
            if any(abs(t-x)<0.2 for x in onsets.get(m+dm,[])):continue
            s=score(on,t,m+dm)
            if s is not None:negN.append(s)
        if d>=0.7:
            tm=t+0.5
            if not any(abs(tm-x)<0.3 for x in onsets.get(m,[])):
                s=score(on,tm,m);s2=score(nt,tm,m)
                if s is not None:negR.append(s);negRNote.append(s2)
    print(os.path.basename(wf),len(notes),'notes',flush=True)
pos,negN,negR=map(np.array,(pos,negN,negR));negRNote=np.array(negRNote)
print('\npositives',len(pos),'neighbour negatives',len(negN),'ring negatives',len(negR))
for th in (0.2,0.3,0.4,0.5,0.6,0.7):
    print('onset>=%.1f  note recall %.1f%%  semitone-neighbour accepted %.1f%%  ringing note accepted %.1f%%'%(th,100*(pos>=th).mean(),100*(negN>=th).mean(),100*(negR>=th).mean()))
print('(for comparison: a ringing note shown as simply "still active" in the note output: accepted',round(100*(negRNote>=0.3).mean(),1),'% at 0.3)')
