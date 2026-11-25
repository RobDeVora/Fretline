# v1.151: run the Lab's Basic Pitch (with pitch-bend contours) over IDMT-SMT-Guitar files; writes /tmp/idmt/bp_<file>.json (resumes). Usage: /tmp/withsrv.sh python3 bp_bends.py
import json,os,base64,numpy as np,librosa
from playwright.sync_api import sync_playwright
D='/tmp/idmt/';need=json.load(open(D+'need.json'))
JS="""async(b64)=>{if(!window.BP)await loadScript('basic-pitch/basic-pitch.bundle.js');await BP.tf.setBackend('cpu');await BP.tf.ready();
 const bin=atob(b64),u=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)u[i]=bin.charCodeAt(i);const x=new Float32Array(u.buffer);
 const bp=new BP.BasicPitch('basic-pitch/model.json');const fr=[],on=[],co=[];await bp.evaluateModel(x,(f,o,c)=>{fr.push(...f);on.push(...o);co.push(...c);},()=>{});
 return BP.noteFramesToTime(BP.addPitchBendsToNoteEvents(co,BP.outputToNotesPoly(fr,on,0.5,0.3,5))).map(n=>({m:n.pitchMidi,t:n.startTimeSeconds,d:n.durationSeconds,a:n.amplitude,b:n.pitchBends||[]}));}"""
with sync_playwright() as p:
    br=p.chromium.launch();pg=br.new_page();pg.goto('http://localhost:8769/lab/stems.html');pg.wait_for_timeout(1500)
    for k,b in enumerate(sorted(need)):
        out=D+'bp_'+b+'.json'
        if os.path.exists(out) or not os.path.exists(D+b+'.wav'):continue
        y,_=librosa.load(D+b+'.wav',sr=22050,mono=True)
        notes=pg.evaluate(JS,base64.b64encode(y.astype(np.float32).tobytes()).decode())
        json.dump(notes,open(out,'w'));print(k,b,len(y)/22050,'s',len(notes),'notes',flush=True)
    br.close()
