# Session closeout

Triggered when the Founder says **收工**, **準備收工**, or **close out this
session**. It does not replace `docs/agent-operating-loop.md` or
`governance/AUTONOMY_POLICY.md`. Closeout never merges, deploys, sends mail,
or mutates production.

The split between an append-only technical trace and a human-editable public
draft is adapted from the compact small-software harness spec (v3) on the
Founder's desktop. That spec is a per-project document system; this SOP maps
the same split onto existing control-plane files.

## Order (do not skip; say "no change" when empty)

1. **Progress.** Update `state/work-queue.yaml` and, if the dashboard would
   otherwise lie, `CEO_DASHBOARD.md`: what finished, what is blocked, current
   focus. Do not invent a second WBS tree.
2. **Touched specs.** If `docs/`, `governance/`, or a product `AGENTS.md` /
   constitution changed in this session, name the files. If none, say so.
3. **Technical record.** Append a `docs/templates/learning-record.md` (or the
   same fields in `reports/YYYY-MM-DD-*.md`). Do not edit earlier bullets to
   rewrite history; add a correction line that points at the old entry.
4. **Public draft.** Append `docs/templates/session-journal.md` raw material
   only. Mark each bullet speakable / not speakable. Do not write a finished
   post.
5. **Lesson promotion.** If a failure matches `docs/HARD_LESSONS.md` rules,
   append one line there (or to the product `AI_REGRESSION_LESSONS.md` when
   the defect is product-specific). Do not rewrite autonomy policy.
6. **Closeout summary.** One short paragraph: done, unverified, Founder-gated
   leftover.

## Mapping (do not create a parallel seven-file tree here)

| Harness idea | Control-plane file |
|---|---|
| roadmap cockpit | `state/work-queue.yaml`, `CEO_DASHBOARD.md` |
| append-only log | learning record / dated `reports/` |
| public journal | `docs/templates/session-journal.md` |
| hard lessons | `docs/HARD_LESSONS.md` or product regression lessons |
| ai-rules | `CLAUDE.md` + `governance/AUTONOMY_POLICY.md` (Founder-owned) |

AllTrue and Sunrise keep their own INDEX / constitution. Closeout does not
install `spec.md` / `design.md` / `roadmap.md` into those products.
