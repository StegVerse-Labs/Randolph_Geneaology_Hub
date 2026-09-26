# sdk-staging

Work destined for `StegVerse-org/StegVerse-SDK`, held here because this session can read that
repository but cannot push to it (`push_check: refused` — the Claude GitHub App is not installed
on `StegVerse-org`). See `docs/BLOCKED_WORK_FOR_REVIEW.md` §3.

These files are **not** a draft. They were written inside a real clone of the SDK at
`ecccfb511c6baf012c33ea27aa8e747dfe482273` and verified there:

```
python3 -m unittest tests.test_worker_lifecycle_qualifier      Ran 14 tests   OK
python3 -m unittest tests.test_purpose_bound_worker_cost_demo  Ran  4 tests   OK   (unchanged)
```

and the copies here are byte-identical to the versions that passed:

| file | sha256 (first 16) |
|---|---|
| `stegverse/worker_lifecycle_qualifier.py` | `988a82615ff251d0` |
| `tests/test_worker_lifecycle_qualifier.py` | `ef9fedea6727928d` |

`tests/test_sdk_worker_lifecycle_qualifier_staging.py` in this repository re-checks those
digests, so the staged copy cannot drift from what was verified.

## To land it

```
cp sdk-staging/stegverse/worker_lifecycle_qualifier.py  <sdk>/stegverse/
cp sdk-staging/tests/test_worker_lifecycle_qualifier.py <sdk>/tests/
cd <sdk> && python3 -m unittest tests.test_worker_lifecycle_qualifier
```

The SDK contains a directory named `pytest`, which shadows the pytest module when invoked from
the repository root — `python3 -m pytest` collects 0 tests there, for the existing suite as much
as this one. Use `unittest`, or invoke pytest from outside the root. Pre-existing, not caused by
this change.

## What the module does

It qualifies the worker lifetime a task assignment implies, from the task's estimated resource
cost, under the canonical invariant
`WORKER_LIFETIME_IS_DERIVED_PER_INTENDED_TASK_NOT_GLOBALLY_FIXED`.

It **delegates the sum to `purpose_bound_worker_cost_demo._sum_budget`** rather than restating
it. An earlier draft here reimplemented those five components; reading the real SDK showed the
sum already existed, so the two would have been free to drift apart. A test asserts the
delegation.

A task stating no resource estimate yields `TASK_STATES_NO_RESOURCE_COST_ESTIMATE` and no
lifetime — never a default, because a defaulted lifetime is the globally fixed lifetime the
invariant forbids. Qualification is an observation: `authority_effect: NONE_QUALIFICATION_ONLY`.
