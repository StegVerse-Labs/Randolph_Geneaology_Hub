#!/usr/bin/env python3
"""Claim intake + CID minting for the Randolph Genealogy Hub.

Implements Phase 2 of docs/MYKV_SERVICE_DESIGN.md: validates Claims/*.json
against the shape in schemas/claim.schema.json, evaluates corroboration
per Claims/README.md's algorithm, and mints a new CID (with a minimal
Individuals/ stub) for any PENDING:<key> subject whose birth claim has
cleared the confirmation bar. It does not rewrite existing Individuals/
records from claims about already-registered subjects, and it does not
fully populate a minted stub from every confirmed claim type about that
subject — both are Phase 3's corroboration engine.

Usage:
  python3 tools/cid_registrar.py          # check only; exit 1 on any problem
  python3 tools/cid_registrar.py --write  # also mint any mintable CIDs
"""
import json
import re
import sys
import pathlib
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import validate_ledger  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLAIMS_DIR = ROOT / "Claims"
INDIVIDUALS = ROOT / "Individuals"

EVIDENCE_RANK = {"A": 0, "B": 1, "C": 2, "D": 3}
CONFIRM_THRESHOLD = {"A": 1, "B": 2, "C": 3, "D": None}
VALID_CLAIM_TYPES = {
    "birth", "parent_child", "death", "marriage", "burial",
    "migration", "military", "occupation",
}
VALID_STATUSES = {"pending", "confirmed", "contested", "rejected"}
CID_RE = re.compile(r"^[A-Z]{2,4}-(?:c\d{3,4}|\d{3,4})-[A-Za-z0-9.]+-[A-Z]{2}$")
PENDING_RE = re.compile(r"^PENDING:[a-z0-9][a-z0-9-]*$")
CLAIM_ID_RE = re.compile(r"^CLM-[a-z0-9-]+$")


def load_claims(claims_dir=CLAIMS_DIR):
    claims = []
    errors = []
    seen_ids = {}
    for f in sorted(claims_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{f.relative_to(ROOT)}: invalid JSON: {exc}")
            continue
        file_errors = validate_claim(data, f)
        if file_errors:
            errors.extend(file_errors)
            continue
        cid_id = data["claim_id"]
        if cid_id in seen_ids:
            errors.append(
                f"{f.relative_to(ROOT)}: duplicate claim_id '{cid_id}' "
                f"(already used by {seen_ids[cid_id].relative_to(ROOT)})"
            )
            continue
        seen_ids[cid_id] = f
        data["_file"] = f
        claims.append(data)
    return claims, errors


def validate_claim(data, f):
    errors = []
    required = ["claim_id", "claim_type", "subject_cid", "assertion", "source", "submitted_by", "submitted_at", "status"]
    for field in required:
        if field not in data:
            errors.append(f"{f.relative_to(ROOT)}: missing required field '{field}'")
    if errors:
        return errors

    if not CLAIM_ID_RE.match(data["claim_id"]):
        errors.append(f"{f.relative_to(ROOT)}: claim_id '{data['claim_id']}' must match ^CLM-[a-z0-9-]+$")
    if data["claim_type"] not in VALID_CLAIM_TYPES:
        errors.append(f"{f.relative_to(ROOT)}: invalid claim_type '{data['claim_type']}'")
    subj = data["subject_cid"]
    if not (CID_RE.match(subj) or PENDING_RE.match(subj)):
        errors.append(f"{f.relative_to(ROOT)}: subject_cid '{subj}' is neither a valid CID nor a PENDING:<key>")
    obj = data.get("object_cid")
    if obj is not None and not (CID_RE.match(obj) or obj == "UNK"):
        errors.append(f"{f.relative_to(ROOT)}: object_cid '{obj}' must be a real CID or 'UNK'")
    source = data.get("source", {})
    if not isinstance(source, dict) or source.get("evidence_level") not in EVIDENCE_RANK:
        errors.append(f"{f.relative_to(ROOT)}: source.evidence_level must be one of A/B/C/D")
    if data["status"] not in VALID_STATUSES:
        errors.append(f"{f.relative_to(ROOT)}: invalid status '{data['status']}'")
    if not isinstance(data.get("assertion"), dict):
        errors.append(f"{f.relative_to(ROOT)}: assertion must be an object")
    return errors


def check_reference_integrity(claims, known_cids):
    errors = []
    for c in claims:
        subj = c["subject_cid"]
        if CID_RE.match(subj) and subj not in known_cids:
            errors.append(f"{c['_file'].relative_to(ROOT)}: subject_cid '{subj}' is not a registered CID")
        obj = c.get("object_cid")
        if obj and CID_RE.match(obj) and obj not in known_cids:
            errors.append(f"{c['_file'].relative_to(ROOT)}: object_cid '{obj}' is not a registered CID")
    return errors


def cluster_key(claim):
    return json.dumps(claim["assertion"], sort_keys=True)


def evaluate(claims):
    """Group by (subject_cid, claim_type); cluster by identical assertion;
    decide confirmed/contested per cluster. Returns dict keyed by
    (subject_cid, claim_type) -> {"clusters": [...], "contested": bool}."""
    groups = defaultdict(list)
    for c in claims:
        groups[(c["subject_cid"], c["claim_type"])].append(c)

    reports = {}
    for key, group_claims in groups.items():
        clusters_map = defaultdict(list)
        for c in group_claims:
            clusters_map[cluster_key(c)].append(c)

        cluster_reports = []
        for cluster_claims in clusters_map.values():
            submitters = {c["submitted_by"] for c in cluster_claims}
            best_level = min(
                (c["source"]["evidence_level"] for c in cluster_claims),
                key=lambda lvl: EVIDENCE_RANK[lvl],
            )
            threshold = CONFIRM_THRESHOLD[best_level]
            confirmed = threshold is not None and len(submitters) >= threshold
            cluster_reports.append({
                "claims": cluster_claims,
                "submitters": submitters,
                "best_level": best_level,
                "confirmed": confirmed,
            })

        reports[key] = {
            "clusters": cluster_reports,
            "contested": len(clusters_map) > 1,
        }
    return reports


def pending_keys(claims):
    keys = set()
    for c in claims:
        if PENDING_RE.match(c["subject_cid"]):
            keys.add(c["subject_cid"])
        obj = c.get("object_cid")
        if obj and PENDING_RE.match(obj):
            keys.add(obj)
    return keys


def next_sequence(known_cids, ns, year, state):
    pattern = re.compile(rf"^{re.escape(ns)}-c?{year}-(\d+)-{re.escape(state)}$")
    seqs = [int(m.group(1)) for cid in known_cids if (m := pattern.match(cid))]
    return max(seqs, default=0) + 1


def mintable_for_pending(pending_key, reports, claims, known_cids):
    """Return (new_cid, birth_claims, parent_claims) if pending_key's birth
    claim is confirmed & uncontested & structurally complete; else None."""
    birth_report = reports.get((pending_key, "birth"))
    if not birth_report or birth_report["contested"]:
        return None
    confirmed = [r for r in birth_report["clusters"] if r["confirmed"]]
    if len(confirmed) != 1:
        return None
    birth_claims = confirmed[0]["claims"]
    assertion = birth_claims[0]["assertion"]
    ns = assertion.get("namespace")
    year = assertion.get("birth_year")
    state = assertion.get("birth_state")
    name = assertion.get("full_legal_name")
    if not (ns and year and state and name):
        return None

    seq = next_sequence(known_cids, ns, year, state)
    new_cid = f"{ns}-{year}-{seq:03d}-{state}"

    parent_report = reports.get((pending_key, "parent_child"), {"clusters": [], "contested": False})
    parent_claims = []
    if not parent_report["contested"]:
        for cluster in parent_report["clusters"]:
            if cluster["confirmed"]:
                parent_claims.append(cluster["claims"][0])

    return new_cid, birth_claims, parent_claims


def write_stub(new_cid, name, birth_claims, parent_claims):
    filename_name = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")
    path = INDIVIDUALS / f"{new_cid}__{filename_name}.md"

    father_cid = "UNK"
    mother_cid = "UNK"
    for c in parent_claims:
        rel = c["assertion"].get("relationship")
        parent = c.get("object_cid", "UNK")
        if rel == "father":
            father_cid = parent
        elif rel == "mother":
            mother_cid = parent

    birth = birth_claims[0]
    source_lines = []
    for c in birth_claims + parent_claims:
        src = c["source"]
        source_lines.append(
            f"Source_ID: {src.get('source_id', 'UNK')}  \n"
            f"Description: {src['description']}  \n"
            f"Evidence_Level: {src['evidence_level']}  "
        )

    content = f"""# Identity

Canonical_ID: {new_cid}
Full_Legal_Name: {name}
Known_As:
Birth: {birth["assertion"].get("birth_date", str(birth["assertion"]["birth_year"]))}, {birth["assertion"].get("birth_place", birth["assertion"]["birth_state"])}
Death: UNK
Burial: UNK
Primary_Locations:
- {birth["assertion"]["birth_state"]}

Notes: Minted by tools/cid_registrar.py from confirmed Claims/ submissions. This is a minimal stub — see Claims/{birth["claim_id"]}.json and related claims for full submission detail.

---

# Parentage

Father_CID: {father_cid}
Mother_CID: {mother_cid}
Evidence_Level: {birth["source"]["evidence_level"]}

---

# Marriages

Spouse_CID: UNK
Marriage_Date: UNK
Marriage_Location: UNK
Source_ID: UNK

---

# Children

Child_CID:
- UNK (Pending discovery)

---

# Migration Timeline

Year: UNK
Location: UNK
Source_ID: UNK

---

# Military Record

Unit:
Rank:
Service_Dates:
Source_ID:

---

# Occupation

UNK

---

# Source Citations

{chr(10).join(source_lines)}

---

# Evidence Confidence Rating

{birth["source"]["evidence_level"]}
"""
    path.write_text(content, encoding="utf-8")
    return path


def rewrite_pending_refs(claims, pending_key, new_cid):
    for c in claims:
        changed = False
        if c["subject_cid"] == pending_key:
            c["subject_cid"] = new_cid
            changed = True
        if c.get("object_cid") == pending_key:
            c["object_cid"] = new_cid
            changed = True
        if changed:
            f = c["_file"]
            out = {k: v for k, v in c.items() if k != "_file"}
            f.write_text(json.dumps(out, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def main():
    write = "--write" in sys.argv
    errors = []

    known_records, ledger_errors = validate_ledger.load_individuals()
    errors.extend(ledger_errors)
    known_cids = set(known_records)

    claims, claim_errors = load_claims()
    errors.extend(claim_errors)
    errors.extend(check_reference_integrity(claims, known_cids))

    if errors:
        print("CID REGISTRAR FAILED")
        for e in errors:
            print("-", e)
        sys.exit(1)

    if not claims:
        print("CID REGISTRAR PASSED (0 claims)")
        return

    minted = []
    already_reported = set()
    remaining_claims = claims
    for _ in range(len(pending_keys(claims)) + 1):
        reports = evaluate(remaining_claims)
        ready = None
        for key in sorted(pending_keys(remaining_claims)):
            if key in already_reported:
                continue
            result = mintable_for_pending(key, reports, remaining_claims, known_cids)
            if result:
                ready = (key, result)
                break
        if not ready:
            break
        key, (new_cid, birth_claims, parent_claims) = ready
        already_reported.add(key)
        if write:
            name = birth_claims[0]["assertion"]["full_legal_name"]
            path = write_stub(new_cid, name, birth_claims, parent_claims)
            rewrite_pending_refs(remaining_claims, key, new_cid)
            print(f"Minted {new_cid} -> {path.relative_to(ROOT)}")
        minted.append((key, new_cid))
        known_cids.add(new_cid)

    if minted and not write:
        print("CID REGISTRAR FAILED")
        for key, new_cid in minted:
            print(
                f"- {key} is confirmed and mintable as {new_cid} but not yet minted — "
                "run `python3 tools/cid_registrar.py --write` and commit the result"
            )
        sys.exit(1)

    if write and minted:
        records, _ = validate_ledger.load_individuals()
        new_text, marker_error = validate_ledger.rewrite_index(records)
        if marker_error:
            print("-", marker_error)
            sys.exit(1)
        validate_ledger.INDEX_FILE.write_text(new_text, encoding="utf-8")
        print(f"Rewrote {validate_ledger.INDEX_FILE.relative_to(ROOT)}")

    print(f"CID REGISTRAR PASSED ({len(claims)} claims, {len(minted)} newly minted)")


if __name__ == "__main__":
    main()
