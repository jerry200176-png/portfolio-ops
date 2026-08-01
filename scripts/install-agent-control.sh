#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -P "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${AGENT_CONTROL_ROOT:-/home/jerry/workspace/agent-control}"
[[ "${1:-}" == "--apply" ]] || {
  echo "Usage: $0 --apply" >&2
  echo "Without --apply this script makes no changes." >&2
  exit 2
}

while IFS= read -r source; do
  relative="${source#"$ROOT/"}"
  target="$TARGET/${relative#agent-control/}"
  mkdir -p "$(dirname "$target")"
  if [[ -e "$target" ]] && cmp -s "$source" "$target"; then
    echo "agent-control: unchanged $target"
    continue
  fi
  if [[ -e "$target" ]]; then
    backup="$target.backup.$(date -u +%Y%m%dT%H%M%SZ)"
    cp -p "$target" "$backup"
    echo "agent-control: backed up $target -> $backup"
  fi
  cp "$source" "$target"
  case "$target" in
    */bin/*|*/bootstrap/*.sh|*/scripts/*.sh) chmod +x "$target" ;;
  esac
  echo "agent-control: installed $target"
done < <(find "$ROOT/agent-control" -type f -print | sort)
