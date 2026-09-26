"""Qualify a worker lifecycle from the resource cost of the task assigned.

The canonical model already exists. `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001` states it
as an invariant:

    WORKER_LIFETIME_IS_DERIVED_PER_INTENDED_TASK_NOT_GLOBALLY_FIXED

and gives the derivation as five resource-cost components summing to the lifetime, with
production requiring `recompute_per_task`, `cost_analysis_required`,
`early_retirement_on_purpose_completion` and
`budget_extension_requires_new_governed_recalculation`.

`purpose_bound_worker_cost_demo._sum_budget` already implements that sum, so this module reuses
it rather than restating it: one derivation, one place, and a change to the components cannot
silently disagree between the demo and the qualifier.

What the demo does not answer is whether a given task can derive a lifetime at all. The chain is
**task -> estimated resource cost -> worker lifecycle**, and the estimate belongs on the task.
A task stating no estimate produces no derivable lifetime, and this module says so rather than
defaulting to one -- a defaulted lifetime is the globally-fixed lifetime the invariant forbids.

That matters because the lifecycle is what governance and record keeping bind to: the expiry is
the window in which a worker may act, and therefore the window its receipts cover. A task with
no resource estimate produces a window nobody can check.

Deterministic and offline: no I/O, no account state, no network. Qualification is an
observation; it grants no execution authority and starts no worker.
"""
from __future__ import annotations

from typing import Any, Mapping

from .purpose_bound_worker import PurposeBoundWorkerError
from .purpose_bound_worker_cost_demo import _sum_budget

SCHEMA = "stegverse.sdk.worker-lifecycle-qualification.v1"

LIFETIME_INVARIANT = "WORKER_LIFETIME_IS_DERIVED_PER_INTENDED_TASK_NOT_GLOBALLY_FIXED"

# The five components the canonical lifetime_model sums, in its own order. Kept in step with
# purpose_bound_worker_cost_demo._sum_budget, which performs the sum.
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


def derive_lifetime_from_resource_cost(cost: Mapping[str, Any]) -> int:
    """Sum the five canonical components into a derived maximum lifetime.

    This is the canonical derivation, not a new one: it delegates to the same `_sum_budget` the
    cost demo uses, so the two cannot drift apart.
    """
    if not isinstance(cost, Mapping):
        raise PurposeBoundWorkerError("resource cost estimate must be an object")
    missing = [c for c in COST_COMPONENTS if cost.get(c) is None]
    if missing:
        raise PurposeBoundWorkerError(f"resource cost estimate is incomplete; missing {missing}")
    return _sum_budget(cost)


def _nonneg_int(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise PurposeBoundWorkerError(f"{name} must be a nonnegative integer")
    return value


def qualify_task_lifecycle(assignment: Mapping[str, Any]) -> dict[str, Any]:
    """Qualify the worker lifetime a task assignment implies.

    The task carries the estimated resource cost; the lifetime is what that cost sums to.
    """
    if assignment.get("schema") != SCHEMA:
        raise PurposeBoundWorkerError(f"schema must be {SCHEMA}")
    task_id = assignment.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        raise PurposeBoundWorkerError("task_id required")

    cost = assignment.get("estimated_resource_cost")
    claimed = assignment.get("claimed_max_lifetime_seconds")

    base = {
        "schema": SCHEMA,
        "task_id": task_id,
        "claimed_max_lifetime_seconds": claimed,
        "lifetime_invariant": LIFETIME_INVARIANT,
        "authority_effect": "NONE_QUALIFICATION_ONLY",
    }

    if cost is None:
        return {**base, "verdict": NO_ESTIMATE, "derivable": False,
                "derived_max_lifetime_seconds": None, "components_present": [],
                "components_missing": list(COST_COMPONENTS),
                "governance_window_derivable": False,
                "reason": "the task states no estimated resource cost, so no worker lifetime "
                          "can be derived for it"}

    if not isinstance(cost, Mapping):
        raise PurposeBoundWorkerError("estimated_resource_cost must be an object")

    present = [c for c in COST_COMPONENTS if cost.get(c) is not None]
    missing = [c for c in COST_COMPONENTS if cost.get(c) is None]
    if missing:
        return {**base, "verdict": INCOMPLETE, "derivable": False,
                "derived_max_lifetime_seconds": None, "components_present": present,
                "components_missing": missing, "governance_window_derivable": False,
                "reason": f"resource cost estimate omits {missing}; the model requires every "
                          "component in production"}

    derived = derive_lifetime_from_resource_cost(cost)
    verdict = DERIVED
    reason = "worker lifetime derives from the task's estimated resource cost"
    if claimed is not None:
        _nonneg_int(claimed, "claimed_max_lifetime_seconds")
        if claimed != derived:
            verdict = MISMATCH
            reason = (f"claimed lifetime {claimed}s does not equal the {derived}s its own "
                      "components sum to")

    return {**base, "verdict": verdict, "derivable": True,
            "derived_max_lifetime_seconds": derived, "components_present": present,
            "components_missing": [],
            "component_seconds": {c: cost[c] for c in COST_COMPONENTS},
            "governance_window_derivable": verdict == DERIVED, "reason": reason}


def qualify_many(assignments: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Qualify several task assignments and report lifecycle derivability across them."""
    if not assignments:
        raise PurposeBoundWorkerError("at least one assignment required")
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
    "derive_lifetime_from_resource_cost", "qualify_task_lifecycle", "qualify_many",
]
