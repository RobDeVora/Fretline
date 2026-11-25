import json,glob,os,re,collections,numpy as np
D='/tmp/idmt/'
rows=[]
for f in glob.glob(D+'bp_*.json'):
    b=os.path.basename(f)[3:-5];notes=json.load(open(f));t=open(D+b+'.xml').read()
    for e in re.findall(r'<event>(.*?)</event>',t,re.S):
        g=lambda k:(re.search(f'<{k}>(.*?)</{k}>',e) or [0,''])[1]
        ex=g('expressionStyle');on=float(g('onsetSec'));off=float(g('offsetSec'));p=int(g('pitch'))
        if off-on<0.25:continue
        c=[n for n in notes if abs(n['t']-on)<0.1 and abs(n['m']-p)<=2 and n['d']>=0.2 and len(n['b'])>=4]
        if not c:rows.append((ex,b,None));continue
        n=min(c,key=lambda n:abs(n['t']-on)+0.05*abs(n['m']-p));bb=np.array(n['b'],float)
        rows.append((ex,b,dict(rng=float(bb.max()-bb.min()),net=float(bb[-3:].mean()-bb[:3].mean()),mx=float(np.abs(bb).max()),m=n['m']-p,d=n['d'])))
cnt=collections.Counter(r[0] for r in rows);found=collections.Counter(r[0] for r in rows if r[2])
print('events',dict(cnt),'matched',dict(found))
for k in ('BE','SL','VI','HA','DN','NO'):
    x=[r[2] for r in rows if r[0]==k and r[2]]
    if x:print(k,len(x),'range pct10/50/90',np.percentile([a['rng'] for a in x],[10,50,90]).round(2),'net',np.percentile([a['net'] for a in x],[10,50,90]).round(2),'pitch shift vs label median',np.median([a['m'] for a in x]))
json.dump([r for r in rows if r[2]],open(D+'bend_rows.json','w'))
