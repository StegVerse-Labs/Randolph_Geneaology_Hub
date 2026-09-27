# Registering the WorkSpace canonical task

Date: 2026-09-27
Status: **built and validated here; delivery to the registry blocked on repository access.**
Target repository: `StegVerse-Labs/.github`
Basis: `docs/WORKSPACE_MYKV_SKAP_REGISTRY_REVIEW.md` §6–§9

---

## 1. What this is

`docs/WORKSPACE_MYKV_SKAP_REGISTRY_REVIEW.md` established that **zero canonical
registry tasks govern the StegVerse WorkSpace surface**. This registers one.

The task is `STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001`, COSV task vector
`10500000114000`, `coordination_state: PROPOSED`, `checkout_state: UNCLAIMED`.

It is produced by `tools/register_workspace_canonical_task.py` and pinned by
`tests/test_workspace_canonical_task_registration.py` (50 tests). It mints no
authority: `worker_claim` is the canonical projection required by
`TASK_REGISTRY_CANONICAL_INVARIANTS.md` when no authentic WorkerCoordinator
claim or fence has been observed.

## 2. Why it is not already in the registry

Both delivery paths were tested first-hand, not assumed:

| Path | Result |
| --- | --- |
| `git push` to `StegVerse-Labs/.github` | `remote: access denied by the git proxy: StegVerse-Labs/.github is not in this session's authorized repository set` → HTTP 403 |
| `add_repo` (the remedy the proxy names) | `repository name ".github" begins with '.', so its clone directory would be a hidden path … Repositories whose names begin with '.' cannot be attached to this session.` |
| GitHub API (`get_file_contents`) | `Access denied: repository "stegverse-labs/.github" is not configured for this session` |

Anonymous **read** works, which is how everything below was validated. Write
does not, by either transport, and the one documented remedy is refused for this
specific repository name. This is an environment constraint, not a permissions
decision a reviewer can grant from inside the repo.

## 3. Applying it

In a `StegVerse-Labs/.github` checkout:

```bash
python3 register_workspace_canonical_task.py --registry-root .
```

It prints `REGISTERED … vector=10500000114000 generation=261`, or
`ALREADY_REGISTERED` and writes nothing. `--print-only` dumps the four artifacts
without touching the tree.

It writes four surfaces, because the registry keeps a task in four places:

| Surface | Change |
| --- | --- |
| `data/canonical-task-registry.json` | one `tasks[]` row; `generation` 260 → 261 |
| `data/canonical-task-records/STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001.json` | new record |
| `control/task-vectors/STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001.json` | new COSV source state vector, with per-metric evidence |
| `control/task-vector-index.json` | one `tasks[]` row; both coverage counts 117 → 118 |

## 4. Validation actually run

Applied to a clean worktree of `.github` at `origin/main` `495832cd`, then the
registry's own checkers were run.

**The three validators that execute in CI all pass:**

| Validator | Result |
| --- | --- |
| `scripts/validate_task_registration_substrate_resolution.py` | exit 0 |
| `scripts/validate_four_missing_cosv_tracking.py` | exit 0 |
| `scripts/audit_canonical_task_projections.py` | exit 0, `structural_errors: []` |

**Every per-task requirement of the strict validator passes.** Running
`scripts/validate_canonical_work_coordination.py` against the new task in
isolation clears all of: `task_id`, `correlation_id`, uniqueness,
`worker_claim.authority == WORKERCOORDINATOR`, `worker_claim.projection_only is
True`, `runtime_requirements` dict, `runtime_requirements.capabilities` list,
the three boolean runtime flags, and `blockers[].dependency_id ⊆
dependencies[].dependency_id`.

Two of those were **defects in a first draft of this registration**, caught only
because the validator was actually run: `runtime_requirements` was on the record
but not on the registry row, and `dependencies` was a list of strings, which
would have crashed the validator's set comprehension rather than failing closed.
Both are fixed and both are now pinned by tests.

## 5. Three findings about the registry's own gates

Recorded because they were found while validating, and because the first one
means "the validator passes" is not a claim anyone can currently make.

### 5.1 `validate_canonical_work_coordination.py` cannot pass on any commit

It requires five exact phrases in
`docs/CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md`. **All five are
absent from that file.** The string `one canonical work truth and many
projections` occurs in exactly one file in the repository — the validator that
demands it.

So the validator is unpassable by construction, independent of any task.

### 5.2 It also never runs

`grep -rn validate_canonical_work_coordination .github/workflows/` returns
nothing. The validator that enforces the registry's documented canonical
invariants is not wired to any workflow. That is why 5.1 and 5.3 have gone
unobserved.

### 5.3 48 of 93 tasks fail its first per-task check

`worker_claim.authority == "WORKERCOORDINATOR"` is required of every task. The
actual distribution:

| `worker_claim` state | Tasks |
| --- | --- |
| `authority = WORKERCOORDINATOR` (compliant) | 46 |
| field absent entirely — `claim.get("authority")` → `None` → fail | 36 |
| `authority = CURRENT_SESSION` | 9 |
| `authority = CURRENT_SESSION_PLUS_PREAUTHORIZED_BOUNDED_GROUP` | 1 |
| `authority = CURRENT_SESSION_COORDINATION_ONLY` | 1 |
| a bare string `"CURRENT_SESSION"` instead of an object | 1 |

The eleven structured violations name the exact value the invariant forbids.
`TASK_REGISTRY_CANONICAL_INVARIANTS.md` says, verbatim: *"`CURRENT_SESSION`, a
model identity, repository identity, transport identity, or handoff reference
must never be encoded as execution claim/fence authority."* Six of the eleven
also use a `docs/*_MIRROR_HANDOFF.md` path as `claim_ref` — the handoff
reference the same sentence forbids — and ten of the eleven set
`projection_only: false`, asserting a real claim rather than a projection.

The bare-string case is worse than non-compliant: the validator does
`claim.get("authority")` on it, so reaching that task raises `AttributeError`
rather than failing closed.

The affected task ids are listed in the commit for this change. **None of this
was fixed here.** Ten of the eleven are other tasks' records, the fix is a
registry-owner decision per record, and this session cannot deliver it anyway.

This is the same shape as every other defect found in this ecosystem today: the
rule is written down, the checker exists, and nothing runs it.

## 6. The task's own content

`goal` — make WorkSpace the canonical browser representation of MyKV and Org KV,
with capability functions bound to admitted operations, and the single governed
input surface for sensitive material entering the SKAP Vault, such that
WorkSpace state derives entirely from admitted state transitions and stays exact
for the same principal across any browser session, on any operating system, on
any device.

**Five work units**, none with an assigned owner, which is why COSV `U = 5`:

| Work unit | Current state |
| --- | --- |
| `WU1-NO-BROWSER-LOCAL-ROOT-OF-TRUTH` | Violated — Personal path gated on IndexedDB registration; Org path reads `sessionStorage` |
| `WU2-REGISTRATION-RECOVERY-ON-A-NEW-DEVICE` | Absent — without it `node_id` is a physical-device identity gate in effect |
| `WU3-RECEIPT-LINEAGE-SURVIVES-REREGISTRATION` | Absent — re-registration mints a new Receipt #1 |
| `WU4-SECOND-REGISTERED-PLATFORM` | Absent — 6 Apple tasks, 0 Android/Windows/Linux |
| `WU5-WORKSPACE-STORAGE-PERSISTENCE-REQUEST` | Absent — mitigation only, does not discharge WU1 |

**Four blockers**, all `decision_owner: REGISTRY_OWNER`, which is why `B = 4`:
the canonical WorkSpace surface (`workspace.html` vs `my-kv.html`), SKAP ingress
consolidation across the four existing surfaces, whether the WorkSpace KV store
keeps its Google Drive writer, and whether the
`SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004` name collision is resolved by
renaming. Each is represented once as a canonical dependency object and
referenced by its blocker, per the validator's subset rule.

**Twelve evidence predicates**, including three that only an any-OS-any-device
reading would demand: `WORKSPACE_PROJECTION_EXACT_ON_A_SECOND_BROWSER_SESSION_SAME_PRINCIPAL`,
`WORKSPACE_PROJECTION_EXACT_ON_A_DEVICE_THAT_NEVER_HELD_A_REGISTRATION`,
`WORKSPACE_PROJECTION_EXACT_ON_A_SECOND_OPERATING_SYSTEM`.

## 7. The COSV vector, digit by digit

`10500000114000`, symbol order `LRUIVGOCMTBEAP`, width 14, per
`management/COSV_PROFILE_V1.json#task`. Derived by
`register_workspace_canonical_task.derive_vector()` from `EXACT_METRICS`, never
written by hand — a test asserts the two agree, and a second test reproduces
`QUANTUM-RESILIENCE-001`'s published derivation (`10100000100000`) through the
same function.

| Pos | Symbol | Name | Value | Why |
| --- | --- | --- | --- | --- |
| 0 | L | lifecycle | `1` UNCLAIMED | no WorkerCoordinator claim or fence observed |
| 1 | R | archive_ready | `0` | no handoff, evidence package or validation run |
| 2 | U | unassigned_work | `5` | the five work units, none assigned |
| 3 | I | chat_owned_implementation | `0` | no session owns implementation |
| 4 | V | chat_owned_validation | `0` | no session owns validation |
| 5 | G | chat_owned_integration | `0` | no session owns integration |
| 6 | O | chat_owned_observation | `0` | no session owns observation |
| 7 | C | chat_owned_credentials | `0` | credentials remain TV/TVC |
| 8 | M | canonical_owner_installed | `1` | **contested — see below** |
| 9 | T | thread_required | `1` | spans four repositories; four registry-owner decisions |
| 10 | B | blocker_count | `4` | the four decisions |
| 11 | E | evidence_complete | `0` | no predicate satisfied |
| 12 | A | activated | `0` | no runtime activation |
| 13 | P | propagated | `0` | no propagation |

**The one digit a reviewer may reasonably reject is `M`.** All 68 vectored tasks
in the registry set `canonical_owner_installed = 1`, including `PROPOSED` ones
with no claim, which reads as *the registry owner row exists* rather than *a
runtime owner is installed*. On that reading the registration itself installs
it, so `M = 1`. On the stricter reading — no runtime owner exists for WorkSpace,
which is the finding — `M = 0` and the vector is `10500000014000`. Both the
metric evidence and a test name the alternative, so the disagreement is visible
rather than buried.

## 8. What this does not do

- **It does not activate anything.** `PROPOSED`, `UNCLAIMED`,
  `authority_effect: NONE_COORDINATION_REGISTRATION_ONLY`.
- **It does not claim a runtime observation of WorkSpace.** Nothing here was run
  against a live KV, browser, or device.
- **It does not assert the seven-day eviction as observed.** A nonclaim says so
  explicitly; it remains cited published platform policy until someone observes
  it on a device.
- **It does not supersede the Site claim.** `SITE-WORKSPACE-INTEROPERABILITY-001`
  stays the Site-side implementation claim; this is the canonical coordination
  owner its `task_id` never resolved to, and its own
  `next_task_after_release` names this task's WU1.
- **It does not fix the 48 failing `worker_claim` records**, the unpassable
  validator, or wire that validator into CI. Each is a registry-owner decision,
  and none is deliverable from here.
