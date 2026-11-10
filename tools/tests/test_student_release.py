"""tools/student_release.py: the matrix, the pinned manifest, the API driver and the LFS check."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import student_release as sr  # noqa: E402

STUB = REPO / "tools" / "tests" / "fixtures" / "student-release-images.stub.json"
WORKFLOW = REPO / ".github" / "workflows" / "student-release.yml"
D1 = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64
V = "2026.11.09-7"


def row(lab, service, source="build", **kw):
    base = {"lab": lab, "service": service, "source": source, "platforms": ["linux/amd64", "linux/arm64"],
            "variable": f"{lab}_{service}_IMAGE".upper().replace("-", "_")}
    base.update({"context": f"dynamic-labs/{lab}", "dockerfile": "Dockerfile"} if source == "build" else {})
    base.update(kw)
    return base


class Images(unittest.TestCase):
    def test_the_stub_has_the_generated_shape(self):
        images = sr.load_images(STUB)
        self.assertTrue(any(r["source"] == "build" for r in images))
        self.assertTrue(any(r["source"] == "upstream" for r in images))

    def test_a_row_without_its_build_fields_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "images.json"
            bad = row("a", "b")
            del bad["dockerfile"]
            path.write_text(json.dumps({"images": [bad]}))
            with self.assertRaises(SystemExit):
                sr.load_images(path)

    def test_a_platform_with_no_runner_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "images.json"
            path.write_text(json.dumps({"images": [row("a", "b", platforms=["linux/s390x"])]}))
            with self.assertRaises(SystemExit):
                sr.load_images(path)

    def test_a_shared_variable_is_built_once(self):
        rows = [row("dex", "anvil", variable="DEX_ANVIL_IMAGE"), row("dex", "anvil-l2", variable="DEX_ANVIL_IMAGE")]
        self.assertEqual(len(sr.one_per_variable(rows)), 1)

    def test_a_shared_variable_built_two_ways_is_refused(self):
        rows = [row("dex", "anvil", variable="X"), row("dex", "other", variable="X", dockerfile="Other")]
        with self.assertRaises(SystemExit):
            sr.one_per_variable(rows)


class Matrix(unittest.TestCase):
    def test_one_row_per_build_and_platform_on_a_native_runner(self):
        rows = sr.build_matrix([row("tron", "page"), row("router", "router", "upstream", image="nginx:alpine"),
                                row("wallet", "mempool", platforms=["linux/amd64"])], V)
        self.assertEqual([(r["key"], r["runner"]) for r in rows],
                         [("tron--page--amd64", "ubuntu-24.04"), ("tron--page--arm64", "ubuntu-24.04-arm"),
                          ("wallet--mempool--amd64", "ubuntu-24.04")])
        self.assertEqual(rows[0]["image"], f"ghcr.io/astevegreen/course-labs:tron-page-{V}")

    def test_one_dockerfile_is_built_once_for_two_variables(self):
        rows = sr.build_matrix([row("hlf", "hlf"), row("hlf", "hlf-runner")], V)
        self.assertEqual({r["image"] for r in rows}, {f"ghcr.io/astevegreen/course-labs:hlf-hlf-{V}"})

    def test_the_real_bitcoin_instructor_is_the_student_build(self):
        """The real manifest: bitcoin's student and instructor share a Dockerfile, so the release builds it once and
        both variables pin that digest (as the published 2026.11.10-11 latest.json does). A change that gave the
        instructor its own Dockerfile would build and ship a second copy; this says so."""
        images = sr.load_images(REPO / "dynamic-labs" / "student-release-images.json")
        built = [(r["lab"], r["service"]) for r in sr.build_matrix(images, V) if r["lab"] == "bitcoin"]
        self.assertNotIn(("bitcoin", "instructor"), built)
        self.assertIn(("bitcoin", "student"), built)
        with tempfile.TemporaryDirectory() as tmp:
            for r in sr.build_matrix(images, V):
                (Path(tmp) / f"{sr.slug(r['lab'])}--{sr.slug(r['service'])}").write_text(D1)
            got = sr.resolve_images(images, V, Path(tmp), inspect=lambda ref: D2)
        self.assertEqual(got["BITCOIN_INSTRUCTOR_IMAGE"], got["BITCOIN_STUDENT_IMAGE"])
        self.assertIn(":bitcoin-student-", got["BITCOIN_INSTRUCTOR_IMAGE"])

    def test_every_stub_tag_is_a_valid_docker_tag(self):
        for r in sr.build_matrix(sr.load_images(STUB), V):
            tag = r["image"].split(":", 1)[1]
            self.assertRegex(tag, r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$")

    def test_the_cli_refuses_a_bad_version(self):
        with self.assertRaises(SystemExit):
            sr.main(["matrix", "--images", str(STUB), "--version", "v1"])


class Resolve(unittest.TestCase):
    def test_built_and_upstream_images_are_pinned(self):
        images = [row("hlf", "hlf"), row("hlf", "hlf-runner"),
                  row("router", "router", "upstream", image="nginx:alpine"),
                  row("wallet", "gateway", "upstream", image="nginx:alpine")]
        asked = []
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "hlf--hlf").write_text(D1 + "\n")
            got = sr.resolve_images(images, V, Path(tmp), inspect=lambda ref: asked.append(ref) or D2)
        self.assertEqual(got["HLF_HLF_IMAGE"], f"ghcr.io/astevegreen/course-labs:hlf-hlf-{V}@{D1}")
        self.assertEqual(got["HLF_HLF_RUNNER_IMAGE"], got["HLF_HLF_IMAGE"])
        self.assertEqual(got["ROUTER_ROUTER_IMAGE"], f"nginx:alpine@{D2}")
        self.assertEqual(asked, ["nginx:alpine"], "one registry call per upstream image")

    def test_a_missing_digest_fails(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(SystemExit):
            sr.resolve_images([row("tron", "page")], V, Path(tmp))

    def test_a_malformed_digest_fails(self):
        with self.assertRaises(SystemExit):
            sr.pinned("nginx:alpine", "latest")


class Assemble(unittest.TestCase):
    def tree(self, root: Path) -> list[dict]:
        for rel in ("dynamic-labs/tron/docker-compose.launcher.yml",
                    "dynamic-labs/router/docker-compose.launcher.yml",
                    "dynamic-labs/router/routes/local/quiz-off.conf",
                    "dynamic-labs/regression-tests/fixtures/hello-lab/docker-compose.launcher.yml"):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(f"# {rel}\n")
        return [{"id": "tron", "kind": "lab", "student_local": True, "student_compose_file": "docker-compose.launcher.yml"},
                {"id": "router", "kind": "shared", "student_local": True,
                 "student_compose_file": "docker-compose.launcher.yml"},
                {"id": "quiz-engine-v2", "kind": "instructor", "student_local": False},
                {"id": "bitcoin-forensics", "kind": "lab", "student_local": False},
                {"id": "hello-lab", "kind": "fixture", "student_local": True,
                 "student_compose_file": "docker-compose.launcher.yml"}]

    def test_the_release_folder_follows_the_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, out = Path(tmp) / "repo", Path(tmp) / "out"
            labs = self.tree(root)
            manifest = sr.assemble([], labs, V, {"B_IMAGE": "b@" + D1, "A_IMAGE": "a@" + D2}, out, root=root)
            self.assertEqual(manifest["launcher_image"], f"ghcr.io/astevegreen/course-labs:launcher-{V}")
            self.assertEqual([lab["id"] for lab in manifest["labs"]], ["tron", "router"])
            self.assertEqual(list(manifest["images"]), ["A_IMAGE", "B_IMAGE"])
            self.assertEqual(sorted(p.name for p in (out / "release" / "labs").iterdir()), ["router", "tron"])
            self.assertTrue((out / "release/labs/tron/docker-compose.launcher.yml").is_file())
            self.assertTrue((out / "release/router/local/quiz-off.conf").is_file())
            self.assertEqual(json.loads((out / "latest.json").read_text()), manifest)
            self.assertEqual(json.loads((out / "release/manifest.json").read_text()), manifest)

    def test_the_fixture_ships_only_in_a_fixture_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, out = Path(tmp) / "repo", Path(tmp) / "out"
            labs = self.tree(root)
            manifest = sr.assemble([], labs, V, {}, out, root=root, fixtures=True)
            self.assertIn("hello-lab", [lab["id"] for lab in manifest["labs"]])
            self.assertTrue((out / "release/labs/hello-lab/docker-compose.launcher.yml").is_file())

    def test_the_real_fixture_has_an_image_to_rebuild(self):
        # The smoke test's Change check builds each row twice; with no row both launchers run the same digest.
        rows = sr.fixture_builds()
        self.assertEqual([(r["lab"], r["service"], r["variable"]) for r in rows],
                         [("hello-lab", "hello", "HELLO_LAB_HELLO_IMAGE")])
        self.assertTrue((sr.REPO / rows[0]["context"] / rows[0]["dockerfile"]).is_file())

    def test_a_missing_launcher_compose_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            labs = [{"id": "tron", "kind": "lab", "student_local": True,
                     "student_compose_file": "docker-compose.launcher.yml"}]
            with self.assertRaises(SystemExit):
                sr.assemble([], labs, V, {}, Path(tmp) / "out", root=Path(tmp))

    def test_image_var_follows_the_launcher_rule(self):
        self.assertEqual(sr.image_var("cross-chain", "page", {}), "CROSS_CHAIN_PAGE_IMAGE")
        self.assertEqual(sr.image_var("dex", "anvil-l2", {"variable": "DEX_ANVIL_IMAGE"}), "DEX_ANVIL_IMAGE")


class Smoke(unittest.TestCase):
    def test_only_student_labs_with_ci_tests_are_smoke_tested(self):
        labs = [{"id": "tron", "kind": "lab", "student_local": True, "order": {"day": 5, "position": 1}},
                {"id": "explorer", "kind": "lab", "student_local": True, "order": {"day": 2, "position": 1}},
                {"id": "router", "kind": "shared", "student_local": True},
                {"id": "quiz-engine-v2", "kind": "instructor", "student_local": False},
                {"id": "bitcoin-forensics", "kind": "lab", "student_local": False},
                {"id": "nope", "kind": "lab", "student_local": True}]
        got = sr.smoke_labs(labs, tested=["tron", "explorer", "quiz-engine", "nope"])
        self.assertEqual(got, [{"lab": "explorer", "test": "explorer"}, {"lab": "tron", "test": "tron"}])


class FakeLauncher:
    def __init__(self, labs, phases):
        self.labs, self.phases, self.calls, self.now = labs, list(phases), [], 0.0

    def call(self, base, method, path):
        self.calls.append((method, path))
        if path == "/api/health":
            return {"ok": True, "version": V}
        if path == "/api/labs":
            return {"labs": self.labs}  # the envelope server.py sends; a bare list here hid a bug until the first real run
        if path.endswith("/start"):
            return {}
        return {"phase": self.phases.pop(0) if len(self.phases) > 1 else self.phases[0], "message": "m"}

    def sleep(self, seconds):
        self.now += seconds

    def clock(self):
        return self.now


class Drive(unittest.TestCase):
    def run_drive(self, fake, lab="tron", timeout=60):
        return sr.drive("http://x", lab, timeout, call=fake.call, sleep=fake.sleep, clock=fake.clock,
                        log=lambda *_: None)

    def test_start_then_wait_for_running(self):
        fake = FakeLauncher([{"id": "tron", "state": "not-downloaded"}], ["pulling", "starting", "running"])
        self.assertEqual(self.run_drive(fake), 0)
        self.assertIn(("POST", "/api/labs/tron/start"), fake.calls)

    def test_an_unavailable_lab_is_skipped(self):
        fake = FakeLauncher([{"id": "tron", "state": "unavailable", "unavailable_reason": "amd64 only"}], ["running"])
        self.assertEqual(self.run_drive(fake), sr.SKIPPED)
        self.assertNotIn(("POST", "/api/labs/tron/start"), fake.calls)

    def test_an_error_phase_fails(self):
        with self.assertRaises(SystemExit):
            self.run_drive(FakeLauncher([{"id": "tron", "state": "stopped"}], ["pulling", "error"]))

    def test_a_lab_the_launcher_does_not_list_fails(self):
        with self.assertRaises(SystemExit):
            self.run_drive(FakeLauncher([], ["running"]))

    def test_a_lab_that_never_runs_times_out(self):
        with self.assertRaises(SystemExit):
            self.run_drive(FakeLauncher([{"id": "tron", "state": "stopped"}], ["pulling"]), timeout=10)

    def test_health_waits_through_refused_connections(self):
        fake = FakeLauncher([], ["running"])
        answers = [ConnectionRefusedError(), ConnectionRefusedError(), {"ok": True, "version": V}]

        def call(base, method, path):
            answer = answers.pop(0)
            if isinstance(answer, Exception):
                raise answer
            return answer
        self.assertEqual(sr.wait_health("http://x", 30, call, fake.sleep, fake.clock)["version"], V)


class LfsCheck(unittest.TestCase):
    def test_a_pointer_is_found_and_a_real_file_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / ".gitattributes").write_text("*.dat filter=lfs diff=lfs merge=lfs -text\n")
            (root / "pointer.dat").write_bytes(sr.LFS_HEADER + b"\noid sha256:abc\nsize 3\n")
            (root / "real.dat").write_bytes(b"\x00\x01real")
            subprocess.run(["git", "-c", "filter.lfs.clean=cat", "-c", "filter.lfs.smudge=cat",
                            "-c", "filter.lfs.required=false", "add", "."], cwd=root, check=True)
            self.assertEqual(sr.lfs_pointers(root), ["pointer.dat"])


class ShippedLfs(unittest.TestCase):
    def test_only_lfs_files_a_student_image_ships_are_fetched(self):
        files = ["dynamic-labs/bitcoin-forensics/x-instructor-dir/blocks/blk.dat", "dynamic-labs/tron/data/chain.dat",
                 "dynamic-labs/tron/answers/key.dat", "dynamic-labs/tronic/other.dat"]
        got = sr.shipped_lfs(files, ["dynamic-labs/tron"], ["dynamic-labs/tron/answers/**"])
        self.assertEqual(got, ["dynamic-labs/tron/data/chain.dat"])

    def test_lane_service_built_from_dynamic_labs_fetches_the_forensics_snapshot(self):
        # S3's lane-service/Dockerfile.launcher builds from dynamic-labs/ and bakes the forensics v3 blocks (LFS).
        import student_exclude
        lane = {"lab": "lane-service", "service": "lane-service", "source": "build", "context": "dynamic-labs/",
                "dockerfile": "lane-service/Dockerfile.launcher", "variable": "X", "platforms": ["linux/amd64"]}
        files = sr.lfs_files()
        blocks = [f for f in files if f.startswith("dynamic-labs/bitcoin-forensics/forensics-lab-v3-instructor-dir/blocks/")]
        self.assertTrue(blocks, "the forensics blocks are no longer LFS files")
        got = sr.shipped_lfs(files, sr.shipped_contexts([lane]), student_exclude.patterns())
        self.assertTrue(set(blocks) <= set(got))

    def test_the_bases_and_launcher_count_as_shipped(self):
        contexts = sr.shipped_contexts([row("tron", "page")])
        self.assertIn("dynamic-labs/tron", contexts)
        self.assertTrue(set(sr.BASE_CONTEXTS) <= set(contexts))


class Workflow(unittest.TestCase):
    def setUp(self):
        self.text = WORKFLOW.read_text(encoding="utf-8")

    def test_dispatch_only_with_publish_off_by_default(self):
        import yaml
        flow = yaml.safe_load(self.text)
        on = flow.get("on", flow.get(True))
        # Builds run only when the owner starts them (.claude/rules/ci.md).
        self.assertEqual(set(on), {"workflow_dispatch"})
        self.assertIs(on["workflow_dispatch"]["inputs"]["publish"]["default"], False)

    def test_publish_waits_for_the_smoke_tests(self):
        import yaml
        publish = yaml.safe_load(self.text)["jobs"]["publish"]
        self.assertIn("smoke", publish["needs"])
        self.assertIn("inputs.publish", publish["if"])
        self.assertIn("needs.smoke.result == 'success'", publish["if"])
        self.assertIn("mac", publish["needs"])
        self.assertIn("needs.mac.result == 'success'", publish["if"])

    def test_the_mac_job_runs_the_command_wrappers_with_macos_bash(self):
        import yaml
        mac = yaml.safe_load(self.text)["jobs"]["mac"]
        # GitHub's arm64 Macs have no nested virtualization, so no Docker engine: the Intel Mac runs Colima.
        self.assertTrue(mac["runs-on"].startswith("macos-") and mac["runs-on"].endswith("-intel"))
        runs = " ".join(str(s.get("run", "")) for s in mac["steps"])
        lint = next(str(s["run"]) for s in mac["steps"] if "shellcheck -S warning" in str(s.get("run", "")))
        for wrapper in ("Start-Course-Labs.command", "Stop-Course-Labs.command"):
            self.assertIn(f"/bin/bash student-launcher/{wrapper}", runs)
            self.assertIn(f"student-launcher/{wrapper}", lint)
        self.assertIn('COURSE_LABS_IMAGE="$PACKAGE:launcher-$VERSION"', runs)
        self.assertIn("student_release.py drive", runs)

    def test_every_job_that_builds_fetches_and_checks_the_shipped_lfs_files(self):
        import yaml
        jobs = yaml.safe_load(self.text)["jobs"]
        for name in ("prepare", "bases", "build"):
            with self.subTest(job=name):
                runs = " ".join(str(s.get("run", "")) for s in jobs[name]["steps"])
                self.assertIn('student_release.py lfs-check --images "$IMAGES" --pull', runs)

    def test_version_and_tags(self):
        self.assertIn('version="$(date -u +%Y.%m.%d)-$RUN"', self.text)
        self.assertIn('"$PACKAGE:launcher-$VERSION"', self.text)
        self.assertIn('"$PACKAGE:launcher-stable"', self.text)
        self.assertIn('"student-v$VERSION" --draft', self.text)
        self.assertIn("--draft=false --prerelease=false", self.text)

    def test_the_zip_keeps_wrapper_names_and_adds_the_read_me_when_present(self):
        self.assertIn("files=(student-launcher/Start-Course-Labs.* student-launcher/Stop-Course-Labs.*)", self.text)
        self.assertIn("[ -f student-launcher/READ-ME-FIRST.html ] && files+=(student-launcher/READ-ME-FIRST.html)",
                      self.text)
        self.assertIn('zip -j "$RUNNER_TEMP/Course-Labs.zip" "${files[@]}"', self.text)
        self.assertIn('[ ${#files[@]} -gt 0 ] || { echo "no Start-Course-Labs.* or Stop-Course-Labs.* in student-launcher/"; '
                      'exit 1; }', self.text)

    def test_the_zip_glob_finds_the_wrappers_in_the_repo(self):
        # The first dry run to reach this step (42755031048) failed here: the glob named a folder that does not exist.
        found = sorted(p.name for pattern in ("Start-Course-Labs.*", "Stop-Course-Labs.*")
                       for p in (REPO / "student-launcher").glob(pattern))
        for name in ("Start-Course-Labs.cmd", "Start-Course-Labs.command", "Stop-Course-Labs.cmd",
                     "Stop-Course-Labs.command"):
            self.assertIn(name, found)

    def test_latest_json_names_the_launcher_by_digest(self):
        self.assertIn('.launcher_image = $ref', self.text)
        self.assertIn('"$PACKAGE:launcher-$VERSION@$digest"', self.text)

    def test_hlf_builds_from_the_fabric_samples_commit_lab_sh_pins(self):
        self.assertIn("if: startsWith(format('{0}/{1}', matrix.context, matrix.dockerfile), 'dynamic-labs/hlf/')",
                      self.text)
        self.assertIn('FABRIC_SAMPLES_REF="$ref" bash install-fabric.sh samples', self.text)
        lab = (REPO / "dynamic-labs" / "hlf" / "lab.sh").read_text(encoding="utf-8")
        self.assertRegex(lab, r"HLF_FABRIC_SAMPLES_REF:-[0-9a-f]{40}")

    def test_both_runner_architectures_are_smoke_tested(self):
        self.assertIn("runner: [ubuntu-24.04, ubuntu-24.04-arm]", self.text)


if __name__ == "__main__":
    unittest.main()
