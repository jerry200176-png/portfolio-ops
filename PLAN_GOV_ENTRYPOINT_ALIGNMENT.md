# Plan: align portfolio agent entrypoints

## Goal

Make the committed `AGENTS.md`, `CLAUDE.md`, and `codex.md` point to the same
authority chain and required session gateway already specified by the current
`governance/AGENT_BOOTSTRAP.md` and `governance/company-agent-contract.yaml`.
Preserve the existing risk, review, merge, deployment, and Founder gates.

## Steps

1. Inspect all committed entrypoints, precedence contract, existing tests, and
   current GitHub rules/checks; do not treat the stale local checkout as source.
2. Remove stale generated instructions that make ExoProtocol mandatory or
   describe it as a parallel policy authority. Keep only an explicit note that
   Exo is optional for isolated experiments and cannot override committed
   product/company contracts. Preserve the tracked `.exo/` files as a legacy
   experiment exception in this scoped PR; do not describe them as local-only.
3. Align the portable portfolio overlay and onboarding path with the approved
   operator policy. Restrict the Exo governance workflow to manual exact-SHA
   experiment dispatch and use that curated file as the onboarding template;
   the live rulesets do not require it.
4. Extend the existing governance baseline test to detect entrypoint authority
   drift, mandatory Exo lifecycle instructions, and accidental Exo CI gating.
5. Run focused and full required local checks, inspect the diff, then open a PR
   with exact evidence and rollback notes. Merge only if current checks and
   applicable review/risk policy authorize it.

## Acceptance

- Each agent entrypoint names `governance/AGENT_BOOTSTRAP.md` as the portable
  company bootstrap, `COMPANY_CONSTITUTION.md` / `AUTONOMY_POLICY.md` as policy
  authority, and `agent-control/bin/agent-start` as the local gateway.
- None claims Exo session start/finish, Exo locks, `exo push`, or Exo-generated
  text is mandatory for ordinary governed delivery.
- The optional Exo workflow does not run on every PR and is absent from required
  checks; explicit experiment runs remain possible.
- The onboarding command describes generated Exo files and CI as local/manual
  experiments and does not recommend merging them or adding required checks.
- The legacy tracked `.exo/` tree is explicitly excluded from this PR and is not
  presented as a fleet authority or gate; its migration/removal is a separate
  scoped decision because the current bootstrap calls for local-only trees.
- A regression test fails if those contradictions return.
- No protected-action boundary or runtime state is changed.

## Stop points

- Stop before changing substantive autonomy, review, or production policy.
- Do not merge if required checks, review evidence, or release-trigger risk
  classification is missing or stale.
