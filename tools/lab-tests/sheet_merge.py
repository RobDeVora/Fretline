# v1.90: Lab with a tab (the solo) AND a chord sheet for /tmp/solotest/solo90.wav (make_solo90.py): chords G C [solo] D Em.
# Checks the merge: the 16 solo notes are single notes on the solo's picks, the chords are around them, no chord inside
# the solo; then "the chords win". Usage: python3 sheet_merge.py   (serve the repo on 8769, cdnsrv.py on 8771 first)
import json,os
from playwright.sync_api import sync_playwright
T=json.load(open('/tmp/solotest/truth.json'))
# tab for the solo: G B D B G B D G (x2), one column per 8th, 8 per bar
notes=[(3,0),(4,0),(4,3),(4,0),(3,0),(4,0),(4,3),(5,3)];names='EADGBe';rows=[[] for _ in range(6)]
for bar in range(2):
  for s,f in notes:
    for k in range(6):rows[k].append('--'+(str(f) if k==s else '-'))
  for k in range(6):rows[k].append('|')
tab='\n'.join(names[k]+'|'+''.join(rows[k]) for k in range(5,-1,-1))
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');ctx=b.new_context(viewport={'width':412,'height':900},service_workers='block')
  for first,win in ((('tab','tab'),) if os.environ.get('FROMTO') else (('tab','tab'),('chords','tab'),('tab','chords'))):
    pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('http://localhost:8769/lab/stems.html?ortbase=http://localhost:8771/&modelurl=http://localhost:8771/dummy.onnx');pg.wait_for_timeout(800)
    pg.set_input_files('#file','/tmp/solotest/solo90.wav');pg.select_option('#secs','0');pg.select_option('#be','wasm');pg.fill('#ttl','Merge '+first+' '+win)
    pg.click('#sheetBox summary');a,c='G  C  G  D  Em',tab
    pg.fill('#sheet',tab if first=='tab' else 'G  C  G  D  Em');pg.fill('#sheet2','G  C  G  D  Em' if first=='tab' else tab)
    if os.environ.get('FROMTO'):f,t=os.environ['FROMTO'].split(',');pg.fill('#tabFrom',f);pg.fill('#tabTo',t)
    if os.environ.get('STRUMS'):pg.select_option('#strumMode','strums')
    pg.select_option('#mergeWin',win);pg.click('#go');pg.wait_for_function('window.__labDone',timeout=900000)
    print('==',first,'first; wins:',win);print('\n'.join(l for l in pg.text_content('#log').split('\n') if l.startswith(('sheet','merge','tempo','song','ERROR'))))
    d=pg.evaluate('window.__labSong');ev=d['events'];spb=60/d['bpm'];ts=lambda e:round(d['recOffset']+e['t']*spb,3)
    json.dump(d,open('/tmp/solotest/def.json','w'))
    single=[e for e in ev if not e.get('chord') and not e.get('strum') and len(e['notes'])==1];ch=[e for e in ev if e.get('chord') or e.get('strum')]
    st=T['solo'][0]-0.3;en=T['solo'][-1]+0.3
    print('steps',len(ev),'· single notes',len(single),'· chords',[(e.get('chord') or e.get('label'),ts(e)) for e in ch],'· chords inside the solo',sum(1 for e in ch if st<=ts(e)<=en))
    if single:err=[int(abs(ts(e)-t)*1000) for e,t in zip(single,T['solo'])];print('solo note-time errors (ms) first 16:',err[:16],'· truth chord times',T['truth'])
    print('errors',errs);pg.close()
  b.close()
