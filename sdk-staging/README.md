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

Qualifies a purpose-bound worker's lifetime at task assignment. `purpose_bound_worker`
accepts `max_lifetime_seconds` and checks only that it is a positive integer — nothing
checks that the lifetime is justified by the work the worker exists to do.

Worker cost analysis is the factor that determines the lifecycle, and the lifecycle is what
governance and record keeping bind to: the expiry is the window in which a worker may act,
and therefore the window its receipts cover.

Three verdicts:

```
QUALIFIED_DERIVED_FROM_STATED_COST        derivation stated, names cost factors the record
                                          carries, and expiry covers expected work
ASSERTED_NOT_DERIVED                      expiry covers the work, nothing derives it
UNSATISFIABLE_EXPIRY_BELOW_EXPECTED_WORK  the worker would expire before finishing
```

**It refuses to supply a coefficient nobody stated.** Choosing how many beats a compute unit
earns is an economics decision with governance consequences; inventing one would manufacture
the false precision this exists to expose. It requires the derivation to be stated and checks
only what follows from meaning.

## What it demonstrates

Against the canonical corpus in `StegVerse-Labs/.github/cost-basis/`, 48 records carrying
both a cost estimate and a heartbeat estimate:

| | |
|---|---|
| qualified | **1 of 48** |
| asserted, no derivation stated | **47 of 48** |
| unsatisfiable | 0 of 48 |

Headroom (expiry over expected work) runs `min 2.0x, median 12.8x, max 2666.7x`. And two
pairs of records carry byte-identical cost inputs with expiries **64x** and **93x** apart —
so cost does not determine lifecycle today.

The tests reproduce both the collision and the headroom spread, so the SDK demonstrates the
real condition rather than a constructed one.

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
