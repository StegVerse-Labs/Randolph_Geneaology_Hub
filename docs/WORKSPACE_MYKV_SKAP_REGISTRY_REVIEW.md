# WorkSpace / MyKV / SKAP Vault — canonical task registry review

Date: 2026-09-27
Method: read-only inspection of the canonical registry at
`StegVerse-Labs/.github` `origin/main` `495832cd` (**generation 260**,
status `EXISTING_SHWP_SOURCE_IDENTITY_RECONCILED_RUNTIME_EVIDENCE_PENDING`),
plus local checkouts of `StegVerse-Labs/Site` (`16b99c34`) and
`StegVerse-Labs/continuity-vault-kit`. Every count below was computed, not
recalled. `continuity-vault-kit`'s WorkSpace test suite was executed
(`tests/test_workspace_projection.py` — 4 passed).

This document records evidence. It mints no authority, claims no runtime
observation, and upgrades no handoff state.

Companion: `docs/KV_SKAP_GAP_SURVEY.md` (2026-09-21) covers KV + SKAP Vault
broadly. This review is the WorkSpace-specific cut, which that survey did not
reach.

---

## 1. Headline

**WorkSpace is not a registered canonical task, and what is built is read-only
over a store that has no writer.**

Three findings carry the rest of the document:

1. **Zero canonical registry tasks govern the StegVerse WorkSpace surface.**
   The only task id containing `WORKSPACE` is
   `SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004`, and its WORKSPACE is
   **Google** Workspace, not yours. WorkSpace exists canonically only as a
   *Site-local claim* (`SITE-WORKSPACE-INTEROPERABILITY-001`) whose task id
   appears nowhere in `.github`.

2. **The WorkSpace KV store has exactly one writer, and it is Google Drive.**
   `continuity-vault-kit/runtime/workspace_projection.py` reads seven JSON
   files under `KnowledgeVault/_System/Workspace/`. The only module that may
   write that path is `runtime/personal_provider_binding.py`, whose
   materialization scope `_System/Workspace/**` is fed by a read-only
   `GOOGLE_DRIVE` broker result. Nothing else writes those files. So the
   projection's own two legal states are `KV_WORKSPACE_PROJECTED` and
   `KV_WORKSPACE_EMPTY`, and absent a hand-placed file or a Google Drive
   materialization it is structurally `KV_WORKSPACE_EMPTY`.

3. **Of your four stated properties, one is partly built, three are absent.**
   Not blocked, not in progress — absent, with no task registered to produce
   them. Detail in §4.

The name collision in (1) is not a coincidence, and that is the part worth
sitting with: the Google-Workspace task is the *only* thing that populates the
StegVerse WorkSpace store. Data flows **in from Google**; nothing flows from
WorkSpace into SKAP Vault.

---

## 2. Registry census

`data/canonical-task-registry.json` and `data/canonical-task-records/` are
**different sets**, which matters for any search:

| Set | Count |
| --- | --- |
| Tasks in `canonical-task-registry.json` `tasks[]` | 93 |
| Record files in `data/canonical-task-records/` | 163 |
| In both | 73 |
| Registry task with **no** record file | 20 |
| Record file **not** in the registry `tasks[]` | 90 |

A search of one set silently misses the other. Searching `tasks[]` alone hides
`SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004`; searching records alone hides
`MYKV-NATIVE-IOS-PACKAGING-DISTRIBUTION-001`.

### 2.1 Every task id matching WORKSPACE / MYKV / SKAP / VAULT

Seven, across both sets:

| Task id | State | COSV | Where |
| --- | --- | --- | --- |
| `MYKV-NATIVE-IOS-PACKAGING-DISTRIBUTION-001` | `ACTIVE_SOURCE_WORK` | `40000100100000` | registry only |
| `MYKV-PERSONAL-DATA-BACKUP-001` | `ACTIVE` | — | record only |
| `SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004` | `ACTIVE` | `71000000100110` | record only |
| `SS-SKAP-ACCOUNT-INVENTORY-PROJECTION-001` | `ACTIVE` | — | record only |
| `SS-SKAP-AUTHENTIC-ACCOUNT-METADATA-POPULATION-001` | `ACTIVE` | — | record only |
| `SS-KV-SKAP-SOCIAL-RELEASE-001` | `ACTIVE` | `60000000102000` | both |
| `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` | `ACTIVE` | `50000000102000` | both |

**Zero task ids contain `VAULT`.** SKAP Vault has no task named for it; it is
referenced only as the authority term inside other tasks' goals and in the
global invariants.

### 2.2 The word "workspace" anywhere in a registry task body

Three tasks, all incidental:

- `SDK-UNTRUSTED-DEPENDENCY-EXECUTION-BOUNDARY-001` — "IDE **workspace**
  initialization" (an attack surface, not your surface).
- `SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004` — Google Workspace (§3).
- `GP10-COMMERCIAL-RESPONSE-VALIDATION-001` — commercial outreach.

So: no canonical task, in either set, governs the browser WorkSpace.

### 2.3 Related canonical tasks that bear on WorkSpace without naming it

| Task id | State | Relevance |
| --- | --- | --- |
| `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` | `ACTIVE` | The **only** task that makes the `StegOS Device ↔ KnowledgeVault ↔ SKAP Vault` lane bidirectional. If WorkSpace is ever to be an ingress surface, this is the lane it must ride. It is scoped to "sovereign single-device". |
| `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001` | `ACTIVE` (`50000010100000`) | KV-bound browser projection with "authentic KV projection … without binding completion to a physical device". Closest existing task to your property 4. It is about release/bootstrap flow, not WorkSpace. |
| `SS-KV-SKAP-SOCIAL-RELEASE-001` | `ACTIVE` | Personal-KV-private-by-default with bounded release grants. The visibility model WorkSpace renders (`visibilityAllows`) is a hardcoded duplicate of this doctrine. |
| `MYKV-PERSONAL-DATA-BACKUP-001` | `ACTIVE` | Personal KV durability, adjacent to cross-device continuity. |
| `TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001` | `ACTIVE` | Provider-neutral sovereign KV event custody — the shape a state-transition-driven WorkSpace would need. Scoped to the Task Registry's own event history. |

None of these is WorkSpace. Each would be a dependency of a WorkSpace task if
one existed.

---

## 3. `SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004` is Google Workspace

Because the name will keep causing this confusion, the evidence, verbatim from
the record:

- `components`: `owner-present-google-consent`,
  `external-provider-file-probe`, `external-collaboration-client-secret-custody`,
  `sovereign-service-gateway`.
- `handoff_projection_refs` includes
  `StegVerse-org/StegVerse-SDK:docs/SHARED_DOCS_EPHEMERAL_MANIFEST_WORKSPACE_MIRROR_HANDOFF.md`.
- `parent_task_id`: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`.
- `activation_condition`: `PARENT_GOAL_PROMPT_COUNT_REACHES_20`.

Its goal is an external-collaboration runtime proof chain — reseal/listener
consumption, sovereign callback reachability, owner-present consent, provider
probe, MIR reporting, Master Records reconstruction. It is about collaborating
through Google, not about representing MyKV in a browser.

**One thing it does own that belongs to your WorkSpace:** its broker is the
only writer into `_System/Workspace/**` (§5.1). The naming collision has become
a functional one.

---

## 4. Your four properties, measured

> "WorkSpace is intended to be the browser representation of MyKV and Org KV
> including capabilities functions; and the input surface for all sensitive info
> that enters into the SKAP Vault. This WorkSpace should be 100% state
> transition driven such that the WorkSpace remains precise and consistent
> across any browser session on any device."

| # | Property | Registered? | Built? |
| --- | --- | --- | --- |
| P1a | Browser representation of **MyKV** | no canonical task | **partly** — real fail-closed DEVICE_KV read path |
| P1b | Browser representation of **Org KV** | no canonical task | **no** — browser `sessionStorage` placeholder |
| P1c | **Capabilities functions** | no canonical task | **no** — declared, never bound |
| P2 | Input surface for **all sensitive info → SKAP Vault** | no canonical task | **no** — zero write paths; ≥4 competing ingress surfaces already ship |
| P3 | **100% state-transition driven** | no canonical task | **no** — mutable object + direct render calls |
| P4 | Precise and consistent **across any browser session on any device** | no canonical task | **no** — gated on per-browser IndexedDB node registration |

### P1a — MyKV representation: the one real part

`Site:assets/workspace-kv-bridge.js` (68 lines) is genuinely good work. One
call, `loadPersonalWorkspace()`, runs the whole governed path: node status →
InTr intent → HB binding → materialization request → queue on registered node →
sync → delivery receipt → **payload hash equality** → **exact canonical
recovery equality** (`intr.canonical(decoded)===intr.canonical(response)`) →
schema and authority validation. Every step is `requireValue(...)`, i.e.
fail-closed, and it asserts `credential_material_present===false`,
`provider_operation_authorized===false`, `workspace_grants_authority===false`,
`authority_effect==="NONE"`.

It is also strictly **read-only**: `operation:"REQUEST"`
(`workspace-kv-bridge.js:14`) with a `requested_scope` of seven read fields
(`:18`). There is no write, put, submit, or mutate path anywhere in the
WorkSpace files.

### P1b — Org KV: a placeholder, and the guard that misses it

`Site:assets/workspace.js:33`, `renderKvGate()`, in organizational mode:

```js
const ctx=JSON.parse(sessionStorage.getItem("stegverse.workspace.orgEmpGate")||"{}");
const admitted=keys.every(k=>ctx[k]===true);
```

The five Org-Emp-KV predicates — `employee_identity_matches`,
`machine_identity_matches`, `active_membership`, `role_capability_admitted`,
`transition_admitted` — are read from **browser session storage**. Nothing in
the repository writes that key; the single grep hit is the read itself. There is
no organizational projection on the server either: `workspace_projection.py`
hardcodes `workspace_type:"PERSONAL"` and exposes no
`get_organizational_workspace_projection`.

Scope of the defect, stated precisely: `admitted` is used **only** to render the
words `ADMITTED` or `LOCKED`. Nothing gates on it, so this is not an authority
bypass. It is a display that can be made to read `ADMITTED` from the browser
console with no KV/SKAP admission behind it, which is its own problem — two of
the five predicates it displays (`role_capability_admitted`,
`transition_admitted`) are admission facts, and
`TASK-REGISTRY-KV-SKAP-VERIFIER-NODE-INVARIANT-001` makes
`user_verification_authority: "KV/SKAP Vault"` **exclusive**
(`NO_SECONDARY_USER_VERIFIER_OUTSIDE_KV_SKAP_VAULT`).

**And the test that exists to prevent exactly this does not catch it.**
`Site:tests/workspace-kv-binding.test.cjs:11`:

```js
if(ui.includes('localStorage.getItem("stegverse.workspace.'))throw new Error('Workspace must not substitute browser localStorage for canonical KV data');
```

The guard names `localStorage`. The code uses `sessionStorage`. The assertion
names one API and the code uses the adjacent one — the same defect shape found
repeatedly across this ecosystem: *something moved, and the thing asserting
about it did not follow.* The fix is one token:

```js
if(/(local|session)Storage\.getItem\("stegverse\.workspace\./.test(ui))throw new Error('Workspace must not substitute browser storage for canonical KV data');
```

That patch is **not applied** — it lands in `StegVerse-Labs/Site`, which needs
its own pre-work claim, and it will fail the suite until the Org path has a real
source. It is written here so the decision is explicit rather than implied.

### P1c — Capabilities functions: declared, then discarded

`Site:data/workspace/bootstrap.json` declares 10 capabilities (`FEED`,
`CONTACTS`, `FRIENDS`, `ORGANIZATIONS`, `MEMBERSHIPS`, `SEARCH`, `MESSAGING`,
`WORK`, `AI_ASSISTANT`, `AI_CONTACTS`), the four principal types with badges,
eight relationship types, eight visibility levels, and the five Org-Emp-KV
predicates.

**It is fetched and thrown away.** `state.bootstrap` is assigned twice — once
from the fetch, once to `{}` in the catch (`workspace.js:38`) — and **never
read again**. The UI hardcodes its own copies of all of it: `badge()` hardcodes
the principal-type map, `visibilityAllows()` hardcodes the eight visibility
values, `renderKvGate()` hardcodes the five predicates. Two sources of truth,
no binding between them. That is a live drift hazard against "precise and
consistent".

Of the 10 declared capabilities:

| Capability | Status |
| --- | --- |
| `FEED`, `CONTACTS`, `FRIENDS`, `ORGANIZATIONS`, `MEMBERSHIPS`, `SEARCH`, `AI_ASSISTANT` | render from the projection |
| `MESSAGING` | `alert(JSON.stringify(action,null,2))` — a browser alert dialog; no dispatch |
| `WORK` | hardcoded empty-state string in `workspace.html:32` |
| `AI_CONTACTS` | no distinct path; folded into `CONTACTS` |

The governing invariant for what "capabilities functions" must mean is already
written: `node_local_capability` — "A node may expose and invoke locally
available capabilities **after** applicable KV/SKAP-backed user-verification
state and Interlock/InTr admission are bound to the exact operation." Nothing in
WorkSpace binds a capability to an admitted operation.

### P2 — SKAP Vault input surface: absent, and already contested

There is **no** occurrence of `skap` or `vault` in `workspace.html`,
`assets/workspace.js`, `assets/workspace.css`, or `data/workspace/bootstrap.json`.
The only `<input>` on the page is `#search`. WorkSpace cannot accept sensitive
input today by any path.

Meanwhile sensitive ingress to SKAP **already ships on at least four other Site
surfaces**:

| Surface | Lines | SKAP ingress modules |
| --- | --- | --- |
| `my-kv.html` | 612 | `my-kv-connected-accounts-bridge.js`, `my-kv-personal-form-profile.js`, + 16 more `my-kv-*.js` (2,921 lines total) |
| `stegos-apple-credential.html` | 31 | `assets/stegos-apple/app-store-connect-skap-ingress{,-ui,-submission}.js` |
| `stegfin-trade.html` | 59 | `assets/stegfin-phone/coinbase-skap-ingress{,-ui}.js`, `coinbase-skap-submission.js` |
| `generic-login-test.html` | 221 | `assets/kv-ui/intr-auth-client.js` + `intr-kv-client.js`; carries a live `<input type="password">` for SKAP step-up re-authentication (`:72`) |

So "the input surface for **all** sensitive info" is contradicted by shipped
code in four places. Consolidating them behind WorkSpace is real, unregistered,
and non-trivial work — and it is a security-relevant consolidation, because each
of those surfaces currently carries its own ingress validation.

Two precisions on that table, since "test" in a filename invites the wrong
conclusion: `generic-login-test.html` is a maintained reference surface — it has
its own CI gate, `.github/workflows/generic-login-test-validation.yml`, and
`intr-kv-client.js` names `generic-login-test` as a requester component — and it
implements the `KV → SKAP` step-up boundary explicitly ("Ordinary KV login is
insufficient. Re-authentication creates a separate step-up assertion before the
KV→SKAP boundary is projected."). It is the surface closest to what you describe
WorkSpace should be, and it is not WorkSpace.

**`my-kv.html` is already a second, larger browser representation of MyKV.** 612
lines plus 18 modules, against WorkSpace's 43 plus 150. Neither page links to
the other — `grep -i workspace my-kv.html` and `grep -i my-kv workspace.html`
are both empty. Compare record classes: the MyKV family uses 12
(`MY_KV_INSTANCE_SET_PROJECTION`, `MY_KV_RELATIONSHIP_TRANSITION_REQUEST`,
`MY_KV_PROVIDER_OPERATION_REQUEST`, `MY_KV_SET_PROJECTION_ADMISSION_TRIGGER`,
`MY_KV_N_RESIDENT_TRANSPORT`, …); WorkSpace uses one,
`WORKSPACE_PERSONAL_PROJECTION`, read-only.

If WorkSpace is to be the browser representation of MyKV, then **one of these
two surfaces has to absorb the other**, and that decision is not recorded
anywhere.

### P3 — State-transition driven: not at all, but the machinery exists nearby

`assets/workspace.js` holds a plain mutable object:

```js
const state={bootstrap:null,mode:"personal",projection:null,data:{…}};
```

`setMode()` assigns `state.mode` and calls renderers directly. There is no
transition table, no reducer, no admitted-transition record, no event log, and
nothing is persisted or recorded when the mode changes. The only cross-call
state is the `sessionStorage` read in §P1b.

The shape you are describing exists one directory away, in the MyKV family:
`MY_KV_RELATIONSHIP_TRANSITION_REQUEST`, schema
`stegverse.site.my-kv.relationship-transition-request/v1`. WorkSpace has no
transition record class at all.

The ecosystem also already carries the reusable component for the adjacent
problem — `RTC-BROWSER-LOCAL-STATE-SCHEMA-MIGRATION-V1` in
`.github/data/reusable-browser-local-state-schema-migration-component-contract.json`,
whose `authority_owner` is `CANONICAL_RUNTIME_OWNER_OF_THE_PERSISTENT_STATE` and
whose `execution_role` states the browser "may execute an already-admitted
migration but is not a user verifier or transition authority." Nothing binds
WorkSpace to it.

### P4 — Consistent across any session on any device: contradicted at the first precondition

`workspace-kv-bridge.js:45`:

```js
requireValue(s&&s.registered===true&&s.registration&&s.registration.node_id,
  "Register this device before opening Personal Workspace KV context");
```

Node registration lives in **device-local IndexedDB** — the `META` object store,
key `registration`, in `Site:assets/stegverse-node-continuity-impl.js` (which
also enforces `FAIL_CLOSED: registration exists without Receipt #1` and
`registration and Receipt #1 do not match`). An unregistered browser throws
`REGISTER_DEVICE_REQUIRED`. A fresh browser profile on a new device mints a new
`node_id` with a new Receipt #1.

Consequence: WorkSpace shows nothing on a new browser session until that browser
has its own node registration, and the organizational half's only state is
`sessionStorage`, which is per-tab and cleared when the tab closes. That is the
strongest possible violation of the property you stated.

**The intent is already canonical doctrine, so this needs no new policy.** From
`.github/data/task-registry-global-invariants.json`
(`TASK-REGISTRY-KV-SKAP-VERIFIER-NODE-INVARIANT-001`):

- `stegos_device_role`: `INTERCHANGEABLE_TRANSPORT_NODE`
- `physical_device_identity_gate`: `NONE_PROHIBITED`
- `device_interchangeability`: "Replacing one eligible StegOS device/node with
  another does not change the user's verifier. Only available local capability
  endpoints and resulting execution evidence may change."

Stated carefully: requiring a registered node as *transport* is not itself a
verifier gate, so this is not a clean invariant violation. But the effect
contradicts P4 — device registration state currently determines whether
WorkSpace has anything to show — and no registered task exists to make the
WorkSpace projection independent of which node registration happens to be
present.

---

## 5. The store underneath, and why it is empty

### 5.1 Seven files, one writer, and the writer is Google

`continuity-vault-kit/runtime/workspace_projection.py` (115 lines, 4 tests
passing) reads seven optional files from `KnowledgeVault/_System/Workspace/`:
`workspace.json`, `principals.json`, `relationships.json`,
`organizations.json`, `memberships.json`, `feed.json`, `assistant.json`. It
validates each file's schema and `authority_effect==="NONE"`, derives
`ai_label_required` from `principal_type`, checks relationship and feed actors
against known principals, validates membership status against
`{ACTIVE,PENDING,SUSPENDED,REVOKED}`, and rejects path escapes. It is careful,
fail-closed code.

It is also **purely a reader**. The only module in `continuity-vault-kit` that
may write that path is `runtime/personal_provider_binding.py`, which admits
`_System/Workspace/**` as a materialization scope
(`_path_admitted`, matching `_System/Workspace/[A-Za-z0-9._-]+`) and materializes
bytes from a broker response it requires to be
`provider=="GOOGLE_DRIVE"`, `read_only is True`,
`provider_mutation_performed is False`.

So the complete answer to "where does WorkSpace data come from" is: **a
read-only Google Drive materialization, or a hand-placed file.** There is no
StegVerse-native writer. `KV_WORKSPACE_EMPTY` is the structural default, which
is why the UI ships the string `"Personal KV connected; Workspace registry is
empty."` and why the test asserts on it.

### 5.2 A reader/writer disagreement on the same lane

`workspace_projection.py` rejects any field whose **name** contains any of
`password, secret, token, credential, private_key, seed, mnemonic,
recovery_code` — `FORBIDDEN`, checked against `str(key).lower()`.

`credential_authority` contains `credential`.

- `personal_provider_binding.py` **requires**
  `result.get("credential_authority")=="TV/TVC"` on the broker result.
- `Site:data/workspace/bootstrap.json` carries
  `"credential_authority": "TV/TVC"` in its `authority` block.

A WorkSpace file carrying the ecosystem's own mandatory non-secret assertion
would therefore be rejected by the reader as
`secret_field_forbidden:workspace.json.credential_authority`. The two halves of
one lane disagree about whether `credential_authority` is a secret.

This is a named instance of finding **C3** in `docs/KV_SKAP_GAP_SURVEY.md`: ten
separately hand-rolled substring secret scanners across
`continuity-vault-kit/runtime/`, several of which ban the assertions that prove
a boundary is governed correctly. The fix remains the one that survey named —
one shared allow-listed scanner, not ten patched token tuples.

---

## 6. What is registered vs. unregistered, in one place

**Registered and active** (canonical tasks that exist and bear on this work):
`STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001`,
`KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`,
`SS-KV-SKAP-SOCIAL-RELEASE-001`, `MYKV-PERSONAL-DATA-BACKUP-001`,
`MYKV-NATIVE-IOS-PACKAGING-DISTRIBUTION-001`,
`SS-SKAP-ACCOUNT-INVENTORY-PROJECTION-001`,
`SS-SKAP-AUTHENTIC-ACCOUNT-METADATA-POPULATION-001`,
`TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001`.

**Site-local claims with no canonical task behind them** (the id resolves in
`Site`, and nowhere in `.github`):
`SITE-WORKSPACE-INTEROPERABILITY-001`,
`GP10-SITE-SECURE-GUIDED-WORKSPACE-001`,
`GP10-SITE-WORKSPACE-TASKS-001`,
`SITE-KV-SKAP-ACCOUNT-METADATA-BRIDGE-001`,
`SITE-SKAP-INTR-PUBLIC-ROUTE-CONSUMER-001`,
`SITE-APP-STORE-CONNECT-SKAP-INGRESS-001`,
`SITE-STEGFIN-SKAP-INTR-SUBMIT-001`,
`SITE-SS-SKAP-AUTHENTIC-ACCOUNT-METADATA-POPULATION-001`.

**Unregistered entirely** — no canonical task, no Site claim, no record:

1. Organizational WorkSpace projection (server function and browser path).
2. WorkSpace capability binding to admitted operations.
3. WorkSpace as SKAP Vault ingress, and consolidation of the four existing
   ingress surfaces.
4. WorkSpace state-transition model and transition record class.
5. WorkSpace projection continuity across node registrations / devices.
6. Resolution of `workspace.html` vs `my-kv.html` as the MyKV representation.
7. A StegVerse-native writer for `_System/Workspace/*.json`.

`SITE-WORKSPACE-INTEROPERABILITY-001`'s own `next_task_after_release` already
names (1): *"Bind Organizational Workspace to organization-resident
Org-KV/Org-Emp-KV admission and then route federated discovery/feed/messaging/
work through the org .github InTr boundary."* That successor was never
registered as a canonical task.

---

## 7. Decisions this review cannot make

These are registry-owner calls, recorded rather than assumed:

1. **Does WorkSpace get a canonical task id?** Today it is a Site claim. Every
   property you stated is cross-repository (`Site`, `continuity-vault-kit`,
   `.github`, `StegOS`), and a Site-local claim cannot fence work in another
   repository.
2. **`workspace.html` or `my-kv.html`?** Two browser representations of MyKV
   ship, unlinked, with 12 record classes on one side and 1 on the other.
3. **Does the WorkSpace store keep a Google Drive writer?** If WorkSpace is to
   be the sensitive-input surface, having its only writer be an external
   provider materialization is backwards, and unwinding it touches
   `SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004`.
4. **Is the name collision resolved by renaming?** `SDK-WORKSPACE-EXTCOLLAB-*`
   will keep being mistaken for the StegVerse WorkSpace — it already shares its
   KV path.

## 8. Not done, and why

- **The `sessionStorage` test-guard patch (§P1b)** is written out but not
  applied. It belongs to `StegVerse-Labs/Site`, which requires its own pre-work
  claim resolving to exactly one active claim for the PR branch, and the patch
  fails the suite until the Org path has a real source. Say the word and it
  lands as a Site PR with the claim ceremony.
- **No canonical task was registered.** Registering a WorkSpace task is a
  registry-owner action (§7.1), and `StegVerse-Labs/.github` cannot be attached
  to a session — its name begins with `.`, which the repository-attach path
  rejects. That constraint is recorded in `docs/HANDOFF_ACTIONS.md`.
- **No runtime observation is claimed.** Nothing here was executed against a
  live KV; the only execution was `continuity-vault-kit`'s own WorkSpace test
  suite (4 passed).
