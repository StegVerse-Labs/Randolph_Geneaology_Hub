"""Demonstrate the exact cost binding applied at worker creation / task assignment.

These tests are deterministic and offline. They demonstrate the calculation against the
SDK's own shipped cost-demo fixture, so the demonstration is of real assignment values
rather than invented ones.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from stegverse import worker_cost_binding as wcb
from stegverse.worker_cost_binding import WorkerCostBindingError

FIXTURE = Path("inspection/examples/tt-purpose-worker-cost-demo.example.json")

PRIVATE_LINUX = {"visibility": "private", "runner_class": "linux"}


def assignment(lifetime: int, workers: int = 1, substrate: dict | None = None) -> dict:
    return {
        "schema": wcb.SCHEMA,
        "derived_max_lifetime_seconds": lifetime,
        "worker_count": workers,
        "substrate": dict(substrate or PRIVATE_LINUX),
    }


class WorkerCostBindingTests(unittest.TestCase):
    def test_a_sub_minute_worker_bills_a_whole_minute(self) -> None:
        """The rounding fact, stated at its smallest."""
        self.assertEqual(wcb.billed_units_for_worker(1, substrate_visibility="private"), 1)
        self.assertEqual(wcb.billed_units_for_worker(59, substrate_visibility="private"), 1)
        self.assertEqual(wcb.billed_units_for_worker(60, substrate_visibility="private"), 1)
        self.assertEqual(wcb.billed_units_for_worker(61, substrate_visibility="private"), 2)

    def test_a_public_substrate_bills_nothing_at_any_lifetime(self) -> None:
        for lifetime in (1, 60, 3600, 86400):
            self.assertEqual(
                wcb.billed_units_for_worker(lifetime, substrate_visibility="public"), 0
            )

    def test_runner_class_multiplies_a_private_bill(self) -> None:
        self.assertEqual(
            wcb.billed_units_for_worker(30, substrate_visibility="private", runner_class="linux"), 1
        )
        self.assertEqual(
            wcb.billed_units_for_worker(30, substrate_visibility="private", runner_class="windows"), 2
        )
        # One macOS worker bills like ten Linux workers.
        self.assertEqual(
            wcb.billed_units_for_worker(30, substrate_visibility="private", runner_class="macos"), 10
        )

    def test_the_shipped_cost_tiers_are_not_cost_distinguishable(self) -> None:
        """LOW, MEDIAN and HIGH bill identically despite a 9x compute spread.

        This is the finding that matters at task assignment: the fixture's lifetime
        tiering is not a cost tiering on a billed substrate.
        """
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        tiers = fixture["individual_tasks"]
        self.assertEqual([t["expected_compute_units"] for t in tiers], [1, 3, 9])
        self.assertEqual([t["derived_max_lifetime_seconds"] for t in tiers], [15, 30, 60])

        result = wcb.compare_assignments(
            [assignment(t["derived_max_lifetime_seconds"]) for t in tiers]
        )
        self.assertEqual(result["billed_units_total_by_assignment"], [1, 1, 1])
        self.assertEqual(result["distinct_billed_costs"], 1)
        self.assertFalse(result["tiers_are_cost_distinguishable"])

    def test_worker_count_is_the_cost_driver_not_lifetime(self) -> None:
        """The concurrent case costs 3x the HIGH case while doing the same total compute."""
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        high = next(t for t in fixture["individual_tasks"] if t["cost_class"] == "HIGH")
        concurrent = fixture["concurrent_task"]
        self.assertEqual(
            high["expected_compute_units"], concurrent["aggregate_expected_compute_units"]
        )

        high_binding = wcb.bind_worker_cost_at_assignment(
            assignment(high["derived_max_lifetime_seconds"])
        )
        concurrent_binding = wcb.bind_worker_cost_at_assignment(
            assignment(
                concurrent["per_worker_derived_max_lifetime_seconds"],
                workers=concurrent["worker_count"],
            )
        )
        self.assertEqual(high_binding["billed_units_total"], 1)
        self.assertEqual(concurrent_binding["billed_units_total"], 3)
        self.assertEqual(concurrent_binding["cost_driver"], "WORKER_COUNT")

    def test_rounding_share_is_reported_and_matches_the_measured_range(self) -> None:
        """A 21s worker, the measured TVC median, wastes 39 of the 60 seconds billed."""
        binding = wcb.bind_worker_cost_at_assignment(assignment(21))
        self.assertEqual(binding["billed_units_total"], 1)
        self.assertEqual(binding["unusable_rounding_seconds"], 39)
        self.assertAlmostEqual(binding["rounding_share_of_billed"], 0.65, places=2)

    def test_an_unbilled_substrate_reports_no_rounding_waste(self) -> None:
        binding = wcb.bind_worker_cost_at_assignment(
            assignment(21, substrate={"visibility": "public", "runner_class": "linux"})
        )
        self.assertEqual(binding["billed_units_total"], 0)
        self.assertEqual(binding["unusable_rounding_seconds"], 0)
        self.assertEqual(binding["rounding_share_of_billed"], 0.0)
        self.assertEqual(binding["cost_driver"], "NONE_SUBSTRATE_NOT_BILLED")

    def test_binding_grants_no_authority(self) -> None:
        binding = wcb.bind_worker_cost_at_assignment(assignment(30))
        self.assertEqual(binding["authority_effect"], "NONE_COST_BASIS_ONLY")
        self.assertIn("measured-actions-cost-basis.json", binding["measurement_ref"])

    def test_malformed_assignments_fail_closed(self) -> None:
        with self.assertRaises(WorkerCostBindingError):
            wcb.bind_worker_cost_at_assignment({"schema": "wrong"})
        with self.assertRaises(WorkerCostBindingError):
            wcb.bind_worker_cost_at_assignment(assignment(0))
        with self.assertRaises(WorkerCostBindingError):
            wcb.bind_worker_cost_at_assignment(assignment(30, workers=0))
        with self.assertRaises(WorkerCostBindingError):
            wcb.billed_units_for_worker(30, substrate_visibility="internal")
        with self.assertRaises(WorkerCostBindingError):
            wcb.billed_units_for_worker(30, substrate_visibility="private", runner_class="risc")
        with self.assertRaises(WorkerCostBindingError):
            wcb.bind_worker_cost_at_assignment(
                {"schema": wcb.SCHEMA, "derived_max_lifetime_seconds": 30, "worker_count": 1}
            )


if __name__ == "__main__":
    unittest.main()
