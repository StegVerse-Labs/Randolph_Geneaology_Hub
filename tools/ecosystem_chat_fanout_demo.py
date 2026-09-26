#!/usr/bin/env python3
"""Run ecosystem chat's fan-out to a SET of LLM sessions, in parallel, and converge them.

This is the shape asked for: ecosystem chat calls a set of sessions, each contributing
independently, converged into one governed answer. The machinery is not written here -- it is
`llm_adapter.distributed_executor` in StegVerse-org/LLM-adapter, whose `routing_mode: parallel`
is exactly that set. This driver builds a real workload, runs it, and prints what came back.

What this proves:
  - the parallel fan-out runs, and per-source outcomes are accounted separately
  - a provider refusal is retained as evidence rather than silently dropped
  - contributions converge in workload order
  - the result validates against ecosystem-chat-distributed-llm-execution.schema.json
  - no authority is granted by any of it

What this does NOT prove, and must not be read as proving:
  - any real provider call. Sessions are the adapter's own FixtureProviderClient; nothing
    leaves the machine.
  - Interlock/InTr ingress or egress admission, TV/TVC credential custody, WorkerCoordinator
    claim/fence, or Master Records reconstruction.

That gap is the adapter's own recorded state for this work:
LLMA-EXTERNAL-LLM-CONVERGENCE-306 is SOURCE_COMPLETE_MERGED_RUNTIME_PROOF_REQUIRED. The source
is complete and merged; the runtime proof is what is missing. This driver exercises the source.

The LLM-adapter is a separate component from the SDK and is not vendored here. Point --adapter
at a clone of StegVerse-org/LLM-adapter.

Exit 0 when the fan-out runs and validates, 2 when the adapter clone is absent, 1 on mismatch.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ADAPTER = Path("/home/user/stegverse-org/llm-adapter")
ARTIFACT = ROOT / "data/runtime-demos/ecosystem-chat-fanout.observed.json"

FIXED = "2026-09-26T22:00:00+00:00"
MESSAGES = ({"role": "user", "content": "What is the governed state of the ecosystem?"},)

SOURCES = (
    ("local",     "stegverse-local", "stegverse-reference-lm-v1", True,  "sovereign local answer"),
    ("anthropic", "anthropic",       "claude",                    False, "anthropic answer"),
    ("deepseek",  "deepseek",        "deepseek-chat",             False, "deepseek answer"),
    ("kimi",      "moonshot",        "kimi",                      False, None),  # refuses
)


def run(adapter: Path) -> dict:
    sys.path.insert(0, str(adapter))
    from llm_adapter.distributed_executor import (  # noqa: E402
        ProviderRefusalError, execute_distributed_workload, validate_execution_result)
    from llm_adapter.distributed_workload import (  # noqa: E402
        build_distributed_workload, build_source_descriptor)
    from llm_adapter.provider_client import FixtureProviderClient  # noqa: E402

    @dataclass
    class RefusingSession:
        """A session whose provider refuses. The refusal is evidence, not an error to swallow."""
        reason: str = "provider policy refusal"

        def complete(self, request):
            raise ProviderRefusalError(self.reason)

    workload = build_distributed_workload(
        workload_id="workload:ecosystem-chat:set-demo",
        canonical_request_id="event:req:ecosystem-chat-set",
        canonical_request_hash="b" * 64,
        routing_mode="parallel",
        sources=tuple(
            build_source_descriptor(
                source_id=sid, provider=prov, model=model, required=req,
                capabilities=("reasoning", "text"),
                locality="sovereign" if sid == "local" else "external-optional")
            for sid, prov, model, req, _ in SOURCES),
        governance_refs=("intr:ecosystem-chat",),
        created_at=FIXED,
    )

    clients = {
        sid: (FixtureProviderClient(ans) if ans is not None else RefusingSession())
        for sid, _, _, _, ans in SOURCES
    }
    result = execute_distributed_workload(workload, clients, MESSAGES, created_at=FIXED)
    s = result.summary

    return {
        "schema": "stegverse.hub.ecosystem-chat-fanout-observation/v1",
        "authority_effect": "NONE_LOCAL_DEMONSTRATION_ONLY",
        "real_provider_call_made": False,
        "intr_admission_exercised": False,
        "master_records_written": False,
        "adapter_commit": _head(adapter),
        "routing_mode": s.routing_mode,
        "attempted_source_ids": list(s.attempted_source_ids),
        "returned_source_ids": list(s.returned_source_ids),
        "refused_source_ids": list(s.refused_source_ids),
        "failed_source_ids": list(s.failed_source_ids),
        "skipped_source_ids": list(s.skipped_source_ids),
        "contributions": [{"source_id": c.source_id, "output": c.output}
                          for c in result.contributions],
        "workload_hash": s.workload_hash,
        "execution_hash": s.execution_hash,
        "schema_validates": bool(validate_execution_result(workload, result)),
        "authority_flags": s.to_dict()["authority"],
        "reproducibility": _reproducibility(workload, clients, execute_distributed_workload),
    }


def _reproducibility(workload, clients, execute) -> dict:
    """Re-run the identical workload and compare hashes.

    workload_hash is content-addressed and reproduces. execution_hash does not: each
    LLMContribution defaults created_at to utc_now_iso(), which lands inside its payload, so
    contribution_hash -> contribution_hashes -> execution_hash all carry wall-clock time.

    That matters for EPHEMERAL-STEGBROWSER-EXTERNAL-AI-ACTIVATION-001's predicate
    RECEIPT_SHA256_EQUALS_RECONSTRUCTED_RECEIPT_SHA256: it can be satisfied by replaying a
    stored evidence envelope, and can never be satisfied by re-executing the workload.
    """
    import time
    a = execute(workload, clients, MESSAGES, created_at=FIXED)
    time.sleep(1.1)
    b = execute(workload, clients, MESSAGES, created_at=FIXED)
    return {
        "workload_hash_reproduces": a.summary.workload_hash == b.summary.workload_hash,
        "execution_hash_reproduces": a.summary.execution_hash == b.summary.execution_hash,
        "cause": "LLMContribution.created_at defaults to utc_now_iso() and is inside its "
                 "hashed payload",
        "consequence": "reconstruction must replay the recorded envelope; re-executing the "
                       "same workload yields a different execution_hash",
    }


def _head(adapter: Path) -> str | None:
    import subprocess
    r = subprocess.run(["git", "-C", str(adapter), "rev-parse", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip() or None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--adapter", type=Path, default=DEFAULT_ADAPTER)
    ap.add_argument("--write", action="store_true", help="update the observed artifact")
    args = ap.parse_args(argv)

    if not (args.adapter / "llm_adapter" / "distributed_executor.py").is_file():
        print(f"LLM-adapter clone not found at {args.adapter}\n"
              f"  clone it: GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 "
              f"https://github.com/StegVerse-org/llm-adapter {args.adapter}", file=sys.stderr)
        return 2

    obs = run(args.adapter)
    print(f"routing_mode : {obs['routing_mode']}")
    print(f"attempted    : {obs['attempted_source_ids']}")
    print(f"returned     : {obs['returned_source_ids']}")
    print(f"refused      : {obs['refused_source_ids']}")
    print(f"failed       : {obs['failed_source_ids']}")
    for c in obs["contributions"]:
        print(f"   {c['source_id']:10} -> {c['output']!r}")
    print(f"execution_hash   : {obs['execution_hash']}")
    print(f"schema validates : {obs['schema_validates']}")
    print(f"authority granted: {any(obs['authority_flags'].values())}")
    r = obs["reproducibility"]
    print(f"workload_hash reproduces : {r['workload_hash_reproduces']}")
    print(f"execution_hash reproduces: {r['execution_hash_reproduces']}"
          f"   <- carries wall-clock time")
    print("real provider call made: NO  (fixture sessions; runtime proof still required)")

    if args.write:
        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        ARTIFACT.write_text(json.dumps(obs, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {ARTIFACT.relative_to(ROOT)}")

    if obs["failed_source_ids"] or not obs["schema_validates"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
