# Ecosystem chat fan-out — what runs today

Recorded 2026-09-26. Run it: `python3 tools/ecosystem_chat_fanout_demo.py`
(needs a clone of `StegVerse-org/LLM-adapter`; pass `--adapter PATH` if it is elsewhere).

## The shape asked for

Ecosystem chat calls a **set** of ephemeral instances, each holding an LLM session, and responds
with governed information converged from all of them.

## It runs

```
routing_mode : parallel
attempted    : ['local', 'anthropic', 'deepseek', 'kimi']
returned     : ['local', 'anthropic', 'deepseek']
refused      : ['kimi']
failed       : []

   local      -> 'sovereign local answer'
   anthropic  -> 'anthropic answer'
   deepseek   -> 'deepseek answer'
   kimi       -> None

schema validates : True
authority granted: False
```

Four sessions in parallel, three returning, one refusing — and the refusal is **retained as a
contribution** rather than dropped, so the answer records who declined. The result validates
against `schemas/ecosystem-chat-distributed-llm-execution.schema.json`, and all six authority
flags stay false.

None of this machinery is written here. It is `llm_adapter.distributed_executor` in
`StegVerse-org/LLM-adapter`, whose `SUPPORTED_EXECUTION_MODES = {single, parallel, fallback}`.
`parallel` is the set. This repository only drives it and records what came back.

## What it does not show

- **No real provider call.** Sessions are the adapter's own `FixtureProviderClient`; nothing
  left the machine.
- No Interlock/InTr ingress or egress admission, no TV/TVC credential custody, no
  WorkerCoordinator claim or fence, no Master Records reconstruction.

That is the adapter's own recorded position. `LLMA-EXTERNAL-LLM-CONVERGENCE-306` is
`SOURCE_COMPLETE_MERGED_RUNTIME_PROOF_REQUIRED`: source complete and merged, runtime proof
missing. This exercises the source.

## Finding: `execution_hash` is not reproducible from inputs

Running the identical workload twice, 1.1 seconds apart:

```
workload_hash  reproduces : True
execution_hash reproduces : False
```

`LLMContribution.created_at` defaults to `utc_now_iso()` and sits inside the payload it hashes,
so wall-clock time flows `contribution_hash -> contribution_hashes -> execution_hash`.

This bears directly on `EPHEMERAL-STEGBROWSER-EXTERNAL-AI-ACTIVATION-001`'s predicate
`RECEIPT_SHA256_EQUALS_RECONSTRUCTED_RECEIPT_SHA256`. That predicate can be satisfied by
**replaying a recorded evidence envelope**, and can never be satisfied by **re-executing** the
workload — a re-run always produces a different `execution_hash`. Anyone attempting the proof by
re-execution will fail indefinitely without an obvious cause.

`workload_hash` is content-addressed and does reproduce, so inputs remain independently
verifiable. A test pins both facts; if the adapter ever makes `execution_hash` content-addressed,
that test fails and this finding should be retired rather than left stale.

## The blocker for a real run

`LLMA-EXTERNAL-LLM-CONVERGENCE-306` states its own next step:

> Continue through **`SHWP-ECOSYSTEM-CHAT-INFERENCE-001`** on the existing WorkerCoordinator +
> Interlock/InTr + TV/TVC + Master Records lane for authentic same-execution provider proof.

**That task has never existed.** Across 6,516 commits of `StegVerse-Labs/.github` history no file
was ever named for it — no deletion, no rename. Every match in history is a commit *adding a
reference to it* while registering something else. Seven canonical tasks point at it, and
`HIL-RESIDENT-SESSION-MANIFOLD-ACTIVATION-001` lists it under `dependencies`, not merely as
adjacent. No SHWP task under any other name covers ecosystem chat inference.

So the next step of a working executor routes through a task that was never registered. That is
a registration gap, not a missing capability — see `docs/BLOCKED_WORK_FOR_REVIEW.md` §1 for why
this session cannot write that registry.
