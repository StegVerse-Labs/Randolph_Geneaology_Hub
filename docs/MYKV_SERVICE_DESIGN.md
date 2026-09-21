# Design: A Shared Genealogy Service, Confirmed by Corroboration, Backed by MyKV

Status: **Draft for review** — no code in this document has been built yet.
This is Phase 0 of turning the Randolph Genealogy Hub from a single family's
static ledger into a service anyone can use to build sourced, CID-anchored
genealogy records, where individuals confirm each other's facts through
independent corroboration, and where private research can live in a
contributor's own [MyKV](https://github.com/StegVerse-Labs/continuity-vault-kit)
(KnowledgeVault) instance instead of only in a public GitHub PR.

---

## 1. What "available as a service to anyone" means here

Today this repo is one family's evidence ledger, edited by hand-authored
Markdown PRs. The target end state:

- **Anyone** can register a namespace (not just `RND`/`LND`) and start
  building their own family's Individuals/Sources/Research, using the same
  CID format, evidence grading, and privacy rules already defined in
  `Standards/`.
- **Individual records are built from Claims, not hand-edited files.** A
  Claim is one atomic, sourced assertion ("X is the child of Y," "X was born
  on date D in place P"). Confirmed Individual records are *generated* from
  Claims that clear the corroboration bar — no one hand-writes a CID's
  `Father_CID` line and hopes it's right (this is exactly how the current
  ledger drifted — see §6).
- **Confirmation comes from independent people, not a single curator.**
  Per the trust model chosen for this project: anyone can submit a Claim;
  it becomes *confirmed* when independent submitters corroborate it (§4),
  not when a maintainer approves it.
- **Private research can stay private until a contributor chooses to share
  it**, using MyKV as the personal vault it's designed to be, and only ever
  crossing into the public ledger as a small, explicit, non-secret
  submission — never as a dump of vault contents.

This document does not change any files yet. It defines the target
architecture and a phased migration so the next PRs have a spec to build
against.

---

## 2. Fixed points this design must respect

These already exist in this repo and are **not** being redesigned — the
service is built on top of them:

| Existing rule | Source |
|---|---|
| `<NS>-<BirthYear>-<Sequence>-<BirthState>` CID format, never reused/altered | `README.md`, `CID_Index_Master.md` |
| A–D evidence grading; no lineage link may rest on Grade D alone | `Standards/Evidence_Grading.md` |
| Required record structure (Identity/Parentage/Marriages/Children/Migration/Military/Occupation/Sources) | `Standards/Schema_v1.md` |
| No exact birthdates/addresses/contact info for living people; living entries default to Grade C until obituary/military/newspaper confirmation | `Standards/Living_Persons_Privacy_Protocol.md` |
| Consent-based, revocable, user-controlled identity data; no centralized PII storage | `ETHICAL_FRAMEWORK.md`, `LICENSE_SOVEREIGN_USE.md` |

And from MyKV's own README, these are hard constraints on *any* integration,
not suggestions:

> `storage location != authority` · `copy != original` ·
> `historical evidence != current doctrine` · `import receipt != truth
> certification`

Concretely: this service must never treat "it came from someone's MyKV" as
proof of anything, must never require a hosted account or MyKV to *read*
public confirmed records (MyKV's own baseline is file-only, no account, no
SDK — this service matches that), and must never receive raw vault content
or credentials — only bounded, explicit submissions (§5).

---

## 3. Data model: Claims vs. Confirmed Records

### 3.1 Claim (new)

A Claim is the unit anyone submits. One Claim = one assertion.

```yaml
claim_id: CLM-<uuid>
claim_type: parent_child | birth | death | marriage | burial | migration | military | occupation
subject_cid: RND-1796-001-TN        # or UNK-PENDING if the subject has no CID yet
object_cid: RND-c1760-001-VA        # e.g. the parent, for parent_child claims
assertion:
  # shape depends on claim_type, e.g. for birth:
  date: 1796
  place: Tennessee, USA
source:
  evidence_level: C                 # A–D, per Standards/Evidence_Grading.md
  description: "Find A Grave memorial transcription"
  source_id: SRC-FindAGrave-42802428   # must resolve in Source_Registry/
submitted_by: <submitter_identity>   # §4.1
submitted_at: 2026-09-21
corroborations: []                   # filled in as others submit matching claims
status: pending | confirmed | contested | rejected
```

Claims are additive and append-only. Nobody edits someone else's Claim;
disagreement is expressed by submitting a *contradicting* Claim, which the
corroboration engine surfaces as `contested` (§4.3) rather than a silent
overwrite — this preserves the "reversibility" and "transparent about
limitations" commitments already in `README.md` and `docs/ethics.md`.

### 3.2 Confirmed Record (evolution of today's `Individuals/*.md`)

Once a subject has at least one `confirmed` Claim of each required type per
`Schema_v1.md`, the service *generates* the Individual file from the
confirmed Claims. Hand-editing an `Individuals/*.md` file directly is
deprecated once this ships — it's the exact mechanism that let
`RND-1796-001-TN__Ruben_Randolph.md` reference eight child CIDs that were
never registered, and let `RND-1900-UNK-OR__Robert_Randolph.md` cite a
`Mother_CID` that resolves to nothing (see the review findings this design
follows from). Generating the file from confirmed Claims makes both classes
of error structurally impossible: a CID can't be referenced until the
Claim that mints it has cleared confirmation and the CID Registrar (§6) has
issued it.

---

## 4. Peer-corroboration confirmation model

### 4.1 Independence

A corroboration only counts if it comes from a **submitter identity
distinct from the original submitter**, per the chosen trust model (open
submission, no curator gate). Two submissions from the same GitHub account,
or the same MyKV `kv_set_id` (an owner's *own* multiple KV instances, per
MyKV's KV #1/KV #2/KV #n model — same owner, not independent), do not
corroborate each other. This needs one piece of new infrastructure: a
lightweight submitter-identity record (GitHub account today; can extend to
a MyKV instance identity later) so "independent" is checkable, not
self-reported.

### 4.2 Promotion table

| Claim evidence grade | Confirmation requirement |
|---|---|
| A (primary document) | 1 submission is enough — the source itself is the corroboration |
| B (transcribed primary) | 1 independent corroborating submission *or* 1 A-grade source |
| C (secondary/compiled) | 2 independent corroborating submissions, or 1 upgrade to B/A-grade source |
| D (oral history/unsourced) | Never auto-confirms — matches the existing repo-wide rule that no lineage link may rest solely on Grade D. D-grade claims can only be *linked as context* on a confirmed record, never form the link itself |

This is a direct extension of `Standards/Evidence_Grading.md`'s existing
"No lineage link may rest solely on Grade D evidence" — corroboration count
is the new mechanism, evidence grade is still the ceiling.

### 4.3 Contradictions

If two confirmed (or corroborating) Claims conflict on the same
`subject_cid` + `claim_type` (e.g., two different birth dates), the record
enters `contested` status: the Confirmed Record still generates, but
carries both claims and their evidence grades visibly, exactly as
`README.md`'s Integrity Statement already promises ("separate hypothesis
from proof"). Nothing is silently dropped.

### 4.4 Living persons

Corroboration count never overrides `Living_Persons_Privacy_Protocol.md`.
A living person's record stays capped at Grade C and stays free of exact
birthdates/addresses regardless of how many people corroborate a claim,
unless the existing obituary/military-record/newspaper exception applies.

---

## 5. MyKV integration

### 5.1 Why MyKV fits here

MyKV's own README already anticipates this: `specs/kv-personal-services-registry.v1.json`
lists an `OPTIONAL_GENEALOGY_PROVIDER` dependency for relationship-editor /
share-UI personal services, and the historical-corpus-import path
(`runtime/historical_corpus_import.py`, `KV_HISTORICAL_CORPUS_IMPORT_MIRROR_HANDOFF.md`)
already describes owner-authorized historical artifacts producing a
**Master Records custody-request candidate** — a request that only an
independent destination can validate and accept. A genealogy hub confirming
records via independent corroboration is a natural fit for that kind of
destination, scoped specifically to genealogical claims rather than
arbitrary historical corpora.

### 5.2 v0 — file-only, no hosted anything (build this first)

Matches MyKV's own stated baseline ("file-based. No account, hosted
service, SDK, or AI provider is required"):

1. A contributor keeps private research under their own KV's `_Entities/<person>/`
   and `02_Research/` — this never leaves their machine/storage.
2. When they're ready to share one fact, they run a small export script
   (to be built in this repo, e.g. `tools/export_kv_claim.py`) that reads
   *only* the specific entity file they point it at and emits a single
   Claim object (§3.1) as JSON. No other vault content is read. This
   mirrors the `private_content_included=false` /
   `credential_material_included=false` contract MyKV's own
   `runtime/kv_my_kv_projection.py` uses for anything crossing its boundary.
3. That Claim JSON is what gets submitted — today as a PR adding one file
   under a new `Claims/` directory, later via an API (§7, Phase 3). The hub
   never touches the contributor's KV directly.
4. Nothing about this requires MyKV — a contributor with no KV can write
   the same Claim JSON by hand or via a plain form. MyKV is a convenience
   for organizing private research before sharing, not a dependency of the
   public service.

### 5.3 Future — governed live sync (explicitly out of reach of this repo alone)

A live, automatic sync between a contributor's KV and this service would
need to go through MyKV's actual admission machinery — Interlock/InTr
admission, receipts, SKAP-scoped credentials where relevant — the same way
every other "future capability" in `continuity-vault-kit` is gated. This
repo cannot build that alone: it depends on StegVerse-Labs' shared
Interlock/InTr runtime, which lives outside this repository. What this repo
*can* do now is make sure its own side of that boundary is ready:

- Accept a Claim submission that carries an admitted InTr receipt
  reference, if present, and treat that no differently from a plain PR
  submission for confirmation purposes — an import receipt is still not a
  truth certification (per MyKV's own rule), so corroboration (§4) still
  governs whether it confirms.
- Never accept raw KV bytes or credentials over that channel, matching
  every other MyKV integration boundary.
- Independently validate before minting anything — never treat a custody
  request as already-accepted custody, per the custody-request schema in
  `continuity-vault-kit`'s `schemas/kv-historical-custody-request.schema.json`.

---

## 6. CID lifecycle fixes (prerequisite, not optional)

The current ledger has exactly the failure modes this design is meant to
prevent — found in review before this doc was written:

- `CID_Index_Master.md` is missing 6 issued CIDs that have real
  `Individuals/*.md` files (all 5 `LND-*` and `RND-1900-UNK-OR`).
- `RND-1796-001-TN__Ruben_Randolph.md` lists 8 children CIDs with no
  matching file and no index entry.
- `RND-1900-UNK-OR__Robert_Randolph.md` cites `Mother_CID: LND-1885-001-TX`,
  which resolves to nothing — the real record is `LND-1885-001-MN`, and
  `LND-1885-001-TX` only exists as an explicitly *unconfirmed* research
  label in `Research/`.

None of the Claims/corroboration machinery above matters if a service can
still generate or accept a record that points at a CID nobody issued. So
**Phase 1 is a validator, not the corroboration engine**: a script that
walks `Individuals/`, `CID_Index_Master.md`, and every `*_CID:` reference,
and fails closed (matching MyKV's own vocabulary for this exact situation)
if any reference doesn't resolve. `CID_Index_Master.md` stops being
hand-edited and becomes generated output once the CID Registrar (§3.2,
§6) exists — that alone prevents the drift that produced the three bugs
above.

---

## 7. Phased migration

| Phase | Deliverable | Depends on external infra? |
|---|---|---|
| 0 | Fix the 3 CID bugs above, dedupe `FAMILY_TREE.md` and the duplicate Research files, fix dead links (`docs/start.md`, `/stories`, `/branches`, `Standards/Genealogy_Naming_Contract_v1.md`) | No |
| 1 | CID/reference validator wired into `.github/workflows/test-readiness.yml`; `CID_Index_Master.md` becomes generated | No |
| 2 | Claim schema + `Claims/` directory + CID Registrar (mints a CID only from a confirmed Claim) | No |
| 3 | Corroboration engine (§4) generates Confirmed Records from Claims; `tools/export_kv_claim.py` for MyKV v0 (§5.2) | No |
| 4 | Multi-family namespaces (already gestured at in `README.md`'s "Multi-family namespace expansion" and `docs/assets/Start_Your_Own_Family_Hub.pdf`) — anyone forks or registers a new `<NS>` | No |
| 5 | API layer + hosted read service, so records are browsable without cloning the repo | No (but needs a hosting decision) |
| 6 | Governed live MyKV sync via Interlock/InTr (§5.3) | **Yes** — StegVerse-Labs shared runtime |

Phases 0–5 are buildable entirely inside this repo and don't require
anything from `continuity-vault-kit` beyond the export script matching its
projection conventions. Phase 6 is explicitly a future activation lane, the
same way MyKV treats its own unbuilt capabilities.

---

## 8. Open questions

1. **Submitter identity for independence checks (§4.1):** GitHub account
   is enough for v0. Do we want an explicit link to a MyKV instance ID
   later, so corroboration can distinguish "two different people" from
   "one person's two KV instances" more rigorously?
2. **Hosting for Phase 5's read API/site** — GitHub Pages (already partly
   set up via `docs/index.md`'s Jekyll front matter) is enough for a
   read-only browsable ledger; anything with a write API needs a real
   hosting decision.
3. **Multi-family namespace governance (Phase 4):** does a new family's
   `<NS>` live in this same repo, or does each family fork and this repo
   becomes the schema/spec reference? `README.md` already says "Enable
   duplication across other families," which points at fork-based, but
   that's worth confirming before Phase 4.

Feedback on any of the above changes the phase order; nothing after Phase 0
should start until this doc is agreed on.
