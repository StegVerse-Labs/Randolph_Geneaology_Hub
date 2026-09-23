"""Keep the staged SDK qualifier honest against the corpus survey that cites it.

tools/qualify_worker_lifecycles.py applies the staged module to the canonical corpus. If
the module and the recorded survey disagree, the SDK would demonstrate a qualification this
repository no longer supports. These tests tie them together.
"""
from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGED = ROOT / "sdk-staging/stegverse/worker_lifecycle_qualifier.py"
STAGED_TEST = ROOT / "sdk-staging/tests/test_worker_lifecycle_qualifier.py"
SURVEY = ROOT / "data/cost-basis/worker-lifecycle-qualification.json"


def _load():
    spec = importlib.util.spec_from_file_location("staged_worker_lifecycle_qualifier", STAGED)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _assignment(mod, expiry, completion=1, idle=0, derivation=None):
    a = {
        "schema": mod.SCHEMA,
        "cost_estimate": {"compute_units": 1, "failure_recovery_units": 1},
        "lifecycle": {
            "expected_completion_beats": completion,
            "expected_idle_beats": idle,
            "expiry_candidate_beats": expiry,
        },
    }
    if derivation:
        a["derivation"] = derivation
    return a


def test_staged_files_parse():
    for path in (STAGED, STAGED_TEST):
        ast.parse(path.read_text(encoding="utf-8"))


def test_survey_records_the_corpus_condition():
    survey = json.loads(SURVEY.read_text(encoding="utf-8"))
    assert survey["records_qualified"] == 48
    assert survey["qualified_count"] == 1
    assert survey["asserted_count"] == 47
    assert survey["unsatisfiable_count"] == 0
    assert survey["cost_determines_lifecycle"] is False
    assert len(survey["identical_cost_different_expiry"]) == 2


def test_a_lifetime_without_a_derivation_is_asserted():
    mod = _load()
    assert mod.qualify_worker_lifecycle(_assignment(mod, 16))["verdict"] == mod.ASSERTED


def test_a_derivation_naming_a_carried_factor_qualifies():
    mod = _load()
    r = mod.qualify_worker_lifecycle(_assignment(
        mod, 16, derivation={"basis": "per compute unit", "derived_from": ["compute_units"]}))
    assert r["verdict"] == mod.QUALIFIED


def test_expiry_below_expected_work_is_unsatisfiable():
    mod = _load()
    r = mod.qualify_worker_lifecycle(_assignment(mod, 4, completion=8, idle=2))
    assert r["verdict"] == mod.UNSATISFIABLE


def test_identical_cost_different_expiry_is_reported_as_a_collision():
    mod = _load()
    r = mod.qualify_many([_assignment(mod, 64), _assignment(mod, 4096)])
    assert r["cost_determines_lifecycle"] is False
    assert r["identical_cost_different_expiry"][0]["expiries"] == [64, 4096]


def test_qualifier_grants_no_authority():
    mod = _load()
    assert mod.qualify_worker_lifecycle(_assignment(mod, 16))["authority_effect"] == "NONE_QUALIFICATION_ONLY"
