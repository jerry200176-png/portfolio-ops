#!/usr/bin/env bash
set -euo pipefail
for a in "$@"; do [[ "$a" == --dry-run ]] && echo '{"profile":"terra","model":"stub","reasoning_effort_override":null,"reason":"t","resolution":"selected","requested_tier":"terra","selected_tier":"terra"}' && exit 0; done
sleep 60 &
sleep 60
