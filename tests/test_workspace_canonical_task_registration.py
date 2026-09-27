"""Pin the WorkSpace canonical task registration.

This repository cannot push to StegVerse-Labs/.github, so the registration is
generated here and applied by a registry owner. These tests hold the generated
artifacts to the registry's own contracts, so a drifted generator fails here
rather than in the registry.

The per-task contract asserted below is transcribed from
StegVerse-Labs/.github:scripts/validate_canonical_work_coordination.py as read
at origin/main 495832cd, and from TASK_REGISTRY_CANONICAL_INVARIANTS.md.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import register_workspace_canonical_task as reg  # noqa: E402

TASK_ID = "STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001"


class TestVectorDerivation(unittest.TestCase):
    """The COSV vector must be derived from exact metrics, never hand-written."""

    def test_vector_is_derived_from_exact_metrics(self):
        self.assertEqual(reg.VECTOR, reg.derive_vector(reg.EXACT_METRICS))

    def test_vector_matches_profile_width(self):
        self.assertEqual(len(reg.VECTOR), 14)

    def test_vector_value(self):
        # L=1 UNCLAIMED, R=0, U=5, IVGOC=0, M=1, T=1, B=4, E=0, A=0, P=0
        self.assertEqual(reg.VECTOR, "10500000114000")

    def test_symbol_order_matches_canonical_profile(self):
        self.assertEqual(reg.EXACT_METRICS["symbol_order"], "LRUIVGOCMTBEAP")

    def test_every_metric_carries_evidence(self):
        metrics = set(reg.EXACT_METRICS) - {"symbol_order"}
        self.assertEqual(metrics, set(reg.METRIC_EVIDENCE))

    def test_derivation_round_trips_a_known_registry_vector(self):
        """QUANTUM-RESILIENCE-001's published derivation must reproduce."""
        published = {
            "symbol_order": "LRUIVGOCMTBEAP",
            "lifecycle": "UNCLAIMED",
            "archive_ready": False,
            "unassigned_work": 1,
            "chat_owned_implementation": 0,
            "chat_owned_validation": 0,
            "chat_owned_integration": 0,
            "chat_owned_observation": 0,
            "chat_owned_credentials": 0,
            "canonical_owner_installed": True,
            "thread_required": False,
            "blocker_count": 0,
            "evidence_complete": False,
            "activated": False,
            "propagated": False,
        }
        self.assertEqual(reg.derive_vector(published), "10100000100000")

    def test_quantity_saturates_at_nine(self):
        metrics = dict(reg.EXACT_METRICS, unassigned_work=25)
        self.assertEqual(reg.derive_vector(metrics)[2], "9")

    def test_unknown_ternary_encodes_as_two(self):
        metrics = dict(reg.EXACT_METRICS, activated=None)
        self.assertEqual(reg.derive_vector(metrics)[12], "2")


class TestMintsNoAuthority(unittest.TestCase):
    """TASK_REGISTRY_CANONICAL_INVARIANTS.md: the claim/fence projection."""

    def setUp(self):
        self.task = reg.build_task()

    def test_worker_claim_authority_is_workercoordinator(self):
        self.assertEqual(self.task["worker_claim"]["authority"], "WORKERCOORDINATOR")

    def test_worker_claim_is_projection_only(self):
        self.assertIs(self.task["worker_claim"]["projection_only"], True)

    def test_no_claim_or_fence_reference_is_asserted(self):
        self.assertIsNone(self.task["worker_claim"]["claim_ref"])
        self.assertIsNone(self.task["worker_claim"]["fence_ref"])

    def test_current_session_is_never_claim_authority(self):
        """The invariant names CURRENT_SESSION as forbidden, verbatim."""
        self.assertNotIn("CURRENT_SESSION", json.dumps(self.task["worker_claim"]))

    def test_coordination_state_is_proposed_and_unclaimed(self):
        self.assertEqual(self.task["coordination_state"], "PROPOSED")
        self.assertEqual(self.task["checkout_state"], "UNCLAIMED")

    def test_authority_effect_grants_nothing(self):
        self.assertEqual(
            self.task["authority_effect"], "NONE_COORDINATION_REGISTRATION_ONLY"
        )

    def test_user_verification_stays_with_kv_skap_vault(self):
        self.assertEqual(self.task["authority_model"]["user_verification"], "KV_SKAP_VAULT")

    def test_credential_authority_stays_tv_tvc(self):
        self.assertEqual(self.task["authority_model"]["credential_authority"], "TV/TVC")

    def test_github_holds_no_runtime_authority(self):
        self.assertEqual(self.task["authority_model"]["github_runtime_authority"], "NONE")


class TestValidatorPerTaskContract(unittest.TestCase):
    """Every per-task requirement in validate_canonical_work_coordination.py."""

    def setUp(self):
        self.task = reg.build_task()

    def test_task_id_and_correlation_id_present(self):
        for field in ("task_id", "correlation_id"):
            self.assertIsInstance(self.task[field], str)
            self.assertTrue(self.task[field])

    def test_runtime_requirements_is_a_dict(self):
        self.assertIsInstance(self.task["runtime_requirements"], dict)

    def test_runtime_capabilities_is_a_list(self):
        self.assertIsInstance(self.task["runtime_requirements"]["capabilities"], list)
        self.assertTrue(self.task["runtime_requirements"]["capabilities"])

    def test_runtime_requirement_flags_are_boolean(self):
        for flag in ("mutation_required", "deployment_required",
                     "current_observation_required"):
            self.assertIsInstance(self.task["runtime_requirements"][flag], bool)

    def test_blocker_dependency_ids_are_a_subset_of_dependency_ids(self):
        blockers = {b["dependency_id"] for b in self.task["blockers"]}
        dependencies = {d["dependency_id"] for d in self.task["dependencies"]}
        self.assertTrue(blockers.issubset(dependencies))

    def test_dependencies_are_objects_not_strings(self):
        """A list of strings crashes the validator's set comprehension."""
        for dependency in self.task["dependencies"]:
            self.assertIsInstance(dependency, dict)
            self.assertIn("dependency_id", dependency)

    def test_no_runtime_resolution_is_projected(self):
        """Omitted rather than guessed: it would have to pin the runtime-map generation."""
        self.assertNotIn("runtime_resolution", self.task)

    def test_not_closed_so_completion_gate_does_not_apply(self):
        self.assertNotEqual(self.task["coordination_state"], "CLOSED")


class TestExecutionSubstrateResolution(unittest.TestCase):
    """Transcribed from StegVerse-Labs/.github:scripts/validate_task_registration_substrate_resolution.py.

    That validator treats any record carrying a runtime_requirements dict as
    runtime-capable and then requires execution_substrate_resolution. The first
    delivery of this registration omitted the block and CI rejected it, so the
    contract is pinned here rather than rediscovered in the registry.
    """

    REVIEW_ORDER = [
        "STEG-BROWSER-RETAINED-RESIDENT-NODE",
        "STEGOS-CURRENT-DEVICE-NODE",
        "STEG-BROWSER-EPHEMERAL-LEASE",
        "SAME-DEVICE-SITE-SAFARI-SERVICE-WORKER",
        "ADMITTED-EPHEMERAL-STEGOS-NODE",
        "REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT",
    ]
    DISPOSITIONS = {"SELECTED", "SUITABLE", "PENDING_EVIDENCE", "UNSUITABLE", "NOT_APPLICABLE"}
    LIMITATIONS = {"NONE", "EVIDENCE_REACHABILITY", "ARCHITECTURAL", "AUTHORITY", "PLATFORM", "NOT_APPLICABLE"}

    def setUp(self):
        self.task = reg.build_task()
        self.record = reg.build_record()
        self.resolution = self.task["execution_substrate_resolution"]

    def test_runtime_capable_record_carries_a_resolution(self):
        """The exact condition the registry validator fails on."""
        self.assertIsInstance(self.record.get("runtime_requirements"), dict)
        self.assertIsInstance(self.record.get("execution_substrate_resolution"), dict)

    def test_registry_row_and_record_carry_the_same_resolution(self):
        """runtime_requirements was once on the record but not the row; do not repeat it."""
        self.assertEqual(
            self.task["execution_substrate_resolution"],
            self.record["execution_substrate_resolution"],
        )

    def test_schema_is_exact(self):
        self.assertEqual(
            self.resolution["schema"], "stegverse.execution-substrate-resolution/v1"
        )

    def test_review_order_is_canonical_single_device_first(self):
        self.assertEqual(self.resolution["review_order"], self.REVIEW_ORDER)

    def test_resolution_mints_no_authority(self):
        self.assertEqual(self.resolution["authority_effect"], "NONE")

    def test_second_user_operated_device_is_not_allowed(self):
        self.assertIs(self.resolution["second_user_operated_device_allowed"], False)

    def test_external_device_is_not_required(self):
        self.assertIsInstance(self.resolution["external_device_required"], bool)
        self.assertIs(self.resolution["external_device_required"], False)

    def test_one_review_per_substrate_in_canonical_order(self):
        seen = [row["substrate_id"] for row in self.resolution["reviews"]]
        self.assertEqual(seen, self.REVIEW_ORDER)

    def test_dispositions_and_limitations_are_in_the_allowed_sets(self):
        for row in self.resolution["reviews"]:
            self.assertIn(row["disposition"], self.DISPOSITIONS)
            self.assertIn(row["limitation_class"], self.LIMITATIONS)

    def test_evidence_refs_are_string_arrays(self):
        for row in self.resolution["reviews"]:
            self.assertIsInstance(row["evidence_refs"], list)
            for ref in row["evidence_refs"]:
                self.assertIsInstance(ref, str)
                self.assertTrue(ref.strip())

    def test_nothing_is_selected_because_nothing_was_observed(self):
        """No runtime observation exists, so no substrate can be shown suitable."""
        self.assertIsNone(self.resolution["selected_substrate_id"])
        self.assertEqual(
            [r for r in self.resolution["reviews"] if r["disposition"] == "SELECTED"], []
        )

    def test_no_evidence_gap_is_promoted_to_unsuitable(self):
        """The validator forbids it, and ruling a substrate out would be a claim."""
        for row in self.resolution["reviews"]:
            if row["limitation_class"] == "EVIDENCE_REACHABILITY":
                self.assertNotEqual(row["disposition"], "UNSUITABLE")

    def test_every_substrate_is_pending_evidence(self):
        for row in self.resolution["reviews"]:
            self.assertEqual(row["disposition"], "PENDING_EVIDENCE")
            self.assertEqual(row["limitation_class"], "EVIDENCE_REACHABILITY")


class TestGoalCoversEveryStatedProperty(unittest.TestCase):
    """The four properties, plus the invariant that governs them."""

    def setUp(self):
        self.goal = reg.build_task()["goal"].lower()
        self.predicates = reg.EXPECTED_EVIDENCE_PREDICATES

    def test_goal_names_mykv_and_org_kv(self):
        self.assertIn("mykv", self.goal)
        self.assertIn("org kv", self.goal)

    def test_goal_names_capability_functions(self):
        self.assertIn("capability", self.goal)

    def test_goal_names_skap_vault_ingress(self):
        self.assertIn("skap vault", self.goal)

    def test_goal_names_state_transition_derivation(self):
        self.assertIn("state transitions", self.goal)

    def test_goal_names_any_os_and_any_device(self):
        self.assertIn("any operating system", self.goal)
        self.assertIn("any device", self.goal)

    def test_a_predicate_covers_a_device_that_never_held_a_registration(self):
        self.assertIn(
            "WORKSPACE_PROJECTION_EXACT_ON_A_DEVICE_THAT_NEVER_HELD_A_REGISTRATION",
            self.predicates,
        )

    def test_a_predicate_covers_a_second_operating_system(self):
        self.assertIn(
            "WORKSPACE_PROJECTION_EXACT_ON_A_SECOND_OPERATING_SYSTEM", self.predicates
        )

    def test_a_predicate_forbids_a_secondary_user_verifier(self):
        self.assertIn(
            "NO_SECONDARY_USER_VERIFIER_OUTSIDE_KV_SKAP_VAULT_OBSERVED", self.predicates
        )

    def test_a_predicate_forbids_a_physical_device_identity_gate(self):
        self.assertIn("NO_PHYSICAL_DEVICE_IDENTITY_GATE_OBSERVED", self.predicates)

    def test_five_work_units_match_the_unassigned_work_count(self):
        self.assertEqual(len(reg.WORK_UNITS), reg.EXACT_METRICS["unassigned_work"])

    def test_four_blockers_match_the_blocker_count(self):
        self.assertEqual(len(reg.BLOCKERS), reg.EXACT_METRICS["blocker_count"])

    def test_no_work_unit_claims_an_owner(self):
        for unit in reg.WORK_UNITS:
            self.assertIsNone(unit["assigned_owner"])

    def test_every_blocker_is_a_registry_owner_decision(self):
        for blocker in reg.BLOCKERS:
            self.assertEqual(blocker["decision_owner"], "REGISTRY_OWNER")


class TestNameCollisionIsNotRepeated(unittest.TestCase):
    def test_task_id_is_distinguishable_from_the_google_workspace_task(self):
        self.assertNotIn("EXTCOLLAB", TASK_ID)
        self.assertTrue(TASK_ID.startswith("STEGVERSE-WORKSPACE-"))

    def test_the_google_workspace_task_is_recorded_as_adjacent_not_parent(self):
        task = reg.build_task()
        self.assertIsNone(task["parent_task_id"])
        self.assertIn("SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004",
                      task["adjacent_task_refs"])


class TestFourSurfacesAgree(unittest.TestCase):
    """The registry keeps a task in four places; they must not drift."""

    def setUp(self):
        self.task = reg.build_task()
        self.record = reg.build_record()
        self.vector_file = reg.build_vector_file()
        self.index_row = reg.build_index_row()

    def test_task_id_is_identical_across_all_four(self):
        ids = {
            self.task["task_id"],
            self.record["task_id"],
            self.index_row["task_id"],
            self.vector_file["identity"].rsplit(":", 1)[-1],
        }
        self.assertEqual(ids, {TASK_ID})

    def test_vector_is_identical_across_all_three_that_carry_it(self):
        self.assertEqual(
            {self.task["cosv_task_vector"], self.vector_file["vector"],
             self.index_row["vector"]},
            {reg.VECTOR},
        )

    def test_index_row_points_at_the_vector_file(self):
        self.assertEqual(
            self.index_row["source_state_vector_ref"],
            f"control/task-vectors/{TASK_ID}.json",
        )

    def test_vector_file_cites_the_record(self):
        self.assertIn(
            f"data/canonical-task-records/{TASK_ID}.json",
            self.vector_file["evidence_refs"],
        )

    def test_every_surface_disclaims_authority(self):
        self.assertEqual(self.vector_file["authority_effect"], "NONE")
        self.assertEqual(self.index_row["authority_effect"], "NONE")

    def test_all_four_surfaces_are_json_serialisable(self):
        for payload in (self.task, self.record, self.vector_file, self.index_row):
            json.loads(json.dumps(payload))


class TestNonclaims(unittest.TestCase):
    def test_registration_disclaims_execution_authority(self):
        self.assertIn(
            "REGISTRATION_IS_COORDINATION_INTENT_ONLY_AND_GRANTS_NO_EXECUTION_AUTHORITY",
            reg.NONCLAIMS,
        )

    def test_eviction_policy_is_flagged_as_cited_not_observed(self):
        self.assertIn(
            "SEVEN_DAY_BROWSER_STORAGE_EVICTION_IS_CITED_PUBLISHED_PLATFORM_POLICY_NOT_AN_OBSERVED_FAILURE",
            reg.NONCLAIMS,
        )

    def test_no_runtime_observation_is_claimed(self):
        self.assertIn("NO_RUNTIME_OBSERVATION_OF_WORKSPACE_IS_CLAIMED", reg.NONCLAIMS)

    def test_the_contested_cosv_reading_is_disclosed(self):
        """canonical_owner_installed=1 is a reading a reviewer may reject."""
        self.assertIn(
            "COSV_CANONICAL_OWNER_INSTALLED_REFERS_TO_THE_REGISTRY_OWNER_ROW_NOT_AN_INSTALLED_RUNTIME_OWNER",
            reg.NONCLAIMS,
        )
        self.assertIn("10500000014000", reg.METRIC_EVIDENCE["canonical_owner_installed"])


if __name__ == "__main__":
    unittest.main()
