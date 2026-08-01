#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -P "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${COMPANY_WORKSPACE_ROOT:-/home/jerry/workspace}"
[[ "${1:-}" == "--apply" ]] || { echo "Usage: $0 --apply" >&2; exit 2; }
mkdir -p "$TARGET"
for name in AGENTS.md CLAUDE.md .cursorrules; do
  source="$ROOT/docs/workspace-entrypoints/$name"
  target="$TARGET/$name"
  if [[ -e "$target" ]]; then
    if cmp -s "$source" "$target"; then
      echo "workspace-entrypoint: unchanged $target"
      continue
    fi
    backup="$target.backup.$(date -u +%Y%m%dT%H%M%SZ)"
    cp -p "$target" "$backup"
    echo "workspace-entrypoint: backed up $target -> $backup"
  fi
  cp "$source" "$target"
  echo "workspace-entrypoint: installed $target"
done
