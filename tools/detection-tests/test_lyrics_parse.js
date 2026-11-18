const fs=require('fs');const h=fs.readFileSync(process.argv[2],'utf8');
const core=h.match(/<script id="core">([\s\S]*?)<\/script>/)[1];
const f=new Function(core+';return {parseChordSheet};')();
const show=(name,txt)=>{const ev=f.parseChordSheet(txt,4);console.log('== '+name+': '+ev.length+' chords',ev.map(e=>e.label||e.chord).join(' '));
  for(const L of ev.lyrics||[])console.log('  t0='+L.t0+' | '+L.segs.map(s=>s.t+':'+JSON.stringify(s.text)).join(' '));};
show('chordpro',`{title: Amazing Grace}
{start_of_verse}
Verse 1
A[G]mazing [G7]grace, how [C]sweet the [G]sound
That [G]saved a wretch like [D]me
{end_of_verse}
[Chorus]
I [G]once was [G7]lost but [C]now am [G]found`);
show('over',`Verse 1:
G          C          G
Amazing grace, how sweet the sound
        G              D
That saved a wretch like me

Chorus x2
G    C   G   D  (x2)
I once was lost but now am found
G  D  G

Was blind, but now I see`);
show('no lyrics',`G G C G\nG G D D`);
