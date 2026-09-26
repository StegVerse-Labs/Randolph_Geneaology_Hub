# Blocked work — for review

Recorded 2026-09-26. Everything below was attempted and refused. Each entry names what was
tried, the exact refusal, who can clear it, and what is already built and waiting.

Nothing here is blocked on a decision I was waiting to be told to make. The authorization to
proceed was given; these are platform and installation limits that authorization does not move.

---

## 1. Resource cost estimates for 162 canonical tasks — BLOCKED, cannot be done from any session with this constraint

**What it is.** `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001` states the invariant
`WORKER_LIFETIME_IS_DERIVED_PER_INTENDED_TASK_NOT_GLOBALLY_FIXED` and gives the derivation as
five resource-cost components summing to a lifetime. Measured across the 163 canonical task
records, **exactly one carries a resource cost estimate** — the record whose purpose is to prove
the model. The other 162 assign work whose worker lifetime nothing derives, so the expiry window
their receipts cover is not checkable.

**Why it is blocked.** The estimates belong on the canonical task records in
`StegVerse-Labs/.github`, under `data/canonical-task-records/`. That repository **cannot be
attached to this session at all**:

```
add_repo: repository name ".github" begins with '.', so its clone directory would be a
hidden path under this session's working directory and could collide with configuration
directories (e.g. ~/.claude). Repositories whose names begin with '.' cannot be attached
to this session.
```

A direct push is refused for the same reason:

```
remote: access denied by the git proxy: StegVerse-Labs/.github is not in this session's
authorized repository set, so the proxy will not inject a credential for it.
```

This is a hard platform limit on the repository *name*, not a permission. Granting access does
not clear it.

**Who can clear it.** Nobody, within this constraint. The work needs either a session whose
tooling can attach a dot-prefixed repository, a mirror of the registry under a non-dot name, or
a person applying the change directly.

**What is ready.** `tools/qualify_worker_lifecycles.py` applies the staged qualifier to all 163
records and reports which can derive a lifetime; it exits 3 while any cannot. The cheapest
starting set is the 5 cost-basis records whose `task_class` already resolves to a canonical task
id — those have measured inputs and need only transcribing into the record.

---

## 2. Registering `STEGOS-GOVERNED-FREE-TIER-UNIT-ECONOMICS-001` — BLOCKED, same limit, plus an open ownership question

**What it is.** The third of three canonical task registration proposals drafted in
`StegVerse-Labs/StegOS` (`data/canonical-task-registration-proposals/`). Two of the three —
`STEGOS-LOCAL-AI-ENTITY-CHATGPT-001` and `-CLAUDE-CODE-001` — were registered upstream and now
carry `registration.benchmark_id` naming Site benchmarks S1_CHATGPT and S1_CLAUDE. This third
one was not.

**Why it is blocked.** Two independent reasons:

1. Registration is a write to `StegVerse-Labs/.github`, blocked exactly as in item 1.
2. The proposal carries `ownership_review_required: true` and an `alternate_owner_candidate`.
   That flag is there because the owning component was genuinely unclear when it was drafted —
   free-tier unit economics spans StegOS, the LLM adapter and Site. Resolving it is a governance
   decision, not a coding one, and it was flagged for TVC.

**Who can clear it.** TVC decides ownership; then whoever can write the registry registers it.

**What is downstream.** Site benchmark `S1_FREE_COST` cannot bind to a canonical task until this
is registered. It is currently recorded in
`data/economy/public-release-benchmarks.v1.json` as unbound with that reason stated, and the
binding guard enforces that it stays honest.

---

## 3. Publishing the worker lifecycle qualifier to the SDK — BUILT AND VERIFIED, push refused

**What it is.** `stegverse/worker_lifecycle_qualifier.py` plus `tests/test_worker_lifecycle_qualifier.py`
for `StegVerse-org/StegVerse-SDK`.

**Status: built, and verified inside a real clone of the SDK** at `ecccfb51`:

```
python3 -m unittest tests.test_worker_lifecycle_qualifier     Ran 14 tests   OK
python3 -m unittest tests.test_purpose_bound_worker_cost_demo Ran  4 tests   OK   (unchanged)
```

Reading the real SDK changed the module. The earlier staged draft reimplemented the five-component
sum; the SDK already has it as `purpose_bound_worker_cost_demo._sum_budget`. The verified version
**delegates to it** rather than restating it, so the demo and the qualifier cannot drift apart,
and raises the SDK's own `PurposeBoundWorkerError`. A test asserts the delegation.

**Why it is blocked.** The repository attaches for reading, but:

```
push_check: refused — Claude doesn't have GitHub access to stegverse-org/stegverse-sdk
for your organization.
```

**Who can clear it.** An organization admin installs the Claude GitHub App on `StegVerse-org`
(https://github.com/apps/claude/installations/select_target), or GitHub is reconnected from
claude.ai settings to re-link an existing installation.

**What is ready.** Both files are in `sdk-staging/`, byte-identical to the versions verified in
the SDK clone (sha256 `988a8261…` and `ef9fedea…`). They are a copy away from landing:

```
cp sdk-staging/stegverse/worker_lifecycle_qualifier.py  <sdk>/stegverse/
cp sdk-staging/tests/test_worker_lifecycle_qualifier.py <sdk>/tests/
python3 -m unittest tests.test_worker_lifecycle_qualifier
```

Note for whoever runs it: the SDK contains a directory named `pytest`, which shadows the pytest
module when invoked from the repository root — `python3 -m pytest` collects 0 tests there, for
the existing suite as well as this one. Use `unittest`, or invoke pytest from outside the root.
That is a pre-existing condition of the repository, not of this change.

---

## 4. Canonical Task Registry issues could not be read — three references in the ephemeral-browser review remain unverified

`StegVerse-Labs/.github` issues #1299, #60 and #2721, `StegVerse-Labs/StegBrowser` issues #2 and
#4, and `StegVerse-org/LLM-adapter` issue #7 are cited in
`StegVerse-Labs/Site:docs/EPHEMERAL_BROWSER_LLM_ECOSYSTEM_CHAT_REVIEW.md`. Their existence and
titles could not be confirmed: the `.github` and StegBrowser repositories are not in this
session's GitHub scope, and `.github` cannot be attached at all.

`Site#242` and `StegOS#213` **were** verified — both open, titles matching their descriptions.
`.github#2721` is corroborated indirectly: it is the `registration.source` recorded on
`STEGOS-LOCAL-AI-ENTITY-CHATGPT-001`.

The registry *contents* were verified throughout, from a read-only clone on disk. Only the issue
tracker was unreachable.

---

## 5. The stop-hook fix does not survive a container restart — needs one paste into environment settings

`~/.claude/stop-hook-git-check.sh` counts commits ahead of the branch's own upstream rather than
commits on no remote at all, so restarting a branch from a freshly merged default branch reports
already-published commits as unpushed. The one-line fix is verified against three cases
(genuine local-only commit still warns; merged-and-restarted branch goes silent; new work on the
restarted branch warns again).

It is reapplied whenever the container restarts and lost again on the next one, because the home
directory is reprovisioned from the base image. An idempotent patcher was written and exercised
on all four paths — stock file, already patched, file absent, upstream changed the line. It
belongs in the environment's **Setup script** (cloud environment menu → Edit), which only the
account holder can set.

---

## Not blocked, deliberately not done

**A gate that fails when an active claim lands without a COSV projection row.** This is the
change that would have caught three separate incidents at the source rather than after the fact:
a COSV row referencing a claim file that was on `main` and not the branch; my own claim indexed
one third of the way; and two dormant claims merged weeks late with no rows at all. Each was
repaired individually, in Site #1465, #1463 and #1466.

It is not built because it changes what the claim registry enforces for every contributor, and
that is a decision for the claim-registry owners rather than a correction to make unasked. It is
recorded in Site #1466 and in that claim's `next_task_after_release`.

**Review question 6** — whether `EPHEMERAL-STEGBROWSER-EXTERNAL-AI-ACTIVATION-001` owns the
ephemeral-browser/LLM/Ecosystem Chat workflow or must be distinguished from it — is put to its
owners in the review rather than answered for them.
