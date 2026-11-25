# v1.149: Spotify hand-off check (needs the test server on 8769): link regex, Lab prefill, banner. Run: /tmp/withsrv.sh python3 test_spotify_handoff.py
import sys
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page();msgs=[];pg.on('console',lambda m:msgs.append(m.text[:200]));pg.on('pageerror',lambda e:msgs.append('ERR '+str(e)[:300]));pg.goto('http://localhost:8769/index.html');pg.wait_for_timeout(1500)
    r=pg.evaluate("""()=>[spotifyLinkOf('Check this out https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC?si=abc123'),spotifyLinkOf('https://open.spotify.com/intl-de/album/1ABC'),spotifyLinkOf('https://example.com/x'),spotifyLinkOf('')]""")
    print(r)
    print(pg.evaluate("(async()=>{const o=localStorage.setItem;let v=null;localStorage.setItem=function(k,x){v=[k,x];return o.call(localStorage,k,x)};try{await Promise.race([spotifyHandoff('https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC','Wonderwall - song and lyrics by Oasis | Spotify'),new Promise(r=>setTimeout(r,500))])}catch(e){v='EXC '+e};return JSON.stringify(v)})()"))
    pg.wait_for_url('**/lab/stems.html',timeout=8000);pg.wait_for_timeout(2500)
    print(pg.url);print('ttl=',pg.input_value('#ttl'));print('banner=',pg.evaluate("document.querySelector('#ttl').previousElementSibling.textContent.slice(0,120)"),pg.evaluate("window.__spLink"))
    print('key cleared:',pg.evaluate("localStorage.getItem('fretline:labSpotify')"))
    print('lab page has code:',pg.evaluate("fetch('/lab/stems.html').then(r=>r.text()).then(t=>t.includes('labSpotify'))"))
    print(msgs[:8]);print('sw',pg.evaluate("navigator.serviceWorker&&navigator.serviceWorker.controller?'ctl':'none'"))
    b.close()
