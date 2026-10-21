# Governance decision log

Append-only, MADR-style. Never edit or delete an entry's Decision text; when a later decision
replaces it, change only its **Status** to `Superseded by D-NNNN` (and say which part).
Decisions bind only as restated in `governance/RULEBOOK.md` or a repo `AGENTS.md`.
Product decision logs (for example AllTrue `docs/governance/FOUNDER_STANDING_DECISIONS.md`)
follow the same form.

## D-0001 Company Constitution v1.2.0 (2026-07-19)

- **Status:** Superseded by D-0004 (precedence list and "stricter rule wins" clause).
- **Context:** Agents needed one authority chain across products.
- **Decision:** `governance/COMPANY_CONSTITUTION.md` set a 7-level precedence list; portable
  overlays said "if this overlay conflicts with a stricter product or safety rule, the stricter
  rule wins".
- **Consequences:** Any stale "needs Founder approval" sentence anywhere counted as stricter,
  so agents stopped on routine work (plan C9).

## D-0002 Agent is the operator; risk-based autonomy (2026-09-04, revised 2026-10-04)

- **Status:** Accepted; restated in RULEBOOK sections 3–5. The "protected activation needs
  Founder approval" part is superseded by D-0004.
- **Decision:** `governance/AUTONOMY_POLICY.md` made eligible reversible merges, routine deploys,
  issue close and migration authoring agent-owned; production data mutation, credential
  rotation and policy semantics stayed with the Founder.

## D-0003 Cloud session default; ExoProtocol retired; additive migrations (2026-10-14)

- **Status:** Accepted; restated in RULEBOOK sections 3 and 9.
- **Decision:** Default environment is a Claude cloud session (fresh clone, branch, PR); the
  local `agent-start` gateway is legacy. ExoProtocol is retired. Additive-only migrations that
  a product's committed classifier marks T2 run through that product's pipeline (PR #136, #137).

## D-0004 One portfolio rulebook; end-to-end delivery; gates face outside input (2026-10-21)

- **Status:** Accepted (Founder-directed via the coordinating session).
- **Context:** About 120 agent-facing files restated the rules up to 9 times and contradicted
  each other (consolidation plan, contradictions C1–C23). Founder, 2026-10-21:
  「你也看有什麼開源技術 把我們文件有矛盾的地方處理掉 整理一下所有文件 感覺文件太多規則太矛盾複雜等
  要讓所有agent有同套規則遵循」; 「不要一直要我批准 很煩」;
  「要擋的是外來的東西 或是想透過in-app回報攻擊我的系統的人」; 「你要修正上線做功能都是」;
  「整個流程要參考開源技術或是大公司 不能因為這樣就不嚴謹」.
- **Decision:**
  1. `governance/RULEBOOK.md` (+ `rules.yaml`) is the single rule set, vendored byte-for-byte
     into product repos and drift-checked in CI. `CLAUDE.md` imports `AGENTS.md` and the
     rulebook; `.cursorrules` and `codex.md` are removed (AGENTS.md open standard).
  2. Precedence is one list. Safety-stricter rules win; approval-stricter rules do not.
  3. Gates block untrusted input (in-app reports, non-Founder GitHub content, bots, web, email).
     Founder-directed fixes, features and deploys run the full delivery chain D1–D9 with
     independent review, automated verification, rollback and a stop-the-line freeze.
  4. Open questions from the plan (section 6), answered by Founder direction via the
     coordinating session:
     - Q1 Rulebook text: proceed.
     - Q2 New billing/payment, identity/permission and privacy *policy* rules still come from
       the Founder's direction; agents do not invent them from in-app or GitHub suggestions.
       Code that implements decided policy is ordinary delivery. (RULEBOOK F4, T5.)
     - Q3 The single channel for Founder questions is the coordinating chat session, batched
       into one list. (Supersedes `needs-founder` issues and per-item messages; plan C12.)
     - Q4 `exoprotocol` stays public with a RETIRED banner; it is not archived.
  5. Founder-only actions are F1–F4 only. Machine bans B1–B9 keep their enforcing controls; the
     Gmail hook now matches both `mcp__claude_ai_Gmail__*` and `mcp__Gmail__*` (plan C21).
  6. When Codex is unavailable, a fresh-context reviewer agent performs D3 (plan C8, C11).
  7. Reference-first design (D0). Founder, 2026-10-21:
     「我希望雲端環境我們在做修復或是新功能 都能去參考成熟開源或是大公司軟體」. Every fix or
     feature names 1–3 mature references and records a 「參考做法」 section in the PR.
- **Consequences:** Older policy files become pointers in follow-up PRs. Until then, where they
  conflict with the rulebook, the rulebook wins. Platform controls that still name the Founder
  as reviewer stay in force until a product PR changes them.
