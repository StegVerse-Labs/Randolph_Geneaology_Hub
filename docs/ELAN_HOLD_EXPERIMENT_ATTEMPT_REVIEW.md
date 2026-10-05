# Review of the ELAN HOLD experiment attempt record

Reviews `ELAN-HOLD-EXPERIMENT-ATTEMPT-REVIEW-20261005`
(`data/hold-experiment/ELAN_HOLD_EXPERIMENT_ATTEMPT_REVIEW_20261005.json`)
against `StegVerse-org/StegVerse-SDK` at the commit it names, `eacc19ee`.

You can re-run the checks with `tools/probe_hold_evaluator.py`. It reads source and never
imports or executes SDK code.

## Summary

The record's discipline holds. It keeps manifest construction, SDK handoff and
InTr admission apart, and it claims nothing for T0–T4. Three of its factual
premises do not match the source it cites:

1. **The evaluator does not implement the experiment the record specifies.**
   T2–T4 differ.
2. **At `eacc19ee` the T0 path cannot reach the SDK handoff the record reports.**
   It fails closed one boundary earlier, inside the SDK.
3. **Every condition carries the same authority state.** HOLD is a label in the
   payload, not an authority-state difference.

So the stated first unsatisfied predicate is one boundary too far. The
continuation also aims at a handoff that the reviewed code does not generate.

## Finding 1 — three different T0–T4 designs

| | Record (spec) | `run_independent_hold_evaluator.py` | `experiment_sv_hold_independent.py` |
| --- | --- | --- | --- |
| T0 | BASELINE | BASELINE | PRE_HOLD |
| T1 | HOLD_ENTERED | HOLD_ENTERED | HOLD_ENTERED |
| T2 | **ACTION_DURING_HOLD** | HOLD_PERSISTENCE | HOLD_PERSISTENCE_AFTER_TIME_ADVANCE |
| T3 | **HOLD_RELEASED** | UNAUTHORIZED_RESUME | RESUME_PROPOSED_WITHOUT_FRESH_DELEGATION |
| T4 | **POST_HOLD** | AUTHORIZED_RESUME | RESUME_PROPOSED_WITH_NEW_DECLARED_DELEGATION |

The record's design is *attempt the action under HOLD, release HOLD, repeat the
action*. The evaluator's design is *HOLD persists over time, resume is attempted
without authority, then with it*. Neither evaluator has an explicit release step
(record T3) or a controlled action attempted during HOLD (record T2). The record's
`comparison_rule` therefore cannot be applied to evidence that this evaluator
produces. Running T1–T4 "unchanged", as `on_success` directs, would run the
evaluator's experiment and not the record's.

## Finding 2 — T0 fails closed before the handoff

The record's sequence 3 is `HANDOFF_T0_TOWARD_INTERLOCK_INTR: SDK_HANDOFF_REPORTED`.
At `eacc19ee` the source does not allow that:

- `manifest_declared_destination()` has been an inert shim returning `None` since
  `2213239` ("Fail closed until canonical organization endpoint resolves",
  2026-10-01).
- The evaluator calls `execute_manifest(manifest)` with no `organization_boundary`.
  That parameter is the canonical route added in `7a924fb` (2026-10-02).
- With no destination, `build_intr_handoff` returns `_destination_not_declared`:
  `disposition: FAIL_CLOSED`, `evaluation_boundary: SDK_ORGANIZATION_DESTINATION_RESOLUTION`,
  `failed_predicate: REGISTERED_CAPABILITY_RESOLVES_TO_CANONICAL_ORGANIZATION_GITHUB_INGRESS_ENDPOINT`.
- The evaluator asserts `result["evaluation_boundary"] == "SDK_MANIFEST_HANDOFF"`
  (line 55). At this commit that assertion fails, so the script exits before it
  writes `results.json`.

The evaluator was last changed in `4534b5a`, before `2213239` on the same day. Its
workflow only re-runs on PRs that touch the evaluator or the workflow, so the
runtime change never re-ran it. Any "handoff reported" observation must therefore
come from a run on an earlier commit, not from `eacc19ee`. As a control, the
probe passes this check against `4534b5a`.

*Basis:* static reading, cross-checked by the probe. I did not execute the
evaluator in this session, because running external SDK code was not permitted
here. Running `python -m scripts.run_independent_hold_evaluator` at `eacc19ee` is
the direct confirmation: expect an `AssertionError` at line 55.

**Narrower first unsatisfied predicate:**

```text
REGISTERED_CAPABILITY_RESOLVES_TO_CANONICAL_ORGANIZATION_GITHUB_INGRESS_ENDPOINT
  boundary: SDK_ORGANIZATION_DESTINATION_RESOLUTION   (SDK-local, before any InTr contact)
```

The record's `AUTHENTIC_T0_INTR_ADMISSION_AND_HOLD_TRANSITION_OBSERVATION_NOT_ESTABLISHED`
is still true, but it comes after this predicate.

## Finding 3 — HOLD is a label, not an authority state

Every condition builds its manifest with `processor_request=governance_request()`,
imported from `tests/test_manifest_builder.py`. It is the same fixture each time,
with `actor_authority_current: True` and target `source-native-object`. The only
per-condition difference is the payload (`requested_transition: "HOLD_ENTERED"`
etc.). The design fixture does vary an `authority_declaration` per condition, but
the evaluator does not use it.

That leaves T1 with no explicit HOLD invocation in any authority-bearing field.
The record's prohibited promotion "do not infer HOLD from silence" is not violated,
but HOLD is not invoked either; it is only named.

## Smaller points

- **Disposition the evaluator emits vs the record.** When T0 does reach the
  handoff, the evaluator writes `disposition: "ALLOW"` with `failed_predicate: None`.
  That is the SDK's handoff disposition. The record correctly reports
  `FAIL_CLOSED`, but the evaluator's own artifact invites the promotion the record
  prohibits. T1–T4 get `NOT_ATTEMPTED_PREDECESSOR_NOT_ADMITTED`, which is outside
  the `ALLOW | DENY | FAIL_CLOSED` vocabulary in `evidence_requirements`, and
  `failed_predicate: T0_ADMISSION_NOT_OBSERVED`, whose name differs from the
  record's.
- **Task/COSV correlation is payload-only.** `ELAN-PAPER-COAUTHOR-PUBLICATION-001`
  and `71000000100100` appear only as `goal_task_id`/`cosv` in the payload. The
  governance adapter sets `canonical_task_id` from an organization batch binding,
  which is absent here, so the handoff's `canonical_task_id` is `null`.
- **Two manifest hashes.** The evaluator's `manifest_sha256` is its own hash of
  the manifest dict. The SDK binds `canonical_manifest_sha256` and
  `wire_manifest_sha256`. A reconstruction needs to know which hash is the identity.
- **Evidence retention.** The evidence is a CI artifact, which expires.
  `created_at` is fixed at `2026-09-27T00:00:00Z` for every condition. The same
  shape is described in `SDK_EVALUATOR_RUNTIME_PROOF_BLOCKER.md`.
- **The handoff is never transported.** Even when it is produced, it has
  `receiver_contacted: false` and `transport_performed_by_sdk: false`. The "already-generated
  T0 handoff" exists only as a local dict in an artifact. Nothing carries it to
  InTr, so "trace it into the receiving operation" needs a caller. The design
  fixture names that caller `REQUIRES_SEPARATELY_AUTHORIZED_LIVE_CALLER`.

## Answers to the record's review questions

| Question | Answer |
| --- | --- |
| T0 represents the pre-HOLD baseline? | As specified, yes. As implemented, T0's authority state is a test fixture shared by every condition, so it is not a distinct baseline. |
| T1 requires explicit HOLD invocation? | Spec: yes. Implementation: no. HOLD is a payload label only (Finding 3). |
| T2 isolates behavior during HOLD? | Spec: yes. Implementation: T2 is "HOLD persistence over time" with no controlled action (Finding 1). |
| T3 requires explicit release? | Spec: yes. Implementation: there is no release step; T3 is an unauthorized resume (Finding 1). |
| T4 is a valid post-release comparison? | Not against the evaluator's T4 (authorized resume). That needs the spec's T2 and T3 to exist first. |
| Handoff and admission kept separate? | Yes, in both the record and the SDK (`intr_admission_observed: false`). The evaluator's `ALLOW` label weakens that in its artifact. |
| First predicate narrow enough? | No. It sits one boundary past the actual failure (Finding 2). |
| Evidence permits independent T0–T4 reconstruction? | No. The conditions don't match, the artifacts expire, task/COSV binding is payload-only, and the hash identity is ambiguous. |

## Proposed continuation (for the owner to decide)

Within the record's own scope (no new ingress, no HOLD redesign):

1. **Reconcile the condition set first.** Choose the record's T0–T4 or the
   evaluator's. Until then, nothing T1–T4 produces answers the record's question.
2. **Repair T0 at the actual boundary.** Pass the canonical
   `organization_boundary` to `execute_manifest`, as `7a924fb` provides.
   `resolve_organization_ingress` requires it to come from the organization's
   `<org>/.github` with an `sdk-manifest-ingress` / `SDK:ManifestIngress` /
   `SUBMIT_MANIFEST` binding. If no such binding exists, the result is `FAIL_CLOSED`
   on the predicate above, and that should be recorded as the T0 disposition.
3. **Add `stegverse/manifest_state_transition_runtime.py` to the workflow's path
   filter**, so a runtime change re-runs the evaluator.
4. Only after an authentic InTr admission is observed does the record's existing
   continuation apply.

## Not claimed

This review makes no claims about any runtime. Nothing was executed against the
SDK, nothing was sent to InTr or ÉLAN, and no workflow run was inspected; workflow
artifacts cannot be reached from this session. Every finding is a statement about
source at a named commit, and the probe re-checks it.
