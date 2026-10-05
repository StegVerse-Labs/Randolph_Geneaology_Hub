# Handoff — run the ELAN experiment end to end

Written 2026-10-05 for the next session. Do this, in this order, and don't stop
to ask the owner questions this note already answers.

## What the owner wants

An LLM submits the experiment declaration
(`data/hold-experiment/ELAN_HOLD_EXPERIMENT_ATTEMPT_REVIEW_20261005.json`)
through **LLM-adapter**. LLM-adapter is **only the transport** between the LLM
and the SDK. The SDK manifest builder builds the manifest, and the experiment
runs through the generic chain to an authentic governance disposition. "HOLD" is
just the experiment's name. Nothing in code should be HOLD-specific. Where the
chain can't do this, **fix the chain**.

## What was proven in the previous session (local source execution, not runtime)

Running the declaration through the generic chain:

| Stage | Result |
|---|---|
| builder, no processor request | refused: `--processor-request is required` |
| builder with request derived from the declaration | ok |
| SDK `execute_manifest(manifest, org boundary)` | `ALLOW` at `SDK_MANIFEST_HANDOFF` |
| org `organization_manifest_ingress.receive`, egress `LLM_ADAPTER` | `FAIL_CLOSED`, `declared-capability-not-admitted-by-service:governance` |
| same, egress `BOUNDARY_DIAGNOSTIC` | crossing completes, repo + org receipts written; then `GOVERNANCE_RESULT_DISPOSITION_INVALID` |

`BOUNDARY_DIAGNOSTIC` was only a probe. It is **not** a fix: `LLM_ADAPTER` is the
correct return path.

### First governance decision (later the same day)

With the four canonical packages at hand (SDK `main`, StegCore `main` `bf41bd4`,
core-lite `72bdb0f`, master-records/orchestration `0331223`), the declaration's
parameter sections (`goal`, `experimental_question`, `conditions`,
`evidence_requirements`) were built into a governance manifest and run through
`stegverse.governance_ingress_runtime.run_external_manifest`:

```text
T0  DENY  signal.inputs_incomplete   (StegCore StegGate three-layer decision)
    route stegverse.route.canonical-governed.v1, 10 transitions, chain verified
    no external side effect
```

The DENY is correct for what was submitted: the declaration carries no
authenticated authority grant, so `authenticated_current_grant` is missing. T0 can
only be ALLOW when the submission carries a real TV/TVC grant.

This was called directly in the container. It did **not** enter or leave through
`StegVerse-org/.github`, which is required. Found along the way:

- The `implementation_under_review` section has a `workflow` key. Public
  inspection refuses any key containing `workflow`, `script`, `code`, `command`,
  `token` and similar. That section describes an old evaluator, not experiment
  parameters, so only the parameter sections were submitted.
- The SDK pins StegCore at `ef38410`, which lacks `pre_execution_observer`, an
  argument SDK `main` passes. The pin must move to `bf41bd4` or later.
- **The owner's rule: Master Records must not be involved.** The SDK governance
  route writes Master Records custody on every run (`run_sovereign_validation`),
  and `_validate_governance_runtime_result` requires
  `organization_master_records_closure_observed`. Both must come out of the
  governance path.

## The three fixes

1. **SDK (`StegVerse-org/StegVerse-SDK`, `stegverse/manifest_builder.py`).** When
   `process == "governance"` and no processor request is supplied, derive it from
   the submitted declaration, granting nothing: the declaration's sha256 is the
   only admitted signal, `actor_authority_current: false`,
   `delegation_current: false`, `permission_present: false`,
   `missing_inputs: ["authenticated_current_grant"]`. Make the CLI accept no
   `--processor-request` for governance. Leave the egress default as `LLM_ADAPTER`.
2. **Org ingress (`StegVerse-org/.github`).** `resident-runtime/sdk_manifest_crossing.py`
   resolves `completion.egress.final_stegverse_transition_surface` as the
   *processing* endpoint. It must route processing by the manifest's declared
   `processing.capability` (governance), and use the egress surface only as the
   return path.
3. **Org ingress, governance decision.** `organization_manifest_ingress.runtime_result`
   returns no `disposition`. It must call the canonical governance evaluator
   (`stegverse.sovereign_validation_runtime.run_sovereign_validation`, which needs
   `core_lite` from `Data-Continuation/core-lite@72bdb0f110031ccc2cd98b8ebb7c22b1ab7326f8`)
   and return the result in the shape `_validate_governance_runtime_result` in the
   SDK's `manifest_state_transition_runtime.py` checks.

4. **SDK pin.** Move `stegcore` in `pyproject.toml` to StegCore `bf41bd4` or later.
5. **Remove Master Records from the governance path** (owner's rule). Remove the
   custody write from the governance route, and remove the
   `organization_master_records_closure_observed` requirement from the SDK's
   governance result validator.

All organization ingress and egress goes through `StegVerse-org/.github`. Then
run the declaration through the chain and report T0's actual disposition.

## Access

GitHub access is already granted: `list_repos` shows `can_push: true` for
`StegVerse-org/.github`, `Data-Continuation/core-lite` and the SDK. The previous
session was blocked only by its Auto-mode safety check: attaching the SDK with push
access, fetching core-lite, and editing the builder were refused automatically.
Switching the session's mode from Auto to Accept edits turns those
automatic refusals into approval prompts for the owner.

`StegVerse-org/.github` cannot be attached mid-session (its name begins with `.`),
so **start the session with both `StegVerse-org/.github` and
`StegVerse-org/StegVerse-SDK` selected as sources**, alongside this repo.

## Owner

iPhone only. Answer in chat, briefly. Open PRs ready for review, not as drafts.
Don't ask questions this note answers.
