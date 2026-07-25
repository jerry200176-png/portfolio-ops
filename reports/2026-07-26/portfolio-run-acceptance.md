# Portfolio Run Acceptance Record

## Findings

| Severity | Finding | Resolution / evidence |
|---|---|---|
| medium | PR #9 had no minimal operator interface for creating, validating, selecting, checkpointing, resuming, and closing a mission. | Added deterministic CLI flows and documented the smallest command set. |
| medium | PR #9 described runtime usage but could not demonstrate Claude Code slash-command discovery from Codex. | Added an explicit Claude-only smoke test; no unsupported runtime claim remains. |
| medium | Mission selection was explicit-path only and could not prove exactly one active mission. | Added `active` selection, rejecting zero or multiple non-example active missions. |
| medium | The loop did not record the complete Observe → Plan → Act → Verify → Checkpoint trace. | Added deterministic phase-history checkpoint evidence. |
| low | Duplicate-PR evidence was not persisted as a Draft-PR identifier. | Persisted `draft_pr` evidence and retained reuse test. |
| accepted design | The helper is not a Claude runtime scheduler. | It is intentionally a bounded, dependency-free state helper; Claude Code remains controller and sole active-state writer. |
| accepted design | Existing Portfolio OS state is not duplicated. | Missions link to work discovered by `/portfolio-maintain`; Dashboard and work queue remain authoritative for portfolio status. |
| accepted design | Founder approvals are only for pre-existing Founder-only boundaries. | Queue bundles related actions and allows independent steps to continue. |
| accepted design | Existing safety hooks and read-only agent restrictions remain authoritative. | Deterministic tests assert existing settings and agent-definition controls; no policy files changed. |

No blocker or high finding remains.

## Runtime evidence

Codex validated the deterministic helper, schema, mission selection, resume,
bounded turn cap, monitoring, queue behavior, and `/portfolio-maintain status`
compatibility. Claude Code skill-discovery semantics are intentionally isolated
to the one smoke test in `docs/portfolio-run.md`.
