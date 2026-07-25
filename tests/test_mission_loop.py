import importlib.util, json, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("loop", ROOT / ".claude/skills/portfolio-run/scripts/mission_loop.py")
loop = importlib.util.module_from_spec(spec); spec.loader.exec_module(loop)
def fixture(name): return json.loads((ROOT / "state/missions" / name).read_text())
class MissionLoopTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.p=Path(self.tmp.name); self.m=self.p/"mission.yaml"; self.q=self.p/"queue.yaml"; self.policy=self.p/"policy.yaml"
  self.q.write_text('{"schema_version":1,"updated_at":"","approvals":[]}'); self.policy.write_text((ROOT/"state/mission-loop-policy.yaml").read_text())
 def tearDown(self): self.tmp.cleanup()
 def execute(self,m): self.m.write_text(json.dumps(m)); return loop.run(self.m,self.q,self.policy)
 def test_pr_open_is_not_a_stop_reason(self):
  r=self.execute(fixture("example-ci-monitor.yaml")); self.assertEqual(r["stop_reason"],"mission_complete"); self.assertEqual(r["completed_steps"],["open-draft-pr","monitor-ci"])
 def test_existing_draft_pr_is_reused(self):
  m=fixture("example-ci-monitor.yaml"); m["evidence"]=[{"draft_pr":"synthetic://draft/1"}]; r=self.execute(m); self.assertEqual(r["evidence"][1]["result"],"Existing Draft PR reused")
 def test_pending_ci_is_monitored_not_terminal(self):
  r=self.execute(fixture("example-ci-monitor.yaml")); self.assertEqual([x.get("ci") for x in r["evidence"] if "ci" in x],["pending","success"])
 def test_founder_action_enters_approval_queue(self):
  self.execute(fixture("example-founder-bundle.yaml")); self.assertEqual(len(json.loads(self.q.read_text())["approvals"]),1)
 def test_unblocked_work_continues_with_pending_approval(self):
  r=self.execute(fixture("example-founder-bundle.yaml")); self.assertEqual(r["stop_reason"],"founder_only_blocker"); self.assertIn("prepare-docs",r["completed_steps"]); self.assertIn("prepare-verification",r["completed_steps"])
 def test_related_approvals_are_bundled(self):
  self.execute(fixture("example-founder-bundle.yaml")); self.assertEqual(len(json.loads(self.q.read_text())["approvals"][0]["bundled_actions"]),2)
 def test_retry_occurs_no_more_than_once(self):
  m=fixture("example-ci-monitor.yaml"); m["steps"]=[{"id":"broken","kind":"failure"}]; r=self.execute(m); self.assertEqual(r["stop_reason"],"tool_unavailable"); self.assertEqual(r["steps"][0]["retries"],1)
 def test_turn_cap_writes_resumable_checkpoint(self):
  m=fixture("example-ci-monitor.yaml"); m["steps"]=[{"id":f"work-{n}","kind":"work"} for n in range(13)]; r=self.execute(m); self.assertEqual(r["stop_reason"],"budget_or_turn_cap"); self.assertIn("resume",r["resume_instruction"]); self.assertEqual(len(r["completed_steps"]),12)
 def test_fresh_session_resumes_durable_state(self):
  m=fixture("example-ci-monitor.yaml"); m["steps"]=[{"id":f"work-{n}","kind":"work"} for n in range(13)]; self.execute(m); r=loop.run(self.m,self.q,self.policy); self.assertEqual(r["stop_reason"],"mission_complete"); self.assertEqual(len(r["completed_steps"]),13)
 def test_only_allowed_stop_reasons_validate(self):
  m=fixture("example-ci-monitor.yaml"); m["stop_reason"]="CI pending"
  with self.assertRaises(ValueError): loop.validate(m)
  for reason in loop.ALLOWED_STOPS: m["stop_reason"]=reason; loop.validate(m)
 def test_existing_safety_hooks_and_agent_restrictions_remain_intact(self):
  settings=json.loads((ROOT/".claude/settings.json").read_text()); self.assertIn("Bash(git reset --hard*)",settings["permissions"]["deny"]); self.assertIn("guard_bash.py",(ROOT/".claude/settings.json").read_text()); rules=(ROOT/".claude/rules/agent-definitions.md").read_text(); self.assertIn("`repo-maintainer` has Write/Edit",rules); self.assertIn("every other agent returns text",rules)
if __name__ == "__main__": unittest.main()
