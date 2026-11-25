# v1.151: how often does the Lab's string/fret choice match the real tab? Songsterr tab MIDIs put each string on its own channel, so the channel gives the true string.
# Usage: /tmp/withsrv.sh python3 score_frets.py TAB.mid [TAB2.mid ...]   (prints per-track and total match rate for string+fret, and playability of chords)
import sys,itertools,collections,json,mido
from playwright.sync_api import sync_playwright
OPEN=[40,45,50,55,59,64]
def truth(path):
    m=mido.MidiFile(path);tpb=m.ticks_per_beat;out=[]
    for ti,t in enumerate(m.tracks):
        name='';prog=None;notes=[];tick=0
        for msg in t:
            tick+=msg.time
            if msg.type=='track_name':name=msg.name
            if msg.type=='program_change' and prog is None:prog=msg.program
            if msg.type=='note_on' and msg.velocity>0 and msg.channel!=9:notes.append((tick/tpb,msg.note,msg.channel))
        if not notes or prog is None or not(24<=prog<=31):continue
        chs=sorted({c for _,_,c in notes},key=lambda c:min(n for _,n,cc in notes if cc==c))
        lo={c:min(n for _,n,cc in notes if cc==c) for c in chs}
        best=None
        for off in (0,-1,-2,-3,-4):   # the file may be in a lowered tuning (E flat ...): then every string sits `off` semitones below standard
            for sub in itertools.combinations(range(6),len(chs)):
                ok=True;cost=0
                for c,s in zip(chs,sub):
                    for _,n,cc in notes:
                        if cc!=c:continue
                        f=n-(OPEN[s]+off)
                        if f<0 or f>24:ok=False;break
                        cost+=f
                    if not ok:break
                if ok and(best is None or cost<best[0]-1e-9):best=(cost,dict(zip(chs,sub)),off)
            if best and off==0:break
        if not best:print('  (no consistent string mapping for',name,'chs',chs,')');continue
        mp=best[1];off=best[2];out.append((name or f'track{ti}',[(b,n-off,mp[c],n-off-OPEN[mp[c]]) for b,n,c in sorted(notes)]))
    return out
res=[];tot=[0,0,0];J=[0,0,0]
with sync_playwright() as p:
    br=p.chromium.launch();pg=br.new_page();pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(1500)
    for path in sys.argv[1:]:
        for name,tr in truth(path):
            # first 400 beats, one pass
            tr=[x for x in tr if x[0]<400]
            notes=[{'midi':n,'beat':b,'dur':0.5} for b,n,s,f in tr]
            evs=pg.evaluate("(a)=>eventsFromNotes(a,{shift:0,bpb:4}).map(e=>({t:e.t,notes:e.notes.map(n=>({s:n.s,f:n.f,midi:n.midi}))}))",notes)
            byT=collections.defaultdict(list)
            for e in evs:
                for n in e['notes']:byT[n['midi']].append((e['t'],n['s'],n['f']))
            hit=tot_=0;stretch=0;chords=0
            for b,n,s,f in tr:
                c=[x for x in byT.get(n,[]) if abs(x[0]-b)<=0.14]
                if not c:continue
                g=min(c,key=lambda x:abs(x[0]-b));tot_+=1;hit+=((g[1],g[2])==(s,f))
            for e in evs:
                fr=[n['f'] for n in e['notes'] if n['f']>0]
                if len(e['notes'])>=3:
                    chords+=1;stretch+=(max(fr)-min(fr)>4) if len(fr)>1 else 0
            pos=[];
            for e in evs:
                fr=[n['f'] for n in e['notes'] if n['f']>0]
                if fr:pos.append(sum(fr)/len(fr))
            jumps=[abs(a-b) for a,b in zip(pos,pos[1:])];big=sum(1 for j in jumps if j>4)
            print(f"{path.split('/')[-1][:20]:20} {name[:12]:12} notes {tot_:5} match {100*hit/max(tot_,1):5.1f}%  chords {chords} span>4: {stretch}  steps {len(evs)} mean hand move {sum(jumps)/max(len(jumps),1):.2f} frets, moves >4 frets: {big} ({100*big/max(len(jumps),1):.1f}%)")
            J[0]+=sum(jumps);J[1]+=len(jumps);J[2]+=big
            tot[0]+=hit;tot[1]+=tot_;tot[2]+=stretch
    br.close()
print(f"HAND mean move {J[0]/max(J[1],1):.2f} frets, moves >4: {J[2]}");print(f"TOTAL match {100*tot[0]/max(tot[1],1):.1f}% of {tot[1]} notes; unplayable chords {tot[2]}")
