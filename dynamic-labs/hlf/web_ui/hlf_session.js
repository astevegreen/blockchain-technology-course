/* Phase 7.3½e — session heartbeat.
 *
 * Posts to <base>/api/hlf/claims/heartbeat every 60s while the tab is
 * visible so the idle sweeper treats active students as live. Uses a
 * relative URL so /labs/hlf/c/<uuid>/ resolves to the per-session
 * proxy (nginx injects X-HLF-Session); the legacy /labs/hlf/ and
 * /labs/hlf/s/<id>/ surfaces fall back to the cookie or produce a
 * harmless 400 (no session).
 */

/* Shared URL-base resolver for every HLF surface (explorer, exercises,
 * node console, etc.). All the per-page basePath() helpers delegate to
 * this so a single place owns the "which prefix owns this request"
 * decision.
 *
 * Preference order (first match wins):
 *   1. /labs/hlf/c/<uuid>/...   → /labs/hlf/c/<uuid>   (session URL)
 *   2. /labs/hlf/s/sNN/...      → /labs/hlf/s/sNN      (station URL)
 *   3. hlf_session cookie set   → /labs/hlf/c/<uuid>   (cookie fallback)
 *   4. bare /labs/hlf/...       → /labs/hlf            (preview / unscoped)
 *
 * The cookie fallback matters when the student lands on a naked surface
 * like /labs/hlf/explorer/ (bookmark, stale link, or a ../ from a nested
 * page). Without it, the back-to-lesson link would drop the UUID.
 */
(function () {
  function resolve() {
    var path = window.location.pathname;
    var m = path.match(/^(\/labs\/hlf\/c\/[0-9a-f-]{36})(?=\/|$)/i);
    if (m) return m[1];
    var s = path.match(/^(\/labs\/hlf\/s\/s\d{2})(?=\/|$)/i);
    if (s) return s[1];
    var c = /(?:^|;\s*)hlf_session=([0-9a-f-]{36})/i.exec(document.cookie || '');
    if (c) return '/labs/hlf/c/' + c[1];
    var marker = '/labs/hlf/';
    var idx = path.indexOf(marker);
    if (idx !== -1) return path.slice(0, idx + marker.length - 1);
    return '';
  }
  window.HLFBase = { resolve: resolve };
})();

(function () {
  "use strict";
  var INTERVAL_MS = 60 * 1000;
  var timer = null;

  function endpoint() {
    // Resolve against HLFBase so the heartbeat always hits
    // <session-prefix>/api/hlf/claims/heartbeat regardless of which
    // sub-surface (/explorer/, /exercises/, etc.) the page lives on.
    // The old bare-relative "api/hlf/claims/heartbeat" resolved against
    // window.location.href and 405'd from any subpath.
    var base = (window.HLFBase && window.HLFBase.resolve()) || "";
    return base + "/api/hlf/claims/heartbeat";
  }

  function beat() {
    try {
      fetch(endpoint(), {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: "{}",
        keepalive: true,
      }).then(function (r) {
        if (r.status === 404) {
          stop();
          window.location.href = "/labs/hlf/claim";
        }
      }).catch(function () { /* swallow — network error is fine */ });
    } catch (e) { /* ignore */ }
  }

  function start() {
    if (timer !== null) return;
    beat();
    timer = setInterval(beat, INTERVAL_MS);
  }

  function stop() {
    if (timer === null) return;
    clearInterval(timer);
    timer = null;
  }

  function onVisibilityChange() {
    if (document.visibilityState === "visible") {
      start();
    } else {
      stop();
    }
  }

  document.addEventListener("visibilitychange", onVisibilityChange);
  // Only start if we're on a session-scoped URL — otherwise the
  // heartbeat would just 400 on every tick for preview-mode viewers.
  if (/\/labs\/hlf\/c\/[0-9a-f-]+\//.test(window.location.pathname)) {
    if (document.visibilityState === "visible") start();
  }
})();
