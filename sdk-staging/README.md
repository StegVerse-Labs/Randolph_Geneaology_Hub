# SDK staging — worker cost binding

Two files destined for `StegVerse-org/StegVerse-SDK`, staged here because this session
cannot attach that repository: `add_repo` refuses a cross-tier add, since the session
already holds `stegverse-labs` sources. They are staged rather than described so the SDK
write is a copy, not a re-authoring.

| staged here | drops into the SDK at |
|---|---|
| `stegverse/worker_cost_binding.py` | `stegverse/worker_cost_binding.py` |
| `tests/test_worker_cost_binding.py` | `tests/test_worker_cost_binding.py` |

## What it does

Binds the measured Actions cost basis — `docs/ACTIONS_COST_BASIS.md` and
`data/cost-basis/measured-actions-cost-basis.json` — to a purpose-bound worker at task
assignment, so the SDK can demonstrate the exact billed cost of creating a worker rather
than only its derived lifetime.

The calculation is deterministic and offline: no network, no account state, no I/O. That
is deliberate — a test demonstrating the binding must not depend on a live bill.

```
billed_units = 0                                   if the substrate is public
             = ceil(lifetime_s / 60) x multiplier  if private   (linux 1, windows 2, macos 10)
total        = billed_units x worker_count
```

## What it demonstrates against the SDK's own fixture

`inspection/examples/tt-purpose-worker-cost-demo.example.json` ships three cost classes.
Applying the measured billing rule to them:

| cost class | compute units | derived lifetime | billed (private linux) |
|---|---|---|---|
| LOW | 1 | 15s | **1 min** |
| MEDIAN | 3 | 30s | **1 min** |
| HIGH | 9 | 60s | **1 min** |
| CONCURRENT (x3) | 9 aggregate | 30s each | **3 min** |

Two results follow, and the tests assert both:

1. **The shipped lifetime tiering is not a cost tiering.** A 9x spread in expected compute
   and a 4x spread in lifetime bill identically, because every tier is under one minute.
2. **Worker count is the cost driver.** CONCURRENT does the same aggregate compute as HIGH
   and bills three times as much, purely for being three workers.

At task assignment, then, the lever is how many workers are created — not how long each is
permitted to live.

## Verified against the real SDK

Both files were copied into a live `StegVerse-org/StegVerse-SDK` checkout and run there:

```
new module alone                  9 tests, all pass
unittest discover, baseline     336 tests, 4 failures, 10 errors, 2 skipped
unittest discover, with these   345 tests, 4 failures, 10 errors, 2 skipped
```

The nine added tests pass and nothing else moves. The checkout was restored afterwards.

The SDK's CI runs `python -m unittest` per module, which is how these were exercised.

**Pre-existing and not mine:** `tests/test_external_interlock_bootstrap.py` line 29 carries
a literal `\n` in committed source and cannot be parsed, so that module never runs. It is
identical with and without this change. It is the same defect shape as the one repaired in
Site PR #1456, now in a third repository.

## Not claimed

No dollar amount: per-minute rates and plan allowances are account state, not run evidence.
The binding grants no authority, sets no price, commits no budget and promotes no
benchmark. It covers GitHub Actions only.
