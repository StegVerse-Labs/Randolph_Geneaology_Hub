# Organization state-transition recording gap

Status: diagnosed, fix built and verified, delivery blocked on repository access.
Target repository: `StegVerse-Labs/.github`.

## What was asked

Find why a class of tasks in the canonical task registry cannot be completed,
on the stated premise that state transition receipts are not being recorded at
the organization and Master Records levels, and that state transitions *are*
the runtime — so the right move is to trace receipts until one is not what the
next transition requires, and then allow or deny.

## What the trace found

The receipts exist. The recorder does not.

1. **The canonical allocator runs and produces a signed transition.**
   `scripts/allocate_claims.py` and its portable projection
   `org_allocator/portable_allocator.js` both compute a complete claim
   transition and emit `stegverse.org-allocator-portable-receipt/v1`.

2. **All three surfaces that run it throw the result away.**
   - The CI workflow `org-control-plane-validate.yml` runs the allocator under
     the step *"Exercise allocator deterministically without persistence
     authority"*, then states in its own log line that the mutations are
     runner-local and never committed. The workflow has `permissions: {}`, no
     checkout action and no token, so it structurally cannot record anything.
   - `scripts/consume_org_claim_allocator_request.py` runs the allocator
     against a separate `--runtime-root` and retains grant evidence *there*,
     not in the organization repository.
   - The user's device ran it and persisted the receipt into a hash-chained
     node journal on the device.

3. **The organization repository therefore never advanced.**
   `control/claims-active.json` sits at generation 2 with `"claims": []`.

4. **The heartbeat consequently has nothing to assert.**
   `heartbeat_runtime/org_assertions.py` iterates the active claims. With none,
   it issues none. That is directly visible: every one of the 26
   `organization_assertions_issued` events in `events/heartbeat-runtime.jsonl`
   (epochs 4 through 29) carries `"issued_count": 0, "issued_refs": []`.

5. **So nothing reaches the organization event log or Master Records.**
   `events/org-events.jsonl` holds one line — the generation-0 bootstrap.
   `workloads/master-records/` holds one record, written by an unrelated
   worker-lifecycle lane.

The important correction to the earlier working assumption: there are **no
unrecorded assertions to replay**. The 26 events are not receipts that went
unrecorded; they are 26 records of an issuer that had nothing to issue.
Replaying them would fabricate organization state that no allocator produced.

## The device receipt is real and verifies

`evidence/global-runtime-evidence-closure-001/original/stegverse-org-allocator-TASK-2026-0011-G7-v2.json`
carries a transition executed on the user's device on 2026-09-11:

- node `stegnode-web-2d6daa94e496d451d16bd5619bd30a25`,
  device `stegdevice-0d0f5403f48ff804fb3d31fb346e748c94e395bc`
- selected `TASK-2026-0011`, claim registry generation 7, fencing token 7
- node journal sequence 67, replay `PASS` over 67 entries

Four recorded digests were recomputed independently in Python against the
canonicalization used by `portable_allocator.js`, and all four match exactly:
the allocator receipt hash, the claim snapshot hash, the journal receipt hash
and the journal entry hash. The receipt closes with
`allocator_mutation_performed: false`, `authority_effect: NONE_EVIDENCE_ONLY` —
the device did the transition and the organization never admitted it.

## What was built

`scripts/admit_org_allocator_transition_receipt.py` — the missing recorder.

It never allocates and cannot create claim authority. It admits a receipt the
canonical allocator already signed, and fails closed on anything it cannot
verify:

- receipt schema, state and `receipt_sha256` recomputed over the canonical body
- the allocator's governance assertions, each checked by name
  (`credential_authority: TV/TVC`, `github_token_runtime_authority: NONE`,
  `heartbeat_grants_claim_authority: false`, and the rest)
- a secret-bearing-field scan with the governance-assertion allow-list, so the
  fields that prove no credential is present are not themselves refused
- claim snapshot digest, when a grant observation accompanies the receipt
- fencing token agreement with the claim registry generation
- generation continuity against recorded state

On admission it appends the organization event to `events/org-events.jsonl`,
advances `control/claims-active.json`, sets the task active, and writes a
Master Records custody record under
`workloads/master-records/orchestration/custody/org-allocation/`, shaped after
the one custody record the repository already holds. The organization event
carries the Master Records reference and record hash, so the two levels are
linked rather than merely parallel. Admission is idempotent on
`receipt_sha256`.

## Denial is the first result, and it is the useful one

Run against the real device evidence, the admitter denies:

```
"deny_reason": "GENERATION_GAP",
"recorded_generation": 2,
"receipt_generation": 7,
"missing_generations": [3, 4, 5, 6]
```

The device advanced 2 → 7 across five allocations. Only generation 7's evidence
was ever recovered into the repository. Generations 3, 4, 5 and 6 exist only in
the device's node journal.

This is the requested behaviour rather than a failure: trace the receipts, and
where the next transition receipt is not what continuity requires, deny and say
exactly what is missing. Stepping over the gap would invent four organization
state transitions.

## The next step is an export, not more code

The 67-entry node journal on the device holds the generation 3–6 receipts.
Exported the same way the peer export was, they replay in one command:

```
python scripts/admit_org_allocator_transition_receipt.py \
    <journal entries G3..G7> --apply --source-commit <commit>
```

The admitter sorts by generation, admits contiguously, and stops at the first
gap. Once generations 3–7 are recorded, `control/claims-active.json` carries
live claims, the heartbeat issues organization assertions again instead of
`issued_count: 0`, and each admitted transition lands a Master Records record.

That chain is pinned by test, not asserted: `test_no_claims_means_no_assertions`
shows the current state issues nothing, and `test_admission_restores_assertion_issuance`
shows that after admission `issue_claim_assertions` produces a real assertion
carrying the admitted fencing token.

## Verification

19 tests, all passing, covering receipt integrity against the real device
evidence, device provenance carry-through, generation continuity and gap
denial, admission recording at both levels, idempotency, dry-run purity,
tamper and resealed-tamper denial, governance assertion enforcement, secret
field denial, and the heartbeat lane restoration above.

The patch was applied to a pristine clone and the suite re-run there. The
pre-existing `validate_workflow_surface_hygiene.py` failure over nine
unregistered workflow files reproduces identically without this change and is
unrelated to it.

## Delivery

`StegVerse-Labs/.github` cannot be attached to a session — `add_repo` rejects
the leading-dot repository name, and the GitHub tools are gated by the same
allowlist. The change is therefore delivered as a verified patch:

    patches/github-org-transition-admitter.patch

Apply from the root of a `StegVerse-Labs/.github` checkout:

    git apply patches/github-org-transition-admitter.patch
    python -m unittest tests.test_org_allocator_transition_admission -v

It adds `scripts/admit_org_allocator_transition_receipt.py` and
`tests/test_org_allocator_transition_admission.py`, and adds two reporting
steps to `.github/workflows/org-control-plane-validate.yml` — the test run, and
a non-authorizing report of unrecorded canonical allocator transitions. The
workflow keeps `permissions: {}` and admits nothing; the guard step proving it
holds no authority-bearing constructs still passes.
