#!/usr/bin/env python3
"""PreToolUse hook that denies Gmail trash/delete tools.

Standalone test:
  echo '{"tool_name":"mcp__claude_ai_Gmail__delete_message","tool_input":{}}' | python3 deny_tool.py
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
                f"Blocked: {tool} is machine-banned mailbox destruction "
                "(governance/AUTONOMY_POLICY.md). Send/reply/label are allowed."
            ),
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
