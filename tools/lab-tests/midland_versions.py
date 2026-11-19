# v1.103: rhythm + lead tab (Midland "Put The Hurt On Me"). A guitar track is synthesised from the tab's own guitar notes
# (/tmp/midland_gtr.f32, tab at 1.3 s) and the real tab + chords MIDI files (/tmp/midland_tab.mid, /tmp/midland_chords.mid)
# are run through the Lab. Prints each version: steps, chord steps, longest silent stretch, where it starts.
import json,sys,numpy as np
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page(service_workers='block');errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/lab/stems.html');pg.wait_for_timeout(800)
  r=pg.evaluate("""async()=>{const g=new Float32Array(await (await fetch('http://localhost:8771/midland_gtr.f32')).arrayBuffer());const core=await loadCore();
    const rd=async f=>({info:core.parseMidi(new Uint8Array(await (await fetch('http://localhost:8771/'+f)).arrayBuffer())),fmt:'MIDI',name:f});
    const tab=await rd('midland_tab.mid'),ch=await rd('midland_chords.mid');$('secs').innerHTML+='<option value="0">x</option>';$('secs').value='0';$('ttl').value='Midland test';$('mergeWin').value='auto';
    setSheetFile(tab);$('sheetAs').value='notes';setSheetFile2(ch);const picked=$('sheetPart').options[$('sheetPart').selectedIndex].text;
    let sheet=readSecond(core,readSheet(core,'','auto'),'');const z=new Float32Array(g.length);R.length=0;await makeSheetSong(sheet,g,g,g,g,z,z,g.length);const d=window.__labSong;
    const vs=(d.parts||[{label:'(single)',events:d.events,recEvT:d.recEvT}]).map(q=>({label:q.label,sub:q.sub,n:q.events.length,chords:q.events.filter(e=>e.notes.length>=3).length,T:q.recEvT}));
    return {picked,log:R.join('\\n'),bpm:d.bpm,vs};}""")
  print('tab part picked:',r['picked']);print('\n'.join(l for l in r['log'].split('\n') if l.startswith(('sheet','merge','tempo','song','versions'))))
  for v in r['vs']:
    T=np.array(v['T']);gaps=np.diff(T);k=int(np.argmax(gaps)) if len(gaps) else 0
    print('%-14s %4d steps · %3d chords · starts %.1f s · ends %.1f s · longest silence %.1f s (at %.0f s) · %s'%(v['label'],v['n'],v['chords'],T[0],T[-1],gaps[k] if len(gaps) else 0,T[k] if len(gaps) else 0,v.get('sub')))
  print('errors',errs);b.close()
