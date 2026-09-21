import json
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import cid_registrar  # noqa: E402
import export_kv_claim  # noqa: E402


VALID_BLOCK = """```genealogy-claim
{
  "claim_type": "birth",
  "subject_cid": "PENDING:margaret-randolph-1850-tn",
  "assertion": {
    "full_legal_name": "Margaret Randolph",
    "namespace": "RND",
    "birth_year": 1850,
    "birth_state": "TN"
  },
  "source": {
    "evidence_level": "C",
    "description": "Find A Grave memorial transcription",
    "source_id": "SRC-FindAGrave-42802428"
  }
}
```"""


def make_entity_file(tmp_path, body):
    entity = tmp_path / "entity.md"
    entity.write_text(f"# Margaret Randolph\n\n**Relationship:** great-great-aunt\n\n{body}\n", encoding="utf-8")
    return entity


def test_extracts_and_fills_defaults(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = pathlib.Path(tmp)
        claims_dir = tmp_root / "Claims"
        claims_dir.mkdir()
        monkeypatch.setattr(export_kv_claim, "ROOT", tmp_root)
        monkeypatch.setattr(cid_registrar, "ROOT", tmp_root)

        entity = make_entity_file(tmp_root, VALID_BLOCK)
        results, had_errors = export_kv_claim.export(entity, "alice", claims_dir=claims_dir)

        assert had_errors is False
        assert len(results) == 1
        claim_id, path, wrote = results[0]
        assert wrote is True
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["submitted_by"] == "alice"
        assert data["status"] == "pending"
        assert data["claim_id"] == claim_id
        assert "submitted_at" in data
        assert data["assertion"]["full_legal_name"] == "Margaret Randolph"


def test_only_reads_the_one_file_given(monkeypatch):
    """The export must not touch anything besides Claims/ and the exact
    file path it's given — no scanning of sibling files or directories."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = pathlib.Path(tmp)
        claims_dir = tmp_root / "Claims"
        claims_dir.mkdir()
        monkeypatch.setattr(export_kv_claim, "ROOT", tmp_root)
        monkeypatch.setattr(cid_registrar, "ROOT", tmp_root)

        other = tmp_root / "other_private_notes.md"
        other.write_text(VALID_BLOCK, encoding="utf-8")
        original_other = other.read_text()

        entity = make_entity_file(tmp_root, VALID_BLOCK)
        export_kv_claim.export(entity, "alice", claims_dir=claims_dir)

        assert other.read_text() == original_other
        assert len(list(claims_dir.glob("*.json"))) == 1


def test_rerun_with_unchanged_content_is_a_noop(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = pathlib.Path(tmp)
        claims_dir = tmp_root / "Claims"
        claims_dir.mkdir()
        monkeypatch.setattr(export_kv_claim, "ROOT", tmp_root)
        monkeypatch.setattr(cid_registrar, "ROOT", tmp_root)

        block_with_id = VALID_BLOCK.replace(
            '"claim_type": "birth",',
            '"claim_id": "CLM-margaret-birth-01",\n  "claim_type": "birth",',
        )
        entity = make_entity_file(tmp_root, block_with_id)

        results1, errors1 = export_kv_claim.export(entity, "alice", claims_dir=claims_dir)
        assert errors1 is False
        assert results1[0][2] is True  # wrote

        results2, errors2 = export_kv_claim.export(entity, "alice", claims_dir=claims_dir)
        assert errors2 is False
        assert results2[0][2] is False  # unchanged, not rewritten
        assert len(list(claims_dir.glob("*.json"))) == 1


def test_invalid_claim_is_reported_and_not_written(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = pathlib.Path(tmp)
        claims_dir = tmp_root / "Claims"
        claims_dir.mkdir()
        monkeypatch.setattr(export_kv_claim, "ROOT", tmp_root)
        monkeypatch.setattr(cid_registrar, "ROOT", tmp_root)

        bad_block = """```genealogy-claim
{
  "claim_type": "birth",
  "subject_cid": "PENDING:margaret-randolph-1850-tn",
  "assertion": {"full_legal_name": "Margaret Randolph"},
  "source": {"description": "no evidence_level here"}
}
```"""
        entity = make_entity_file(tmp_root, bad_block)
        results, had_errors = export_kv_claim.export(entity, "alice", claims_dir=claims_dir)

        assert had_errors is True
        assert results == []
        assert list(claims_dir.glob("*.json")) == []


def test_dry_run_writes_nothing_but_still_reports_errors(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = pathlib.Path(tmp)
        claims_dir = tmp_root / "Claims"
        claims_dir.mkdir()
        monkeypatch.setattr(export_kv_claim, "ROOT", tmp_root)
        monkeypatch.setattr(cid_registrar, "ROOT", tmp_root)

        entity = make_entity_file(tmp_root, VALID_BLOCK)
        results, had_errors = export_kv_claim.export(entity, "alice", claims_dir=claims_dir, dry_run=True)

        assert had_errors is False
        assert results[0][2] is True  # "would write"
        assert list(claims_dir.glob("*.json")) == []  # nothing actually written

        bad_block = VALID_BLOCK.replace('"evidence_level": "C",', "")
        entity2 = make_entity_file(tmp_root, bad_block)
        _, had_errors2 = export_kv_claim.export(entity2, "alice", claims_dir=claims_dir, dry_run=True)
        assert had_errors2 is True


def test_multiple_blocks_get_distinct_auto_ids(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = pathlib.Path(tmp)
        claims_dir = tmp_root / "Claims"
        claims_dir.mkdir()
        monkeypatch.setattr(export_kv_claim, "ROOT", tmp_root)
        monkeypatch.setattr(cid_registrar, "ROOT", tmp_root)

        entity = make_entity_file(tmp_root, VALID_BLOCK + "\n\n" + VALID_BLOCK)
        results, had_errors = export_kv_claim.export(entity, "alice", claims_dir=claims_dir)

        assert had_errors is False
        assert len(results) == 2
        assert results[0][0] != results[1][0]
