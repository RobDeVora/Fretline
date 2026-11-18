from playwright.sync_api import sync_playwright
with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--autoplay-policy=no-user-gesture-required']);pg=b.new_page(viewport={'width':412,'height':915},device_scale_factor=2);errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(600)
  r=pg.evaluate("""async()=>{settings.soundDelay=190;settings.backing=false;openSong({id:'m-x',cat:'mine',title:'X',bpm:90,bpb:4,kind:'chords',cb:4,src:'G C D G',capo:0,strum:''});document.querySelectorAll('.overlay.show').forEach(o=>o.classList.remove('show'));
    const before=$('#lsTune').style.display;$('#btnListen').click();await new Promise(r=>setTimeout(r,300));const during=$('#lsTune').style.display,v0=$('#lsVal').textContent;
    $('#lsEarly').click();$('#lsEarly').click();$('#lsEarly').click();const v1=$('#lsVal').textContent,saved=settings.soundDelay;$('#lsLate').click();
    const v2=$('#lsVal').textContent;$('#btnListen').click();await new Promise(r=>setTimeout(r,100));return {before,during,v0,v1,saved,v2,after:$('#lsTune').style.display};}""")
  print(r,errs);b.close()
