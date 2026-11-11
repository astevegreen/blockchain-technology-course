from __future__ import annotations

import importlib.util
import random
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
DHT_DEMO_PATH = REPO_ROOT / "p2p_trust" / "scripts" / "dht_demo.py"


def load_dht_demo():
    spec = importlib.util.spec_from_file_location("dht_demo", DHT_DEMO_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DhtDemoRouteTests(unittest.TestCase):
    def test_seed_3_route_reaches_goal_without_cycles(self) -> None:
        dht_demo = load_dht_demo()

        random.seed(3)
        ids, bits = dht_demo.make_ring(100, 16)
        fingers = dht_demo.build_fingers(ids, bits)
        start = random.choice(ids)
        target = random.randint(0, 2**bits)
        goal = dht_demo.successor(ids, target)
        path = dht_demo.greedy_route(ids, fingers, start, target, bits)

        self.assertEqual((start, target, goal), (45099, 39713, 40589))
        self.assertEqual(path, [45099, 12773, 30398, 39456, 40589])
        self.assertEqual(path[-1], goal)
        self.assertEqual(len(path), len(set(path)))

        remaining = [dht_demo.ring_distance(node, goal, bits) for node in path]
        self.assertEqual(remaining[-1], 0)
        self.assertTrue(all(a > b for a, b in zip(remaining, remaining[1:])))
