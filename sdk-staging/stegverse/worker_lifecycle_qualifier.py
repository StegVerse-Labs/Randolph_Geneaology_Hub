"""Derive and qualify a worker lifecycle from the resource cost of the task assigned.

The canonical model already exists. `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001` states
it as an invariant:

    WORKER_LIFETIME_IS_DERIVED_PER_INTENDED_TASK_NOT_GLOBALLY_FIXED

and gives the derivation as five resource-cost components that sum to the lifetime:

    expected_task_execution          6
    known_delay                      4
    inferred_unknown_delay_reserve   8
    records_decomposition            7
    safety_reserve                   5
                                  = 30 seconds

with production requiring `recompute_per_task`, `cost_analysis_required`,
`early_retirement_on_purpose_completion`, and
`budget_extension_requires_new_governed_recalculation`.

`purpose_bound_worker_cost_demo._sum_budget` already implements exactly that sum. So the
formula is not missing and this module does not invent one.

What is missing is the input. The chain is: **task -> estimated resource cost -> worker
lifecycle**, and the estimate belongs on the task. Measured across the 163 canonical task
records, exactly one carries a resource cost estimate, one carries a lifetime model, and
one carries a cost_basis_ref -- the same record, whose purpose is to prove the model. The
other 162 assign work whose worker lifetime nothing derives.

That matters because the lifecycle is what governance and record keeping bind to: the
expiry is the window in which a worker may act, and therefore the window its receipts
cover. A task with no resource estimate produces a window nobody can check.

Deterministic and offline: no I/O, no account state, no network.

Analysis of record: StegVerse-Labs/Randolph_Geneaology_Hub docs/WORKER_LIFECYCLE_COST_QUALIFIER.md
"""
from __future__ import annotations

from typing import Any, Mapping

SCHEMA = "stegverse.sdk.worker-lifecycle-qualification.v1"

LIFETIME_INVARIANT = "WORKER_LIFETIME_IS_DERIVED_PER_INTENDED_TASK_NOT_GLOBALLY_FIXED"

# The five components the canonical lifetime_model sums, in its own order.
COST_COMPONENTS = (
    "expected_task_execution",
    "known_delay",
    "inferred_unknown_delay_reserve",
    "records_decomposition",
    "safety_reserve",
)

DERIVED = "DERIVED_FROM_TASK_RESOURCE_COST"
NO_ESTIMATE = "TASK_STATES_NO_RESOURCE_COST_ESTIMATE"
INCOMPLETE = "RESOURCE_COST_ESTIMATE_INCOMPLETE"
MISMATCH = "CLAIMED_LIFETIME_DISAGREES_WITH_ITS_COMPONENTS"


class WorkerLifecycleQualificationError(ValueError):
    """Raised when an assignment cannot be qualified as stated."""


def _nonneg_int(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise WorkerLifecycleQualificationError(f"{name} must be a nonnegative integer")
    return value


def derive_lifetime_from_resource_cost(cost: Mapping[str, Any]) -> int:
    """Sum the five canonical components into a derived maximum lifetime.

    This is the canonical derivation, not a new one: the same five components, in the same
    sense, that the lifetime_model states and that the SDK cost demo already sums. Every
    component is required, because the model requires each of them in production.
    """
    if not isinstance(cost, Mapping):
        raise WorkerLifecycleQualificationError("resource cost estimate must be an object")
    missing = [c for c in COST_COMPONENTS if cost.get(c) is None]
    if missing:
        raise WorkerLifecycleQualificationError(
            f"resource cost estimate is incomplete; missing {missing}"
        )
    return sum(_nonneg_int(cost[c], c) for c in COST_COMPONENTS)


def qualify_task_lifecycle(assignment: Mapping[str, Any]) -> dict[str, Any]:
    """Qualify the worker lifetime a task assignment implies.

    The task carries the estimated resource cost. The lifetime is what that cost sums to.
    A task stating no estimate cannot derive a lifetime, and says so rather than defaulting
    to one -- a defaulted lifetime is the globally-fixed lifetime the invariant forbids.
    """
    if assignment.get("schema") != SCHEMA:
        raise WorkerLifecycleQualificationError(f"schema must be {SCHEMA}")
    task_id = assignment.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        raise WorkerLifecycleQualificationError("task_id required")

    cost = assignment.get("estimated_resource_cost")
    claimed = assignment.get("claimed_max_lifetime_seconds")

    if cost is None:
        return {
            "schema": SCHEMA,
            "task_id": task_id,
            "verdict": NO_ESTIMATE,
            "derivable": False,
            "derived_max_lifetime_seconds": None,
            "claimed_max_lifetime_seconds": claimed,
            "components_present": [],
            "components_missing": list(COST_COMPONENTS),
            "lifetime_invariant": LIFETIME_INVARIANT,
            "governance_window_derivable": False,
            "reason": "the task states no estimated resource cost, so no worker lifetime "
                      "can be derived for it",
            "authority_effect": "NONE_QUALIFICATION_ONLY",
        }

    if not isinstance(cost, Mapping):
        raise WorkerLifecycleQualificationError("estimated_resource_cost must be an object")

    present = [c for c in COST_COMPONENTS if cost.get(c) is not None]
    missing = [c for c in COST_COMPONENTS if cost.get(c) is None]
    if missing:
        return {
            "schema": SCHEMA,
            "task_id": task_id,
            "verdict": INCOMPLETE,
            "derivable": False,
            "derived_max_lifetime_seconds": None,
            "claimed_max_lifetime_seconds": claimed,
            "components_present": present,
            "components_missing": missing,
            "lifetime_invariant": LIFETIME_INVARIANT,
            "governance_window_derivable": False,
            "reason": f"resource cost estimate omits {missing}; the model requires every "
                      "component in production",
            "authority_effect": "NONE_QUALIFICATION_ONLY",
        }

    derived = derive_lifetime_from_resource_cost(cost)
    verdict = DERIVED
    reason = "worker lifetime derives from the task's estimated resource cost"
    if claimed is not None:
        _nonneg_int(claimed, "claimed_max_lifetime_seconds")
        if claimed != derived:
            verdict = MISMATCH
            reason = (f"claimed lifetime {claimed}s does not equal the {derived}s its own "
                      "components sum to")

    return {
        "schema": SCHEMA,
        "task_id": task_id,
        "verdict": verdict,
        "derivable": True,
        "derived_max_lifetime_seconds": derived,
        "claimed_max_lifetime_seconds": claimed,
        "components_present": present,
        "components_missing": [],
        "component_seconds": {c: cost[c] for c in COST_COMPONENTS},
        "lifetime_invariant": LIFETIME_INVARIANT,
        "governance_window_derivable": verdict == DERIVED,
        "reason": reason,
        "authority_effect": "NONE_QUALIFICATION_ONLY",
    }


def qualify_many(assignments: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Qualify several task assignments and report lifecycle derivability across them."""
    if not assignments:
        raise WorkerLifecycleQualificationError("at least one assignment required")
    results = [qualify_task_lifecycle(a) for a in assignments]
    derived = [r for r in results if r["verdict"] == DERIVED]

    # Identical resource cost must produce identical lifetime; that is what "derived" means.
    by_cost: dict[tuple, set[int]] = {}
    for r in derived:
        key = tuple(r["component_seconds"][c] for c in COST_COMPONENTS)
        by_cost.setdefault(key, set()).add(r["derived_max_lifetime_seconds"])
    collisions = [
        {"components": dict(zip(COST_COMPONENTS, k)), "lifetimes": sorted(v)}
        for k, v in by_cost.items() if len(v) > 1
    ]

    return {
        "schema": SCHEMA,
        "qualifications": results,
        "tasks_qualified": len(results),
        "derived_count": len(derived),
        "no_estimate_count": sum(1 for r in results if r["verdict"] == NO_ESTIMATE),
        "incomplete_count": sum(1 for r in results if r["verdict"] == INCOMPLETE),
        "mismatch_count": sum(1 for r in results if r["verdict"] == MISMATCH),
        "identical_cost_different_lifetime": collisions,
        "lifetime_invariant": LIFETIME_INVARIANT,
        "authority_effect": "NONE_QUALIFICATION_ONLY",
    }


__all__ = [
    "SCHEMA", "LIFETIME_INVARIANT", "COST_COMPONENTS",
    "DERIVED", "NO_ESTIMATE", "INCOMPLETE", "MISMATCH",
    "WorkerLifecycleQualificationError",
    "derive_lifetime_from_resource_cost", "qualify_task_lifecycle", "qualify_many",
]
