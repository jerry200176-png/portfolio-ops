"""Agent Graph Runtime — deterministic transitions; durable Phase 1A store.

In-memory v0 dry-run APIs remain. Durable Runs live in control-plane SQLite.
This package does NOT call Cursor Agents API, merge, or deploy.
"""

from .models import Event, TaskState
from .runtime import GraphRuntime
from .reducer import reduce
from .router import route, validate_transition
from .durable_runtime import DurableGraphRuntime
from .sqlite_store import SqliteControlPlaneStore
from .harness import GraphHarness, FakeWorkerAdapter
from .worker_contract import WorkerResult, validate_worker_result

__all__ = [
    "Event",
    "TaskState",
    "GraphRuntime",
    "DurableGraphRuntime",
    "SqliteControlPlaneStore",
    "GraphHarness",
    "FakeWorkerAdapter",
    "WorkerResult",
    "validate_worker_result",
    "reduce",
    "route",
    "validate_transition",
]

__version__ = "0.2.0"
