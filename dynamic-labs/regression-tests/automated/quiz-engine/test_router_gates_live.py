"""The router's instructor gates, checked by sending requests through it.

Every instructor surface in router/routes.conf and router/routes/*.conf must refuse a stranger: the router bounces
the browser to the shared login (/instructor/) or answers 401. A signed-in instructor must get through. The student
routes that sit beside the HLF gates must stay open.

These checks live in the quiz-engine suite because it is the lightest stack that starts the router, and a change to
the router runs it (tools/lab_tests.py treats router/ as a shared part). The router decides before it proxies, so a
lab that is not running answers 502 or 504 here, which counts as "let through".
"""

from __future__ import annotations

import unittest
from urllib.parse import urlparse

import requests

from live_support import DEFAULT_BASE_URL, login_instructor, new_session, wait_for_http

LOGIN_PATH = "/instructor/"
ROUTER_API_REFUSAL = '{"error":"instructor auth required"}'  # @hlf_api_unauth in router/routes/_auth.conf

# One path per gated location, with the file that gates it.
GATED = [
    "/instructor/labs-progress",  # routes.conf, the lane service checks the cookie
    "/api/instructor/sessions",  # routes.conf, the instructor auth service checks the cookie
    "/quiz/instructor",  # routes.conf
    "/quiz/instructor/api/metrics",  # routes.conf
    "/exercises/insider/instructor",  # routes.conf
    "/exercises/insider/instructor/api/state",  # routes.conf
    "/labs/bitcoin/admin",  # routes/bitcoin.conf
    "/labs/bitcoin/instructor/",  # routes/bitcoin.conf
    "/labs/bitcoin/static-web-instructor/",  # routes/bitcoin.conf
    "/labs/consensus/admin",  # routes/consensus.conf
    "/labs/consensus/instructor/",  # routes/consensus.conf
    "/labs/cryptography/admin",  # routes/cryptography.conf
    "/labs/cryptography/instructor/",  # routes/cryptography.conf
    "/labs/cryptography/instructor/dashboard",  # routes/cryptography.conf
    "/labs/ethereum/admin",  # routes/ethereum.conf
    "/labs/ethereum_lab/instructor",  # routes/ethereum.conf, redirects to ?mode=instructor
    "/labs/ethereum_lab/?mode=instructor",  # routes/ethereum.conf, @ethereum_instructor_mode
    "/labs/hlf/api/hlf/claims",  # routes/hlf.conf, the API catch-all
    "/labs/hlf/instructor/term/org1/",  # routes/hlf.conf
    "/labs/hlf/instructor/term/orderer/",  # routes/hlf.conf
    "/labs/hlf/peer/org1/console/",  # routes/hlf.conf
    "/labs/hlf/orderer/console/",  # routes/hlf.conf
    "/labs/hlf/instructor",  # routes/hlf.conf, the instructor panel page
    "/labs/hlf/instructor/",  # routes/hlf.conf
    "/labs/p2p_trust/admin",  # routes/p2p_trust.conf
    "/labs/p2p_trust/instructor/",  # routes/p2p_trust.conf
]

# Student routes in routes/hlf.conf that a broader gate could swallow.
OPEN = [
    "/labs/hlf/api/hlf/status",
    "/labs/hlf/api/hlf/claims/active",
    "/labs/hlf/peer/org1/",
    "/labs/hlf/orderer/",
]


def _walk(session: requests.Session, base_url: str, path: str) -> list[requests.Response]:
    """Every response on the way, following redirects that stay on the router (at most five)."""
    host = urlparse(base_url).netloc
    url = f"{base_url}{path}"
    hops: list[requests.Response] = []
    for _ in range(5):
        resp = session.get(url, timeout=15, allow_redirects=False, headers={"Accept": "text/html,application/json"})
        hops.append(resp)
        location = resp.headers.get("Location")
        if resp.status_code not in (301, 302, 303, 307, 308) or not location:
            break
        target = urlparse(location)
        if target.netloc and target.netloc != host:
            break
        url = f"{base_url}{target.path}" + (f"?{target.query}" if target.query else "")
    return hops


def _sent_to_login(hops: list[requests.Response]) -> bool:
    return any(urlparse(h.headers.get("Location", "")).path == LOGIN_PATH for h in hops)


def _refused(hops: list[requests.Response]) -> bool:
    return _sent_to_login(hops) or hops[-1].status_code in (401, 403)


def _describe(hops: list[requests.Response]) -> str:
    return " -> ".join(f"{h.status_code} {h.headers.get('Location', '')}".strip() for h in hops)


class RouterInstructorGateLiveTests(unittest.TestCase):
    base_url = DEFAULT_BASE_URL

    @classmethod
    def setUpClass(cls) -> None:
        cls.instructor_session = new_session()
        wait_for_http(
            cls.instructor_session,
            f"{cls.base_url}{LOGIN_PATH}",
            lambda resp: resp.status_code == 200,
            description="shared instructor login page",
        )
        # The lane service gates this path itself and starts last, so it can still be booting when the suite begins
        # (a 502 here once failed CI). Wait until it answers.
        wait_for_http(
            cls.instructor_session,
            f"{cls.base_url}/instructor/labs-progress",
            lambda resp: resp.status_code not in (502, 503, 504),
            description="lane service behind /instructor/labs-progress",
            allow_redirects=False,
        )
        login_instructor(cls.instructor_session, cls.base_url)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.instructor_session.close()

    def test_each_gate_refuses_a_stranger(self) -> None:
        for path in GATED:
            with self.subTest(path=path), new_session() as stranger:
                hops = _walk(stranger, self.base_url, path)
                self.assertTrue(_refused(hops), f"{path} let a stranger through: {_describe(hops)}")

    def test_each_gate_lets_the_instructor_through(self) -> None:
        for path in GATED:
            with self.subTest(path=path):
                hops = _walk(self.instructor_session, self.base_url, path)
                self.assertFalse(_refused(hops), f"{path} refused the instructor: {_describe(hops)}")

    def test_hlf_student_routes_stay_open(self) -> None:
        for path in OPEN:
            with self.subTest(path=path), new_session() as stranger:
                hops = _walk(stranger, self.base_url, path)
                self.assertFalse(_sent_to_login(hops), f"{path} sent a student to login: {_describe(hops)}")
                self.assertNotEqual(hops[-1].text.strip(), ROUTER_API_REFUSAL, f"{path} is gated by the router")


if __name__ == "__main__":
    unittest.main()
