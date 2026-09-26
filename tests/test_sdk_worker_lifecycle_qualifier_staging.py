"""The staged SDK files must stay identical to the versions verified inside the SDK clone.

This repository cannot push to StegVerse-org/StegVerse-SDK, so these files wait here. What makes
them trustworthy is that they were verified in a real clone of the SDK and have not changed
since; these digests are how that stays true.
"""
from __future__ import annotations

import ast
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / "sdk-staging"

# sha256 of the exact files that passed `python3 -m unittest tests.test_worker_lifecycle_qualifier`
# inside StegVerse-org/StegVerse-SDK at ecccfb511c6baf012c33ea27aa8e747dfe482273.
VERIFIED = {
    "stegverse/worker_lifecycle_qualifier.py":
        "988a82615ff251d0",
    "tests/test_worker_lifecycle_qualifier.py":
        "ef9fedea6727928d",
}


class StagedSdkFilesTests(unittest.TestCase):
    def test_staged_files_match_what_was_verified_in_the_sdk(self):
        for rel, prefix in VERIFIED.items():
            path = STAGING / rel
            self.assertTrue(path.is_file(), f"missing staged file: {rel}")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertTrue(digest.startswith(prefix),
                            f"{rel} changed since SDK verification: {digest[:16]} != {prefix}")

    def test_staged_files_are_valid_python(self):
        for rel in VERIFIED:
            ast.parse((STAGING / rel).read_text(encoding="utf-8"), filename=rel)

    def test_module_delegates_the_sum_to_the_sdk_rather_than_restating_it(self):
        """The whole point of the SDK-shaped rewrite: one derivation, one place."""
        src = (STAGING / "stegverse/worker_lifecycle_qualifier.py").read_text(encoding="utf-8")
        self.assertIn("from .purpose_bound_worker_cost_demo import _sum_budget", src)
        self.assertIn("return _sum_budget(cost)", src)
        # It must not carry its own summation of the five components.
        self.assertNotIn("sum(_nonneg_int(cost[c], c) for c in COST_COMPONENTS)", src)

    def test_module_never_defaults_a_lifetime(self):
        src = (STAGING / "stegverse/worker_lifecycle_qualifier.py").read_text(encoding="utf-8")
        self.assertIn("TASK_STATES_NO_RESOURCE_COST_ESTIMATE", src)
        self.assertIn("NONE_QUALIFICATION_ONLY", src)


class OfflineShimContractTests(unittest.TestCase):
    """The census shim stands in for the SDK's _sum_budget; it must hold the same contract.

    The SDK's version is authoritative. This pins the stand-in to the canonical demonstration
    so an offline census cannot quietly compute a different lifetime from the SDK.
    """

    def qualifier(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("qwl", ROOT / "tools/qualify_worker_lifecycles.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.load_qualifier()

    def test_canonical_components_sum_to_the_demonstrated_lifetime(self):
        wlq = self.qualifier()
        self.assertEqual(wlq.derive_lifetime_from_resource_cost({
            "expected_task_execution": 6, "known_delay": 4,
            "inferred_unknown_delay_reserve": 8, "records_decomposition": 7,
            "safety_reserve": 5}), 30)

    def test_shim_rejects_negative_and_boolean_components(self):
        wlq = self.qualifier()
        base = {"expected_task_execution": 6, "known_delay": 4,
                "inferred_unknown_delay_reserve": 8, "records_decomposition": 7,
                "safety_reserve": 5}
        for bad in ({**base, "safety_reserve": -1}, {**base, "known_delay": True}):
            with self.assertRaises(ValueError):
                wlq.derive_lifetime_from_resource_cost(bad)

    def test_a_task_without_an_estimate_still_derives_nothing(self):
        wlq = self.qualifier()
        r = wlq.qualify_task_lifecycle({"schema": wlq.SCHEMA, "task_id": "T",
                                        "estimated_resource_cost": None})
        self.assertEqual(r["verdict"], wlq.NO_ESTIMATE)
        self.assertIsNone(r["derived_max_lifetime_seconds"])


if __name__ == "__main__":
    unittest.main()
