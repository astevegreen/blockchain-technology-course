// Per-student progress beacon.
//
// Fire-and-forget POST to /api/hlf/progress/touch whenever the current
// exercise step changes, or whenever a tracked surface page loads.
// Silently no-ops in preview mode (no session cookie/UUID in URL) — the
// server also drops unknown sessions, so this is belt-and-suspenders.
//
// Intentionally dumb: no retries, no batching. Progress visits are
// idempotent on the server side (count goes up, but that's fine — it's
// the whole point of the "total_views" metric).

(function () {
  'use strict';

  // Dedupe identical consecutive touches — a single-page render often
  // re-calls renderCurrentExercise() multiple times in rapid succession.
  let lastSent = null;
  let lastSentAt = 0;

  function basePath() {
    return (window.HLFBase && window.HLFBase.resolve()) || '';
  }

  function looksClaimed() {
    // Either we're under /labs/hlf/c/<uuid>/ (session path) or an
    // hlf_session cookie exists. Either way, the server will figure out
    // whether the UUID is valid.
    if (/\/labs\/hlf\/c\/[0-9a-f-]{36}\b/i.test(window.location.pathname)) return true;
    return /(?:^|;\s*)hlf_session=/.test(document.cookie || '');
  }

  function recordStep(routeId) {
    if (!routeId) return;
    if (!looksClaimed()) return; // preview mode — do nothing
    const now = Date.now();
    if (routeId === lastSent && (now - lastSentAt) < 1500) return;
    lastSent = routeId;
    lastSentAt = now;
    try {
      fetch(`${basePath()}/api/hlf/progress/touch`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ route_id: routeId }),
        keepalive: true,
      }).catch(() => {});
    } catch (_) {
      /* ignore */
    }
  }

  window.HLFProgress = { recordStep };
})();
