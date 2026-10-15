"""Regression tests for the Gmail trash/delete machine ban and agent tool scopes.

The ban (governance/AUTONOMY_POLICY.md "Gmail trash / delete: No — Machine
ban") is enforced by `.claude/settings.json` routing destructive Gmail MCP
tools to `.claude/hooks/deny_tool.py`. Claude Code names the Gmail server
`claude_ai_Gmail` locally and `Gmail` in cloud sessions, so both schemes must
be covered. These tests read the committed settings, so tightening or
loosening the matcher is visible here.
"""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / ".claude" / "settings.json"
DENY_TOOL = ROOT / ".claude" / "hooks" / "deny_tool.py"
AGENTS = ROOT / ".claude" / "agents"

PREFIXES = ("mcp__claude_ai_Gmail__", "mcp__Gmail__")
DESTRUCTIVE = (
    "trash_message",
    "trash_thread",
    "untrash_message",
    "untrash_thread",
    "delete_message",
    "delete_thread",
    "batch_delete_messages",
    "delete_draft",
    "delete_label",
    "mark_message_spam",
    "mark_thread_spam",
)
# Allowed by AUTONOMY_POLICY ("Read, search, label, archive, draft, send, and
# reply"). The hook must not route these to deny_tool.py.
ALLOWED = (
    "search_threads",
    "get_thread",
    "get_message",
    "list_labels",
    "send_message",
    "reply",
    "create_draft",
    "update_draft",
    "label_message",
    "label_thread",
    "unlabel_message",
    "create_label",
)
READ_ONLY_AGENTS = (
    "evidence-verifier",
    "github-triage",
    "gmail-signal-analyst",
    "reference-repo-researcher",
    "security-reviewer",
    "ux-reviewer",
    "portfolio-auditor",
)
# GitHub/Gmail MCP tools a read-only agent may hold: search/get/list, the
# single-method readers (issue_read, pull_request_read), and secret scanning,
# which reports alerts without changing the repository.
READ_SHAPE = re.compile(r"^((search|get|list)_\w+|\w+_read|run_secret_scanning)$")


def _settings():
    return json.loads(SETTINGS.read_text(encoding="utf-8"))


def _gmail_matchers():
    out = []
    for entry in _settings()["hooks"]["PreToolUse"]:
        commands = " ".join(h.get("command", "") for h in entry.get("hooks", []))
        if "deny_tool.py" in commands:
            out.append(entry["matcher"])
    return out


def _matches(matcher, tool):
    # Claude Code treats a matcher of only [A-Za-z0-9_|] as an exact name
    # list and anything else as a regex.
    if re.fullmatch(r"[A-Za-z0-9_|]+", matcher):
        return tool in matcher.split("|")
    return re.search(matcher, tool) is not None


def _agent_tools(name):
    text = (AGENTS / f"{name}.md").read_text(encoding="utf-8")
    line = re.search(r"^tools: (.*)$", text, re.M).group(1)
    return [t.strip() for t in line.split(",")]


class GmailDenyHookTest(unittest.TestCase):
    def test_every_destructive_name_is_denied_by_every_matcher(self):
        matchers = _gmail_matchers()
        self.assertGreaterEqual(len(matchers), 2, "need regex + exact-name layers")
        for matcher in matchers:
            for prefix in PREFIXES:
                for tool in DESTRUCTIVE:
                    with self.subTest(matcher=matcher[:30], tool=prefix + tool):
                        self.assertTrue(_matches(matcher, prefix + tool))

    def test_regex_layer_covers_unknown_gmail_server_and_verb_variants(self):
        regexes = [m for m in _gmail_matchers() if not re.fullmatch(r"[A-Za-z0-9_|]+", m)]
        self.assertTrue(regexes)
        for name in (
            "mcp__plugin_google_gmail__trash_message",
            "mcp__gmail__permanently_delete_thread",
            "mcp__Gmail__batch_trash_messages",
            "mcp__Gmail__empty_trash",
        ):
            with self.subTest(name=name):
                self.assertTrue(any(re.search(r, name) for r in regexes))

    def test_allowed_gmail_tools_are_not_routed_to_deny(self):
        for matcher in _gmail_matchers():
            for prefix in PREFIXES:
                for tool in ALLOWED:
                    with self.subTest(tool=prefix + tool):
                        self.assertFalse(_matches(matcher, prefix + tool))

    def test_permissions_deny_lists_core_names_in_both_schemes(self):
        deny = set(_settings()["permissions"]["deny"])
        for prefix in PREFIXES:
            for tool in ("trash_message", "trash_thread", "delete_message",
                         "delete_thread", "batch_delete_messages"):
                self.assertIn(prefix + tool, deny)

    def test_deny_tool_emits_deny_decision(self):
        for prefix in PREFIXES:
            payload = json.dumps({"tool_name": prefix + "trash_thread", "tool_input": {}})
            out = subprocess.run(
                [sys.executable, str(DENY_TOOL)], input=payload,
                capture_output=True, text=True, check=True,
            )
            decision = json.loads(out.stdout)["hookSpecificOutput"]
            self.assertEqual(decision["permissionDecision"], "deny")


class AgentToolScopeTest(unittest.TestCase):
    def test_local_mcp_tools_have_cloud_twins(self):
        pairs = {
            "mcp__plugin_github_github__": "mcp__github__",
            "mcp__claude_ai_Gmail__": "mcp__Gmail__",
        }
        for path in AGENTS.glob("*.md"):
            tools = _agent_tools(path.stem)
            for tool in tools:
                for local, cloud in pairs.items():
                    if tool.startswith(local):
                        with self.subTest(agent=path.stem, tool=tool):
                            self.assertIn(cloud + tool[len(local):], tools)
            # No cloud tool may exist without the same local tool.
            for tool in tools:
                for local, cloud in pairs.items():
                    if tool.startswith(cloud):
                        with self.subTest(agent=path.stem, tool=tool):
                            self.assertIn(local + tool[len(cloud):], tools)

    def test_read_only_agents_have_no_write_tools(self):
        for name in READ_ONLY_AGENTS:
            tools = _agent_tools(name)
            self.assertFalse({"Write", "Edit", "NotebookEdit"} & set(tools), name)
            for tool in tools:
                if tool.startswith("mcp__") and "playwright" not in tool:
                    verb = tool.split("__")[-1]
                    with self.subTest(agent=name, tool=tool):
                        self.assertRegex(verb, READ_SHAPE)

    def test_gmail_signal_analyst_is_search_and_get_only(self):
        gmail = [t.split("__")[-1] for t in _agent_tools("gmail-signal-analyst")
                 if "Gmail" in t]
        self.assertTrue(gmail)
        for verb in gmail:
            self.assertRegex(verb, r"^(search|get|list)_")


if __name__ == "__main__":
    unittest.main()
