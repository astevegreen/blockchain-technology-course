"""
Fire-and-forget progress beacon for the cryptography Streamlit app.

Each page calls `fire("<route_id>")` once at render time. The helper
renders a zero-height `st.iframe` whose script
reads the `crypto_lab_session` cookie from the parent document and
POSTs `{route_id, session}` to `/api/cryptography/progress/touch`.

Idempotent + dedup-friendly: a second call with the same route_id
inside ~5s is suppressed client-side via sessionStorage, so
Streamlit reruns don't flood the beacon.

The beacon is a no-op when the cookie is missing (e.g., direct hit
without going through the landing page that seeds the cookie).
"""

from __future__ import annotations

import json

import streamlit as st


_BEACON_TEMPLATE = """
<script>
(function () {
  var routeId = __ROUTE__;
  var now = Date.now();
  try {
    var key = 'cryptobeacon:' + routeId;
    var last = Number(window.parent.sessionStorage.getItem(key) || 0);
    if (now - last < 5000) return;
    window.parent.sessionStorage.setItem(key, String(now));
  } catch (_) {}
  var session = '';
  try {
    var m = (window.parent.document.cookie || '').match(/(?:^|;\\s*)crypto_lab_session=([^;]+)/);
    if (m) session = decodeURIComponent(m[1]);
  } catch (_) {}
  if (!session) return;
  try {
    fetch('/api/cryptography/progress/touch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ route_id: routeId, session: session }),
      keepalive: true,
    }).catch(function(){});
  } catch (_) {}
})();
</script>
"""


def fire(route_id: str) -> None:
    """Render an invisible beacon snippet for the given route_id."""
    if not route_id:
        return
    snippet = _BEACON_TEMPLATE.replace("__ROUTE__", json.dumps(str(route_id)))
    st.iframe(snippet, height=1, width=1)


__all__ = ["fire"]
