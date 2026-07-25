---
paths:
  - ".claude/agents/**/*.md"
---

# Writing or editing a subagent definition

Codifies the pattern already followed by every agent in `.claude/agents/` —
write new ones the same way, don't improvise a different shape.

- Frontmatter needs `name`, `description` (specific enough that the
  orchestrator picks the right agent without guessing), `tools` (an
  explicit allowlist — never omit it to "inherit everything"), and
  `model: inherit` unless there's a specific reason to pin one.
- State what the agent's tool list makes *impossible*, not just what it
  shouldn't do — e.g. "you have no merge_pull_request tool, merging is
  impossible for you, by construction" beats "don't merge." Instruction
  compliance is best-effort; a missing tool is not.
- Read `../../CLAUDE.md` (and `../../docs/security-boundaries.md` for
  anything touching untrusted content or secrets) as the agent's first
  instruction — every existing agent does this because subagents don't
  inherit the orchestrator's context, so each one needs its own pointer.
- State what the agent returns (text findings vs. files) and to whom. Only
  `repo-maintainer` has Write/Edit — every other agent returns text for the
  orchestrator to persist, keeping a single auditable writer for portfolio
  state.
- A reviewer/verifier agent (`ux-reviewer`, `security-reviewer`,
  `evidence-verifier`) must re-derive claims from primary sources, not
  restate an implementer's summary as fact.
