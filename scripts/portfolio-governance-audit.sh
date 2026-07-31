#!/usr/bin/env bash
set -euo pipefail

usage() { echo "usage: $0 <output.tsv> <repo>..." >&2; exit 2; }
[[ $# -ge 2 ]] || usage
output=$1; shift
mkdir -p "$(dirname "$output")"
printf 'path\tremote\tbranch\tstatus\tahead\tbehind\tsize\tlast_activity\tREADME\tCONTRIBUTING\tSECURITY\tCODE_OF_CONDUCT\tLICENSE\tCODEOWNERS\tISSUE_PR_TEMPLATES\tCI_DEPENDABOT\tgovernance_score_8\n' >"$output"

has_file() {
  local repo=$1 pattern=$2
  compgen -G "$repo/$pattern" >/dev/null 2>&1
}

for repo in "$@"; do
  [[ -d "$repo" ]] || { echo "STOP: repository missing: $repo" >&2; exit 1; }
  top=$(git -C "$repo" rev-parse --show-toplevel)
  remote=$(git -C "$repo" remote get-url origin 2>/dev/null || echo none)
  branch=$(git -C "$repo" branch --show-current)
  status=clean
  [[ -z "$(git -C "$repo" status --porcelain=v1)" ]] || status=dirty
  ahead=0; behind=0
  if git -C "$repo" rev-parse --verify '@{upstream}' >/dev/null 2>&1; then
    read -r behind ahead < <(git -C "$repo" rev-list --left-right --count '@{upstream}...HEAD')
  fi
  size=$(du -sh "$top" | cut -f1)
  last_activity=$(git -C "$repo" log -1 --format=%cI)
  score=0
  readme=no; contributing=no; security=no; conduct=no; license=no; owners=no; templates=no; automation=no
  if has_file "$top" 'README*'; then readme=yes; score=$((score+1)); fi
  if has_file "$top" 'CONTRIBUTING*'; then contributing=yes; score=$((score+1)); fi
  if has_file "$top" 'SECURITY*'; then security=yes; score=$((score+1)); fi
  if has_file "$top" 'CODE_OF_CONDUCT*'; then conduct=yes; score=$((score+1)); fi
  if has_file "$top" 'LICENSE*'; then license=yes; score=$((score+1)); fi
  if has_file "$top" '.github/CODEOWNERS'; then owners=yes; score=$((score+1)); fi
  if has_file "$top" '.github/PULL_REQUEST_TEMPLATE*' || [[ -d "$top/.github/ISSUE_TEMPLATE" ]]; then templates=yes; score=$((score+1)); fi
  if [[ -d "$top/.github/workflows" ]] || [[ -f "$top/.github/dependabot.yml" ]]; then automation=yes; score=$((score+1)); fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$top" "$remote" "$branch" "$status" "$ahead" "$behind" "$size" "$last_activity" \
    "$readme" "$contributing" "$security" "$conduct" "$license" "$owners" "$templates" "$automation" "$score" >>"$output"
done

sha256sum "$output" >"$output.sha256"
echo "PASS: governance audit written to $output"
