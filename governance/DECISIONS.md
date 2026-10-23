# Governance decision log

Append-only, MADR-style. Never edit or delete an entry's Decision text; when a later decision
replaces it, change only its **Status** to `Superseded by D-NNNN` (and say which part).
Decisions bind only as restated in `governance/RULEBOOK.md` or a repo `AGENTS.md`.
Product decision logs (for example AllTrue `docs/governance/FOUNDER_STANDING_DECISIONS.md`)
follow the same form.

## D-0001 Company Constitution v1.2.0 (2026-07-19)

- **Status:** Superseded by D-0003 (precedence list and "stricter rule wins" clause).
- **Decision:** `governance/COMPANY_CONSTITUTION.md` set a 7-level precedence list; overlays said
  the stricter rule wins, so any stale "needs Founder approval" sentence bound agents (plan C9).

## D-0002 Agent is operator (2026-09-04); cloud default, Exo retired (2026-10-14)

- **Status:** Accepted, restated in RULEBOOK sections 3–5 and 9. "Protected activation needs
  Founder approval" is superseded by D-0003.
- **Decision:** `governance/AUTONOMY_POLICY.md` made eligible merges, routine deploys, issue close
  and migration authoring agent-owned. Cloud session is the default; ExoProtocol is retired;
  additive-only migrations marked T2 by a product classifier use its pipeline (PR #136, #137).

## D-0003 One portfolio rulebook; end-to-end delivery; gates face outside input (2026-10-21)

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
     Clarified the same day: 「我說的參考也可以比如說 使用rea參考競品 參考相關功能
     其他大公司軟體怎麼做的 從根本問題解決」. References include competitors and big-company
     software, and the section states root cause vs symptom.
  8. Add-ons the same day: competitor research is black-box only and new MCP/agent tools need a
     security review (B10; `rea` not adopted: anomalous star growth, single maintainer, unpinned
     `@latest` install, code-executing tools, known malicious clone). Token budget K1–K6 (Founder:
     「然後也參考開源解決消耗token太大的問題」); portfolio-ops runs at 340 lines until its CLAUDE.md
     is slimmed in PR 1b.
- **Consequences:** Older policy files become pointers in follow-up PRs; until then the rulebook
  wins on conflict. Platform controls naming the Founder stay until a product PR changes them.

## D-0004 Design before code; no duplicate features (2026-10-21)

- **Status:** Accepted (Founder-directed via the coordinating session). Rulebook 2.1.0.
- **Context:** Founder, 2026-10-21: 「我怕你在修或做功能的時候做出重複的東西 或是UI/UX不好
  希望你做之前都能詳細規劃 有架構等 就像一個軟體公司要上線產品一樣」.
- **Decision:** Every feature and non-trivial fix has a short design doc in the issue before
  implementation (problem and user, inventory of existing features, at least two options,
  architecture, UX, acceptance, rollout and rollback, metrics), modelled on Google design docs
  and Amazon working backwards. D3 reviewers check for duplication and UX consistency;
  duplication is P1. Skill `product-design-doc` is vendored to product repos with
  `reference-first-design`; PR templates gain 「設計文件」 and 「重複檢查」 lines. Fixes of about
  50 lines or less with no UI change use a 5-line version.
- **Also:** PR 1b slimmed `CLAUDE.md`/`AGENTS.md` and pointer-ized the Constitution, Autonomy
  policy, Agent bootstrap and Portfolio agent contract, so `max_always_loaded_lines` is back at
  the default 300 (K1; the temporary 340 in D-0003 is retired).

## D-0005 Agents may delete stale remote branches; B5 narrowed (2026-10-23)

- **Status:** Accepted (Founder-directed via the coordinating session). Rulebook 2.2.0. Widens
  agent capability, so per RULEBOOK section 11 the PR (opened 2026-10-23T16:30Z, 2026-10-24
  00:30 Asia/Taipei) merges no earlier than 2026-10-25 00:30 Asia/Taipei (2026-10-24T16:30Z).
  B1 is unchanged.
- **Context:** Founder, 2026-10-23: 「我希望你有權限幫我刪除branches」; 「我不要你一直來跟我要批准
  或是要求GO」. Cloud sessions push one branch per task, and branches merged outside
  `gh pr merge --delete-branch`, closed PRs and abandoned agent work pile up in every repo
  (see `docs/github-governance/BRANCH_CLEANUP_CANDIDATES.md`). Old B5 allowed only
  `--delete-branch` at merge, so every other cleanup waited on the Founder.
- **Decision:** An agent may delete a remote branch only when all hold: it is not the default
  branch, `HEAD`, `release/*`, a tag or protected by a ruleset or branch protection; it has no
  open PR; its tip SHA is the head of a merged or closed PR from it, or is already in the
  default branch (`git merge-base --is-ancestor <tip> origin/main`); it is deleted alone, after
  those checks, as its own top-level command in one of four forms (`git push <remote> --delete
  refs/heads/<branch>`, `-d refs/heads/<branch>`, `:refs/heads/<branch>`, or `DELETE
  .../git/refs/heads/<branch>` via `gh api` or `curl`); and its name and tip SHA are recorded in
  the session checkpoint. Deleting unmerged commits that no PR preserves, force-push and
  history rewrite stay banned; `gh pr close --delete-branch` is not a B5 form. The Bash hook
  allows only those four forms for one valid, non-protected branch per command and denies:
  bare or tag names; protected and release names; invalid ref names and `.`/`..`/empty
  segments; globs, variables, substitution and percent-encoding in names; deletions run
  through xargs, parallel, find -exec, eval, `bash -c`, loops or other tools; more than one
  deletion; abbreviated, ambiguous or unknown `git push` long options (git accepts prefixes
  such as `--del`); `--mirror`, `--prune`, `+<refspec>`, `--force*` and short flags with `f`;
  `remote.<name>.push`/`.mirror` set through `-c`, `GIT_CONFIG_*` or `git config`, and push
  mirror remotes; REST create/update/force of refs and any REST method the hook cannot read;
  writes to rulesets, branch protection and branch renames; GraphQL ref, branch-protection and
  ruleset mutations and queries read from files; `gh pr close --delete-branch`,
  `gh release delete --cleanup-tag` and `gh pr merge --admin`. The hook cannot see PR state or
  ancestry; those checks are the agent's duty under B5. Review round 1 on the PR found the
  first hook revision bypassable (prefixes, xargs placeholders, REST dot segments, combined
  `-sX`); all reported shapes are now regression tests.
- **Why it is reversible:** a branch whose tip is a merged or closed PR head comes back with the
  PR's "Restore branch" button (GitHub keeps `refs/pull/<n>/head`). A tip already in the default
  branch is recreated from the recorded SHA (`git push origin <sha>:refs/heads/<name>`).
- **Residual risk:** the hook checks text, not history. An agent that skips the PR and ancestry
  checks can delete commits no PR holds; those survive only while GitHub keeps the unreachable
  objects (no guarantee), and only the recorded tip SHA finds them. Protected branches named
  outside the hook's list (for example `production`) rely on their ruleset. Not caught by the
  hook: indirection across tool calls or through a variable command name (`g=git; $g push`,
  aliases), deletions inside script files, a REST POST whose path is in a variable, and edits
  to `.git/config` by other means. Mitigations: tip SHA in the checkpoint, ruleset deletion
  protection on default branches, D3 review of any cleanup script.
