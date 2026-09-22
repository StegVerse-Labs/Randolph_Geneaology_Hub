# InTr lifecycle closure: the last receipt

Status: built and verified. CVK change is PR #221; the `.github` wiring ships
as a patch because that repository cannot be attached to a session.

## What was missing

An InTr materialization crosses three boundaries:

1. the browser writes a write-once outbox entry and triggers the root service
   worker (`stegos.node_intr_outbox_entry.v1`);
2. the far-end ingress admits it (`INGRESS_ADMITTED`);
3. the consumer runs and reports `MATERIALIZATION_EXECUTION_ATTEMPTED`.

**Attempted is not recorded.** No terminal receipt was ever produced.

That explains an otherwise puzzling observation: searching every repository in
the ecosystem, `runtime_materialization_observed`, `receiver_receipt_observed`
and `tvc_receipt_observed` are *never set true anywhere*. The only matches are
negative assertions in `site/tests/test_stegos_node_projection.py:384-386`
forbidding the emitting side from claiming them. That guard is correct — the
sender must not fabricate a reply. But the receiving side had no artifact to
assert with either. Not a forgotten writer; a missing contract.

A second defect compounded it: the far end validated the node's outbox entry
digest in memory and then discarded the artifact. Stage one could not be
reconstructed from stored evidence even in principle.

## What it cost

From continuity-vault-kit's own readiness facts:

```
Universal Interlock adoption review state: BLOCKED
blockers: AUTHENTIC_RUNTIME_BINDING_MISSING
          MASTER_RECORDS_CUSTODY_RECEIPT_MISSING
          MASTER_RECORDS_RECONSTRUCTION_NOT_VERIFIED
```

Running `scripts/evaluate_kv_activation_readiness.py`:

```
46 entries (13 modules + 33 personal services)
install_state:             INSTALLED_INACTIVE  46/46
governed_action_readiness: BLOCKED             46/46

blocker frequency:
  46  production_interlock_runtime_activated
  46  transport_capability:DEVICE_KV_INTR
  29  provider_session_evidence_observed
```

Two of the three Universal Interlock blockers are the missing terminal
receipt. It gates `production_interlock_runtime_activated`, which gates all 46
— StegID, StegTalk, StegWallet/Pay, genealogy, Auri, family sharing, the rest.
One writer, 46 entries.

## What was built

**`continuity-vault-kit/runtime/intr_lifecycle_closure.py`** (PR #221) — the
canonical closure. It records; it does not execute and cannot grant authority.

- Every stage digest is recomputed from the stored artifact and must equal the
  digest that artifact carries. That is the reconstruction the readiness facts
  ask for, performed rather than asserted.
- Each stage names its immediate predecessor's receipt.
- A chain that does not close is refused naming the stage that broke it.
- Reuses `runtime/secret_field_policy` so `credential_authority: "TV/TVC"` and
  its siblings survive the secret scan instead of being read as the danger
  they exist to deny.
- Refuses any stage claiming execution authority or a minted claim/fence.

The promoted observations are emitted as a **separate far-end record**, never
written back into the node's write-once entry. Only the side where the receipt
exists may state that the receiver replied. `tvc_receipt_observed` stays false
with a stated reason — a different provider boundary this closure does not
cross.

**`patches/github-intr-lifecycle-closure.patch`** — the `.github` wiring:

- `workers/stegbrowser_intr_materialization_ingress.py` retains the admitted
  outbox entry write-once, so stage one becomes reconstructable;
- `workers/close_stegbrowser_intr_lifecycle.py` loads the canonical closure
  from the current KV source root — the same convention the Workspace
  DEVICE_KV extension uses for `runtime/workspace_projection.py` — and
  persists the terminal receipt, the Master Records custody record and the
  far-end observation;
- `tests/test_stegbrowser_intr_lifecycle_closure_wiring.py` covers it.

The closure logic is not reimplemented in `.github`. One implementation, so
the two InTr clients cannot drift apart.

## Convergence with the SDK, proven

The terminal shape matches the contract the StegVerse SDK already enforces for
the *other* InTr client (`stegverse/manifest_state_transition_runtime.py`,
`validate_runtime_result`): ordered `RECORDED` closures, `replay_status` and
`reconstruction_status` PASS, terminal state `records_only` with no continued
authority. Two clients of one runtime should not disagree about what
"finished" means.

Running the SDK's own `_validate_transition_closures` over the receipt this
module builds:

```
CVK REQUIRED_CLOSURE == SDK _REQUIRED_CLOSURE: True
SDK validator over CVK terminal receipt: PASS
negative control: SDK rejects broken link ->
  MASTER_RECORDS_IMMEDIATE_PREDECESSOR_MISMATCH:MATERIALIZATION_EXECUTION_ATTEMPTED
negative control 2: SDK rejects non-RECORDED ->
  MASTER_RECORDS_CLOSURE_REQUIRED:NODE_OUTBOX_ENTRY_WRITTEN:state
```

## Verification

- CVK: 27 new tests; full suite **742 passed**; compile gate over every
  runtime module passes.
- `.github`: 8 wiring tests; end-to-end run against a simulated runtime root
  produced a verifying terminal receipt with
  `receiver_receipt_observed: true` and
  `runtime_materialization_observed: true` — the flags nothing in the
  ecosystem could previously set.
- Idempotent re-run is write-once stable; a tampered retained entry is refused
  with `NODE_OUTBOX_ENTRY_WRITTEN:digest_reconstruction_mismatch`.
- Patch applied to a pristine clone: 29 tests pass there.
- The 10 pre-existing `tests/test_stegbrowser_*` failures in `.github`
  reproduce identically with these changes stashed and are unrelated.

## Not claimed

This records a transition that already occurred. It does not claim the
materialized work succeeded — only that it was attempted and recorded. It does
not itself flip `production_interlock_runtime_activated`; that remains an
observation the organization control plane makes once these receipts exist.
The second universal blocker, `transport_capability:DEVICE_KV_INTR`, is a
separate piece of work.

## Applying the patch

From the root of a `StegVerse-Labs/.github` checkout:

    git apply patches/github-intr-lifecycle-closure.patch
    STEGVERSE_KV_SOURCE_ROOT=<path to continuity-vault-kit> \
      python -m pytest -q tests/test_stegbrowser_intr_lifecycle_closure_wiring.py
