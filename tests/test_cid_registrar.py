import json
import sys
import pathlib
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import cid_registrar  # noqa: E402
import validate_ledger  # noqa: E402


def make_claim(**kwargs):
    base = {
        "claim_id": "CLM-test",
        "claim_type": "birth",
        "subject_cid": "PENDING:test-person",
        "assertion": {},
        "source": {"evidence_level": "C", "description": "test source"},
        "submitted_by": "alice",
        "submitted_at": "2026-01-01",
        "status": "pending",
    }
    base.update(kwargs)
    base["_file"] = pathlib.Path("Claims/CLM-test.json")
    return base


def test_grade_a_confirms_alone():
    claims = [make_claim(source={"evidence_level": "A", "description": "birth cert"})]
    reports = cid_registrar.evaluate(claims)
    report = reports[("PENDING:test-person", "birth")]
    assert report["clusters"][0]["confirmed"] is True
    assert report["contested"] is False


def test_grade_c_needs_three_distinct_submitters():
    shared_assertion = {"full_legal_name": "Test Person", "namespace": "RND", "birth_year": 1900, "birth_state": "TN"}
    claims = [
        make_claim(claim_id="CLM-1", submitted_by="alice", assertion=shared_assertion),
        make_claim(claim_id="CLM-2", submitted_by="bob", assertion=shared_assertion),
    ]
    reports = cid_registrar.evaluate(claims)
    report = reports[("PENDING:test-person", "birth")]
    assert report["clusters"][0]["confirmed"] is False  # only 2 of 3 needed

    claims.append(make_claim(claim_id="CLM-3", submitted_by="carol", assertion=shared_assertion))
    reports = cid_registrar.evaluate(claims)
    report = reports[("PENDING:test-person", "birth")]
    assert report["clusters"][0]["confirmed"] is True


def test_same_submitter_twice_does_not_corroborate():
    shared_assertion = {"full_legal_name": "Test Person", "namespace": "RND", "birth_year": 1900, "birth_state": "TN"}
    claims = [
        make_claim(claim_id="CLM-1", submitted_by="alice", assertion=shared_assertion, source={"evidence_level": "B", "description": "x"}),
        make_claim(claim_id="CLM-2", submitted_by="alice", assertion=shared_assertion, source={"evidence_level": "B", "description": "y"}),
    ]
    reports = cid_registrar.evaluate(claims)
    report = reports[("PENDING:test-person", "birth")]
    assert report["clusters"][0]["confirmed"] is False  # 1 distinct submitter, B needs 2


def test_grade_d_never_confirms():
    claims = [
        make_claim(claim_id=f"CLM-{i}", submitted_by=f"person{i}", source={"evidence_level": "D", "description": "family lore"})
        for i in range(10)
    ]
    reports = cid_registrar.evaluate(claims)
    report = reports[("PENDING:test-person", "birth")]
    assert report["clusters"][0]["confirmed"] is False


def test_conflicting_assertions_are_contested_not_averaged():
    claims = [
        make_claim(claim_id="CLM-1", submitted_by="alice", assertion={"birth_year": 1850}, source={"evidence_level": "A", "description": "x"}),
        make_claim(claim_id="CLM-2", submitted_by="bob", assertion={"birth_year": 1855}, source={"evidence_level": "A", "description": "y"}),
    ]
    reports = cid_registrar.evaluate(claims)
    report = reports[("PENDING:test-person", "birth")]
    assert report["contested"] is True


def test_end_to_end_mint_and_write(monkeypatch):
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

        monkeypatch.setattr(validate_ledger, "ROOT", tmp_root)
        monkeypatch.setattr(validate_ledger, "INDIVIDUALS", individuals)
        monkeypatch.setattr(validate_ledger, "INDEX_FILE", index_file)
        monkeypatch.setattr(cid_registrar, "ROOT", tmp_root)
        monkeypatch.setattr(cid_registrar, "INDIVIDUALS", individuals)
        monkeypatch.setattr(cid_registrar, "CLAIMS_DIR", claims_dir)

        assertion = {"full_legal_name": "Test Person", "namespace": "RND", "birth_year": 1900, "birth_state": "TN"}
        for i, submitter in enumerate(["alice", "bob", "carol"]):
            claim = {
                "claim_id": f"CLM-test-{i}",
                "claim_type": "birth",
                "subject_cid": "PENDING:test-person",
                "assertion": assertion,
                "source": {"evidence_level": "C", "description": "compiled genealogy"},
                "submitted_by": submitter,
                "submitted_at": "2026-01-01",
                "status": "pending",
            }
            (claims_dir / f"CLM-test-{i}.json").write_text(json.dumps(claim), encoding="utf-8")

        claims, errors = cid_registrar.load_claims(claims_dir)
        assert errors == []
        known_records, _ = validate_ledger.load_individuals()
        known_cids = set(known_records)

        reports = cid_registrar.evaluate(claims)
        result = cid_registrar.mintable_for_pending("PENDING:test-person", reports, claims, known_cids)
        assert result is not None
        new_cid, birth_claims, parent_claims = result
        assert new_cid == "RND-1900-001-TN"

        path = cid_registrar.write_stub(new_cid, "Test Person", birth_claims, parent_claims)
        assert path.exists()
        assert "Canonical_ID: RND-1900-001-TN" in path.read_text()

        cid_registrar.rewrite_pending_refs(claims, "PENDING:test-person", new_cid)
        for c in claims:
            assert c["subject_cid"] == new_cid
        for f in claims_dir.glob("*.json"):
            assert json.loads(f.read_text())["subject_cid"] == new_cid

        records, ledger_errors = validate_ledger.load_individuals()
        assert ledger_errors == []
        assert new_cid in records
