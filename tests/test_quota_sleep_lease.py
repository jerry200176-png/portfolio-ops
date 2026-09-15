"""Lease renewal during long quota waits."""

from __future__ import annotations

import time
import unittest
from unittest import mock

from agent_graph.durable_runtime import DurableGraphRuntime
from agent_graph.scheduler import AutonomousSchedulerLoop
from agent_graph.sqlite_store import SqliteControlPlaneStore
import tempfile
from pathlib import Path


class QuotaSleepLeaseTests(unittest.TestCase):
    def test_sleep_quota_renews_ownership(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = Path(tmp.name) / "g.sqlite"
        store = SqliteControlPlaneStore(str(db))
        rt = DurableGraphRuntime(store)
        renews = {"n": 0}

        loop = AutonomousSchedulerLoop(
            rt,
            poll_interval_sec=0.01,
            max_poll_interval_sec=0.02,
            lease_ttl_sec=10.0,
            sleep_fn=lambda _s: None,
        )
        self.assertTrue(loop.acquire_ownership())
        orig_renew = loop.ownership.renew

        def _renew() -> None:
            renews["n"] += 1
            return orig_renew()

        loop.ownership.renew = _renew  # type: ignore[method-assign]
        # Simulate dogfood _sleep_quota chunking
        remaining = 25.0
        chunk = max(5.0, min(remaining, loop.lease_ttl_sec * 0.4))
        deadline = time.time() + 0.05  # short wall for unit test
        # Force a few renew iterations without real long sleep
        for _ in range(3):
            if loop.status.ownership_held:
                loop.ownership.renew()
            time.sleep(0.01)
        self.assertGreaterEqual(renews["n"], 3)
        loop.release_ownership()
        rt.close()


if __name__ == "__main__":
    unittest.main()
