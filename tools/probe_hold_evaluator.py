#!/usr/bin/env python3
"""Re-check the ELAN HOLD experiment review against StegVerse-SDK source.

`ELAN-HOLD-EXPERIMENT-ATTEMPT-REVIEW-20261005` records the attempt as: T0 manifest
built, SDK handoff reported, authentic InTr admission not observed, T1-T4 not
invoked. This script asks what the reviewed source can actually do, by reading it.

It never imports or executes SDK code. Every check is a parse of source text, so
it proves nothing about any runtime and grants no authority. It answers only:
does the evaluator implement the experiment the record specifies, and can its T0
path reach the boundary the record says it reached?

Exit 0 when every check resolves, 3 when a check finds a discrepancy, 2 when a
required file is missing.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORD = ROOT / "data/hold-experiment/ELAN_HOLD_EXPERIMENT_ATTEMPT_REVIEW_20261005.json"
EVALUATOR_REL = "scripts/run_independent_hold_evaluator.py"
WORKFLOW_REL = ".github/workflows/independent-hold-evaluator.yml"
RUNTIME_REL = "stegverse/manifest_state_transition_runtime.py"

findings: list[str] = []


def report(name: str, ok: bool, detail: str) -> bool:
    print(f"[{'ok  ' if ok else 'DRIFT'}] {name}: {detail}")
    if not ok:
        findings.append(f"{name}: {detail}")
    return ok


def module_constant(tree: ast.Module, name: str):
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    return None


def function(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    return next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name), None)


def returns_only_none(fn: ast.FunctionDef) -> bool:
    """True when the function body, docstring aside, is exactly `return None`."""
    body = [n for n in fn.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
    return (len(body) == 1 and isinstance(body[0], ast.Return)
            and (body[0].value is None or (isinstance(body[0].value, ast.Constant) and body[0].value.value is None)))


def calls(tree: ast.AST, name: str) -> list[ast.Call]:
    return [n for n in ast.walk(tree) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name) and n.func.id == name]


def check_conditions(record: dict, evaluator: ast.Module) -> None:
    specified = [(c["id"], c["name"]) for c in record["conditions"]]
    implemented = [(c[0], c[1]) for c in (module_constant(evaluator, "CONDITIONS") or [])]
    differing = [f"{s[0]}: record {s[1]} / evaluator {i[1]}" for s, i in zip(specified, implemented) if s != i]
    report("conditions", not differing and len(specified) == len(implemented),
           "evaluator implements the specified T0-T4" if not differing
           else "evaluator implements a different experiment: " + "; ".join(differing))


def check_t0_reachability(evaluator: ast.Module, runtime: ast.Module) -> None:
    shim = function(runtime, "manifest_declared_destination")
    shim_inert = shim is not None and returns_only_none(shim)
    exec_calls = calls(evaluator, "execute_manifest")
    passes_boundary = any(len(c.args) > 1 or any(k.arg == "organization_boundary" for k in c.keywords)
                          for c in exec_calls)
    asserts_handoff = "SDK_MANIFEST_HANDOFF" in {
        n.value for a in ast.walk(evaluator) if isinstance(a, ast.Assert)
        for n in ast.walk(a.test) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    unreachable = shim_inert and not passes_boundary and asserts_handoff
    report("t0-handoff-reachable", not unreachable,
           "T0 can reach SDK_MANIFEST_HANDOFF" if not unreachable else
           "manifest_declared_destination() returns None and the evaluator passes no "
           "organization_boundary, so execute_manifest fails closed at "
           "SDK_ORGANIZATION_DESTINATION_RESOLUTION and the evaluator's "
           "SDK_MANIFEST_HANDOFF assertion cannot hold")


def check_authority_varies(evaluator: ast.Module) -> None:
    imports_fixture = any(isinstance(n, ast.ImportFrom) and (n.module or "").startswith("tests.")
                          and any(a.name == "governance_request" for a in n.names) for n in ast.walk(evaluator))
    report("authority-state-varies", not imports_fixture,
           "processor request is condition-specific" if not imports_fixture else
           "every condition uses the same tests.test_manifest_builder.governance_request(); "
           "HOLD exists only as a payload label, not as an authority-state difference")


def check_workflow_trigger(workflow_text: str) -> None:
    covers_runtime = "stegverse/" in workflow_text or "paths:" not in workflow_text
    report("workflow-reruns-on-runtime-change", covers_runtime,
           "workflow re-runs when the SDK runtime changes" if covers_runtime else
           "workflow path filter names only the evaluator and itself; runtime changes never re-run it")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--sdk-root", required=True, type=Path)
    p.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    args = p.parse_args()

    paths = {rel: args.sdk_root / rel for rel in (EVALUATOR_REL, WORKFLOW_REL, RUNTIME_REL)}
    missing = [str(path) for path in [args.record, *paths.values()] if not path.is_file()]
    if missing:
        print("missing: " + ", ".join(missing), file=sys.stderr)
        return 2

    record = json.loads(args.record.read_text(encoding="utf-8"))
    evaluator = ast.parse(paths[EVALUATOR_REL].read_text(encoding="utf-8"))
    runtime = ast.parse(paths[RUNTIME_REL].read_text(encoding="utf-8"))

    check_conditions(record, evaluator)
    check_t0_reachability(evaluator, runtime)
    check_authority_varies(evaluator)
    check_workflow_trigger(paths[WORKFLOW_REL].read_text(encoding="utf-8"))

    print(f"\n{len(findings)} unresolved" if findings else "\nall checks resolve")
    return 3 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
