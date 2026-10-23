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
.claude/hooks/test_guard_bash.py`) — 219 dangerous cases, 53 safe cases, plus
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
| Remote branch deletion via the shell (RULEBOOK B5) | `git push origin --delete old-feature`, `gh api -X DELETE .../git/refs/heads/x` | Main denied `git push --delete` and `:<ref>` (with a false positive on `git push origin HEAD:refs/heads/x`), but **missed** `git push -d`, `gh api`/`curl` DELETE and the shapes below | **2026-10-23 (D-0005):** every shell-level deletion is denied; the only path besides `gh pr merge --delete-branch` is `python3 scripts/delete-merged-branch.py --repo <o>/<n> --branch <b>`, allowed only as the whole command (section below) |
| Hook-approved deletions (first two revisions of PR #144) | `git push --del`, `xargs -I BR git push origin --delete BR`, `--delete refs/heads/ok '#' refs/heads/main`, `curl -X DELETE ".../heads/m[a-a]in"`, `".../heads/old;anything/../main"`, multi-line `bash -c`/`for` wrappers, `git config -- remote.origin.push :refs/heads/main --get` | **Bypassed** in review: 4 P1 (fresh-context reviewer) + 5 P1 (Codex), each a shell, curl or git parsing quirk | Fixed by design: the hook never approves a deletion it parsed. All are regression cases and are denied wholesale |
| Force, mirror and prune shapes | `git push origin +feature-x`, `-uf`, `--mirror`, `--prune`, prefixes `--mirr`, `--pru`, `--del`, `--f` | **Allowed** except `--force`/`-f` | Denied: any long option that is a prefix of `--delete`, `--mirror`, `--prune` or `--force*`; short flags with `d` or `f`; `:`/`+` refspecs, `$VAR:` sources, `$@`, brace/glob expansion and `$'...'` after a `push` word, quoted or not, in any wrapper |
| REST and GraphQL ref writes | `curl -sX DELETE .../heads/main`, `gh api -iX DELETE`, `--req DELETE`, `-X DEL\ETE`, `.../issues/1/../../git/refs/...`, `g%2569t`, `PATCH ... force=true`, `POST .../git/refs`, GraphQL `deleteRef`/`updateRef` | **Allowed** | Denied: any write (explicit, abbreviated or combined method flag, or a body flag of that client) to a target with a `git`, `refs`, `matching-refs` or `rulesets` segment, a dot segment, curl glob syntax or a variable, after full percent-decoding; GraphQL ref, protection and ruleset mutations and queries read from files. Reads stay allowed (`curl -f` is `--fail`) |
| Config-driven pushes | `git -c remote.origin.push=:refs/heads/main push`, `-c remote.origin.mirror=true`, `git config -- remote.origin.push ... --get`, `-c alias.p=push`, `-c include.path=...`, `GIT_CONFIG_*`, `git remote add --mirror=push` | **Allowed** (except the `-c ...push=:` form) | Denied: any statement naming `remote.<n>.push`/`.mirror`, `include.path` or a git alias unless it is exactly `git config --get[-all] <key>`; `GIT_CONFIG*` assignments; push mirrors |
| Backstops B5 relies on | `gh api -X DELETE .../rulesets/1`, `PUT .../branches/main/protection/...`, `POST .../branches/main/rename`, GraphQL `deleteBranchProtectionRule` | **Allowed** | Denied: any write to rulesets, branch protection or branch renames |
| gh shortcuts | `gh pr merge --admin`, `gh pr close --delete-branch`, `gh release delete --cleanup-tag` | **Allowed** | Denied |
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

The hook denies every shell-level remote branch or tag deletion and ref write, as strictly as
before B5 2.2.0 or more (`governance/DECISIONS.md` D-0005). Two earlier revisions of PR #144 let
the hook approve a parsed `git push --delete` or REST DELETE; review found 9 P1 bypasses, each a
case where the hook's reading of the command differed from what shell, curl or git would do. A
text hook cannot close that class, so it never approves a deletion it parsed:

- **Allowed:** `gh pr merge --delete-branch`, and `python3 scripts/delete-merged-branch.py
  --repo <owner>/<name> --branch <name>` (optionally `--dry-run`) as the *whole* command, with
  both values matching fixed regexes (no quotes, metacharacters, globs or `..`). Any other
  command naming the script with `--repo`/`--branch` (wrapped, chained, quoted, looped,
  reordered, `--repo=`, another path) is denied.
- **The script decides through the GitHub API**, not the shell: forks are refused (upstream
  PRs are not visible from them); then default branch, protection,
  ruleset `deletion`/`update` rules, open PRs (head or base), and whether the tip is a merged
  or closed PR head or already in the default branch. It re-reads the tip before deleting and
  prints the name and tip SHA for the checkpoint (`tests/test_delete_merged_branch.py`).
- **Strictness costs:** deletion-looking arguments after any `push` word are denied even in
  harmless contexts (`echo push --delete`), and a REST write whose target path holds a variable
  (`gh api -X POST "repos/o/r/issues/$N/comments"`) is denied; name write paths literally.
- **curl and gh are parsed per client:** short clusters split per letter with attached
  values (`-d'{...}'`, `-sXPOST`, `-Fname=@f`), unambiguous long prefixes, `-G`/`--get` keeps
  `-d` a read, `-T` is a PUT. GraphQL bodies read from a file, stdin or a variable are denied
  for curl and gh. The `git stash push` exemption applies only after `git [global options]
  stash`, so `git -C /tmp/stash push ...` is checked.
- **Review stop rule (from 2026-10-23):** shell-text matching cannot be complete. Protection of
  `main`, release branches and tags rests on GitHub rulesets (platform-enforced for every token)
  plus restorable branches. Reviewer findings that `main`'s hook also allows (not introduced or
  widened by this PR) go to a follow-up issue instead of blocking; findings in new code (the
  deletion script, new exemptions, new allowlists) are always fixed.
- **Recommended complement:** GitHub's "Automatically delete head branches" setting removes the
  head branch at merge; it is a Founder settings change per repo.

## What hooks reliably prevent

- Direct, ordinary invocations of the listed destructive Git operations,
  including through common wrapping (`bash -c`, `env`, `command`, `git -C`,
  chaining, multiline).
- Ordinary shell-level remote branch or tag deletion and ref writes (`git push --delete`,
  `:<ref>`, `+<ref>`, REST or GraphQL ref writes, config-driven push refspecs); the only
  deletion path is the verified `scripts/delete-merged-branch.py` command.
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
- **Branch deletion through other means** (B5): git invoked through an alias or function
  defined in an earlier tool call, deletions inside script files or other languages, and
  `.git/config` edited by other means are not seen. The deletion script's own checks, rulesets
  and review cover these.
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
