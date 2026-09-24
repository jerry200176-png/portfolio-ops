#!/usr/bin/env bash
# Shared helpers for agent-control (Phase 0.5)
set -euo pipefail

AGENT_CONTROL_ROOT="${AGENT_CONTROL_ROOT:-/home/jerry/workspace/agent-control}"
REPOS_ROOT="${REPOS_ROOT:-/home/jerry/workspace/repos}"
TASKS_ROOT="${TASKS_ROOT:-/home/jerry/workspace/tasks}"
SESSIONS_DIR="${AGENT_CONTROL_ROOT}/sessions"
LOGS_DIR="${AGENT_CONTROL_ROOT}/logs"
GATEWAY_VERSION="0.5.0"

declare -A PROJECT_BARE=(
  [portfolio-ops]="${REPOS_ROOT}/portfolio-ops.git"
  [alltrue]="${REPOS_ROOT}/AllTrue_System.git"
  [sunrise]="${REPOS_ROOT}/sunrise-cafe.git"
)
declare -A PROJECT_REMOTE=(
  [portfolio-ops]="https://github.com/jerry200176-png/portfolio-ops.git"
  [alltrue]="https://github.com/jerry200176-png/AllTrue_System.git"
  [sunrise]="https://github.com/jerry200176-png/sunrise-cafe.git"
)
declare -A PROJECT_TASK_ROOT=(
  [portfolio-ops]="${TASKS_ROOT}/portfolio-ops"
  [alltrue]="${TASKS_ROOT}/alltrue"
  [sunrise]="${TASKS_ROOT}/sunrise"
)
declare -A PROJECT_GH=(
  [portfolio-ops]="jerry200176-png/portfolio-ops"
  [alltrue]="jerry200176-png/AllTrue_System"
  [sunrise]="jerry200176-png/sunrise-cafe"
)

FORBIDDEN_SUBSTRINGS=(
  "/home/jerry/alltrue"
  "/actions-runner-alltrue/"
  "/workspace-backups/"
  "/mnt/c/"
  "/AllTrue_System-clean"
  "/workspace/AllTrue_System"
  "/workspace/sunrise-cafe"
)

# Note: exact /home/jerry/alltrue is forbidden; /home/jerry/alltrue-* historically allowed
# but Phase 0.5 official path is only TASKS_ROOT.

fail() { echo "agent-control: FAIL: $*" >&2; exit 1; }
ok() { echo "agent-control: OK: $*"; }

resolve() {
  local p="$1"
  realpath -m "$p" 2>/dev/null || readlink -f "$p" 2>/dev/null || echo "$p"
}
assert_project() {
  local p="$1"
  [[ -n "${PROJECT_BARE[$p]:-}" ]] || fail "unknown project '$p' (portfolio-ops|alltrue|sunrise)"
}

assert_task_id() {
  local t="$1"
  [[ "$t" =~ ^[0-9A-Za-z][0-9A-Za-z._-]{0,63}$ ]] || fail "invalid task_id '$t'"
}

assert_not_forbidden_path() {
  local path
  path="$(resolve "$1")"
  # Exact forbidden legacy checkout
  if [[ "$path" == "/home/jerry/alltrue" ]]; then
    fail "forbidden checkout: $path"
  fi
  local s
  for s in "${FORBIDDEN_SUBSTRINGS[@]}"; do
    # special-case: substring /home/jerry/alltrue would also match alltrue-foo;
    # only exact match handled above for that path.
    if [[ "$s" == "/home/jerry/alltrue" ]]; then
      continue
    fi
    if [[ "$path" == *"$s"* ]]; then
      fail "forbidden path class matched '$s' in $path"
    fi
  done
  # Bare repos themselves are not worktrees for code
  if [[ "$path" == *.git ]] || [[ "$path" == */repos/*.git ]]; then
    fail "cannot use bare repository as worktree: $path"
  fi
}

assert_task_path() {
  local project="$1" path="$2"
  local root expected
  root="$(resolve "${PROJECT_TASK_ROOT[$project]}")"
  path="$(resolve "$path")"
  case "$path" in
    "$root"/*) ;;
    *) fail "worktree not under task root $root: $path" ;;
  esac
}

new_session_id() {
  python3 - <<'PY'
import uuid
print(uuid.uuid4().hex)
PY
}

write_json() {
  local out="$1"
  python3 - "$out" <<'PY'
import json,sys
out=sys.argv[1]
obj=json.load(sys.stdin)
with open(out,'w') as f:
    json.dump(obj,f,indent=2,ensure_ascii=False)
    f.write('\n')
PY
}

append_launch_log() {
  local manifest_path="$1"
  mkdir -p "$LOGS_DIR"
  python3 - "$manifest_path" "$LOGS_DIR/launches.jsonl" <<'PY'
import json,sys,datetime
m=json.load(open(sys.argv[1]))
row={
  "logged_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "session_id": m.get("session_id"),
  "project": m.get("project"),
  "task_id": m.get("task_id"),
  "base_sha": m.get("base_sha"),
  "branch": m.get("branch"),
  "worktree_path": m.get("worktree_path"),
  "preflight_result": m.get("preflight_result"),
  "agent_cli": m.get("agent_cli"),
}
with open(sys.argv[2],'a') as f:
    f.write(json.dumps(row,ensure_ascii=False)+'\n')
PY
}

validate_manifest_file() {
  local path="$1"
  python3 - "$path" "${AGENT_CONTROL_ROOT}/schema/session-manifest.schema.json" <<'PY'
import json,sys,re
manifest=json.load(open(sys.argv[1]))
# Lightweight schema check (no external jsonschema dependency required)
required=[
 "schema_version","session_id","project","task_id","repo_remote","base_sha",
 "branch","worktree_path","started_at","production_mutation","preflight_result",
 "provenance_type"
]
for k in required:
    if k not in manifest:
        raise SystemExit(f'missing {k}')
if manifest["schema_version"]!="1.0":
    raise SystemExit('bad schema_version')
if manifest["project"] not in ("portfolio-ops", "alltrue", "sunrise"):
    raise SystemExit('bad project')
if not re.match(r'^[0-9a-f]{40}$', manifest["base_sha"]):
    raise SystemExit('bad base_sha')
if manifest["production_mutation"] is not False:
    raise SystemExit('production_mutation must be false')
if manifest["preflight_result"]!="pass":
    raise SystemExit('preflight_result must be pass')
if manifest["provenance_type"] not in ("agent-session","human-authored"):
    raise SystemExit('bad provenance_type')
state=manifest.get("lifecycle_state")
if state is not None and state not in ("active","idle","terminal"):
    raise SystemExit('bad lifecycle_state')
if state in ("idle","terminal") and not manifest.get("lifecycle_updated_at"):
    raise SystemExit('idle/terminal manifest needs lifecycle_updated_at')
if state == "active" and manifest.get("lifecycle_updated_at"):
    raise SystemExit('active manifest cannot have lifecycle_updated_at')
quarantine=manifest.get("quarantine")
if quarantine is not None:
    required_q=("owner","task","reason","entered_at","state")
    if not isinstance(quarantine,dict) or any(not quarantine.get(k) for k in required_q):
        raise SystemExit('incomplete quarantine metadata')
    if quarantine["state"] not in ("active","terminal"):
        raise SystemExit('bad quarantine state')
# Reject secret-looking keys/values
secret_re=re.compile(r'(api[_-]?key|token|password|secret|private[_-]?key)', re.I)
blob=json.dumps(manifest)
if secret_re.search(blob):
    # allow the word production_mutation only
    for k,v in manifest.items():
        if secret_re.search(k) and k!="production_mutation":
            raise SystemExit(f'sensitive key {k}')
        if isinstance(v,str) and secret_re.search(v) and 'mutation' not in v.lower():
            raise SystemExit(f'sensitive value in {k}')
print('manifest-ok')
PY
}
