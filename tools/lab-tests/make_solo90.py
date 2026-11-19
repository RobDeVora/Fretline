# Builds /tmp/solotest/solo90.wav + truth.json for sheet_merge.py: 2 s silence, then at 90 BPM: G 2 bars (8th strums),
# C 1 bar, a 2-bar single-note solo (G B D B G B D G x2, 8th notes), D 1 bar, Em 2 bars. Same strings as make_chords90.py.
import numpy as np,wave,json,os
os.makedirs('/tmp/solotest',exist_ok=True)
sr=44100;bpm=90;spb=60/bpm;start=2.0
shapes={'G':[43,47,50,55,59,67],'C':[48,52,55,60,64],'D':[50,57,62,66],'Em':[40,47,52,55,59,64]}
solo=[55,59,62,59,55,59,62,67]*2
prog=[('G',8),('C',4),('SOLO',8),('D',4),('Em',8)]
T=start+sum(b for _,b in prog)*spb+2;x=np.zeros(int(T*sr))
def pluck(m,t,amp):
  f=440*2**((m-69)/12);n=int(1.5*sr);tt=np.arange(n)/sr;s=np.zeros(n)
  for h in range(1,9):s+=np.sin(2*np.pi*f*h*tt)/(h**1.3)*np.exp(-tt*(2.5+h*0.8))
  s*=amp*np.minimum(1,tt/0.003);i=int(t*sr);j=min(len(x),i+n);x[i:j]+=s[:j-i]
truth=[];soloT=[];t=start;rng=np.random.default_rng(1)
for name,beats in prog:
  truth.append((name,round(t,3)))
  if name=='SOLO':
    for k,m in enumerate(solo):tk=t+k*spb/2+rng.normal(0,0.005);pluck(m,tk,0.35);soloT.append(round(tk,3))
  else:
    for k in range(beats*2):
      tk=t+k*spb/2+rng.normal(0,0.008);notes=shapes[name] if k%2==0 else shapes[name][::-1]
      for i,m in enumerate(notes):pluck(m,tk+i*0.012,0.25 if k%2==0 else 0.15)
  t+=beats*spb
x/=np.abs(x).max()*1.1;d=(np.stack([x,x],1)*32767).astype('<i2')
w=wave.open('/tmp/solotest/solo90.wav','wb');w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes(d.tobytes());w.close()
json.dump({'truth':truth,'solo':soloT},open('/tmp/solotest/truth.json','w'));print(truth,len(soloT))
