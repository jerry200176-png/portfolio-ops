#!/usr/bin/env bash
set -euo pipefail

usage() { echo "usage: $0 <evidence-root> <repo>..." >&2; exit 2; }
[[ $# -ge 2 ]] || usage
evidence_root=$1; shift
run_id=$(date -u +%Y%m%dT%H%M%SZ)
run_dir="$evidence_root/phase3-cleanup-proposal/$run_id"
mkdir -p "$run_dir"
proposal="$run_dir/cleanup-proposal.tsv"
printf 'path\tclass\treason\trisk\tapproval_required\n' >"$proposal"
prunable="$run_dir/prunable-worktrees.tsv"
printf 'repo\tpath\thead\tbranch\tmarker\n' >"$prunable"

for repo in "$@"; do
  [[ -d "$repo" ]] || { echo "STOP: repository missing: $repo" >&2; exit 1; }
  top=$(git -C "$repo" rev-parse --show-toplevel)
  status=$(git -C "$repo" status --porcelain=v1 | tr '\n' ' ')
  worktrees="$run_dir/$(printf '%s' "$top" | sed 's#^/##; s#[^A-Za-z0-9._-]#_#g').worktrees.txt"
  git -C "$repo" worktree list --porcelain >"$worktrees"
  if [[ "$top" == "/home/jerry/alltrue" ]]; then
    class=archive-candidate
    reason='legacy checkout; preserve because it is divergent and may be referenced by existing worktrees'
    risk='high: dirty state and severe branch divergence; external references unknown'
    approval=yes
  elif [[ -n "$status" ]]; then
    class=keep
    reason='dirty or untracked state requires preservation before any lifecycle decision'
    risk='high if changed in place'
    approval=no
  else
    class=keep
    reason='canonical/control-plane or active checkout; retain as an integration point'
    risk='low while untouched'
    approval=no
  fi
  printf '%s\t%s\t%s\t%s\t%s\n' "$top" "$class" "$reason" "$risk" "$approval" >>"$proposal"
  awk -v repo="$top" '
    /^worktree / { path=$2 }
    /^HEAD / { head=$2 }
    /^branch / { branch=$2 }
    /^prunable/ { print repo "\t" path "\t" head "\t" branch "\t" $0 }
  ' "$worktrees" >>"$prunable"
done

cat >"$run_dir/README.txt" <<'EOF'
Proposal only. No path was moved, removed, pruned, reset, cleaned, merged,
rebased, or renamed. `prunable` entries are unresolved references, not delete
permission. Before any lifecycle action, verify path existence, branch/HEAD,
process references, backup checksums, and rollback destination; then obtain
explicit Founder approval.
EOF
sha256sum "$run_dir"/* >"$run_dir/SHA256SUMS"
echo "PASS: proposal written to $run_dir"
