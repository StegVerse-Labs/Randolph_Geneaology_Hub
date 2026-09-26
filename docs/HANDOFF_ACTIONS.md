# Handoff actions

Recorded 2026-09-26. Two kinds of item: one that is mechanically clearable by an
administrative action, and four that are genuine decisions for a person to make.

Companion to `docs/BLOCKED_WORK_FOR_REVIEW.md`, which records *why* each item is not done.
This file records *how to do it*.

---

# Part 1 — Clearable: publish the worker lifecycle qualifier to the SDK

**Estimated effort: one settings action, then a two-file copy and one command.**

## 1.1 Why it is stuck

`StegVerse-org/StegVerse-SDK` attaches to a session for reading, but pushes are refused:

```
push_check: refused — Claude doesn't have GitHub access to stegverse-org/stegverse-sdk
for your organization.
```

The Claude GitHub App is installed for `StegVerse-Labs` but not for `StegVerse-org`.

## 1.2 Clear it

Either of these, done by a GitHub organization owner of `StegVerse-org`:

- Install the Claude GitHub App on the organization:
  https://github.com/apps/claude/installations/select_target
  Select `StegVerse-org`, and grant it `StegVerse-SDK` (all repositories is not required).
- Or, if an installation already exists and is merely unlinked, reconnect GitHub from
  claude.ai settings: https://claude.ai/customize/connectors?auth_start=github&auth_start_force=1

Verify it took effect: in a session, `add_repo` for `StegVerse-org/StegVerse-SDK` with
`access: "push"` should return without `push_check: refused`.

## 1.3 Land the change

The two files are already written and verified. They are **not drafts** — they were authored
inside a real clone of the SDK at `ecccfb511c6baf012c33ea27aa8e747dfe482273` and passed there.

```bash
# from a checkout of StegVerse-org/StegVerse-SDK
cp <hub>/sdk-staging/stegverse/worker_lifecycle_qualifier.py  stegverse/
cp <hub>/sdk-staging/tests/test_worker_lifecycle_qualifier.py tests/

python3 -m unittest tests.test_worker_lifecycle_qualifier      # expect: Ran 14 tests  OK
python3 -m unittest tests.test_purpose_bound_worker_cost_demo  # expect: Ran  4 tests  OK
```

**Use `unittest`, not `pytest`.** The SDK contains a directory named `pytest`, which shadows the
pytest module when invoked from the repository root: `python3 -m pytest` collects **0 tests**
there — for the existing suite as much as for this one. That is a pre-existing condition of the
repository, unrelated to this change. (Worth fixing separately; renaming that directory or
adding a `pytest.ini` with an explicit `testpaths` would do it.)

Confirm the files are the verified ones before copying:

| file | sha256 (first 16) |
|---|---|
| `sdk-staging/stegverse/worker_lifecycle_qualifier.py` | `988a82615ff251d0` |
| `sdk-staging/tests/test_worker_lifecycle_qualifier.py` | `ef9fedea6727928d` |

`tests/test_sdk_worker_lifecycle_qualifier_staging.py` in this repository checks those digests
on every run, so a drifted copy fails here before it reaches the SDK.

## 1.4 What it adds, in one paragraph for the PR body

Qualifies the worker lifetime a task assignment implies, from the task's estimated resource
cost, under the canonical invariant
`WORKER_LIFETIME_IS_DERIVED_PER_INTENDED_TASK_NOT_GLOBALLY_FIXED`. It **delegates the
five-component sum to `purpose_bound_worker_cost_demo._sum_budget`** rather than restating it, so
the demo and the qualifier cannot drift apart; a test asserts the delegation. A task stating no
resource estimate yields `TASK_STATES_NO_RESOURCE_COST_ESTIMATE` and no lifetime — never a
default, because a defaulted lifetime is the globally fixed lifetime the invariant forbids.
Qualification is an observation: `authority_effect: NONE_QUALIFICATION_ONLY`. Deterministic and
offline: no I/O, no account state, no network.

## 1.5 After it lands

Update `docs/BLOCKED_WORK_FOR_REVIEW.md` §3 from blocked to landed, and note the SDK PR number.

---

# Part 2 — Decisions

Four items that are not blocked by access. Each needs a person to choose, and each is stated
with what the choice costs either way.

## 2.1 A gate for claims that land without a COSV projection row

### What happened three times

The Site ceremony is **claim → COSV projection index → counter bumps**. Three separate incidents
did the first step and not the rest:

| incident | repaired in |
|---|---|
| A COSV row named a claim file that existed only on `main`, not on the branch carrying the row | Site #1465 |
| My own claim carried a claim file and no index row | Site #1463 |
| Two dormant claims (`GADI-001`, `STEGVERSE-002-EXPERIMENT-RERUN-001`, written 2026-09-08 and 2026-09-17) merged weeks later with no rows | Site #1466 |

Each was repaired individually, after the fact.

### Why the existing checker did not stop them

`scripts/check_cosv_task_projection.py` **already computes** the unindexed set:

```python
unindexed_active = sorted(active_task_ids - indexed_ids)
```

but it does not fail on it. It accepts a non-empty set provided the coverage block declares the
fail-closed state (lines ~218-222):

```python
if unindexed_active:
    assert cov["repository_unindexed_active_claim_tasks_present"] is True
    assert cov["repository_vector_present_blocker"] == "UNINDEXED_ACTIVE_CLAIM_TASKS_REMAIN"
    assert cov["repository_active_task_surface_audit_complete"] is False
    assert cov["repository_vector_present_claimed"] is False
```

So "a claim with no COSV row" is a **declarable state**, not an error. That is a deliberate
design — it lets the repository record an incomplete surface honestly rather than lie — and it is
exactly why nothing objected.

Worth correcting an assumption: `.github/workflows/validate.yml` has **no path filters**; it runs
on every push and pull request. The escape was the declarable state, not the trigger.

### The change, if you want it

In `check_cosv_task_projection.py`, make a non-empty `unindexed_active` a hard failure rather
than a declarable state — while keeping the declarable path available behind an explicit,
dated, per-task exemption list, so an honest incomplete surface is still expressible but must be
named rather than merely counted.

Sketch:

```python
EXEMPT = load("data/cosv/unindexed-active-exemptions.json")   # task_id -> {reason, recorded_at}
unexplained = [t for t in unindexed_active if t not in EXEMPT]
if unexplained:
    raise AssertionError(
        "active claims without a COSV projection row: " + ", ".join(unexplained))
```

### What it costs

**For it.** All three incidents fail at the pull request that introduces them, naming the task,
instead of being found later by someone reading a red `main`. The repair each time was two JSON
entries and a counter — trivial once seen, invisible until.

**Against it.** Every contributor adding a claim must also add a projection row in the same
change, or add an exemption. A dormant branch (the `GADI-001` case: a claim written on
2026-09-08 and merged on 2026-09-26) will fail on merge, possibly to someone who did not write
it. That is the intended behaviour, but it is a real tax on long-lived branches.

**Recommendation.** Worth doing, with the exemption list, because the failure mode it prevents is
silent and the repair is cheap. But it changes what the registry enforces for everyone, which is
why it was not done unasked.

**Owner.** The claim-registry owners. Recorded in Site #1466 and in
`SITE-COSV-INDEX-GADI-SV002-RECONCILIATION-001`'s `next_task_after_release`.

## 2.2 Ownership of `STEGOS-GOVERNED-FREE-TIER-UNIT-ECONOMICS-001`

### The decision

Which component owns *measuring the true unit economics of one complete governed Free-tier
workflow*. The proposal in `StegVerse-Labs/StegOS:data/canonical-task-registration-proposals/`
carries `ownership_review_required: true` and an `alternate_owner_candidate` because the work
genuinely spans three owners:

- **StegOS** — the admitted execution surface the workflow runs on
- **LLM adapter** — the provider transport whose usage is the largest measured cost
- **Site** — where `S1_FREE_COST` is published and where the measurement is displayed

### Why it cannot be deferred indefinitely

Site benchmark `S1_FREE_COST` cannot bind to a canonical task until this is registered. It is
currently recorded unbound with that exact reason in
`data/economy/public-release-benchmarks.v1.json`, and the binding guard added in Site #1463
enforces that it stays honestly unbound rather than quietly acquiring a wrong binding.

### What to do

1. TVC decides the owner.
2. Whoever can write `StegVerse-Labs/.github` registers the task (see
   `docs/BLOCKED_WORK_FOR_REVIEW.md` §1 — that repository cannot be attached to a session at all,
   so this is a human or differently-provisioned action).
3. Bind `S1_FREE_COST` in the Site benchmarks file with
   `provenance: REGISTRY_ASSERTED` if the new record names the benchmark in its `registration`
   block, or `SITE_ASSERTED_REGISTERED_TASK` if it does not. The guard enforces the distinction.

## 2.3 Review question 6 — does `EPHEMERAL-STEGBROWSER-EXTERNAL-AI-ACTIVATION-001` own the ephemeral browser workflow?

### The decision

`docs/EPHEMERAL_BROWSER_LLM_ECOSYSTEM_CHAT_REVIEW.md` (Site, merged in #1467) describes a
workflow: Ecosystem Chat request → KV continuity → InTr admission and WorkerCoordinator fence →
ephemeral StegBrowser lease plus a separately authorized LLM session → Organization Records →
Master Records reconstruction → authorized feedback → session destruction.

The registered canonical task `EPHEMERAL-STEGBROWSER-EXTERNAL-AI-ACTIVATION-001` (PROPOSED)
states almost the same thing, and its `expected_evidence_predicates` correspond closely to the
review's §6 acceptance criteria including the non-ALLOW path.

Either it owns this work, or the review describes something that must be explicitly
distinguished from it. The review asks; it does not answer, because that is its owners' call.

### What to do

Put the question to that task's owners. If it owns the workflow, the review becomes its
supporting analysis and should say so in §2. If not, record the distinction in the review's
§2.1 alongside the other superseded and unregistered references, so the next reader does not
have to re-derive it.

Either answer is a one-paragraph edit to a merged document plus, if it does own it, a citation
update in `data/reviews/ephemeral-browser-llm-ecosystem-chat.v1.json` — which the guard will
check against registry state on the next run.

## 2.4 Make the stop-hook fix survive container restarts

### The problem

`~/.claude/stop-hook-git-check.sh` counts commits ahead of the branch's **own upstream** rather
than commits on **no remote at all**:

```bash
unpushed=$(git rev-list "$upstream..HEAD" --count 2>/dev/null) || unpushed=0
```

So restarting a branch from a freshly merged default branch reports already-published commits as
unpushed — by exactly the merge commit, every time.

The fix is one line, using the idiom the same file already uses at lines 79 and 96:

```bash
unpushed=$(git rev-list HEAD --not --remotes --count 2>/dev/null) || unpushed=0
```

Verified against three cases: a genuine local-only commit still warns; a merged-and-restarted
branch goes silent; new work on the restarted branch warns again.

It has been applied three times in this session and lost three times, because the home directory
is reprovisioned from the base image on every container restart.

### What to do

Paste the script below into the environment's **Setup script**: the cloud environment menu in the
session title bar → **Edit** → Setup script. It runs on each container start.

```bash
#!/bin/bash
# Idempotent: make the stop hook count commits that are on NO remote, rather than
# commits merely ahead of this branch's own upstream. Without this, restarting a
# branch from a freshly-merged default branch reports already-published commits
# as "unpushed". No-ops if already patched, if the file is absent, or if upstream
# changed the line (so it can't silently mangle a future version).
set -u
H="$HOME/.claude/stop-hook-git-check.sh"
OLD='unpushed=$(git rev-list "$upstream..HEAD" --count 2>/dev/null) || unpushed=0'
NEW='unpushed=$(git rev-list HEAD --not --remotes --count 2>/dev/null) || unpushed=0'

[ -f "$H" ] || { echo "patch-stop-hook: $H absent, skipping"; exit 0; }
grep -qF "$NEW" "$H" && { echo "patch-stop-hook: already patched"; exit 0; }
grep -qF "$OLD" "$H" || { echo "patch-stop-hook: expected line not found, leaving file alone"; exit 0; }

python3 - "$H" "$OLD" "$NEW" <<'PY'
import sys, pathlib
path, old, new = sys.argv[1], sys.argv[2], sys.argv[3]
p = pathlib.Path(path); s = p.read_text()
assert s.count(old) == 1, f"expected exactly one match, got {s.count(old)}"
p.write_text(s.replace(old, new))
PY

bash -n "$H" && echo "patch-stop-hook: applied and syntax-clean"
```

Exercised on all four paths: stock file (`applied and syntax-clean`), already patched
(`already patched`, no double-apply), file absent (`skipping`), and upstream changed the line
(`leaving file alone` — it will not mangle a future version of the hook).

### Caveat worth knowing

`--not --remotes` reads remote-tracking refs, so it is only as fresh as the last `git fetch`.
This was observed live in this session: a single-branch clone had its remote-tracking ref pruned,
and the count briefly read 2 unpushed commits that were in fact published. A `git fetch` cleared
it. If that becomes a nuisance, add `git fetch --quiet origin` before the count — at the cost of
a network call on every hook run.

---

# Summary

| item | who | action |
|---|---|---|
| SDK qualifier | `StegVerse-org` GitHub org owner | install the Claude GitHub App, then copy two files and run one command (§1) |
| claim → COSV gate | claim-registry owners | decide; implementation sketched in §2.1 |
| Free-tier task ownership | TVC | decide the owner, then register and bind (§2.2) |
| Review question 6 | owners of `EPHEMERAL-STEGBROWSER-EXTERNAL-AI-ACTIVATION-001` | answer; one-paragraph edit either way (§2.3) |
| Stop-hook persistence | account holder | paste the script into the environment Setup script (§2.4) |
