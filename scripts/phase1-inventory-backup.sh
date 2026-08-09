#!/usr/bin/env bash
set -euo pipefail

usage() { echo "usage: $0 <evidence-root> <repo>..." >&2; exit 2; }
[[ $# -ge 2 ]] || usage
evidence_root=$1; shift
run_id=$(date -u +%Y%m%dT%H%M%SZ)
run_dir="$evidence_root/phase1-inventory-backup/$run_id"
mkdir -p "$run_dir"

for repo in "$@"; do
  [[ -d "$repo" ]] || { echo "STOP: repository missing: $repo" >&2; exit 1; }
  top=$(git -C "$repo" rev-parse --show-toplevel)
  id=$(printf '%s' "$top" | sed 's#^/##; s#[^A-Za-z0-9._-]#_#g')
  out="$run_dir/$id"
  mkdir -p "$out"
  {
    echo "path=$top"
    git -C "$repo" remote -v
    git -C "$repo" branch --show-current
    git -C "$repo" rev-parse HEAD
    git -C "$repo" status --short --branch
    git -C "$repo" rev-list --left-right --count '@{upstream}...HEAD' 2>/dev/null || true
    du -sh "$top"
    git -C "$repo" log -1 --format='last_commit=%cI %H %s'
    git -C "$repo" worktree list --porcelain
  } >"$out/inventory.txt"
  git -C "$repo" diff --binary >"$out/working-tree.diff"
  git -C "$repo" diff --cached --binary >"$out/staged.diff"
  git -C "$repo" status --porcelain=v1 -z >"$out/status.porcelain.z"
  git -C "$repo" ls-files --others --exclude-standard -z >"$out/untracked.zlist"
  if [[ -s "$out/untracked.zlist" ]]; then
    tar -C "$top" --null --files-from="$out/untracked.zlist" -czf "$out/untracked.tar.gz"
  else
    : >"$out/untracked.tar.gz"
  fi
  git -C "$repo" bundle create "$out/repository.bundle" --all
  git -C "$repo" bundle verify "$out/repository.bundle" >"$out/bundle.verify.txt"
  sha256sum "$out"/* >"$out/SHA256SUMS"
done

sha256sum "$run_dir"/*/* >"$run_dir/SHA256SUMS"
echo "PASS: phase 1 evidence written to $run_dir"
