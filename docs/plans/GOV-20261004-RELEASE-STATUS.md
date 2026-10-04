# Weekly release status follow-up

Goal: extend the existing read-only weekly report with an evidence-backed
pending deployment candidate, protected blocker, and evidence age. A healthy
runtime endpoint must not imply product acceptance.

1. Read GitHub deployment/status/pending-deployment evidence through the
   existing `gh` CLI. Missing access or ambiguous status yields UNKNOWN.
2. Show exact observed runtime SHA, pending candidate SHA, pending reviewer
   blocker only when GitHub proves it, and observation/inventory ages.
3. Test pending reviewer, unproven waiting, old successful deployment,
   missing API access, and runtime-only verification semantics.

Risk: R1 reporting code only. No new secrets, scheduler, database, production
mutation, or inventory timestamp edits. Rollback is a normal revert. Stop at
Draft PR for independent review and required checks.
