from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BrowserRegressionContractTests(unittest.TestCase):
    def test_ethereum_diagnostics_autorun_tracks_provider_initialization(self) -> None:
        source = (
            ROOT / "ethereum_lab/frontend/src/views/DiagnosticsView.jsx"
        ).read_text(encoding="utf-8")

        effect = re.search(
            r"useEffect\(\(\) => \{\s*"
            r"if \(!autoRun\) return\s*"
            r"const timer = setTimeout\(\(\) => \{\s*"
            r"runAll\(\)\s*"
            r"\}, 600\).*?"
            r"\}, \[([^\]]+)\]\)",
            source,
            flags=re.S,
        )
        self.assertIsNotNone(effect)
        dependencies = {dep.strip() for dep in effect.group(1).split(",")}
        self.assertIn("provider", dependencies)

    def test_hlf_exercise_surface_links_resolve_against_hlf_base(self) -> None:
        source = (ROOT / "hlf/web_ui/hlf_exercises.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("function resolveSurfaceHref(href)", source)
        self.assertIn("exercisesBasePath().replace", source)
        self.assertIn("resolveSurfaceHref(item.href)", source)
        self.assertNotIn('href="${item.href}"', source)

    def test_consensus_catalog_includes_interactive_selfish_mining(self) -> None:
        source = (ROOT / "lane-service/labs/consensus_catalog.yaml").read_text(
            encoding="utf-8"
        )

        self.assertIn("pow-selfish-student", source)
        self.assertIn(
            "python3 scripts/pow_local.py --reset --miners 4 --strategy selfish-student",
            source,
        )

    def test_p2p_trust_catalog_avoids_badactor_placeholder(self) -> None:
        catalog = (ROOT / "lane-service/labs/p2p_trust_catalog.yaml").read_text(
            encoding="utf-8"
        )
        readme = (ROOT / "p2p_trust/README.md").read_text(encoding="utf-8")

        self.assertNotIn("<BADACTOR_ID>", catalog)
        self.assertNotIn("<node_id>", readme)
        self.assertIn("python3 scripts/ngo_sim.py audit --trace 123456", catalog)
        self.assertIn("python3 ngo_sim.py audit --trace 123456", readme)

    def test_hlf_scenario_playbook_uses_stop_start_language(self) -> None:
        source = (
            ROOT
            / "regression-tests/agent/hlf/tasks/instructor-scenario-controls.md"
        ).read_text(encoding="utf-8")

        self.assertIn('"action":"stop"', source)
        self.assertIn('"action":"start"', source)
        self.assertNotIn("activate/deactivate fault", source.lower())

    def test_ethereum_view_navigation_syncs_query_string(self) -> None:
        source = (ROOT / "ethereum_lab/frontend/src/App.jsx").read_text(
            encoding="utf-8"
        )

        self.assertIn("SHAREABLE_QUERY_VIEWS", source)
        self.assertIn("u.searchParams.set('view', nextView)", source)
        self.assertIn("u.searchParams.delete('view')", source)

    def test_cryptography_docs_match_shipped_scenario_count(self) -> None:
        for rel in ("cryptography/README.md", "cryptography/STUDENT_README.md"):
            source = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("Scenarios 1 through 4", source)
            self.assertIn("Complete all four scenarios", source)
            self.assertNotIn("Scenarios 1 through 5", source)
            self.assertNotIn("Complete all five scenarios", source)


if __name__ == "__main__":
    unittest.main()
