"""Portfolio freshness gate: PR correctness vs operational monitor."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "portfolio_freshness", ROOT / "scripts/portfolio-freshness.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


STALE_PORTFOLIO = """\
schema_version: 1
updated_at: "2020-01-01T00:00:00+00:00"
freshness:
  p0_evidence_ttl_hours: 24
  inventory_ttl_days: 7
  status_ttl_hours: 24
projects:
  - id: alltrue
    last_verified_at: "2020-01-01T00:00:00+00:00"
    evidence_expires_at: "2020-01-02T00:00:00+00:00"
    open_p0: 0
    source_commit: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  - id: sunrise
    last_verified_at: "2020-01-01T00:00:00+00:00"
    evidence_expires_at: "2020-01-02T00:00:00+00:00"
    open_p0: 0
    source_commit: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
"""

FRESH_PORTFOLIO = """\
schema_version: 1
updated_at: "2026-09-15T00:00:00+00:00"
freshness:
  p0_evidence_ttl_hours: 24
  inventory_ttl_days: 7
  status_ttl_hours: 24
projects:
  - id: alltrue
    last_verified_at: "2026-09-15T00:00:00+00:00"
    evidence_expires_at: "2026-09-16T00:00:00+00:00"
    open_p0: 0
    source_commit: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  - id: sunrise
    last_verified_at: "2026-09-15T00:00:00+00:00"
    evidence_expires_at: "2026-09-16T00:00:00+00:00"
    open_p0: 0
    source_commit: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
"""

NOW = "2026-09-15T12:00:00+00:00"


class PortfolioFreshnessGateTests(unittest.TestCase):
    def _write(self, body: str) -> Path:
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".yaml", delete=False, encoding="utf-8"
        )
        handle.write(body)
        handle.close()
        return Path(handle.name)

    def test_case_a_code_only_stale_inventory_is_informational(self) -> None:
        path = self._write(STALE_PORTFOLIO)
        rc = MODULE.main(
            [
                "--now",
                NOW,
                "--portfolio",
                str(path),
                "--fail-on-stale-when-inventory-changed",
                "--changed-paths",
                "agent_graph/sqlite_store.py,tests/test_graph_concurrency.py",
            ]
        )
        self.assertEqual(rc, 0)

    def test_case_b_inventory_touch_stale_fails_closed(self) -> None:
        path = self._write(STALE_PORTFOLIO)
        rc = MODULE.main(
            [
                "--now",
                NOW,
                "--portfolio",
                str(path),
                "--fail-on-stale-when-inventory-changed",
                "--changed-paths",
                "portfolio.yaml,README.md",
            ]
        )
        self.assertEqual(rc, 1)

    def test_case_c_inventory_touch_fresh_passes(self) -> None:
        path = self._write(FRESH_PORTFOLIO)
        rc = MODULE.main(
            [
                "--now",
                NOW,
                "--portfolio",
                str(path),
                "--fail-on-stale-when-inventory-changed",
                "--changed-paths",
                "portfolio.yaml",
            ]
        )
        self.assertEqual(rc, 0)

    def test_case_d_scheduled_fail_on_stale_preserved(self) -> None:
        path = self._write(STALE_PORTFOLIO)
        rc = MODULE.main(
            [
                "--now",
                NOW,
                "--portfolio",
                str(path),
                "--fail-on-stale",
            ]
        )
        self.assertEqual(rc, 1)

    def test_ownership_helper(self) -> None:
        self.assertTrue(MODULE.inventory_ownership_touched({"portfolio.yaml"}))
        self.assertFalse(
            MODULE.inventory_ownership_touched({"agent_graph/cli.py", "scripts/graph"})
        )

    def test_mutually_exclusive_flags(self) -> None:
        path = self._write(STALE_PORTFOLIO)
        rc = MODULE.main(
            [
                "--now",
                NOW,
                "--portfolio",
                str(path),
                "--fail-on-stale",
                "--fail-on-stale-when-inventory-changed",
                "--changed-paths",
                "portfolio.yaml",
            ]
        )
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
