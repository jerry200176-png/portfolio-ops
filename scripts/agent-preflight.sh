#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -P "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 scripts/validate-governance-contract.py
python3 scripts/validate-company-agent-contract.py
python3 scripts/company-context.py --check
test -f CLAUDE.md
test -f AGENTS.md
if [[ -n "$(git -c core.filemode=false status --porcelain)" ]]; then
  echo "agent-preflight: worktree is dirty" >&2
  git -c core.filemode=false status --short >&2
  exit 1
fi
echo "agent-preflight: portfolio-ops contract, context, and worktree clean"
