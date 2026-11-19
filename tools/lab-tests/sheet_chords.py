# v1.83: Lab with a chord sheet ("G C D Em G C") for a synthetic strummed track (/tmp/chordtest/chords90.wav:
# 2 s silence, then G 2 bars, C 1, D 1, Em 2, G 1, C 1 at 90 BPM, 8th-note strums). The sheet has no lengths, so
# the change times must come from the recording. Then the same with "follow the recording's strums".
import json,sys
from playwright.sync_api import sync_playwright
T=json.load(open('/tmp/chordtest/truth.json'))
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');ctx=b.new_context(viewport={'width':412,'height':900},service_workers='block')
  for mode in ('changes','strums'):
    pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('http://localhost:8769/lab/stems.html?ortbase=http://localhost:8771/&modelurl=http://localhost:8771/dummy.onnx');pg.wait_for_timeout(800)
    pg.set_input_files('#file','/tmp/chordtest/chords90.wav');pg.select_option('#secs','0');pg.select_option('#be','wasm');pg.fill('#ttl','Chords '+mode)
    pg.click('#sheetBox summary')
    if __import__('os').environ.get('MIDI'):pg.set_input_files('#sheetFile',__import__('os').environ['MIDI']);pg.wait_for_timeout(1500);pg.select_option('#sheetAs','chords')
    else:pg.fill('#sheet',__import__('os').environ.get('SHEET','Intro\nG  C  D  Em\nG  C'))
    pg.select_option('#strumMode',mode);pg.click('#go');pg.wait_for_function('window.__labDone',timeout=900000)
    print('\n'.join(l for l in pg.text_content('#log').split('\n') if l.startswith(('sheet','tempo','song','ERROR'))))
    d=pg.evaluate('window.__labSong');ev=d['events'];spb=60/d['bpm']
    names=[(e.get('chord') or e.get('label'),round(d['recOffset']+e['t']*spb,3)) for e in ev]
    if mode=='changes':
      errs_ms=[int(abs(a[1]-b[1])*1000) for a,b in zip(names,T['truth'])];print('chords',[n for n,_ in names],'· change-time errors (ms)',errs_ms,'· bpm',d['bpm'])
    else:
      print('strums',len(ev),'(recording has',T['strums'],') · dirs',''.join(e['strum'] for e in ev[:16]),'· names',[n for n,_ in names][:3])
    print('errors',errs);pg.close()
  b.close()
