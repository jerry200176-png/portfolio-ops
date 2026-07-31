# Company governance benchmark — 2026-08

## Research question

What repeatable repository and workspace controls make a small portfolio look
and operate like a software company, while keeping destructive actions behind
explicit approval?

## Sources reviewed

The review covered the owner's starred repositories, including
[OpenSSF Scorecard](https://github.com/ossf/scorecard),
[Gitleaks](https://github.com/gitleaks/gitleaks),
[StepSecurity Harden Runner](https://github.com/step-security/harden-runner),
[Supabase](https://github.com/supabase/supabase),
[Chatwoot](https://github.com/chatwoot/chatwoot),
[Filament](https://github.com/filamentphp/filament),
[Primer CSS](https://github.com/primer/css),
[Radix Primitives](https://github.com/radix-ui/primitives), and the owner's
[AllTrue System](https://github.com/jerry200176-png/AllTrue_System) and
[Sunrise Cafe](https://github.com/jerry200176-png/sunrise-cafe).

Recurring repository patterns were: README and contributor guidance, a code of
conduct, security policy, license decision, CODEOWNERS, issue/PR templates,
lockfiles/manifests, tests, and workflows for CI, security, dependency
updates, and releases. Mature projects also separate product code from
operational metadata and keep an explicit rollback/evidence trail.

The current portfolio already has a useful control-plane foundation: bare
repositories under `workspace/repos`, active worktrees under
`workspace/worktrees` and `workspace/tasks`, and `portfolio-ops` governance,
mission state, and evidence policies. The gap is standardization and
verification, not a need to mass-move product directories.

## Adopted baseline

This branch adds:

- community-health files and review ownership;
- issue/PR intake templates;
- weekly GitHub Actions dependency monitoring;
- least-privilege CI and security workflows;
- a versioned workspace manifest and operating model;
- phase 1 inventory/backup, phase 2 fetch-only, and phase 3 proposal-only
  scripts;
- tests and acceptance checks for the safety boundaries.

## Deliberately not automated

No script deletes, moves, renames, resets, cleans, merges, rebases, prunes, or
force-pushes. A legal license choice, repository rulesets, required checks,
production deployment, and any archive/removal action remain Founder decisions.

## Official guidance used

GitHub's [community profile checklist](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories)
checks for README, code of conduct, license, and contributing guidance.
[Dependabot](https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/dependabot-quickstart)
and [dependency review](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security/configure-dependency-review-action)
support dependency hygiene. GitHub documents
[CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners),
[issue forms](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/configuring-issue-templates-for-your-repository),
and [rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets).
[OpenSSF Scorecard](https://www.scorecard.dev/) provides a useful security
posture benchmark.
