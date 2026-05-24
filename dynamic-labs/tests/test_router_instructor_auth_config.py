from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER_DIR = ROOT / "router"


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _block(text: str, marker: str) -> str:
    start = text.index(marker)
    end = text.index("\n}", start) + 2
    return text[start:end]


class RouterInstructorAuthConfigTests(unittest.TestCase):
    def test_shared_auth_subrequest_targets_central_auth_service_verify_endpoint(self) -> None:
        auth_conf = _read("router/routes/_auth.conf")
        self.assertIn('set $auth_host "instructor-auth-service";', auth_conf)
        self.assertIn("proxy_pass http://$auth_host:8080/api/instructor/verify;", auth_conf)
        self.assertIn('proxy_cache_key "$cookie_hlf_instructor";', auth_conf)
        self.assertIn("proxy_cache_valid 200 401 5s;", auth_conf)

    def test_shared_login_redirect_captures_original_uri_via_auth_service(self) -> None:
        auth_conf = _read("router/routes/_auth.conf")

        self.assertIn("location @instructor_login {", auth_conf)
        self.assertIn('set $login_host "instructor-auth-service";', auth_conf)
        self.assertIn(
            "proxy_pass http://$login_host:8080/api/instructor/return-to;",
            auth_conf,
        )
        self.assertIn("proxy_method GET;", auth_conf)
        self.assertIn("proxy_set_header X-Original-URI $request_uri;", auth_conf)
        self.assertIn("proxy_set_header X-Original-Method $request_method;", auth_conf)
        self.assertNotIn("?next=", auth_conf)

    def test_top_level_instructor_and_portal_routes_remain_pinned(self) -> None:
        routes_conf = _read("router/routes.conf")
        self.assertIn("location = /instructor {", routes_conf)
        self.assertIn("return 301 $scheme://$http_host/instructor/;", routes_conf)
        self.assertIn("location ~ ^/instructor/labs-progress(?<rest>/.*)?$ {", routes_conf)
        self.assertIn('set $target_host "lane-service-lane-service-1";', routes_conf)
        self.assertIn(
            "proxy_pass http://$target_host:8090/instructor/labs-progress$rest$is_args$args;",
            routes_conf,
        )
        self.assertIn("location ~ ^/api/portal(?<rest>/.*)?$ {", routes_conf)
        self.assertIn("proxy_pass http://$target_host:8090/api/portal$rest$is_args$args;", routes_conf)
        self.assertIn("location ~ ^/instructor(?<rest>/.*)?$ {", routes_conf)
        self.assertIn('set $target_host "instructor-auth-service";', routes_conf)
        self.assertIn("proxy_pass http://$target_host:8080/instructor$rest$is_args$args;", routes_conf)
        self.assertIn("location ~ ^/api/instructor(?<rest>/.*)?$ {", routes_conf)
        self.assertIn(
            "proxy_pass http://$target_host:8080/api/instructor$rest$is_args$args;",
            routes_conf,
        )

    def test_quiz_and_exercise_instructor_surfaces_use_shared_auth_request(self) -> None:
        routes_conf = _read("router/routes.conf")
        self.assertIn("location ~ ^/exercises/(?<exercise>[a-zA-Z]+)/instructor(?<rest>/.*)?$ {", routes_conf)
        self.assertIn("location ~ ^/quiz/instructor(?<rest>/.*)?$ {", routes_conf)
        self.assertIn('set $target_host "quiz-engine-v2";', routes_conf)
        self.assertIn("proxy_pass http://$target_host:8000/instructor$rest$is_args$args;", routes_conf)
        self.assertIn("proxy_pass http://$target_host:8000$rest$is_args$args;", routes_conf)
        self.assertGreaterEqual(routes_conf.count("auth_request /_auth/instructor;"), 2)
        self.assertGreaterEqual(routes_conf.count("error_page 401 = @instructor_login;"), 2)

    def test_lab_route_fragments_keep_instructor_surfaces_gated(self) -> None:
        expected_files = [
            "router/routes/bitcoin.conf",
            "router/routes/consensus.conf",
            "router/routes/p2p_trust.conf",
            "router/routes/cryptography.conf",
            "router/routes/hlf.conf",
        ]
        for path in expected_files:
            with self.subTest(path=path):
                conf = _read(path)
                self.assertIn("auth_request /_auth/instructor;", conf)

    def test_hlf_route_fragment_keeps_runner_served_instructor_assets(self) -> None:
        hlf_conf = _read("router/routes/hlf.conf")
        self.assertIn(
            "location ~ ^/labs/hlf/(hlf_instructor\\.html|hlf_instructor\\.js|hlf_session\\.js)$ {",
            hlf_conf,
        )
        self.assertIn('set $target_host "hlf-hlf-runner-1";', hlf_conf)

    def test_hlf_route_fragment_keeps_student_governance_and_node_detail_surfaces_public(self) -> None:
        hlf_conf = _read("router/routes/hlf.conf")
        claims_block = _block(hlf_conf, "location = /labs/hlf/api/hlf/claims/active {")
        self.assertNotIn("auth_request /_auth/instructor;", claims_block)
        self.assertIn('set $target_host "hlf-hlf-runner-1";', claims_block)

        peer_block = _block(hlf_conf, "location ~ ^/labs/hlf/peer/org[1-5](?<rest>/.*)?$ {")
        self.assertNotIn("auth_request /_auth/instructor;", peer_block)
        self.assertIn('set $target_host "hlf-hlf-1";', peer_block)

        orderer_block = _block(hlf_conf, "location ~ ^/labs/hlf/orderer(?<rest>/.*)?$ {")
        self.assertNotIn("auth_request /_auth/instructor;", orderer_block)
        self.assertIn('set $target_host "hlf-hlf-1";', orderer_block)

        console_block = _block(hlf_conf, "location ~ ^/labs/hlf/peer/org[1-5]/console(?<rest>/.*)?$ {")
        self.assertIn("auth_request /_auth/instructor;", console_block)

        orderer_console_block = _block(hlf_conf, "location ~ ^/labs/hlf/orderer/console(?<rest>/.*)?$ {")
        self.assertIn("auth_request /_auth/instructor;", orderer_console_block)

    def test_ethereum_route_fragment_keeps_shared_instructor_gates(self) -> None:
        ethereum_conf = _read("router/routes/ethereum.conf")
        self.assertIn("location = /labs/ethereum_lab/ {", ethereum_conf)
        self.assertIn("if ($arg_mode = instructor) {", ethereum_conf)
        instructor_mode_block = _block(ethereum_conf, "location @ethereum_instructor_mode {")
        self.assertIn(
            'add_header Set-Cookie "ethereum_instructor_mode=1; Path=/labs/ethereum_lab/; SameSite=Lax" always;',
            instructor_mode_block,
        )
        self.assertIn('set $eth_instructor "ethereum-trainer-instructor";', instructor_mode_block)
        self.assertIn("proxy_pass http://$eth_instructor:5173$uri$is_args$args;", instructor_mode_block)
        self.assertIn("proxy_set_header X-Instructor 1;", instructor_mode_block)
        self.assertIn("location = /labs/ethereum/admin {", ethereum_conf)
        self.assertIn("location = /labs/ethereum_lab/instructor {", ethereum_conf)
        self.assertIn("location = /labs/ethereum_lab/instructor/ {", ethereum_conf)
        self.assertIn("return 302 /labs/ethereum_lab/?mode=instructor;", ethereum_conf)
        self.assertGreaterEqual(ethereum_conf.count("auth_request /_auth/instructor;"), 3)
        self.assertIn("auth_request /_resolve/ethereum;", ethereum_conf)


if __name__ == "__main__":
    unittest.main()
