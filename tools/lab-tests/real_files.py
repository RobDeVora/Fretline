# v1.91 on a real song: TYSK guitar stem (/tmp/tysk_full_gtr.f32) + the tab MIDI (/tmp/tysk.mid, box 1, notes) + the
# chords MIDI (/tmp/tysk_chords.mid, box 2). Truth for the tab = /tmp/tysk_full_song.json (the song the Lab made from
# the tab MIDI alone). Prints what was kept, the chord names, and how far the tab notes are from the truth.
# python3 real_files.py [mergeWin] [swap]   (swap = chords file in box 1, tab in box 2)
import json,sys,numpy as np
from playwright.sync_api import sync_playwright
WIN=sys.argv[1] if len(sys.argv)>1 else 'tab';SWAP=len(sys.argv)>2
T=np.array(json.load(open('/tmp/tysk_full_song.json'))['recEvT'])
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page(service_workers='block');errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/lab/stems.html');pg.wait_for_timeout(800)
  r=pg.evaluate("""async([win,swap])=>{const g=new Float32Array(await (await fetch('http://localhost:8771/tysk_full_gtr.f32')).arrayBuffer());const core=await loadCore();
    const rd=async f=>({info:core.parseMidi(new Uint8Array(await (await fetch('http://localhost:8771/'+f)).arrayBuffer())),fmt:'MIDI',name:f});
    const tab=await rd('tysk.mid'),ch=await rd('tysk_chords.mid');$('secs').innerHTML+='<option value="0">x</option>';$('secs').value='0';$('ttl').value='TYSK both';$('mergeWin').value=win;
    if(!swap){setSheetFile(tab);$('sheetAs').value='notes';setSheetFile2(ch);}else{setSheetFile(ch);$('sheetAs').value='chords';setSheetFile2(tab);}
    const part2=$('sheet2Part').options[$('sheet2Part').selectedIndex].text;
    let sheet=readSecond(core,readSheet(core,'','auto'),'');const s2=sheet.also;
    const z=new Float32Array(g.length);R.length=0;await makeSheetSong(sheet,g,g,g,g,z,z,g.length);const d=window.__labSong;
    window.__dump=JSON.stringify(d);return {part2,kinds:[sheet.kind,s2.kind],log:R.join('\\n'),bpm:d.bpm,capo:d.capo||0,tuning:d.tuning+'/'+d.builtTuning,ev:d.events.map(e=>({c:!!(e.chord||e.strum),name:e.chord||e.label||'',n:e.notes.length,pcs:(e.pcs||[]).map(x=>(x+(d.capo||0))%12)})),T:d.recEvT};}""",[WIN,SWAP])
  print('second-box track picked:',r['part2'],'· kinds',r['kinds']);print('\n'.join(l for l in r['log'].split('\n') if l.startswith(('sheet','merge','tempo','song'))))
  ev=r['ev'];tt=np.array(r['T']);isC=np.array([e['c'] for e in ev])
  print('bpm',r['bpm'],'capo',r['capo'],'tuning',r['tuning'],'· steps',len(ev),'· tab steps',int((~isC).sum()),'· chord steps',int(isC.sum()))
  names=[];[names.append(e['name']) for e in ev if e['c'] and (not names or names[-1]!=e['name'])];print('chord changes (first 24):',names[:24])
  ts=tt[~isC];near=np.array([np.min(np.abs(T-t)) for t in ts])*1000 if len(ts) else np.array([0])
  print('tab steps vs the tab-only song: %d of %d within 20 ms of a true step, median %.0f ms'%((near<=20).sum(),len(ts),np.median(near)))
  # where the chords are kept: list gaps
  ct=tt[isC];print('chord steps kept at (s):',np.round(ct[:30],1))
  open('/tmp/tysk_merge.json','w').write(pg.evaluate('window.__dump'));print('errors',errs);b.close()
# agreement: for each chord step (merge "chords win" keeps them all), the share of the tab-only song's notes inside
# its span whose note name is in the chord (the tab-only song is verified against the recording)
if WIN=='chords':
  base=json.load(open('/tmp/tysk_full_song.json'));bt=np.array(base['recEvT']);bpc=[[n['midi']%12 for n in e['notes']] for e in base['events']]
  ev=r['ev'];tt=np.array(r['T'])
  ch=[(t,e) for t,e in zip(tt,ev) if e['c']]
  def agree(shift):
    hit=tot=0
    for k,(t,e) in enumerate(ch):
      t2=ch[k+1][0] if k+1<len(ch) else t+3
      for bt_,pc in zip(bt,bpc):
        if t+shift<=bt_<t2+shift:
          for q in pc:tot+=1;hit+=q in e['pcs']
    return hit/max(1,tot)
  sp=[]
  for k,(t,e) in enumerate(ch):
    t2=ch[k+1][0] if k+1<len(ch) else t+3;hit=tot=0
    for bt_,pc in zip(bt,bpc):
      if t<=bt_<t2:
        for q in pc:tot+=1;hit+=q in e['pcs']
    sp.append((round(t,1),e['name'],tot,round(hit/max(1,tot),2)))
  print('per chord span (time, chord, tab notes, share in chord):');print(' '.join('%s %s %d %.2f |'%x for x in sp))
  print('chord vs tab-note agreement as placed: %.2f'%agree(0),' · if the chords were moved by: ',' '.join('%+.1fs %.2f'%(s,agree(s)) for s in [-21.5,-20.6,-13.7,-6.9,-3.4,3.4,6.9]))
