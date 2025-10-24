// Minimal service worker for FS Randoms Trainer
self.addEventListener("install", event => {
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  self.clients.claim();
});

// Optional: cache the shell for faster reloads
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.open("fs-trainer-v1").then(cache => {
      return cache.match(event.request).then(response => {
        return response || fetch(event.request).then(networkResponse => {
          // Cache static files only (PNG, JS, CSS)
          if (event.request.url.match(/\.(png|jpg|jpeg|js|css|html)$/)) {
            cache.put(event.request, networkResponse.clone());
          }
          return networkResponse;
        });
      });
    })
  );
});
