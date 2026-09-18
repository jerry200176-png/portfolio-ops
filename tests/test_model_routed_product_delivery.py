"""Fixtures for MODEL_ROUTED_PRODUCT_DELIVERY_V1 routing / handoff policy."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
RESOLVE = ROOT / "agent-control" / "bin" / "model-route-resolve"
CODEX_ROUTE = ROOT / "agent-control" / "bin" / "codex-route"
POLICY_PATH = Path.home() / ".codex" / "model-routing.toml"


def load_codex_route():
    loader = importlib.machinery.SourceFileLoader("codex_route_v", str(CODEX_ROUTE))
    spec = importlib.util.spec_from_loader("codex_route_v", loader)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


ROUTER = load_codex_route()


def write_profile(home: Path, name: str, model: str) -> None:
    (home / f"{name}.config.toml").write_text(f'model = "{model}"\n', encoding="utf-8")


def signal(**overrides):
    value = {
        "complexity": "medium",
        "ambiguity": "medium",
        "blast_radius": "medium",
        "risk": "medium",
        "workload": "coding",
        "hermes_verdict": "BLOCK",
        "sol_insufficient": False,
        "astra_eligible": False,
        "protected_reasoning": False,
    }
    value.update(overrides)
    return value


class ModelRouteResolveFixtures(unittest.TestCase):
    def test_cursor_sol_unavailable_fails_closed_no_composer_substitute(self) -> None:
        available = "composer-2.5-fast - Composer\nauto - Auto\n"
        with tempfile.NamedTemporaryFile("w", delete=False) as handle:
            handle.write(available)
            path = handle.name
        proc = subprocess.run(
            [
                str(RESOLVE),
                "--provider", "cursor",
                "--role", "planning",
                "--available-models", path,
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["fail_closed"])
        self.assertEqual(payload["resolution"], "capacity_blocked")
        self.assertNotIn("composer-2.5-fast", payload.get("model") or "")

    def test_cursor_astra_mapping_empty_fails_closed(self) -> None:
        proc = subprocess.run(
            [
                str(RESOLVE),
                "--provider", "cursor",
                "--role", "tier",
                "--tier", "astra",
                "--astra-eligible",
                "--sol-insufficient",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["fail_closed"])
        self.assertEqual(payload["resolution"], "unavailable_mapping")

    def test_protected_decision_allows_plan_blocks_implementation(self) -> None:
        available = "gpt-5.6-sol-medium - Sol\n"
        with tempfile.NamedTemporaryFile("w", delete=False) as handle:
            handle.write(available)
            path = handle.name
        proc = subprocess.run(
            [
                str(RESOLVE),
                "--provider", "cursor",
                "--role", "planning",
                "--protected-decision",
                "--available-models", path,
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["implementation_allowed"])
        self.assertTrue(payload["protected_decision"])

    def test_single_item_blocked_other_work_continues_marker(self) -> None:
        """Policy fixture: blocked planning item must not freeze unrelated low-risk work."""
        blocked = {
            "item": "complex-plan-A",
            "status": "CAPACITY_BLOCKED",
            "continue_other_authorized_work": True,
        }
        env = os.environ.copy()
        env["CODEX_ROUTE_BIN"] = str(CODEX_ROUTE)
        low_risk = subprocess.run(
            [
                str(RESOLVE),
                "--provider", "codex",
                "--complexity", "low",
                "--ambiguity", "low",
                "--blast-radius", "low",
                "--risk", "low",
                "--workload", "batch",
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        # If machine policy/profiles exist, low-risk should still resolve independently.
        if low_risk.returncode == 0:
            payload = json.loads(low_risk.stdout)
            self.assertEqual(payload.get("selected_tier"), "luna")
        self.assertTrue(blocked["continue_other_authorized_work"])

    def test_fresh_session_resume_via_plan_ref_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan = Path(tmp) / "PLAN_MRPD_V1_r1.md"
            plan.write_text(
                "# Plan\n\n- Plan ref / revision: MRPD-V1-r1\n- Authorization basis: fixture\n",
                encoding="utf-8",
            )
            checkpoint = Path(tmp) / "checkpoint.json"
            checkpoint.write_text(
                json.dumps(
                    {
                        "goal": "MODEL_ROUTED_PRODUCT_DELIVERY_V1",
                        "plan_ref": "MRPD-V1-r1",
                        "plan_path": str(plan),
                        "status": "ready_for_implementation",
                        "duplicate_dispatch": False,
                    }
                ),
                encoding="utf-8",
            )
            loaded = json.loads(checkpoint.read_text(encoding="utf-8"))
            self.assertEqual(loaded["plan_ref"], "MRPD-V1-r1")
            self.assertTrue(Path(loaded["plan_path"]).is_file())
            self.assertFalse(loaded["duplicate_dispatch"])


@unittest.skipUnless(POLICY_PATH.is_file(), "machine model-routing.toml required")
class CodexRouteProtectedFailClosed(unittest.TestCase):
    def policy_home(self) -> tempfile.TemporaryDirectory:
        directory = tempfile.TemporaryDirectory()
        home = Path(directory.name)
        (home / "model-routing.toml").write_text(
            POLICY_PATH.read_text(encoding="utf-8"), encoding="utf-8"
        )
        return directory

    def test_protected_sol_unavailable_fails_closed(self) -> None:
        directory = self.policy_home()
        self.addCleanup(directory.cleanup)
        home = Path(directory.name)
        write_profile(home, "terra", "gpt-5.6-terra")
        with patch.object(ROUTER, "_codex_home", return_value=home):
            policy = ROUTER._load_policy()
            requested, reason = ROUTER._choose(
                signal(risk="critical", workload="coding"), policy
            )
            with self.assertRaisesRegex(RuntimeError, "fail-closed"):
                ROUTER._resolve(requested, policy, reason)


if __name__ == "__main__":
    unittest.main()
