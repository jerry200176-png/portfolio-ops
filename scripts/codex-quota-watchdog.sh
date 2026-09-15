#!/usr/bin/env bash
# Watchdog: keep wait-through RealCodex dogfood alive until DONE_MARKER.
# Restarts from tip on process death or stale scheduler ownership lease.
set -uo pipefail

STATE_DIR="${GRAPH_DOGFOOD_STATE_DIR:-${HOME}/workspace/state/portfolio-ops}"
ROOT="${GRAPH_DOGFOOD_ROOT:-$STATE_DIR/dogfood-runtime}"
WAITER="${GRAPH_DOGFOOD_WAITER:-$STATE_DIR/codex-quota-wait-dogfood.sh}"
PIDFILE="${GRAPH_DOGFOOD_WAITER_PIDFILE:-$STATE_DIR/codex-quota-waiter.pid}"
DONE_MARKER="${STATE_DIR}/real-codex-dogfood.done"
LOG="${STATE_DIR}/codex-quota-watchdog.log"
DB="${GRAPH_CONTROL_DB:-$STATE_DIR/graph-control-sched-dogfood.sqlite}"
POLL_SEC="${WATCHDOG_POLL_SEC:-300}"
LEASE_STALE_GRACE_SEC="${WATCHDOG_LEASE_STALE_GRACE_SEC:-120}"
DOGFOOD_PATH="${HOME}/.npm-global/bin:${HOME}/.local/bin:/usr/local/bin:/usr/bin:/bin:${HOME}/workspace/agent-control/bin"

mkdir -p "$STATE_DIR"
cd "$ROOT" || exit 1

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

dogfood_python_pid() {
  pgrep -f 'scripts/graph-schedule-realcodex-dogfood.py' | head -1 || true
}

dogfood_alive() {
  if [[ -f "$PIDFILE" ]]; then
    local pid
    pid="$(cat "$PIDFILE" 2>/dev/null || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
  fi
  local py
  py="$(dogfood_python_pid)"
  [[ -n "$py" ]] && kill -0 "$py" 2>/dev/null
}

lease_stale() {
  [[ -f "$DB" ]] || return 1
  python3 - "$DB" "$LEASE_STALE_GRACE_SEC" <<'PY'
import sys, sqlite3, time
from datetime import datetime, timezone
db, grace = sys.argv[1], float(sys.argv[2])
con = sqlite3.connect(db)
row = con.execute(
    "select expires_at, worker_pid from leases "
    "where resource_key='scheduler:portfolio-ops' and released_at is null "
    "order by rowid desc limit 1"
).fetchone()
if not row or not row[0]:
    sys.exit(1)
exp = datetime.fromisoformat(row[0].replace("Z", "+00:00")).timestamp()
sys.exit(0 if time.time() > exp + grace else 1)
PY
}

stop_dogfood() {
  local py waiter
  py="$(dogfood_python_pid)"
  waiter="$(cat "$PIDFILE" 2>/dev/null || true)"
  [[ -n "$py" ]] && kill "$py" 2>/dev/null || true
  [[ -n "$waiter" ]] && kill "$waiter" 2>/dev/null || true
  sleep 2
  [[ -n "$py" ]] && kill -9 "$py" 2>/dev/null || true
  [[ -n "$waiter" ]] && kill -9 "$waiter" 2>/dev/null || true
}

sync_tip() {
  if git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git -C "$ROOT" fetch origin main --quiet || true
    git -C "$ROOT" checkout -B main origin/main --quiet || true
  fi
}

refresh_live_pids() {
  local waiter_pid dog_pid tip
  waiter_pid="$(cat "$PIDFILE" 2>/dev/null || true)"
  dog_pid="$(dogfood_python_pid)"
  tip="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
  STATE_JSON="$STATE_DIR/live-dogfood-state.json" \
  WAITER_PID="$waiter_pid" DOG_PID="$dog_pid" WD_PID="$$" TIP="$tip" \
  python3 - <<'PY' || true
import json, os, time
from pathlib import Path
p = Path(os.environ["STATE_JSON"])
d = {}
if p.is_file():
    try:
        d = json.loads(p.read_text())
    except json.JSONDecodeError:
        d = {}
d["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
d["watchdog_pid"] = int(os.environ.get("WD_PID") or 0) or d.get("watchdog_pid")
if os.environ.get("WAITER_PID"):
    d["waiter_pid"] = int(os.environ["WAITER_PID"])
if os.environ.get("DOG_PID"):
    d["dogfood_pid"] = int(os.environ["DOG_PID"])
d["dogfood_runtime_tip"] = os.environ.get("TIP") or d.get("dogfood_runtime_tip")
d["dogfood_alive"] = bool(os.environ.get("DOG_PID"))
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(d, indent=2) + "\n")
PY
}

start_dogfood() {
  sync_tip
  # Install tip waiter/watchdog so restarts pick up RESUME_RUN_ID wiring.
  if [[ -f "$ROOT/scripts/codex-quota-wait-dogfood.sh" ]]; then
    install -m 0755 "$ROOT/scripts/codex-quota-wait-dogfood.sh" "$WAITER"
  fi
  nohup env -i \
    HOME="${HOME:-/home/jerry}" \
    USER="${USER:-jerry}" \
    PATH="$DOGFOOD_PATH" \
    GRAPH_DOGFOOD_ROOT="$ROOT" \
    GRAPH_DOGFOOD_STATE_DIR="$STATE_DIR" \
    ${GRAPH_DOGFOOD_RESUME_RUN_ID:+GRAPH_DOGFOOD_RESUME_RUN_ID="$GRAPH_DOGFOOD_RESUME_RUN_ID"} \
    "$WAITER" >>"$STATE_DIR/codex-quota-retry.log" 2>&1 &
  echo $! >"$PIDFILE"
  refresh_live_pids
  log "restarted dogfood waiter pid=$(cat "$PIDFILE") tip=$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
  echo "AGENT_LOOP_TICK_realcodex {\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"status\":\"watchdog_restart\",\"pid\":$(cat "$PIDFILE")}"
}

log "watchdog_started poll=${POLL_SEC}s root=$ROOT stale_grace=${LEASE_STALE_GRACE_SEC}s"

while true; do
  if [[ -f "$DONE_MARKER" ]]; then
    log "done_marker present; exiting"
    echo "AGENT_LOOP_TICK_realcodex {\"status\":\"closed_success\",\"via\":\"watchdog\"}"
    exit 0
  fi
  if dogfood_alive; then
    refresh_live_pids
    if lease_stale; then
      log "scheduler_lease_stale; restarting dogfood"
      stop_dogfood
      start_dogfood
    fi
  else
    log "dogfood_not_alive; starting"
    start_dogfood
  fi
  sleep "$POLL_SEC"
done
