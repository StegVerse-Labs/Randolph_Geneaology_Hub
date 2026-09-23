# Worker cost analysis qualifies the lifecycle

Measured: 2026-09-23 against `StegVerse-Labs/.github/cost-basis/`.
Re-run with `tools/qualify_worker_lifecycles.py`.

## What worker cost analysis is for

It is not billing. Billing is what a provider charges, and that question is answered by
billing data.

Worker cost analysis is the factor that **determines the worker lifecycle**, and it is the
qualifier for establishing a *precise* lifecycle. That precision is what governance and
record keeping depend on: `expiry_candidate_beats` is the window in which a worker may act,
so it is also the window its receipts cover. A lifecycle nothing derives is a governance
bound nobody can check.

The canonical corpus already has the right shape. Each record carries cost factors and a
heartbeat estimate:

```
cost_estimate   compute_units, token_units, storage_bytes, network_bytes,
                operator_seconds, latency_ms, failure_recovery_units
hb_estimate     expected_completion_beats, expected_idle_beats,
                expiry_candidate_beats, confidence
```

`external_cost_usd` is one field of eight, and it is `0` in every record that carries it.
Money is incidental here. The substance is work and time.

## The finding: the lifecycle is assigned, not derived

Across the 48 records carrying both a cost estimate and a heartbeat estimate:

| | |
|---|---|
| qualified — expiry derived from stated cost | **1 of 48** |
| asserted — no derivation stated | **47 of 48** |
| unsatisfiable — expiry below expected work | 0 of 48 |

The floor holds everywhere: no worker is required to finish after it expires. That is the
one property the corpus gets right, and it is worth keeping.

But the ceiling is unexplained. Headroom — expiry over expected work — runs:

```
min 2.0x     median 12.8x     max 2666.7x
```

A worker may be granted twice the beats it needs, or two and a half thousand times, and no
record says why.

### Identical cost buys different lifetimes

The decisive evidence. Two pairs of records carry **byte-identical cost inputs** and grant
different expiries:

```
compute_units 1, storage_bytes 1048576, failure_recovery_units 1
   stegverse001-bounded-autonomy-runtime      64 beats
   stegagents-governed-runtime              4096 beats     64x

compute_units 4, storage_bytes 8388608, failure_recovery_units 2
   sv-dn1-repository-persistence-dispatch    256 beats
   tvc-repository-broker-validation        24000 beats     93x
```

If the cost estimate determined the lifecycle, identical cost would produce identical
lifetime. It does not. `cost_determines_lifecycle: false`.

## What this costs governance

The expiry is the governance window. When it is asserted rather than derived:

- **The record cannot be validated.** There is no statement to check a lifetime against, so
  a wrong expiry and a right one are indistinguishable in review.
- **Receipts bind to an arbitrary window.** A receipt covering a 4096-beat window and one
  covering 64 beats look equally authoritative when the underlying work was the same.
- **Drift is undetectable.** If the work a task class does changes, nothing says the
  lifetime should change with it, so it will not.

That is the same defect shape this repository has been cataloguing, arriving at the place
it matters most: an assertion whose basis was never written down.

## What the qualifier does, and refuses to do

`sdk-staging/stegverse/worker_lifecycle_qualifier.py` returns one of three verdicts:

```
QUALIFIED_DERIVED_FROM_STATED_COST     a derivation is stated and names cost factors the
                                       record actually carries, and expiry covers the work
ASSERTED_NOT_DERIVED                   expiry covers the work, but nothing derives it
UNSATISFIABLE_EXPIRY_BELOW_EXPECTED_WORK   the worker would expire before finishing
```

**It refuses to supply a coefficient nobody stated.** Choosing how many beats a compute unit
earns is an economics decision with governance consequences, and inventing one here would
manufacture exactly the false precision this document is about. What the qualifier does
instead is require the derivation to be stated, and check the conditions that follow from
meaning alone — that a worker cannot be required to finish after it expires, and that a
stated basis must refer to cost factors the record carries rather than to nothing.

So `ASSERTED_NOT_DERIVED` is not a claim that a lifetime is wrong. It is the claim that
nothing establishes it, which is the honest status of 47 of 48 records today.

## Re-running

```bash
python3 tools/qualify_worker_lifecycles.py \
  --cost-basis-root /home/user/stegverse-labs/.github/cost-basis \
  --json data/cost-basis/worker-lifecycle-qualification.json
```

Exit `0` when every record qualifies, `3` when any is asserted or unsatisfiable, `2` when
the corpus cannot be read. It exits `3` today.

The survey and the SDK demonstration run **the same qualifier module**, so they cannot
diverge.

## Not claimed

No lifetime is asserted to be wrong, and none is changed. No coefficient, ratio or bound is
proposed. 13 records carry no cost/heartbeat pair and are reported as skipped rather than
counted. This is a qualification of what the records state, and it grants no authority,
sets no lifetime and promotes nothing.
