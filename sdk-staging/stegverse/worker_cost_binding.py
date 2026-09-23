"""Bind a measured billed-cost basis to a purpose-bound worker at task assignment.

`purpose_bound_worker_cost_demo` derives a worker's maximum lifetime in seconds from a
time budget, and tiers workers LOW/MEDIAN/HIGH by that lifetime. Measurement of retained
GitHub Actions run evidence across six StegVerse repositories shows that lifetime in
seconds is not what a run is billed for. Two facts decide the bill:

  visibility   Actions minutes on a public repository are free. Measured, 45,836 of
               60,208 runs (76.1%) were in public repositories and billed nothing.
  rounding     A private-repository run bills by the minute, rounded UP, per run. Every
               measured median run was under 25 seconds, so 61.8%-66.9% of each billed
               minute was rounding rather than compute.

The consequence for worker creation is exact and counter-intuitive: a worker assigned a
15-second lifetime and one assigned a 60-second lifetime bill identically, while creating
three workers of any lifetime bills three times. **Cost at task assignment is set by how
many workers are created, not by how long each may live.**

This module is the calculation only. It performs no I/O, reads no network, and is fully
deterministic, so a test can demonstrate the exact binding without a live account. It
grants no authority, sets no price, and commits no budget.

Measurement of record: Randolph_Geneaology_Hub docs/ACTIONS_COST_BASIS.md and
data/cost-basis/measured-actions-cost-basis.json, produced by
tools/measure_actions_cost_basis.py.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

SCHEMA = "stegverse.sdk.worker-cost-binding.v1"

# GitHub's published per-minute multipliers for private-repository runners.
RUNNER_MULTIPLIER = {"linux": 1, "windows": 2, "macos": 10}

BILLING_INCREMENT_SECONDS = 60

MEASUREMENT_REF = (
    "StegVerse-Labs/Randolph_Geneaology_Hub/data/cost-basis/measured-actions-cost-basis.json"
)


class WorkerCostBindingError(ValueError):
    """Raised when a cost binding cannot be derived from the assignment as stated."""


def _positive_int(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise WorkerCostBindingError(f"{name} must be a positive integer")
    return value


def billed_units_for_worker(
    lifetime_seconds: int,
    *,
    substrate_visibility: str,
    runner_class: str = "linux",
) -> int:
    """Billed units one worker of this lifetime incurs on this substrate.

    A public substrate bills nothing at all, whatever the lifetime. A private substrate
    bills ceil(lifetime / 60) increments, multiplied by the runner class.
    """
    _positive_int(lifetime_seconds, "lifetime_seconds")
    visibility = str(substrate_visibility).lower()
    if visibility not in ("public", "private"):
        raise WorkerCostBindingError("substrate_visibility must be 'public' or 'private'")
    runner = str(runner_class).lower()
    if runner not in RUNNER_MULTIPLIER:
        raise WorkerCostBindingError(
            f"runner_class must be one of {sorted(RUNNER_MULTIPLIER)}"
        )
    if visibility == "public":
        return 0
    increments = math.ceil(lifetime_seconds / BILLING_INCREMENT_SECONDS)
    return increments * RUNNER_MULTIPLIER[runner]


def bind_worker_cost_at_assignment(assignment: Mapping[str, Any]) -> dict[str, Any]:
    """Bind the measured cost basis to a worker assignment.

    The assignment states the derived lifetime, how many workers will be created, and the
    substrate they will run on. The binding reports what that actually bills, and how much
    of it is per-minute rounding rather than compute the worker can use.
    """
    if assignment.get("schema") != SCHEMA:
        raise WorkerCostBindingError(f"schema must be {SCHEMA}")

    lifetime = _positive_int(
        assignment.get("derived_max_lifetime_seconds"), "derived_max_lifetime_seconds"
    )
    worker_count = _positive_int(assignment.get("worker_count"), "worker_count")
    substrate = assignment.get("substrate")
    if not isinstance(substrate, Mapping):
        raise WorkerCostBindingError("substrate required")

    visibility = str(substrate.get("visibility", "")).lower()
    runner = str(substrate.get("runner_class", "linux")).lower()

    per_worker = billed_units_for_worker(
        lifetime, substrate_visibility=visibility, runner_class=runner
    )
    total = per_worker * worker_count

    # Seconds the assignment pays for but no worker can use. Zero where nothing is billed.
    billed_seconds = total * BILLING_INCREMENT_SECONDS
    usable_seconds = lifetime * worker_count
    rounding_seconds = max(0, billed_seconds - usable_seconds) if total else 0
    rounding_share = (rounding_seconds / billed_seconds) if billed_seconds else 0.0

    return {
        "schema": SCHEMA,
        "derived_max_lifetime_seconds": lifetime,
        "worker_count": worker_count,
        "substrate": {"visibility": visibility, "runner_class": runner},
        "billing_increment_seconds": BILLING_INCREMENT_SECONDS,
        "runner_multiplier": RUNNER_MULTIPLIER[runner] if runner in RUNNER_MULTIPLIER else None,
        "billed_units_per_worker": per_worker,
        "billed_units_total": total,
        "billed_for_substrate": visibility == "private",
        "unusable_rounding_seconds": rounding_seconds,
        "rounding_share_of_billed": round(rounding_share, 4),
        "cost_driver": "WORKER_COUNT" if total else "NONE_SUBSTRATE_NOT_BILLED",
        "measurement_ref": MEASUREMENT_REF,
        "authority_effect": "NONE_COST_BASIS_ONLY",
    }


def compare_assignments(assignments: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Bind several assignments and report whether their billed costs actually differ.

    A lifetime tiering that collapses to one billed unit is not a cost tiering, and this
    says so rather than letting distinct-looking tiers imply distinct cost.
    """
    if not assignments:
        raise WorkerCostBindingError("at least one assignment required")
    bindings = [bind_worker_cost_at_assignment(a) for a in assignments]
    totals = [b["billed_units_total"] for b in bindings]
    return {
        "schema": SCHEMA,
        "bindings": bindings,
        "billed_units_total_by_assignment": totals,
        "distinct_billed_costs": len(set(totals)),
        "tiers_are_cost_distinguishable": len(set(totals)) == len(totals),
        "authority_effect": "NONE_COST_BASIS_ONLY",
    }


__all__ = [
    "SCHEMA",
    "RUNNER_MULTIPLIER",
    "BILLING_INCREMENT_SECONDS",
    "WorkerCostBindingError",
    "billed_units_for_worker",
    "bind_worker_cost_at_assignment",
    "compare_assignments",
]
