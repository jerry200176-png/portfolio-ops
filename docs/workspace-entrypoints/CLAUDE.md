# Jerry Software Portfolio workspace rules

The authoritative company SOP is in `/home/jerry/workspace/portfolio-ops`.
Read the company contract and operating loop before the target repository's
own instructions. Use `workspace.manifest.yaml` as inventory truth and the
`agent-control` gateway for isolated worktrees and session provenance.

The required operating loop is:

```text
discover -> research -> plan -> implement -> verify -> review -> learn
```

Eligible T0/T1 work runs the inner verify-retry loop in
`docs/verify-retry-loop.md` before verify is done. R0–R2 squash-merge after
required GitHub checks (`docs/fleet-merge-policy.md`). The Agent is the
operator. Machine bans stay (secrets, force-push, production SSH).

The Portfolio Ops repository is the company control plane. Record the plan,
evidence, verification result, and learning record in GitHub and the control
plane. Do not start from a dirty canonical checkout.

Research concrete choices using official or primary material, a mature-company
practice, and a maintained open-source or starred repository. Record fit,
license, adoption cost, and the smallest experiment. CI passing is evidence
for merge, not a reason to wait for a human click.
