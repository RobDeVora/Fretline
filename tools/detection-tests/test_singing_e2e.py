import sys,json
from playwright.sync_api import sync_playwright
SHEET="""[G]Down in the [C]valley, the [G]valley so [D]low
[G]Hang your head [C]over, hear the [D]wind [G]blow"""
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--autoplay-policy=no-user-gesture-required'])
  pg=b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8768/index.html');pg.wait_for_timeout(600)
  r=pg.evaluate("""async(SHEET)=>{await ensureAudio();const out={};
    const played=[];voxNote=(m,t,d)=>played.push(m);
    const run=async(beats)=>{played.length=0;G.mode='play';G.playing=true;G.waiting=false;G.clock=-1;voxSeek();for(let c=-1;c<beats;c+=0.25){G.clock=c;voxTick();}G.playing=false;return played.length;};
    // A: library tune
    const L=await loadLibrary();await getLibSong(L.find(x=>x.id==='tr-amazinggrace'));document.querySelectorAll('.overlay.show').forEach(o=>o.classList.remove('show'));
    out.lib={src:G.voxSrc,notes:G.vox&&G.vox.length,lines:songLyrics(G.song).map(l=>l.segs.map(s=>s.text).join('')),singBtn:$('#singBtn').style.display,piano:G.song.noPianoTune,scheduled:await run(48),first:G.vox&&G.vox.slice(0,3)};
    settings.vocalLibrary=false;setupBand();out.libOff={vox:!!G.vox,lyrics:!!songLyrics(G.song),btn:(syncSingBtn(),$('#singBtn').style.display)};settings.vocalLibrary=true;
    // B: chord sheet with words -> made-up tune
    openSong({id:'m-sheet',cat:'mine',title:'Valley',bpm:90,bpb:4,kind:'chords',cb:4,src:SHEET,capo:0,strum:''});document.querySelectorAll('.overlay.show').forEach(o=>o.classList.remove('show'));
    const v=G.vox||[];out.made={src:G.voxSrc,n:v.length,syll:songLyrics(G.song).reduce((a,l)=>a+syllableSpots(l.segs.map(s=>s.text).join('')).length,0),range:[Math.min(...v.map(x=>x.midi)),Math.max(...v.map(x=>x.midi))],
      inSong:v.every(x=>x.t>=0&&x.t+x.d<=G.song.length+0.01),ordered:v.every((x,i)=>!i||x.t>v[i-1].t-1e-9),names:v.slice(0,10).map(x=>midiToName(x.midi)+'@'+x.t).join(' '),scheduled:await run(G.song.length)};
    settings.vocalMadeUp=false;setupBand();out.madeOff=!!G.vox;settings.vocalMadeUp=true;
    settings.vocalGuide=false;setupBand();out.guideOff={vox:!!G.vox,lyrics:!!songLyrics(G.song)};settings.vocalGuide=true;
    settings.sing=false;setupBand();out.singOff={active:voxActive(),scheduled:await run(8)};settings.sing=true;setupBand();
    // C: MIDI with lyric events
    const mb=new Uint8Array(await (await fetch('twinkle.mid')).arrayBuffer());const mi=parseMidi(mb);
    impFile={...mi,fmt:'MIDI',name:'twinkle.mid'};const iv=importVocal({half:false});
    out.midi={parts:mi.parts.map(x=>x.label),vocal:mi.vocal&&mi.vocal.label,words:mi.vocal&&mi.vocal.words&&mi.vocal.words.length,first:iv.vocal&&iv.vocal.slice(0,2),lines:iv.lyrics&&iv.lyrics.map(l=>l.segs.map(s=>s.text).join('')+' @'+l.t0)};
    // D: MusicXML with lyrics
    const xi=parseMusicXML(await (await fetch('song.musicxml')).text());impFile={...xi,fmt:'MusicXML',name:'song.musicxml'};const xv=importVocal({half:false});
    out.xml={parts:xi.parts.map(x=>x.label),vocal:xi.vocal&&xi.vocal.label,lines:xv.lyrics&&xv.lyrics.map(l=>l.segs.map(s=>s.text).join('')),notes:xv.vocal&&xv.vocal.length};
    impFile=null;return out;}""",SHEET)
  print(json.dumps(r,indent=1));print('errors',errs);b.close()
