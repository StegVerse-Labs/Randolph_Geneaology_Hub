#!/usr/bin/env python3
"""Qualify every canonical worker-runtime lifecycle against its own cost estimate.

Worker cost analysis is the factor that determines worker lifecycle, and the lifecycle is
what governance and record keeping bind to: `expiry_candidate_beats` is the window in which
a worker may act, and therefore the window its receipts cover. A window nothing derives is
a governance bound nobody can check.

This applies the staged SDK qualifier (sdk-staging/stegverse/worker_lifecycle_qualifier.py)
to the canonical corpus in StegVerse-Labs/.github/cost-basis/, so the SDK demonstration and
this survey cannot diverge -- they are the same code.

It reads local files only. It grants no authority, changes no record, and sets no lifetime.

Exit 0 when every record qualifies, 3 when any is asserted or unsatisfiable, 2 when the
corpus cannot be read.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUALIFIER = ROOT / "sdk-staging/stegverse/worker_lifecycle_qualifier.py"


def load_qualifier():
    spec = importlib.util.spec_from_file_location("worker_lifecycle_qualifier", QUALIFIER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load qualifier: {QUALIFIER}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cost-basis-root", type=Path,
                    default=Path("/home/user/stegverse-labs/.github/cost-basis"))
    ap.add_argument("--json", type=Path, help="write the qualification record here")
    args = ap.parse_args()

    if not args.cost_basis_root.is_dir():
        print(f"cost-basis corpus not present: {args.cost_basis_root}", file=sys.stderr)
        return 2

    wlq = load_qualifier()
    assignments, names, skipped = [], [], []
    for path in sorted(args.cost_basis_root.rglob("*.json")):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            skipped.append((path.name, f"unreadable: {exc}"))
            continue
        cost, hb = rec.get("cost_estimate"), rec.get("hb_estimate")
        if not isinstance(cost, dict) or not isinstance(hb, dict):
            skipped.append((path.name, "no cost_estimate and hb_estimate pair"))
            continue
        derivation = None
        basis = rec.get("estimate_basis") or rec.get("expiry_basis")
        if basis:
            # A stated basis only counts if it names cost factors the record carries.
            derivation = {"basis": str(basis),
                          "derived_from": [f for f in wlq.COST_FACTORS if cost.get(f) is not None]}
        assignments.append({
            "schema": wlq.SCHEMA,
            "cost_estimate": cost,
            "lifecycle": hb,
            **({"derivation": derivation} if derivation else {}),
        })
        names.append(path.stem)

    if not assignments:
        print("no qualifiable records found", file=sys.stderr)
        return 2

    result = wlq.qualify_many(assignments)
    rows = list(zip(names, result["qualifications"]))
    ratios = [q["headroom_ratio"] for _, q in rows if q["headroom_ratio"] is not None]

    print(f"{len(rows)} qualifiable records ({len(skipped)} skipped)\n")
    print(f"  qualified (derived from stated cost) : {result['qualified_count']}")
    print(f"  asserted  (no derivation stated)     : {result['asserted_count']}")
    print(f"  unsatisfiable (expiry below work)    : {result['unsatisfiable_count']}")
    if ratios:
        print(f"\n  headroom expiry/work  min={min(ratios):.1f}x  "
              f"median={statistics.median(ratios):.1f}x  max={max(ratios):.1f}x")
    coll = result["identical_cost_different_expiry"]
    print(f"\n  identical cost, different expiry: {len(coll)} group(s)")
    for c in coll:
        factors = {k: v for k, v in c["cost_factors"].items() if v not in (None, 0)}
        print(f"     {factors}")
        print(f"        expiries {c['expiries']}")
    print(f"\n  cost_determines_lifecycle: {result['cost_determines_lifecycle']}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({
            "schema": "stegverse.worker-lifecycle-qualification-survey/v1",
            "records_qualified": len(rows),
            "records_skipped": [{"record": n, "reason": r} for n, r in skipped],
            "qualified_count": result["qualified_count"],
            "asserted_count": result["asserted_count"],
            "unsatisfiable_count": result["unsatisfiable_count"],
            "headroom_min": min(ratios) if ratios else None,
            "headroom_median": statistics.median(ratios) if ratios else None,
            "headroom_max": max(ratios) if ratios else None,
            "identical_cost_different_expiry": coll,
            "cost_determines_lifecycle": result["cost_determines_lifecycle"],
            "per_record": [{"record": n, "verdict": q["verdict"],
                            "expiry_candidate_beats": q["expiry_candidate_beats"],
                            "expected_work_beats": q["expected_work_beats"],
                            "headroom_ratio": q["headroom_ratio"]} for n, q in rows],
            "authority_effect": "NONE_QUALIFICATION_ONLY",
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"\nwrote {args.json}")

    return 0 if result["qualified_count"] == len(rows) else 3


if __name__ == "__main__":
    raise SystemExit(main())
