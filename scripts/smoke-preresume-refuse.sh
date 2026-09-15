#!/usr/bin/env bash
# Smoke: preresume reexec refuses non-quota_wait without touching live dogfood.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP"
cat >"$TMP/live-dogfood-state.json" <<'EOF'
{"status":"closed_success","run_id":"run_fake"}
EOF

set +e
GRAPH_DOGFOOD_STATE_DIR="$TMP" \
GRAPH_DOGFOOD_ROOT="$TMP" \
  bash "$ROOT/scripts/codex-quota-preresume-reexec.sh" >"$TMP/out" 2>&1
code=$?
set -e
if [[ "$code" -eq 0 ]]; then
  echo "expected non-zero refuse for closed_success" >&2
  cat "$TMP/out" >&2
  exit 1
fi
if ! grep -q 'refuse re-exec' "$TMP/out" "$TMP/codex-quota-preresume.log" 2>/dev/null; then
  # log may hold the message via tee
  if ! grep -rq 'refuse re-exec' "$TMP"; then
    echo "missing refuse message" >&2
    cat "$TMP/out" >&2
    exit 1
  fi
fi
echo "ok: preresume refuses closed_success"
