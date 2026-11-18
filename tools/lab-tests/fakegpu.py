import sys
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page(viewport={'width':412,'height':900});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/lab/stems.html?ortbase=http://localhost:8771/&modelurl=http://localhost:8771/dummy.onnx');pg.wait_for_timeout(3500)
  pg.evaluate("""async()=>{await loadScript(ORT_BASE+'ort.webgpu.min.js');ort.env.wasm.wasmPaths=ORT_BASE;const C=ort.InferenceSession.create.bind(ort.InferenceSession);let gpuRuns=0;
    ort.InferenceSession.create=async(m,o)=>{const ep=o.executionProviders[0];const gpu=(ep&&ep.name||ep)==='webgpu';if(gpu)window.__forced=(ep.forceCpuNodeNames||[]).length;
      const s=await C(m,Object.assign({},o,{executionProviders:['wasm']}));if(!gpu)return s;const r=s.run.bind(s);
      s.run=async(f)=>{gpuRuns++;if(gpuRuns===2)throw new Error("Failed to execute 'mapAsync' on 'GPUBuffer': [Device] is lost.");const out=await r(f);if(gpuRuns>=4){const d=out[s.outputNames[0]].data;for(let i=0;i<d.length;i+=7)d[i]=NaN;}return out;};return s;};}""")
  pg.set_input_files('#file',sys.argv[1]);pg.select_option('#secs','30');pg.select_option('#be','auto');pg.click('#go');pg.wait_for_function('window.__labDone',timeout=600000)
  print(pg.text_content('#log'))
  print(pg.evaluate("""async()=>{const f=document.getElementById('file').files[0];const ac=new AudioContext({sampleRate:44100});const b=await ac.decodeAudioData(await f.arrayBuffer());const L=b.getChannelData(0);
    const g=new Int16Array(await (await fetch(document.getElementById('aGtr').src)).arrayBuffer(),44);let e=0,z=0;for(let i=1000;i<g.length/2-1000;i+=97){e=Math.max(e,Math.abs(g[2*i]/32768-0.3*L[i]));}return 'max error guitar '+e.toFixed(4);}"""))
  print('errors',errs);b.close()
