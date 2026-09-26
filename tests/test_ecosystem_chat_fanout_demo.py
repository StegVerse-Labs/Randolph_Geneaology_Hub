"""The ecosystem-chat fan-out observation must keep claiming exactly what it proved.

The risk with a demonstration artifact is that it drifts into reading like a runtime proof.
These tests pin both what it showed and what it did not.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBS = ROOT / "data/runtime-demos/ecosystem-chat-fanout.observed.json"


class EcosystemChatFanoutObservationTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(OBS.is_file(), "observation artifact missing")
        self.d = json.loads(OBS.read_text(encoding="utf-8"))

    def test_the_set_actually_fanned_out_in_parallel(self):
        self.assertEqual(self.d["routing_mode"], "parallel")
        self.assertEqual(len(self.d["attempted_source_ids"]), 4)
        self.assertEqual(self.d["failed_source_ids"], [])

    def test_a_refusal_is_retained_as_evidence_not_dropped(self):
        self.assertEqual(self.d["refused_source_ids"], ["kimi"])
        refused = [c for c in self.d["contributions"] if c["source_id"] == "kimi"]
        self.assertEqual(len(refused), 1, "the refusing source must still appear as a contribution")
        self.assertIsNone(refused[0]["output"])

    def test_the_returned_sources_converged_with_output(self):
        returned = set(self.d["returned_source_ids"])
        self.assertEqual(returned, {"local", "anthropic", "deepseek"})
        for c in self.d["contributions"]:
            if c["source_id"] in returned:
                self.assertTrue(c["output"], c["source_id"])

    def test_the_result_validated_against_the_adapter_schema(self):
        self.assertIs(self.d["schema_validates"], True)

    def test_no_authority_was_granted_by_any_of_it(self):
        self.assertEqual(self.d["authority_effect"], "NONE_LOCAL_DEMONSTRATION_ONLY")
        self.assertFalse(any(self.d["authority_flags"].values()))

    def test_it_does_not_claim_a_real_provider_call(self):
        """The whole point: this is fixture sessions, and must never read as runtime proof."""
        self.assertIs(self.d["real_provider_call_made"], False)
        self.assertIs(self.d["intr_admission_exercised"], False)
        self.assertIs(self.d["master_records_written"], False)

    def test_the_reproducibility_finding_is_recorded(self):
        """workload_hash is content-addressed; execution_hash carries wall-clock time.

        A reconstruction that re-executes the workload can never reproduce execution_hash, so
        RECEIPT_SHA256_EQUALS_RECONSTRUCTED_RECEIPT_SHA256 has to mean replaying the recorded
        envelope. If the adapter ever makes execution_hash content-addressed, this test fails
        and the finding should be retired rather than left stale.
        """
        r = self.d["reproducibility"]
        self.assertIs(r["workload_hash_reproduces"], True)
        self.assertIs(r["execution_hash_reproduces"], False)
        self.assertIn("created_at", r["cause"])
        self.assertIn("replay", r["consequence"])

    def test_provenance_of_the_observation_is_recorded(self):
        self.assertTrue(self.d["adapter_commit"])
        self.assertEqual(self.d["schema"], "stegverse.hub.ecosystem-chat-fanout-observation/v1")


if __name__ == "__main__":
    unittest.main()
