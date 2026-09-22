# Guard drift census

Measured: 2026-09-22. Method and raw commands are in this document so the
sweep can be re-run rather than re-derived.

## Why this exists

The gap survey of 2026-09-21 found three instances of one shape — ten
independent secret scanners disagreeing (C3), an unimportable module no
workflow referenced (C4), one `sys.modules` write breaking 46 test files
(C6). The shape was named but never counted, so it was re-derived the next
day. This is the count.

The shape: **something moved, and the thing that asserts about it did not
follow.** A checker, test, or recorder still points at a file that no longer
holds the code it asserts about.

## Headline

The pattern is real, and it is **concentrated rather than ecosystem-wide**.
Three repositories are fully green. Two carry nearly all of it.

| repository | suite result | state |
|---|---|---|
| continuity-vault-kit | 742 passed | clean |
| StegOS | 1675 passed | clean |
| stegfin-governance | 263 passed | clean |
| Randolph_Geneaology_Hub | 20 passed | clean |
| TVC | suite aborts, 28 collection errors | one root cause |
| Site | suite aborts; excluding 3 files, 64 failed / 461 passed | epicentre |

## Site — the epicentre

The suite cannot run at all. Three files abort collection:

```
tests/test_stegos_ipod_bootstrap_projection.py   SystemExit: 0 at import
tests/test_my_kv_personal_form_profile_source.py SyntaxError in committed source
tests/test_stegmusic_browser.py                  playwright absent (environment, not a defect)
```

The first is the sharpest instance of the shape. `scripts/check_stegos_ipod_bootstrap_projection.py`
is a wrapper that `exec`s its implementation with `__name__ = "__main__"`, so
importing it runs `raise SystemExit(main())`. A test imports it, `SystemExit`
escapes collection, and pytest aborts — **one script's exit code takes down all
487 guards in the repository.** Three scripts in `scripts/` use that wrapper
pattern.

The second is the same class as the survey's C4: source committed in a state
that cannot be parsed.

With those three excluded: **64 failed, 461 passed, 1462 subtests passed**,
across 31 distinct failing files. Classifying the 94 assertion-error lines:

```
43   marker not present in the file content being asserted against
 6   value == expected drift
45   other
```

So the single largest failure mode is literally the shape: an assertion
naming a string that the target file no longer contains.

One of those 43 is directly connected to today's open work:

```
AssertionError: '"MY_KV_INSTALLATION_STATUS":true' not found in
  '"use strict";\n\n/* Root-scoped Universal InTr service worker.
   The prior runtime is retained byte-for-byte in intr-service-worker-base-v1.js. ...'
```

That is the **same file and the same drift** as the blocker on
`SITE-HIL-ROOT-INTR-CONFORMANCE-CHILD-102-20260920`: the root Universal InTr
worker was split into a base plus a wrapper, and consumers still assert
against the wrapper. The HIL task is one symptom of a defect with at least two
independent witnesses.

## TVC — one root cause, nineteen files

28 collection errors:

```
19   AttributeError: partially initialized module 'tvc_provider_operation_broker'
     has no attribute 'ProviderOperationBrokerError' (circular import)
 6   ModuleNotFoundError: fastapi   (absent in the measuring environment, not a defect)
 3   ImportError
```

One circular import blocks nineteen test files. Excluding the six
environment-caused errors, the suite still aborts.

## Blast-radius amplifiers recur

| amplifier | guards taken out |
|---|---|
| `SystemExit` at import (Site) | 487 |
| one unrestored `sys.modules` write (survey C6, `.github`) | 46 |
| one circular import (TVC) | 19 |

Each is a single line or a single import. The cost is not proportional to the
defect.

## Guards that cannot fire

Counting test and checker files against the workflows that reference them,
crediting workflows that run a tree wholesale (`pytest tests/`):

```
repository                guards    unreferenced
site                         487             247   51%
stegverse-sdk                255              28   11%
stegfin-governance            97               6    6%
stegverse-labs/.github       660              31    5%
tvc                          302               4    1%
continuity-vault-kit         140               2    1%
StegOS                       325               0    0%
TOTAL                       2271             318   14%
```

A first pass that did not credit bulk runs reported 64%. That number was
wrong; most repositories do run their trees wholesale. Site is the real
outlier, and it is also the repository whose 64 failures nothing observes —
those two facts are the same fact.

## What this says about the MyKV thesis

Both halves hold, for different populations.

- For the **KV capability layer**, MyKV is definitionally the key. The
  activation readiness evaluator gives 46/46 entries `BLOCKED`, with
  `production_interlock_runtime_activated` and
  `transport_capability:DEVICE_KV_INTR` each appearing in all 46. Nothing
  else is close.
- For the **wider set of stalled tasks**, this census is the larger share.
  Of three named examples, only one is genuinely on the InTr lane, and even
  that one is blocked by a stale validator literal rather than by the
  protocol: `verify-nvidia-hf-publication.yml` contains zero occurrences of
  intr/knowledgevault/device_kv, and `crypto-bot` is a separate repository
  with no link from here.

The two are cheaply separable. Two root causes — Site's `SystemExit`-at-import
and TVC's circular import — restore 506 guards to being runnable at all, which
is a prerequisite for knowing what else is broken.

## Re-running this

```bash
# guards versus workflow references
python3 /tmp/sweep2.py

# per-repository suite state
for r in continuity-vault-kit tvc stegos site stegfin-governance; do
  (cd /home/user/$r && python3 -m pytest -q --no-header -p no:cacheprovider 2>&1 | tail -2)
done

# Site, excluding the three collection aborts
cd /home/user/site && python3 -m pytest -q --no-header -p no:cacheprovider \
  --ignore=tests/test_stegos_ipod_bootstrap_projection.py \
  --ignore=tests/test_my_kv_personal_form_profile_source.py \
  --ignore=tests/test_stegmusic_browser.py
```

## Not claimed

These are measurements of guard health, not of runtime. A green suite does not
mean a capability works, and a failing guard does not by itself mean the
runtime is wrong — in several of the 43 marker cases the implementation moved
and is correct while the assertion is stale. Nothing here grants execution or
activation authority. `playwright` and `fastapi` absences are artifacts of the
measuring environment and are excluded from the defect counts above.
