"""Keep the staged SDK cost binding honest against the measurement it cites.

The staged module hard-codes the billing rule derived in docs/ACTIONS_COST_BASIS.md. If
the measured record and the staged calculation ever disagree, the SDK would demonstrate a
binding this repository no longer supports -- the exact drift this repository exists to
catch. These tests tie the two together.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGED = ROOT / "sdk-staging/stegverse/worker_cost_binding.py"
STAGED_TEST = ROOT / "sdk-staging/tests/test_worker_cost_binding.py"
MEASURED = ROOT / "data/cost-basis/measured-actions-cost-basis.json"


def _load():
    spec = importlib.util.spec_from_file_location("staged_worker_cost_binding", STAGED)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_staged_files_parse():
    for path in (STAGED, STAGED_TEST):
        ast.parse(path.read_text(encoding="utf-8"))


def test_staged_binding_reproduces_the_measured_billable_units():
    """Re-derive each measured repository's billable units through the staged calculation."""
    mod = _load()
    record = json.loads(MEASURED.read_text(encoding="utf-8"))
    for repo in record["repositories"]:
        # The measurement counted whole runs; the binding bills one worker per run.
        visibility = repo["visibility"]
        if repo["runner_classes_observed"] != {"linux": repo["sampled_runs"]}:
            continue  # mixed-runner samples are not a like-for-like re-derivation
        expected = repo["sample_billed_units"]
        derived = sum(
            mod.billed_units_for_worker(60, substrate_visibility=visibility)
            for _ in range(repo["sampled_runs"])
        )
        assert derived == expected, f"{repo['repository']}: {derived} != {expected}"


def test_public_substrate_bills_nothing_in_both_measurement_and_binding():
    mod = _load()
    record = json.loads(MEASURED.read_text(encoding="utf-8"))
    for repo in record["repositories"]:
        if repo["billed_for_actions_minutes"]:
            continue
        assert repo["sample_billed_units"] == 0
        assert mod.billed_units_for_worker(3600, substrate_visibility="public") == 0


def test_rounding_rule_matches_the_documented_increment():
    mod = _load()
    assert mod.BILLING_INCREMENT_SECONDS == 60
    for seconds, units in ((1, 1), (59, 1), (60, 1), (61, 2), (120, 2), (121, 3)):
        assert mod.billed_units_for_worker(seconds, substrate_visibility="private") == units
        assert units == math.ceil(seconds / 60)


def test_runner_multipliers_are_the_published_ones():
    mod = _load()
    assert mod.RUNNER_MULTIPLIER == {"linux": 1, "windows": 2, "macos": 10}


def test_staged_module_cites_the_measurement_it_depends_on():
    mod = _load()
    assert MEASURED.name in mod.MEASUREMENT_REF
    binding = mod.bind_worker_cost_at_assignment({
        "schema": mod.SCHEMA,
        "derived_max_lifetime_seconds": 30,
        "worker_count": 1,
        "substrate": {"visibility": "private", "runner_class": "linux"},
    })
    assert binding["authority_effect"] == "NONE_COST_BASIS_ONLY"
