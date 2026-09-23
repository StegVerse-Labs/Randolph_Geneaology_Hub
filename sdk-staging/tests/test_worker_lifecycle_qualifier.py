"""Demonstrate deriving a worker lifecycle from the resource cost of the task assigned.

The canonical lifetime_model states the invariant and the five components; these tests
demonstrate the derivation against the model's own worked example, and against the
condition the canonical corpus actually exhibits -- a task that states no estimate.

Deterministic and offline.
"""
from __future__ import annotations

import unittest

from stegverse import worker_lifecycle_qualifier as wlq
from stegverse.worker_lifecycle_qualifier import WorkerLifecycleQualificationError

# The worked example from SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001.lifetime_model.
CANONICAL_COMPONENTS = {
    "expected_task_execution": 6,
    "known_delay": 4,
    "inferred_unknown_delay_reserve": 8,
    "records_decomposition": 7,
    "safety_reserve": 5,
}
CANONICAL_LIFETIME = 30


def assignment(task_id="TASK-001", cost=None, claimed=None, omit_cost=False) -> dict:
    a = {"schema": wlq.SCHEMA, "task_id": task_id}
    if not omit_cost:
        a["estimated_resource_cost"] = dict(CANONICAL_COMPONENTS if cost is None else cost)
    if claimed is not None:
        a["claimed_max_lifetime_seconds"] = claimed
    return a


class WorkerLifecycleFromTaskCostTests(unittest.TestCase):
    def test_derivation_reproduces_the_canonical_worked_example(self) -> None:
        """6 + 4 + 8 + 7 + 5 = 30, exactly as the lifetime_model states."""
        self.assertEqual(
            wlq.derive_lifetime_from_resource_cost(CANONICAL_COMPONENTS), CANONICAL_LIFETIME
        )
        result = wlq.qualify_task_lifecycle(assignment())
        self.assertEqual(result["verdict"], wlq.DERIVED)
        self.assertEqual(result["derived_max_lifetime_seconds"], CANONICAL_LIFETIME)
        self.assertTrue(result["governance_window_derivable"])
        self.assertEqual(result["lifetime_invariant"], wlq.LIFETIME_INVARIANT)

    def test_a_task_stating_no_resource_cost_derives_no_lifetime(self) -> None:
        """162 of 163 canonical task records are in this condition."""
        result = wlq.qualify_task_lifecycle(assignment(omit_cost=True))
        self.assertEqual(result["verdict"], wlq.NO_ESTIMATE)
        self.assertFalse(result["derivable"])
        self.assertIsNone(result["derived_max_lifetime_seconds"])
        self.assertFalse(result["governance_window_derivable"])
        self.assertEqual(result["components_missing"], list(wlq.COST_COMPONENTS))

    def test_no_lifetime_is_defaulted_when_the_estimate_is_absent(self) -> None:
        """A defaulted lifetime would be the globally-fixed lifetime the invariant forbids."""
        result = wlq.qualify_task_lifecycle(assignment(omit_cost=True))
        self.assertIsNone(result["derived_max_lifetime_seconds"])

    def test_an_incomplete_estimate_does_not_derive_a_lifetime(self) -> None:
        partial = dict(CANONICAL_COMPONENTS)
        del partial["safety_reserve"]
        del partial["records_decomposition"]
        result = wlq.qualify_task_lifecycle(assignment(cost=partial))
        self.assertEqual(result["verdict"], wlq.INCOMPLETE)
        self.assertFalse(result["derivable"])
        self.assertEqual(
            sorted(result["components_missing"]), ["records_decomposition", "safety_reserve"]
        )

    def test_every_component_contributes_to_the_lifetime(self) -> None:
        """Dropping any one component changes the derived lifetime, so none is decorative."""
        for component, value in CANONICAL_COMPONENTS.items():
            reduced = dict(CANONICAL_COMPONENTS, **{component: 0})
            self.assertEqual(
                wlq.derive_lifetime_from_resource_cost(reduced), CANONICAL_LIFETIME - value,
                f"{component} did not contribute",
            )

    def test_a_claimed_lifetime_disagreeing_with_its_components_fails(self) -> None:
        result = wlq.qualify_task_lifecycle(assignment(claimed=300))
        self.assertEqual(result["verdict"], wlq.MISMATCH)
        self.assertFalse(result["governance_window_derivable"])
        self.assertIn("300", result["reason"])

    def test_a_claimed_lifetime_matching_its_components_is_derived(self) -> None:
        result = wlq.qualify_task_lifecycle(assignment(claimed=CANONICAL_LIFETIME))
        self.assertEqual(result["verdict"], wlq.DERIVED)

    def test_identical_resource_cost_derives_identical_lifetime(self) -> None:
        """This is what 'derived' means, and is the property the corpus currently lacks."""
        result = wlq.qualify_many([assignment("A"), assignment("B")])
        self.assertEqual(result["derived_count"], 2)
        self.assertEqual(result["identical_cost_different_lifetime"], [])
        lifetimes = {q["derived_max_lifetime_seconds"] for q in result["qualifications"]}
        self.assertEqual(lifetimes, {CANONICAL_LIFETIME})

    def test_different_resource_cost_derives_different_lifetime(self) -> None:
        heavier = dict(CANONICAL_COMPONENTS, expected_task_execution=60)
        result = wlq.qualify_many([assignment("A"), assignment("B", cost=heavier)])
        self.assertEqual(
            [q["derived_max_lifetime_seconds"] for q in result["qualifications"]],
            [CANONICAL_LIFETIME, CANONICAL_LIFETIME + 54],
        )

    def test_a_population_of_estimateless_tasks_is_counted(self) -> None:
        result = wlq.qualify_many([assignment(f"T{i}", omit_cost=True) for i in range(5)])
        self.assertEqual(result["no_estimate_count"], 5)
        self.assertEqual(result["derived_count"], 0)

    def test_qualification_grants_no_authority(self) -> None:
        self.assertEqual(
            wlq.qualify_task_lifecycle(assignment())["authority_effect"],
            "NONE_QUALIFICATION_ONLY",
        )

    def test_malformed_assignments_fail_closed(self) -> None:
        with self.assertRaises(WorkerLifecycleQualificationError):
            wlq.qualify_task_lifecycle({"schema": "wrong"})
        with self.assertRaises(WorkerLifecycleQualificationError):
            wlq.qualify_task_lifecycle({"schema": wlq.SCHEMA})
        with self.assertRaises(WorkerLifecycleQualificationError):
            wlq.qualify_task_lifecycle(assignment(cost={**CANONICAL_COMPONENTS,
                                                       "safety_reserve": -1}))
        with self.assertRaises(WorkerLifecycleQualificationError):
            wlq.derive_lifetime_from_resource_cost({"expected_task_execution": 1})
        with self.assertRaises(WorkerLifecycleQualificationError):
            wlq.qualify_many([])


if __name__ == "__main__":
    unittest.main()
