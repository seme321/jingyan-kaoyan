const CACHE_NAME = 'jingyan-multi-v19';
const PRECACHE_URLS = [
  './',
  './index.html',
  './icon.svg',
  './manifest.webmanifest',
  './data/courses.json',
  './data/announcements.json',
  './data/guestbook.json',
  './data/hhu-814/index.json',
  './data/hhu-814/2026.json',
  './data/hhu-814/2025.json',
  './data/hhu-814/2024.json',
  './data/hhu-814/2023.json',
  './data/hhu-814/2022.json',
  './data/hhu-814/2021.json',
  './data/hhu-814/2020.json',
  './data/hhu-814/2019.json',
  './data/hhu-814/2018.json',
  './data/hhu-814/2017.json',
  './data/hhu-814/2016.json',
  './data/hhu-814/2015.json',
  './data/hhu-814/2014.json',
  './data/hhu-814/2013.json',
  './data/hhu-814/chapters.json',
  './data/hhu-814/formulas.json',
  './data/yzu-849/index.json',
  './data/yzu-849/2024.json',
  './data/yzu-849/2023.json',
  './data/yzu-849/2022.json',
  './data/yzu-849/2021.json',
  './data/yzu-849/2020.json',
  './data/yzu-849/2019.json',
  './data/yzu-849/2018.json',
  './data/yzu-849/2017.json',
  './data/yzu-849/2016.json',
  './data/yzu-849/2015.json',
  './data/yzu-849/2014.json',
  './data/yzu-849/2013.json',
  './data/yzu-849/2012.json',
  './data/yzu-849/2011.json',
  './data/yzu-849/2010.json',
  './data/yzu-849/2008.json',
  './data/yzu-849/2007.json',
  './data/yzu-849/chapters.json',
  './data/yzu-849/formulas.json',
  './mascot/hero.webp',
  './mascot/think.webp',
  './mascot/cheer.webp',
  './mascot/study.webp',
  './mascot/gemini.webp',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    caches.match(event.request).then((cached) => {
      const fetchPromise = fetch(event.request)
        .then((networkResp) => {
          if (networkResp && networkResp.status === 200 && networkResp.type === 'basic') {
            const copy = networkResp.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return networkResp;
        })
        .catch(() => cached);
      return cached || fetchPromise;
    })
  );
});
