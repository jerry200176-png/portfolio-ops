# Security Policy — portfolio-ops

**Last reviewed:** 2026-07-27  
**Owner:** Founder (jerry200176-png)  
**Scope:** This repository is a **control plane** (docs, triage state, governance). It does not host product runtime secrets or production deploy credentials.

## Reporting
- Do not file public security issues for AllTrue / Sunrise product vulnerabilities here.
- Product security: follow each product repo's `SECURITY.md` (AllTrue, Sunrise).
- Control-plane credential exposure (App private keys, founder tokens): rotate immediately; notify Founder offline.

## Non-goals
- This repo must not store production `.env`, SSH keys, or raw secret values in git.
- Audit reports may list secret **names** only.

## Related
- `governance/AUTONOMY_POLICY.md`
- `docs/security-boundaries.md`
- `docs/github-governance/PERMISSION_GAPS.md` (Operator App read gaps)
