import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import cid_registrar  # noqa: E402
import validate_ledger  # noqa: E402


def write_namespaces_file(tmp_root, *namespaces):
    path = tmp_root / "NAMESPACES.md"
    rows = "\n".join(f"| `{ns}` | Test |" for ns in namespaces)
    path.write_text(f"# Registered Namespaces\n\n| Namespace | Family |\n|---|---|\n{rows}\n", encoding="utf-8")
    return path


def test_registered_namespace_passes(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = pathlib.Path(tmp)
        namespaces_file = write_namespaces_file(tmp_root, "RND", "LND")
        monkeypatch.setattr(validate_ledger, "NAMESPACES_FILE", namespaces_file)

        registered, errors = validate_ledger.load_registered_namespaces()
        assert errors == []
        assert registered == {"RND", "LND"}

        records = {"RND-1900-001-TN": {"file": tmp_root / "f.md"}}
        assert validate_ledger.check_namespaces(records, registered) == []


def test_unregistered_namespace_fails_ledger_validation(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = pathlib.Path(tmp)
        namespaces_file = write_namespaces_file(tmp_root, "RND")
        monkeypatch.setattr(validate_ledger, "ROOT", tmp_root)
        monkeypatch.setattr(validate_ledger, "NAMESPACES_FILE", namespaces_file)

        registered, errors = validate_ledger.load_registered_namespaces()
        assert errors == []

        records = {"ZZZ-1900-001-TN": {"file": tmp_root / "f.md"}}
        problems = validate_ledger.check_namespaces(records, registered)
        assert len(problems) == 1
        assert "ZZZ" in problems[0]
        assert "not registered" in problems[0] or "isn't registered" in problems[0]


def test_missing_namespaces_file_fails_closed(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = pathlib.Path(tmp)
        monkeypatch.setattr(validate_ledger, "ROOT", tmp_root)
        monkeypatch.setattr(validate_ledger, "NAMESPACES_FILE", tmp_root / "does-not-exist.md")

        registered, errors = validate_ledger.load_registered_namespaces()
        assert registered is None
        assert len(errors) == 1


def test_birth_claim_with_unregistered_namespace_blocks_minting(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = pathlib.Path(tmp)
        individuals = tmp_root / "Individuals"
        claims_dir = tmp_root / "Claims"
        individuals.mkdir()
        claims_dir.mkdir()
        index_file = tmp_root / "CID_Index_Master.md"
        index_file.write_text(
            "# Index\n\n<!-- BEGIN GENERATED: tools/validate_ledger.py -->\n<!-- END GENERATED -->\n",
            encoding="utf-8",
        )
        namespaces_file = write_namespaces_file(tmp_root, "RND")  # ZZZ deliberately not registered

        monkeypatch.setattr(validate_ledger, "ROOT", tmp_root)
        monkeypatch.setattr(validate_ledger, "INDIVIDUALS", individuals)
        monkeypatch.setattr(validate_ledger, "INDEX_FILE", index_file)
        monkeypatch.setattr(validate_ledger, "NAMESPACES_FILE", namespaces_file)
        monkeypatch.setattr(cid_registrar, "ROOT", tmp_root)
        monkeypatch.setattr(cid_registrar, "INDIVIDUALS", individuals)
        monkeypatch.setattr(cid_registrar, "CLAIMS_DIR", claims_dir)

        import json
        claim = {
            "claim_id": "CLM-test-birth",
            "claim_type": "birth",
            "subject_cid": "PENDING:test-person",
            "assertion": {"full_legal_name": "Test Person", "namespace": "ZZZ", "birth_year": 1900, "birth_state": "TN"},
            "source": {"evidence_level": "A", "description": "primary record"},
            "submitted_by": "alice",
            "submitted_at": "2026-01-01",
            "status": "pending",
        }
        (claims_dir / "CLM-test-birth.json").write_text(json.dumps(claim), encoding="utf-8")

        monkeypatch.setattr(sys, "argv", ["cid_registrar.py"])
        try:
            cid_registrar.main()
            raised = False
        except SystemExit as e:
            raised = True
            assert e.code == 1
        assert raised, "expected cid_registrar.main() to fail closed on an unregistered namespace"
        assert list(individuals.glob("*.md")) == []
