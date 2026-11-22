"""Bend steps need a real bend (v1.146). Builds a synthetic recording for the 'Bends and vibrato' lesson from a real report's
step times (the owner's run 1411): every plain step is a steady plucked tone, every bend step is either played WITHOUT bending (must MISS)
or glides up the whole step to the target within 0.22 s and holds (must HIT).
Usage (from tools/lab-tests via /tmp/withsrv.sh): python3 ../detection-tests/test_bends.py REPORT.txt"""
import sys,re,subprocess,numpy as np,soundfile as sf,os
rep=sys.argv[1];SR=22050
names=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
def midi(n):
    m=re.match(r'([A-G]#?)(\d)',n);return 12*(int(m.group(2))+1)+names.index(m.group(1))
steps=[]
for l in open(rep).read().split('\n'):
    m=re.match(r'#(\d+) ([A-G]#?\d) \S+ · .*?@([\d.]+)s',l)
    if m:steps.append((int(m.group(1)),midi(m.group(2)),float(m.group(3))))
def tone(f0,f1,dur,sr=SR):
    # a bend: up a half step in 0.15 s, held 0.4 s (a half-step bend stops here), then on up to the whole step (a full bend)
    n=int(dur*sr);t=np.arange(n)/sr
    g=np.clip(t/0.15,0,1)*0.5 if f1==f0 else np.where(t<0.55,np.clip(t/0.15,0,1)*0.5,0.5+np.clip((t-0.55)/0.15,0,1)*0.5)
    f=f0*(f1/f0)**g
    ph=2*np.pi*np.cumsum(f)/sr;y=sum(np.sin(k*ph)/k**1.2 for k in range(1,9))
    env=np.exp(-t/1.1)*np.minimum(1,t/0.004);return 0.25*y*env
def build(bent):
    y=np.zeros(int((steps[-1][2]+4)*SR))
    for i,m,t in steps:
        f=440*2**((m-69)/12);isb=i%2==1
        x=tone(f,f*2**(2/12) if (isb and bent) else f,2.0 if isb else 0.9);a=int(t/1.00843*SR);y[a:a+len(x)]+=x[:len(y)-a]
    return y
for name,bent in(('unbent',False),('bent',True)):
    sf.write(f'/tmp/synb/{name}.wav',build(bent),SR)
    r=subprocess.run(['python3',os.path.join(os.path.dirname(os.path.abspath(__file__)),'replay_run.py'),f'/tmp/synb/{name}.wav',rep,f'/tmp/synb/{name}'],env={**os.environ,'LESSON':'i-bend'},capture_output=True,text=True)
    out=r.stdout;print(name,[l for l in out.split('\n') if l.startswith('steps ') or l.startswith('real HIT') or l.startswith('real MISS')])
    txt=open(f'/tmp/synb/{name}.txt').read();rows={int(re.match(r'#(\d+)',l).group(1)):('HIT' in l.split('·')[1]) for l in txt.split('\n') if re.match(r'#\d+ ',l)}
    bs=[i for i in rows if i%2==1];hit=[i for i in bs if rows[i]]
    print(name,'bend steps hit',len(hit),'of',len(bs))
    ok=(len(hit)==0) if not bent else (len(hit)==len(bs))
    print('PASS' if ok else 'FAIL',name)
    if not ok:sys.exit(1)
