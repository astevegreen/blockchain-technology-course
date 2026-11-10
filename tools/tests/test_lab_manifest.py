"""Tests for tools/lab_manifest.py. Run: python -m unittest discover -s tools/tests"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lab_manifest as lm  # noqa: E402

SCHEMA = lm.load_schema()


def good(lab_id="demo"):
    return {
        "id": lab_id, "title": "Demo", "kind": "lab", "order": {"day": None, "position": 0},
        "compose_project": lab_id, "compose_file": "docker-compose.yml", "student_local": True,
        "student_compose_file": "docker-compose.launcher.yml",
        "services": {"web": {"source": "build", "context": ".", "platforms": ["linux/amd64"]},
                     "db": {"source": "upstream", "image": "postgres:16", "platforms": ["linux/amd64"]}},
        "networks": [{"name": "router-net", "internal": False}], "routes": ["routes/demo.conf"],
        "uses_lane_service": False, "entry": {"path": "/labs/demo/"}, "memory_mb": 1, "approx_download_mb": 1,
        "data": [], "keep_volumes_on_update": True,
    }


class Validator(unittest.TestCase):
    def problems(self, manifest, folder="demo"):
        return lm.validate_manifest(folder, manifest, SCHEMA)

    def test_good_manifest_passes(self):
        self.assertEqual(self.problems(good()), [])

    def test_missing_required_field(self):
        m = good()
        del m["title"]
        self.assertTrue(any("missing required field `title`" in p for p in self.problems(m)))

    def test_unknown_field_rejected(self):
        m = good()
        m["extra"] = 1
        self.assertTrue(any("extra" in p for p in self.problems(m)))

    def test_enum_pattern_minimum_type_items(self):
        m = good()
        m["kind"] = "nope"
        m["compose_project"] = "Bad Name"
        m["memory_mb"] = -1
        m["routes"] = ["x.conf"]
        m["uses_lane_service"] = "yes"
        text = "\n".join(self.problems(m))
        for needle in ("kind", "compose_project", "memory_mb", "routes[0]", "uses_lane_service"):
            self.assertIn(needle, text)

    def test_type_list_accepts_null_and_integer(self):
        for day in (None, 3):
            m = good()
            m["order"]["day"] = day
            self.assertEqual(self.problems(m), [])
        m = good()
        m["order"]["day"] = "3"
        self.assertTrue(self.problems(m))

    def test_bool_is_not_integer(self):
        m = good()
        m["memory_mb"] = True
        self.assertTrue(self.problems(m))

    def test_id_must_equal_folder(self):
        self.assertTrue(any("must equal the folder" in p for p in self.problems(good("other"), folder="demo")))

    def test_student_compose_file_required_when_student_local(self):
        m = good()
        del m["student_compose_file"]
        self.assertTrue(any("student_compose_file is required" in p for p in self.problems(m)))
        m["student_local"] = False
        self.assertEqual(self.problems(m), [])

    def test_data_mount_with_unresolved_variable_fails(self):
        m = good()
        m["data"] = [{"path": "./${NGINX_CONF", "into": "-nginx-ssl.conf}", "how": "baked"}]
        self.assertTrue(any("data[0]" in p for p in self.problems(m)))
        m["data"] = [{"path": "./nginx-ssl.conf", "into": "/etc/nginx/conf.d/default.conf", "how": "baked"}]
        self.assertEqual(self.problems(m), [])

    def test_service_needs_image_or_context(self):
        m = good()
        del m["services"]["db"]["image"]
        del m["services"]["web"]["context"]
        text = "\n".join(self.problems(m))
        self.assertIn("upstream service needs `image`", text)
        self.assertIn("build service needs `context`", text)


def tree(root: Path, manifests: dict, launcher: dict | None = None, route_files=(), routes_conf=""):
    """A throwaway dynamic-labs folder: the real schema, one compose file per manifest, and the router."""
    labs = root / "dynamic-labs"
    labs.mkdir()
    (labs / lm.SCHEMA).write_text((lm.LABS / lm.SCHEMA).read_text(encoding="utf-8"), encoding="utf-8")
    for folder, m in manifests.items():
        (labs / folder).mkdir(exist_ok=True)
        (labs / folder / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
        (labs / folder / "lab.yaml").write_text(yaml.safe_dump(m), encoding="utf-8")
    for folder, text in (launcher or {}).items():
        (labs / folder / "docker-compose.launcher.yml").write_text(text, encoding="utf-8")
    (labs / "router" / "routes").mkdir(parents=True, exist_ok=True)
    for name in route_files:
        (labs / "router" / "routes" / name).write_text("# route\n", encoding="utf-8")
    (labs / "router" / "routes.conf").write_text(routes_conf, encoding="utf-8")
    return labs


class Rules(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_compose_folder_without_manifest_fails(self):
        labs = tree(self.root, {"demo": good()})
        (labs / "bare").mkdir()
        (labs / "bare" / "compose.yaml").write_text("services: {}\n", encoding="utf-8")
        self.assertTrue(any("bare/ holds a compose file but has no lab.yaml" in p for p in lm.check_manifests(labs)))

    def test_valid_tree_passes_manifest_rule(self):
        self.assertEqual(lm.check_manifests(tree(self.root, {"demo": good()})), [])

    def test_missing_compose_file_fails(self):
        m = good()
        m["compose_file"] = "nope.yml"
        labs = tree(self.root, {"demo": m})
        self.assertTrue(any("nope.yml does not exist" in p for p in lm.check_manifests(labs)))

    def test_network_internal_flag_must_agree(self):
        a, b = good("a"), good("b")
        b["networks"] = [{"name": "router-net", "internal": True}]
        labs = tree(self.root, {"a": a, "b": b})
        self.assertTrue(any("disagree" in p for p in lm.check_manifests(labs)))

    def launcher(self, text):
        return lm.check_launcher_files(tree(self.root, {"demo": good()}, {"demo": text}))

    def test_launcher_missing_file_is_skipped(self):
        self.assertEqual(lm.check_launcher_files(tree(self.root, {"demo": good()})), [])

    def test_launcher_clean_file_passes(self):
        text = ("services:\n  web:\n    image: ${DEMO_WEB_IMAGE}\n    volumes: [data:/d]\n"
                "  db:\n    image: ${DEMO_DB_IMAGE:?set it}\n    volumes:\n      - type: tmpfs\n        target: /t\n"
                "volumes:\n  data: {}\n")
        self.assertEqual(self.launcher(text), [])

    def test_launcher_bind_mount_fails(self):
        for vol in ("./data:/d", "/srv/x:/d", "C:/x:/d", "../shared:/d:ro"):
            text = f"services:\n  web:\n    image: ${{DEMO_WEB_IMAGE}}\n    volumes: ['{vol}']\n"
            self.assertTrue(any("host path" in p for p in self.launcher(text)), vol)
            self._tmp.cleanup()
            self.setUp()

    def test_launcher_long_bind_syntax_fails(self):
        text = ("services:\n  web:\n    image: ${DEMO_WEB_IMAGE}\n    volumes:\n      - type: bind\n"
                "        source: ./x\n        target: /d\n")
        self.assertTrue(any("host path" in p for p in self.launcher(text)))

    SOCK = "/var/run/docker.sock:/var/run/docker.sock"

    def socket_tree(self, lab_id, flag, volume):
        m = good(lab_id)
        if flag:
            m["docker_socket"] = True
        var = lm.variable_for(lab_id, "web", m["services"]["web"])
        text = f"services:\n  web:\n    image: ${{{var}}}\n    volumes: ['{volume}']\n"
        return lm.check_launcher_files(tree(self.root, {lab_id: m}, {lab_id: text}))

    def test_docker_socket_allowed_for_each_listed_lab_that_sets_it(self):
        self.assertEqual(set(lm.DOCKER_SOCKET_LABS), {"lane-service", "hlf"})
        for lab_id in lm.DOCKER_SOCKET_LABS:
            self.assertEqual(self.socket_tree(lab_id, True, self.SOCK), [], lab_id)
            self._tmp.cleanup()
            self.setUp()

    def test_docker_socket_refused_without_the_flag(self):
        for lab_id in ("hlf", "lane-service"):
            self.assertTrue(any("host path" in p for p in self.socket_tree(lab_id, False, self.SOCK)), lab_id)
            self._tmp.cleanup()
            self.setUp()

    def test_min_docker_fields_are_set_together(self):
        m = good("other")
        m["min_docker_engine"] = "26.0"
        self.assertTrue(any("set together" in p for p in lm.validate_manifest("other", m, SCHEMA)))
        m["min_docker_desktop"] = "4.29"
        self.assertEqual(lm.validate_manifest("other", m, SCHEMA), [])
        m["min_docker_engine"] = "new"
        self.assertTrue(lm.validate_manifest("other", m, SCHEMA))

    def test_docker_socket_flag_refused_for_an_unlisted_lab(self):
        m = good("other")
        m["docker_socket"] = True
        self.assertTrue(any("docker_socket is allowed only for" in p
                            for p in lm.validate_manifest("other", m, SCHEMA)))
        self.assertTrue(any("host path" in p for p in self.socket_tree("other", True, self.SOCK)))

    def test_docker_socket_flag_does_not_allow_other_host_paths(self):
        for vol in ("/srv/x:/d", "/var/run/docker.sock:/other", "/var/run:/var/run",
                    "/var/run/docker.sock:/var/run/docker.sock:ro", "./data:/d"):
            self.assertTrue(any("host path" in p for p in self.socket_tree("hlf", True, vol)), vol)
            self._tmp.cleanup()
            self.setUp()

    def test_launcher_build_fails(self):
        text = "services:\n  web:\n    build: .\n    image: ${DEMO_WEB_IMAGE}\n"
        self.assertTrue(any("`build:`" in p for p in self.launcher(text)))

    def test_launcher_literal_image_fails(self):
        self.assertTrue(any("must be ${VAR}" in p for p in self.launcher("services:\n  web:\n    image: nginx\n")))

    def test_launcher_unknown_variable_fails(self):
        text = "services:\n  web:\n    image: ${OTHER_IMAGE}\n"
        self.assertTrue(any("not in the manifest" in p for p in self.launcher(text)))

    def test_routes_orphan_file_has_no_owner(self):
        labs = tree(self.root, {"demo": good()}, route_files=["demo.conf", "orphan.conf"],
                    routes_conf="include /etc/nginx/routes/demo.conf;\n")
        self.assertEqual(lm.check_routes(labs),
                         ["router/routes/orphan.conf has no owner: list it under `routes` in a lab.yaml"])

    def test_routes_missing_file_and_missing_include(self):
        m = good()
        m["routes"] = ["routes/demo.conf", "routes/gone.conf"]
        labs = tree(self.root, {"demo": m}, route_files=["demo.conf"], routes_conf="")
        text = "\n".join(lm.check_routes(labs))
        self.assertIn("routes/gone.conf does not exist", text)
        self.assertIn("routes.conf does not include routes/demo.conf", text)

    def test_routes_host_file_needs_no_include(self):
        m = good()
        m["routes"] = ["routes/demo-host.conf"]
        labs = tree(self.root, {"demo": m}, route_files=["demo-host.conf"])
        self.assertEqual(lm.check_routes(labs), [])

    def test_routes_single_owner(self):
        a, b = good("a"), good("b")
        a["routes"] = b["routes"] = ["routes/x.conf"]
        labs = tree(self.root, {"a": a, "b": b}, route_files=["x.conf"],
                    routes_conf="include /etc/nginx/routes/x.conf;")
        self.assertTrue(any("more than one manifest" in p for p in lm.check_routes(labs)))


class Generators(unittest.TestCase):
    def manifests(self):
        a = good("alpha")
        a["order"] = {"day": 1, "position": 0}
        b = good("beta_lab")
        b["networks"] = [{"name": "router-net", "internal": False}, {"name": "beta-net", "internal": True}]
        return {"alpha": a, "beta_lab": b}

    def test_network_list_is_union_router_first(self):
        self.assertEqual(lm.network_list(self.manifests()), [("router-net", False), ("beta-net", True)])

    def test_aliases(self):
        self.assertEqual(lm.aliases("p2p_trust"), ["p2p_trust", "p2p-trust"])
        self.assertIn("ethereum", lm.aliases("ethereum_lab"))
        self.assertIn("quiz", lm.aliases("quiz-engine-v2"))

    def test_list_targets_keeps_the_hyphen_name_lab_manager_compares_against(self):
        m = good("instructor_auth_service")
        body = lm.sh_bodies({"instructor_auth_service": m})["LIST_TARGETS"]
        self.assertIn("\ninstructor-auth-service\n", body)
        self.assertNotIn("instructor_auth_service", body)

    def test_block_lists_by_day_then_off_schedule(self):
        block = lm.course_site_block(self.manifests())
        self.assertIn("* Day 1: [Demo](/labs/demo/)", block)
        self.assertIn("### Labs outside the ten-day schedule\n\n* [Demo]", block)

    def test_release_images_cover_every_service(self):
        rows = json.loads(lm.release_images(self.manifests()))["images"]
        self.assertEqual([(r["lab"], r["service"], r["variable"]) for r in rows[:2]],
                         [("alpha", "web", "ALPHA_WEB_IMAGE"), ("alpha", "db", "ALPHA_DB_IMAGE")])
        self.assertEqual(rows[0]["context"], "dynamic-labs/alpha")
        self.assertEqual(rows[1]["image"], "postgres:16")

    def test_render_replaces_only_marked_region(self):
        source = f'before\n{lm.BLOCK_BEGIN}\nBLOCK = """old"""\n{lm.BLOCK_END}\nafter\n'
        out = lm.render_inject(source, self.manifests())
        self.assertTrue(out.startswith("before\n") and out.endswith("after\n"))
        self.assertNotIn("old", out)
        self.assertEqual(lm.render_inject(out, self.manifests()), out)


class RealRepo(unittest.TestCase):
    def test_every_manifest_valid_and_outputs_current(self):
        self.assertEqual(lm.check_all(), [])


if __name__ == "__main__":
    unittest.main()
