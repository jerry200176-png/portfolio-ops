"""Gated live Codex integration test (skipped unless GRAPH_REAL_CODEX=1)."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(
    os.environ.get("GRAPH_REAL_CODEX") == "1",
    "explicit integration gate: set GRAPH_REAL_CODEX=1",
)
class RealCodexLiveIntegrationTests(unittest.TestCase):
    def test_real_codex_a_to_b_proof_script(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/graph-real-codex-proof.py")],
            cwd=str(ROOT),
            env={**os.environ, "GRAPH_REAL_CODEX": "1"},
            capture_output=True,
            text=True,
            timeout=int(os.environ.get("GRAPH_REAL_CODEX_TIMEOUT", "1800")),
        )
        self.assertEqual(
            proc.returncode,
            0,
            msg=f"stdout={proc.stdout[-2000:]}\nstderr={proc.stderr[-2000:]}",
        )


if __name__ == "__main__":
    unittest.main()
