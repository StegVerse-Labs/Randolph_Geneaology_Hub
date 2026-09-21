#!/usr/bin/env python3
"""Export genealogy Claims embedded in a single local file into Claims/*.json.

This is the v0, file-only MyKV path from docs/MYKV_SERVICE_DESIGN.md §5.2.
MyKV (https://github.com/StegVerse-Labs/continuity-vault-kit) has no
genealogy-specific entity format today — its People template
(vault_template/KnowledgeVault/_Entities/People/_Template.md) is free-form
personal-relationship notes (Relationship, Basic Info, Memory Highlights,
...), not sourced/graded genealogical assertions, and its own README lists
a genealogy provider only as an unbuilt "OPTIONAL_GENEALOGY_PROVIDER"
dependency. So rather than guessing at how to parse an unstructured
"Birthday:" line, this tool defines one small, explicit convention layered
on top of any plain Markdown file: a fenced ```genealogy-claim code block
containing a JSON object shaped like schemas/claim.schema.json (minus the
bookkeeping fields this tool fills in for you). A contributor adds one such
block per fact they're ready to share — anywhere in their own vault file,
e.g. under a People entity's "Notes Over Time" section — and this script
reads *only* the file they point it at, extracts those blocks, and writes
each as its own Claims/<id>.json. Nothing else in the file, and nothing
else in the vault, is read or touched — the same
private_content_included=false boundary MyKV's own bounded projections use.

Example embedded block:

    ## Genealogy Claim: birth

    ```genealogy-claim
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
    ```

claim_id, submitted_by, submitted_at, and status are filled in by this
tool if omitted — claim_id is derived from subject_cid + claim_type + a
counter unique within Claims/; submitted_by comes from --submitted-by;
submitted_at is today; status is always "pending" (the registrar
recomputes real status itself; see Claims/README.md).

Usage:
  python3 tools/export_kv_claim.py --file path/to/entity.md --submitted-by <identity>
  python3 tools/export_kv_claim.py --file path/to/entity.md --submitted-by <identity> --dry-run
"""
import argparse
import datetime
import json
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import cid_registrar  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLAIMS_DIR = ROOT / "Claims"

BLOCK_RE = re.compile(r"```genealogy-claim\s*\n(.*?)```", re.DOTALL)


def extract_blocks(text):
    return [m.group(1).strip() for m in BLOCK_RE.finditer(text)]


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "claim"


def next_claim_id(base_slug, claims_dir, used_this_run):
    n = 1
    while True:
        candidate = f"CLM-{base_slug}-{n:02d}"
        if candidate not in used_this_run and not (claims_dir / f"{candidate}.json").exists():
            return candidate
        n += 1


def fill_defaults(raw, submitted_by, claims_dir, used_this_run):
    claim = dict(raw)
    claim.setdefault("submitted_by", submitted_by)
    claim.setdefault("submitted_at", datetime.date.today().isoformat())
    claim.setdefault("status", "pending")
    if "claim_id" not in claim:
        subject = claim.get("subject_cid", "unknown")
        subject_part = subject.split(":", 1)[-1] if subject.startswith("PENDING:") else slugify(subject)
        base_slug = slugify(f"{subject_part}-{claim.get('claim_type', 'claim')}")
        claim["claim_id"] = next_claim_id(base_slug, claims_dir, used_this_run)
    return claim


def export(file_path, submitted_by, claims_dir=CLAIMS_DIR, dry_run=False):
    """Returns (results, had_errors). results is a list of
    (claim_id, path, would_write) for every block that parsed and
    validated, whether or not it needed writing. had_errors is True if any
    block was invalid JSON, failed schema validation, or collided with a
    differently-content claim already on disk — independent of --dry-run,
    since a dry run should still report a bad claim as a failure."""
    text = file_path.read_text(encoding="utf-8")
    blocks = extract_blocks(text)
    if not blocks:
        print(f"No ```genealogy-claim blocks found in {file_path}")
        return [], False

    results = []
    had_errors = False
    used_this_run = set()
    for i, block in enumerate(blocks, start=1):
        try:
            raw = json.loads(block)
        except Exception as exc:
            print(f"- block {i}: invalid JSON: {exc}")
            had_errors = True
            continue
        claim = fill_defaults(raw, submitted_by, claims_dir, used_this_run)
        used_this_run.add(claim["claim_id"])

        out_path = claims_dir / f"{claim['claim_id']}.json"
        errors = cid_registrar.validate_claim(claim, out_path)
        if errors:
            print(f"- block {i} ({claim['claim_id']}): invalid claim:")
            for e in errors:
                print(f"    {e}")
            had_errors = True
            continue

        if out_path.exists():
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            if existing == claim:
                print(f"- {claim['claim_id']}: unchanged, already exported")
                results.append((claim["claim_id"], out_path, False))
                continue
            print(f"- {claim['claim_id']}: already exists with different content — skipped; "
                  "give this claim a distinct claim_id and re-run")
            had_errors = True
            continue

        if dry_run:
            print(f"- would write {out_path.relative_to(ROOT)} ({claim['claim_type']} claim about {claim['subject_cid']})")
        else:
            out_path.write_text(json.dumps(claim, indent=2) + "\n", encoding="utf-8")
            print(f"- wrote {out_path.relative_to(ROOT)} ({claim['claim_type']} claim about {claim['subject_cid']})")
        results.append((claim["claim_id"], out_path, True))

    return results, had_errors


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", required=True, type=pathlib.Path, help="the single local file to read")
    parser.add_argument("--submitted-by", required=True, help="submitter identity, e.g. a GitHub username")
    parser.add_argument("--dry-run", action="store_true", help="show what would be written without writing")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"No such file: {args.file}")
        sys.exit(1)

    _, had_errors = export(args.file, args.submitted_by, dry_run=args.dry_run)
    if had_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
