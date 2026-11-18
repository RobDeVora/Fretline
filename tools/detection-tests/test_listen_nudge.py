from playwright.sync_api import sync_playwright
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':412,'height':915});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(600)
  r=pg.evaluate("""async()=>{settings.backing=false;settings.listenTuned=false;openSong({id:'m-x',cat:'mine',title:'X',bpm:90,bpb:4,kind:'chords',cb:4,src:'G C D G',capo:0,strum:''});document.querySelectorAll('.overlay.show').forEach(o=>o.classList.remove('show'));
    const L=async()=>{$('#btnListen').click();await new Promise(r=>setTimeout(r,250));const v=$('#lsTune').style.display;return v;};const stop=async()=>{$('#btnListen').click();await new Promise(r=>setTimeout(r,100));};
    const first=await L();$('#lsDone').click();const afterDone=$('#lsTune').style.display;await stop();
    const again=await L();await stop();
    $('#sDelEar').onclick();const asked=await L();await stop();
    return {first,afterDone,again,asked,tuned:settings.listenTuned};}""")
  print(r,errs);b.close()
