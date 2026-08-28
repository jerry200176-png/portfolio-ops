#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
usage: install-governance-autopilot-timer.sh [--enable-now]

Install the user-level unit templates without enabling them by default.
--enable-now is an explicit one-time activation request.
EOF
  exit 2
}

enable_now=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --enable-now) enable_now=1; shift ;;
    -h|--help) usage ;;
    *) echo "unknown argument: $1" >&2; usage ;;
  esac
done

script_root=$(cd -P "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
unit_source="$script_root/automation/systemd"
user_home=$(getent passwd "$(id -un)" | cut -d: -f6)
config_root=${XDG_CONFIG_HOME:-"$user_home/.config"}
unit_dir="$config_root/systemd/user"
service_name=portfolio-ops-governance-autopilot.service
timer_name=portfolio-ops-governance-autopilot.timer

[[ -f "$unit_source/$service_name" && -f "$unit_source/$timer_name" ]] || {
  echo "unit templates missing under $unit_source" >&2
  exit 1
}
mkdir -p "$unit_dir"

for unit in "$service_name" "$timer_name"; do
  destination="$unit_dir/$unit"
  if [[ -e "$destination" ]] && ! cmp -s "$unit_source/$unit" "$destination"; then
    echo "refusing to overwrite a different existing unit: $destination" >&2
    exit 1
  fi
  if [[ ! -e "$destination" ]]; then
    install -m 0644 "$unit_source/$unit" "$destination"
  fi
done

systemctl --user daemon-reload
if [[ "$enable_now" == 1 ]]; then
  systemctl --user enable --now "$timer_name"
  echo "enabled: $timer_name"
else
  echo "installed but not enabled: $timer_name (rerun with --enable-now after review)"
fi
