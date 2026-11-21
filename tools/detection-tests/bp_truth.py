import re,sys,numpy as np
FR=22050/256;names=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
def midi(n):
    m=re.match(r'([A-G]#?)(\d)',n);return 12*(int(m.group(2))+1)+names.index(m.group(1))
on=np.load('/tmp/on1352.npy');s=309/60000;ic=0.122
def parse(p):
    d={}
    for l in open(p):
        m=re.match(r'#(\d+) ([A-G]#?\d) \S+ · (HIT|MISS)',l)
        if m:d[int(m.group(1))]=(midi(m.group(2)),m.group(3)=='HIT',l.strip())
    return d
R=parse('/mnt/user-data/uploads/4a2d1f5b-attachment.txt');T={}
for l in open('/mnt/user-data/uploads/4a2d1f5b-attachment.txt'):
    m=re.match(r'#(\d+) .*@([\d.]+)s',l)
    if m:T[int(m.group(1))]=float(m.group(2))
def truth(i):
    m=R[i][0];t=T[i];tt=t+ic+s*t;a=max(0,int((tt-0.15)*FR));b=min(len(on),int((tt+0.15)*FR)+1);return float(on[a:b,m-21].max())
def stats(path,th=0.6):
    P=parse(path);fh=[];fm=[];ok=0
    for i in P:
        sc=truth(i);played=sc>=th
        if P[i][1] and sc<0.5:fh.append(i)
        if (not P[i][1]) and played:fm.append(i)
        if P[i][1]==played:ok+=1
    return len(P),ok,fh,fm
if __name__=='__main__':
    for p in sys.argv[1:]:
        n,ok,fh,fm=stats(p);print(p,'agree with BP-truth %d/%d'%(ok,n),'false hits',len(fh),fh,'false misses',len(fm),fm)
