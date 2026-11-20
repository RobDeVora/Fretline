# v1.116: a known-answer test recording. Plays the guitar tracks (Lead + Rhythm) of /tmp/midland_tab.mid with a plucked-string
# synth (harmonics 1-8, amplitude h^-1.2, decay e^-(3+0.9h)t, 2 ms attack) for the first SECS seconds.
# Writes /tmp/score_gtr.f32 (44.1 kHz mono float32) and /tmp/score_truth.json ([[t, dur, midi]...]).
import json,sys,mido,numpy as np
SECS=float(sys.argv[1]) if len(sys.argv)>1 else 60;SR=44100
m=mido.MidiFile('/tmp/midland_tab.mid');notes=[]
for ti in (0,1):
    t=0.0;on={}
    for msg in m.tracks[ti]:
        t+=mido.tick2second(msg.time,m.ticks_per_beat,500000) if False else 0
    # use the merged timeline so the tempo map applies
tl=[]
for msg in mido.merge_tracks(m.tracks):pass
abs_t=0.0;tracks_notes={0:[],1:[]}
# per-track absolute seconds using the file's tempo map (tempo changes live in track 0)
tempos=[];tick=0
for msg in m.tracks[0]:
    tick+=msg.time
    if msg.type=='set_tempo':tempos.append((tick,msg.tempo))
if not tempos or tempos[0][0]!=0:tempos.insert(0,(0,500000))
def sec(tk):
    s=0.0;prev=0;cur=tempos[0][1]
    for (tt,tp) in tempos:
        if tt>=tk:break
        if tt>prev:s+=mido.tick2second(tt-prev,m.ticks_per_beat,cur);prev=tt
        cur=tp
    return s+mido.tick2second(tk-prev,m.ticks_per_beat,cur)
for ti in (0,1):
    tick=0;on={}
    for msg in m.tracks[ti]:
        tick+=msg.time
        if msg.type=='note_on' and msg.velocity>0:on[msg.note]=(tick,msg.velocity)
        elif msg.type in('note_off','note_on') and msg.note in on:
            t0,v=on.pop(msg.note);notes.append((sec(t0),sec(tick)-sec(t0),msg.note,v))
notes=sorted(n for n in notes if n[0]<SECS-0.5)
y=np.zeros(int((SECS+3)*SR),dtype=np.float32)
for t,d,mid,v in notes:
    f0=440*2**((mid-69)/12);L=int(min(max(d,0.25)+0.4,3.0)*SR);tt=np.arange(L)/SR;w=np.zeros(L)
    for h in range(1,9):
        if f0*h<SR/2.2:w+=h**-1.2*np.sin(2*np.pi*f0*h*tt)*np.exp(-(3+0.9*h)*tt*(0.55 if mid<52 else 1.0))
    w*=np.minimum(1,tt/0.002)*(v/127)*0.25;i=int(t*SR);y[i:i+L]+=w[:len(y)-i]
y=y[:int(SECS*SR)];y/=max(1e-9,np.abs(y).max())/0.9;y.astype(np.float32).tofile('/tmp/score_gtr.f32')
json.dump([[round(t,4),round(d,4),m] for t,d,m,v in notes],open('/tmp/score_truth.json','w'))
print(len(notes),'notes',round(len(y)/SR),'s')
