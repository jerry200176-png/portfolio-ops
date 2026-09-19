# Effect Journal + reconciler + scheduler

## Allowlisted mutations

- `github_pr_create`
- `github_pr_comment`
- `github_pr_merge`

Repos: `jerry200176-png/portfolio-ops` only.

**Forbidden:** deploy, workflow_dispatch, production DB write, migration, SSH.

## Safety

- Deterministic `effect_id` from run/action/repo/target/head_sha
- Idempotent declare/execute
- Approval consume-once
- TOCTOU head re-check
- `executing`/`ambiguous` → reconcile via observation
- Production deploy authority remains disabled

## CLI

- `graph effect RUN_ID --action … --pr N [--fake]`
- `graph reconcile RUN_ID --pr N`
- `graph schedule-tick`
