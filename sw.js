const CACHE_NAME = 'binance-scanner-v34';
const STATIC_ASSETS = ['./manifest.json', './icon.svg'];

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(STATIC_ASSETS)).catch(() => {}));
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// دائماً جلب أحدث تقرير من الإنترنت أولاً، واستخدام النسخة المحفوظة فقط عند انقطاع الشبكة
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    fetch(event.request, { cache: 'no-store' })
      .then(resp => {
        const clone = resp.clone();
        caches.open(CACHE_NAME).then(c => c.put(event.request, clone)).catch(() => {});
        return resp;
      })
      .catch(() => caches.match(event.request))
  );
});
