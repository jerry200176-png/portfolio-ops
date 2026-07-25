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

## Why these are safe to trust

Before wiring them into `settings.json`, both scripts were:

1. Pipe-tested standalone against synthetic stdin (safe commands: `git
   status/log/diff/fetch`, `ls`, `find`, `cat` of ordinary files, `gh issue
   list`, `npm test/lint/build`, `git push` to a non-main branch, `git
   branch -a` — all confirmed to produce no output, i.e. allowed; unsafe
   commands — force push, `reset --hard`, `git clean -fd`, force branch
   delete, remote delete-push, each deploy-tool pattern, `.env`/`.pem`
   reads, credential exfil via curl — all confirmed denied with a clear
   reason).
2. Tested against a real throwaway Git repository (created under the
   session scratchpad, deleted after): confirmed `git commit` is denied on
   an **unborn** `main` branch (no commits yet) and on a **committed**
   `main` branch, and allowed on a feature branch — the branch check uses
   `git symbolic-ref`/`rev-parse` against the actual repository state, not
   a string match on the command.
3. Confirmed `~/.claude/settings.json` (the pre-existing global config with
   real user settings — `bypassPermissions`, enabled plugins, etc.) parses
   as valid JSON and is byte-for-byte unchanged after this install.

## Known limitations (be aware, don't over-trust)

- Pattern matching on shell command strings can be evaded by a sufficiently
  unusual invocation (e.g. an aliased command, a script that internally
  shells out to `git push --force`). This is a guardrail against ordinary
  mistakes and casual attempts, not a sandbox — the real backstop is
  `CLAUDE.md`'s rules plus agents not being *instructed* to do these things.
- The credential-leak guard only recognizes a few common filename shapes.
  It will not catch a renamed secrets file or a secret embedded inline in a
  command argument.
- `merge_pull_request`/Gmail-mutation denial is by tool name, so it holds
  regardless of arguments — but any *new* MCP server/tool added later isn't
  covered until added to the matcher.

## Testing changes to these hooks

Re-run the standalone pipe tests before trusting an edit:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"git status"}}' | python3 guard_bash.py   # expect: no output
echo '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"}}' | python3 guard_bash.py  # expect: deny JSON
echo '{"tool_name":"mcp__plugin_github_github__merge_pull_request","tool_input":{}}' | python3 deny_tool.py  # expect: deny JSON
```
