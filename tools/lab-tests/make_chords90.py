# Builds /tmp/chordtest/chords90.wav + truth.json for sheet_chords.py: 2 s silence, then G 2 bars, C 1, D 1, Em 2,
# G 1, C 1 at 90 BPM, 8th-note strums (down louder, up reversed), additive "guitar" strings, slight timing jitter.
import numpy as np,wave,json,os
os.makedirs('/tmp/chordtest',exist_ok=True)
sr=44100;bpm=90;spb=60/bpm;start=2.0
shapes={'G':[43,47,50,55,59,67],'C':[48,52,55,60,64],'D':[50,57,62,66],'Em':[40,47,52,55,59,64]}
prog=[('G',8),('C',4),('D',4),('Em',8),('G',4),('C',4)]
T=start+sum(b for _,b in prog)*spb+2;x=np.zeros(int(T*sr))
def pluck(m,t,amp):
  f=440*2**((m-69)/12);n=int(1.5*sr);tt=np.arange(n)/sr;s=np.zeros(n)
  for h in range(1,9):s+=np.sin(2*np.pi*f*h*tt)/(h**1.3)*np.exp(-tt*(2.5+h*0.8))
  s*=amp*np.minimum(1,tt/0.003);i=int(t*sr);j=min(len(x),i+n);x[i:j]+=s[:j-i]
truth=[];t=start;rng=np.random.default_rng(1);strums=0
for name,beats in prog:
  truth.append((name,round(t,3)))
  for k in range(beats*2):
    tk=t+k*spb/2+rng.normal(0,0.008);notes=shapes[name] if k%2==0 else shapes[name][::-1]
    for i,m in enumerate(notes):pluck(m,tk+i*0.012,0.25 if k%2==0 else 0.15)
    strums+=1
  t+=beats*spb
x/=np.abs(x).max()*1.1;d=(np.stack([x,x],1)*32767).astype('<i2')
w=wave.open('/tmp/chordtest/chords90.wav','wb');w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes(d.tobytes());w.close()
json.dump({'truth':truth,'strums':strums},open('/tmp/chordtest/truth.json','w'));print(truth,strums)
