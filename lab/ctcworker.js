/* v1.125: runs the speech model for ONE listen (the mix, or the singing alone) in its own thread, so the two listens run side by side */
self.onmessage=async e=>{const {sig,model,ortBase,tag,id}=e.data;
  try{importScripts(ortBase+'ort.webgpu.min.js');importScripts('fbank.js');
    ort.env.wasm.wasmPaths=ortBase;ort.env.wasm.numThreads=1;const sess=await ort.InferenceSession.create(model,{executionProviders:['wasm']});
    const fb=makeFbank(),CH=16000*30,V=1025,parts=[];let T=0;
    for(let s=0;s<sig.length;s+=CH){self.postMessage({id,prog:s/sig.length});const seg=sig.subarray(s,Math.min(sig.length,s+CH));if(seg.length<1600)break;
      const f=fb(seg),nb=f.bins,nf=f.frames;const m=new Float32Array(nb),sd=new Float32Array(nb);
      for(let b=0;b<nb;b++){let a=0;for(let i=0;i<nf;i++)a+=f.data[i*nb+b];m[b]=a/nf;}
      for(let b=0;b<nb;b++){let a=0;for(let i=0;i<nf;i++){const d=f.data[i*nb+b]-m[b];a+=d*d;}sd[b]=Math.sqrt(a/nf);}
      const inp=new Float32Array(nb*nf);for(let i=0;i<nf;i++)for(let b=0;b<nb;b++)inp[b*nf+i]=(f.data[i*nb+b]-m[b])/(sd[b]+1e-5);
      const o=await sess.run({audio_signal:new ort.Tensor('float32',inp,[1,nb,nf]),length:new ort.Tensor('int64',BigInt64Array.from([BigInt(nf)]),[1])});
      const lp=o[sess.outputNames[0]];parts.push(lp.data.slice());T+=lp.dims[1];}
    const all=new Float32Array(T*V);let off=0;for(const p of parts){all.set(p,off);off+=p.length;}
    try{sess.release&&sess.release();}catch(_){}
    self.postMessage({id,all,T},[all.buffer]);
  }catch(err){self.postMessage({id,error:String(err&&err.message||err)});}};
