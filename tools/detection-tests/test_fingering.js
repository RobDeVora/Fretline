const fs=require('fs');const h=fs.readFileSync(process.argv[2],'utf8');
const core=h.match(/<script id="core">([\s\S]*?)<\/script>/)[1];
const f=new Function(core+';return {chordFingers,planFingers};')();
const C={C:[-1,3,2,0,1,0],G:[3,2,0,0,0,3],D:[-1,-1,0,2,3,2],A:[-1,0,2,2,2,0],E:[0,2,2,1,0,0],Am:[-1,0,2,2,1,0],Em:[0,2,2,0,0,0],Dm:[-1,-1,0,2,3,1],F:[1,3,3,2,1,1],Bm:[-1,2,4,4,3,2],B7:[-1,2,1,2,0,2],G7:[3,2,0,0,0,1],C7:[-1,3,2,3,1,0],'A5(355)':[-1,-1,-1,-1,-1,-1].map((x,i)=>i===0?5:i===1?7:i===2?7:-1),'E5 3-5-5':[3,5,5,-1,-1,-1]};
for(const [k,v] of Object.entries(C))console.log(k.padEnd(9),v.map(x=>x<0?'x':x).join(''),'->',f.chordFingers(v).map(x=>x<0?'x':x).join(''));
// single-note lines: A minor pentatonic box at 5, then first-position C major scale, then a shift
const mk=(arr)=>arr.map(([s,fr],i)=>({t:i*0.5,d:0.5,notes:[{s,f:fr}]}));
for(const [name,line] of [['Am penta box 5',[[0,5],[0,8],[1,5],[1,7],[2,5],[2,7],[3,5],[3,7],[4,5],[4,8],[5,5],[5,8]]],['C major 1st pos',[[1,3],[2,0],[2,2],[2,3],[3,0],[3,2],[4,0],[4,1]]],['riff with shift',[[0,3],[0,5],[1,3],[1,5],[3,7],[3,9],[4,8],[4,10]]],['user lead (E string 3/0, A 0/3)',[[0,3],[1,0],[1,3],[0,0],[0,3],[1,0],[1,3]]]]){
  const ev=mk(line);f.planFingers(ev);console.log(name.padEnd(30),ev.map(e=>'EADGBe'[e.notes[0].s]+e.notes[0].f+':'+e.notes[0].fg+'@'+e.hand).join(' '));}
