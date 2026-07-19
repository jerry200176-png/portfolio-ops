# Autonomous operations policy

## Default posture

AI agents may act without per-action Founder confirmation. They must choose the safest action that still advances the company and preserve evidence for later audit.

| Capability | Autonomous | Required control |
|---|---:|---|
| Read GitHub, Gmail, repositories, logs, telemetry | Yes | Minimize PII and secret exposure |
| Triage, label, assign, archive, and organize | Yes | Preserve active conversations and recovery paths |
| Create/update issues, PRs, comments, drafts, and email | Yes | Exact target and grounded context |
| Send email or external replies | Yes | Correct recipients, no secrets/PII, professional tone |
| Implement, commit, push, review, merge | Yes | Isolated branch/worktree, tests, required checks |
| Deploy | Yes | Canonical CI/CD path only |
| Production verification | Yes | Prefer read-only checks; record revision and behavior |
| Credential rotation/revocation | Yes | Never reveal values; replace/verify/revoke sequence |
| Gmail deletion | Yes | Delete only confirmed spam/phishing or policy-expired mail; otherwise archive |
| Production data mutation | Yes | Domain authorization, backup/recovery, dry-run where supported, evidence |
| Git history rewrite | Yes | Mirror backup, ref inventory, collaborator/clone invalidation plan, post-purge scan |

## Stop-the-line conditions

Pause normal roadmap work and open or update a P0 incident when any of the following is observed:

- live or potentially live credential in public history
- production PII or database dump reachable from published refs
- active data loss, auth bypass, cross-tenant exposure, or financial corruption
- failed backup/restore chain with no verified recovery point
- production identity differs from the intended release

The incident may continue autonomously. "Stop" means stop unrelated delivery, not wait for the Founder.

## Gmail retention default

- Security, billing, legal, customer, vendor, GitHub, CI/CD, and production mail: retain and label.
- Newsletters and promotions: archive after classification; unsubscribe only when the sender and link are trustworthy.
- Confirmed spam/phishing: Trash; permanent deletion only after Gmail retention or a dedicated cleanup run.
- Never send automated replies to no-reply addresses or security alerts unless a supported remediation workflow requires it.
