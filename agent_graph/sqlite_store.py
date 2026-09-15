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

SCHEMA_VERSION = 2
DEFAULT_BUSY_TIMEOUT_MS = 5000


class StaleStateError(RuntimeError):
    """Compare-and-swap rejected: Run state_version moved under the writer."""


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
  attempt_id TEXT,
  type TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  evidence_refs_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  ingest_key TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS attempts (
  attempt_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES runs(run_id),
  node TEXT NOT NULL,
  worker_type TEXT NOT NULL,
  model_profile TEXT,
  worker_pid INTEGER,
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
  created_at TEXT NOT NULL
);

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

CREATE INDEX IF NOT EXISTS idx_events_run_created ON events(run_id, created_at);
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
                cols = {
                    r[1]
                    for r in conn.execute("PRAGMA table_info(runs)").fetchall()
                }
                if "state_version" not in cols:
                    conn.execute(
                        "ALTER TABLE runs ADD COLUMN state_version INTEGER NOT NULL DEFAULT 0"
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
        # Append order is canonical; do not sort by created_at (clock skew / fixture stamps).
        rows = self._conn.execute(
            "SELECT * FROM events WHERE run_id=? ORDER BY rowid ASC",
            (run_id,),
        ).fetchall()
        return [_row_to_event(r) for r in rows]

    def append_event(
        self,
        event: CanonicalEvent,
        *,
        ingest_key: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> None:
        c = conn or self._conn
        c.execute(
            """
            INSERT INTO events(event_id, run_id, attempt_id, type, payload_json, evidence_refs_json, created_at, ingest_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.run_id,
                event.attempt_id,
                event.type,
                json.dumps(event.payload, sort_keys=True),
                json.dumps(list(event.evidence_refs)),
                event.created_at,
                ingest_key,
            ),
        )

    # --- Attempts / Artifacts ---

    def insert_attempt(self, attempt: Attempt, *, conn: Optional[sqlite3.Connection] = None) -> None:
        c = conn or self._conn
        c.execute(
            """
            INSERT INTO attempts(
              attempt_id, run_id, node, worker_type, model_profile, worker_pid,
              started_at, ended_at, status, result_ingest_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attempt.attempt_id,
                attempt.run_id,
                attempt.node,
                attempt.worker_type,
                attempt.model_profile,
                attempt.worker_pid,
                attempt.started_at,
                attempt.ended_at,
                attempt.status,
                attempt.result_ingest_key,
            ),
        )

    def update_attempt(self, attempt: Attempt, *, conn: Optional[sqlite3.Connection] = None) -> None:
        c = conn or self._conn
        c.execute(
            """
            UPDATE attempts SET ended_at=?, status=?, result_ingest_key=?, worker_pid=?, model_profile=?
            WHERE attempt_id=?
            """,
            (
                attempt.ended_at,
                attempt.status,
                attempt.result_ingest_key,
                attempt.worker_pid,
                attempt.model_profile,
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
            started_at=row["started_at"],
            ended_at=row["ended_at"],
            status=row["status"],
            result_ingest_key=row["result_ingest_key"],
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
    return CanonicalEvent(
        event_id=row["event_id"],
        run_id=row["run_id"],
        attempt_id=row["attempt_id"],
        type=row["type"],
        payload=json.loads(row["payload_json"]),
        evidence_refs=tuple(refs),
        created_at=row["created_at"],
    )
