#!/usr/bin/env bash
# Start schedule RealCodex dogfood; waits through Codex quota when needed.
# Install to $GRAPH_DOGFOOD_STATE_DIR via scripts/install-graph-realcodex-dogfood-ops.sh
set -uo pipefail

STATE_DIR="${GRAPH_DOGFOOD_STATE_DIR:-${HOME}/workspace/state/portfolio-ops}"
ROOT="${GRAPH_DOGFOOD_ROOT:-${STATE_DIR}/dogfood-runtime}"
LOG="${STATE_DIR}/codex-quota-retry.log"
DONE_MARKER="${STATE_DIR}/real-codex-dogfood.done"
DOGFOOD_SCRIPT="${GRAPH_DOGFOOD_SCRIPT:-$ROOT/scripts/graph-schedule-realcodex-dogfood.py}"

# Prefer explicit epoch; else optional local datetime; else leave unset for adapter parse.
if [[ -n "${GRAPH_CODEX_QUOTA_RESUME_EPOCH:-}" ]]; then
  RESET_EPOCH="$GRAPH_CODEX_QUOTA_RESUME_EPOCH"
elif [[ -n "${GRAPH_CODEX_QUOTA_RESUME_LOCAL:-}" ]]; then
  RESET_EPOCH=$(date -u -d "$GRAPH_CODEX_QUOTA_RESUME_LOCAL" +%s)
else
  # Default matches the live ChatGPT Codex reset observed 2026-09-15.
  RESET_EPOCH=$(date -u -d '2026-09-19 08:26:00' +%s)
fi

mkdir -p "$STATE_DIR" "$ROOT/.agent-session"
cd "$ROOT"

tick() {
  local payload="$1"
  echo "AGENT_LOOP_TICK_realcodex $payload"
  echo "AGENT_LOOP_TICK_realcodex $payload" >>"$LOG"
}

log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" >>"$LOG"
}

if [[ -f "$DONE_MARKER" ]]; then
  tick "{\"status\":\"already_done\"}"
  exit 0
fi

tick "{\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"status\":\"dogfood_start_wait_through_quota\",\"reset_epoch\":$RESET_EPOCH,\"root\":\"$ROOT\"}"
log "starting wait-through schedule dogfood tip=$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
set +e
# Force live budgets — do not inherit short test env from parent shells.
# `codex` lives under npm-global; env -i parents often omit it.
export PATH="${HOME}/.npm-global/bin:${HOME}/.local/bin:/usr/local/bin:/usr/bin:/bin:${HOME}/workspace/agent-control/bin${PATH:+:$PATH}"
if ! command -v codex >/dev/null 2>&1; then
  tick "{\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"status\":\"codex_missing_on_path\"}"
  exit 1
fi
# Optional: continue an existing Run after tip re-exec at quota resume.
# Only auto-load when live state is still in quota_wait (avoid trapping fresh starts).
if [[ -z "${GRAPH_DOGFOOD_RESUME_RUN_ID:-}" && -f "${STATE_DIR}/live-dogfood-state.json" ]]; then
  GRAPH_DOGFOOD_RESUME_RUN_ID="$(
    STATE_JSON="${STATE_DIR}/live-dogfood-state.json" python3 - <<'PY'
import json, os
from pathlib import Path
d = json.loads(Path(os.environ["STATE_JSON"]).read_text())
if str(d.get("status") or "") == "quota_wait":
    print(d.get("run_id") or "")
PY
  )"
  export GRAPH_DOGFOOD_RESUME_RUN_ID
fi
env \
  PATH="$PATH" \
  GRAPH_REAL_CODEX=1 \
  GRAPH_REAL_CODEX_TIMEOUT="${GRAPH_REAL_CODEX_TIMEOUT:-1200}" \
  GRAPH_DOGFOOD_MAX_TICKS="${GRAPH_DOGFOOD_MAX_TICKS:-500}" \
  GRAPH_DOGFOOD_POLL="${GRAPH_DOGFOOD_POLL:-5}" \
  GRAPH_DOGFOOD_SLEEP_CAP="${GRAPH_DOGFOOD_SLEEP_CAP:-45}" \
  GRAPH_DOGFOOD_MAX_POLL="${GRAPH_DOGFOOD_MAX_POLL:-45}" \
  GRAPH_DOGFOOD_WALL_SEC="${GRAPH_DOGFOOD_WALL_SEC:-604800}" \
  GRAPH_DOGFOOD_QUOTA_SLEEP_CAP="${GRAPH_DOGFOOD_QUOTA_SLEEP_CAP:-3600}" \
  GRAPH_DOGFOOD_LEASE_TTL="${GRAPH_DOGFOOD_LEASE_TTL:-300}" \
  GRAPH_DOGFOOD_NO_PROGRESS_LIMIT="${GRAPH_DOGFOOD_NO_PROGRESS_LIMIT:-8}" \
  GRAPH_CODEX_QUOTA_RESUME_EPOCH="$RESET_EPOCH" \
  GRAPH_CONTROL_DB="${GRAPH_CONTROL_DB:-$STATE_DIR/graph-control-sched-dogfood.sqlite}" \
  GRAPH_DOGFOOD_ROOT="$ROOT" \
  GRAPH_DOGFOOD_STATE_JSON="${GRAPH_DOGFOOD_STATE_JSON:-$STATE_DIR/live-dogfood-state.json}" \
  GRAPH_DOGFOOD_RESUME_RUN_ID="${GRAPH_DOGFOOD_RESUME_RUN_ID:-}" \
  python3 "$DOGFOOD_SCRIPT" >>"$LOG" 2>&1
code=$?
set -e
tick "{\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"status\":\"dogfood_exit\",\"code\":$code}"
if [[ "$code" -eq 0 ]]; then
  date -u +%Y-%m-%dT%H:%M:%SZ >"$DONE_MARKER"
  mkdir -p "$STATE_DIR/evidence"
  stamp="$(date -u +%Y-%m-%d)"
  if [[ -d "$ROOT/reports/$stamp/schedule-realcodex-dogfood" ]]; then
    cp -a "$ROOT/reports/$stamp/schedule-realcodex-dogfood" \
      "$STATE_DIR/evidence/schedule-realcodex-dogfood-$stamp" || true
  fi
  if [[ -f "$ROOT/scripts/graph-v1-completion-audit.py" ]]; then
    python3 "$ROOT/scripts/graph-v1-completion-audit.py" >>"$LOG" 2>&1 || true
  fi
  tick "{\"status\":\"closed_success\",\"done\":true}"
  exit 0
fi
exit "$code"
