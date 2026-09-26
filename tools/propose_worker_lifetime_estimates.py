#!/usr/bin/env python3
"""Propose a derived worker lifetime for every canonical task whose own cost basis supplies one.

The survey in data/cost-basis/worker-lifecycle-derivability.json reported 1 of 163 canonical
tasks able to derive a lifetime. That number was an artefact of how cost-basis records were
matched to tasks: by `task_class`, which almost never equals a canonical task id. Records also
name tasks in `evidence_refs` as `handoffs/<TASK-ID>.json`, and matching on that finds six.

The anchor is SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001, the one task carrying both a
canonical `lifetime_model` and a cost-basis record:

    cost-basis hb_estimate.expected_completion_beats = 30
    canonical  lifetime_model derived_max_lifetime_seconds = 30

so `expected_completion_beats` is the derived maximum lifetime in seconds, and any task linked
to a record carrying that field has its total.

What this does NOT do is split the total into the five canonical components
(expected_task_execution, known_delay, inferred_unknown_delay_reserve, records_decomposition,
safety_reserve). One calibration point cannot determine five coefficients, and that single point
has three of its four structural signals at zero (15 evidence predicates, 0 dependencies,
0 blockers, 0 declared capabilities). Fitting a component rule to it would be invention. The
split is a policy for the registry owners to state; this proposes only what the evidence carries.

Reads local clones only. Writes a proposal artifact. Grants no authority, registers nothing,
sets no lifetime.

Exit 0 when the proposal is written, 2 when the registry clone is absent.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = Path("/home/user/stegverse-labs/.github")
OUT = ROOT / "data/cost-basis/worker-lifetime-estimate-proposal.json"

TASK_ID = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{3}\b")
COMPONENTS = ("expected_task_execution", "known_delay", "inferred_unknown_delay_reserve",
              "records_decomposition", "safety_reserve")
ANCHOR = "SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001"


def git_show(repo: Path, sha: str, path: str) -> str | None:
    r = subprocess.run(["git", "-C", str(repo), "show", f"{sha}:{path}"],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def load(repo: Path, sha: str, path: str):
    s = git_show(repo, sha, path)
    if s is None:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


def build(repo: Path) -> dict:
    sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "origin/main"],
                         capture_output=True, text=True).stdout.strip()
    names = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "--name-only", sha],
                           capture_output=True, text=True).stdout.split()

    tasks: dict[str, dict] = {}
    for n in names:
        if n.startswith("data/canonical-task-records/") and n.endswith(".json"):
            d = load(repo, sha, n)
            if d and d.get("task_id"):
                tasks[d["task_id"]] = d

    proposed, unbound, linked_without_estimate = [], [], []
    for n in (x for x in names if x.startswith("cost-basis/")):
        d = load(repo, sha, n)
        if not d:
            continue
        beats = (d.get("hb_estimate") or {}).get("expected_completion_beats")
        confidence = (d.get("hb_estimate") or {}).get("confidence")

        # Bind by explicit task_id, else by any canonical task id named in evidence_refs.
        hits = set()
        if d.get("task_id") in tasks:
            hits.add(d["task_id"])
        for ref in (d.get("evidence_refs") or []):
            hits.update(t for t in TASK_ID.findall(ref) if t in tasks)

        if not hits:
            unbound.append({
                "cost_basis_record": n,
                "task_class": d.get("task_class"),
                "expected_completion_beats": beats,
                "reason": "names no canonical task id, in task_id or in evidence_refs",
            })
            continue
        if beats is None:
            linked_without_estimate.append({"cost_basis_record": n, "tasks": sorted(hits)})
            continue

        for t in sorted(hits):
            existing = ((tasks[t].get("lifetime_model") or {}).get("demonstration") or {})
            proposed.append({
                "task_id": t,
                "proposed_derived_max_lifetime_seconds": beats,
                "source": {"cost_basis_record": n, "field": "hb_estimate.expected_completion_beats",
                           "confidence": confidence},
                "components_proposed": None,
                "components_reason": "the five-component split is policy, not evidence; see the "
                                     "component_split_not_proposed block",
                "agrees_with_existing_lifetime_model": (
                    existing.get("derived_max_lifetime_seconds") == beats
                    if existing.get("derived_max_lifetime_seconds") is not None else None),
            })

    anchor = next((p for p in proposed if p["task_id"] == ANCHOR), None)
    return {
        "schema": "stegverse.worker-lifetime-estimate-proposal/v1",
        "authority_effect": "NONE_PROPOSAL_ONLY",
        "grants_registration": False,
        "sets_any_lifetime": False,
        "observed_from": {"repository": "StegVerse-Labs/.github", "ref": "main", "commit": sha,
                          "canonical_task_records": len(tasks)},
        "anchor": {
            "task_id": ANCHOR,
            "holds": "expected_completion_beats equals derived_max_lifetime_seconds",
            "verified": bool(anchor and anchor["agrees_with_existing_lifetime_model"]),
            "value_seconds": anchor["proposed_derived_max_lifetime_seconds"] if anchor else None,
        },
        "component_split_not_proposed": {
            "components": list(COMPONENTS),
            "why": "One calibration point cannot determine five coefficients. That point has "
                   "15 evidence predicates, 0 dependencies, 0 blockers and 0 declared "
                   "capabilities, so three of four structural signals are zero and no "
                   "per-signal coefficient is identifiable from it.",
            "what_would_resolve_it": "a stated policy from the registry owners, or a second "
                                     "task carrying both a component split and a cost basis",
        },
        "proposed": sorted(proposed, key=lambda p: p["task_id"]),
        "proposed_count": len(proposed),
        "cost_basis_unbound": sorted(unbound, key=lambda u: u["cost_basis_record"]),
        "cost_basis_unbound_count": len(unbound),
        "cost_basis_unbound_carrying_an_estimate": sum(
            1 for u in unbound if u["expected_completion_beats"] is not None),
        "cost_basis_linked_without_estimate": linked_without_estimate,
        "tasks_total": len(tasks),
        "tasks_still_without_any_linked_estimate": len(tasks) - len({p["task_id"] for p in proposed}),
        "binding_is_not_inferrable": "No additional record binds under task_class normalisation: "
                                     "task_class values do not correspond to canonical task ids "
                                     "by name. The mapping must be authored by whoever knows "
                                     "which task each class serves.",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--print", action="store_true")
    args = ap.parse_args(argv)

    if not (args.registry / ".git").is_dir():
        print(f"registry clone absent: {args.registry}", file=sys.stderr)
        return 2

    report = build(args.registry)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"proposed lifetimes:        {report['proposed_count']} task(s)")
    print(f"anchor verified:           {report['anchor']['verified']} "
          f"({report['anchor']['value_seconds']}s)")
    print(f"unbound cost-basis records: {report['cost_basis_unbound_count']} "
          f"({report['cost_basis_unbound_carrying_an_estimate']} carry an estimate)")
    print(f"tasks still with no linked estimate: {report['tasks_still_without_any_linked_estimate']}"
          f" of {report['tasks_total']}")
    if args.print:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
