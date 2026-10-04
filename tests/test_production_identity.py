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
            "github_repo": "example/sample",
            "source_commit": expected,
            "last_verified_at": "2026-10-02T00:00:00Z",
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
        self.assertEqual(row["delivery_state"], "RUNTIME_VERIFIED")
        self.assertEqual(row["health"], "HEALTHY")
        self.assertTrue(row["inventory_match"])

    def test_new_runtime_sha_does_not_relabel_stale_inventory(self) -> None:
        responses = {"https://example.test/health": {"status": "ok"},
                     "https://example.test/version": {"build_sha": SHA_B}}
        row = MODULE.probe(portfolio(), responses.__getitem__, NOW)["projects"][0]
        self.assertEqual(row["delivery_state"], "RUNTIME_VERIFIED")
        self.assertEqual(row["serving_sha"], SHA_B)
        self.assertFalse(row["inventory_match"])
        self.assertIn("NO", MODULE.render_markdown({"generated_at": NOW.isoformat(), "projects": [row]}))

    def test_unhealthy_runtime_is_not_runtime_verified(self) -> None:
        responses = {"https://example.test/health": {"ok": False},
                     "https://example.test/version": {"commit": SHA_A}}
        row = MODULE.probe(portfolio(), responses.__getitem__, NOW)["projects"][0]
        self.assertEqual(row["delivery_state"], "RUNTIME_UNHEALTHY")
        self.assertEqual(row["health"], "UNHEALTHY")

    def test_healthy_endpoint_with_degraded_rate_limit_is_not_healthy(self) -> None:
        responses = {"https://example.test/health": {
                         "ok": True,
                         "rate_limit_mode": "memory",
                         "rate_limit_grade": "degraded_per_isolate",
                     },
                     "https://example.test/version": {"commit": SHA_A}}
        row = MODULE.probe(portfolio(), responses.__getitem__, NOW)["projects"][0]
        self.assertEqual(row["delivery_state"], "RUNTIME_DEGRADED")
        self.assertEqual(row["health"], "DEGRADED")
        self.assertEqual(row["health_details"], {
            "rate_limit_mode": "memory",
            "rate_limit_grade": "degraded_per_isolate",
        })
        markdown = MODULE.render_markdown({"generated_at": NOW.isoformat(), "projects": [row]})
        self.assertIn("RUNTIME_DEGRADED", markdown)
        self.assertIn("degraded_per_isolate", markdown)

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

    def test_waiting_deployment_with_pending_reviewer_is_protected_blocker(self) -> None:
        responses = {"https://example.test/health": {"ok": True},
                     "https://example.test/version": {"commit": SHA_A}}
        api = {
            "repos/example/sample/deployments?per_page=20": [
                {"id": 42, "sha": SHA_B, "environment": "production-activation",
                 "created_at": "2026-10-03T12:00:00Z"}],
            "repos/example/sample/deployments/42/statuses?per_page=20": [
                {"state": "waiting", "created_at": "2026-10-03T12:01:00Z"}],
            f"repos/example/sample/actions/runs?head_sha={SHA_B}&status=waiting&per_page=20": {
                "workflow_runs": [{"id": 72, "head_sha": SHA_B, "status": "waiting"}]},
            "repos/example/sample/actions/runs/72/pending_deployments": [
                {"environment": {"name": "production-activation"},
                 "reviewers": [{"type": "User", "reviewer": {"login": "owner"}}]}],
        }
        row = MODULE.probe(portfolio(), responses.__getitem__, NOW, api.__getitem__)["projects"][0]
        self.assertEqual(row["candidate_sha"], SHA_B)
        self.assertEqual(row["candidate_state"], "WAITING")
        self.assertEqual(row["candidate_age_hours"], 12)
        self.assertEqual(row["inventory_age_hours"], 48)
        self.assertEqual(row["protected_blocker"], "ENVIRONMENT_REVIEW_REQUIRED")
        self.assertEqual(row["product_acceptance"], "UNKNOWN")

    def test_waiting_without_reviewer_evidence_keeps_blocker_unknown(self) -> None:
        responses = {"https://example.test/health": {"ok": True},
                     "https://example.test/version": {"commit": SHA_A}}
        def api(path: str) -> dict | list:
            if path.endswith("deployments?per_page=20"):
                return [{"id": 42, "sha": SHA_B, "environment": "Production",
                         "created_at": "2026-10-03T12:00:00Z"}]
            if "/statuses?" in path:
                return [{"state": "waiting", "created_at": "2026-10-03T12:01:00Z"}]
            raise RuntimeError("API unavailable")
        row = MODULE.probe(portfolio(), responses.__getitem__, NOW, api)["projects"][0]
        self.assertEqual(row["candidate_sha"], SHA_B)
        self.assertEqual(row["protected_blocker"], "UNKNOWN")

    def test_old_successful_deployment_is_not_candidate(self) -> None:
        responses = {"https://example.test/health": {"ok": True},
                     "https://example.test/version": {"commit": SHA_A}}
        def api(path: str) -> dict | list:
            if path.endswith("deployments?per_page=20"):
                return [{"id": 42, "sha": SHA_B, "environment": "Production",
                         "created_at": "2026-09-01T00:00:00Z"}]
            return [{"state": "success", "created_at": "2026-09-01T00:02:00Z"}]
        row = MODULE.probe(portfolio(), responses.__getitem__, NOW, api)["projects"][0]
        self.assertIsNone(row["candidate_sha"])
        self.assertEqual(row["candidate_state"], "UNKNOWN")

    def test_no_github_access_keeps_candidate_and_blocker_unknown(self) -> None:
        responses = {"https://example.test/health": {"ok": True},
                     "https://example.test/version": {"commit": SHA_A}}
        def api(_path: str) -> dict | list:
            raise RuntimeError("private repo not readable")
        row = MODULE.probe(portfolio(), responses.__getitem__, NOW, api)["projects"][0]
        self.assertIsNone(row["candidate_sha"])
        self.assertEqual(row["protected_blocker"], "UNKNOWN")

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
