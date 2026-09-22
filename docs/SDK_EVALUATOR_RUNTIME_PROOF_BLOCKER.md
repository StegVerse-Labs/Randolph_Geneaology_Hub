# What actually blocks the SDK evaluator runtime proof

`SDK-EVALUATOR-GOVERNANCE-POSTURE-RUNTIME-PROOF-001` has been sitting on one
predicate:

```text
EXACT_EVALUATOR_MANIFEST_MATERIALIZED_ON_ADMITTED_CANONICAL_RUNTIME_SUBSTRATE
```

Its handoff carries five dated sections against that predicate. Each searches
the accessible evidence projections for a recorded manifest hash, finds nothing,
and — correctly, under `MISSING_EVIDENCE_IS_NOT_PROOF_OF_NON_OCCURRENCE` —
declines to infer that materialization did not happen. The conclusion is
`UNKNOWN_NOT_FALSE` five times over.

That invariant is about **evidence**. It says nothing about **source**, and
source is where the answer is. Absence of a retained receipt proves nothing;
absence of a producer in source is a different kind of fact, and it is
mechanical. This is what the chain does when you invoke it.

Re-run it with `tools/probe_evaluator_posture_chain.py`.

## The half that already works

The recorded evidence says `authentic_live_stegos_intr_proven: false`. That is a
true statement about workflow run `34539775942`. It is not a statement about the
boundary.

With the StegOS source root present, the SDK's own evaluator manifest builder
produces a manifest, and the **live** StegOS resolver — `stegos/intr_security_posture_resolution.py`
at the current head blob `e7f1e89a`, no fixture and no injected resolver —
resolves its posture:

```text
resolution_authority      : INTERLOCK_INTR
effective posture tier    : HIGHEST
transition_request_sha256 : sha256:e1336ec77d95722c487d19ba04d089f80fbbf8d127485a0afa9ca7070f196c74
```

The Interlock/InTr posture boundary is not what is blocking this task.

The SDK's cross-repo test binds to a byte snapshot of that StegOS module,
`tests/fixtures/stegos_intr_security_posture_resolution_84ddc96e.py`. Pinned
copies of another repository's source are the exact shape counted in
`GUARD_DRIFT_CENSUS.md`, so it was worth checking: **this one has not drifted.**
It is identical to the live module apart from its provenance docstring, and the
blob SHA it claims, `e7f1e89a`, is StegOS's current blob for that path. A clean
result, recorded so it is not re-derived.

## What the fail-closed actually is

The recorded label is opaque:

```text
governance_execution: FAIL_CLOSED_MISSING_CANONICAL_RUNTIME_PACKAGES
```

It reproduces exactly, and it has a name. Posture resolution succeeds; the very
next call does not:

```text
run_evaluator_governance_manifest
  -> resolve_manifest_posture           ... INTERLOCK_INTR, ok
  -> run_sovereign_validation
       -> sovereign_validation_runtime._components()
            -> from core_lite.transaction_route import ManifestRouteCarrier, ...
            ModuleNotFoundError: No module named 'core_lite'
       SovereignValidationError: Canonical StegCore, Core-Lite and Master Records
       packages are required; no parallel evaluator is provided.
```

The missing package is `core_lite`, not StegOS. SDK source declares where it
comes from and pins it exactly —
`Data-Continuation/core-lite@72bdb0f110031ccc2cd98b8ebb7c22b1ab7326f8`, in
`stegverse/production_release_set.py` and `stegverse/local_governance_experiment.py` —
but `pyproject.toml` does not list it, so no environment that installs the SDK
by its own metadata can satisfy the import. `Data-Continuation` is a separate
organization.

This is not a new defect. It is the task record's own first remaining item,
"canonical TV/TVC-gated public runtime package publication", stated precisely
enough to act on. The fail-closed is the design working: the SDK refuses to
substitute a parallel evaluator.

## What no one can do, on any substrate

Two findings are about reachability, and they are the ones that matter.

**Nothing in production source materializes the manifest.** The resident
consumer requires `runtime-state/sdk-evaluator-governance-posture/manifest.json`
to already exist and returns `INPUT_NOT_MATERIALIZED` otherwise. Four files
reference that locator; the only executable one is
`tests/test_sdk_evaluator_governance_posture_resident.py`, which writes a stub
`{"schema": "x", "manifest_sha256": "sha256:m"}` against a stub entrypoint. The
consumer has never been exercised against a real manifest. The builder that
could produce one lives in the SDK, which contains **zero** references to the
locator. Both ends exist; nothing joins them.

**The gating hashes have no producer.** The predicate names an *exact* manifest,
and progression is gated on these:

```text
manifest_sha256           : 1f2b204fc55a22fe0ba533a1825d2bc11a8a1427d70fa8191776c71f4c323bc3
transition_request_sha256 : 3d06812c7d1c1967cdded761c1245db4cc4587b275c5944b6de89bb0ac67909b
```

Each appears in exactly three places — two task records and one handoff
paragraph. No source file in either repository produces either one, and the
inputs that would produce them are recorded nowhere. The evidence came from
CI artifacts that are uploaded and discarded; `evidence/` is not even tracked in
the SDK working tree.

Checked against the recorded head rather than assumed: `8ce3643` touched one
workflow line, and the manifest-producing script on that workflow emits
`07a08496…` deterministically, both at that commit and today. Not `1f2b204f`.

So the exactness the predicate demands is unverifiable. Publish
`Data-Continuation/core-lite` tomorrow, run the whole chain on a properly
admitted substrate, and the manifest it produces still cannot be checked against
`1f2b204f` by anyone, because nothing says what inputs that hash was over.

## The shape

`GUARD_DRIFT_CENSUS.md` counts one defect shape: *something moved, and the thing
that asserts about it did not follow*. This is the same shape with the subject
missing rather than moved — an assertion whose referent was never written down.
It is the more expensive variant, because a stale assertion can be re-pointed at
the file that now holds the code, and an orphan hash cannot be re-pointed at
anything.

The cost is visible in the handoff itself: five sections, four dates, one
question, no answer. Each re-derivation searched evidence because evidence is
what the invariant talks about. None asked what source can produce, which takes
one script.

## Not claimed

This host is not an admitted canonical runtime substrate, and nothing here
claims the predicate is satisfied, that materialization did or did not occur, or
that any transition may progress. No governed transition was executed, nothing
was submitted to Master Records, and no network call was made — the probe stops
at the posture binding by design.

No source or runtime defect is inferred from evidence absence. The two
reachability findings are statements about what source contains, which is
checkable and rechecked by the script rather than argued. `RESIDENT_REQUEST_DISPATCH_VISIT`
remains excluded as a predecessor, no second manifest builder is proposed here,
and the manifest's canonical source owner remains `StegVerse-org/StegVerse-SDK`.

## Re-running this

```bash
python3 tools/probe_evaluator_posture_chain.py \
  --sdk-root /home/user/stegverse-sdk \
  --stegos-root /home/user/stegos \
  --github-root /home/user/stegverse-labs/.github
```

Exit `0` when every check resolves, `3` on an unresolved finding, `2` when a
source root is absent. Four are unresolved today; the two reachability findings
are the ones that close without waiting on another organization.
