# Hook threat model

`.claude/hooks/guard_bash.py` and `.claude/hooks/deny_tool.py` are a
**textual guardrail against ordinary mistakes and casual bypass attempts**,
wired via `.claude/settings.json` PreToolUse hooks. They are **not a
sandbox** — see `docs/security-boundaries.md` for what actually bounds
agent behavior (tool-list restriction per agent, this repo's `CLAUDE.md`
rules, GitHub rulesets, and machine bans in `governance/RULEBOOK.md` section 5). This document records
the adversarial testing performed, what was found and fixed, and — just as
important — what remains unfixable by a textual hook and must be covered by
something else.

All testing below was performed with **no destructive action against a real
repository and no real credential** — throwaway repos under the OS temp
dir / session scratchpad, dummy `.env` content, and standalone piping of
synthetic JSON into the hook scripts (never executing the dangerous command
itself). The full machine-checked list lives in
`.claude/hooks/test_guard_bash.py` (run: `python3
.claude/hooks/test_guard_bash.py`) — 149 dangerous cases, 53 safe cases, plus
branch-detection and symlink-resolution cases, all passing as of this
writing.

## Adversarial cases tested, and outcome

| Category | Example | Before this pass | After |
|---|---|---|---|
| `bash -c` / `-lc`, `sh -c` wrapping | `bash -c "git push --force origin main"` | Denied (git checks were never adjacency-strict) | Denied |
| `command git ...`, `env VAR=x git ...` | `env FOO=bar git push --force origin main` | Denied | Denied |
| `git -C <path> ...` | `git -C /tmp/x reset --hard` | **Bypassed** — regex required `git` immediately followed by whitespace+subcommand | Fixed — gap-tolerant matching between `git` and subcommand |
| Chained `; && \|\|` | `echo hi && git push --force origin main` | Denied | Denied |
| Multiline / backslash continuation | `git push \`↵`  --force origin main` | Denied by luck (unbounded force-flag check) | Denied deliberately — line continuations joined before matching |
| Python subprocess list literal | `subprocess.run(['git','push','--force',...])` | **Bypassed** — no whitespace between tokens (`'git','push'`) | Fixed — gap class now includes quote/comma punctuation |
| Node `child_process.execSync` | `execSync('git push --force origin main')` | Denied (string literal keeps real whitespace) | Denied |
| Alias/function defined **in the same command** | `alias gp='git push --force'; gp origin main` | Denied (literal text still present) | Denied |
| Deploy tool invocations | `vercel deploy --prod`, `terraform apply`, `kubectl apply` | Denied | Denied |
| Generic deploy scripts | `./scripts/deploy_production.sh`, `make deploy`, `sh deploy.sh --prod` | **Not covered at all** | Added, and **anchored to actual command position** (see false-positive note below) |
| `bash -c` wrapping a deploy command | `bash -c "vercel deploy --prod"` | N/A (pattern added anchored, which would have reopened this) | Denied — dedicated unwrap pass extracts the quoted payload and re-checks it |
| Credential file, relative/absolute path | `cat .env`, `cat /home/.../.env` | Denied | Denied |
| Credential file, `../` traversal | `cat ../../.env` | Denied | Denied |
| Credential file via **symlink** | `cat innocuous_name` → symlinks to `.env` | **Bypassed** — filename-text matching only | Fixed — resolves `cat`/`head`/`tail`/`less`/`more` path arguments with `os.path.realpath` and checks the resolved target |
| GitHub merge tool, synonym server names | `mcp__other_github_server__merge_pull_request` | **Not covered** — matcher was one exact tool name | **2026-08-15:** matcher **removed**. R0–R2 merge after required checks is fleet-autonomous (`docs/fleet-merge-policy.md`). GitHub required checks remain the backstop. |
| Gmail mutation tool name variants | `mcp__claude_ai_Gmail__update_label` | **Bypassed — this tool existed and was simply missing from the original deny list** | Fixed — added, plus defensive coverage for plausible future verbs (send/trash/archive/batch-delete/batch-modify) |
| PR body / commit message *describing* a dangerous command | `gh pr create --body "$(cat <<'EOF'\nBlocks git reset --hard\nEOF\n)"` | **Bypassed live in an actual session** — unanchored git-destructive patterns matched the literal phrase inside descriptive text, not just real invocations | Fixed — `_strip_non_executed_text` blanks text captured specifically as the value of `-m`/`--body`/`--title`/`--description`/`--message`/`-F`/`--body-file`, including the `$(cat <<'EOF' ... EOF)` shape this project's own commit/PR conventions use, before pattern scanning |
| Remote branch deletion, any branch (RULEBOOK B5 before 2.2.0) | `git push origin --delete old-feature` | Denied, along with an ordinary push: `git push -u origin HEAD:refs/heads/x` was a **false positive** (the `:<ref>` regex matched mid-refspec). `git push -d`, `+<refspec>`, `--mirror`, combined `-uf` and `gh api -X DELETE .../git/refs/heads/main` were **not covered** | **2026-10-23 (B5 narrowed, D-0005):** one top-level command may delete one valid, non-protected `refs/heads/<branch>`; everything else is denied (see section below) |
| Protected / release / tag names | `git push origin :main`, `--delete release/1.4`, `--delete refs/tags/v1.2.0`, `--delete mytag` | Denied (all deletes were) | Denied: deletions must name `refs/heads/<branch>` (a bare name can resolve to a tag); protected names (`main`, `master`, `HEAD`, `trunk`, `develop`, `gh-pages`, `release*`) case-insensitive; `gh release delete --cleanup-tag` |
| Bulk, wrapped or unreadable deletes | `xargs -I BR git push origin --delete BR`, `parallel`, `find -exec`, `eval`, `bash -c`, loops, `--delete "$B"`, `'feature-*'`, two deletes chained | Denied (all deletes were) | Denied. **Review round 1 found `xargs -I BR` (a non-brace placeholder) allowed by the first B5 revision, a regression from main**: deletions now count only as the statement's own top-level `git push` / `gh api` / `curl`, one literal name per command |
| Force, mirror and prune shapes | `git push origin +feature-x`, `-uf`, `--mirror`, `--prune`, and git's accepted long-option prefixes `--mirr`, `--pru`, `--del`, `--al` | **Allowed** (prefixes allowed in the first B5 revision too) | Denied: every `git push` long option is resolved to its full name first; an ambiguous or unknown one is denied |
| REST and GraphQL ref writes | `curl -sX DELETE .../heads/main`, `gh api -iX DELETE`, `--req DELETE`, `-X DEL\ETE`, `.../heads/x/../../tags/v1`, `git//refs`, `%6Dain`, `PATCH ... force=true`, GraphQL `deleteRef`/`updateRef` | **Allowed** (combined `-sX` and dot segments also passed the first B5 revision) | Quote-aware tokens (shlex), one URL-decode; any non-GET method on `git/refs` other than one top-level branch DELETE is denied, as is a method or path the hook cannot read; names must pass `git check-ref-format` rules with no `.`/`..`/empty segments or `%`. GraphQL ref, branch-protection and ruleset mutations and `query=@file` are denied |
| Config-driven pushes | `git -c remote.origin.push=:refs/heads/release/9 push origin`, `-c remote.origin.mirror=true`, `git config remote.origin.mirror true`, `GIT_CONFIG_KEY_0=remote.origin.push`, `git remote add --mirror=push` | **Allowed** (a regression in the first B5 revision: main's `:<ref>` regex had caught the `-c` form) | Denied: setting `remote.<name>.push` or `.mirror` by any of these routes |
| Backstops B5 relies on | `gh api -X DELETE .../rulesets/1`, `PUT .../branches/main/protection/...`, `POST .../branches/main/rename`, GraphQL `deleteBranchProtectionRule` | **Allowed** | Denied: any write to rulesets, branch protection or branch renames |
| gh shortcuts | `gh pr merge --admin`, `gh pr close --delete-branch` | **Allowed** | Denied: `--admin` (B1); `pr close --delete-branch` deletes a branch the hook cannot name |
| Line continuation | `git pu\`↵`sh origin --delete ...` | Continuation replaced by a space, so `git pu sh` hid the push | Removed as bash does (an unescaped backslash-newline vanishes) |

## A false positive found and fixed along the way (two rounds)

**Round 1**: Anchoring the new deploy-script patterns naively (matching
"make" + anything + "deploy" anywhere in the command) **denied a harmless
commit message**: `git commit -m "about to make a deploy plan"`. Fixed by
anchoring deploy/credential patterns to an actual statement-start position
(with tolerated `sudo`/`env`/`command`/`exec` prefixes) instead of searching
free-floating text — see `ANCHOR` in `guard_bash.py`.

**Round 2** (found live, in a real session, not just adversarial testing):
git-destructive patterns (`push --force`, `reset --hard`, etc.) were
deliberately left unanchored — false negatives there are worse than a rare
false positive — but this bit a genuine case: a `gh pr create --body
"$(cat <<'EOF' ... EOF)"` call whose body *described* the hook's own
blocking rules, including the literal phrase `git reset --hard`, got denied
even though nothing would execute. Blanket-stripping all heredocs or all
quoted strings would reopen a real bypass (`bash -c "$(cat <<'EOF'\ngit
reset --hard\nEOF\n)"` must still be caught). The fix is deliberately
narrow: only text captured as the value of a flag whose *entire purpose* is
free-form human text (`-m`, `--body`, `--title`, `--description`,
`--message`, `-F`, `--body-file`) is blanked before scanning — never a flag
that could carry a path, ref, or nested command, and never a bare heredoc
with no such flag in front of it. `test_guard_bash.py` has explicit
regression cases for both directions: descriptive text in those flags is
allowed, and a real dangerous command adjacent to (or disguised inside) one
of those flags is still denied.

**Known residual gap**: this fix only covers the *named* descriptive flags
above. A dangerous-looking phrase embedded in an unrelated heredoc (e.g.
piped to `python3 -` as a string literal, never executed as shell) can
still be falsely denied — accepted as a rare, safe-direction false positive
rather than attempting full shell parsing (see "not a sandbox," above).

## Remote branch deletion (RULEBOOK B5, 2.2.0)

B5 lets an agent delete a stale remote branch when it is not the default, protected,
`release/*` or a tag ref, has no open PR, and its tip is a merged or closed PR head or already
in the default branch (`governance/DECISIONS.md` D-0005). The hook enforces only the part it
can read in the command text:

- **Allowed:** one branch per command, as the statement's own top-level command, in exactly the
  rulebook's forms: `git push <remote> --delete refs/heads/<branch>`, `-d refs/heads/<branch>`,
  `:refs/heads/<branch>`, or `DELETE .../git/refs/heads/<branch>` via `gh api` or `curl`. The
  name must pass `git check-ref-format` rules and not be protected. `gh pr merge
  --delete-branch` is untouched.
- **Denied:** bare names (they can resolve to tags), tags and non-branch refs, protected and
  release names, invalid names, globs, variables, substitution and percent-encoding in names,
  deletions through xargs, parallel, find -exec, eval, `bash -c`, loops or other HTTP tools,
  more than one deletion, abbreviated/ambiguous/unknown `git push` long options, `--mirror`,
  `--prune`, `+<refspec>`, `--force*`, short flags containing `f`, `remote.<name>.push` or
  `.mirror` config writes, REST ref create/update/force, unreadable REST methods or paths,
  rulesets/branch-protection/rename writes, GraphQL ref, protection and ruleset mutations,
  `gh pr close --delete-branch`, `gh release delete --cleanup-tag` and `gh pr merge --admin`.
- **Not checkable here, so B5 makes it the agent's duty:** open PRs, whether the tip is a
  merged or closed PR head or an ancestor of the default branch, and recording the name and
  tip SHA in the session checkpoint.

## What hooks reliably prevent

- Direct, ordinary invocations of the listed destructive Git operations,
  including through common wrapping (`bash -c`, `env`, `command`, `git -C`,
  chaining, multiline).
- Deleting a protected, release or tag ref, or more than one remote branch, in one
  ordinary command (`git push --delete`, `:<ref>`, REST `DELETE .../git/refs/...`).
- Ordinary attempts to read a credential-shaped file by name, including via
  a symlink or relative-path traversal.
- Any call to the exact-named (or now wildcard-matched) merge/Gmail-mutation
  MCP tools, regardless of arguments.

## What hooks cannot reliably prevent (by construction — no sandbox)

- **Encoded/obfuscated payloads**: `echo <base64> | base64 -d | bash`,
  hex-encoded strings, string concatenation built from variables not present
  as literal text in the command (`F="--for""ce"; git push $F origin main`).
  Verified: an encoded force-push is **not** caught. This requires either
  execution-time interception (a real sandbox) or refusing to run
  fully-opaque piped-decode-execute patterns categorically, which would
  also block many legitimate uses of `base64 -d`.
- **Cross-invocation indirection**: an alias or shell function defined in a
  *previous*, separate Bash tool call, then invoked by a short name in a
  later call the hook has no memory of. The hook is stateless per
  invocation by design (matches the Claude Code hook contract).
- **Semantically-equivalent tools/scripts with unrelated names**: a wrapper
  script called `./ship.sh` that internally force-pushes has no textual
  signal for us to key on. Only names/patterns we've actually enumerated are
  covered.
- **A determined, knowledgeable adversary operating outside instructions**:
  these hooks assume the agent is *trying* to follow `CLAUDE.md` and might
  slip via an unusual command shape — not that it's actively adversarial.
  Nothing here stops an agent explicitly instructed (e.g. via a successful
  prompt injection) to hand-craft an evasion once it knows the patterns
  above.
- **Branch history and PR state** (B5): the hook reads names, not commits. It cannot tell a
  merged branch from one with unpreserved work, see open PRs, or know a repo's ruleset-protected
  names beyond the fixed list. Not caught: git invoked through a variable or an alias defined
  in the same or an earlier call (`g=git; $g push ...`), deletions inside script files, a REST
  POST whose path is in a variable, and `.git/config` edited by other means. Rulesets and the
  agent's B5 checks cover these.
- **Non-Bash mutation paths entirely**: any MCP tool not covered by a
  PreToolUse matcher is unaffected by these hooks. New tools/integrations
  added later are not automatically covered — matcher lists need updating
  when the tool surface changes.

## Must rely on external controls, not this hook

- **GitHub branch protection** on `main`/`master` for AllTrue and Sunrise —
  the authoritative backstop against a merge or force-push actually landing,
  independent of whether our local hook fired.
- **GitHub required status checks / required reviews** for actually
  preventing a bad merge, not just an agent's local `merge_pull_request`
  call being denied.
- **Production platform permissions** (Vercel/Supabase project roles, the
  Raspberry Pi deploy path's own auth) as the real control on who/what can
  deploy — this hook only stops the *agent* from casually invoking a deploy
  command locally, not a compromised or misconfigured CI job.
- **Credential rotation/revocation itself** happening at the provider
  (GitHub/Laravel/Telegram/etc.), never something a local text hook can
  verify or enforce.

## Operational caveat found during this test pass

Live end-to-end firing (an actual Bash tool call in a running session being
blocked by the wired hook) was **not** confirmed in this session: a test
`git clean -fd` in a throwaway repo executed instead of being blocked, which
matches Claude Code's documented behavior — the settings/hook file watcher
only observes `.claude/` directories that existed when the session started,
so a `settings.json` created mid-session (as ours was) does not take effect
until the session is restarted or `/hooks` is opened once to reload config.
**Action needed**: open `/hooks` or start a fresh session in
`portfolio-ops`, then re-run the live proof (a safe `git clean -fd` in a
throwaway repo with a dummy file, confirming the file survives) before
trusting these hooks operationally.

## Regression testing

`.claude/hooks/test_guard_bash.py` is the permanent regression suite. Run it
after any edit to `guard_bash.py`:

```bash
python3 .claude/hooks/test_guard_bash.py
```
