#!/usr/bin/env bash
# Add a new project to the governed portfolio: one command, then open one PR in the target.
#   scripts/bootstrap-repo.sh <owner/repo> [--sha <40-hex portfolio-ops sha>] [--dry-run]
# Clones the target to a temp dir, writes AGENTS.md skeleton (only if absent), CLAUDE.md imports,
# vendored rulebook + lock, skills, PR template and the CI caller, pushes branch
# chore/governance-bootstrap, and registers the repo in portfolio.yaml (governance_sync: true).
# Never force-pushes; never writes to the default branch.
set -euo pipefail

usage() { sed -n 2,7p "$0" | sed 's/^# \{0,1\}//'; }
[[ $# -ge 1 && "$1" != -h && "$1" != --help ]] || { usage; exit 2; }
REPO="$1"; shift
SHA="$(git -C "$(dirname "$0")/.." rev-parse HEAD)"; DRY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --sha) SHA="$2"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    *) usage; exit 2 ;;
  esac
done
[[ "$REPO" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || { echo "bad repo: $REPO" >&2; exit 2; }
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || { echo "--sha must be a full 40-hex commit" >&2; exit 2; }

SRC="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${REPO##*/}"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
gh repo clone "$REPO" "$WORK/repo" -- --depth 1 >/dev/null
cd "$WORK/repo"
git checkout -q -b chore/governance-bootstrap

mkdir -p scripts governance .github/workflows .claude/skills/reference-first-design .claude/skills/product-design-doc
cp "$SRC/scripts/check-rulebook.py" scripts/check-rulebook.py
cp "$SRC/.claude/skills/reference-first-design/SKILL.md" .claude/skills/reference-first-design/SKILL.md
cp "$SRC/.claude/skills/product-design-doc/SKILL.md" .claude/skills/product-design-doc/SKILL.md
[[ -f .github/PULL_REQUEST_TEMPLATE.md ]] || cp "$SRC/governance/templates/pull_request_template.md" .github/PULL_REQUEST_TEMPLATE.md
[[ -f AGENTS.md ]] || sed "s#__NAME__#$NAME#" "$SRC/governance/templates/AGENTS.skeleton.md" > AGENTS.md
printf '@AGENTS.md\n@governance/RULEBOOK.md\n\n# Claude Code notes\n\n- The two imports above are the rules; this file adds only Claude-specific mechanics.\n' > CLAUDE.md
printf 'source_repo=jerry200176-png/portfolio-ops\nsource_ref=pending\nsha256=pending\n' > governance/RULEBOOK.lock
python3 scripts/check-rulebook.py --update "$SHA" || true
sed "s#__PORTFOLIO_OPS_SHA__#$SHA#" "$SRC/governance/templates/rulebook-check-caller.yml" > .github/workflows/rulebook.yml
git rm -q --ignore-unmatch .cursorrules codex.md

if ! grep -q "repo: $REPO" "$SRC/portfolio.yaml" 2>/dev/null && ! grep -q "github_repo: $REPO" "$SRC/portfolio.yaml"; then
  python3 - "$SRC/portfolio.yaml" "$REPO" "$NAME" <<'PY'
import sys
path, repo, name = sys.argv[1:]
text = open(path, encoding="utf-8").read().rstrip("\n")
marker = "\n\n# Governance profile"
entry = (f"\n  - id: {name}\n    name: {name}\n    local_path: /home/jerry/workspace/{name}\n"
         f"    github_repo: {repo}\n    governance_sync: true\n    note: added by scripts/bootstrap-repo.sh\n")
if marker in text:
    text = text.replace(marker, entry.rstrip("\n") + "\n" + marker, 1)
else:
    text += entry
open(path, "w", encoding="utf-8").write(text + "\n")
PY
  echo "registered $REPO in portfolio.yaml (commit it in a portfolio-ops PR)"
fi

git add -A
git status --short
if [[ $DRY -eq 1 ]]; then echo "dry-run: nothing committed or pushed"; exit 0; fi
git -c user.name=governance-bootstrap -c user.email=noreply@github.com commit -q -m "governance: bootstrap portfolio rulebook (portfolio-ops@${SHA:0:12})"
git push -q origin chore/governance-bootstrap
echo "pushed chore/governance-bootstrap; open the PR (REST): gh api repos/$REPO/pulls -X POST -f title='governance: bootstrap portfolio rulebook' -f head=chore/governance-bootstrap -f base=<default> -f body=..."
