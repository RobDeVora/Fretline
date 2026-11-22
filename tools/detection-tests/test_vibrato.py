"""v1.146/147: the report's vibrato line (report only). Synthetic recordings built from a real 'Bends and vibrato' report: every bend step is bent up and held;
with vibrato (30 cents p2p, 5.5 Hz from 0.8 s) -> 'vibrato N cents'; steady -> 'no vibrato heard'.
Usage: cd tools/lab-tests; /tmp/withsrv.sh python3 ../detection-tests/test_vibrato.py REPORT.txt"""
import sys,re,subprocess,os,numpy as np,soundfile as sf
rep=sys.argv[1];SR=22050;names=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
def midi(n):
    m=re.match(r'([A-G]#?)(\d)',n);return 12*(int(m.group(2))+1)+names.index(m.group(1))
steps=[(int(m.group(1)),midi(m.group(2)),float(m.group(3))) for l in open(rep) for m in [re.match(r'#(\d+) ([A-G]#?\d) \S+ · .*?@([\d.]+)s',l)] if m]
def tone(f0,dur,bend,vib):
    n=int(dur*SR);t=np.arange(n)/SR
    g=np.where(t<0.55,np.clip(t/0.15,0,1)*0.5,0.5+np.clip((t-0.55)/0.15,0,1)*0.5) if bend else 0*t
    cents=g*200+(vib*0.5*np.sin(2*np.pi*5.5*t)*np.clip((t-0.7)/0.1,0,1) if vib else 0)
    f=f0*2**(cents/1200);ph=2*np.pi*np.cumsum(f)/SR;y=sum(np.sin(k*ph)/k**1.2 for k in range(1,9))
    return 0.25*y*np.exp(-t/1.1)*np.minimum(1,t/0.004)
for name,vib in(('vib',30),('steady',0)):
    y=np.zeros(int((steps[-1][2]+4)*SR))
    for i,m,t in steps:
        x=tone(440*2**((m-69)/12),2.0 if i%2 else 0.9,i%2==1,vib if i%2 else 0);a=int(t/1.00843*SR);y[a:a+len(x)]+=x[:len(y)-a]
    sf.write(f'/tmp/synb/v_{name}.wav',y,SR)
    subprocess.run(['python3',os.path.join(os.path.dirname(os.path.abspath(__file__)),'replay_run.py'),f'/tmp/synb/v_{name}.wav',rep,f'/tmp/synb/v_{name}'],env={**os.environ,'LESSON':'i-bend'},capture_output=True,text=True)
    L=[l for l in open(f'/tmp/synb/v_{name}.txt').read().split('\n') if re.match(r'#\d+ ',l) and int(l[1:l.index(' ')])%2==1]
    got=[re.search(r'(vibrato \d+ cents|slight vibrato|no vibrato heard|vibrato not judged)',l) for l in L]
    print(name,[g.group(1) if g else None for g in got])
    ok=all(g and ((name=='vib' and g.group(1).startswith('vibrato ') and 'not' not in g.group(1)) or (name=='steady' and g.group(1)=='no vibrato heard')) for g in got)
    print('PASS' if ok else 'FAIL',name)
