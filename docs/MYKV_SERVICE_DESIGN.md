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

**Implemented as of Phase 2** (this sketch was illustrative; the shipped
format is JSON, not YAML, to stay dependency-free — no PyYAML in CI —
and uses `PENDING:<key>` rather than a single `UNK-PENDING` sentinel so
multiple claims can agree on *which* not-yet-registered person they're
about):

```json
{
  "claim_id": "CLM-ruben-randolph-marriage-01",
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
  },
  "submitted_by": "some-github-username",
  "submitted_at": "2026-09-21",
  "status": "pending"
}
```

Full field-by-field documentation lives in `schemas/claim.schema.json`
and `Claims/README.md`, which are the source of truth from here on —
this section stays illustrative.

Claims are additive and append-only. Nobody edits someone else's Claim;
disagreement is expressed by submitting a *contradicting* Claim, which the
corroboration engine surfaces as `contested` (§4.3) rather than a silent
overwrite — this preserves the "reversibility" and "transparent about
limitations" commitments already in `README.md` and `docs/ethics.md`.

### 3.2 Confirmed Record (evolution of today's `Individuals/*.md`)

**Implemented as of Phase 3.** Once a subject has a confirmed `birth`
Claim, `tools/cid_registrar.py` *generates* its Individual file from every
confirmed Claim type about it — Parentage, Marriages, Children (found by
scanning *other* subjects' confirmed `parent_child` claims for this CID as
`object_cid`, not stored on the subject itself), Migration, Military,
Occupation, Death/Burial, and Source Citations — and marks the file with a
`GENERATED BY` comment. It keeps regenerating that same file, in place, as
further claims about the subject confirm later.

This only ever applies to *claim-managed* records: a subject minted this
way, or one already carrying that marker. A subject whose file has no
marker — every individual already in this ledger before the Claims
pipeline existed — is never touched, however many claims reference its
CID; `docs/MYKV_SERVICE_DESIGN.md`'s own Phase 0/1/2 history is exactly
why: those 20 records were hand-authored before any of this existed, and
silently regenerating them from a currently-empty `Claims/` directory
would delete real content, not fix it. Hand-editing is deprecated for
*new* individuals from here on — it's the exact mechanism that let
`RND-1796-001-TN__Ruben_Randolph.md` reference eight child CIDs that were
never registered, and let `RND-1900-UNK-OR__Robert_Randolph.md` cite a
`Mother_CID` that resolves to nothing (see the review findings this design
follows from) — but the existing 20 stay hand-edited until someone
deliberately backfills Claims for them and asks the registrar to take over.

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

Confirmation is decided per cluster of claims that share the same
`subject_cid` + `claim_type` + *identical* `assertion` content (a
differing assertion is a contradiction, not a weaker corroboration — see
§4.3). Within a cluster, the requirement is the **total number of
distinct submitters**, sized to the strongest evidence grade present:

| Best evidence grade in the cluster | Distinct submitters required |
|---|---|
| A (primary document) | 1 — the source itself is the corroboration |
| B (transcribed primary) | 2 (the original submission plus 1 independent corroboration) |
| C (secondary/compiled) | 3 (the original submission plus 2 independent corroborations) |
| D (oral history/unsourced) | Never auto-confirms — matches the existing repo-wide rule that no lineage link may rest solely on Grade D. D-grade claims can only be *linked as context* on a confirmed record, never form the link itself |

This is a direct extension of `Standards/Evidence_Grading.md`'s existing
"No lineage link may rest solely on Grade D evidence" — corroboration count
is the new mechanism, evidence grade is still the ceiling. Implemented in
`tools/cid_registrar.py`'s `evaluate()`; see `Claims/README.md` for the
worked-through algorithm description.

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

"MyKV" is actually two repositories, and this design should keep that split
straight:

- **[`StegVerse-Labs/continuity-vault-kit`](https://github.com/StegVerse-Labs/continuity-vault-kit)**
  defines the KV *content model*: the file-based vault structure, the
  relationship/instance model (KV #1/KV #2/KV #n), the bounded-projection
  and historical-corpus-import contracts referenced throughout this
  document.
- **[`StegVerse-Labs/Site`](https://github.com/StegVerse-Labs/Site)** is the
  web front end (`my-kv.html` et al.) that a person actually installs and
  clicks through — it implements the browser-side installation-status
  bridge and the Interlock/InTr entrypoint launcher that a service like
  this one would need to integrate with for anything beyond v0's manual
  export (§5.2). §5.3 below is grounded in that implementation, not just
  the abstract contract.

### 5.2 v0 — file-only, no hosted anything (build this first)

Matches MyKV's own stated baseline ("file-based. No account, hosted
service, SDK, or AI provider is required"):

1. A contributor keeps private research under their own KV's `_Entities/<person>/`
   and `02_Research/` — this never leaves their machine/storage.
2. When they're ready to share one fact, they run
   **`tools/export_kv_claim.py --file <entity-file> --submitted-by <identity>`**
   (built in Phase 3), which reads *only* the specific entity file they
   point it at and emits one `Claims/<id>.json` per embedded
   ` ```genealogy-claim ` block. No other vault content is read. This
   mirrors the `private_content_included=false` /
   `credential_material_included=false` contract MyKV's own
   `runtime/kv_my_kv_projection.py` uses for anything crossing its boundary.
   MyKV's own People entity template has no genealogy-specific fields, so
   the ` ```genealogy-claim ` block is a convention this project defines,
   documented in the tool's module docstring and `Claims/README.md`.
3. That Claim JSON is what gets submitted — today as a PR adding files
   under `Claims/`, later via an API (§7, Phase 5). The hub never touches
   the contributor's KV directly.
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

**Concrete contract, as actually implemented in `StegVerse-Labs/Site`.**
`assets/kv-entrypoint-intr-launcher.js` is the real thing a future
integration would consume, not a hypothetical one:

- It reads installation status from `window.StegVerseKVInstallationStatusBridge.getInstallationStatus()`
  and validates the result is schema `stegverse.kv.installation-status-projection/v1`,
  `state` one of `KV_INSTALLATION_VERIFIED` / `KV_INSTALLATION_NOT_VERIFIED`,
  `credential_material_present === false`, `provider_operation_authorized === false`,
  and `authority_effect === "NONE"` — failing closed (throwing
  `FAIL_CLOSED: ...`) on any mismatch, exactly the posture this design
  asks for in §5.2 and §6.
- On success it round-trips the validated `state` into the destination URL
  (`my-kv.html?entry=intr&kv_state=<state>`) purely as a launch artifact —
  `my-kv.html` itself never reads those query parameters back out; it
  re-derives its own status independently via a fresh
  `getInstallationStatus()` call on load. A URL carrying
  `kv_state=KV_INSTALLATION_VERIFIED` is therefore real evidence that
  *some* browser session got a verified projection at some point, but is
  not itself proof of current state — the same "import receipt != truth
  certification" posture this document already commits to, now with a
  concrete example. **Any future integration on this repo's side must
  apply the identical rule: never treat a `kv_state` query parameter, or
  any other artifact copied out of a MyKV URL, as sufficient evidence by
  itself — always require the live, schema-validated projection (or an
  admitted InTr receipt, per above), never a copied link.**
- The genuinely reusable piece for this design is the projection schema
  itself (`stegverse.kv.installation-status-projection/v1`) and its
  fail-closed validation shape. A future `tools/verify_kv_projection.py`
  in this repo (Phase 6) should mirror `validateProjection()` from
  `kv-entrypoint-intr-launcher.js` field-for-field rather than inventing
  its own projection shape, so a genealogy-hub-side consumer and the
  Site-side producer stay compatible.

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
| 0 | ✅ Fix the 3 CID bugs above, dedupe `FAMILY_TREE.md` and the duplicate Research files, fix dead links (`docs/start.md`, `/stories`, `/branches`, `Standards/Genealogy_Naming_Contract_v1.md`) | No |
| 1 | ✅ CID/reference validator (`tools/validate_ledger.py`) wired into `.github/workflows/test-readiness.yml`; `CID_Index_Master.md` becomes generated | No |
| 2 | ✅ Claim schema (`schemas/claim.schema.json`) + `Claims/` directory + CID Registrar (`tools/cid_registrar.py`, mints a CID only from a confirmed Claim) | No |
| 3 | ✅ Corroboration engine (§4) generates Confirmed Records from Claims (`tools/cid_registrar.py`, extended beyond Phase 2's minimal stub); `tools/export_kv_claim.py` for MyKV v0 (§5.2) | No |
| 4 | ✅ Multi-family namespaces — `NAMESPACES.md` registry + `tools/validate_ledger.py`/`tools/cid_registrar.py` enforcement, `docs/start.md` walkthrough | No |
| 5 | 📋 Planned (§8), not built. Read-only GitHub Pages site: no blocker. Write API: design settled, hosting platform still open | Read-only: No. Write API: needs a hosting decision |
| 6 | Governed live MyKV sync via Interlock/InTr (§5.3) | **Yes** — StegVerse-Labs shared runtime |

Phases 0–5 are buildable entirely inside this repo and don't require
anything from `continuity-vault-kit` beyond the export script matching its
projection conventions. Phase 6 is explicitly a future activation lane, the
same way MyKV treats its own unbuilt capabilities.

---

## 8. Phase 5 plan: hosted read service

Planned, not yet built. This section exists to answer *how*, so that
whenever building it starts, it starts from a decision rather than a
blank page.

### 8.1 Split the read side from the write side

These have very different risk profiles and should not be planned as one
lump:

- **Read-only browsing** — a visitor sees confirmed records, sourced
  claims, and contested facts without cloning the repo. This needs no new
  infrastructure, no credentials, and no hosting decision: **GitHub
  Pages**, which `docs/index.md`'s existing Jekyll front matter already
  targets. This is the part of Phase 5 that's ready to build whenever
  it's prioritized.
- **Write access over HTTP** (submitting a Claim without a GitHub
  account/PR) — this is the part that genuinely needs a hosting decision
  (platform, who holds any credentials, cost, abuse handling) and stays
  explicitly deferred; §8.3 below records the recommended shape for
  *when* that decision gets made, so it doesn't have to be re-derived
  from scratch later.

### 8.2 Read-only site (buildable now, no decision needed)

Render straight from the same files the validator already trusts —
never a separate database that could drift from `Individuals/`/`Claims/`:

- **Generator**: Jekyll (GitHub Pages' native engine) reading
  `Individuals/*.md`, `CID_Index_Master.md`, `Claims/*.json`,
  `Source_Registry/`, and `Research/` as Jekyll *data files*/collections,
  rather than a custom static-site generator — avoids adding a build
  dependency GitHub Pages doesn't already run for free.
- **Pages**: a namespace index (one per `NAMESPACES.md` entry), a person
  page per confirmed CID (rendering the same sections `Schema_v1.md`
  requires, plus a "claims behind this record" panel for claim-managed
  entries), a pending/contested Claims dashboard (surfaces exactly the
  `contested` and not-yet-confirmed clusters `tools/cid_registrar.py`
  already computes), and a search/browse index across all namespaces.
- **Freshness**: a GitHub Actions step (alongside the existing
  `test-readiness.yml` checks) rebuilds and deploys the Pages site on
  every push to `main` — no separate deploy credential beyond what
  GitHub Pages' own `actions/deploy-pages` action already uses.
- **Privacy**: the generator must apply `Standards/Living_Persons_Privacy_Protocol.md`
  at render time, not just trust that `Individuals/*.md` already
  redacted everything — a defense-in-depth check, since a public static
  site is a bigger exposure surface than a repo a contributor has to
  clone first.

### 8.3 Write API (deferred — recorded for whenever it's decided)

The recommended shape, so the eventual hosting decision only has to pick
a platform, not redesign the approach: **the API's only job is to open a
PR**, authenticated as a bot/service account, adding one `Claims/*.json`
file per submission — it does not reimplement corroboration, minting, or
generation logic. That stays exactly what it is today:
`tools/cid_registrar.py`, running in CI on the resulting PR, unchanged.
This avoids needing a database (the repo *is* the database), sidesteps
reimplementing the fail-closed validation this design leans on so
heavily, and means a submission is inherently reviewable before it lands
on `main`, matching the "reversible, transparent" commitments in
`README.md` and `docs/ethics.md`.

What's still genuinely open, and needs a person to decide rather than
tooling to derive: which hosting platform runs that thin API layer, who
holds the bot account's PR-creation credential, and what abuse/rate-limit
protection a public write endpoint needs that a PR-only workflow doesn't.

---

## 9. Open questions

1. **Submitter identity for independence checks (§4.1):** GitHub account
   is enough for v0. Do we want an explicit link to a MyKV instance ID
   later, so corroboration can distinguish "two different people" from
   "one person's two KV instances" more rigorously?
2. ~~**Hosting for Phase 5's read API/site**~~ — **narrowed, not fully
   resolved**: see §8. The read-only side needs no decision (GitHub
   Pages). The write-API side's *design* is settled (a thin PR-opening
   layer in front of the unchanged Claims/CI pipeline, §8.3) but its
   *hosting platform* is still genuinely open and deferred until someone
   decides to build it.
3. ~~**Multi-family namespace governance (Phase 4)**~~ — **resolved**:
   fork-based, per `README.md`'s "Enable duplication across other
   families." A new family forks this repo and registers its own
   namespace(s) in `NAMESPACES.md`; this repo can also grow a
   *second* namespace directly (documented in `NAMESPACES.md` itself) if
   a connected family's line is being researched here rather than
   separately. Either way, `tools/validate_ledger.py` and
   `tools/cid_registrar.py` both fail closed on any CID/claim using a
   namespace that repo's `NAMESPACES.md` doesn't list — see
   `test_namespaces.py`.

Feedback on any of the above changes the phase order; nothing after Phase 0
should start until this doc is agreed on.
