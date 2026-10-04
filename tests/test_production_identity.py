"""Production status comes from live endpoint evidence, never stale inventory."""

from __future__ import annotations

import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "production_identity", ROOT / "scripts/check-production-identity.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

SHA_A = "a" * 40
SHA_B = "b" * 40
NOW = datetime(2026, 10, 4, tzinfo=timezone.utc)


def portfolio(expected: str = SHA_A) -> dict:
    return {
        "projects": [{
            "id": "sample",
            "source_commit": expected,
            "production": {
                "health_url": "https://example.test/health",
                "version_url": "https://example.test/version",
            },
        }]
    }


class ProductionIdentityTests(unittest.TestCase):
    def test_matching_full_sha_and_health_are_runtime_verified(self) -> None:
        responses = {"https://example.test/health": {"ok": True},
                     "https://example.test/version": {"commit": SHA_A}}
        row = MODULE.probe(portfolio(), responses.__getitem__, NOW)["projects"][0]
        self.assertEqual(row["delivery_state"], "VERIFIED")
        self.assertEqual(row["health"], "HEALTHY")
        self.assertTrue(row["inventory_match"])

    def test_new_runtime_sha_does_not_relabel_stale_inventory(self) -> None:
        responses = {"https://example.test/health": {"status": "ok"},
                     "https://example.test/version": {"build_sha": SHA_B}}
        row = MODULE.probe(portfolio(), responses.__getitem__, NOW)["projects"][0]
        self.assertEqual(row["delivery_state"], "VERIFIED")
        self.assertEqual(row["serving_sha"], SHA_B)
        self.assertFalse(row["inventory_match"])
        self.assertIn("NO", MODULE.render_markdown({"generated_at": NOW.isoformat(), "projects": [row]}))

    def test_unhealthy_runtime_is_only_deployed(self) -> None:
        responses = {"https://example.test/health": {"ok": False},
                     "https://example.test/version": {"commit": SHA_A}}
        row = MODULE.probe(portfolio(), responses.__getitem__, NOW)["projects"][0]
        self.assertEqual(row["delivery_state"], "DEPLOYED")
        self.assertEqual(row["health"], "UNHEALTHY")

    def test_ambiguous_health_is_unknown_and_cannot_verify(self) -> None:
        responses = {"https://example.test/health": {"message": "alive"},
                     "https://example.test/version": {"commit": SHA_A}}
        row = MODULE.probe(portfolio(), responses.__getitem__, NOW)["projects"][0]
        self.assertEqual(row["delivery_state"], "DEPLOYED")
        self.assertEqual(row["health"], "UNKNOWN")

    def test_missing_inventory_identity_does_not_claim_match(self) -> None:
        responses = {"https://example.test/health": {"ok": True},
                     "https://example.test/version": {"commit": SHA_A}}
        row = MODULE.probe(portfolio(""), responses.__getitem__, NOW)["projects"][0]
        self.assertIsNone(row["inventory_match"])
        self.assertEqual(row["product_acceptance"], "UNKNOWN")

    def test_missing_or_short_version_is_unknown_even_with_healthy_endpoint(self) -> None:
        responses = {"https://example.test/health": {"ok": True},
                     "https://example.test/version": {"commit": SHA_A[:8]}}
        row = MODULE.probe(portfolio(), responses.__getitem__, NOW)["projects"][0]
        self.assertEqual(row["delivery_state"], "UNKNOWN")
        self.assertIsNone(row["inventory_match"])

    def test_probe_error_is_unknown_and_does_not_leak_exception_text(self) -> None:
        def fetch(url: str) -> dict:
            if url.endswith("health"):
                return {"ok": True}
            raise OSError("private URL or credential")

        row = MODULE.probe(portfolio(), fetch, NOW)["projects"][0]
        self.assertEqual(row["delivery_state"], "UNKNOWN")
        self.assertEqual(row["errors"], ["version probe failed: OSError"])
        self.assertNotIn("credential", str(row))


if __name__ == "__main__":
    unittest.main()
