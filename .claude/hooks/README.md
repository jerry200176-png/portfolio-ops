# Hooks

Two PreToolUse hook scripts, wired in `../settings.json` (project-level —
`~/.claude/settings.json` was never touched; verified still valid/unchanged
after this install).

- `guard_bash.py` — matcher `Bash`. Denies: direct `git commit` on
  `main`/`master` (checked against the real current branch, not guessed),
  force push, `git reset --hard`, `git clean -f*/-d*`, force branch delete,
  remote branch/ref deletion, common production deploy/migration command
  shapes (`vercel --prod`, `terraform apply`, `supabase db push`, `prisma
  migrate deploy`, `kubectl apply`, `gh workflow run *deploy*`, `npm/yarn/
  pnpm run deploy`), and commands that dump a credential-shaped file
  (`.env`, `*.pem`, `id_rsa`, `credentials.json`) to stdout or toward an
  external host via curl/scp/rsync.
- `deny_tool.py` — matcher on Gmail **trash/delete/spam** MCP tool names,
  in both naming schemes: local (`mcp__claude_ai_Gmail__*`) and cloud
  (`mcp__Gmail__*`). Two redundant entries: a regex over any server name
  containing "gmail" and any tool containing `trash`/`delete`/`spam`, plus an
  exact-name list (the plain `a|b` form Claude Code never reads as regex).
  `permissions.deny` repeats the core trash/delete names as a third layer.
  Send, reply, draft, and label are allowed (`governance/AUTONOMY_POLICY.md`).
  Regression test: `python -m unittest tests.test_gmail_deny_hook`.
  GitHub merge is allowed after required checks; do not hook-deny it.

No `jq` on this machine, so both hooks are plain Python 3 reading/writing
the hook JSON protocol directly (stdlib only, no dependencies).

`.claude/settings.json` also carries a `permissions.deny` block for the
handful of most-literal destructive patterns (`git push --force`, `git
reset --hard`, etc.) as a complementary hard layer — per Claude Code's own
guidance, Bash pattern-matching in hooks is best-effort and can fail open
on ambiguous parsing, while the native permission system is a harder
allow/deny. `guard_bash.py` stays as the deeper, adversarially-tested layer
(symlink resolution, `git -C` tolerance, wrapper unwrapping) that a simple
glob can't do — the two are deliberately redundant on the simplest cases,
not a replacement of one by the other.

## Full detail and known limitations

`../../docs/hook-threat-model.md` is the maintained, up-to-date source for
adversarial test results, confirmed bypasses that were fixed, false
positives found and fixed, and what remains unfixable by a textual hook —
don't duplicate that narrative here; it drifts. The current regression
count is in `test_guard_bash.py`'s own output (`python3
test_guard_bash.py`).

## Testing changes to these hooks

Re-run the full regression suite before trusting an edit:

```bash
python3 test_guard_bash.py
```

Or pipe-test a single case directly:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"git status"}}' | python3 guard_bash.py   # expect: no output
echo '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"}}' | python3 guard_bash.py  # expect: deny JSON
echo '{"tool_name":"mcp__Gmail__trash_message","tool_input":{}}' | python3 deny_tool.py  # expect: deny JSON (deny_tool denies whatever settings.json routes to it)
```

## Portability (Cloud / alternate checkouts)

Hook commands in `../settings.json` must **not** hardcode
an absolute checkout path such as `$HOME/workspace/portfolio-ops/...`
(the legacy local layout) — cloud sessions clone elsewhere.

They use:

```bash
python3 "${CLAUDE_PROJECT_DIR:-.}/.claude/hooks/guard_bash.py"
```

- If Claude Code sets `CLAUDE_PROJECT_DIR`, that absolute project root is used.
- Otherwise `.` (project cwd) is used — Claude Code project hooks run with the
  repository root as the working directory.

**Last verified portable form:** 2026-07-27 (Jerry GitHub Operator).
After merging this change, reload hooks (`/hooks` or new session) before
trusting live blocking.
