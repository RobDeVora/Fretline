import re,numpy as np,librosa
wav='/mnt/user-data/uploads/e0800d8c-fretline-audio-b-fp-arp2-1237.wav';rep='/mnt/user-data/uploads/5e79633b-fretline-report-b-fp-arp2.txt'
y,sr=librosa.load(wav,sr=22050);N=4096;win=np.hanning(N)
names=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
def midi(n):
    m=re.match(r'([A-G]#?)(\d)',n);return 12*(int(m.group(2))+1)+names.index(m.group(1))
def mag(t0,f):
    a=int(t0*sr);x=y[a:a+N]
    if len(x)<N:return 1e-9
    S=np.abs(np.fft.rfft(x*win));fr=np.fft.rfftfreq(N,1/sr);k=int(np.argmin(np.abs(fr-f)));return S[max(k-1,0):k+2].max()+1e-9
rows=[]
for l in open(rep):
    m=re.match(r'#(\d+) (\S+) \S+ · (HIT|MISS) .*?bp ([\d.]+)(?: · bp also \S+ [\d.]+)?(?: · bp@([+-]\d+)ms)?.*?@([\d.]+)s',l)
    if not m:continue
    i,n,res,bp,off,t=int(m.group(1)),m.group(2),m.group(3),float(m.group(4)),m.group(5),float(m.group(6))
    tp=t+(int(off)/1000 if off else 0.12);f=440*2**((midi(n)-69)/12)
    pre_t=mag(tp-0.14,f);post_t=mag(tp+0.02,f);pre_o=mag(tp-0.14,f/2);post_o=mag(tp+0.02,f/2)
    rows.append((i,n,res,bp,post_t/pre_t,post_o/pre_o,post_t/post_o))
def show(tag,sel):
    print(tag)
    for r in sel:print('  #%d %s %s bp %.2f | target rise x%.1f | octave-below rise x%.1f | target/octave-below level x%.1f'%r)
show('FALSE MISSES (BP says played, app missed)',[r for r in rows if r[0] in (5,13,14,37,46)])
show('NOT PLAYED (bp<0.3, app MISS)',[r for r in rows if r[2]=='MISS' and r[3]<0.3])
hit=[r for r in rows if r[2]=='HIT' and r[3]>=0.8]
print('BP-confirmed HITS (%d): target rise pct10/50/90'%len(hit),np.percentile([r[4] for r in hit],[10,50,90]).round(1),'target/oct-below level pct10/50/90',np.percentile([r[6] for r in hit],[10,50,90]).round(1))
