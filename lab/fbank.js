/* kaldi-style 80-bin log-mel filterbank (matches kaldi_native_fbank defaults: povey window, preemph .97, DC removal, snip_edges=false) */
function makeFbank(){const SR=16000,FL=400,FS=160,NFFT=512,NB=80,LOW=20,HIGH=SR/2;
  const win=new Float32Array(FL);for(let i=0;i<FL;i++)win[i]=Math.pow(0.5-0.5*Math.cos(2*Math.PI*i/(FL-1)),0.85);
  const mel=f=>1127*Math.log(1+f/700),imel=m=>700*(Math.exp(m/1127)-1);
  const nfb=NFFT/2;const mlo=mel(LOW),mhi=mel(HIGH),dm=(mhi-mlo)/(NB+1);const fb=[];
  for(let b=0;b<NB;b++){const l=mlo+b*dm,c=mlo+(b+1)*dm,r=mlo+(b+2)*dm;const w=new Float32Array(nfb);
    for(let i=0;i<nfb;i++){const m=mel(i*SR/NFFT);if(m>l&&m<r)w[i]=m<=c?(m-l)/(c-l):(r-m)/(r-c);}fb.push(w);}
  const cosT=new Float32Array(NFFT/2),sinT=new Float32Array(NFFT/2);for(let i=0;i<NFFT/2;i++){cosT[i]=Math.cos(2*Math.PI*i/NFFT);sinT[i]=-Math.sin(2*Math.PI*i/NFFT);}
  const rev=new Uint16Array(NFFT);for(let i=0;i<NFFT;i++){let r=0,x=i;for(let b=0;b<9;b++){r=(r<<1)|(x&1);x>>=1;}rev[i]=r;}
  const re=new Float32Array(NFFT),im=new Float32Array(NFFT);
  function fft(){for(let i=0;i<NFFT;i++){const j=rev[i];if(j>i){let t=re[i];re[i]=re[j];re[j]=t;t=im[i];im[i]=im[j];im[j]=t;}}
    for(let len=2;len<=NFFT;len<<=1){const h=len>>1,st=NFFT/len;for(let i=0;i<NFFT;i+=len)for(let k=0;k<h;k++){const wr=cosT[k*st],wi=sinT[k*st];const a=i+k,b=a+h;const xr=re[b]*wr-im[b]*wi,xi=re[b]*wi+im[b]*wr;re[b]=re[a]-xr;im[b]=im[a]-xi;re[a]+=xr;im[a]+=xi;}}}
  return function(x){const n=x.length;const nf=Math.floor((n+FS/2)/FS);const out=new Float32Array(nf*NB);const fr=new Float32Array(FL);const EPS=1.1920929e-7;
    for(let f=0;f<nf;f++){const start=Math.floor(f*FS+FS/2-FL/2);
      for(let i=0;i<FL;i++){let p=start+i;if(p<0)p=-p-1;if(p>=n)p=2*n-1-p;if(p<0)p=0;fr[i]=(x[p]||0)*32768;}
      let mean=0;for(let i=0;i<FL;i++)mean+=fr[i];mean/=FL;for(let i=0;i<FL;i++)fr[i]-=mean;
      for(let i=FL-1;i>0;i--)fr[i]-=0.97*fr[i-1];fr[0]-=0.97*fr[0];
      for(let i=0;i<NFFT;i++){re[i]=i<FL?fr[i]*win[i]:0;im[i]=0;}fft();
      for(let b=0;b<NB;b++){let s=0;const w=fb[b];for(let i=0;i<nfb;i++)if(w[i])s+=w[i]*(re[i]*re[i]+im[i]*im[i]);out[f*NB+b]=Math.log(Math.max(s,EPS));}}
    return {data:out,frames:nf,bins:NB};};}
if(typeof module!=='undefined')module.exports={makeFbank};
