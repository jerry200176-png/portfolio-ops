"""Agent Graph Runtime v0 — deterministic, dry-run only.

This package does NOT call Cursor Agents API, GitHub Operator, merge, or deploy.
"""

from .models import Event, TaskState
from .runtime import GraphRuntime
from .reducer import reduce
from .router import route, validate_transition

__all__ = [
    "Event",
    "TaskState",
    "GraphRuntime",
    "reduce",
    "route",
    "validate_transition",
]

__version__ = "0.1.0"
