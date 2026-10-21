from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check-rulebook.py"


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), *args],
                          capture_output=True, text=True, check=False)


class RulebookTests(unittest.TestCase):
    def setUp(self):
        self.rulebook = (ROOT / "governance/RULEBOOK.md").read_text(encoding="utf-8")
        self.rules = yaml.safe_load((ROOT / "governance/rules.yaml").read_text(encoding="utf-8"))

    def test_rules_yaml_ids_and_version_match_rulebook(self):
        self.assertIn(f"Version: {self.rules['version']} ", self.rulebook)
        rows = (self.rules["trust"] + self.rules["delivery_chain"]
                + self.rules["founder_only"] + self.rules["machine_bans"])
        ids = {row["id"] for row in rows}
        self.assertEqual(len(ids), len(rows), "duplicate rule IDs")
        for rule_id in ids:
            self.assertRegex(self.rulebook, rf"\b{rule_id}\b", rule_id)
        in_text = set(re.findall(r"\*\*([TFB]\d)\*\*|\| ([DB]\d) ", self.rulebook))
        in_text = {a or b for a, b in in_text}
        self.assertEqual(in_text - ids, set(), "rulebook IDs missing from rules.yaml")
        for ban in self.rules["machine_bans"]:
            self.assertTrue(ban["enforced_by"], ban["id"])

    def test_lock_pins_current_rulebook(self):
        lock = (ROOT / "governance/RULEBOOK.lock").read_text(encoding="utf-8")
        digest = hashlib.sha256((ROOT / "governance/RULEBOOK.md").read_bytes()).hexdigest()
        self.assertIn(f"sha256={digest}", lock)
        self.assertEqual(run(ROOT).returncode, 0, run(ROOT).stdout)

    def test_check_follows_lock_and_stale_phrase_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "governance").mkdir()
            shutil.copy(ROOT / "governance/RULEBOOK.md", repo / "governance/RULEBOOK.md")
            digest = hashlib.sha256((repo / "governance/RULEBOOK.md").read_bytes()).hexdigest()
            lock = repo / "governance/RULEBOOK.lock"
            lock.write_text(f"source_repo=x/y\nsource_ref={'a' * 40}\nsha256={digest}\n")
            (repo / "AGENTS.md").write_text("# agents\n")
            (repo / "CLAUDE.md").write_text("@AGENTS.md\n@governance/RULEBOOK.md\n")
            self.assertEqual(run(repo).returncode, 0, run(repo).stdout)
            # A retired phrase split across lines in an adapter is caught.
            (repo / "AGENTS.md").write_text("every PR requires an independent human\napproval\n")
            self.assertIn("AGENTS.md:1", run(repo).stdout)
            # A phrase added to the rulebook block is enforced; the lock must follow the edit.
            (repo / "AGENTS.md").write_text("ok\nuse the zebra gate\n")
            text = (repo / "governance/RULEBOOK.md").read_text(encoding="utf-8")
            (repo / "governance/RULEBOOK.md").write_text(
                text.replace("```stale-phrases\n", "```stale-phrases\nzebra gate\n"))
            out = run(repo).stdout
            self.assertIn("does not match the sha256", out)
            self.assertIn("AGENTS.md:2", out)
            # Out-of-scope paths are ignored unless the lock includes them.
            (repo / "AGENTS.md").write_text("ok\n")
            (repo / "notes").mkdir()
            (repo / "notes/x.md").write_text("zebra gate\n")
            self.assertNotIn("notes/x.md", run(repo).stdout)
            lock.write_text(lock.read_text() + "scan_include=notes/*.md\n")
            self.assertIn("notes/x.md", run(repo).stdout)
            (repo / ".cursorrules").write_text("x")
            (repo / "CLAUDE.md").write_text("@AGENTS.md\n")
            out = run(repo).stdout
            self.assertIn(".cursorrules is retired", out)
            self.assertIn("must import @governance/RULEBOOK.md", out)

    def test_gmail_hook_matches_both_tool_prefixes(self):
        settings = json.loads((ROOT / ".claude/settings.json").read_text(encoding="utf-8"))
        matchers = [h["matcher"] for h in settings["hooks"]["PreToolUse"]
                    if "deny_tool.py" in h["hooks"][0]["command"]]
        for tool in ("mcp__Gmail__trash_message", "mcp__Gmail__trash_thread",
                     "mcp__claude_ai_Gmail__trash_message", "mcp__claude_ai_Gmail__delete_thread"):
            self.assertTrue(any(re.fullmatch(m, tool) for m in matchers), tool)
        for tool in ("mcp__Gmail__send_message", "mcp__Gmail__label_message"):
            self.assertFalse(any(re.fullmatch(m, tool) for m in matchers), tool)

    def test_reference_first_skill_and_templates(self):
        skill = (ROOT / ".claude/skills/reference-first-design/SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill.startswith("---\nname: reference-first-design\n"))
        self.assertIn("「參考做法」", skill)
        for path in (".github/PULL_REQUEST_TEMPLATE.md", "governance/templates/pull_request_template.md"):
            self.assertIn("參考做法", (ROOT / path).read_text(encoding="utf-8"), path)


if __name__ == "__main__":
    unittest.main()
