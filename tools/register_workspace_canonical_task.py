#!/usr/bin/env python3
"""Register the StegVerse WorkSpace canonical task in StegVerse-Labs/.github.

This repository cannot push to `StegVerse-Labs/.github` — `add_repo` refuses any
repository whose name begins with `.`, and the git proxy will not inject a
credential for an unattached repository. So the registration is produced here,
validated against the registry's own checkers, and applied by a registry owner
who runs this script inside a `.github` checkout:

    python3 register_workspace_canonical_task.py --registry-root /path/to/.github

It is idempotent: re-running against an already-registered registry reports
ALREADY_REGISTERED and writes nothing.

What it writes (four surfaces, because the registry keeps a task in four places):

    data/canonical-task-registry.json          tasks[] row, generation bump
    data/canonical-task-records/<TID>.json     the canonical task record
    control/task-vectors/<TID>.json            the COSV source state vector
    control/task-vector-index.json             the index row + coverage counts

It mints no authority. `coordination_state` is PROPOSED, `checkout_state` is
UNCLAIMED, and `worker_claim` is the canonical projection required by
TASK_REGISTRY_CANONICAL_INVARIANTS.md when no authentic WorkerCoordinator
claim/fence has been observed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TASK_ID = "STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001"
OBSERVED_AT = "2026-09-27T09:15:00-05:00"

# ---------------------------------------------------------------------------
# COSV task.v1 vector, derived from management/COSV_PROFILE_V1.json#task
# symbol order LRUIVGOCMTBEAP, width 14. Every digit is justified in
# METRIC_EVIDENCE below; nothing here is chosen for convenience.
# ---------------------------------------------------------------------------
EXACT_METRICS = {
    "symbol_order": "LRUIVGOCMTBEAP",
    "lifecycle": "UNCLAIMED",              # L = 1
    "archive_ready": False,                # R = 0
    "unassigned_work": 5,                  # U = 5
    "chat_owned_implementation": 0,        # I = 0
    "chat_owned_validation": 0,            # V = 0
    "chat_owned_integration": 0,           # G = 0
    "chat_owned_observation": 0,           # O = 0
    "chat_owned_credentials": 0,           # C = 0
    "canonical_owner_installed": True,     # M = 1
    "thread_required": True,               # T = 1
    "blocker_count": 4,                    # B = 4
    "evidence_complete": False,            # E = 0
    "activated": False,                    # A = 0
    "propagated": False,                   # P = 0
}

LIFECYCLE_CODES = {
    "UNKNOWN": 0, "UNCLAIMED": 1, "CLAIMED_IMPLEMENTATION": 2,
    "CLAIMED_VALIDATION": 3, "CLAIMED_INTEGRATION": 4, "MACHINE_OWNED": 5,
    "BLOCKED": 6, "COMPLETE": 7, "SUPERSEDED": 8,
    "MERGED_INTO_CANONICAL_WORKSTREAM": 9,
}


def derive_vector(metrics: dict) -> str:
    """Compose the 14-symbol task.v1 vector from exact metrics.

    Ternary positions encode false=0 / true=1 / unknown=2. Quantity positions
    encode the count, saturating at 9 ("9_or_more").
    """

    def q(value: int) -> str:
        return str(min(int(value), 9))

    def t(value) -> str:
        return "2" if value is None else ("1" if value else "0")

    return "".join([
        str(LIFECYCLE_CODES[metrics["lifecycle"]]),   # L
        t(metrics["archive_ready"]),                  # R
        q(metrics["unassigned_work"]),                # U
        q(metrics["chat_owned_implementation"]),      # I
        q(metrics["chat_owned_validation"]),          # V
        q(metrics["chat_owned_integration"]),         # G
        q(metrics["chat_owned_observation"]),         # O
        q(metrics["chat_owned_credentials"]),         # C
        t(metrics["canonical_owner_installed"]),      # M
        t(metrics["thread_required"]),                # T
        q(metrics["blocker_count"]),                  # B
        t(metrics["evidence_complete"]),              # E
        t(metrics["activated"]),                      # A
        t(metrics["propagated"]),                     # P
    ])


VECTOR = derive_vector(EXACT_METRICS)

METRIC_EVIDENCE = {
    "lifecycle": (
        "UNCLAIMED. No authentic WorkerCoordinator claim or fence has been "
        "observed for WorkSpace, and this registration does not create one. "
        "coordination_state is PROPOSED."
    ),
    "archive_ready": (
        "False. No handoff projection, evidence package, or validation run "
        "exists for this task yet."
    ),
    "unassigned_work": (
        "5. The five properties in work_units below, none of which has an "
        "assigned owner: browser-storage root-of-truth removal, registration "
        "recovery on a device that never held one, receipt lineage survival "
        "across re-registration, a second registered platform, and the "
        "WorkSpace persistence request."
    ),
    "chat_owned_implementation": "0. No chat or session owns implementation for this task.",
    "chat_owned_validation": "0. No chat or session owns validation for this task.",
    "chat_owned_integration": "0. No chat or session owns integration for this task.",
    "chat_owned_observation": "0. No chat or session owns observation for this task.",
    "chat_owned_credentials": (
        "0. No chat or session holds credentials for this task. Credential "
        "authority remains TV/TVC and user verification remains KV/SKAP Vault."
    ),
    "canonical_owner_installed": (
        "True by virtue of this registration: the registry row is the canonical "
        "owner surface for WorkSpace, which previously had none. Before this "
        "task, WorkSpace existed only as the Site-local claim "
        "SITE-WORKSPACE-INTEROPERABILITY-001, whose task_id resolves nowhere in "
        "StegVerse-Labs/.github. A reviewer who reads canonical_owner_installed "
        "as requiring an installed runtime owner rather than an installed "
        "registry owner should set this to false and the vector to 10500000014000."
    ),
    "thread_required": (
        "True. The goal spans StegVerse-Labs/Site, StegVerse-Labs/"
        "continuity-vault-kit, StegVerse-Labs/.github and StegVerse-Labs/StegOS, "
        "and four of its decisions are registry-owner decisions rather than "
        "implementation steps."
    ),
    "blocker_count": (
        "4. The four registry-owner decisions recorded in blockers below. Each "
        "blocks implementation rather than merely informing it."
    ),
    "evidence_complete": "False. No predicate in expected_evidence_predicates is satisfied.",
    "activated": "False. No runtime activation is claimed or observed.",
    "propagated": "False. No downstream propagation has occurred.",
}

GOAL = (
    "Make the StegVerse WorkSpace the canonical browser representation of MyKV "
    "and Org KV, including capability functions bound to admitted operations, "
    "and the single governed input surface for sensitive material entering the "
    "SKAP Vault, such that WorkSpace state is derived entirely from admitted "
    "state transitions and remains exact and consistent for the same principal "
    "across any browser session, on any operating system, on any device. "
    "Preserve KV/SKAP Vault as the exclusive user verifier, Interlock/InTr as "
    "transition authority, TV/TVC as credential authority, Master Records as "
    "organization records and reconstruction, and the global invariant that eligible StegOS devices are "
    "interchangeable transport nodes with no physical-device identity gate. "
    "Create no second user verifier, no duplicate runtime, no duplicate KV "
    "authority, and no browser-local root of truth for user-visible state."
)

WORK_UNITS = [
    {
        "work_unit_id": "WU1-NO-BROWSER-LOCAL-ROOT-OF-TRUTH",
        "statement": (
            "No user-visible WorkSpace state may have its root of truth in "
            "script-writable browser storage. IndexedDB and localStorage may "
            "cache an admitted projection; they may not be its authority."
        ),
        "current_state": (
            "Violated. The Personal path's precondition is a node registration "
            "held in device-local IndexedDB, and the Organizational path reads "
            "its five Org-Emp-KV predicates from "
            "sessionStorage['stegverse.workspace.orgEmpGate'], which nothing "
            "writes."
        ),
        "assigned_owner": None,
    },
    {
        "work_unit_id": "WU2-REGISTRATION-RECOVERY-ON-A-NEW-DEVICE",
        "statement": (
            "A principal's node registration must be recoverable on a device "
            "that has never held one, without minting a new identity."
        ),
        "current_state": (
            "Absent. Site:assets/workspace-kv-bridge.js requires "
            "node.status().registered === true and otherwise fails closed with "
            "'Register this device before opening Personal Workspace KV "
            "context'. Without recovery, node_id is a physical-device identity "
            "gate in effect, which the global invariant prohibits."
        ),
        "assigned_owner": None,
    },
    {
        "work_unit_id": "WU3-RECEIPT-LINEAGE-SURVIVES-REREGISTRATION",
        "statement": (
            "Receipt lineage must survive re-registration, so that losing a "
            "device-local registration does not break reconstruction proofs "
            "anchored to the previous node_id."
        ),
        "current_state": (
            "Absent. stegverse-node-continuity-impl.js fails closed when "
            "registration and Receipt #1 disagree, and re-registration mints a "
            "new Receipt #1. Every lineage anchored to the prior node_id is "
            "then anchored to an identity the device no longer holds."
        ),
        "assigned_owner": None,
    },
    {
        "work_unit_id": "WU4-SECOND-REGISTERED-PLATFORM",
        "statement": (
            "At least one non-Apple platform must be a registered goal, so that "
            "'any operating system' is a property a task can fail to meet."
        ),
        "current_state": (
            "Absent. Six canonical tasks name Apple platforms; Android, Windows "
            "and Linux name zero between them. Site carries assets/stegos-apple/ "
            "and stegos-apple-credential.html with no equivalent for any other "
            "platform."
        ),
        "assigned_owner": None,
    },
    {
        "work_unit_id": "WU5-WORKSPACE-STORAGE-PERSISTENCE-REQUEST",
        "statement": (
            "The WorkSpace path must request storage persistence where the "
            "platform offers it, as a mitigation that does not discharge WU1."
        ),
        "current_state": (
            "Absent. The single navigator.storage.persist() call in Site is in "
            "assets/device-local-kv-installer.js, loaded only by "
            "device-kv-install.html and cloud-kv-peers.html. WorkSpace's script "
            "chain never reaches it. Persistence is advisory and may be refused, "
            "so this mitigates eviction without satisfying WU1."
        ),
        "assigned_owner": None,
    },
]

BLOCKERS = [
    {
        "dependency_id": "BLK1-CANONICAL-WORKSPACE-SURFACE-OWNER",
        "blocker_id": "BLK1-CANONICAL-WORKSPACE-SURFACE-OWNER",
        "statement": (
            "Which browser surface is the canonical representation of MyKV: "
            "Site:workspace.html or Site:my-kv.html? Both ship today, neither "
            "links to the other, and my-kv.html is far larger (612 lines plus 18 "
            "modules, 12 record classes) than workspace.html (43 lines plus 150, "
            "1 read-only record class)."
        ),
        "decision_owner": "REGISTRY_OWNER",
    },
    {
        "dependency_id": "BLK2-SKAP-INGRESS-CONSOLIDATION",
        "blocker_id": "BLK2-SKAP-INGRESS-CONSOLIDATION",
        "statement": (
            "Does sensitive ingress consolidate behind WorkSpace? At least four "
            "Site surfaces already accept it — my-kv.html, "
            "stegos-apple-credential.html, stegfin-trade.html and "
            "generic-login-test.html — each with its own ingress validation. "
            "Consolidation is security-relevant and cannot be assumed."
        ),
        "decision_owner": "REGISTRY_OWNER",
    },
    {
        "dependency_id": "BLK3-WORKSPACE-KV-STORE-WRITER",
        "blocker_id": "BLK3-WORKSPACE-KV-STORE-WRITER",
        "statement": (
            "Does the WorkSpace KV store keep a Google Drive writer? Today the "
            "only module permitted to write KnowledgeVault/_System/Workspace/** "
            "is continuity-vault-kit/runtime/personal_provider_binding.py, fed "
            "by a read-only GOOGLE_DRIVE broker result. A StegVerse-native "
            "writer does not exist, so KV_WORKSPACE_EMPTY is the structural "
            "default."
        ),
        "decision_owner": "REGISTRY_OWNER",
    },
    {
        "dependency_id": "BLK4-WORKSPACE-NAME-COLLISION",
        "blocker_id": "BLK4-WORKSPACE-NAME-COLLISION",
        "statement": (
            "Is the name collision with SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-"
            "RUNTIME-004 resolved by renaming? That task's WORKSPACE is Google "
            "Workspace, and it already writes the same KV path, so the collision "
            "is functional and not only nominal."
        ),
        "decision_owner": "REGISTRY_OWNER",
    },
]

EXPECTED_EVIDENCE_PREDICATES = [
    "WORKSPACE_PROJECTION_ROOT_OF_TRUTH_IS_NOT_BROWSER_LOCAL_STORAGE",
    "WORKSPACE_ORG_KV_PROJECTION_RETURNED_BY_CANONICAL_RUNTIME_NOT_BROWSER_STORAGE",
    "WORKSPACE_CAPABILITY_BOUND_TO_ADMITTED_OPERATION_WITH_INTERLOCK_INTR_TRANSITION",
    "WORKSPACE_SENSITIVE_INPUT_REACHES_SKAP_VAULT_THROUGH_GOVERNED_TRANSITION_ONLY",
    "WORKSPACE_STATE_DERIVED_ONLY_FROM_ADMITTED_STATE_TRANSITIONS",
    "WORKSPACE_PROJECTION_EXACT_ON_A_SECOND_BROWSER_SESSION_SAME_PRINCIPAL",
    "WORKSPACE_PROJECTION_EXACT_ON_A_DEVICE_THAT_NEVER_HELD_A_REGISTRATION",
    "WORKSPACE_PROJECTION_EXACT_ON_A_SECOND_OPERATING_SYSTEM",
    "RECEIPT_LINEAGE_RECONSTRUCTS_ACROSS_NODE_REREGISTRATION",
    "NO_SECONDARY_USER_VERIFIER_OUTSIDE_KV_SKAP_VAULT_OBSERVED",
    "NO_PHYSICAL_DEVICE_IDENTITY_GATE_OBSERVED",
    "CREDENTIAL_MATERIAL_PRESENT_FALSE_ON_EVERY_WORKSPACE_PROJECTION",
]

SOURCE_REFS = [
    "StegVerse-Labs/Site:workspace.html",
    "StegVerse-Labs/Site:assets/workspace.js",
    "StegVerse-Labs/Site:assets/workspace-kv-bridge.js",
    "StegVerse-Labs/Site:data/workspace/bootstrap.json",
    "StegVerse-Labs/Site:tests/workspace-kv-binding.test.cjs",
    "StegVerse-Labs/Site:assets/stegverse-node-continuity-impl.js",
    "StegVerse-Labs/Site:assets/device-local-kv-installer.js",
    "StegVerse-Labs/Site:data/session-work-claims.d/site-workspace-interoperability-20260831.json",
    "StegVerse-Labs/continuity-vault-kit:runtime/workspace_projection.py",
    "StegVerse-Labs/continuity-vault-kit:runtime/personal_provider_binding.py",
    "StegVerse-Labs/.github:data/task-registry-global-invariants.json",
    "StegVerse-Labs/.github:TASK_REGISTRY_CANONICAL_INVARIANTS.md",
    "StegVerse-Labs/.github:management/COSV_PROFILE_V1.json",
    "StegVerse-Labs/.github:data/reusable-browser-local-state-schema-migration-component-contract.json",
    "StegVerse-Labs/Randolph_Geneaology_Hub:docs/WORKSPACE_MYKV_SKAP_REGISTRY_REVIEW.md",
]

ADJACENT_TASK_REFS = [
    "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001",
    "KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001",
    "SS-KV-SKAP-SOCIAL-RELEASE-001",
    "MYKV-PERSONAL-DATA-BACKUP-001",
    "MYKV-NATIVE-IOS-PACKAGING-DISTRIBUTION-001",
    "TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001",
    "SDK-WORKSPACE-EXTCOLLAB-AUTHENTIC-RUNTIME-004",
]

# scripts/validate_canonical_work_coordination.py requires every
# blockers[].dependency_id to exist in dependencies[].dependency_id, and reads
# dependencies as objects. Each registry-owner decision is therefore represented
# once as a canonical dependency object and referenced by the blocker.
DEPENDENCIES = [
    {
        "dependency_id": blocker["dependency_id"],
        "dependency_kind": "HUMAN_DECISION",
        "decision_owner": blocker["decision_owner"],
        "statement": blocker["statement"],
        "resolved": False,
    }
    for blocker in BLOCKERS
] + [
    {
        "dependency_id": f"TASK-{task_id}",
        "dependency_kind": "CANONICAL_TASK",
        "task_id": task_id,
        "resolved": False,
    }
    for task_id in (
        "STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001",
        "KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001",
        "SS-KV-SKAP-SOCIAL-RELEASE-001",
        "MYKV-PERSONAL-DATA-BACKUP-001",
        "TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001",
    )
]

# Required on the registry row itself, not only on the record.
RUNTIME_REQUIREMENTS = {
    "capabilities": [
        "browser-kv-projection",
        "interlock-intr-governed-transition",
        "skap-vault-user-verification",
        "master-records-organization-record",
        "cross-platform-browser-runtime",
    ],
    "mutation_required": True,
    "deployment_required": True,
    "current_observation_required": True,
    "workercoordinator_claim_required_before_implementation": True,
    "second_operating_system_required_for_evidence_completion": True,
}

CANONICAL_SUBSTRATE_REVIEW_ORDER = [
    "STEG-BROWSER-RETAINED-RESIDENT-NODE",
    "STEGOS-CURRENT-DEVICE-NODE",
    "STEG-BROWSER-EPHEMERAL-LEASE",
    "SAME-DEVICE-SITE-SAFARI-SERVICE-WORKER",
    "ADMITTED-EPHEMERAL-STEGOS-NODE",
    "REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT",
]

# scripts/validate_task_registration_substrate_resolution.py treats any record
# carrying a runtime_requirements dict as runtime-capable and then requires this
# block. Every substrate is PENDING_EVIDENCE/EVIDENCE_REACHABILITY because no
# runtime observation of WorkSpace exists: nothing has been run against a live
# KV, browser or device, so no substrate can be shown suitable and none can be
# ruled out. The validator itself forbids promoting an evidence/reachability gap
# to UNSUITABLE, which is exactly this situation. Nothing is SELECTED and no
# external device is required, so the block mints no execution authority and is
# consistent with coordination_state PROPOSED / checkout_state UNCLAIMED.
EXECUTION_SUBSTRATE_RESOLUTION = {
    "schema": "stegverse.execution-substrate-resolution/v1",
    "authority_effect": "NONE",
    "second_user_operated_device_allowed": False,
    "external_device_required": False,
    "selected_substrate_id": None,
    "review_order": CANONICAL_SUBSTRATE_REVIEW_ORDER,
    "reviews": [
        {
            "substrate_id": substrate_id,
            "disposition": "PENDING_EVIDENCE",
            "limitation_class": "EVIDENCE_REACHABILITY",
            "evidence_refs": [],
        }
        for substrate_id in CANONICAL_SUBSTRATE_REVIEW_ORDER
    ],
}

NONCLAIMS = [
    "REGISTRATION_IS_COORDINATION_INTENT_ONLY_AND_GRANTS_NO_EXECUTION_AUTHORITY",
    "NO_WORKERCOORDINATOR_CLAIM_OR_FENCE_IS_ASSERTED_BY_THIS_REGISTRATION",
    "NO_RUNTIME_OBSERVATION_OF_WORKSPACE_IS_CLAIMED",
    "SEVEN_DAY_BROWSER_STORAGE_EVICTION_IS_CITED_PUBLISHED_PLATFORM_POLICY_NOT_AN_OBSERVED_FAILURE",
    "COSV_CANONICAL_OWNER_INSTALLED_REFERS_TO_THE_REGISTRY_OWNER_ROW_NOT_AN_INSTALLED_RUNTIME_OWNER",
    "SITE_DOES_NOT_BECOME_WORKSPACE_AUTHORITY",
]


def build_task() -> dict:
    return {
        "schema": "stegverse.canonical-task-record/v1",
        "task_id": TASK_ID,
        "correlation_id": TASK_ID,
        "root_correlation_id": TASK_ID,
        "parent_task_id": None,
        "goal": GOAL,
        "coordination_state": "PROPOSED",
        "checkout_state": "UNCLAIMED",
        "repository": "StegVerse-Labs/.github",
        "cosv_task_vector": VECTOR,
        "authority_model": {
            "work_intent_and_coordination": "TASK_REGISTRY",
            "execution_claim_and_fence": "WORKERCOORDINATOR",
            "governed_transition": "INTERLOCK_INTR",
            "user_verification": "KV_SKAP_VAULT",
            "credential_authority": "TV/TVC",
            "observed_reality_custody": "MASTER_RECORDS",
            "heartbeat": "OBSERVABILITY_ONLY",
            "github_runtime_authority": "NONE",
        },
        "authority_effect": "NONE_COORDINATION_REGISTRATION_ONLY",
        # Canonical projection required by TASK_REGISTRY_CANONICAL_INVARIANTS.md
        # when no authentic WorkerCoordinator claim/fence has been observed.
        "worker_claim": {
            "authority": "WORKERCOORDINATOR",
            "claim_ref": None,
            "fence_ref": None,
            "projection_only": True,
        },
        "governing_invariant_ref": "TASK-REGISTRY-KV-SKAP-VERIFIER-NODE-INVARIANT-001",
        "device_interchangeability_enforced": True,
        "physical_device_identity_gate": "NONE_PROHIBITED",
        "targets": {
            "organizations": ["StegVerse-Labs"],
            "repositories": [
                "StegVerse-Labs/Site",
                "StegVerse-Labs/continuity-vault-kit",
                "StegVerse-Labs/StegOS",
                "StegVerse-Labs/.github",
            ],
            "components": [
                "workspace-personal-kv-projection",
                "workspace-org-kv-projection",
                "workspace-capability-admission",
                "workspace-skap-ingress",
                "workspace-state-transition-model",
                "node-registration-portability",
                "receipt-lineage-continuity",
                "cross-platform-browser-runtime",
            ],
        },
        "work_units": WORK_UNITS,
        "blockers": BLOCKERS,
        "dependencies": DEPENDENCIES,
        "runtime_requirements": RUNTIME_REQUIREMENTS,
        "execution_substrate_resolution": EXECUTION_SUBSTRATE_RESOLUTION,
        "adjacent_task_refs": ADJACENT_TASK_REFS,
        "expected_evidence_predicates": EXPECTED_EVIDENCE_PREDICATES,
        "source_refs": SOURCE_REFS,
        "existing_evidence_refs": [
            "StegVerse-Labs/Randolph_Geneaology_Hub:pull/17",
            "StegVerse-Labs/Randolph_Geneaology_Hub:pull/18",
        ],
        "allowed_next_transitions": [
            "PROPOSED_TO_ACTIVE_ON_REGISTRY_OWNER_DECISION_OF_ALL_FOUR_BLOCKERS",
            "PROPOSED_TO_SUPERSEDED_IF_MERGED_INTO_AN_EXISTING_OWNER",
        ],
        "completion": {
            "state": "NOT_STARTED",
            "evidence_complete": False,
            "runtime_observed": False,
        },
        "nonclaims": NONCLAIMS,
        "registration": {
            "registered_by": "StegVerse-Labs/Randolph_Geneaology_Hub session",
            "registered_at": OBSERVED_AT,
            "basis": "docs/WORKSPACE_MYKV_SKAP_REGISTRY_REVIEW.md",
            "supersedes_site_local_claim": "SITE-WORKSPACE-INTEROPERABILITY-001",
            "site_local_claim_note": (
                "The Site claim remains the Site-side implementation claim. This "
                "task is the canonical coordination owner the claim's task_id "
                "never resolved to, and its next_task_after_release names this "
                "task's WU1 Org-KV binding."
            ),
        },
    }


def build_record() -> dict:
    record = build_task()
    record["handoff_projection_refs"] = []
    return record


def build_vector_file() -> dict:
    return {
        "identity": f"StegVerse-Labs/.github:task:{TASK_ID}",
        "profile": "task.v1",
        "level": "task",
        "vector": VECTOR,
        "evidence_refs": [
            f"data/canonical-task-records/{TASK_ID}.json",
            "StegVerse-Labs/Randolph_Geneaology_Hub:docs/WORKSPACE_MYKV_SKAP_REGISTRY_REVIEW.md",
            "StegVerse-Labs/Randolph_Geneaology_Hub:pull/17",
            "StegVerse-Labs/Randolph_Geneaology_Hub:pull/18",
        ],
        "observed_at": OBSERVED_AT,
        "exact_metrics": EXACT_METRICS,
        "metric_evidence": METRIC_EVIDENCE,
        "authority_effect": "NONE",
    }


def build_index_row() -> dict:
    return {
        "task_id": TASK_ID,
        "repository": "StegVerse-Labs/.github",
        "registry_ref": "control/worker-registry.json",
        "source_state_vector_ref": f"control/task-vectors/{TASK_ID}.json",
        "vector": VECTOR,
        "vector_state": "EMITTED",
        "authority_effect": "NONE",
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def apply(root: Path) -> str:
    registry_path = root / "data/canonical-task-registry.json"
    index_path = root / "control/task-vector-index.json"
    for required in (registry_path, index_path):
        if not required.is_file():
            raise SystemExit(f"not a .github checkout: missing {required}")

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if any(t.get("task_id") == TASK_ID for t in registry["tasks"]):
        return "ALREADY_REGISTERED"

    registry["tasks"].append(build_task())
    registry["generation"] = int(registry["generation"]) + 1
    _write_json(registry_path, registry)

    _write_json(root / f"data/canonical-task-records/{TASK_ID}.json", build_record())
    _write_json(root / f"control/task-vectors/{TASK_ID}.json", build_vector_file())

    index = json.loads(index_path.read_text(encoding="utf-8"))
    index["tasks"].append(build_index_row())
    coverage = index.setdefault("coverage", {})
    for key in ("indexed_vectorized_tasks", "local_cosv_record_tasks"):
        if key in coverage:
            coverage[key] = int(coverage[key]) + 1
    _write_json(index_path, index)

    return f"REGISTERED {TASK_ID} vector={VECTOR} generation={registry['generation']}"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry-root", type=Path, required=True,
                        help="path to a StegVerse-Labs/.github checkout")
    parser.add_argument("--print-only", action="store_true",
                        help="print the four artifacts without writing")
    args = parser.parse_args(argv)

    if args.print_only:
        print(json.dumps({
            "registry_task": build_task(),
            "record": build_record(),
            "vector_file": build_vector_file(),
            "index_row": build_index_row(),
        }, indent=2))
        return 0

    print(apply(args.registry_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
