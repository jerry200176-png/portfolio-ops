# Company baseline — 2026-07-19

## Portfolio

- AllTrue canonical main: `49baef28`; clean against `origin/main` at inspection time.
- Sunrise canonical main: `d03313a`; clean against `origin/main` at inspection time.
- Both GitHub repositories are public and the authenticated account has administrative permissions.
- GitHub connector reads succeed; connector writes fail with HTTP 403. Authenticated `gh` CLI is the proven write path.

## P0/P1 facts

- Four GitGuardian alerts dated 2026-07-17 identify a Telegram token, Laravel `APP_KEY`, and bearer credentials in published AllTrue history.
- AllTrue issue #1007 is the canonical P0 incident. Founder autonomous authorization was recorded through `gh` after the connector write failed.
- Current AllTrue open PR #1324 addresses production bug-queue SSH host-key handling.
- Sunrise has recent Vercel production-deployment failures and an open non-mergeable grouped dependency PR #235 containing several major-version upgrades.
- GitHub reported 100% consumption of included Actions minutes, threatening both products' CI and governed deployment paths.

## Gmail baseline

- Account: `jerry200176@gmail.com`
- Inbox: 16,913 messages; 12,848 unread at inspection time.
- Recent high-signal mail: GitGuardian secret alerts, GitHub Actions capacity exhaustion, CI failures, Vercel failed production deployments, and Sentry SQL errors.
- Most remaining unread volume appears to be GitHub notifications, promotions, newsletters, and transactional mail; cleanup must be staged and reversible.

## Immediate operating decision

Stop unrelated roadmap delivery until live credential containment is verified. Sunrise deployment diagnosis may proceed read-only in parallel. Do not merge the grouped dependency PR until majors are split and individually verified.
