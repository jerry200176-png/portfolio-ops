#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -P "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORKTREE="$(pwd)"

[[ -f "$WORKTREE/scripts/agent-preflight.sh" ]] || {
  echo "portfolio-ops preflight script missing" >&2
  exit 1
}

bash "$WORKTREE/scripts/agent-preflight.sh"
git -C "$WORKTREE" -c core.filemode=false status --short
echo "portfolio-ops gateway preflight passed"
