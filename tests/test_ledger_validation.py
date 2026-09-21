import subprocess
import sys
from pathlib import Path


def test_cid_ledger_is_internally_consistent():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(root / "tools" / "validate_ledger.py")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
