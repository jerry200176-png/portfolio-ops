#!/usr/bin/env bash
# Install / refresh the single-host graph scheduler user unit.
# Syncs a stable runtime checkout from origin/main, then enables the unit.
set -euo pipefail

STATE="${HOME}/workspace/state/portfolio-ops"
RUNTIME="${STATE}/scheduler-runtime"
BARE="${HOME}/workspace/repos/portfolio-ops.git"
UNIT_SRC="$(cd "$(dirname "$0")" && pwd)/systemd/graph-scheduler.service"
UNIT_DST="${HOME}/.config/systemd/user/graph-scheduler.service"

mkdir -p "$STATE" "${HOME}/.config/systemd/user"

if [[ ! -d "$BARE" ]]; then
  echo "missing bare repo: $BARE" >&2
  exit 1
fi

git --git-dir="$BARE" fetch origin main --quiet
if [[ -d "$RUNTIME/.git" ]] || git -C "$RUNTIME" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$RUNTIME" fetch origin main --quiet
  git -C "$RUNTIME" checkout -B main origin/main
else
  # Prefer agent-start worktree if available; else plain worktree from bare.
  if command -v agent-start >/dev/null 2>&1; then
    agent-start portfolio-ops scheduler-runtime --dry-run >/dev/null
    # agent-start places under tasks/; symlink for stable path
    SRC="$(ls -d "${HOME}/workspace/tasks/portfolio-ops/"*scheduler-runtime* 2>/dev/null | tail -1 || true)"
    if [[ -n "${SRC:-}" ]]; then
      git -C "$SRC" fetch origin main --quiet || true
      git -C "$SRC" checkout -B main origin/main || true
      ln -sfn "$SRC" "$RUNTIME"
    else
      git --git-dir="$BARE" worktree add --force -B main "$RUNTIME" origin/main
    fi
  else
    git --git-dir="$BARE" worktree add --force -B main "$RUNTIME" origin/main
  fi
fi

# Resolve symlink for WorkingDirectory
RUNTIME_REAL="$(readlink -f "$RUNTIME")"
cp "$UNIT_SRC" "$UNIT_DST"
# Rewrite WorkingDirectory/PYTHONPATH to resolved path if symlinked
sed -i "s|WorkingDirectory=%h/workspace/state/portfolio-ops/scheduler-runtime|WorkingDirectory=${RUNTIME_REAL}|" "$UNIT_DST"
sed -i "s|Environment=PYTHONPATH=%h/workspace/state/portfolio-ops/scheduler-runtime|Environment=PYTHONPATH=${RUNTIME_REAL}|" "$UNIT_DST"

systemctl --user daemon-reload
systemctl --user enable graph-scheduler.service
echo "installed: $UNIT_DST"
echo "runtime: $RUNTIME_REAL @ $(git -C "$RUNTIME_REAL" rev-parse --short HEAD)"
echo "start with: systemctl --user start graph-scheduler.service"
echo "status: systemctl --user status graph-scheduler.service"
echo "ops: PYTHONPATH=$RUNTIME_REAL python3 -m agent_graph.cli --db $STATE/graph-control.sqlite schedule-status"
