"""Vibrato check on a shared lesson recording: pyin pitch contour of each long step, wobble depth (cents peak-to-peak after removing drift below 2.5 Hz) and strongest 3.5-9 Hz rate. Usage: python3 vibrato_check.py AUDIO.wav REPORT.txt (written for the Bends lesson: odd steps, drift 1.00843)."""
import re,sys,numpy as np,librosa,scipy.signal as ss
wav,rep=sys.argv[1:3]
y,sr=librosa.load(wav,sr=22050)
f0,vf,_=librosa.pyin(y,fmin=80,fmax=1000,sr=sr,frame_length=2048,hop_length=256)
fr=sr/256;cents=1200*np.log2(f0/440)
steps=[(int(m.group(1)),m.group(2),float(m.group(3)),'HIT' in m.group(0)) for l in open(rep) for m in [re.match(r'#(\d+) (\S+) \S+ · (HIT|MISS).*?@([\d.]+)s',l)] if m for m in [type('M',(),{'group':lambda s,k,m=m:[m.group(0),m.group(1),m.group(2),m.group(4)][k]})()]] if False else []
for l in open(rep):
    m=re.match(r'#(\d+) (\S+) .*?@([\d.]+)s',l)
    if m:steps.append((int(m.group(1)),m.group(2),float(m.group(3))))
for i,n,t in steps:
    if i%2==0:continue
    a=int((t/1.00843+0.45)*fr);b=int((t/1.00843+1.9)*fr);c=cents[a:b];v=~np.isnan(c)
    if v.sum()<30:print(i,n,'too little pitched audio',v.sum());continue
    c=np.interp(np.arange(len(c)),np.where(v)[0],c[v])
    hp=ss.sosfiltfilt(ss.butter(2,2.5/(fr/2),'high',output='sos'),c-c.mean())
    p2p=np.percentile(hp,95)-np.percentile(hp,5)
    fq,P=ss.periodogram(hp,fr);band=(fq>=3.5)&(fq<=9);pk=fq[band][np.argmax(P[band])]
    print(i,n,'voiced %d%%'%(100*v.mean()),'wobble p2p %.0f cents'%p2p,'peak %.1f Hz'%pk,'band share %.0f%%'%(100*P[band].sum()/P.sum()))
print('--- contours (cents vs median, every 60 ms)')
for i,n,t in steps:
    if i not in (1,9,11):continue
    a=int((t/1.00843+0.3)*fr);b=int((t/1.00843+2.0)*fr);c=cents[a:b];med=np.nanmedian(c)
    print(i,n,' '.join('%d'%round(x-med) if not np.isnan(x) else '.' for x in c[::4]))
