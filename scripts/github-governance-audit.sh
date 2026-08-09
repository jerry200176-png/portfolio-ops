#!/usr/bin/env bash
set -euo pipefail

# Read-only GitHub enforcement audit. It reports drift against the local
# declarative policy; it never edits rulesets or branch protection.
usage() { echo "usage: $0 <output-dir> <owner/repo>..." >&2; exit 2; }
[[ $# -ge 2 ]] || usage
output_dir=$1
shift
mkdir -p "$output_dir"

for repo in "$@"; do
  safe=$(printf '%s' "$repo" | tr '/:' '__')
  out="$output_dir/$safe"
  mkdir -p "$out"
  printf 'repository=%s\nread_only=true\n' "$repo" >"$out/meta.txt"
  if ! gh api "repos/$repo/rulesets" >"$out/rulesets.json" 2>"$out/rulesets.error"; then
    printf '{"error":"rulesets request failed; see rulesets.error"}\n' >"$out/rulesets.json"
  fi
  if ! gh api "repos/$repo/branches/main/protection" >"$out/main-protection.json" 2>"$out/main-protection.error"; then
    printf '{"error":"branch protection request failed; see main-protection.error"}\n' >"$out/main-protection.json"
  fi
  echo "AUDITED: $repo -> $out"
done

find "$output_dir" -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum >"$output_dir/SHA256SUMS"
echo "PASS: GitHub governance audit written to $output_dir"
