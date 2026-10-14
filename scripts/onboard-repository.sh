#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  governance-onboard <owner/repo> [--local-path <path>]
      [--dry-run|--apply] [--enable-ci]

Read-only check that a repository exists. ExoProtocol is retired (Founder
2026-10-14): --apply and --enable-ci are refused, so no .exo/ tree or Exo
workflow is created. New repositories carry the committed
governance/PORTFOLIO_AGENT_CONTRACT.md overlay and are worked on from cloud
sessions. The command never pushes, merges, or changes GitHub rulesets.
EOF
}

[[ $# -ge 1 ]] || { usage; exit 2; }
REPO="$1"
shift
LOCAL_PATH="/home/jerry/workspace/${REPO##*/}"
APPLY=0
ENABLE_CI=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --local-path) LOCAL_PATH="$2"; shift 2 ;;
    --dry-run) APPLY=0; shift ;;
    --apply) APPLY=1; shift ;;
    --enable-ci) ENABLE_CI=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

[[ "$REPO" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || {
  echo "invalid repository slug: $REPO" >&2
  exit 2
}

gh repo view "$REPO" --json name,defaultBranchRef >/dev/null
if [[ "$APPLY" == 1 || "$ENABLE_CI" == 1 ]]; then
  echo "Refusing --apply/--enable-ci: ExoProtocol onboarding is retired (Founder 2026-10-14)." >&2
  exit 2
fi
echo "governance-onboard: dry-run OK: $REPO"
echo "local_path=$LOCAL_PATH"
echo "default session path: Claude cloud session (agent-start is legacy local)"
