# KV / SKAP Vault Gap Survey

Date: 2026-09-21
Scope: the KV + SKAP Vault surface that `docs/MYKV_SERVICE_DESIGN.md` §10 is paused on.
Method: read-only inspection of local checkouts of `StegVerse-Labs/.github`,
`StegVerse-Labs/continuity-vault-kit`, `StegVerse-Labs/StegOS`,
`StegVerse-Labs/StegCore`, `StegVerse-Labs/Site`, plus executing each repo's
own test suite.

This document records evidence. It claims no runtime observation, mints no
authority, and does not upgrade any handoff state.

---

## 1. Headline

The KV/SKAP surface is **not** mostly-unbuilt. It is mostly **built and
blocked**, with a small number of genuinely-owed pieces and a small number of
pieces that are written but demonstrably do not execute.

The three categories, with counts from the survey:

| Category | What it means | Count |
| --- | --- | --- |
| **A. Source-complete, runtime-blocked** | Code exists, tests pass, handoff says the only remaining step is authentic runtime evidence. No code is owed. | dominant majority |
| **B. Genuinely unbuilt** | A named component has no implementation anywhere in the five repos. | 3 |
| **C. Written but broken** | Code exists and is referenced as done, but fails on execution. | 6 |

Category C is the important finding, because it is invisible to the handoff
documents — every one of these lanes reads as implemented.

---

## 2. Category A — source-complete, waiting on runtime

These need no code from anyone. They need one authentic execution on the
owner's device.

| Lane | Owning repo | Recorded state | Evidence |
| --- | --- | --- | --- |
| Device↔KV↔SKAP four-leg roundtrip | StegOS + `.github` | `AWAITING_AUTHENTIC_FOUR_LEG_RUNTIME_EVIDENCE` | `handoffs/STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001.json`; blockers are all `*_NOT_YET_OBSERVED` |
| KV→SKAP ciphertext custody transport | `.github` | `MERGED_ORGANIZATION_VALIDATED / AUTHENTIC_RESIDENT_KV_SKAP_EVENT_NOT_YET_OBSERVED` | `docs/KV_SKAP_OPERATIONAL_INTR_TRANSPORT_MIRROR_HANDOFF.md`; all 9 source-completion predicates listed as met; `tests/test_kv_skap_custody_materialization.py` — 8 passed |
| SKAP↔KV↔Device roundtrip verifier | StegOS | `SOURCE_ROUNDTRIP_VERIFIER_IMPLEMENTED_AWAITING_VALIDATION` | `stegos/skap_kv_device_roundtrip.py` present; StegOS suite 1652 passed |
| `kv-skap-account-metadata` InTr profile | StegOS | `IMPLEMENTED_AWAITING_VALIDATION` | `specs/kv-skap-account-metadata-profile.v1.json` present + dedicated workflow |
| Canonical runtime domain binding | StegOS | merged (the `.github` handoff no longer carries `DEVICE_KV_SKAP_CANONICAL_RUNTIME_DOMAIN_BINDING_NOT_YET_MERGED`) | `stegos/device_kv_skap_canonical_runtime.py` present |
| Connected Accounts UI | Site | merged at `b310ff3` | `my-kv-connected-accounts.html`, `assets/my-kv-connected-accounts.js` |

**StegOS test suite: 1652 passed.** (One file, `tests/test_verifier_plugins.py`,
cannot be collected in this container for a missing `_cffi_backend`; that is an
environment gap, not a repo defect.)

---

## 3. Category B — genuinely unbuilt

Three named components have **no implementation anywhere** in the five repos
inspected.

### B1. `StegVerseKVAccountObservationBridge` — owner: Site

The Connected Accounts page consumes it:

```
my-kv-connected-accounts.html:35        var bridge = window.StegVerseKVAccountObservationBridge || null;
assets/my-kv-connected-accounts.js:48   if(!bridge || typeof bridge.populateSelectedAccountMetadata !== "function")
                                          return Promise.reject(new Error("FAIL_CLOSED: ..."));
scripts/check_my_kv_directory.py:59     asserts the marker string is present
```

Those are the **only four** references in the repo. Nothing defines it. The UI
therefore always takes its fail-closed branch. This is exactly what
`.github/docs/SKAP_AUTHENTIC_ACCOUNT_METADATA_POPULATION_MIRROR_HANDOFF.md`
lists as remaining work item 1.

Precedent to follow already exists in the same directory:
`assets/my-kv-personal-form-profile-write-bridge.js` and
`assets/my-kv-personal-profile-write-bridge.js`.

### B2. `SKAP_ACCOUNT_METADATA_ADMIT` consumer — owner: TVC

`continuity-vault-kit/KV_SKAP_INTR_ACCOUNT_TRANSFER_MIRROR_HANDOFF.md` states
the receiving side is unimplemented and specifies seven requirements for it
(exact packet + envelope validation; retained InTr decision bound to the exact
hashes; rejection of missing owner-selection evidence, secret-bearing fields,
raw provider account ids, hash drift, replay mutation and synthetic elevation;
bounded non-secret persistence; receipt compatible with
`TVC/tools/skap_account_inventory_projection.py`; idempotent exact replay;
refusal of conflicting replay).

No file in `.github`, CVK, StegOS, StegCore or Site implements it. The only
non-CVK, non-StegOS hit for the string across all five repos is a task record.

### B3. Site-side propagation of the account-metadata profile — owner: Site

`stegos/docs/KV_SKAP_ACCOUNT_METADATA_PROFILE_MIRROR_HANDOFF.md` remaining
items 3–5 require the profile to reach the generated Site browser connector and
bind `populateSelectedAccountMetadata` to it. Site contains **zero** references
to `kv-skap-account-metadata` or `SKAP_ACCOUNT_METADATA_ADMIT`.

---

## 4. Category C — written but broken

Each of these was found by running the repo's own tests. Each reads as complete
in its handoff.

### C1. `continuity-vault-kit/runtime/kv_skap_account_transfer.py` — producer cannot build any packet

`build_transfer_packet()` raises on **every** input. All 7 tests in
`tests/test_kv_skap_account_transfer.py` fail with:

```
KVSKAPTransferError: secret_or_raw_identifier_field_prohibited:packet.contains_secret_material
```

Root cause: the packet is required by `validate_transfer_packet()` to carry the
assertion `contains_secret_material: False`, and the same function's
substring scanner rejects any key containing the token `"secret"`. The
exclusion list at line 74 exempts only `raw_provider_account_identifier_present`.
The field is simultaneously mandatory and forbidden.

This is the producer half of the very lane B2 is waiting to consume.

### C2. `continuity-vault-kit/runtime/kv_interlock_endpoint.py` — rejects the ecosystem's own credential-authority assertion

`_contains_forbidden_name()` bans the token `"credential"`. The ecosystem
requires `credential_authority: "TV/TVC"` on governed surfaces. Any policy
result whose context carries that assertion is classified secret-bearing and the
request returns `FAIL_CLOSED` with
`policy_profile: "KV-INTERLOCK-v1:POLICY_RESULT_REJECTED"`.

Observed live in `tests/test_persistent_session_interlock.py::test_request_returns_bounded_reconstruction_projection_through_existing_runtime`:
the policy adapter returns `ALLOW_BOUNDED_CONTEXT`; the runtime overrides it to
`FAIL_CLOSED`. The offending key is
`context.session_head.credential_authority`.

### C3. Systemic: ten independent secret scanners, three of which ban `credential_authority`

C1 and C2 are instances of one pattern. `continuity-vault-kit/runtime/` contains
**ten** separately hand-rolled substring secret scanners with ten different
token lists. Cross-checking each against the ecosystem's mandatory non-secret
assertion names:

| Module | Bans `credential_authority` | Bans `contains_secret_material` |
| --- | --- | --- |
| `kv_interlock_endpoint.py` | yes | yes |
| `portable_direct_source_ingress.py` | yes | yes |
| `workspace_projection.py` | yes | yes |
| `kv_skap_account_transfer.py` | no | yes |
| `connection_assembly.py` | no | yes |
| `direct_source_ingress.py` | no | yes |
| `legacy_capsule.py` | no | yes |
| `persistent_session_reconstruction.py` | no | yes |
| `personal_finance.py` | no | yes |
| `conversation_event_store.py` | no | no (bans `token_bucket`) |

Every module that governs a boundary is liable to reject the assertions that
prove the boundary is being governed correctly. The fix is one shared
allow-listed scanner, not ten patched token tuples.

### C4. `continuity-vault-kit/runtime/portable_direct_source_ingress.py` — unimportable (raw NUL byte in committed source)

Byte offset 2583, line 85, inside a guard that is itself checking for NUL:

```python
_require("\x00" not in name, "file_name_nul_forbidden")
```

The `\x00` was committed as a **literal NUL byte** rather than the escape. The
NUL is present in the HEAD blob, not a local corruption. Python 3.11 refuses to
compile it:

```
SyntaxError: source code string cannot contain null bytes
```

The module and its tests are therefore dead. No workflow in CVK's 54 references
`portable_direct_source`, which is how it reached main. The handoff reads
`ACTIVE_IMPLEMENTATION`.

### C5. `.github/scripts/execute_device_kv_skap_roundtrip_event.py` — broken import path under test

Line 30 imports `refresh_sovereign_worker_runtime_source` bare after putting the
**repo root** on `sys.path`; the module lives in `scripts/`. Line 31 correctly
uses the `scripts.` prefix.

Scope, stated precisely: the CLI entrypoint **works** (`--help` succeeds,
because `python scripts/x.py` puts `scripts/` on the path). Only import-based
use breaks, which is why `tests/test_device_kv_skap_event_execution.py` cannot
be collected. This is a test-coverage hole on the roundtrip entrypoint, not a
runtime blocker on the roundtrip itself.

### C6. `.github/tests/test_canonical_transition_predecessor_closure.py` — one unrestored `sys.modules` write breaks 46 other test files

At **module import time**, before any test runs, the file installs a fake
package and a stub submodule into `sys.modules` and never restores them:

```python
package = types.ModuleType("heartbeat_runtime")
package.__path__ = []
oscillator = types.ModuleType("heartbeat_runtime.independent_oscillator")
oscillator.current_reference = lambda now_ns: {...}
sys.modules.setdefault("heartbeat_runtime", package)
sys.modules["heartbeat_runtime.independent_oscillator"] = oscillator
```

The stub defines only `current_reference`. Because the file sorts early, every
later test in the same process that imports the real `heartbeat_runtime` gets
the stub instead and fails with

```
ImportError: cannot import name 'OSCILLATOR_PERIOD_MS' from
  'heartbeat_runtime.independent_oscillator' (unknown location)
```

`(unknown location)` is the `__path__ = []` showing through. This single write
accounts for **all 46** collection errors in a full-suite `.github` run; every
one of those files collects cleanly on its own. Fix: scope the injection with
`unittest.mock.patch.dict(sys.modules, ...)` or restore it in teardown.

---

## 5. Test-suite health as measured

| Repo | Result |
| --- | --- |
| StegOS | 1652 passed (1 file uncollectable for a container-missing `_cffi_backend`) |
| continuity-vault-kit | 621 passed, **9 failed**, 2 files uncollectable (C4) |
| `.github` | 527 of 604 test files pass in isolation; 69 fail, 8 error. A full-suite run additionally dies at collection with 46 `ImportError`s that do **not** occur per-file — root cause identified as C6. |

The 9 CVK failures break down as: 7 = C1; 1 = C2; 1 = a stale assertion in
`test_kv_storage_provider_adapter.py` that expects exactly
`["dropbox", "google-drive", "icloud-drive", "onedrive"]` where the registry now
returns `["device-local", "dropbox", "google-drive", "icloud-drive", "nas",
"onedrive", "removable-storage"]` — three adapters were added without updating
the test. That one is a test bug, not a code bug.

---

## 6. Out of scope

Two Site items read as unbuilt but belong to other lanes, not KV/SKAP:
`SITE_MIRROR_HANDOFF.md:240-241` (cryptographic canonical hash, gateway-origin
canonical events) and the `CACS_MIRROR_HANDOFF.md` projection items. They are
noted here only so they are not mistaken for KV blockers.

`docs/MY_KV_SERVICE_FEDERATION_CONTRACT.md` is `DESIGN CONTRACT /
IMPLEMENTATION AND AUTHENTIC PROVIDER EXECUTION PENDING` — genuinely unbuilt,
but it is the multi-account Mail/Calendar/Notes/Files federation layer, a
successor to the SKAP work rather than a prerequisite for it.

---

## 7. What finishing SKAP Vault + KV actually requires

In dependency order:

1. **Fix C3** (shared allow-listed secret scanner in CVK). Unblocks C1 and C2
   and removes the same latent failure from eight more modules.
2. **Fix C4** (one byte) and add a workflow that imports every `runtime/*.py`,
   so this class cannot recur silently.
3. **Build B1** (`StegVerseKVAccountObservationBridge` in Site), following the
   two existing write-bridge precedents.
4. **Build B3** (propagate the account-metadata profile into Site's generated
   connector; bind `populateSelectedAccountMetadata`).
5. **Build B2** (the `SKAP_ACCOUNT_METADATA_ADMIT` consumer in TVC) to the seven
   requirements already specified.
6. **Fix C5, C6** and the stale assertions, so CI actually gates the lane.
   C6 in particular means `.github`'s suite currently cannot run as a whole,
   which is why so much of this went unnoticed.
7. Only then does the owner-side runtime step (Category A) have a working path
   to execute against.

Steps 1–6 are code. Step 7 is not mine to do and cannot be substituted by
source, CI, or repository evidence.

---

## 8. Repository access required

All five repos below report `can_push: true` for this account. The blocker is
that this session has push scope only for `Randolph_Geneaology_Hub`; attaching
the others needs a permission grant.

| Repo | Needed for | Access |
| --- | --- | --- |
| `StegVerse-Labs/continuity-vault-kit` | C1, C2, C3, C4, stale adapter test | push |
| `StegVerse-Labs/Site` | B1, B3 | push |
| `StegVerse-Labs/TVC` | B2 | push |
| `StegVerse-Labs/.github` | C5, transport scripts, CI hygiene | push |
| `StegVerse-Labs/StegOS` | dispatcher extension for the new profile destination/operation (profile handoff item 4) | push |

`StegVerse-Labs/StegCore` is read-only reference (canonical `BOUNDARIES`); no
changes are owed there.

---

## 9. Relation to this repo

`docs/MYKV_SERVICE_DESIGN.md` §10 pauses the genealogy hub pending KV. This
survey does not change that. It does narrow it: the hub's storage question
depends on KV's persistence path working end to end, and §7 above is the
shortest route to that.
