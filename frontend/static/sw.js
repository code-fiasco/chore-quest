const CACHE = 'chore-quest-v2';
const SHELL = ['/manifest.json', '/icon-192.svg', '/icon-512.svg'];

self.addEventListener('install', (event) => {
	event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)));
	self.skipWaiting();
});

self.addEventListener('activate', (event) => {
	event.waitUntil(
		caches.keys().then((keys) =>
			Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))
		)
	);
	self.clients.claim();
});

function isAppShellRequest(request, url) {
	return (
		request.mode === 'navigate' ||
		url.pathname.endsWith('.html') ||
		url.pathname === '/' ||
		url.pathname.startsWith('/_app/')
	);
}

self.addEventListener('fetch', (event) => {
	if (event.request.method !== 'GET') return;
	const url = new URL(event.request.url);
	if (url.origin !== self.location.origin) return;

	// Always fetch HTML and JS bundles from the network so deploys are not broken by stale cache.
	if (isAppShellRequest(event.request, url)) {
		event.respondWith(fetch(event.request));
		return;
	}

	event.respondWith(
		caches.match(event.request).then((cached) => {
			const fetchPromise = fetch(event.request)
				.then((response) => {
					if (response.ok) {
						const clone = response.clone();
						caches.open(CACHE).then((c) => c.put(event.request, clone));
					}
					return response;
				})
				.catch(() => cached);

			return cached || fetchPromise;
		})
	);
});
