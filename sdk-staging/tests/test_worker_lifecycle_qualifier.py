from __future__ import annotations

import unittest

from stegverse import worker_lifecycle_qualifier as qual
from stegverse.purpose_bound_worker import PurposeBoundWorkerError
from stegverse.purpose_bound_worker_cost_demo import _sum_budget

CANONICAL = {
    "expected_task_execution": 6,
    "known_delay": 4,
    "inferred_unknown_delay_reserve": 8,
    "records_decomposition": 7,
    "safety_reserve": 5,
}


def assignment(**over):
    a = {"schema": qual.SCHEMA, "task_id": "T-1", "estimated_resource_cost": dict(CANONICAL)}
    a.update(over)
    return a


class WorkerLifecycleQualifierTests(unittest.TestCase):
    def test_matches_the_canonical_demonstration(self):
        r = qual.qualify_task_lifecycle(assignment())
        self.assertEqual(r["verdict"], qual.DERIVED)
        self.assertEqual(r["derived_max_lifetime_seconds"], 30)
        self.assertTrue(r["governance_window_derivable"])

    def test_derivation_delegates_to_the_sdk_sum(self):
        """One derivation, one place: the qualifier must not restate _sum_budget."""
        self.assertEqual(qual.derive_lifetime_from_resource_cost(CANONICAL), _sum_budget(CANONICAL))

    def test_no_estimate_never_defaults_a_lifetime(self):
        r = qual.qualify_task_lifecycle(assignment(estimated_resource_cost=None))
        self.assertEqual(r["verdict"], qual.NO_ESTIMATE)
        self.assertIsNone(r["derived_max_lifetime_seconds"])
        self.assertFalse(r["governance_window_derivable"])

    def test_incomplete_estimate_is_not_derivable(self):
        cost = dict(CANONICAL)
        del cost["safety_reserve"]
        r = qual.qualify_task_lifecycle(assignment(estimated_resource_cost=cost))
        self.assertEqual(r["verdict"], qual.INCOMPLETE)
        self.assertEqual(r["components_missing"], ["safety_reserve"])
        self.assertFalse(r["governance_window_derivable"])

    def test_claimed_lifetime_disagreeing_with_its_components_is_flagged(self):
        r = qual.qualify_task_lifecycle(assignment(claimed_max_lifetime_seconds=300))
        self.assertEqual(r["verdict"], qual.MISMATCH)
        self.assertEqual(r["derived_max_lifetime_seconds"], 30)
        self.assertFalse(r["governance_window_derivable"])

    def test_claimed_lifetime_matching_its_components_is_derived(self):
        r = qual.qualify_task_lifecycle(assignment(claimed_max_lifetime_seconds=30))
        self.assertEqual(r["verdict"], qual.DERIVED)

    def test_negative_component_is_rejected_by_the_sdk_sum(self):
        cost = dict(CANONICAL, safety_reserve=-1)
        with self.assertRaises(PurposeBoundWorkerError):
            qual.derive_lifetime_from_resource_cost(cost)

    def test_boolean_component_is_rejected(self):
        cost = dict(CANONICAL, known_delay=True)
        with self.assertRaises(PurposeBoundWorkerError):
            qual.derive_lifetime_from_resource_cost(cost)

    def test_wrong_schema_is_rejected(self):
        with self.assertRaises(PurposeBoundWorkerError):
            qual.qualify_task_lifecycle(assignment(schema="something.else.v1"))

    def test_missing_task_id_is_rejected(self):
        with self.assertRaises(PurposeBoundWorkerError):
            qual.qualify_task_lifecycle(assignment(task_id="  "))

    def test_identical_cost_must_produce_identical_lifetime(self):
        a = assignment(task_id="A")
        b = assignment(task_id="B")
        out = qual.qualify_many([a, b])
        self.assertEqual(out["derived_count"], 2)
        self.assertEqual(out["identical_cost_different_lifetime"], [])

    def test_qualify_many_counts_each_verdict(self):
        out = qual.qualify_many([
            assignment(task_id="A"),
            assignment(task_id="B", estimated_resource_cost=None),
            assignment(task_id="C", claimed_max_lifetime_seconds=999),
        ])
        self.assertEqual((out["derived_count"], out["no_estimate_count"], out["mismatch_count"]),
                         (1, 1, 1))

    def test_empty_batch_is_rejected(self):
        with self.assertRaises(PurposeBoundWorkerError):
            qual.qualify_many([])

    def test_qualification_grants_no_authority(self):
        r = qual.qualify_task_lifecycle(assignment())
        self.assertEqual(r["authority_effect"], "NONE_QUALIFICATION_ONLY")
        self.assertEqual(r["lifetime_invariant"], qual.LIFETIME_INVARIANT)


if __name__ == "__main__":
    unittest.main()
