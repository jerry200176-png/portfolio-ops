#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  governance-onboard <owner/repo> [--local-path <path>]
      [--dry-run|--apply] [--enable-ci]

Default is read-only. --apply creates an isolated onboarding worktree and
installs the pinned ExoProtocol governance core plus only missing adapters.
Existing adapters are never overwritten. --enable-ci is a second-stage action
for a repository that already has .exo/; it adds Exo's CI workflow separately.
The command never pushes, merges, or changes GitHub rulesets.
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
if [[ "$APPLY" == 0 ]]; then
  echo "governance-onboard: dry-run OK: $REPO"
  echo "local_path=$LOCAL_PATH"
  if [[ "$ENABLE_CI" == 1 ]]; then
    echo "would add .github/workflows/exo-governance.yml in a second-stage worktree"
  else
    echo "would create .exo/ and generate only missing adapters"
    echo "CI is intentionally a second-stage action: add --enable-ci after bootstrap merges"
  fi
  exit 0
fi

command -v exo >/dev/null || {
  echo "exo is required; install exoprotocol==0.2.3 in the governed runtime" >&2
  exit 1
}

OVERLAY_TEMPLATE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../governance" && pwd)/PORTFOLIO_AGENT_CONTRACT.md"
[[ -f "$OVERLAY_TEMPLATE" ]] || {
  echo "governance overlay template missing: $OVERLAY_TEMPLATE" >&2
  exit 1
}

append_overlay_pointer() {
  local adapter="$1"
  if ! grep -Fq "governance/PORTFOLIO_AGENT_CONTRACT.md" "$adapter"; then
    cat >> "$adapter" <<'EOF'

## Portfolio governance overlay

Read `governance/PORTFOLIO_AGENT_CONTRACT.md` before writing. It is committed
for cloud/mobile agents and contains the company's PR, approval, production,
and Founder-approval boundaries.
EOF
  fi
}

if [[ ! -d "$LOCAL_PATH/.git" ]]; then
  mkdir -p "$(dirname "$LOCAL_PATH")"
  gh repo clone "$REPO" "$LOCAL_PATH"
fi

[[ -z "$(git -C "$LOCAL_PATH" status --porcelain)" ]] || {
  echo "refusing dirty repository: $LOCAL_PATH" >&2
  exit 1
}

git -C "$LOCAL_PATH" fetch origin main --quiet
slug="${REPO##*/}"
worktree="/home/jerry/workspace/tasks/onboarding/${slug}"
branch="chore/governance-onboard-${slug}-$(date -u +%Y%m%d)"
[[ ! -e "$worktree" ]] || { echo "worktree exists: $worktree" >&2; exit 1; }
mkdir -p "$(dirname "$worktree")"
git -C "$LOCAL_PATH" worktree add -b "$branch" "$worktree" origin/main

if [[ "$ENABLE_CI" == 1 ]]; then
  [[ -f "$worktree/.exo/governance.lock.json" ]] || {
    echo "--enable-ci requires an existing merged .exo/governance.lock.json; run bootstrap first" >&2
    git -C "$LOCAL_PATH" worktree remove --force "$worktree"
    git -C "$LOCAL_PATH" branch -D "$branch"
    exit 1
  }
  if [[ ! -f "$worktree/.github/workflows/exo-governance.yml" ]]; then
    exo --repo "$worktree" adapter-generate --target ci
  else
    echo "governance-onboard: Exo CI already present; leaving it unchanged"
  fi
else
  exo --repo "$worktree" init --no-scan
  mkdir -p "$worktree/governance"
  if [[ ! -f "$worktree/governance/PORTFOLIO_AGENT_CONTRACT.md" ]]; then
    cp "$OVERLAY_TEMPLATE" "$worktree/governance/PORTFOLIO_AGENT_CONTRACT.md"
  fi
  declare -A ADAPTERS=(
    [agents]="AGENTS.md"
    [claude]="CLAUDE.md"
    [cursor]=".cursorrules"
    [codex]="codex.md"
  )
  for target in agents claude cursor codex; do
    path="${ADAPTERS[$target]}"
    if [[ ! -e "$worktree/$path" ]]; then
      cp "$OVERLAY_TEMPLATE" "$worktree/$path"
      echo "governance-onboard: seed missing $path with the company overlay"
    fi
    # Exo uses markers and preserves all content outside its managed section.
    # This makes brownfield adoption reviewable without silently replacing the
    # product's own instructions.
    exo --repo "$worktree" adapter-generate --target "$target"
    append_overlay_pointer "$worktree/$path"
  done
fi

echo "governance-onboard: ready for review"
echo "repo=$REPO"
echo "branch=$branch"
echo "worktree=$worktree"
if [[ "$ENABLE_CI" == 1 ]]; then
  echo "next: inspect the CI workflow, then open a Draft PR; require the Exo check after it passes"
else
  echo "next: inspect .exo policy and generated adapters, then open a Draft PR"
  echo "after that PR merges: rerun with --apply --enable-ci, then require ExoProtocol Governance"
fi
