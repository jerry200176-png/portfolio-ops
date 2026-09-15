#!/usr/bin/env bash
# Pre-resume tip re-exec for RealCodex wait-through dogfood.
# Syncs dogfood-runtime to origin/main, stops the sleeping process, and
# restarts the waiter so GRAPH_DOGFOOD_RESUME_RUN_ID continues the live Run
# (status=quota_wait in live-dogfood-state.json). Safe to re-run.
set -euo pipefail

STATE_DIR="${GRAPH_DOGFOOD_STATE_DIR:-${HOME}/workspace/state/portfolio-ops}"
ROOT="${GRAPH_DOGFOOD_ROOT:-$STATE_DIR/dogfood-runtime}"
WAITER="${GRAPH_DOGFOOD_WAITER:-$STATE_DIR/codex-quota-wait-dogfood.sh}"
WATCHDOG="${GRAPH_DOGFOOD_WATCHDOG:-$STATE_DIR/codex-quota-watchdog.sh}"
PIDFILE="${GRAPH_DOGFOOD_WAITER_PIDFILE:-$STATE_DIR/codex-quota-waiter.pid}"
DONE_MARKER="${STATE_DIR}/real-codex-dogfood.done"
LOG="${STATE_DIR}/codex-quota-preresume.log"
DOGFOOD_PATH="${HOME}/.npm-global/bin:${HOME}/.local/bin:/usr/local/bin:/usr/bin:/bin:${HOME}/workspace/agent-control/bin"

mkdir -p "$STATE_DIR"
log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

if [[ -f "$DONE_MARKER" ]]; then
  log "done_marker present; no re-exec"
  exit 0
fi

# Require quota_wait + run_id so we never orphan / spawn a fresh Goal by mistake.
RUN_ID="$(python3 - "$STATE_DIR/live-dogfood-state.json" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
if not p.is_file():
    raise SystemExit("missing live-dogfood-state.json")
d = json.loads(p.read_text())
if str(d.get("status") or "") != "quota_wait":
    raise SystemExit(f"refuse re-exec: status={d.get('status')!r} (need quota_wait)")
rid = d.get("run_id") or ""
if not rid:
    raise SystemExit("refuse re-exec: missing run_id")
print(rid)
PY
)"
log "preresume_reexec begin run_id=$RUN_ID root=$ROOT"

# Install versioned ops scripts from tip before restart.
if git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$ROOT" fetch origin main --quiet
  git -C "$ROOT" checkout -B main origin/main --quiet
fi
TIP="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
install -m 0755 "$ROOT/scripts/codex-quota-wait-dogfood.sh" "$WAITER"
install -m 0755 "$ROOT/scripts/codex-quota-watchdog.sh" "$WATCHDOG"
if [[ -f "$ROOT/scripts/codex-quota-preresume-reexec.sh" ]]; then
  install -m 0755 "$ROOT/scripts/codex-quota-preresume-reexec.sh" \
    "$STATE_DIR/codex-quota-preresume-reexec.sh"
fi
log "tip=$TIP scripts installed"

# Stop sleeping dogfood + waiter (watchdog may also be running — restart both cleanly).
stop_pid() {
  local pid="$1"
  [[ -n "$pid" ]] || return 0
  kill "$pid" 2>/dev/null || true
  sleep 1
  kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
}
PY="$(pgrep -f 'scripts/graph-schedule-realcodex-dogfood.py' | head -1 || true)"
WAIT="$(cat "$PIDFILE" 2>/dev/null || true)"
WD="$(pgrep -f 'codex-quota-watchdog.sh' | head -1 || true)"
# Prefer live-state PIDs when present.
if [[ -f "$STATE_DIR/live-dogfood-state.json" ]]; then
  mapfile -t _pids < <(python3 - <<PY
import json
d=json.load(open("$STATE_DIR/live-dogfood-state.json"))
for k in ("dogfood_pid","waiter_pid","watchdog_pid"):
    v=d.get(k)
    if v: print(int(v))
PY
)
  for p in "${_pids[@]:-}"; do stop_pid "$p"; done
fi
stop_pid "$PY"
stop_pid "$WAIT"
stop_pid "$WD"
# Also clear any leftover waiter wrapper still attached to old python
pgrep -af 'codex-quota-wait-dogfood.sh' | awk '{print $1}' | while read -r p; do stop_pid "$p"; done
sleep 2
log "stopped prior dogfood/waiter/watchdog"

# Restart watchdog (it starts waiter from tip with clean env).
nohup env -i \
  HOME="${HOME:-/home/jerry}" \
  USER="${USER:-jerry}" \
  PATH="$DOGFOOD_PATH" \
  GRAPH_DOGFOOD_ROOT="$ROOT" \
  GRAPH_DOGFOOD_STATE_DIR="$STATE_DIR" \
  GRAPH_DOGFOOD_RESUME_RUN_ID="$RUN_ID" \
  "$WATCHDOG" >>"$STATE_DIR/codex-quota-watchdog.log" 2>&1 &
echo $! >"$STATE_DIR/codex-quota-watchdog.pid"
log "watchdog_started pid=$(cat "$STATE_DIR/codex-quota-watchdog.pid") tip=$TIP resume=$RUN_ID"
echo "AGENT_LOOP_TICK_realcodex {\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"status\":\"preresume_reexec\",\"tip\":\"$TIP\",\"run_id\":\"$RUN_ID\"}"

# Refresh live state bookkeeping (do not clear quota_wait / run_id).
python3 - <<PY
import json, time
from pathlib import Path
p = Path("$STATE_DIR/live-dogfood-state.json")
d = json.loads(p.read_text())
d["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
d["dogfood_runtime_tip"] = "$TIP"
d["watchdog_pid"] = int(Path("$STATE_DIR/codex-quota-watchdog.pid").read_text().strip())
d["GRAPH_DOGFOOD_RESUME_RUN_ID"] = "$RUN_ID"
d["note"] = "preresume tip re-exec; waiter will auto-resume run while status=quota_wait"
p.write_text(json.dumps(d, indent=2) + "\n")
PY
log "preresume_reexec done"
