# Production status evidence in the weekly report

Goal: make the scheduled portfolio report preserve read-only production identity
evidence even when the committed inventory is stale.

1. Extend the existing production identity probe with structured JSON and
   explicit observed/unknown delivery states; retain its current CLI behavior.
2. Run that probe in the existing weekly workflow and upload both reports even
   when freshness fails.
3. Test identity, health failure, missing identity, and inventory mismatch with
   fixture responses. Run focused and repository checks.

Risk: R1, read-only reporting and CI workflow. No production mutation or
portfolio timestamp update. Rollback: revert this PR. Stop before merge for
independent review and required GitHub checks.
