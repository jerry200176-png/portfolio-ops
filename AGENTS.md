# Agent entry point

This file exists for non-Claude-Code automation that reads `AGENTS.md` by
convention. The authoritative operating rules live in `CLAUDE.md` at the root
of this repository, with procedure in
`.claude/skills/portfolio-maintain/SKILL.md`. Read both before acting.

All local and cloud agents should also load `governance/AGENT_BOOTSTRAP.md`.
It is the compact cross-agent contract; the detailed authority remains in
`governance/` and this repository's `CLAUDE.md`.

Do not duplicate rules here — if this file and `CLAUDE.md` ever disagree,
`CLAUDE.md` wins.
Company-wide contract: read `governance/company-agent-contract.yaml` and
`docs/agent-operating-loop.md` before acting on a portfolio task.

<!-- exo:governance:begin -->
<!-- Governance hash: f45f0f00b0698aa4 -->
# ExoProtocol — Agent Operating Instructions

This repository is governed by ExoProtocol. All AI agent work must follow the session lifecycle.

## ExoProtocol Governance

- kernel: exo-kernel 0.1.0
- lock hash: `f45f0f00b0698aa4...`
- generated: 2026-08-15T14:43:58+08:00

### Filesystem Deny Rules

- **RULE-SEC-001**: deny read, write on `~/.aws/**`, `~/.ssh/**`, `**/.env*`
- **RULE-GIT-001**: deny read, write, delete on `.git/**`

### Structural Rules

- **RULE-LOCK-001** (require_lock): Blocked by RULE-LOCK-001 (acquire a ticket lock first).
- **RULE-CHECK-001** (require_checks): Blocked by RULE-CHECK-001 (checks must pass before done).
- **RULE-EVO-001** (evolution_gate): Practice is mutable, governance requires explicit human approval.
- **RULE-EVO-002** (patch_first): Patch-first evolution required.

### Default Budgets

- max files changed: 12

### Approved Checks

- `npm test`
- `npm run lint`
- `pytest`
- `python -m pytest`
- `python3 -m pytest`

### Active Intents

- **INT-20260828-195058-Y1CK**: Harden deterministic workspace inventory — boundary: *Only modify scripts/workspace-inventory.sh and tests/test_governance_baseline.py in this isolated portfolio-ops worktree. Do not modify product repositories, workspace.manifest.yaml, existing worktrees, legacy checkouts, production, credentials, or cleanup behavior.*
  - TKT-20260828-195105-O0H6: Implement deterministic workspace inventory [allow: scripts/workspace-inventory.sh, tests/test_governance_baseline.py, .exo/cache/**, .exo/memory/**, .exo/locks/**, .exo/tickets/**, .exo/logs/**]
  - TKT-20260828-200309-ZE51: Track reproducible Exo governance baseline [allow: .exo/CONSTITUTION.md, .exo/config.yaml, .exo/governance.lock.json, .exo/LEARNINGS.md, .exo/policy.sealed.json, .exo/cache/**, .exo/memory/**, .exo/locks/**, .exo/tickets/**, .exo/logs/**]
  - TKT-20260828-224425-WVAG: Synchronize generated Exo adapters [allow: AGENTS.md, CLAUDE.md, .claude/settings.json, .exo/cache/**, .exo/memory/**, .exo/locks/**, .exo/tickets/**, .exo/logs/**]
  - TKT-20260828-224803-E36X: Synchronize Exo adapters from tracked baseline [allow: AGENTS.md, CLAUDE.md, .claude/settings.json, .exo/policy.sealed.json, .exo/cache/**, .exo/memory/**, .exo/locks/**, .exo/tickets/**, .exo/logs/**]
- **INT-20260828-225521-D3AV**: Make Exo scaffold reproducible and workspace hygiene explicit — boundary: *Only modify the Exo static scaffold, Exo ticket definitions, generated adapters, sealed-policy runtime artifact, and root ignore rules in this isolated portfolio-ops worktree. Do not alter product repositories, workspace manifest, existing worktrees, legacy paths, production, credentials, or delete unknown data.*
  - TKT-20260828-225531-ND05: Track Exo scaffold and ignore ephemeral state [allow: .gitignore, AGENTS.md, CLAUDE.md, .claude/settings.json, .exo/LEARNINGS.md, .exo/policy.sealed.json, .exo/schemas/**, .exo/scripts/**, .exo/templates/**, .exo/memory/index.yaml, .exo/scratchpad/INBOX.md, .exo/tickets/**, .exo/cache/**, .exo/memory/**, .exo/locks/**, .exo/logs/**]
- **INT-20260828-230615-VU12**: Record ownership-gated workspace cleanup proposal — boundary: *Only add the cleanup proposal report and its Exo governance metadata in this isolated portfolio-ops review worktree. Do not archive, remove, move, reset, clean, merge, rebase, or modify product repositories, workspace manifest, existing worktrees, legacy paths, production, credentials, or user-authored files.*
  - TKT-20260828-230624-20B2: Write durable workspace cleanup proposal [allow: reports/**, AGENTS.md, CLAUDE.md, .claude/settings.json, .exo/policy.sealed.json, .exo/tickets/**, .exo/cache/**, .exo/memory/**, .exo/locks/**, .exo/logs/**]

### Source of Truth

The values above are a **snapshot** generated from the governance manifest.

Manifest paths:
- `.exo/config.yaml` — budgets, checks allowlist, scheduler config
- `.exo/governance.lock.json` — compiled rules, deny patterns, source hash

### Test-Driven, Manifest-First Workflow

This principle applies to **all code you write** — governance and application logic alike.

1. **Config/contract is the source of truth.** When a value is defined in a config file,
   schema, manifest, or contract — code must load it from that source at runtime.
   Never copy a value from a config file and paste it as a literal in source code.
2. **Tests verify the wiring, not the value.** Tests must assert that code reads from
   the config/contract, not that it produces a specific hardcoded result.
   A test that passes when you swap the config value *and* swap the assertion is useless —
   it only proves both sides were copy-pasted from the same place.
3. **If you can change a config value and no test breaks, the test is missing.**
   Every configurable value should have at least one test that will vary the input
   and verify the output follows.

Examples:
- **BAD**: `assert budget == 10` (hardcoded, passes even if config is ignored)
- **GOOD**: set config to 42, assert output contains 42 and not the old default
- **BAD**: `MAX_RETRIES = 3` (literal in source when retries is in config)
- **GOOD**: `max_retries = load_config()['max_retries']`

### Operational Learnings

When you discover a reusable pattern, gotcha, or operational insight during a session:
- Record it with `exo reflect` (CLI) or `exo_reflect` (MCP) — NOT your private memory
- ExoProtocol reflections are injected into future session bootstraps for all agents
- Private memory files (MEMORY.md, .cursorrules, etc.) are agent-specific and invisible to the team
- If you must write to private memory, also create an ExoProtocol reflection with the same insight

**Private memory monitoring**: If `private_memory.watch_paths` in `.exo/config.yaml` is empty,
add the absolute path to your memory file (e.g., `~/.claude/.../memory/MEMORY.md`) so that
ExoProtocol can detect when you write to private memory without creating a shared reflection.

### End-of-Work Reflection

When you complete significant work or the user appears to be wrapping up:
- **Proactively** run `exo reflect --pattern '<what kept happening>' --insight '<what was learned>'`
  for each non-trivial insight discovered during the conversation
- Do NOT wait for `session-finish` — many users close the editor without explicit session end
- Good reflection triggers: bug fixes, CI failures, gotchas, architectural decisions, workflow improvements

### Tool Reuse Protocol

Before writing new utility functions, SEARCH the tool registry:
  `exo tool-search "<keywords>"`

After building a reusable utility, REGISTER it:
  `exo tool-register <module> <function> --description "..."`

Mark a tool as used when you import/call it:
  `exo tool-use <tool_id>`


## Session Lifecycle

1. `exo session-start --ticket-id <TICKET> --vendor <VENDOR> --model <MODEL> --task "<TASK>"`
2. Read `.exo/cache/sessions/<actor>.bootstrap.md`
3. Execute work within ticket scope
4. `exo session-finish --ticket-id <TICKET> --summary "<SUMMARY>" --set-status review`

## Enforcement

- Governance rules are enforced at the kernel level, not by prompt
- The bootstrap file contains your session's scope, checks, and lifecycle commands
- Drift detection runs at session-finish and is recorded in the session memento
- Audit sessions may be triggered to review your work independently

## Governed Push

Before pushing code, ALWAYS run checks first:

```
exo push                      # runs exo check, then git push (recommended)
# OR
exo check && git push         # manual equivalent
```

Do NOT use bare `git push` — it bypasses governance checks.
If checks fail, fix the issues before pushing.

## Non-Negotiables

- No governed execution without active session
- Respect lock ownership and ticket scope
- Verification is default at finish; break-glass must be explicit
- All configurable values must be loaded from their source of truth at runtime — never hardcode, always test
- Read `.exo/LEARNINGS.md` for operational learnings from prior sessions

<!-- exo:governance:end -->
