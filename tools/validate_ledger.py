#!/usr/bin/env python3
"""Validate and (optionally) regenerate the Randolph Genealogy Hub CID ledger.

Checks:
  1. Every Individuals/*.md file has a Canonical_ID matching its filename
     prefix (the part before "__").
  2. No Canonical_ID is issued by more than one file.
  3. Every Father_CID / Mother_CID / Spouse_CID / Children-list CID
     reference (other than UNK) resolves to a Canonical_ID that actually
     has an Individuals/ file.
  4. CID_Index_Master.md's generated block matches what Individuals/*.md
     actually contains.
  5. Every Canonical_ID's namespace is registered in NAMESPACES.md — see
     that file for what a namespace is and how a forked hub registers
     its own.

Usage:
  python3 tools/validate_ledger.py          # check only; exit 1 on any problem
  python3 tools/validate_ledger.py --write  # also regenerate CID_Index_Master.md
"""
import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
INDIVIDUALS = ROOT / "Individuals"
INDEX_FILE = ROOT / "CID_Index_Master.md"
NAMESPACES_FILE = ROOT / "NAMESPACES.md"

BEGIN_MARKER = "<!-- BEGIN GENERATED: tools/validate_ledger.py -->"
END_MARKER = "<!-- END GENERATED -->"

CID_STRICT = re.compile(r"^[A-Z]{2,4}-(?:c\d{3,4}|\d{3,4})-[A-Za-z0-9.]+-[A-Z]{2}$")
NAMESPACE_ROW_RE = re.compile(r"^\|\s*`([A-Z]{2,4})`\s*\|", re.MULTILINE)
FIELD_RE = re.compile(r"^(?:Father_CID|Mother_CID|Spouse_CID):\s*(\S+)", re.MULTILINE)
BULLET_RE = re.compile(r"^-\s+(\S+)", re.MULTILINE)
CANONICAL_RE = re.compile(r"^Canonical_ID:\s*(\S+)", re.MULTILINE)
NAME_RE = re.compile(r"^Full_Legal_Name:\s*(.+)$", re.MULTILINE)


def strip_trailing(token):
    return token.rstrip("\\").rstrip(",").strip()


def sort_key(cid):
    m = re.match(r"^([A-Z]{2,4})-c?(\d{3,4})-([A-Za-z0-9.]+)-([A-Z]{2})$", cid)
    if not m:
        return (cid,)
    ns, year, seq, state = m.groups()
    return (ns, int(year), seq, state)


def load_individuals():
    records = {}
    errors = []
    for f in sorted(INDIVIDUALS.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        m = CANONICAL_RE.search(text)
        if not m:
            errors.append(f"{f.relative_to(ROOT)}: missing Canonical_ID field")
            continue
        cid = strip_trailing(m.group(1))
        if not CID_STRICT.match(cid):
            errors.append(
                f"{f.relative_to(ROOT)}: Canonical_ID '{cid}' doesn't match "
                "the <NS>-<BirthYear>-<Sequence>-<State> format"
            )
        expected_prefix = f.name.split("__")[0]
        if expected_prefix != cid:
            errors.append(
                f"{f.relative_to(ROOT)}: filename prefix '{expected_prefix}' "
                f"doesn't match Canonical_ID '{cid}'"
            )
        if cid in records:
            errors.append(
                f"{f.relative_to(ROOT)}: Canonical_ID '{cid}' is already issued "
                f"by {records[cid]['file'].relative_to(ROOT)}"
            )
            continue

        name_m = NAME_RE.search(text)
        name = strip_trailing(name_m.group(1)) if name_m else cid

        refs = set()
        for value in FIELD_RE.findall(text):
            value = strip_trailing(value)
            if value != "UNK":
                refs.add(value)
        for value in BULLET_RE.findall(text):
            value = strip_trailing(value)
            if value != "UNK" and CID_STRICT.match(value):
                refs.add(value)
        refs.discard(cid)

        records[cid] = {"name": name, "file": f, "refs": refs}
    return records, errors


def check_references(records):
    errors = []
    known = set(records)
    for cid, rec in records.items():
        for ref in sorted(rec["refs"]):
            if ref not in known:
                errors.append(
                    f"{rec['file'].relative_to(ROOT)}: references unregistered CID '{ref}'"
                )
    return errors


def load_registered_namespaces():
    if not NAMESPACES_FILE.exists():
        return None, [f"{NAMESPACES_FILE.relative_to(ROOT)}: file is missing"]
    text = NAMESPACES_FILE.read_text(encoding="utf-8")
    namespaces = set(NAMESPACE_ROW_RE.findall(text))
    if not namespaces:
        return None, [f"{NAMESPACES_FILE.relative_to(ROOT)}: no namespace rows found (expected a `| `XYZ` | ... |` table row)"]
    return namespaces, []


def check_namespaces(records, registered):
    errors = []
    for cid, rec in records.items():
        m = re.match(r"^([A-Z]{2,4})-", cid)
        ns = m.group(1) if m else None
        if ns not in registered:
            errors.append(
                f"{rec['file'].relative_to(ROOT)}: Canonical_ID '{cid}' uses namespace "
                f"'{ns}', which isn't registered in {NAMESPACES_FILE.relative_to(ROOT)}"
            )
    return errors


def generated_block(records):
    lines = [f"{cid} – {records[cid]['name']}" for cid in sorted(records, key=sort_key)]
    return "\n".join(lines)


def rewrite_index(records):
    text = INDEX_FILE.read_text(encoding="utf-8")
    if BEGIN_MARKER not in text or END_MARKER not in text:
        return None, f"{INDEX_FILE.relative_to(ROOT)}: missing generated-block markers"
    before, rest = text.split(BEGIN_MARKER, 1)
    _, after = rest.split(END_MARKER, 1)
    new_text = before + BEGIN_MARKER + "\n" + generated_block(records) + "\n" + END_MARKER + after
    return new_text, None


def main():
    write = "--write" in sys.argv
    records, errors = load_individuals()
    errors.extend(check_references(records))

    registered_namespaces, namespace_errors = load_registered_namespaces()
    errors.extend(namespace_errors)
    if registered_namespaces is not None:
        errors.extend(check_namespaces(records, registered_namespaces))

    new_text, marker_error = rewrite_index(records)
    if marker_error:
        errors.append(marker_error)
    else:
        current_text = INDEX_FILE.read_text(encoding="utf-8")
        if new_text != current_text:
            if write:
                INDEX_FILE.write_text(new_text, encoding="utf-8")
                print(f"Rewrote {INDEX_FILE.relative_to(ROOT)}")
            else:
                errors.append(
                    f"{INDEX_FILE.relative_to(ROOT)} is out of date with Individuals/*.md "
                    "— run `python3 tools/validate_ledger.py --write` and commit the result"
                )

    if errors:
        print("LEDGER VALIDATION FAILED")
        for e in errors:
            print("-", e)
        sys.exit(1)

    print(f"LEDGER VALIDATION PASSED ({len(records)} individuals, all references resolve)")


if __name__ == "__main__":
    main()
