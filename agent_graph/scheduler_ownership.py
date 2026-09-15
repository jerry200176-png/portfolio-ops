"""Single-host autonomous scheduler ownership via execution leases."""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from .process_identity import read_process_identity
from .sqlite_store import (
    LeaseBusyError,
    PreviousWorkerStillAliveError,
    PreviousWorkerUnverifiableError,
    SqliteControlPlaneStore,
    StaleLeaseError,
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _iso_plus_seconds(iso: str, seconds: float) -> str:
    base = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (
        datetime.fromtimestamp(base.timestamp() + seconds, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


SCHEDULER_RESOURCE_PREFIX = "scheduler:"


def scheduler_resource_key(project: str = "portfolio-ops") -> str:
    return f"{SCHEDULER_RESOURCE_PREFIX}{project}"


@dataclass
class SchedulerOwnership:
    """Exclusive scheduler lease for one control-plane DB."""

    store: SqliteControlPlaneStore
    project: str = "portfolio-ops"
    owner_id: str = ""
    lease_id: str = ""
    fencing_token: int = 0
    acquired_at: str = ""
    ttl_sec: float = 30.0

    def __post_init__(self) -> None:
        if not self.owner_id:
            self.owner_id = f"sched_{uuid.uuid4().hex[:12]}"
        if not self.lease_id:
            self.lease_id = f"schedlease_{uuid.uuid4().hex[:12]}"

    @property
    def resource_key(self) -> str:
        return scheduler_resource_key(self.project)

    def try_acquire(self) -> bool:
        now = _utcnow()
        expires = _iso_plus_seconds(now, self.ttl_sec)
        try:
            with self.store.transaction() as conn:
                token = self.store.acquire_execution_lease(
                    resource_key=self.resource_key,
                    attempt_id=self.owner_id,
                    run_id="scheduler",
                    node="loop",
                    now=now,
                    expires_at=expires,
                    lease_id=self.lease_id,
                    conn=conn,
                )
                identity = read_process_identity(os.getpid())
                if identity is not None:
                    self.store.bind_execution_identity(
                        resource_key=self.resource_key,
                        attempt_id=self.owner_id,
                        fencing_token=int(token),
                        identity=identity,
                        conn=conn,
                    )
                self.fencing_token = int(token)
                self.acquired_at = now
            return True
        except (
            LeaseBusyError,
            PreviousWorkerStillAliveError,
            PreviousWorkerUnverifiableError,
        ):
            return False

    def renew(self) -> bool:
        if self.fencing_token <= 0:
            return False
        now = _utcnow()
        expires = _iso_plus_seconds(now, self.ttl_sec)
        try:
            with self.store.transaction() as conn:
                token = self.store.acquire_execution_lease(
                    resource_key=self.resource_key,
                    attempt_id=self.owner_id,
                    run_id="scheduler",
                    node="loop",
                    now=now,
                    expires_at=expires,
                    lease_id=self.lease_id,
                    conn=conn,
                )
                self.fencing_token = int(token)
            return True
        except (
            LeaseBusyError,
            PreviousWorkerStillAliveError,
            PreviousWorkerUnverifiableError,
            StaleLeaseError,
        ):
            return False

    def release(self) -> bool:
        if self.fencing_token <= 0:
            return False
        now = _utcnow()
        try:
            with self.store.transaction() as conn:
                return self.store.release_execution_lease(
                    resource_key=self.resource_key,
                    attempt_id=self.owner_id,
                    fencing_token=self.fencing_token,
                    now=now,
                    conn=conn,
                )
        finally:
            self.fencing_token = 0

    def status(self) -> dict[str, Any]:
        active = self.store.get_active_lease(self.resource_key)
        return {
            "owner_id": self.owner_id,
            "resource_key": self.resource_key,
            "fencing_token": self.fencing_token,
            "acquired_at": self.acquired_at,
            "held": self.fencing_token > 0,
            "active_lease": active,
        }
