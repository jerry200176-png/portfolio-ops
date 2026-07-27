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
- `deny_tool.py` — matcher on specific MCP tool names (`merge_pull_request`,
  and the Gmail mutation tools: create_draft, update_draft, label/unlabel
  message/thread, apply_sensitive_*_label, create_label, delete_label).
  Unconditional deny — those tools are never autonomous here, regardless of
  arguments.

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
echo '{"tool_name":"mcp__plugin_github_github__merge_pull_request","tool_input":{}}' | python3 deny_tool.py  # expect: deny JSON
```

## Portability (Cloud / alternate checkouts)

Hook commands in `../settings.json` must **not** hardcode
`/home/jerry/workspace/portfolio-ops/...`.

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
