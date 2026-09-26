# Worker lifetime estimates — proposal

Recorded 2026-09-26. Regenerate with `python3 tools/propose_worker_lifetime_estimates.py`.

`data/cost-basis/worker-lifetime-estimate-proposal.json` is the machine-readable form.
This grants nothing: no registration, no lifetime set, `authority_effect: NONE_PROPOSAL_ONLY`.

## The correction this makes

`data/cost-basis/worker-lifecycle-derivability.json` reported **1 of 163** canonical tasks
able to derive a worker lifetime. That number was an artefact of the matching, not the
evidence: cost-basis records were matched to tasks by `task_class`, which almost never
equals a canonical task id. Records also name tasks in `evidence_refs` as
`handoffs/<TASK-ID>.json`. Matching on that finds **six**.

## The anchor

`SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001` is the only task carrying both a canonical
`lifetime_model` and a cost-basis record, and the two agree:

```
cost-basis  hb_estimate.expected_completion_beats  = 30
canonical   lifetime_model derived_max_lifetime_seconds = 30
```

So `expected_completion_beats` is the derived maximum lifetime in seconds. A test asserts
this reproduces independently; if it ever stops holding, the proposal fails rather than
quietly proposing from a broken premise.

## What is proposed

| task | proposed lifetime | from |
|---|---|---|
| `GADI-RESIDENT-EXECUTION-001` | 1s | `gadi-resident-execution.json` |
| `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001` | 30s | `stegagents-governed-runtime.json` |
| `SHARED-DOCS-PROVIDER-FREEZE-INTEGRATION-001` | 1s | `shared-docs-provider-content-integrity.json` |
| `SHWP-DEVICE-KV-INTR-OBSERVATION-001` | 8s | `device-kv-intr-observation.json` |
| `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` | 8s | `device-kv-skap-roundtrip.json` |
| `SV-KV-AI-PERSISTENCE-001` | 1s | `kv-ai-memory-resident.json` |

## What is deliberately not proposed

**The five-component split.** One calibration point cannot determine five coefficients, and
that point has 15 evidence predicates, 0 dependencies, 0 blockers and 0 declared capabilities —
three of four structural signals at zero, so no per-signal coefficient is identifiable from it.
Filling in a plausible rule would be invention, and a test asserts no split is proposed.

Resolving it needs either a stated policy from the registry owners, or a second task carrying
both a component split and a cost basis.

## The actual bottleneck

**42 cost-basis records carry a usable
`expected_completion_beats` and name no canonical task.** The estimates already exist. What is
missing is the binding from record to task.

No further record binds under `task_class` normalisation — those values do not correspond to
canonical task ids by name, so the mapping has to be authored by whoever knows which task each
class serves. Every unbound record is listed in the artifact with its `task_class` and its
estimate, ready to be bound.

This is the same shape as the defects repaired in Site #1463, #1465, #1466 and #1467: the
evidence moved, and the thing that would point at it did not follow.

## Where it stands

| | |
|---|---|
| canonical task records | 173 |
| deriving a lifetime today | 6 |
| estimates existing but unbound | 42 |
| tasks with no linked estimate | 167 |

## To act on it

1. Bind the unbound records: add the canonical task id to each record's `task_id`, or reference
   `handoffs/<TASK-ID>.json` in its `evidence_refs`. Re-run the tool; each newly bound record
   with an estimate becomes a proposed lifetime.
2. State the component-split policy, or point at a second calibrated task.
3. Apply accepted proposals to the canonical task records. That is a write to
   `StegVerse-Labs/.github`, which cannot be attached to a session — see
   `docs/BLOCKED_WORK_FOR_REVIEW.md` §1.

