# Claims

This is where sourced genealogical assertions go before they become part
of the confirmed ledger (`Individuals/`, `CID_Index_Master.md`). It's the
mechanism from `docs/MYKV_SERVICE_DESIGN.md` §3-4 made concrete: **anyone
can submit a Claim; a fact only becomes confirmed once independent
submitters agree, per the evidence grade in `Standards/Evidence_Grading.md`.**

## How to submit a Claim

1. Add one file: `Claims/<claim_id>.json`, matching `schemas/claim.schema.json`.
   `claim_id` should be a short, unique, human-readable slug, e.g.
   `CLM-margaret-randolph-birth-01`.
2. If the claim is about someone who already has a Canonical_ID, set
   `subject_cid` to that CID.
3. If the claim is about someone who **doesn't have a CID yet**, set
   `subject_cid` to `PENDING:<key>`, where `<key>` is a short slug you
   choose and reuse across every claim about that same person (e.g.
   `PENDING:margaret-randolph-1850-tn`). Every claim sharing that key is
   treated as being about the same not-yet-registered individual.
4. Always cite a source and grade it honestly per `Standards/Evidence_Grading.md`.
   Set `status` to `"pending"` — the registrar recomputes real status
   itself; it doesn't trust a submitter-set value.
5. Open a PR. CI runs `tools/cid_registrar.py` to validate the file and
   report whether it (together with any existing claims) is enough to
   confirm anything.
6. If your claim's `subject_cid` is a `PENDING:` key and it's now
   mintable (see below), CI will fail with instructions to run
   `python3 tools/cid_registrar.py --write` locally, which mints the CID,
   creates the `Individuals/` stub, and rewrites every claim sharing that
   `PENDING:` key to the new CID. Commit that result in the same PR.

## The confirmation algorithm

For every `(subject_cid, claim_type)` pair, claims are grouped into
**clusters** by exact-match `assertion` content. Two claims with the same
assertion corroborate each other; two claims with a *different* assertion
for the same subject and fact type make that fact **contested** — nothing
is silently picked, per the design doc's Integrity Statement — regardless
of how many submitters are on each side.

Within an uncontested cluster, confirmation depends on the strongest
evidence grade present and how many **distinct submitters** (`submitted_by`)
back it:

| Best evidence grade in the cluster | Distinct submitters required to confirm |
|---|---|
| A (primary record) | 1 |
| B (transcribed primary) | 2 |
| C (secondary/compiled) | 3 |
| D (oral history/unsourced) | Never confirms alone |

This is the total submitter count, not just "corroborations" — a Grade B
claim needs one independent submitter beyond the original (2 total), a
Grade C claim needs two beyond the original (3 total). A single Grade A
source is always enough by itself. This directly extends the existing
repo-wide rule that no lineage link may rest solely on Grade D evidence.

## Minting a new CID

A `PENDING:<key>` subject becomes a real CID only when its `birth` claim
cluster is confirmed (per the table above), uncontested, and carries
enough structured detail to build a Canonical ID:
`assertion.namespace`, `assertion.birth_year`, `assertion.birth_state`,
and `assertion.full_legal_name`. The registrar then:

1. Computes the next free sequence number for that namespace/year/state.
2. Writes a minimal `Individuals/<new-CID>__<Name>.md` stub (Identity
   filled in; Parentage filled in from any confirmed `parent_child`
   claims sharing the same `PENDING:` key; everything else `UNK`, ready
   to be hand-improved or extended by further claims later), then runs
   `tools/validate_ledger.py --write` itself to pick up the new
   registration in `CID_Index_Master.md`.
3. Rewrites `subject_cid`/`object_cid` in every claim file that used the
   old `PENDING:<key>` to the new real CID, so future runs treat it as an
   existing, registered subject.

This deliberately mints only a minimal stub, not a fully-populated record
— folding every confirmed claim type into a complete generated
`Individuals/` file (parentage, marriages, children, migration, sources,
...) is Phase 3's corroboration engine, not this one.
