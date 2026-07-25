---
paths:
  - "portfolio.yaml"
  - "state/work-queue.yaml"
---

# Editing portfolio.yaml or state/work-queue.yaml

- Validate shape against `schemas/portfolio.schema.yaml` before writing —
  don't add fields it doesn't define without updating the schema too.
- Every `work-queue.yaml` item needs `evidence` (what was observed, where,
  how obtained) and `next_action` (concrete, not "investigate further") —
  see `docs/evidence-policy.md`. A status change without evidence attached
  is not a valid update.
- `portfolio.yaml`'s `open_p0`/`open_p1`/`current_priority`/`next_action`/
  `latest_activity` fields must reflect *this pass's* findings, not be left
  citing a prior run — a stale number here is worse than an honest "not
  re-checked this pass."
- Never edit a `forbidden_checkouts` entry's referenced path as if it were
  the canonical checkout.
- Bump `updated_at` whenever either file changes.
