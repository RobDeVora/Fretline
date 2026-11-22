const fs=require('fs');eval(fs.readFileSync('fns.js','utf8')+';globalThis.vibMeasure=vibMeasure;');
globalThis.G={};const ev=JSON.parse(fs.readFileSync('ev_list.json'));const out=[];const cache={};
for(const e of ev){const buf=cache[e.f]||(cache[e.f]=new Float32Array(fs.readFileSync(e.f+'.f32').buffer.slice(0)));const sr=e.sr;
  const t0=(e.on+0.75)*1000,t1=Math.min(e.off,e.on+1.9)*1000;G.vibC=[];
  for(let t=e.on*1000;t<=t1+50;t+=16.7){const end=Math.round(t/1000*sr);if(end<2048||end>buf.length)continue;const sub=buf.subarray(end-2048,end);let q=0;for(const x of sub)q+=x*x;if(Math.sqrt(q/2048)<0.003)continue;const f=yin(sub,sr);if(f<=0||f>1400)continue;G.vibC.push(t,12*Math.log2(f/440)*100);}
  const r=vibMeasure(t0,t1);out.push({f:e.f,ex:e.ex,on:e.on,d:r?r.d:null,hz:r?r.f:null});}
fs.writeFileSync('app_rows.json',JSON.stringify(out));
