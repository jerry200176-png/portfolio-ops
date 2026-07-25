#!/usr/bin/env python3
"""Dependency-free deterministic state transitions for /portfolio-run."""
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_STOPS = {"mission_complete", "founder_only_blocker", "safety_boundary", "tool_unavailable", "budget_or_turn_cap"}
REQUIRED = {"mission_id", "title", "priority", "status", "phase", "goal", "success_criteria", "non_goals", "authority", "hard_boundaries", "completed_steps", "current_step", "next_action", "blockers", "evidence", "verification", "rollback", "stop_reason", "resume_instruction", "created_at", "updated_at"}
def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def load(path): return json.loads(Path(path).read_text())
def save(path, value): Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
def validate(m):
    missing = REQUIRED - m.keys()
    if missing: raise ValueError("missing mission fields: " + ", ".join(sorted(missing)))
    contract = m.get("outcome_contract", {})
    absent = [k for k in ("inputs", "success_criteria", "non_goals", "authority", "verification", "rollback", "stop_conditions") if not contract.get(k)]
    if absent: raise ValueError("incomplete outcome contract: " + ", ".join(absent))
    if m["stop_reason"] is not None and m["stop_reason"] not in ALLOWED_STOPS: raise ValueError("invalid stop_reason")
    for step in m.get("steps", []):
        if step.get("kind") == "investigate" and not step.get("unanswered_question"): raise ValueError("investigation requires a named unanswered_question")
def approval(queue, mission, step):
    key = step.get("bundle_key", step["id"])
    found = next((a for a in queue["approvals"] if a["mission_id"] == mission["mission_id"] and a.get("bundle_key") == key and a["status"] == "pending"), None)
    if found:
        if step["exact_action"] not in found["bundled_actions"]: found["bundled_actions"].append(step["exact_action"])
        return found["approval_id"]
    item = {"approval_id": f"APR-{mission['mission_id']}-{key}".upper(), "mission_id": mission["mission_id"], "bundle_key": key, "exact_action": step["exact_action"], "why_human_only": step["why_human_only"], "risk": step.get("risk", "Founder-only action"), "rollback_ready": step.get("rollback_ready", False), "evidence_ready": step.get("evidence_ready", False), "blocks": step.get("blocks", []), "bundled_actions": [step["exact_action"]], "status": "pending", "requested_at": now(), "resolved_at": None}
    queue["approvals"].append(item); return item["approval_id"]
def done(m, s, result):
    s["status"] = "completed"; m["completed_steps"].append(s["id"]); m["evidence"].append({"step": s["id"], "result": result, "at": now()})
    m.setdefault("phase_history", []).append({"step": s["id"], "phases": ["observe", "plan", "act", "verify", "checkpoint"], "at": now()})
def runnable(m): return next((s for s in m.get("steps", []) if s.get("status", "pending") == "pending" and not s.get("blocked_by")), None)
def run(mission_path, queue_path, policy_path):
    m, q, policy = load(mission_path), load(queue_path), load(policy_path); validate(m)
    # A new invocation resumes a budget checkpoint from durable state.
    if m.get("stop_reason") == "budget_or_turn_cap":
        m.update(status="active", phase="observe", stop_reason=None)
    turns = 0; cap = policy["defaults"]["max_goal_turns"]
    while turns < cap:
        s = runnable(m)
        if not s: break
        turns += 1; m["current_step"] = s["id"]; kind = s.get("kind", "work")
        if kind == "founder_only":
            aid = approval(q, m, s); s["status"] = "approval_pending"; m["blockers"].append({"step": s["id"], "approval_id": aid})
        elif kind == "ci":
            observations, index = s.get("observations", ["pending", "success"]), s.get("observation_index", 0)
            result = observations[min(index, len(observations)-1)]; s["observation_index"] = index + 1; m["evidence"].append({"step": s["id"], "ci": result, "at": now()})
            if result == "success": done(m, s, "CI succeeded")
            elif result != "pending":
                if s.get("retries", 0) < policy["defaults"]["max_retries_per_failure"]: s["retries"] = s.get("retries", 0) + 1
                else: m.update(status="paused", phase="checkpointed", stop_reason="tool_unavailable", resume_instruction=f"Resolve CI failure then resume {m['mission_id']}"); break
        elif kind == "failure":
            if s.get("retries", 0) < policy["defaults"]["max_retries_per_failure"]: s["retries"] = s.get("retries", 0) + 1; m["evidence"].append({"step": s["id"], "repair": "retry scheduled", "at": now()})
            else: m.update(status="paused", phase="checkpointed", stop_reason=s.get("exhausted_stop_reason", "tool_unavailable"), resume_instruction=f"Resolve {s['id']} and resume"); break
        elif kind == "open_pr":
            url = s.get("pr_url", s["id"])
            already_opened = any(e.get("draft_pr") == url for e in m["evidence"] if isinstance(e, dict))
            done(m, s, "Existing Draft PR reused" if already_opened else "Draft PR opened")
            m["evidence"][-1]["draft_pr"] = url
        else: done(m, s, "completed")
        m["next_action"] = next((x["id"] for x in m.get("steps", []) if x.get("status", "pending") == "pending"), "verify exit criteria")
    waiting = [s for s in m.get("steps", []) if s.get("status") == "approval_pending"]
    pending = [s for s in m.get("steps", []) if s.get("status", "pending") == "pending"]
    if not pending and not waiting and m.get("stop_reason") is None: m.update(status="completed", phase="complete", stop_reason="mission_complete", resume_instruction="No action required")
    elif turns >= cap and m.get("stop_reason") is None: m.update(status="paused", phase="checkpointed", stop_reason="budget_or_turn_cap", resume_instruction=f"Run /portfolio-run resume {m['mission_id']}")
    elif not pending and waiting and m.get("stop_reason") is None: m.update(status="paused", phase="checkpointed", stop_reason="founder_only_blocker", resume_instruction=f"Resolve queued approvals then /portfolio-run resume {m['mission_id']}")
    if m.get("stop_reason") not in ALLOWED_STOPS and m.get("stop_reason") is not None: raise ValueError("invalid emitted stop_reason")
    m["updated_at"] = now(); q["updated_at"] = now(); save(mission_path, m); save(queue_path, q); return m
def active(directory):
    choices = []
    for path in sorted(Path(directory).glob("*.yaml")):
        mission = load(path)
        if not mission.get("example") and not mission.get("mission_id", "").startswith("example-") and mission.get("status") in {"active", "paused"}: choices.append(mission)
    if len(choices) != 1: raise ValueError(f"expected exactly one active mission, found {len(choices)}")
    return choices[0]
def require_writer(args):
    if args.writer != "claude_code": raise ValueError("active mission state may only be written with --writer claude_code")
if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("command", choices=["create","validate","active","next","approvals","checkpoint","run","resume","close"]); p.add_argument("--mission"); p.add_argument("--missions-dir", default="state/missions"); p.add_argument("--queue", default="state/founder-approval-queue.yaml"); p.add_argument("--policy", default="state/mission-loop-policy.yaml"); p.add_argument("--writer"); p.add_argument("--mission-id"); p.add_argument("--title"); p.add_argument("--goal"); p.add_argument("--priority", default="p2"); p.add_argument("--reason", default="budget_or_turn_cap"); a = p.parse_args()
    if a.command == "active": print(json.dumps(active(a.missions_dir))); raise SystemExit
    if a.command == "approvals": print(json.dumps(load(a.queue).get("approvals", []))); raise SystemExit
    if a.command == "create":
        require_writer(a); path=Path(a.missions_dir)/f"{a.mission_id}.yaml"; path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists(): raise ValueError("mission already exists")
        t=now(); m={"mission_id":a.mission_id,"title":a.title,"priority":a.priority,"status":"active","phase":"observe","goal":a.goal,"success_criteria":["Define exit criterion"],"non_goals":["Define non-goals"],"authority":["Portfolio control-plane only"],"hard_boundaries":["Existing CLAUDE.md applies"],"completed_steps":[],"current_step":None,"next_action":"define first bounded step","blockers":[],"evidence":[],"verification":{"reviewer_findings":[]},"rollback":"Revert this mission state only.","stop_reason":None,"resume_instruction":"Run /portfolio-run resume.","created_at":t,"updated_at":t,"outcome_contract":{"inputs":["Define inputs"],"success_criteria":["Define exit criterion"],"non_goals":["Define non-goals"],"authority":["Portfolio control-plane only"],"verification":["Define verification"],"rollback":["Revert state"],"stop_conditions":["mission_complete","budget_or_turn_cap"]},"steps":[]}; save(path,m); print(path); raise SystemExit
    if not a.mission: a.mission=str(Path(a.missions_dir)/f"{active(a.missions_dir)['mission_id']}.yaml")
    m=load(a.mission)
    if a.command == "validate": validate(m); print("valid"); raise SystemExit
    if a.command == "next": print(m["next_action"]); raise SystemExit
    require_writer(a)
    if a.command in {"run","resume"}: r=run(a.mission,a.queue,a.policy)
    elif a.command == "checkpoint":
        if a.reason not in ALLOWED_STOPS: raise ValueError("invalid checkpoint reason")
        m.update(status="paused",phase="checkpointed",stop_reason=a.reason,resume_instruction="Run /portfolio-run resume."); m["updated_at"]=now(); save(a.mission,m); r=m
    else:
        if not m.get("verification",{}).get("exit_criteria_passed"): raise ValueError("exit criteria not passed")
        m.update(status="completed",phase="complete",stop_reason="mission_complete"); save(a.mission,m); r=m
    print(json.dumps({"mission_id":r["mission_id"],"status":r["status"],"stop_reason":r["stop_reason"],"next_action":r["next_action"]}))
