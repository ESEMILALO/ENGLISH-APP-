/* Word Log service worker.
 *
 * Two jobs, and they pull against each other:
 *
 *   1. Make the app installable and let it open when the laptop is off.
 *   2. Never show you yesterday's words after you rebuilt the spreadsheet.
 *
 * So the page itself is fetched from the network first and only falls
 * back to the cache when the network does not answer -- rebuild, pull
 * down to refresh, and the new words are there. The icons and the
 * manifest, which change only when you regenerate them, are served from
 * the cache first and quietly refreshed behind your back.
 *
 * Your progress is not in here. That lives in localStorage on whichever
 * device you are holding, exactly as before.
 */

const VERSION = 'wordlog-v1';
const SHELL = [
  '/',
  '/manifest.webmanifest',
  '/icon-192.png',
  '/icon-512.png',
  '/icon-maskable-512.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(VERSION)
      // One missing icon should not stop the whole worker installing.
      .then(cache => Promise.allSettled(SHELL.map(url => cache.add(url))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== VERSION).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

// The copy we already hold, whatever the network just did.
function fromCache(request, lastResort) {
  return caches.match(request)
    .then(hit => hit || caches.match('/'))
    .then(hit => hit || lastResort || Response.error());
}

// Network first, cache as the safety net. Used for the page itself.
function freshFirst(request) {
  return fetch(request)
    .then(response => {
      // A reachable laptop that is not running the server answers 502,
      // and as far as fetch is concerned that succeeded -- it rejects
      // only when it cannot reach anything at all. So an error status
      // has to be caught here too, or the app would show a proxy error
      // page instead of the copy it is already holding.
      if (!response || !response.ok) return fromCache(request, response);
      const copy = response.clone();
      caches.open(VERSION).then(cache => cache.put(request, copy));
      return response;
    })
    .catch(() => fromCache(request, null));
}

// Cache first, refreshed in the background. Used for icons and the manifest.
function cacheFirst(request) {
  return caches.match(request).then(hit => {
    const network = fetch(request)
      .then(response => {
        if (!response || !response.ok) return hit || response;
        const copy = response.clone();
        caches.open(VERSION).then(cache => cache.put(request, copy));
        return response;
      })
      .catch(() => hit || Response.error());
    return hit || network;
  });
}

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  // Only our own origin. The Google Fonts request goes straight out; if
  // it fails the app falls back to system fonts on its own.
  if (url.origin !== self.location.origin) return;

  if (request.mode === 'navigate' || url.pathname === '/' ||
      url.pathname.endsWith('.html')) {
    event.respondWith(freshFirst(request));
    return;
  }
  event.respondWith(cacheFirst(request));
});
