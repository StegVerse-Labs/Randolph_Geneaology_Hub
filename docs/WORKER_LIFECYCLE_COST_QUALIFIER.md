# The task's resource cost determines the worker lifecycle

Measured: 2026-09-23 against `StegVerse-Labs/.github`.
Re-run with `tools/qualify_worker_lifecycles.py`.

## The chain

```
task  ->  estimated resource cost  ->  worker lifecycle
```

This is not billing. Billing is what a provider charges, and billing data answers it. The
cost that determines a worker lifecycle is the **resource cost of the task assigned**, and
the lifecycle is what governance and record keeping bind to: the expiry is the window in
which a worker may act, and therefore the window its receipts cover.

## The model already exists, and it is correct

`SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001` states the invariant:

```
WORKER_LIFETIME_IS_DERIVED_PER_INTENDED_TASK_NOT_GLOBALLY_FIXED
```

and gives the derivation as five resource-cost components that sum to the lifetime:

```
expected_task_execution           6
known_delay                       4
inferred_unknown_delay_reserve    8
records_decomposition             7
safety_reserve                    5
                               = 30 seconds
```

Production requires `recompute_per_task`, `cost_analysis_required`, every component, and
`budget_extension_requires_new_governed_recalculation`. The SDK's
`purpose_bound_worker_cost_demo._sum_budget` already sums exactly these five.

**So the formula is not missing, and nothing here invents one.**

## What is missing is the input

The estimate belongs on the task. Measured across all 163 canonical task records:

| | |
|---|---|
| lifetime derivable from the task's resource cost | **1 of 163** |
| task states no resource cost estimate | **162 of 163** |
| estimate incomplete | 0 |
| claimed lifetime disagreeing with its components | 0 |

The one task that derives a lifetime is `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001` —
the task whose purpose is to prove the model. It derives 30s from the components above.

Every other task assigns work whose worker lifetime nothing derives.

### The corpus is disconnected from the other side too

`cost-basis/worker-runtime/` holds 61 records keyed by `task_class`. Only **5 of 61**
resolve to a canonical task id, and only **1 of 163** tasks carries a `cost_basis_ref`.
That one reference exists because it was repaired: the same task record names the defect
as

```
DANGLING_COST_BASIS_REF_CAUSED_EXPIRY_BASIS_UNAVAILABLE
```

A dangling cost-basis reference left the expiry basis unavailable. The repair pointed it at
a real record. The other 162 tasks were never wired up at all.

## What this costs governance

When a task states no resource cost:

- **No lifetime can be derived**, so any lifetime a worker gets is either defaulted or
  assigned — and a defaulted lifetime is precisely the globally-fixed lifetime the
  invariant forbids.
- **The record cannot be validated.** There is no estimate to check a lifetime against, so
  a correct expiry and a wrong one are indistinguishable in review.
- **Drift is undetectable.** If the work a task does changes, nothing says its worker's
  lifetime should change with it, so it will not.

Independent evidence that this is real rather than theoretical: among the 48 cost-basis
records carrying both a cost and a heartbeat estimate, two pairs hold byte-identical cost
inputs while granting expiries **64x** and **93x** apart. Identical cost, different
lifetime — which cannot happen where the lifetime is derived.

## What the qualifier does

`sdk-staging/stegverse/worker_lifecycle_qualifier.py` derives the lifetime from the task's
estimated resource cost, using the canonical five components, and returns:

```
DERIVED_FROM_TASK_RESOURCE_COST             all five components present; lifetime is their sum
TASK_STATES_NO_RESOURCE_COST_ESTIMATE       nothing to derive from
RESOURCE_COST_ESTIMATE_INCOMPLETE           the model requires every component
CLAIMED_LIFETIME_DISAGREES_WITH_ITS_COMPONENTS   a stated lifetime that its own numbers contradict
```

It never defaults a lifetime when the estimate is absent. Returning a number there would
manufacture the fixed lifetime the invariant exists to forbid, and would hide the finding
rather than report it.

## Re-running

```bash
python3 tools/qualify_worker_lifecycles.py \
  --task-records-root /home/user/stegverse-labs/.github/data/canonical-task-records \
  --json data/cost-basis/worker-lifecycle-derivability.json
```

Exit `0` when every task derives a lifetime, `3` when any cannot, `2` when the corpus is
absent. It exits `3` today.

The survey and the SDK demonstration run **the same qualifier module**, so they cannot
diverge.

Resource cost estimates are located by searching each record for the five components
together, rather than at a fixed path, because no convention has settled — the one task
that carries an estimate holds it under `lifetime_model.demonstration.components_seconds`.
A stricter reader would report every other task as mis-shaped rather than estimateless,
overstating the problem.

## Not claimed

No lifetime is asserted wrong, and none is changed. No component value is proposed for any
task. Deciding what a given task's expected execution, delay, reserve, decomposition and
safety actually are is the estimate itself, and that is the work this measurement says is
missing — not work this measurement performs.

`docs/ACTIONS_COST_BASIS.md` measures GitHub Actions billing. It is a different axis and is
scoped as such; it does not bear on worker lifecycle.
