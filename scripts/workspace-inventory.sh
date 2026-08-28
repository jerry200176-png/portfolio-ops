#!/usr/bin/env bash
set -euo pipefail

# Read-only discovery of Git roots. This deliberately does not fetch, prune,
# clean, move, remove, or modify any repository.
usage() {
  echo "usage: $0 <output.tsv> <discovery-root>..." >&2
  exit 2
}

[[ $# -ge 2 ]] || usage
output=$1
shift
mkdir -p "$(dirname "$output")"

write_row() {
  local first=1 field
  for field in "$@"; do
    [[ "$first" == 1 ]] || printf '\t'
    printf '%s' "$field" | tr '\t\n' '  '
    first=0
  done
  printf '\n'
}

write_row discovery_root candidate git_top role remote branch head status dirty_count upstream last_commit error >"$output"

classify() {
  case "$1" in
    /home/jerry/workspace/portfolio-ops|*/portfolio-governance-baseline) echo control-plane ;;
    /home/jerry/workspace/AllTrue_System-clean|/home/jerry/workspace/sunrise-cafe|/home/jerry/workspace/engineering-intelligence|/home/jerry/workspace/korea-trip-plan|/home/jerry/workspace/income-statement-app|/home/jerry/workspace/income-statement-app-releases) echo canonical-checkout ;;
    /home/jerry/workspace/governance-clones/*) echo governance-clone ;;
    /home/jerry/workspace/worktrees/*|/home/jerry/wt/*) echo active-worktree ;;
    /home/jerry/workspace/tasks/*/*|*/workspace/tasks/*/*|/home/jerry/wt/tasks/*/*|*/wt/tasks/*/*) echo task-worktree ;;
    /home/jerry/workspace/*) echo workspace-checkout ;;
    /home/jerry/*) echo legacy-checkout ;;
    *) echo unknown ;;
  esac
}

find_markers() {
  local root=$1
  if [[ "$root" == "/home/jerry" ]]; then
    find "$root" -mindepth 2 -maxdepth 2 \
      \( -type d -name .git -print -prune \) -o \( -type f -name .git -print \) 2>/dev/null
    return
  fi
  find "$root" -maxdepth 6 \
    \( -type d \( -name node_modules -o -name vendor-modules -o -name .venv -o -name .cache -o -name _diag \) -prune \) -o \
    \( -type d -name .git -print -prune \) -o \( -type f -name .git -print \) 2>/dev/null
}

declare -A seen

for root in "$@"; do
  [[ -d "$root" ]] || {
    write_row "$root" "$root" "" "unknown" "" "" "" "missing" "" "" "" "discovery root missing" >>"$output"
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
      write_row "$root" "$candidate" "" "unresolved" "" "" "" "unreadable" "" "" "" "git root could not be resolved" >>"$output"
      continue
    fi

    remote=$(git -c safe.directory='*' -C "$candidate" remote get-url origin 2>/dev/null || echo none)
    branch=$(git -c safe.directory='*' -C "$candidate" branch --show-current 2>/dev/null || echo detached)
    head=$(git -c safe.directory='*' -C "$candidate" rev-parse HEAD 2>/dev/null || echo unknown)
    status_output=$(git -c safe.directory='*' -C "$candidate" status --porcelain=v1 2>/dev/null || true)
    dirty_count=$(printf '%s\n' "$status_output" | awk 'NF {n++} END {print n+0}')
    status=clean
    [[ "$dirty_count" == 0 ]] || status=dirty
    upstream=$(git -c safe.directory='*' -C "$candidate" rev-list --left-right --count '@{upstream}...HEAD' 2>/dev/null | tr '\t\n' '  ' || true)
    last_commit=$(git -c safe.directory='*' -C "$candidate" log -1 --format=%cI 2>/dev/null || echo unknown)
    write_row "$root" "$candidate" "$git_top" "$(classify "$candidate")" "$remote" "$branch" "$head" "$status" "$dirty_count" "$upstream" "$last_commit" "$error" >>"$output"
  done < <(find_markers "$root" | sort)
done

sha256sum "$output" >"$output.sha256"
echo "PASS: workspace inventory written to $output"
