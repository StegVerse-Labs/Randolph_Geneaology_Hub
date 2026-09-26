#!/usr/bin/env python3
"""Measure how many canonical tasks can derive a worker lifecycle from their resource cost.

The canonical model is stated in SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001:

    WORKER_LIFETIME_IS_DERIVED_PER_INTENDED_TASK_NOT_GLOBALLY_FIXED

with the lifetime derived as the sum of five resource-cost components, recomputed per
task. The formula is not missing. What is missing is the input: the estimated resource
cost belongs on the task, and a task without one cannot derive the window its worker may
act in -- which is the window its receipts cover.

This applies the staged SDK qualifier to the canonical task records, so the SDK
demonstration and this survey are the same code and cannot diverge.

Reads local files only. Grants no authority, changes no record, sets no lifetime.

Exit 0 when every task derives a lifetime, 3 when any cannot, 2 when the corpus is absent.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUALIFIER = ROOT / "sdk-staging/stegverse/worker_lifecycle_qualifier.py"


def _install_sdk_shims() -> None:
    """Give the staged SDK module the two SDK names it imports.

    The staged qualifier is written for StegVerse-org/StegVerse-SDK, where it delegates the
    five-component sum to `purpose_bound_worker_cost_demo._sum_budget` rather than restating
    it. That delegation is the point: one derivation, one place. It also means the file cannot
    be loaded standalone here, because those relative imports resolve only inside the SDK
    package.

    So this census supplies them. `_sum_budget` below is a stand-in for running offline, not a
    second implementation of record -- the SDK's is authoritative, and
    tests/test_sdk_worker_lifecycle_qualifier_staging.py pins this one to the same contract:
    the canonical components sum to 30, and negatives and booleans are rejected.
    """
    import types

    class PurposeBoundWorkerError(ValueError):
        pass

    def _sum_budget(budget):
        names = ("expected_task_execution", "known_delay", "inferred_unknown_delay_reserve",
                 "records_decomposition", "safety_reserve")
        values = []
        for name in names:
            value = budget.get(name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise PurposeBoundWorkerError(f"{name} must be a nonnegative integer")
            values.append(value)
        return sum(values)

    pkg = types.ModuleType("stegverse")
    pkg.__path__ = []  # marks it a package so relative imports resolve
    worker = types.ModuleType("stegverse.purpose_bound_worker")
    worker.PurposeBoundWorkerError = PurposeBoundWorkerError
    demo = types.ModuleType("stegverse.purpose_bound_worker_cost_demo")
    demo._sum_budget = _sum_budget
    demo.PurposeBoundWorkerError = PurposeBoundWorkerError
    sys.modules.setdefault("stegverse", pkg)
    sys.modules["stegverse.purpose_bound_worker"] = worker
    sys.modules["stegverse.purpose_bound_worker_cost_demo"] = demo


def load_qualifier():
    _install_sdk_shims()
    spec = importlib.util.spec_from_file_location(
        "stegverse.worker_lifecycle_qualifier", QUALIFIER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load qualifier: {QUALIFIER}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["stegverse.worker_lifecycle_qualifier"] = mod
    spec.loader.exec_module(mod)
    return mod


def extract_cost(record: dict, components: tuple[str, ...]) -> dict | None:
    """Find a resource cost estimate anywhere in a task record.

    Searched rather than read from a fixed path because no convention has settled: the one
    task carrying an estimate holds it under lifetime_model.demonstration.components_seconds.
    A stricter reader would report every other task as merely mis-shaped rather than
    estimateless, which would overstate the problem.
    """
    found: dict | None = None

    def walk(node):
        nonlocal found
        if found is not None:
            return
        if isinstance(node, dict):
            if all(c in node for c in components):
                found = {c: node[c] for c in components}
                return
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(record)
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task-records-root", type=Path,
                    default=Path("/home/user/stegverse-labs/.github/data/canonical-task-records"))
    ap.add_argument("--json", type=Path, help="write the survey record here")
    args = ap.parse_args()

    if not args.task_records_root.is_dir():
        print(f"canonical task records not present: {args.task_records_root}", file=sys.stderr)
        return 2

    wlq = load_qualifier()
    assignments, unreadable = [], []
    for path in sorted(args.task_records_root.glob("*.json")):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            unreadable.append((path.stem, str(exc)))
            continue
        cost = extract_cost(rec, wlq.COST_COMPONENTS)
        a = {"schema": wlq.SCHEMA, "task_id": rec.get("task_id") or path.stem}
        if cost:
            a["estimated_resource_cost"] = cost
        assignments.append(a)

    if not assignments:
        print("no task records found", file=sys.stderr)
        return 2

    result = wlq.qualify_many(assignments)
    total = result["tasks_qualified"]
    derived = result["derived_count"]

    print(f"{total} canonical task records ({len(unreadable)} unreadable)\n")
    print(f"  lifetime derivable from the task's resource cost : {derived}")
    print(f"  task states no resource cost estimate            : {result['no_estimate_count']}")
    print(f"  resource cost estimate incomplete               : {result['incomplete_count']}")
    print(f"  claimed lifetime disagrees with its components  : {result['mismatch_count']}")
    print(f"\n  invariant: {result['lifetime_invariant']}")

    for q in result["qualifications"]:
        if q["verdict"] == wlq.DERIVED:
            print(f"\n  derived: {q['task_id']}")
            print(f"     {q['component_seconds']}")
            print(f"     -> {q['derived_max_lifetime_seconds']}s")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({
            "schema": "stegverse.worker-lifecycle-derivability-survey/v1",
            "lifetime_invariant": result["lifetime_invariant"],
            "cost_components": list(wlq.COST_COMPONENTS),
            "tasks_surveyed": total,
            "unreadable": [{"task": t, "reason": r} for t, r in unreadable],
            "derived_count": derived,
            "no_estimate_count": result["no_estimate_count"],
            "incomplete_count": result["incomplete_count"],
            "mismatch_count": result["mismatch_count"],
            "derived_tasks": [
                {"task_id": q["task_id"],
                 "component_seconds": q["component_seconds"],
                 "derived_max_lifetime_seconds": q["derived_max_lifetime_seconds"]}
                for q in result["qualifications"] if q["verdict"] == wlq.DERIVED
            ],
            "authority_effect": "NONE_QUALIFICATION_ONLY",
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"\nwrote {args.json}")

    return 0 if derived == total else 3


if __name__ == "__main__":
    raise SystemExit(main())
