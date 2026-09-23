# SDK staging — worker lifecycle qualifier

Two files destined for `StegVerse-org/StegVerse-SDK`, staged here because this session
cannot attach that repository: `add_repo` refuses a cross-tier add, since the session
already holds `stegverse-labs` sources. They are staged byte-identical to what the SDK
needs so the write there is a copy, not a re-authoring.

| staged here | drops into the SDK at |
|---|---|
| `stegverse/worker_lifecycle_qualifier.py` | `stegverse/worker_lifecycle_qualifier.py` |
| `tests/test_worker_lifecycle_qualifier.py` | `tests/test_worker_lifecycle_qualifier.py` |

## What it does

Derives a purpose-bound worker's lifetime from the **resource cost of the task assigned**:

```
task  ->  estimated resource cost  ->  worker lifecycle
```

The canonical model already states this. `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001`
gives the invariant `WORKER_LIFETIME_IS_DERIVED_PER_INTENDED_TASK_NOT_GLOBALLY_FIXED` and
the derivation as five components summing to the lifetime — the same five
`purpose_bound_worker_cost_demo._sum_budget` already sums. **This invents no formula.**

Four verdicts:

```
DERIVED_FROM_TASK_RESOURCE_COST                 all five components present; lifetime is their sum
TASK_STATES_NO_RESOURCE_COST_ESTIMATE           nothing to derive from
RESOURCE_COST_ESTIMATE_INCOMPLETE               the model requires every component
CLAIMED_LIFETIME_DISAGREES_WITH_ITS_COMPONENTS  a lifetime its own numbers contradict
```

It never defaults a lifetime when the estimate is absent. A default would be the
globally-fixed lifetime the invariant forbids.

## What it demonstrates

Against all 163 canonical task records:

| | |
|---|---|
| lifetime derivable from the task's resource cost | **1 of 163** |
| task states no resource cost estimate | **162 of 163** |

The one that derives is the task whose purpose is proving the model, yielding 30s from
`6 + 4 + 8 + 7 + 5`. The tests demonstrate that worked example, the estimateless condition
the other 162 are in, and that every component contributes.

## Verified against the real SDK

Both files were copied into a live `StegVerse-org/StegVerse-SDK` checkout and run there with
`python -m unittest`, which is how the SDK's CI runs tests: **10 tests, all pass.** The
checkout was restored afterwards.

`tools/qualify_worker_lifecycles.py` in this repository applies **this same module** to the
canonical corpus, so the SDK demonstration and the survey cannot diverge.

**Pre-existing and not mine:** the SDK's `tests/test_external_interlock_bootstrap.py` line 29
carries a literal `\n` in committed source and cannot be parsed, so that module never runs.
Same defect shape as the one repaired in Site PR #1456, in a third repository. The SDK's CI
runs `unittest` per module, so it does not surface there.

## Not claimed

No lifetime is asserted to be wrong and none is changed. No coefficient, ratio or bound is
proposed. The qualifier grants no authority, sets no lifetime, and promotes nothing.
