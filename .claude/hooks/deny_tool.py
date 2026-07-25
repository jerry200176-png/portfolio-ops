#!/usr/bin/env python3
"""PreToolUse hook that unconditionally denies whichever tool the settings.json
matcher routed here. Used for tools that are never autonomous in this
portfolio (merge_pull_request, Gmail mutation tools) regardless of arguments.

Standalone test:
  echo '{"tool_name":"mcp__plugin_github_github__merge_pull_request","tool_input":{}}' | python3 deny_tool.py
"""
import json
import sys


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    tool = payload.get("tool_name", "this tool")
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked: {tool} requires explicit Founder approval and is "
                "not autonomous in this portfolio (CLAUDE.md, "
                "governance/AUTONOMY_POLICY.md)."
            ),
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
