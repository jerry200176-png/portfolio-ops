# Small-project harness overlay

Use this **only** when onboarding a **new** repository that matches a small
tool: few users, months of expected life, not payments/PII/medical, not a
multi-year public product.

**Do not apply** to AllTrue, Sunrise Cafe, or portfolio-ops. Those already
have constitutions, INDEX, control-plane contracts, and Founder gates.

Adapted from the Founder's compact small-software harness spec v3 (desktop
meta-spec). Do not paste that file into git. Fill the seven project files
below instead of inventing a sixteenth policy.

## Seven files (one job each)

| File | Job | Who changes it |
|---|---|---|
| `README.md` | 30-second human front door | Founder-led |
| `spec.md` | Spirit, in/out of scope, machine-checkable features | Founder decides, agent proposes |
| `CLAUDE.md` or `ai-rules.md` | Allow / confirm / never; stall rule; closeout | Founder-owned (agents may only append hard lessons) |
| `design.md` | How it is built, rollback before first deploy | Agent-led; taste stays Founder |
| `roadmap.md` | Phase → feature id → leaf checks (commands) | Agent-led |
| `log.md` | Append-only technical trace | Agent appends |
| `journal.md` | Public draft bullets | Agent appends raw; Founder edits |

`CLAUDE.md` is either the rules file itself or a three-line pointer. Do not
duplicate the same rules in two files.

## Required red lines (same as the fleet)

1. Irreversible actions need in-session Founder confirmation.
2. Agent-initiated calls get a trace in `log.md`.
3. `log.md` is append-only; corrections are new entries.

## Pipeline order for the first roadmap phase

Deploy empty shell → git/db/backend/frontend path works → smallest visible
MVP. Features come after the pipe carries water. Reversible CLI/MCP work is
the agent's job; do not hand it back as homework.

## Intake extra fields

When registering such a repo in `docs/templates/project-intake.md`, set
`harness: small-project` and link the seven files. Fleet registration
(manifest, catalog, CI baseline) still applies.
