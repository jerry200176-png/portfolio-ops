"""Single-host process identity for execution-lease recovery.

PID alone is insufficient (reuse). We bind pid + kernel starttime + boot_id
(+ optional pgid) so reclaim can distinguish alive vs dead vs unverifiable.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, Optional


OwnerLiveness = Literal["alive", "dead", "unknown"]


@dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    starttime_ticks: Optional[int]
    boot_id: Optional[str]
    pgid: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, data: Optional[dict[str, Any]]) -> Optional["ProcessIdentity"]:
        if not data or data.get("pid") is None:
            return None
        try:
            pid = int(data["pid"])
        except (TypeError, ValueError):
            return None
        start = data.get("starttime_ticks")
        pgid = data.get("pgid")
        return cls(
            pid=pid,
            starttime_ticks=int(start) if start is not None else None,
            boot_id=str(data["boot_id"]) if data.get("boot_id") is not None else None,
            pgid=int(pgid) if pgid is not None else None,
        )


def read_boot_id() -> Optional[str]:
    path = Path("/proc/sys/kernel/random/boot_id")
    try:
        return path.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def read_process_identity(pid: int) -> Optional[ProcessIdentity]:
    """Return live identity for pid, or None if the process does not exist."""
    if pid <= 0:
        return None
    stat_path = Path(f"/proc/{pid}/stat")
    try:
        raw = stat_path.read_text(encoding="utf-8")
    except OSError:
        return None
    # Format: pid (comm) state ... starttime is field 22 (1-based after pid).
    # comm may contain spaces/parentheses; split on last ')' then fields.
    try:
        after_comm = raw.rsplit(")", 1)[1].strip()
        fields = after_comm.split()
        # fields[0]=state, ..., starttime is fields[19] (22nd overall after pid+comm)
        starttime_ticks = int(fields[19])
    except (IndexError, ValueError):
        return None
    try:
        pgid = os.getpgid(pid)
    except OSError:
        pgid = None
    return ProcessIdentity(
        pid=pid,
        starttime_ticks=starttime_ticks,
        boot_id=read_boot_id(),
        pgid=pgid,
    )


def classify_owner_liveness(stored: Optional[ProcessIdentity]) -> OwnerLiveness:
    """Classify previous lease owner for reclaim decisions."""
    if stored is None or stored.pid is None:
        return "unknown"
    if stored.starttime_ticks is None or stored.boot_id is None:
        # Incomplete identity → cannot safely decide death vs reuse.
        return "unknown"
    current_boot = read_boot_id()
    if current_boot is None:
        return "unknown"
    if stored.boot_id != current_boot:
        # Host rebooted: old PID namespace is gone.
        return "dead"
    live = read_process_identity(stored.pid)
    if live is None:
        return "dead"
    if live.starttime_ticks != stored.starttime_ticks:
        # PID reused by a different process.
        return "dead"
    return "alive"
