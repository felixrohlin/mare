// Maré offline cache. Bump VERSION after changing any file.
const VERSION='mare-v6';
const FILES=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png','./apple-touch-icon.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(VERSION).then(c=>c.addAll(FILES)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==VERSION).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
  const req=e.request;if(req.method!=='GET')return;
  // The app page: try the network first (so updates arrive straight away), fall back to the saved copy when offline.
  if(req.mode==='navigate'){
    e.respondWith(Promise.race([fetch(req),new Promise((_,rej)=>setTimeout(rej,3000))])
      .then(res=>{const copy=res.clone();caches.open(VERSION).then(c=>c.put('./index.html',copy));return res})
      .catch(()=>caches.match('./index.html',{ignoreSearch:true}).then(r=>r||caches.match('./'))));
    return;
  }
  // Voice clip lists: network first so newly generated clips are found; saved copy when offline.
  if(new URL(req.url).pathname.endsWith('/index.json')){
    e.respondWith(fetch(req).then(res=>{if(res.ok){const copy=res.clone();caches.open(VERSION).then(c=>c.put(req,copy))}return res}).catch(()=>caches.match(req,{ignoreSearch:true})));
    return;
  }
  e.respondWith(caches.match(req,{ignoreSearch:true}).then(hit=>hit||fetch(req).then(res=>{
    if(res.ok&&new URL(req.url).origin===location.origin){const copy=res.clone();caches.open(VERSION).then(c=>c.put(req,copy))}
    return res;
  })));
});
