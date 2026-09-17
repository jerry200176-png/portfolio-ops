# External CLI worker handoff (provider-neutral)

## Goal

Prove disposable independent CLI worker handoff without chat dependence:

`Run/Attempt → ExternalCliWorkerAdapter → subprocess → WorkerResult → canonical ingest`

## Domain vs runtime

| Layer | Value |
|-------|--------|
| Domain `worker_type` | `external_cli` |
| Observational `provider_id` | `stub` (tests/dogfood) or `cursor` / `cursor_agent` (optional) |
| Not in Goal contracts | cursor, codex, model names |

## Reuse

- `WorkerResult` / `ProposedOutcome` / `Attempt` / leases / fencing / ingest
- `prompt_compiler`, `GraphHarness.step`
- Existing Codex adapter remains; this adds a provider-neutral path while Codex quota is blocked

## Commands

```bash
PYTHONPATH=. python3 -m unittest tests.test_external_cli_handoff -v
PYTHONPATH=. python3 scripts/graph-external-cli-dogfood.py
python3 -m agent_graph.cli step RUN_ID --external-cli-worker --external-cli-provider stub --db PATH
```

Scheduler runtime selection (optional, dogfood only):

`GRAPH_WORKER_PROVIDER=stub|cursor`

## Failure proofs (tests)

- Crash before `result.json` → state_version unchanged; Founder not required
- Concurrent lease with live prior worker → second attempt rejected
- Independent PID ≠ harness PID

## Non-scope

- Enabling `graph-scheduler.service`
- Production Restate
- GitHub App permission changes
- Multi-provider SDK/framework
