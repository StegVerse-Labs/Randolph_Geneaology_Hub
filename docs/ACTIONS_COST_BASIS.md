# GitHub Actions billing — measured

## Scope correction

This measures **billing**: what GitHub charges for Actions minutes. That is an invoice
question, and billing data answers it.

It is **not** worker cost analysis. Worker cost analysis is the factor that determines the
worker lifecycle, and the qualifier for establishing a precise lifecycle for governance and
record keeping — see `WORKER_LIFECYCLE_COST_QUALIFIER.md`, which is the one the canonical
`cost-basis/` corpus is about. `external_cost_usd` is one field of eight in those records
and is `0` throughout.

Both are real; they are different axes. This document was originally filed under the wrong
one. What follows is unchanged and remains correct as a billing measurement.


Measured: 2026-09-23. Re-run with `tools/measure_actions_cost_basis.py`; the record it
produces is `data/cost-basis/measured-actions-cost-basis.json`.

## Why this exists

`StegVerse-Labs/.github/cost-basis/` already holds 61 worker-runtime cost records. They are
estimates, and they say so. Counted:

```
61 records
44 with zero empirical samples (sample_count 0 or absent)
17 with exactly one; none with more than one
 3 different schemas   worker-runtime-cost-basis/v0.1 (50)
                       worker-cost-basis/v0.1         (10)
                       worker-cost-basis/v1            (1)
11 different confidence vocabularies, including LOW, MEDIUM, HIGH,
   LOW_PRELIVE, INITIAL_BOUNDED_ESTIMATE, LOW_UNTIL_FIRST_SOVEREIGN_RUN
 1 record carrying estimate_basis at all
```

The one record that states its basis states it plainly:
`CONSERVATIVE_SOURCE_BOUNDED_ONE_SHOT_NOT_EMPIRICAL_RUNTIME_MEASUREMENT`.

`STEGOS-GOVERNED-FREE-TIER-UNIT-ECONOMICS-001` requires `COSTS_MEASURED_NOT_ESTIMATED` and
lists `GITHUB_ACTIONS_COST_MEASURED` among its components. This measures that one component
from retained run evidence. It does not address the lifecycle question the corpus exists for.

## The two facts that decide an Actions bill

Neither is how long a workflow takes.

### 1. Visibility. Three quarters of all runs are free.

Actions minutes on a public repository cost nothing. Measured across six repositories:

| repository | visibility | runs | billed |
|---|---|---|---|
| Site | public | 40,000 | **no** |
| continuity-vault-kit | public | 5,787 | **no** |
| Randolph_Geneaology_Hub | public | 49 | **no** |
| TVC | private | 8,827 | yes |
| stegfin-governance | private | 2,948 | yes |
| StegOS | private | 2,597 | yes |

**45,836 of 60,208 runs — 76.1% — are in public repositories and bill nothing.**

Site alone accounts for 40,000 runs, more than every private repository combined, and costs
zero Actions minutes. Any cost analysis that ranks repositories by run count without
checking visibility gets the answer exactly backwards: it would name Site the dominant cost
and miss that the entire bill sits in three repositories it barely mentions.

The billed population is concentrated:

```
TVC                  8,827   61.4% of billed runs
stegfin-governance   2,948   20.5%
StegOS               2,597   18.1%
```

### 2. Per-minute rounding. Roughly two thirds of every billed minute is rounding.

Private-repository runs bill by the minute, rounded **up**, per run. A 16-second run bills a
full minute. Measured over 100 recent runs per repository:

| repository | median run | billable units | actual compute | rounding |
|---|---|---|---|---|
| StegOS | 24s | 100 | 38.2 min | **61.8%** |
| TVC | 21s | 100 | 35.7 min | **64.3%** |
| stegfin-governance | 18s | 100 | 33.1 min | **66.9%** |
| *Site (free)* | *16s* | *103* | *33.0 min* | *67.9%* |
| *continuity-vault-kit (free)* | *12s* | *100* | *23.1 min* | *76.9%* |
| *Randolph_Geneaology_Hub (free)* | *12s* | *49* | *11.1 min* | *77.3%* |

In the billed repositories, **61.8%–66.9% of every Actions minute paid for is rounding, not
compute.**

## What this means, and it is not what you would guess

**The cost driver is run count, not run duration.** Every measured median is under 25
seconds, so essentially every run bills the same one minute whether it takes 3 seconds or
55. Making a workflow twice as fast saves nothing at all.

The only levers that move the bill are:

1. **Run fewer times.** Tighter path filters, fewer workflows triggering on the same event,
   consolidating jobs that always run together. One workflow doing the work of three saves
   two billed minutes per event, regardless of how long any of them take.
2. **Move work to public repositories**, where it is free — subject to whether the content
   belongs in public, which is a governance question and not a cost one.
3. **Watch the runner class.** Private-repo macOS minutes bill at **10×** Linux, Windows at
   2×. StegOS carries two macOS workflows (`ios-apple-toolchain-validation.yml`,
   `ios-device-package-validation.yml`). Neither appeared in the most recent 100 runs, so
   the StegOS figure above is Linux-only and **understates any period in which iOS builds
   run** — a single macOS run bills like ten Linux runs.

The optimisation instinct — make it faster — is the one thing that provably does not help.

## Re-running this

```bash
python3 tools/measure_actions_cost_basis.py \
  --sample 100 \
  --out data/cost-basis/measured-actions-cost-basis.json
```

`--repo owner/name` (repeatable) narrows the set; `--checkout-root` points at local clones,
which is how each run is attributed to a runner class without spending an API request per
run. The record reports `runner_classes_observed`, `runs_without_runner_mapping` and
`runner_map_available` so an unmapped or Linux-only sample is visible rather than silent.

## Not claimed

**No dollar amount.** Per-minute rates, plan allowances and included-minute tiers are
account state, not run evidence, and this reads only run evidence. It reports billable
units and where they concentrate, which is the part that can be measured.

Sampled runs are the **most recent**, not a uniform sample of history, so a workload that
has changed shape is represented by its current shape. Durations are wall-clock from run
metadata and include queueing, which overstates compute slightly and therefore
*understates* the rounding share — the real overhead is at least what is reported.

13 Site runs had no local workflow file to map (`dynamic/pages/pages-build-deployment` and
similar platform-generated runs) and were assumed Linux. Site is public, so this changes
nothing there; on a private repository the same gap would matter.

This covers **GitHub Actions only**. Provider, sandbox, resident Node, governance and
custody cost are the other components `STEGOS-GOVERNED-FREE-TIER-UNIT-ECONOMICS-001`
requires, and none of them is measured here.

Measurements grant no authority, set no price, commit no budget and promote no benchmark.
