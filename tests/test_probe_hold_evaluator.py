"""The HOLD evaluator probe must tell a reachable T0 handoff from an unreachable one.

It reads source only, so these tests build minimal source trees for both shapes
rather than depending on an SDK checkout.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools/probe_hold_evaluator.py"

EVALUATOR = '''
from tests.test_manifest_builder import governance_request
CONDITIONS = [("T0","BASELINE",""),("T1","HOLD_ENTERED",""),("T2","HOLD_PERSISTENCE",""),
              ("T3","UNAUTHORIZED_RESUME",""),("T4","AUTHORIZED_RESUME","")]
result = execute_manifest(manifest)
assert result["evaluation_boundary"] == "SDK_MANIFEST_HANDOFF", result
'''
INERT_SHIM = 'def manifest_declared_destination(canonical) -> None:\n    """Shim."""\n    return None\n'
LIVE_SHIM = ('def manifest_declared_destination(canonical):\n'
             '    egress = canonical.get("egress")\n'
             '    if not egress:\n        return None\n    return dict(egress)\n')
WORKFLOW = "on:\n  pull_request:\n    paths:\n      - 'scripts/run_independent_hold_evaluator.py'\n"


def sdk_tree(base: Path, shim: str) -> Path:
    for rel, text in (("scripts/run_independent_hold_evaluator.py", EVALUATOR),
                      ("stegverse/manifest_state_transition_runtime.py", shim),
                      (".github/workflows/independent-hold-evaluator.yml", WORKFLOW)):
        (base / rel).parent.mkdir(parents=True, exist_ok=True)
        (base / rel).write_text(text, encoding="utf-8")
    return base


def run(sdk: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(PROBE), "--sdk-root", str(sdk)],
                          capture_output=True, text=True)


class ProbeHoldEvaluatorTests(unittest.TestCase):
    def test_inert_destination_shim_makes_t0_unreachable(self):
        with tempfile.TemporaryDirectory() as d:
            out = run(sdk_tree(Path(d), INERT_SHIM))
        self.assertEqual(out.returncode, 3, out.stdout)
        self.assertIn("[DRIFT] t0-handoff-reachable", out.stdout)

    def test_live_destination_shim_leaves_t0_reachable(self):
        with tempfile.TemporaryDirectory() as d:
            out = run(sdk_tree(Path(d), LIVE_SHIM))
        self.assertIn("[ok  ] t0-handoff-reachable", out.stdout)

    def test_condition_mismatch_with_the_record_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            out = run(sdk_tree(Path(d), LIVE_SHIM))
        self.assertIn("T2: record ACTION_DURING_HOLD / evaluator HOLD_PERSISTENCE", out.stdout)
        self.assertIn("[DRIFT] authority-state-varies", out.stdout)
        self.assertIn("[DRIFT] workflow-reruns-on-runtime-change", out.stdout)

    def test_missing_sdk_root_exits_2(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run(Path(d)).returncode, 2)


if __name__ == "__main__":
    unittest.main()
