"""Qualify a purpose-bound worker's lifetime at task assignment.

`purpose_bound_worker` accepts `max_lifetime_seconds` and checks only that it is a
positive integer. Nothing checks that the lifetime is *justified* by the work the worker
was created to do. The cost estimate is what should qualify it: worker cost analysis is
the factor that determines the lifecycle, and the lifecycle is what governance and record
keeping bind to -- the expiry defines the window in which the worker may act, and
therefore the window its receipts cover.

Measured across the 48 canonical worker-runtime cost records that carry both a cost
estimate and a heartbeat estimate:

  0 of 48  are internally contradictory: no worker is required to finish after it expires,
           so the floor is respected everywhere.
  1 of 48  state any derivation basis at all.
  2.0x-2666.7x  is the range of expiry over expected work, median 12.8x.

And two pairs of records carry byte-identical cost inputs while granting expiries 64x and
93x apart. So the expiry is assigned, not derived: identical cost buys wildly different
lifetimes and nothing in the record says why.

This module does not invent the economics. It refuses to supply a coefficient nobody
stated. What it does is require the derivation to be stated and check the conditions that
follow from meaning alone, so an unqualified lifetime fails closed instead of passing as
precise.

Deterministic and offline: no I/O, no account state, no network.

Analysis of record: StegVerse-Labs/Randolph_Geneaology_Hub docs/WORKER_LIFECYCLE_COST_QUALIFIER.md
"""
from __future__ import annotations

from typing import Any, Mapping

SCHEMA = "stegverse.sdk.worker-lifecycle-qualification.v1"

QUALIFIED = "QUALIFIED_DERIVED_FROM_STATED_COST"
ASSERTED = "ASSERTED_NOT_DERIVED"
UNSATISFIABLE = "UNSATISFIABLE_EXPIRY_BELOW_EXPECTED_WORK"

# Cost factors the canonical worker-runtime records carry. A derivation must name at least
# one of these, so a stated basis refers to the cost rather than to nothing.
COST_FACTORS = (
    "compute_units",
    "token_units",
    "storage_bytes",
    "network_bytes",
    "operator_seconds",
    "latency_ms",
    "failure_recovery_units",
)


class WorkerLifecycleQualificationError(ValueError):
    """Raised when an assignment cannot be qualified as stated."""


def _nonneg_int(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise WorkerLifecycleQualificationError(f"{name} must be a nonnegative integer")
    return value


def expected_work_beats(lifecycle: Mapping[str, Any]) -> int:
    """Beats the worker is expected to need: completion plus declared idle."""
    completion = _nonneg_int(lifecycle.get("expected_completion_beats"), "expected_completion_beats")
    idle = _nonneg_int(lifecycle.get("expected_idle_beats"), "expected_idle_beats")
    return completion + idle


def qualify_worker_lifecycle(assignment: Mapping[str, Any]) -> dict[str, Any]:
    """Decide whether a claimed worker lifecycle is derived, merely asserted, or impossible.

    A lifecycle is QUALIFIED only when it states a derivation that names at least one cost
    factor present in the cost estimate, and its expiry covers the expected work. Stating
    no derivation is ASSERTED_NOT_DERIVED: the lifetime may still be correct, but nothing
    in the record establishes it, so governance binds to an unexplained window.
    """
    if assignment.get("schema") != SCHEMA:
        raise WorkerLifecycleQualificationError(f"schema must be {SCHEMA}")

    cost = assignment.get("cost_estimate")
    lifecycle = assignment.get("lifecycle")
    if not isinstance(cost, Mapping):
        raise WorkerLifecycleQualificationError("cost_estimate required")
    if not isinstance(lifecycle, Mapping):
        raise WorkerLifecycleQualificationError("lifecycle required")

    expiry = _nonneg_int(lifecycle.get("expiry_candidate_beats"), "expiry_candidate_beats")
    if expiry <= 0:
        raise WorkerLifecycleQualificationError("expiry_candidate_beats must be positive")
    work = expected_work_beats(lifecycle)

    stated_factors = [f for f in COST_FACTORS if cost.get(f) is not None]
    if not stated_factors:
        raise WorkerLifecycleQualificationError(
            f"cost_estimate states no recognised factor; expected one of {list(COST_FACTORS)}"
        )

    derivation = assignment.get("derivation")
    derivation_factors: list[str] = []
    derivation_stated = False
    if isinstance(derivation, Mapping):
        basis = str(derivation.get("basis") or "").strip()
        named = derivation.get("derived_from") or []
        if isinstance(named, str):
            named = [named]
        derivation_factors = [f for f in named if f in stated_factors]
        derivation_stated = bool(basis) and bool(derivation_factors)

    # A worker required to finish after it expires cannot complete its purpose. This
    # follows from meaning, not from any cost model, so it is checked unconditionally.
    if expiry < work:
        verdict = UNSATISFIABLE
    elif derivation_stated:
        verdict = QUALIFIED
    else:
        verdict = ASSERTED

    headroom = (expiry / work) if work else None

    return {
        "schema": SCHEMA,
        "verdict": verdict,
        "qualified": verdict == QUALIFIED,
        "expiry_candidate_beats": expiry,
        "expected_work_beats": work,
        "headroom_ratio": round(headroom, 2) if headroom is not None else None,
        "cost_factors_stated": stated_factors,
        "derivation_stated": derivation_stated,
        "derivation_factors": derivation_factors,
        "governance_window_explained": verdict == QUALIFIED,
        "reason": {
            QUALIFIED: "expiry derives from stated cost factors and covers expected work",
            ASSERTED: "expiry covers expected work but no derivation from cost is stated; "
                      "the governance window is unexplained",
            UNSATISFIABLE: "expiry is below expected work; the worker would expire before "
                           "completing its purpose",
        }[verdict],
        "authority_effect": "NONE_QUALIFICATION_ONLY",
    }


def qualify_many(assignments: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Qualify several assignments and report whether identical cost buys identical lifetime.

    Two workers whose cost estimates are identical but whose expiries differ cannot both be
    derived from cost. Reporting the collision is the point: it is the evidence that the
    lifecycle is assigned rather than qualified.
    """
    if not assignments:
        raise WorkerLifecycleQualificationError("at least one assignment required")
    results = [qualify_worker_lifecycle(a) for a in assignments]

    by_cost: dict[tuple, set[int]] = {}
    for a, r in zip(assignments, results):
        key = tuple(a["cost_estimate"].get(f) for f in COST_FACTORS)
        by_cost.setdefault(key, set()).add(r["expiry_candidate_beats"])
    collisions = [
        {"cost_factors": dict(zip(COST_FACTORS, key)), "expiries": sorted(exp)}
        for key, exp in by_cost.items()
        if len(exp) > 1
    ]

    return {
        "schema": SCHEMA,
        "qualifications": results,
        "qualified_count": sum(1 for r in results if r["qualified"]),
        "asserted_count": sum(1 for r in results if r["verdict"] == ASSERTED),
        "unsatisfiable_count": sum(1 for r in results if r["verdict"] == UNSATISFIABLE),
        "identical_cost_different_expiry": collisions,
        "cost_determines_lifecycle": not collisions,
        "authority_effect": "NONE_QUALIFICATION_ONLY",
    }


__all__ = [
    "SCHEMA", "QUALIFIED", "ASSERTED", "UNSATISFIABLE", "COST_FACTORS",
    "WorkerLifecycleQualificationError", "expected_work_beats",
    "qualify_worker_lifecycle", "qualify_many",
]
