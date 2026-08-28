# Research decision record — verify-retry inner loop

- Problem and success criteria:
  Eligible T0/T1 work should retry against machine-checkable commands until
  pass or stop-loss, with generate/review split and a written record, without
  weakening Founder gates.
- Official or primary source:
  Captain Balung, [遠航七階](https://captain-balung-blog.ghost.io/seven-stages-ai-agent-workflow/)
  (2026-07). Used as a maturity map only: spec, independent checker, retry,
  record. Not copied as ceremony or as autonomy policy.
- Mature-company practice:
  Existing portfolio-ops loop already separates implement, verify, independent
  evidence review, and Draft PR (`docs/agent-operating-loop.md`,
  `docs/evidence-policy.md`). Google/GitHub-style CI as the gate, human merge.
- Maintained open-source/starred repository:
  ExoProtocol session/ticket checks (fleet pilot) and this repo's
  `evidence-verifier` handoff in `.claude/skills/portfolio-maintain/`.
- Transferable pattern:
  Write checks as commands; keep implementer and reviewer roles; stop after a
  bounded number of retries; keep merge off the inner loop.
- What does not transfer:
  "Human leaves the loop", mythic stage names, cross-media remix (stage 5),
  multi-person fleet rituals (stage 6–7). Irreversible actions stay Founder-only.
- License and fit review:
  Article is a public essay; we paraphrase concepts and link. No code copied.
- Adoption cost and smallest experiment:
  One T0 docs patch in portfolio-ops plus a unit test that the SOP still
  forbids merge/deploy. Do not change AUTONOMY_POLICY.
- Decision and GitHub issue/PR:
  Adopt the inner loop as `docs/verify-retry-loop.md`; first record is this
  change. Issue/PR links added when opened.
