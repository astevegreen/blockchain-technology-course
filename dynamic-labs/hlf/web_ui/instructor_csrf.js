// Instructor CSRF shim.
//
// Fetches a CSRF token from /api/instructor/csrf (POST, cookie-gated)
// and monkeypatches window.fetch so every same-origin mutating request
// (POST/PUT/PATCH/DELETE) automatically gets an X-CSRFToken header.
//
// Include this as the first <script> on any instructor page that
// makes mutating fetch calls. The server enforces CSRF globally via
// a before_request hook, so missing headers surface as 403.
(function () {
  const MUTATING = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);
  const EXEMPT_PATHS = new Set([
    '/api/instructor/login',
    '/api/instructor/logout',
    '/api/instructor/csrf',
  ]);

  let tokenPromise = null;
  function fetchToken() {
    if (tokenPromise) return tokenPromise;
    tokenPromise = window.__origFetch('/api/instructor/csrf', {
      method: 'POST',
      credentials: 'same-origin',
    })
      .then(r => (r.ok ? r.json() : Promise.reject(new Error('csrf ' + r.status))))
      .then(j => j.token)
      .catch(e => {
        tokenPromise = null;
        throw e;
      });
    return tokenPromise;
  }

  window.__origFetch = window.fetch.bind(window);
  window.fetch = async function patched(input, init) {
    init = init || {};
    const method = (init.method || (typeof input === 'object' ? input.method : 'GET') || 'GET').toUpperCase();
    if (!MUTATING.has(method)) return window.__origFetch(input, init);

    // Resolve URL → path for same-origin + exempt check.
    let url;
    try { url = new URL(typeof input === 'string' ? input : input.url, window.location.origin); }
    catch (_) { return window.__origFetch(input, init); }
    if (url.origin !== window.location.origin) return window.__origFetch(input, init);
    if (EXEMPT_PATHS.has(url.pathname)) return window.__origFetch(input, init);

    try {
      const token = await fetchToken();
      const headers = new Headers(init.headers || {});
      if (!headers.has('X-CSRFToken')) headers.set('X-CSRFToken', token);
      init = { ...init, headers, credentials: init.credentials || 'same-origin' };
    } catch (_) {
      // If token mint fails (e.g. cookie expired), let the request
      // go through unmodified and the server's 403 will surface.
    }
    return window.__origFetch(input, init);
  };

  // Eagerly warm the token on load so the first mutation doesn't
  // wait on the /csrf round-trip.
  fetchToken().catch(() => {});
})();
