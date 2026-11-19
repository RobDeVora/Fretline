/* Fretline song storage (v1.101). My songs used to live in localStorage, which holds only about 5 MB in the app.
   They now live in IndexedDB, which uses the phone's own storage (hundreds of MB and more). One record per song
   (its JSON text) plus one "order" record, so changing one song writes only that song.
   Shared by the main page and the Lab. If IndexedDB is unavailable it falls back to localStorage as before.
   SongDB.load()      → Promise; call once before using the rest (moves old localStorage songs over, once)
   SongDB.songs()     → the list (newest first)
   SongDB.save(list)  → Promise; stores the list (only changed songs are written, removed ones are deleted)
   SongDB.add(def) / SongDB.update(def) → Promise (for the Lab)
   SongDB.ids()       → Promise of the saved order, read fresh from the database (to notice another page's changes) */
(function(){
  const DB='fretline-songs',ST='songs',LS='fretline:songs';
  let db=null,ready=false,list=[],loaded=null,chain=Promise.resolve(),sums=new Map(),useLS=false;
  const strip=(k,v)=>k==='_built'?undefined:v;
  const sum=s=>{let h=2166136261;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619);}return s.length+':'+(h>>>0);};
  const req=r=>new Promise((res,rej)=>{r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error);});
  function open(){return new Promise((res,rej)=>{if(!window.indexedDB)return rej(new Error('no IndexedDB'));const r=indexedDB.open(DB,1);
    r.onupgradeneeded=()=>{r.result.createObjectStore(ST,{keyPath:'id'});r.result.createObjectStore('meta');};r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error);r.onblocked=()=>rej(new Error('blocked'));});}
  function legacy(){try{return JSON.parse(localStorage.getItem(LS)||'[]');}catch(e){return [];}}
  async function readAll(){const t=db.transaction([ST,'meta'],'readonly');const recs=await req(t.objectStore(ST).getAll());const order=(await req(t.objectStore('meta').get('order')))||[];
    const by=new Map(recs.map(r=>[r.id,r.json]));const out=[],seen=new Set();
    for(const id of order){const j=by.get(id);if(j==null)continue;try{out.push(JSON.parse(j));sums.set(id,sum(j));seen.add(id);}catch(e){}}
    for(const [id,j] of by){if(seen.has(id))continue;try{out.push(JSON.parse(j));sums.set(id,sum(j));}catch(e){}}
    return out;}
  async function persist(songs){ /* write what changed, delete what is gone, then the order */
    const writes=[],keep=new Set();
    for(const s of songs){const j=JSON.stringify(s,strip);keep.add(s.id);const h=sum(j);if(sums.get(s.id)!==h)writes.push([s.id,j,h]);}
    const gone=[...sums.keys()].filter(id=>!keep.has(id));
    await new Promise((res,rej)=>{const t=db.transaction([ST,'meta'],'readwrite');const os=t.objectStore(ST);
      for(const [id,j] of writes)os.put({id,json:j});for(const id of gone)os.delete(id);t.objectStore('meta').put(songs.map(s=>s.id),'order');
      t.oncomplete=()=>res();t.onerror=()=>rej(t.error||new Error('write failed'));t.onabort=()=>rej(t.error||new Error('storage full or blocked'));});
    for(const [id,,h] of writes)sums.set(id,h);for(const id of gone)sums.delete(id);}
  const SongDB=window.SongDB={ok:false,onError:null,
    load(){return loaded||(loaded=(async()=>{
      try{db=await open();}catch(e){useLS=true;list=legacy();return list;}
      try{list=await readAll();const old=legacy();
        if(old.length){ /* songs saved the old way (or by an older Lab page): bring them over, once */
          const have=new Set(list.map(s=>s.id)),fresh=old.filter(s=>s&&s.id&&!have.has(s.id));list=[...fresh,...list];
          await persist(list);try{localStorage.removeItem(LS);}catch(e){}}
        SongDB.ok=true;
        try{if(navigator.storage&&navigator.storage.persist)navigator.storage.persist();}catch(e){}
      }catch(e){useLS=true;list=legacy().length?legacy():list;}
      ready=true;return list;})());},
    songs(){return list;},
    save(next){if(!ready)return Promise.reject(new Error('songs not loaded yet'));list=next;
      if(useLS){try{localStorage.setItem(LS,JSON.stringify(next,strip));return Promise.resolve();}catch(e){if(SongDB.onError)SongDB.onError(e);return Promise.reject(e);}}
      const p=chain.then(()=>persist(next));chain=p.catch(()=>{});
      return p.catch(e=>{if(SongDB.onError)SongDB.onError(e);throw e;});},
    async add(def){await SongDB.load();return SongDB.save([def,...list.filter(s=>s.id!==def.id)]);},
    async update(def){await SongDB.load();const i=list.findIndex(s=>s.id===def.id);const next=list.slice();if(i>=0)next[i]=def;else next.unshift(def);return SongDB.save(next);},
    async ids(){if(useLS||!db)return legacy().map(s=>s.id);return req(db.transaction('meta','readonly').objectStore('meta').get('order')).then(o=>o||[]);}
  };
})();
