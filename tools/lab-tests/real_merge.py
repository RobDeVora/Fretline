# v1.90 on a real song: the guitar stem of "Thought You Should Know" (/tmp/tysk_full_gtr.f32, 44.1 kHz mono, from a
# Demucs run), its MIDI (/tmp/tysk.mid) and the song the Lab made from the MIDI alone (/tmp/tysk_full_song.json,
# whose recEvT is the truth: median 3 ms from the MIDI's own timing). The MIDI stands in for both sheets: steps A..B
# of it are pasted as a solo-only tab (no timing), and the chord sheet is the MIDI's chord chart. Does the Lab find
# where the tab goes, and are the tab's notes on the right picks?  python3 real_merge.py [A] [B] [mergeWin] [from to]  (from / to typed, like the Lab's boxes)
import json,sys,numpy as np
from playwright.sync_api import sync_playwright
A=int(sys.argv[1]) if len(sys.argv)>1 else 300;B=int(sys.argv[2]) if len(sys.argv)>2 else 348;WIN=sys.argv[3] if len(sys.argv)>3 else 'tab';FT=(sys.argv[4],sys.argv[5]) if len(sys.argv)>5 else ('','')
base=json.load(open('/tmp/tysk_full_song.json'));T=np.array(base['recEvT'])
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');ctx=b.new_context(service_workers='block');pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/lab/stems.html');pg.wait_for_timeout(800)
  r=pg.evaluate("""async([a,b,win,ft])=>{const g=new Float32Array(await (await fetch('http://localhost:8771/tysk_full_gtr.f32')).arrayBuffer());
    const core=await loadCore();const info=core.parseMidi(new Uint8Array(await (await fetch('http://localhost:8771/tysk.mid')).arrayBuffer()));setSheetFile({info,fmt:'MIDI',name:'tysk.mid'});
    $('secs').innerHTML+='<option value="0">x</option>';$('secs').value='0';$('ttl').value='TYSK merge';$('mergeWin').value=win;$('tabFrom').value=ft[0];$('tabTo').value=ft[1];
    const full=readSheet(core,'','auto');const part=info.parts[+$('sheetPart').value];const bpb=info.bpb||4;
    const cc=core.chordChart(core.eventsFromNotes(part.notes,{bpb,shift:0}),bpb,info.bpm);const names=cc.events.map(e=>e.chord).filter(Boolean);
    setSheetFile(null);const chords=readSheet(core,names.join('  '),'chords');
    const tab={kind:'tab',events:full.events.slice(a,b),capo:0,tuning:full.tuning,builtTuning:full.builtTuning};tab.also=chords;
    const z=new Float32Array(g.length);R.length=0;await makeSheetSong(tab,g,g,g,g,z,z,g.length);const d=window.__labSong;
    return {fullSteps:full.events.length,chordNames:names.length,log:R.join('\\n'),bpm:d.bpm,events:d.events.map(e=>({c:!!(e.chord||e.strum),n:e.notes.length})),T:d.recEvT};}""",[A,B,WIN,list(FT)])
  print('MIDI steps',r['fullSteps'],'(baseline has',len(T),') · chord names',r['chordNames'],' · tab = steps',A,'to',B)
  print('\n'.join(l for l in r['log'].split('\n') if l.startswith(('sheet','merge','tempo','song'))))
  ts=np.array([t for t,e in zip(r['T'],r['events']) if not e['c']]);truth=T[A:B]
  print('truth solo from %.2f to %.2f s;'%(truth[0],truth[-1]),'tab steps kept',len(ts),'of',B-A,'chord steps',sum(1 for e in r['events'] if e['c']))
  if len(ts)==len(truth):d=np.abs(ts-truth)*1000;print('tab note-time error vs the MIDI-timed song: median %d ms, 90%% %d ms, max %d ms, %d of %d within 50 ms'%(np.median(d),np.percentile(d,90),d.max(),(d<=50).sum(),len(d)))
  else:
    near=np.array([np.min(np.abs(truth-t)) for t in ts])*1000;print('tab step count differs (%d vs %d); distance of each placed step to the nearest true time: median %d ms, %d of %d within 50 ms, first times'%(len(ts),len(truth),np.median(near),(near<=50).sum(),len(ts)),np.round(ts[:5],2),'truth',truth[:5])
  print('errors',errs);b.close()
