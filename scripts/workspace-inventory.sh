#!/usr/bin/env bash
set -euo pipefail

# Read-only discovery of immediate Git roots. This deliberately does not fetch,
# prune, clean, move, remove, or modify any repository.
usage() {
  echo "usage: $0 <output.tsv> <discovery-root>..." >&2
  exit 2
}

[[ $# -ge 2 ]] || usage
output=$1
shift
mkdir -p "$(dirname "$output")"

printf 'discovery_root\tcandidate\tgit_top\trole\tremote\tbranch\thead\tstatus\tupstream\tlast_commit\terror\n' >"$output"

classify() {
  case "$1" in
    /home/jerry/workspace/portfolio-ops|*/portfolio-governance-baseline) echo control-plane ;;
    /home/jerry/workspace/AllTrue_System-clean|/home/jerry/workspace/sunrise-cafe) echo canonical-checkout ;;
    /home/jerry/workspace/worktrees/*|/home/jerry/wt/*) echo active-worktree ;;
    /home/jerry/workspace/*) echo workspace-checkout ;;
    /home/jerry/*) echo legacy-checkout ;;
    *) echo unknown ;;
  esac
}

declare -A seen

for root in "$@"; do
  [[ -d "$root" ]] || {
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$root" "$root" "" "unknown" "" "" "" "missing" "" "" "discovery root missing" >>"$output"
    continue
  }

  while IFS= read -r marker; do
    candidate="$marker"
    [[ "$(basename "$marker")" == ".git" ]] && candidate="$(dirname "$marker")"
    candidate="$(readlink -f "$candidate" 2>/dev/null || printf '%s' "$candidate")"
    [[ -n "${seen[$candidate]:-}" ]] && continue
    seen[$candidate]=1

    error=""
    if ! git_top=$(git -c safe.directory='*' -C "$candidate" rev-parse --show-toplevel 2>/dev/null); then
      printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$root" "$candidate" "" "unresolved" "" "" "" "unreadable" "" "" "git root could not be resolved" >>"$output"
      continue
    fi

    remote=$(git -c safe.directory='*' -C "$candidate" remote get-url origin 2>/dev/null || echo none)
    branch=$(git -c safe.directory='*' -C "$candidate" branch --show-current 2>/dev/null || echo detached)
    head=$(git -c safe.directory='*' -C "$candidate" rev-parse HEAD 2>/dev/null || echo unknown)
    status=clean
    [[ -z "$(git -c safe.directory='*' -C "$candidate" status --porcelain=v1 2>/dev/null)" ]] || status=dirty
    upstream=$(git -c safe.directory='*' -C "$candidate" rev-list --left-right --count '@{upstream}...HEAD' 2>/dev/null | tr '\n' ' ' || true)
    last_commit=$(git -c safe.directory='*' -C "$candidate" log -1 --format=%cI 2>/dev/null || echo unknown)
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$root" "$candidate" "$git_top" "$(classify "$candidate")" "$remote" "$branch" "$head" "$status" "$upstream" "$last_commit" "$error" >>"$output"
  done < <(find "$root" -maxdepth 2 \( -type d -name .git -o -type f -name .git \) -print 2>/dev/null | sort)
done

sha256sum "$output" >"$output.sha256"
echo "PASS: workspace inventory written to $output"
