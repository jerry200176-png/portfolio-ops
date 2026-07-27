# Security Policy — portfolio-ops

**Last reviewed:** 2026-07-27  
**Owner:** Founder (`@jerry200176-png`)  
**Scope:** This repository is a **control plane** (docs, triage state, governance). It does not host product runtime secrets or production deploy credentials.

## Reporting a vulnerability

Use **one** of these channels (monitored by Founder):

1. **GitHub private vulnerability report** on this repository:  
   `https://github.com/jerry200176-png/portfolio-ops/security/advisories/new`  
   (preferred for control-plane issues that should stay private)
2. **Direct GitHub mention / private message to Founder** `@jerry200176-png` for urgent credential exposure.

Do **not** open a public Issue for credential leaks or App private-key exposure.

### Product (AllTrue / Sunrise) security
- Report against the product repo `SECURITY.md` — not here:
  - `jerry200176-png/AllTrue_System`
  - `jerry200176-png/sunrise-cafe`

### Control-plane credential exposure
If an App private key, installation token, or founder orchestrator API key is exposed: **rotate immediately**, then notify Founder via the channels above. Do not commit secret values into audit docs (names only).

## Non-goals
- This repo must not store production `.env`, SSH keys, or raw secret values in git.
- Audit reports may list secret **names** only.
- No public security@ email is published for this control plane (avoids an unmonitored mailbox).

## Related
- `governance/AUTONOMY_POLICY.md`
- `docs/security-boundaries.md`
- `docs/github-governance/PERMISSION_GAPS.md` (Operator App read gaps)
