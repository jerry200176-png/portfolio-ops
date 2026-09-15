#!/usr/bin/env bash
# Install RealCodex dogfood waiter + watchdog into the host state dir.
# Does not start processes and does not interrupt a healthy live dogfood.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STATE_DIR="${GRAPH_DOGFOOD_STATE_DIR:-${HOME}/workspace/state/portfolio-ops}"
UNIT_DIR="${HOME}/.config/systemd/user"

mkdir -p "$STATE_DIR" "$UNIT_DIR"

install -m 0755 "$ROOT/scripts/codex-quota-wait-dogfood.sh" "$STATE_DIR/codex-quota-wait-dogfood.sh"
install -m 0755 "$ROOT/scripts/codex-quota-watchdog.sh" "$STATE_DIR/codex-quota-watchdog.sh"

# Optional systemd user units (enabled only if user bus is available).
cp "$ROOT/scripts/systemd/graph-realcodex-dogfood-waiter.service" "$UNIT_DIR/"
cp "$ROOT/scripts/systemd/graph-realcodex-dogfood-watchdog.service" "$UNIT_DIR/"

echo "installed waiter+watchdog → $STATE_DIR"
echo "systemd units → $UNIT_DIR"
if [[ -S "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/bus" ]]; then
  systemctl --user daemon-reload
  systemctl --user enable graph-realcodex-dogfood-watchdog.service
  echo "enabled graph-realcodex-dogfood-watchdog.service"
else
  echo "no user dbus; units written but not enabled (crontab @reboot still recommended)"
fi
echo "start watchdog: nohup env GRAPH_DOGFOOD_ROOT=$STATE_DIR/dogfood-runtime $STATE_DIR/codex-quota-watchdog.sh &"
