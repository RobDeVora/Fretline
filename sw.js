// Fretline service worker: always tries the network first so updates you
// upload to GitHub show up on the next launch; falls back to the saved copy offline.
const CACHE = 'fretline-v39';
const SHARE = 'fretline-share'; // holds a song shared from another app until the page picks it up
const CORE = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png', './icon-maskable-512.png', './apple-touch-icon.png'];
self.addEventListener('install', e => {
  // cache each file separately so one missing file can't block installation
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(CORE.map(u => c.add(u).catch(() => {})))).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE && k !== SHARE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  const url = new URL(req.url);
  // "Share → Fretline" from another app (Android): keep what was shared, then open the import screen
  if (req.method === 'POST' && url.origin === self.location.origin && url.pathname.endsWith('/share-target')) {
    e.respondWith((async () => {
      try {
        const fd = await req.formData();
        const c = await caches.open(SHARE);
        await c.put('./shared-data', new Response(JSON.stringify({ title: fd.get('title') || '', text: fd.get('text') || '', url: fd.get('url') || '' }), { headers: { 'Content-Type': 'application/json' } }));
        const f = fd.get('file');
        if (f && typeof f !== 'string' && f.size) await c.put('./shared-file', new Response(f, { headers: { 'X-File-Name': encodeURIComponent(f.name || 'shared.txt') } }));
        else await c.delete('./shared-file');
      } catch (err) {}
      return Response.redirect(new URL('./?shared=1', self.registration.scope).href, 303);
    })());
    return;
  }
  if (req.method !== 'GET') return;
  const sameOrigin = url.origin === self.location.origin;
  const isLib = /cdn\.jsdelivr\.net|cdnjs\.cloudflare\.com|unpkg\.com/.test(url.hostname);
  if (!sameOrigin && !isLib) return;
  if (url.searchParams.has('check')) return; // "Check for updates" always asks GitHub directly
  e.respondWith(
    fetch(req, sameOrigin ? { cache: 'no-cache' } : {}).then(res => {
      if (res && (res.ok || res.type === 'opaque')) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req).then(r => r || (req.mode === 'navigate' ? caches.match('./index.html') : undefined)))
  );
});
