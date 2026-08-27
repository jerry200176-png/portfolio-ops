import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release_evidence", ROOT / "scripts/release-evidence.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ReleaseEvidenceTests(unittest.TestCase):
    def test_matching_short_version_hash_and_health_pass(self):
        evidence = MODULE.build_evidence(
            expected_sha="abcdef1234567890",
            version_status=200,
            version_payload={"hash": "abcdef1"},
            health_status=200,
            health_payload={"status": "ok"},
            generated_at="2026-08-27T02:00:00+00:00",
        )
        self.assertTrue(evidence["passed"])
        self.assertEqual(evidence["version"]["matched"]["key"], "hash")

    def test_wrong_serving_sha_fails_even_when_health_is_ok(self):
        evidence = MODULE.build_evidence(
            expected_sha="abcdef1234567890",
            version_status=200,
            version_payload={"build_sha": "1234567890abcdef"},
            health_status=200,
            health_payload={"ok": True},
        )
        self.assertFalse(evidence["passed"])
        self.assertIsNone(evidence["version"]["matched"])

    def test_main_writes_machine_readable_evidence(self):
        responses = iter([
            (200, {"build_sha": "abcdef1234567890"}),
            (200, {"status": "ok"}),
        ])
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "release-evidence.json"
            with patch.object(MODULE, "fetch_json", side_effect=lambda *_args: next(responses)):
                result = MODULE.main([
                    "--version-url", "https://example.invalid/version.json",
                    "--health-url", "https://example.invalid/health",
                    "--expected-sha", "abcdef1234567890",
                    "--json-out", str(output_path),
                ])
            self.assertEqual(result, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["passed"])

    def test_embedded_credentials_are_rejected(self):
        with self.assertRaises(ValueError):
            MODULE.fetch_json("https://user:pass@example.invalid/version.json")


if __name__ == "__main__":
    unittest.main()
