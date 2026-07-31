# Workspace operating model

## Target structure

```text
workspace/
├── repos/                 # canonical bare Git object stores; no app editing
├── <project>/             # canonical checkout, one per active product
├── tasks/                 # named task metadata and launch state
├── worktrees/             # active isolated branches/worktrees
├── archives/              # approved, immutable-ish snapshots; no auto-delete
├── evidence/              # inventories, fetch records, verification output
├── backups/               # verified recovery artifacts
├── agent-control/         # safe launcher and preflight
└── portfolio-ops/         # company control plane and governance source
```

The current workspace already follows most of this model. Existing legacy
paths remain in place until a separate inventory, backup, impact assessment,
rollback plan, and Founder approval authorize a move or archive.

## Ownership boundaries

- `repos/` is the canonical Git object source.
- Canonical checkouts are stable integration points and are not used for
  high-divergence experiments.
- Active task work belongs in a dedicated worktree and branch.
- `archives/`, `evidence/`, and `backups/` are append-only from the automation
  perspective; retention and deletion are Founder decisions.
- `portfolio-ops` records state, evidence, policy, and decisions. It does not
  contain product source code.

## Safety gates

Before any Git or filesystem mutation: inventory, preserve dirty state,
capture a recovery artifact, checksum it, and write an impact list. Remote
sync is fetch-only until a separately approved integration plan exists.
`prunable` is evidence that Git cannot currently resolve a worktree path; it
is not permission to remove anything. Each such path must be checked for
external references and recovered or archived before a decision.

## Integration rule

When a canonical checkout is far ahead and behind its remote, create a new
integration worktree from the intended remote base. Do not rewrite or merge
the canonical checkout in place. For `/home/jerry/alltrue`, the current
1284-ahead/1683-behind state is therefore a decision and investigation item,
not a synchronization task.
