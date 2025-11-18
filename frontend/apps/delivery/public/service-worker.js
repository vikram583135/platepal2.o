const CACHE_NAME = 'platepal-delivery-v1'
const urlsToCache = [
  '/',
  '/offers',
  '/orders',
  '/earnings',
  '/analytics',
  '/settings',
  '/manifest.json',
]

// Install event - cache resources
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache)
    })
  )
})

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  // In development, bypass SW logic entirely to avoid interfering with Vite
  const isLocal = self.location.hostname === 'localhost' || self.location.hostname === '127.0.0.1'
  if (isLocal) return

  event.respondWith(
    caches.match(event.request).then((response) => {
      // Return cached version or fetch from network
      return response || fetch(event.request).then((response) => {
        // Don't cache non-GET requests or non-200 responses
        if (event.request.method !== 'GET' || response.status !== 200) {
          return response
        }

        // Clone the response
        const responseToCache = response.clone()

        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseToCache)
        })

        return response
      })
    }).catch(() => {
      // Offline fallback for navigation requests
      if (event.request.mode === 'navigate' || event.request.destination === 'document') {
        return caches.match('/')
      }
      // Return a no-content response instead of undefined to satisfy the SW spec
      return new Response(null, { status: 204 })
    })
  )
})

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName)
          }
        })
      )
    })
  )
})

