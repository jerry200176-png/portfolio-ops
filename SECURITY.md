# Security Policy

## Reporting

Do not open a public issue for a suspected credential leak, privacy exposure,
authentication bypass, production-data issue, or other active vulnerability.
Report it privately to the repository owner through the repository's private
security reporting channel.

Do not include secret values in reports. Preserve only the minimum evidence
needed to reproduce and verify the finding.

## Response boundaries

Investigation and evidence capture may proceed read-only. Credential rotation,
production containment, deployment, permission changes, and data mutation
require explicit Founder approval. See `CLAUDE.md` and
`governance/AUTONOMY_POLICY.md`.

Supported versions are the current default branch and the latest released
governance baseline. Security fixes are documented with evidence and rollback
instructions.
