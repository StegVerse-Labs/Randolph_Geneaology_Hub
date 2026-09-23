"""Keep the staged SDK qualifier honest against the survey that cites it.

tools/qualify_worker_lifecycles.py applies the staged module to the canonical task records.
If the module and the recorded survey disagree, the SDK would demonstrate a derivation this
repository no longer supports.
"""
from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGED = ROOT / "sdk-staging/stegverse/worker_lifecycle_qualifier.py"
STAGED_TEST = ROOT / "sdk-staging/tests/test_worker_lifecycle_qualifier.py"
SURVEY = ROOT / "data/cost-basis/worker-lifecycle-derivability.json"

CANONICAL = {
    "expected_task_execution": 6,
    "known_delay": 4,
    "inferred_unknown_delay_reserve": 8,
    "records_decomposition": 7,
    "safety_reserve": 5,
}


def _load():
    spec = importlib.util.spec_from_file_location("staged_worker_lifecycle_qualifier", STAGED)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_staged_files_parse():
    for path in (STAGED, STAGED_TEST):
        ast.parse(path.read_text(encoding="utf-8"))


def test_survey_records_the_corpus_condition():
    survey = json.loads(SURVEY.read_text(encoding="utf-8"))
    assert survey["tasks_surveyed"] == 163
    assert survey["derived_count"] == 1
    assert survey["no_estimate_count"] == 162
    assert survey["derived_tasks"][0]["task_id"] == "SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001"
    assert survey["derived_tasks"][0]["derived_max_lifetime_seconds"] == 30


def test_module_reproduces_the_canonical_worked_example():
    mod = _load()
    assert mod.derive_lifetime_from_resource_cost(CANONICAL) == 30


def test_module_components_match_the_canonical_model():
    mod = _load()
    assert set(mod.COST_COMPONENTS) == set(CANONICAL)
    assert mod.LIFETIME_INVARIANT == "WORKER_LIFETIME_IS_DERIVED_PER_INTENDED_TASK_NOT_GLOBALLY_FIXED"


def test_a_task_without_an_estimate_derives_nothing_and_defaults_nothing():
    mod = _load()
    r = mod.qualify_task_lifecycle({"schema": mod.SCHEMA, "task_id": "T"})
    assert r["verdict"] == mod.NO_ESTIMATE
    assert r["derived_max_lifetime_seconds"] is None


def test_qualifier_grants_no_authority():
    mod = _load()
    r = mod.qualify_task_lifecycle({"schema": mod.SCHEMA, "task_id": "T",
                                    "estimated_resource_cost": CANONICAL})
    assert r["authority_effect"] == "NONE_QUALIFICATION_ONLY"
