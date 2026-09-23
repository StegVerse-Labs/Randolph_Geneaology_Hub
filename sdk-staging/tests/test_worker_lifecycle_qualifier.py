"""Demonstrate what qualifies a worker lifecycle at task assignment.

Worker cost analysis determines the lifecycle; the lifecycle is what governance and record
keeping bind to. These tests demonstrate the qualification, including the case the
canonical corpus actually exhibits: a lifetime that is asserted rather than derived.

Deterministic and offline.
"""
from __future__ import annotations

import unittest

from stegverse import worker_lifecycle_qualifier as wlq
from stegverse.worker_lifecycle_qualifier import WorkerLifecycleQualificationError

COST = {
    "compute_units": 4,
    "token_units": 0,
    "storage_bytes": 131072,
    "network_bytes": 0,
    "operator_seconds": 0,
    "latency_ms": None,
    "failure_recovery_units": 2,
}


def assignment(expiry: int, completion: int = 1, idle: int = 0, derivation=None, cost=None) -> dict:
    a = {
        "schema": wlq.SCHEMA,
        "cost_estimate": dict(cost or COST),
        "lifecycle": {
            "expected_completion_beats": completion,
            "expected_idle_beats": idle,
            "expiry_candidate_beats": expiry,
        },
    }
    if derivation is not None:
        a["derivation"] = derivation
    return a


class WorkerLifecycleQualifierTests(unittest.TestCase):
    def test_a_lifetime_with_no_stated_derivation_is_asserted_not_qualified(self) -> None:
        """The canonical case: 47 of 48 records state no derivation."""
        result = wlq.qualify_worker_lifecycle(assignment(16))
        self.assertEqual(result["verdict"], wlq.ASSERTED)
        self.assertFalse(result["qualified"])
        self.assertFalse(result["governance_window_explained"])
        self.assertIn("unexplained", result["reason"])

    def test_a_lifetime_derived_from_a_named_cost_factor_qualifies(self) -> None:
        result = wlq.qualify_worker_lifecycle(assignment(
            16,
            derivation={"basis": "four beats per compute unit, plus recovery reserve",
                        "derived_from": ["compute_units", "failure_recovery_units"]},
        ))
        self.assertEqual(result["verdict"], wlq.QUALIFIED)
        self.assertTrue(result["qualified"])
        self.assertTrue(result["governance_window_explained"])
        self.assertEqual(result["derivation_factors"], ["compute_units", "failure_recovery_units"])

    def test_a_derivation_naming_no_real_cost_factor_does_not_qualify(self) -> None:
        """A basis must refer to the cost estimate, not to nothing."""
        result = wlq.qualify_worker_lifecycle(assignment(
            16, derivation={"basis": "operational judgement", "derived_from": ["vibes"]}
        ))
        self.assertEqual(result["verdict"], wlq.ASSERTED)

    def test_an_expiry_below_expected_work_is_unsatisfiable(self) -> None:
        """A worker required to finish after it expires cannot complete its purpose."""
        result = wlq.qualify_worker_lifecycle(assignment(4, completion=8, idle=2))
        self.assertEqual(result["verdict"], wlq.UNSATISFIABLE)
        self.assertFalse(result["qualified"])

    def test_unsatisfiable_outranks_a_stated_derivation(self) -> None:
        """Stating a derivation cannot rescue an impossible lifetime."""
        result = wlq.qualify_worker_lifecycle(assignment(
            4, completion=8, idle=2,
            derivation={"basis": "per compute unit", "derived_from": ["compute_units"]},
        ))
        self.assertEqual(result["verdict"], wlq.UNSATISFIABLE)

    def test_headroom_is_reported_so_an_unexplained_window_is_visible(self) -> None:
        """The corpus spans 2.0x to 2666.7x headroom with nothing stating why."""
        tight = wlq.qualify_worker_lifecycle(assignment(4, completion=2, idle=0))
        wide = wlq.qualify_worker_lifecycle(assignment(4096, completion=1, idle=1))
        self.assertEqual(tight["headroom_ratio"], 2.0)
        self.assertEqual(wide["headroom_ratio"], 2048.0)
        self.assertEqual(tight["verdict"], wlq.ASSERTED)
        self.assertEqual(wide["verdict"], wlq.ASSERTED)

    def test_identical_cost_with_different_expiry_shows_cost_does_not_determine_lifecycle(self) -> None:
        """Reproduces the corpus collision: same cost inputs, expiries 64x apart."""
        result = wlq.qualify_many([assignment(64), assignment(4096)])
        self.assertFalse(result["cost_determines_lifecycle"])
        self.assertEqual(len(result["identical_cost_different_expiry"]), 1)
        self.assertEqual(result["identical_cost_different_expiry"][0]["expiries"], [64, 4096])
        self.assertEqual(result["asserted_count"], 2)

    def test_identical_cost_with_identical_expiry_reports_no_collision(self) -> None:
        result = wlq.qualify_many([assignment(64), assignment(64)])
        self.assertTrue(result["cost_determines_lifecycle"])
        self.assertEqual(result["identical_cost_different_expiry"], [])

    def test_qualification_grants_no_authority(self) -> None:
        result = wlq.qualify_worker_lifecycle(assignment(16))
        self.assertEqual(result["authority_effect"], "NONE_QUALIFICATION_ONLY")

    def test_malformed_assignments_fail_closed(self) -> None:
        with self.assertRaises(WorkerLifecycleQualificationError):
            wlq.qualify_worker_lifecycle({"schema": "wrong"})
        with self.assertRaises(WorkerLifecycleQualificationError):
            wlq.qualify_worker_lifecycle(assignment(0))
        with self.assertRaises(WorkerLifecycleQualificationError):
            wlq.qualify_worker_lifecycle(assignment(16, completion=-1))
        with self.assertRaises(WorkerLifecycleQualificationError):
            # A cost estimate stating no recognised factor cannot qualify anything.
            wlq.qualify_worker_lifecycle(assignment(16, cost={"unrelated": 1}))
        with self.assertRaises(WorkerLifecycleQualificationError):
            wlq.qualify_many([])


if __name__ == "__main__":
    unittest.main()
