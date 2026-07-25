# Agent dispatch map

| Step | Agent | Read-only? |
|---|---|---|
| Local/GitHub repo inventory, tiering, baseline survey | `portfolio-auditor` | Yes |
| GitHub issue/PR/CI triage | `github-triage` | Yes |
| Gmail signal search | `gmail-signal-analyst` | Yes |
| Reference/starred-repo research | `reference-repo-researcher` | Yes |
| UX lens of baseline audit | `ux-reviewer` | Yes |
| Security lens / secret-exposure check | `security-reviewer` | Yes |
| Implementation (one repo, one branch, Draft PR) | `repo-maintainer` | No — the only writer |
| Independent re-verification of implementer's claims | `evidence-verifier` | Yes |

Full agent definitions: `../../../agents/`. Dispatch research/review agents
in parallel when their scopes don't overlap; never run two `repo-maintainer`
invocations against the same repository concurrently, and never run
`repo-maintainer` against a dependent/production-adjacent system in parallel
with another mutating agent just because it's technically possible.
