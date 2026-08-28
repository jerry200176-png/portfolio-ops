#!/usr/bin/env bash
set -euo pipefail

usage() { echo "usage: $0 <evidence-root> <verified-phase1-dir> <repo>..." >&2; exit 2; }
[[ $# -ge 3 ]] || usage
evidence_root=$1; phase1_dir=$2; shift 2
[[ -d "$phase1_dir" ]] || { echo "STOP: phase 1 evidence directory is missing: $phase1_dir" >&2; exit 1; }
[[ -f "$phase1_dir/SHA256SUMS" ]] || { echo "STOP: phase 1 checksum manifest is missing: $phase1_dir/SHA256SUMS" >&2; exit 1; }
run_id=$(date -u +%Y%m%dT%H%M%SZ)
run_dir="$evidence_root/phase2-fetch-only/$run_id"
mkdir -p "$run_dir"
sha256sum -c "$phase1_dir/SHA256SUMS" >"$run_dir/phase1-checksum.log"

snapshot() {
  local repo=$1 out=$2
  git -C "$repo" rev-parse HEAD >"$out/HEAD"
  git -C "$repo" status --porcelain=v1 -z >"$out/status.porcelain.z"
  git -C "$repo" diff --binary >"$out/working-tree.diff"
  git -C "$repo" diff --cached --binary >"$out/staged.diff"
  git -C "$repo" ls-files --others --exclude-standard -z >"$out/untracked.zlist"
  git -C "$repo" worktree list --porcelain >"$out/worktrees.txt"
  git -C "$repo" for-each-ref --format='%(refname) %(objectname)' refs/heads refs/remotes/origin >"$out/refs.txt"
}

for repo in "$@"; do
  [[ -d "$repo" ]] || { echo "STOP: repository missing: $repo" >&2; exit 1; }
  top=$(git -C "$repo" rev-parse --show-toplevel)
  id=$(printf '%s' "$top" | sed 's#^/##; s#[^A-Za-z0-9._-]#_#g')
  out="$run_dir/$id"
  mkdir -p "$out/pre" "$out/post"
  snapshot "$repo" "$out/pre"
  git -C "$repo" fetch --no-tags origin >"$out/fetch.log" 2>&1
  snapshot "$repo" "$out/post"
  diff -u "$out/pre/HEAD" "$out/post/HEAD" >"$out/HEAD.diff" || true
  diff -u "$out/pre/status.porcelain.z" "$out/post/status.porcelain.z" >"$out/status.diff" || true
  diff -u "$out/pre/working-tree.diff" "$out/post/working-tree.diff" >"$out/working-tree.diff.diff" || true
  diff -u "$out/pre/staged.diff" "$out/post/staged.diff" >"$out/staged.diff.diff" || true
  diff -u "$out/pre/untracked.zlist" "$out/post/untracked.zlist" >"$out/untracked.diff" || true
  diff -u "$out/pre/worktrees.txt" "$out/post/worktrees.txt" >"$out/worktrees.diff" || true
  diff -u "$out/pre/refs.txt" "$out/post/refs.txt" >"$out/refs.diff" || true
  sha256sum "$out"/fetch.log "$out"/pre/* "$out"/post/* >"$out/SHA256SUMS"
done

sha256sum "$run_dir"/*/SHA256SUMS >"$run_dir/SHA256SUMS"
echo "PASS: fetch-only evidence written to $run_dir"
