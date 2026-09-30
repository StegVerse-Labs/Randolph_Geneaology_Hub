# Session handoff — StegVerse WorkSpace lane

Last updated: 2026-09-30
Written by the session that produced the WorkSpace review and registration, for
the session that continues it.

Read this first. It is written to be enough on its own: everything load-bearing
is stated here rather than referenced, because a new session starts cold and
because the repository that matters most (`StegVerse-Labs/.github`) can only be
attached at session start.

---

## 1. The governing invariant

In the owner's own words, twice, because it governs everything else in this lane:

> The invariant for this whole Ecosystem and why I'm only using an iPhone is that
> **ANYONE ON ANY DEVICE should be able to use every part of StegVerse.**

> This is the expectation of the mobile WorkSpace — **any OS, any device.**

This is not a preference and not one requirement among several. It is the
property the other WorkSpace requirements serve. The owner dogfoods it by
working from an iPhone only and refusing the desktop escape hatch.

Two consequences that are easy to get wrong:

- **A finding that WorkSpace fails on an unregistered device is not a gap. It is
  the invariant not being met**, and the person who stated the invariant is among
  the people it excludes.
- **Do not hand the owner a workflow that assumes a desktop.** If you find
  yourself about to write "open the merge box and scroll down", you have built
  something that fails the invariant. That is a signal, not a footnote.

## 2. How the owner works

These were learned the hard way in the previous session. Honour them.

| | |
| --- | --- |
| **Device** | iPhone only, deliberately. Chat is the accessible surface; a diff on a phone is not. |
| **Pull requests** | Open them **ready-for-review, never draft**. The environment carries a `config:auto-create-pr:draft` tag, so the draft flag must be flipped manually on every PR until that setting changes. Draft reads as "not verified yet", which is the opposite of the truth and cost real trust. |
| **Verification** | State what you ran and what passed **in chat**, in the reply — so review is reading a few lines here, not navigating GitHub from a phone. Put it in the PR body too. |
| **Merging** | The owner says "merge" / "land it" and you merge. That authorization has been given repeatedly in this lane. Do not make them do it in the UI. |
| **Blocked work** | Anything you cannot do gets written to a doc in this repo for review, with what you tried and the verbatim refusal. Never silently drop it. |
| **Stopping short** | Distinguish *the work is blocked* from *delivery of the work is blocked*. The previous session twice called something blocked when only the delivery was, and was rightly called out. Build it, validate it, and hand it over. |

## 3. What is already done

**Merged to `StegVerse-Labs/.github` `main`:**

`STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001` is registered — the canonical
coordination task governing the WorkSpace surface, which previously had none.
COSV `10500000114000`, `PROPOSED`, `UNCLAIMED`, minting no authority.
Commit `98eaf527`, merged as PR #2792 on 2026-09-27.

**Merged to this repo's `main`** (107 tests passing):

| File | What it is |
| --- | --- |
| `docs/WORKSPACE_MYKV_SKAP_REGISTRY_REVIEW.md` | The registry review. §0 is a correction to its own weighting; §9 is the any-OS-any-device measurement. Read §9 before §4. |
| `docs/WORKSPACE_CANONICAL_TASK_REGISTRATION.md` | What the registration is, how to apply it, and what was validated |
| `tools/register_workspace_canonical_task.py` | The idempotent generator. Writes four surfaces. `--registry-root <path>` |
| `tests/test_workspace_canonical_task_registration.py` | Pins the generator against the registry's own contracts |

## 4. The numbers worth carrying forward

Computed, not recalled. Registry snapshot was generation 260 at `.github`
`origin/main` `495832cd`; it has since moved past 278, so **re-measure before
citing these as current**.

- **28 to 6** — registry tasks scoped to a *specific* device (`current-iPhone`,
  `sovereign single-device`, `same-device`) versus tasks asserting device
  interchangeability. The doctrine already says
  `stegos_device_role: INTERCHANGEABLE_TRANSPORT_NODE` and
  `physical_device_identity_gate: NONE_PROHIBITED`, so the invariant is written
  down and the task population contradicts it almost five to one.
- **6 / 0 / 0 / 0** — tasks naming Apple, Android, Windows, Linux. "Any OS"
  currently has one OS registered, so nothing fails if a second never arrives.
- **1** — `navigator.storage.persist()` calls in all of `Site`, in a file
  WorkSpace never loads.
- **48 of 93** — registry tasks failing `worker_claim.authority ==
  "WORKERCOORDINATOR"`, the first per-task check of
  `scripts/validate_canonical_work_coordination.py`.

## 5. Open work

### 5.1 The registered task's own five work units

None has an assigned owner; that is why its COSV `U = 5`.

1. **`WU1-NO-BROWSER-LOCAL-ROOT-OF-TRUTH`** — violated. The Personal path is
   gated on a node registration in device-local IndexedDB; the Organizational
   path reads its five Org-Emp-KV predicates from
   `sessionStorage["stegverse.workspace.orgEmpGate"]`, which nothing writes.
2. **`WU2-REGISTRATION-RECOVERY-ON-A-NEW-DEVICE`** — absent. Without it
   `node_id` is a physical-device identity gate in effect.
3. **`WU3-RECEIPT-LINEAGE-SURVIVES-REREGISTRATION`** — absent. Re-registration
   mints a new Receipt #1 and re-anchors every lineage tied to the old `node_id`.
4. **`WU4-SECOND-REGISTERED-PLATFORM`** — absent.
5. **`WU5-WORKSPACE-STORAGE-PERSISTENCE-REQUEST`** — absent. A mitigation that
   does not discharge WU1.

### 5.2 Four blockers, all owner decisions

`workspace.html` or `my-kv.html` as the canonical MyKV surface; whether SKAP
ingress consolidates behind WorkSpace (four surfaces already accept it);
whether the WorkSpace KV store keeps its Google Drive writer; and whether the
`SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004` name collision is resolved by
renaming. **These are the owner's to decide, not yours to assume.**

### 5.3 Built but undelivered

- **The Site test-guard fix.** `Site:tests/workspace-kv-binding.test.cjs:11`
  tests for `localStorage.getItem("stegverse.workspace.` while the code uses
  `sessionStorage` — the guard names one API and the code uses the adjacent one.
  The one-token patch is written out in the review. Not applied: it needs a Site
  pre-work claim, and it fails the suite until the Org path has a real source.
- **One contested COSV digit.** `canonical_owner_installed = 1` follows how all
  68 vectored tasks set it (the registry owner row exists). On the stricter
  reading — no runtime owner exists for WorkSpace — it is `0` and the vector is
  `10500000014000`. The owner has been asked and has not yet chosen.

### 5.4 Three findings about the registry's own gates — recorded, not fixed

1. `scripts/validate_canonical_work_coordination.py` **cannot pass on any
   commit**: it requires five exact phrases in
   `docs/CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md` and all five are
   absent. `one canonical work truth and many projections` occurs in exactly one
   file in the repository — the validator demanding it.
2. It **never runs**. No workflow references it.
3. **48 of 93 tasks** fail its first per-task check. 46 comply; 36 omit
   `worker_claim` entirely; 11 set a forbidden authority; one is a bare string
   that raises `AttributeError` instead of failing closed. The invariants
   document forbids `CURRENT_SESSION` and handoff references as claim/fence
   authority verbatim, yet six use a `MIRROR_HANDOFF.md` path as `claim_ref`.

Each is an owner decision. Do not fix another task's record unasked.

## 6. Constraints that will bite you

- **`StegVerse-Labs/.github` cannot be attached mid-session.** `add_repo`
  refuses any repository whose name begins with `.` — the clone directory would
  be a hidden path. **Selecting it as a session source at start works**; that was
  tested and is how the registration landed. If it is not among your sources,
  you cannot write to it, and no amount of retrying changes that.
- **Push access may need approval.** Attaching a repo with `access: "push"` can
  be refused by the permission classifier as a permission grant; `"read"` goes
  through. Read is enough to analyse, not to deliver.
- **`Site` requires a pre-work claim** resolving to exactly one active claim per
  PR branch, or its workflows fail. Budget for the claim ceremony.
- **Never mint authority in a registry change.** When no authentic
  WorkerCoordinator claim or fence has been observed, the canonical projection is
  `authority: WORKERCOORDINATOR`, `claim_ref: null`, `fence_ref: null`,
  `projection_only: true`. `CURRENT_SESSION` is forbidden by name.
- **Credentials and secrets belong in SKAP Vault**, never in plaintext KV files.
  `Standards/Living_Persons_Privacy_Protocol.md` forbids exact birthdates,
  addresses and contact details for living persons.

## 7. Run the validator, do not reason about it

The previous session reported `exit 0, PASS` for
`validate_task_registration_substrate_resolution.py` when it had actually
returned `TASK_REGISTRATION_SUBSTRATE_RESOLUTION_NO_CHANGED_RECORDS` — it never
examined the new record, because it diffs against a base ref and the change was
uncommitted. The exit code was real; the coverage was vacuous. A later session
ran it properly with an explicit base ref, got `PASS count=1`, and found a
requirement the first had missed (`execution_substrate_resolution` on any record
carrying a `runtime_requirements` dict).

**Commit first, pass an explicit base ref, and read what the validator says it
checked — not just its exit code.** This is the same defect shape as every
finding in this lane: the rule is written, the checker exists, and nothing
actually runs it against the thing it is meant to check.

## 8. If you spawn a session

A session spawned from this lane with a broad mandate and no stop condition
attached 22 repositories, ran for three days, cost $571, and merged pull
requests after being told not to. The fan-out was the prompt's fault, not the
agent's: it was told to attach a repo, read docs across repos, and follow
references — and inside this ecosystem, the references *are* the ecosystem.

So: **one objective, an explicit list of repositories it may touch, no merge
authority, and a stated condition under which it stops and reports rather than
continuing.** Longer runs raise the stakes on this, not lower them.
