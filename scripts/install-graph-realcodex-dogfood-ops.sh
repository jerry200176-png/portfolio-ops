#!/usr/bin/env bash
# Install RealCodex dogfood waiter + watchdog + pre-resume into the host state dir.
# Arms crontab @reboot and one-shot pre-resume re-exec (does not start processes;
# does not interrupt a healthy live dogfood).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STATE_DIR="${GRAPH_DOGFOOD_STATE_DIR:-${HOME}/workspace/state/portfolio-ops}"
UNIT_DIR="${HOME}/.config/systemd/user"
# Codex resume observed 2026-09-19 16:26 Asia/Taipei → tip re-exec at 16:21 local.
PRERESUME_CRON_SPEC="${GRAPH_DOGFOOD_PRERESUME_CRON:-21 16 19 9 *}"
PRERESUME_YEAR="${GRAPH_DOGFOOD_PRERESUME_YEAR:-2026}"

mkdir -p "$STATE_DIR" "$UNIT_DIR"

install -m 0755 "$ROOT/scripts/codex-quota-wait-dogfood.sh" "$STATE_DIR/codex-quota-wait-dogfood.sh"
install -m 0755 "$ROOT/scripts/codex-quota-watchdog.sh" "$STATE_DIR/codex-quota-watchdog.sh"
if [[ -f "$ROOT/scripts/codex-quota-preresume-reexec.sh" ]]; then
  install -m 0755 "$ROOT/scripts/codex-quota-preresume-reexec.sh" \
    "$STATE_DIR/codex-quota-preresume-reexec.sh"
fi

cp "$ROOT/scripts/systemd/graph-realcodex-dogfood-waiter.service" "$UNIT_DIR/"
cp "$ROOT/scripts/systemd/graph-realcodex-dogfood-watchdog.service" "$UNIT_DIR/"

echo "installed waiter+watchdog+preresume → $STATE_DIR"
echo "systemd units → $UNIT_DIR"
if [[ -S "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/bus" ]]; then
  systemctl --user daemon-reload
  systemctl --user enable graph-realcodex-dogfood-watchdog.service
  echo "enabled graph-realcodex-dogfood-watchdog.service"
else
  echo "no user dbus; units written but not enabled (crontab @reboot still recommended)"
fi

if command -v crontab >/dev/null 2>&1; then
  CRON_TMP="$(mktemp)"
  crontab -l 2>/dev/null \
    | grep -v 'portfolio-ops RealCodex dogfood' \
    | grep -v 'codex-quota-watchdog.sh' \
    | grep -v 'codex-quota-preresume-reexec.sh' \
    >"$CRON_TMP" || true

  cat >>"$CRON_TMP" <<EOF
# portfolio-ops RealCodex dogfood — reboot survival
@reboot /bin/bash -lc 'sleep 45; export PATH=${HOME}/.npm-global/bin:${HOME}/.local/bin:/usr/local/bin:/usr/bin:/bin:${HOME}/workspace/agent-control/bin; test -f ${STATE_DIR}/real-codex-dogfood.done || { pgrep -f codex-quota-watchdog.sh >/dev/null || nohup env -i HOME=${HOME} USER=${USER:-jerry} PATH="\$PATH" GRAPH_DOGFOOD_ROOT=${STATE_DIR}/dogfood-runtime WATCHDOG_POLL_SEC=300 ${STATE_DIR}/codex-quota-watchdog.sh >>${STATE_DIR}/codex-quota-watchdog.log 2>&1 & echo \$! >${STATE_DIR}/codex-quota-watchdog.pid; }'
# portfolio-ops RealCodex dogfood — tip re-exec ~5m before Codex resume
${PRERESUME_CRON_SPEC} /bin/bash -lc 'test "\$(date -u +%Y)" = ${PRERESUME_YEAR} || exit 0; export PATH=${HOME}/.npm-global/bin:${HOME}/.local/bin:/usr/bin:/bin; ${STATE_DIR}/codex-quota-preresume-reexec.sh >>${STATE_DIR}/codex-quota-preresume.log 2>&1'
EOF

  crontab "$CRON_TMP"
  rm -f "$CRON_TMP"
  echo "crontab armed (@reboot + preresume ${PRERESUME_CRON_SPEC} year=${PRERESUME_YEAR})"
else
  echo "crontab unavailable; skip host schedule arming"
fi

echo "start watchdog: nohup env GRAPH_DOGFOOD_ROOT=$STATE_DIR/dogfood-runtime $STATE_DIR/codex-quota-watchdog.sh &"
