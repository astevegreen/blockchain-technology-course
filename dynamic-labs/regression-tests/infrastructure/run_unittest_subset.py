from __future__ import annotations

import argparse
import sys
import unittest


def _iter_cases(suite: unittest.TestSuite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from _iter_cases(test)
        else:
            yield test


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a filtered unittest discovery subset.")
    parser.add_argument("--start-dir", required=True)
    parser.add_argument("--pattern", default="test_*.py")
    parser.add_argument("--match", required=True)
    parser.add_argument("--top-level-dir")
    parser.add_argument("-v", "--verbosity", type=int, default=2)
    args = parser.parse_args()

    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=args.start_dir,
        pattern=args.pattern,
        top_level_dir=args.top_level_dir,
    )
    matched = unittest.TestSuite(
        test for test in _iter_cases(suite) if args.match in test.id()
    )

    if matched.countTestCases() == 0:
        print(
            f"no tests matched pattern {args.match!r} under {args.start_dir}",
            file=sys.stderr,
        )
        return 2

    result = unittest.TextTestRunner(verbosity=args.verbosity).run(matched)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
