#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -P "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${AGENT_CONTROL_ROOT:-/home/jerry/workspace/agent-control}"
[[ "${1:-}" == "--apply" ]] || {
  echo "Usage: $0 --apply" >&2
  echo "Without --apply this script makes no changes." >&2
  exit 2
}

git -C "$ROOT" rev-parse --verify HEAD >/dev/null 2>&1 || {
  echo "agent-control: source must be inside a Git checkout" >&2
  exit 1
}
if [[ -n "$(git -C "$ROOT" status --porcelain -- agent-control)" ]]; then
  echo "agent-control: refusing install from modified agent-control source; commit it first for exact provenance" >&2
  exit 1
fi
SOURCE_SHA="$(git -C "$ROOT" rev-parse HEAD)"
RUNTIME_VERSION="$(<"$ROOT/agent-control/VERSION")"

while IFS= read -r -d '' source; do
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
done < <(git -C "$ROOT" ls-files -z -- agent-control | sort -z)

PROVENANCE="$TARGET/.runtime-provenance.json"
if [[ -L "$PROVENANCE" || -d "$PROVENANCE" ]]; then
  echo "agent-control: refusing non-regular provenance target: $PROVENANCE" >&2
  exit 1
fi
if [[ -e "$PROVENANCE" ]]; then
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  cp -p "$PROVENANCE" "$PROVENANCE.backup.$stamp"
  echo "agent-control: backed up $PROVENANCE -> $PROVENANCE.backup.$stamp"
fi
python3 - "$PROVENANCE" "$RUNTIME_VERSION" "$SOURCE_SHA" <<'PY'
import datetime
import json
import os
from pathlib import Path
import sys
import tempfile

path = Path(sys.argv[1])
data = {
    "runtime_version": sys.argv[2],
    "source_commit_sha": sys.argv[3],
    "installed_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
}
with tempfile.NamedTemporaryFile("w", dir=path.parent, encoding="utf-8", delete=False) as stream:
    json.dump(data, stream, indent=2)
    stream.write("\n")
    temp = Path(stream.name)
os.replace(temp, path)
print(f"agent-control: wrote runtime provenance version={data['runtime_version']} sha={data['source_commit_sha']}")
PY
