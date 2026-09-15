"""SQLite canonical store for the Graph Control Plane (Phase 1A).

- WAL mode
- foreign_keys ON
- events are append-only
- event append + run projection update happen in one transaction
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional

from .durable_models import (
    Attempt,
    CanonicalEvent,
    Goal,
    Run,
)

SCHEMA_VERSION = 5
DEFAULT_BUSY_TIMEOUT_MS = 5000


class StaleStateError(RuntimeError):
    """Compare-and-swap rejected: Run state_version moved under the writer."""


class LeaseBusyError(RuntimeError):
    """Execution lease held by another Attempt (not yet recoverable)."""

    blocker = "lease_busy"


class StaleLeaseError(RuntimeError):
    """Attempt fencing token no longer owns the resource lease."""


class PreviousWorkerStillAliveError(RuntimeError):
    """Expired lease cannot be reclaimed: previous worker process is still alive."""

    blocker = "previous_worker_still_alive"


class PreviousWorkerUnverifiableError(RuntimeError):
    """Expired lease cannot be reclaimed: owner identity cannot be confirmed dead."""

    blocker = "previous_worker_unverifiable"


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS goals (
  goal_id TEXT PRIMARY KEY,
  objective TEXT NOT NULL,
  success_condition TEXT,
  project TEXT NOT NULL,
  risk_tier TEXT NOT NULL DEFAULT 'low',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL REFERENCES goals(goal_id),
  project TEXT NOT NULL,
  graph_version TEXT NOT NULL,
  risk_tier TEXT NOT NULL,
  status TEXT NOT NULL,
  current_node TEXT,
  worktree TEXT,
  branch TEXT,
  base_sha TEXT,
  head_sha TEXT,
  tested_sha TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  blocker TEXT,
  closed INTEGER NOT NULL DEFAULT 0,
  stopped INTEGER NOT NULL DEFAULT 0,
  human_approved INTEGER NOT NULL DEFAULT 0,
  graph_snapshot_json TEXT NOT NULL DEFAULT '{}',
  state_version INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES runs(run_id),
  run_event_seq INTEGER NOT NULL,
  attempt_id TEXT,
  type TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  evidence_refs_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  ingest_key TEXT UNIQUE,
  UNIQUE (run_id, run_event_seq)
);

CREATE TABLE IF NOT EXISTS attempts (
  attempt_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES runs(run_id),
  node TEXT NOT NULL,
  worker_type TEXT NOT NULL,
  model_profile TEXT,
  worker_pid INTEGER,
  expected_state_version INTEGER NOT NULL,
  fencing_token INTEGER NOT NULL DEFAULT 0,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  status TEXT NOT NULL,
  result_ingest_key TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS artifacts (
  artifact_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES runs(run_id),
  attempt_id TEXT,
  kind TEXT NOT NULL,
  uri TEXT NOT NULL,
  sha256 TEXT,
  created_at TEXT NOT NULL
);

-- Minimal interfaces reserved for Phase 1B+ (no behavior in 1A).
CREATE TABLE IF NOT EXISTS leases (
  lease_id TEXT PRIMARY KEY,
  run_id TEXT,
  resource_key TEXT NOT NULL,
  owner TEXT,
  fencing_token INTEGER NOT NULL DEFAULT 0,
  expires_at TEXT,
  created_at TEXT NOT NULL,
  released_at TEXT,
  node TEXT,
  worker_pid INTEGER,
  worker_pgid INTEGER,
  worker_starttime_ticks INTEGER,
  worker_boot_id TEXT,
  identity_status TEXT NOT NULL DEFAULT 'pending'
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_leases_resource_active
  ON leases(resource_key) WHERE released_at IS NULL;

CREATE TABLE IF NOT EXISTS approvals (
  approval_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES runs(run_id),
  scope TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  actor TEXT,
  bound_head_sha TEXT,
  created_at TEXT NOT NULL,
  decided_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_run_seq ON events(run_id, run_event_seq);
CREATE INDEX IF NOT EXISTS idx_attempts_run ON attempts(run_id, started_at);
CREATE INDEX IF NOT EXISTS idx_artifacts_run ON artifacts(run_id);
"""


class SqliteControlPlaneStore:
    """Control-plane-owned SQLite database (never ~/.codex/*.sqlite)."""

    def __init__(
        self,
        path: str | Path,
        *,
        busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
    ) -> None:
        self.path = Path(path)
        self.busy_timeout_ms = int(busy_timeout_ms)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            str(self.path),
            isolation_level=None,  # manual transactions
            check_same_thread=False,
            timeout=max(self.busy_timeout_ms / 1000.0, 0.001),
        )
        self._conn.row_factory = sqlite3.Row
        self._configure()
        self._migrate()

    def _configure(self) -> None:
        cur = self._conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        cur.execute("PRAGMA journal_mode = WAL")
        mode = cur.execute("PRAGMA journal_mode").fetchone()[0]
        if str(mode).lower() != "wal":
            raise RuntimeError(f"failed to enable WAL mode; got {mode!r}")
        # Bounded lock wait: SQLite retries until busy_timeout, then raises.
        cur.execute(f"PRAGMA busy_timeout = {self.busy_timeout_ms}")

    def _migrate(self) -> None:
        # executescript auto-commits; keep it outside an explicit transaction.
        self._conn.executescript(SCHEMA_SQL)
        row = self._conn.execute(
            "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1"
        ).fetchone()
        current = int(row["version"]) if row else 0
        if current < SCHEMA_VERSION:
            with self.transaction() as conn:
                run_cols = {r[1] for r in conn.execute("PRAGMA table_info(runs)").fetchall()}
                if "state_version" not in run_cols:
                    conn.execute(
                        "ALTER TABLE runs ADD COLUMN state_version INTEGER NOT NULL DEFAULT 0"
                    )

                event_cols = {r[1] for r in conn.execute("PRAGMA table_info(events)").fetchall()}
                if "run_event_seq" not in event_cols:
                    conn.execute("ALTER TABLE events ADD COLUMN run_event_seq INTEGER")
                    # Backfill deterministic append order using historical rowid.
                    rows = conn.execute(
                        "SELECT event_id, run_id FROM events ORDER BY run_id ASC, rowid ASC"
                    ).fetchall()
                    counters: dict[str, int] = {}
                    for erow in rows:
                        rid = erow["run_id"]
                        counters[rid] = counters.get(rid, 0) + 1
                        conn.execute(
                            "UPDATE events SET run_event_seq=? WHERE event_id=?",
                            (counters[rid], erow["event_id"]),
                        )
                    conn.execute(
                        "CREATE UNIQUE INDEX IF NOT EXISTS idx_events_run_seq_uq "
                        "ON events(run_id, run_event_seq)"
                    )

                attempt_cols = {
                    r[1] for r in conn.execute("PRAGMA table_info(attempts)").fetchall()
                }
                if "expected_state_version" not in attempt_cols:
                    conn.execute(
                        "ALTER TABLE attempts ADD COLUMN expected_state_version INTEGER NOT NULL DEFAULT 0"
                    )
                if "fencing_token" not in attempt_cols:
                    conn.execute(
                        "ALTER TABLE attempts ADD COLUMN fencing_token INTEGER NOT NULL DEFAULT 0"
                    )

                lease_cols = {
                    r[1] for r in conn.execute("PRAGMA table_info(leases)").fetchall()
                }
                if "released_at" not in lease_cols:
                    conn.execute("ALTER TABLE leases ADD COLUMN released_at TEXT")
                if "node" not in lease_cols:
                    conn.execute("ALTER TABLE leases ADD COLUMN node TEXT")
                for col, decl in (
                    ("worker_pid", "INTEGER"),
                    ("worker_pgid", "INTEGER"),
                    ("worker_starttime_ticks", "INTEGER"),
                    ("worker_boot_id", "TEXT"),
                    ("identity_status", "TEXT NOT NULL DEFAULT 'pending'"),
                ):
                    if col not in lease_cols:
                        conn.execute(f"ALTER TABLE leases ADD COLUMN {col} {decl}")
                conn.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_leases_resource_active "
                    "ON leases(resource_key) WHERE released_at IS NULL"
                )

                conn.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, datetime('now'))",
                    (SCHEMA_VERSION,),
                )

    def close(self) -> None:
        self._conn.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield self._conn
            self._conn.execute("COMMIT")
        except Exception:
            try:
                self._conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise

    # --- Goals / Runs ---

    def insert_goal(self, goal: Goal, *, conn: Optional[sqlite3.Connection] = None) -> None:
        c = conn or self._conn
        c.execute(
            """
            INSERT INTO goals(goal_id, objective, success_condition, project, risk_tier, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                goal.goal_id,
                goal.objective,
                goal.success_condition,
                goal.project,
                goal.risk_tier,
                goal.created_at,
            ),
        )

    def insert_run(self, run: Run, *, conn: Optional[sqlite3.Connection] = None) -> None:
        c = conn or self._conn
        c.execute(
            """
            INSERT INTO runs(
              run_id, goal_id, project, graph_version, risk_tier, status, current_node,
              worktree, branch, base_sha, head_sha, tested_sha, created_at, updated_at,
              blocker, closed, stopped, human_approved, graph_snapshot_json, state_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run.run_id,
                run.goal_id,
                run.project,
                run.graph_version,
                run.risk_tier,
                run.status,
                run.current_node,
                run.worktree,
                run.branch,
                run.base_sha,
                run.head_sha,
                run.tested_sha,
                run.created_at,
                run.updated_at,
                run.blocker,
                1 if run.closed else 0,
                1 if run.stopped else 0,
                1 if run.human_approved else 0,
                json.dumps(run.graph_snapshot, sort_keys=True),
                int(run.state_version),
            ),
        )

    def update_run_projection(
        self,
        run: Run,
        *,
        expected_version: int,
        conn: Optional[sqlite3.Connection] = None,
    ) -> int:
        """CAS update: succeeds only when persisted state_version == expected_version."""
        c = conn or self._conn
        new_version = int(expected_version) + 1
        cur = c.execute(
            """
            UPDATE runs SET
              status=?, current_node=?, worktree=?, branch=?, base_sha=?, head_sha=?,
              tested_sha=?, updated_at=?, blocker=?, closed=?, stopped=?, human_approved=?,
              graph_snapshot_json=?, state_version=?
            WHERE run_id=? AND state_version=?
            """,
            (
                run.status,
                run.current_node,
                run.worktree,
                run.branch,
                run.base_sha,
                run.head_sha,
                run.tested_sha,
                run.updated_at,
                run.blocker,
                1 if run.closed else 0,
                1 if run.stopped else 0,
                1 if run.human_approved else 0,
                json.dumps(run.graph_snapshot, sort_keys=True),
                new_version,
                run.run_id,
                int(expected_version),
            ),
        )
        if cur.rowcount != 1:
            actual = None
            row = c.execute(
                "SELECT state_version FROM runs WHERE run_id=?", (run.run_id,)
            ).fetchone()
            if row is not None:
                actual = int(row["state_version"])
            raise StaleStateError(
                f"stale state_version for {run.run_id}: expected={expected_version} actual={actual}"
            )
        run.state_version = new_version
        return new_version

    def get_run(
        self, run_id: str, *, conn: Optional[sqlite3.Connection] = None
    ) -> Optional[Run]:
        c = conn or self._conn
        row = c.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None:
            return None
        return _row_to_run(row)

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        row = self._conn.execute("SELECT * FROM goals WHERE goal_id=?", (goal_id,)).fetchone()
        if row is None:
            return None
        return Goal(
            goal_id=row["goal_id"],
            objective=row["objective"],
            success_condition=row["success_condition"],
            project=row["project"],
            risk_tier=row["risk_tier"],
            created_at=row["created_at"],
        )

    # --- Events ---

    def get_event(self, event_id: str) -> Optional[CanonicalEvent]:
        row = self._conn.execute("SELECT * FROM events WHERE event_id=?", (event_id,)).fetchone()
        if row is None:
            return None
        return _row_to_event(row)

    def get_event_by_ingest_key(self, ingest_key: str) -> Optional[CanonicalEvent]:
        row = self._conn.execute("SELECT * FROM events WHERE ingest_key=?", (ingest_key,)).fetchone()
        if row is None:
            return None
        return _row_to_event(row)

    def list_events(self, run_id: str) -> list[CanonicalEvent]:
        # Explicit persisted sequence is the only canonical ordering contract.
        rows = self._conn.execute(
            "SELECT * FROM events WHERE run_id=? ORDER BY run_event_seq ASC",
            (run_id,),
        ).fetchall()
        return [_row_to_event(r) for r in rows]

    def allocate_run_event_seq(
        self, run_id: str, *, conn: Optional[sqlite3.Connection] = None
    ) -> int:
        c = conn or self._conn
        row = c.execute(
            "SELECT COALESCE(MAX(run_event_seq), 0) AS mx FROM events WHERE run_id=?",
            (run_id,),
        ).fetchone()
        return int(row["mx"]) + 1

    def append_event(
        self,
        event: CanonicalEvent,
        *,
        ingest_key: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> CanonicalEvent:
        """Append event with explicit run_event_seq. Caller must be in a write TX.

        If event_id already exists, returns the persisted event (idempotent) and
        does not allocate a new sequence number.
        """
        c = conn or self._conn
        existing = c.execute(
            "SELECT * FROM events WHERE event_id=?", (event.event_id,)
        ).fetchone()
        if existing is not None:
            return _row_to_event(existing)

        seq = event.run_event_seq
        if seq <= 0:
            seq = self.allocate_run_event_seq(event.run_id, conn=c)
        stored = CanonicalEvent(
            event_id=event.event_id,
            run_id=event.run_id,
            run_event_seq=seq,
            attempt_id=event.attempt_id,
            type=event.type,
            payload=dict(event.payload),
            evidence_refs=tuple(event.evidence_refs),
            created_at=event.created_at,
        )
        c.execute(
            """
            INSERT INTO events(
              event_id, run_id, run_event_seq, attempt_id, type, payload_json,
              evidence_refs_json, created_at, ingest_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stored.event_id,
                stored.run_id,
                stored.run_event_seq,
                stored.attempt_id,
                stored.type,
                json.dumps(stored.payload, sort_keys=True),
                json.dumps(list(stored.evidence_refs)),
                stored.created_at,
                ingest_key,
            ),
        )
        return stored

    # --- Attempts / Artifacts ---

    def insert_attempt(self, attempt: Attempt, *, conn: Optional[sqlite3.Connection] = None) -> None:
        c = conn or self._conn
        c.execute(
            """
            INSERT INTO attempts(
              attempt_id, run_id, node, worker_type, model_profile, worker_pid,
              expected_state_version, started_at, ended_at, status, result_ingest_key,
              fencing_token
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attempt.attempt_id,
                attempt.run_id,
                attempt.node,
                attempt.worker_type,
                attempt.model_profile,
                attempt.worker_pid,
                int(attempt.expected_state_version),
                attempt.started_at,
                attempt.ended_at,
                attempt.status,
                attempt.result_ingest_key,
                int(attempt.fencing_token),
            ),
        )

    def update_attempt(self, attempt: Attempt, *, conn: Optional[sqlite3.Connection] = None) -> None:
        c = conn or self._conn
        c.execute(
            """
            UPDATE attempts SET ended_at=?, status=?, result_ingest_key=?, worker_pid=?,
              model_profile=?, fencing_token=?
            WHERE attempt_id=?
            """,
            (
                attempt.ended_at,
                attempt.status,
                attempt.result_ingest_key,
                attempt.worker_pid,
                attempt.model_profile,
                int(attempt.fencing_token),
                attempt.attempt_id,
            ),
        )

    def get_attempt(self, attempt_id: str) -> Optional[Attempt]:
        row = self._conn.execute("SELECT * FROM attempts WHERE attempt_id=?", (attempt_id,)).fetchone()
        if row is None:
            return None
        return Attempt(
            attempt_id=row["attempt_id"],
            run_id=row["run_id"],
            node=row["node"],
            worker_type=row["worker_type"],
            model_profile=row["model_profile"],
            worker_pid=row["worker_pid"],
            expected_state_version=int(row["expected_state_version"]),
            started_at=row["started_at"],
            ended_at=row["ended_at"],
            status=row["status"],
            result_ingest_key=row["result_ingest_key"],
            fencing_token=int(row["fencing_token"]) if "fencing_token" in row.keys() else 0,
        )

    def update_run_ephemeral_status(
        self,
        run_id: str,
        *,
        status: str,
        updated_at: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> None:
        """Update non-graph status fields without bumping state_version."""
        c = conn or self._conn
        c.execute(
            "UPDATE runs SET status=?, updated_at=? WHERE run_id=?",
            (status, updated_at, run_id),
        )

    def get_attempt_by_ingest_key(self, ingest_key: str) -> Optional[Attempt]:
        row = self._conn.execute(
            "SELECT * FROM attempts WHERE result_ingest_key=?", (ingest_key,)
        ).fetchone()
        if row is None:
            return None
        return self.get_attempt(row["attempt_id"])

    def insert_artifact(
        self,
        *,
        artifact_id: str,
        run_id: str,
        kind: str,
        uri: str,
        created_at: str,
        attempt_id: Optional[str] = None,
        sha256: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> None:
        c = conn or self._conn
        c.execute(
            """
            INSERT INTO artifacts(artifact_id, run_id, attempt_id, kind, uri, sha256, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (artifact_id, run_id, attempt_id, kind, uri, sha256, created_at),
        )

    def list_artifacts(self, run_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM artifacts WHERE run_id=? ORDER BY created_at ASC, rowid ASC",
            (run_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def pragma_journal_mode(self) -> str:
        return str(self._conn.execute("PRAGMA journal_mode").fetchone()[0]).lower()

    # --- Execution leases (Phase 1B) ---

    def _lease_row_identity(self, row: sqlite3.Row) -> Optional[dict[str, Any]]:
        keys = set(row.keys())
        if "worker_pid" not in keys or row["worker_pid"] is None:
            return None
        return {
            "pid": int(row["worker_pid"]),
            "pgid": int(row["worker_pgid"]) if row["worker_pgid"] is not None else None,
            "starttime_ticks": int(row["worker_starttime_ticks"])
            if row["worker_starttime_ticks"] is not None
            else None,
            "boot_id": row["worker_boot_id"],
        }

    def acquire_execution_lease(
        self,
        *,
        resource_key: str,
        attempt_id: str,
        run_id: str,
        node: str,
        now: str,
        expires_at: str,
        lease_id: str,
        conn: Optional[sqlite3.Connection] = None,
        allow_reclaim_dead: bool = True,
    ) -> int:
        """Acquire exclusive lease; returns fencing_token.

        Expiry does NOT authorize takeover. Reclaim requires the previous
        worker process identity to be confirmed dead.
        """
        from .process_identity import ProcessIdentity, classify_owner_liveness

        c = conn or self._conn
        active = c.execute(
            """
            SELECT * FROM leases
            WHERE resource_key=? AND released_at IS NULL
            ORDER BY fencing_token DESC LIMIT 1
            """,
            (resource_key,),
        ).fetchone()

        if active is not None and active["owner"] == attempt_id:
            prior = c.execute(
                "SELECT COALESCE(MAX(fencing_token), 0) AS mx FROM leases WHERE resource_key=?",
                (resource_key,),
            ).fetchone()
            token = int(prior["mx"]) + 1
            c.execute(
                """
                UPDATE leases SET fencing_token=?, expires_at=?, run_id=?, node=?, created_at=?
                WHERE lease_id=?
                """,
                (token, expires_at, run_id, node, now, active["lease_id"]),
            )
            return token

        if active is not None:
            expired = bool(active["expires_at"] and active["expires_at"] <= now)
            if not expired:
                raise LeaseBusyError(
                    f"resource {resource_key} held by {active['owner']} "
                    f"(token={active['fencing_token']})"
                )
            # Expired → reconciliation required (not automatic takeover).
            identity_status = (
                active["identity_status"] if "identity_status" in active.keys() else None
            ) or "pending"
            if identity_status == "pending" or not allow_reclaim_dead:
                raise PreviousWorkerUnverifiableError(
                    f"resource {resource_key}: expired lease owner={active['owner']} "
                    f"identity_status={identity_status}; reconciliation required"
                )
            stored = ProcessIdentity.from_mapping(self._lease_row_identity(active))
            liveness = classify_owner_liveness(stored)
            if liveness == "alive":
                raise PreviousWorkerStillAliveError(
                    f"resource {resource_key}: previous worker still alive "
                    f"(owner={active['owner']} pid={active['worker_pid']})"
                )
            if liveness != "dead":
                raise PreviousWorkerUnverifiableError(
                    f"resource {resource_key}: previous worker identity unverifiable "
                    f"(owner={active['owner']} liveness={liveness})"
                )
            # Confirmed dead: reclaim — release old lease, mark attempt recovered.
            c.execute(
                "UPDATE leases SET released_at=? WHERE lease_id=? AND released_at IS NULL",
                (now, active["lease_id"]),
            )
            old_attempt = c.execute(
                "SELECT * FROM attempts WHERE attempt_id=?", (active["owner"],)
            ).fetchone()
            if old_attempt is not None and old_attempt["status"] in ("started", "failed"):
                c.execute(
                    """
                    UPDATE attempts SET status=?, ended_at=COALESCE(ended_at, ?)
                    WHERE attempt_id=?
                    """,
                    ("orphaned", now, active["owner"]),
                )

        prior = c.execute(
            "SELECT COALESCE(MAX(fencing_token), 0) AS mx FROM leases WHERE resource_key=?",
            (resource_key,),
        ).fetchone()
        token = int(prior["mx"]) + 1
        c.execute(
            """
            INSERT INTO leases(
              lease_id, run_id, resource_key, owner, fencing_token,
              expires_at, created_at, released_at, node,
              worker_pid, worker_pgid, worker_starttime_ticks, worker_boot_id,
              identity_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, NULL, NULL, NULL, NULL, 'pending')
            """,
            (lease_id, run_id, resource_key, attempt_id, token, expires_at, now, node),
        )
        return token

    def bind_execution_identity(
        self,
        *,
        resource_key: str,
        attempt_id: str,
        fencing_token: int,
        identity: "ProcessIdentity",
        conn: Optional[sqlite3.Connection] = None,
    ) -> None:
        from .process_identity import ProcessIdentity as _PI

        assert isinstance(identity, _PI)
        c = conn or self._conn
        cur = c.execute(
            """
            UPDATE leases SET
              worker_pid=?, worker_pgid=?, worker_starttime_ticks=?, worker_boot_id=?,
              identity_status='bound'
            WHERE resource_key=? AND owner=? AND fencing_token=? AND released_at IS NULL
            """,
            (
                identity.pid,
                identity.pgid,
                identity.starttime_ticks,
                identity.boot_id,
                resource_key,
                attempt_id,
                int(fencing_token),
            ),
        )
        if cur.rowcount < 1:
            raise StaleLeaseError(
                f"cannot bind identity; lease not held for {resource_key} "
                f"owner={attempt_id} token={fencing_token}"
            )

    def release_execution_lease(
        self,
        *,
        resource_key: str,
        attempt_id: str,
        fencing_token: int,
        now: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> bool:
        c = conn or self._conn
        cur = c.execute(
            """
            UPDATE leases SET released_at=?
            WHERE resource_key=? AND owner=? AND fencing_token=? AND released_at IS NULL
            """,
            (now, resource_key, attempt_id, int(fencing_token)),
        )
        return cur.rowcount > 0

    def get_active_lease(
        self, resource_key: str, *, now: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        """Return unreclaimed lease for resource (expiry does not clear ownership)."""
        del now  # retained for API compatibility; expiry is not auto-clear.
        row = self._conn.execute(
            """
            SELECT * FROM leases
            WHERE resource_key=? AND released_at IS NULL
            ORDER BY fencing_token DESC LIMIT 1
            """,
            (resource_key,),
        ).fetchone()
        return dict(row) if row else None

    def assert_lease_fence(
        self,
        *,
        resource_key: str,
        attempt_id: str,
        fencing_token: int,
        now: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> None:
        del now
        c = conn or self._conn
        row = c.execute(
            """
            SELECT * FROM leases
            WHERE resource_key=? AND released_at IS NULL
            ORDER BY fencing_token DESC LIMIT 1
            """,
            (resource_key,),
        ).fetchone()
        if row is None:
            raise StaleLeaseError(f"no active lease for {resource_key}")
        if row["owner"] != attempt_id or int(row["fencing_token"]) != int(fencing_token):
            raise StaleLeaseError(
                f"stale fencing token for {resource_key}: "
                f"have owner={attempt_id} token={fencing_token}, "
                f"active owner={row['owner']} token={row['fencing_token']}"
            )


def _row_to_run(row: sqlite3.Row) -> Run:
    keys = set(row.keys())
    return Run(
        run_id=row["run_id"],
        goal_id=row["goal_id"],
        project=row["project"],
        graph_version=row["graph_version"],
        risk_tier=row["risk_tier"],
        status=row["status"],
        current_node=row["current_node"],
        worktree=row["worktree"],
        branch=row["branch"],
        base_sha=row["base_sha"],
        head_sha=row["head_sha"],
        tested_sha=row["tested_sha"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        blocker=row["blocker"],
        closed=bool(row["closed"]),
        stopped=bool(row["stopped"]),
        human_approved=bool(row["human_approved"]),
        graph_snapshot=json.loads(row["graph_snapshot_json"] or "{}"),
        state_version=int(row["state_version"]) if "state_version" in keys else 0,
    )


def _row_to_event(row: sqlite3.Row) -> CanonicalEvent:
    refs = json.loads(row["evidence_refs_json"] or "[]")
    keys = set(row.keys())
    seq = int(row["run_event_seq"]) if "run_event_seq" in keys and row["run_event_seq"] is not None else 0
    return CanonicalEvent(
        event_id=row["event_id"],
        run_id=row["run_id"],
        run_event_seq=seq,
        attempt_id=row["attempt_id"],
        type=row["type"],
        payload=json.loads(row["payload_json"]),
        evidence_refs=tuple(refs),
        created_at=row["created_at"],
    )
