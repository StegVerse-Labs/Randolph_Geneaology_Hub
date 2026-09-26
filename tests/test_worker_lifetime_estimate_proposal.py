"""The lifetime estimate proposal must propose only what the evidence carries.

The temptation here is to fill in 167 missing estimates with a plausible rule. These tests exist
to stop that: the proposal may carry a total only where a linked cost-basis record states one,
and may not carry a component split at all.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / "data/cost-basis/worker-lifetime-estimate-proposal.json"

ANCHOR = "SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001"


class WorkerLifetimeEstimateProposalTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PROPOSAL.is_file(), "proposal artifact missing")
        self.d = json.loads(PROPOSAL.read_text(encoding="utf-8"))

    def test_proposal_grants_nothing(self):
        self.assertEqual(self.d["authority_effect"], "NONE_PROPOSAL_ONLY")
        self.assertIs(self.d["grants_registration"], False)
        self.assertIs(self.d["sets_any_lifetime"], False)

    def test_anchor_reproduces_the_canonical_lifetime(self):
        """The whole derivation rests on beats == seconds, shown on the one calibrated task."""
        a = self.d["anchor"]
        self.assertEqual(a["task_id"], ANCHOR)
        self.assertIs(a["verified"], True)
        self.assertEqual(a["value_seconds"], 30)

    def test_every_proposal_cites_the_record_it_came_from(self):
        for p in self.d["proposed"]:
            src = p["source"]
            self.assertTrue(src["cost_basis_record"].startswith("cost-basis/"), p["task_id"])
            self.assertEqual(src["field"], "hb_estimate.expected_completion_beats")
            self.assertIsInstance(p["proposed_derived_max_lifetime_seconds"], int)
            self.assertGreaterEqual(p["proposed_derived_max_lifetime_seconds"], 0)

    def test_no_component_split_is_proposed(self):
        """One calibration point cannot determine five coefficients; inventing them is the failure
        mode this artifact exists to avoid."""
        for p in self.d["proposed"]:
            self.assertIsNone(p["components_proposed"], p["task_id"])
        block = self.d["component_split_not_proposed"]
        self.assertEqual(len(block["components"]), 5)
        self.assertIn("cannot determine five coefficients", block["why"])
        self.assertTrue(block["what_would_resolve_it"].strip())

    def test_no_proposal_contradicts_an_existing_lifetime_model(self):
        for p in self.d["proposed"]:
            self.assertIsNot(p["agrees_with_existing_lifetime_model"], False,
                             f"{p['task_id']} contradicts its own canonical lifetime_model")

    def test_unbound_records_are_reported_not_guessed(self):
        """A record naming no task must be listed for an owner to bind, never matched heuristically."""
        self.assertGreater(self.d["cost_basis_unbound_count"], 0)
        for u in self.d["cost_basis_unbound"]:
            self.assertTrue(u["cost_basis_record"].startswith("cost-basis/"))
            self.assertIn("names no canonical task id", u["reason"])
        self.assertIn("must be authored", self.d["binding_is_not_inferrable"])

    def test_the_unbound_estimates_are_counted(self):
        """This count is the actionable number: estimates that exist and cannot be used."""
        carrying = sum(1 for u in self.d["cost_basis_unbound"]
                       if u["expected_completion_beats"] is not None)
        self.assertEqual(carrying, self.d["cost_basis_unbound_carrying_an_estimate"])
        self.assertGreater(carrying, 0)

    def test_counts_are_internally_consistent(self):
        self.assertEqual(len(self.d["proposed"]), self.d["proposed_count"])
        self.assertEqual(len(self.d["cost_basis_unbound"]), self.d["cost_basis_unbound_count"])
        distinct = {p["task_id"] for p in self.d["proposed"]}
        self.assertEqual(self.d["tasks_still_without_any_linked_estimate"],
                         self.d["tasks_total"] - len(distinct))

    def test_provenance_is_recorded(self):
        o = self.d["observed_from"]
        for k in ("repository", "ref", "commit", "canonical_task_records"):
            self.assertTrue(o.get(k), k)


if __name__ == "__main__":
    unittest.main()
