#!/usr/bin/env python3
"""Re-run the SDK evaluator governance-posture runtime-proof determination.

`SDK-EVALUATOR-GOVERNANCE-POSTURE-RUNTIME-PROOF-001` is gated on the predicate
`EXACT_EVALUATOR_MANIFEST_MATERIALIZED_ON_ADMITTED_CANONICAL_RUNTIME_SUBSTRATE`.
Five review sections in its handoff searched evidence projections for a recorded
manifest hash, found nothing, and correctly declined to infer non-occurrence.

None of them asked the separable question this script answers: what does the
chain do when it is actually invoked with the canonical source roots present?
That is source reachability, not evidence absence, and it is mechanical.

Nothing here executes a governed transition, submits to Master Records, reaches
the network, or writes into any repository. It grants no authority and proves no
runtime materialization: this host is not an admitted canonical substrate.

Exit 0 when every check resolves, 3 when a check finds drift, 2 when a required
source root is missing.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
from pathlib import Path

RECORDED_MANIFEST_SHA256 = "1f2b204fc55a22fe0ba533a1825d2bc11a8a1427d70fa8191776c71f4c323bc3"
RECORDED_TRANSITION_SHA256 = "3d06812c7d1c1967cdded761c1245db4cc4587b275c5944b6de89bb0ac67909b"
RUNTIME_MANIFEST_LOCATOR = "runtime-state/sdk-evaluator-governance-posture/manifest.json"
STEGOS_RESOLVER_REL = "stegos/intr_security_posture_resolution.py"
SDK_RESOLVER_FIXTURE_REL = "tests/fixtures/stegos_intr_security_posture_resolution_84ddc96e.py"

findings: list[str] = []


def report(name: str, ok: bool, detail: str) -> bool:
    print(f"[{'ok  ' if ok else 'DRIFT'}] {name}: {detail}")
    if not ok:
        findings.append(f"{name}: {detail}")
    return ok


def body_without_docstring(source: str) -> str:
    """AST of a module with its own docstring removed, so provenance headers do not count as drift."""
    tree = ast.parse(source)
    if (tree.body and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)):
        tree.body = tree.body[1:]
    return ast.dump(tree)


def check_pinned_resolver(sdk: Path, stegos: Path) -> None:
    """The SDK cross-repo test binds to a byte snapshot of a module another repository owns."""
    fixture = sdk / SDK_RESOLVER_FIXTURE_REL
    live = stegos / STEGOS_RESOLVER_REL
    if not fixture.is_file() or not live.is_file():
        report("pinned StegOS resolver", False, f"missing {fixture if not fixture.is_file() else live}")
        return
    same = body_without_docstring(fixture.read_text()) == body_without_docstring(live.read_text())
    report("pinned StegOS resolver", same,
           "snapshot matches live StegOS module (docstring aside)" if same
           else "snapshot has drifted from the live StegOS module; the cross-repo test no longer "
                "proves anything about the resolver that runs")


def check_live_posture_binding(sdk: Path, stegos: Path) -> None:
    """Build an evaluator manifest with the SDK's own builder and bind it against the live resolver."""
    code = r"""
import sys, json, hashlib
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2])
from stegos.intr_security_posture_resolution import resolve_task_security_posture
from stegverse.evaluator_manifest_builder import build_evaluator_governance_manifest
from stegverse.security_posture_request import build_security_posture_request
from stegverse.governance_ingress_runtime import external_manifest_to_public_request
from stegverse.intr_posture_runtime_bridge import resolve_manifest_posture
from tests.test_intr_posture_runtime_bridge import governance_request
m = build_evaluator_governance_manifest(
    data={"class": "evaluator.fixture.v1", "observation": "neutral"},
    source_framework="IndependentEvaluator", source_output_id="case-001",
    governance_request=governance_request(),
    evaluation_declaration={"schema": "evaluator.preregistration.v1", "protocol_ref": "fixed-before-run"},
    security_posture_request=build_security_posture_request(
        task_id="EVAL-CROSSREPO-1", selected_tier="HIGHEST", selection_present=True,
        organization_minimum_tier="SECURE"),
    created_at="2026-09-10T19:00:00Z")
canonical = json.dumps(m, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
b = resolve_manifest_posture(manifest=m, transition_request=external_manifest_to_public_request(m),
                             resolver=resolve_task_security_posture, observed_at="2026-09-10T19:00:00Z")
print(json.dumps({
    "manifest_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
    "resolution_authority": b["resolution"]["resolution_authority"],
    "tier": b["resolution"]["effective_posture"]["tier"],
    "transition_request_sha256": b["transition_request_sha256"],
}))
"""
    proc = subprocess.run([sys.executable, "-c", code, str(stegos), str(sdk)],
                          capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        report("live InTr posture binding", False,
               f"chain did not reach a posture binding: {proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else 'no output'}")
        return
    out = json.loads(proc.stdout.strip().splitlines()[-1])
    report("live InTr posture binding", out["resolution_authority"] == "INTERLOCK_INTR",
           f"resolution_authority={out['resolution_authority']} tier={out['tier']} "
           f"over a manifest the SDK builder produced here")
    print(f"        built manifest sha256    : {out['manifest_sha256']}")
    print(f"        transition_request_sha256: {out['transition_request_sha256']}")


def declared_provenance(sdk: Path, module: str | None) -> str:
    """Report where SDK source says a required runtime package comes from, if it says at all."""
    if not module:
        return "no module name available"
    slug = module.replace("_", "-")
    proc = subprocess.run(["grep", "-rhoE", rf"[A-Za-z0-9._-]+/{slug}(@[0-9a-f]{{7,40}})?",
                           str(sdk), "--include=*.py", "--include=*.md"],
                          capture_output=True, text=True)
    seen = sorted({line.strip() for line in proc.stdout.splitlines() if "/" in line})
    if not seen:
        return "undeclared in SDK source"
    pinned = sorted(x for x in seen if "@" in x)
    declared = (pinned or seen)[0]
    return f"{declared}, declared in source but absent from pyproject dependencies"


def check_sovereign_validation_gap(sdk: Path, stegos: Path) -> None:
    """Name the package whose absence produces FAIL_CLOSED_MISSING_CANONICAL_RUNTIME_PACKAGES."""
    code = r"""
import sys, json
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2])
from stegverse import sovereign_validation_runtime as s
try:
    s._components()
    print(json.dumps({"reached": True}))
except Exception as exc:
    cause = exc.__cause__ or exc.__context__
    print(json.dumps({"reached": False, "error": type(exc).__name__,
                      "missing_module": getattr(cause, "name", None),
                      "message": str(exc)}))
"""
    proc = subprocess.run([sys.executable, "-c", code, str(stegos), str(sdk)],
                          capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        report("sovereign validation components", False, f"probe failed: {proc.stderr.strip()[-200:]}")
        return
    out = json.loads(proc.stdout.strip().splitlines()[-1])
    if out.get("reached"):
        report("sovereign validation components", True,
               "canonical packages resolve on this host; the fail-closed no longer reproduces")
        return
    missing = out.get("missing_module")
    report("sovereign validation components", False,
           f"fail-closed reproduces on the missing package '{missing}' — {out.get('message')} "
           f"[declared provenance: {declared_provenance(sdk, missing)}]")


def check_locator_has_a_producer(sdk: Path, github_repo: Path | None) -> None:
    """The resident consumer requires an already-materialized manifest at a fixed locator."""
    roots = [p for p in (sdk, github_repo) if p is not None and p.is_dir()]
    hits: list[str] = []
    for root in roots:
        proc = subprocess.run(["grep", "-rl", RUNTIME_MANIFEST_LOCATOR, str(root),
                               "--exclude-dir=.git", "--exclude-dir=__pycache__"],
                              capture_output=True, text=True)
        hits.extend(line for line in proc.stdout.splitlines() if line.strip())
    executable = [h for h in hits if Path(h).suffix in {".py", ".sh", ".yml", ".yaml"}]
    production = [h for h in executable if "test" not in Path(h).name]
    report("runtime manifest locator", bool(production),
           f"materialized by {len(production)} production source file(s)"
           if production else
           f"{len(hits)} reference(s); the only executable one(s) are tests "
           f"({', '.join(Path(h).name for h in executable) or 'none'}). The resident consumer "
           f"requires {RUNTIME_MANIFEST_LOCATOR} to already exist and no production source "
           f"materializes it")


def check_recorded_hash_has_a_producer(roots: list[Path]) -> None:
    """The recorded evidence hashes gate progression; check whether source can produce them."""
    for label, digest in (("manifest_sha256", RECORDED_MANIFEST_SHA256),
                          ("transition_request_sha256", RECORDED_TRANSITION_SHA256)):
        hits: list[str] = []
        for root in roots:
            proc = subprocess.run(["grep", "-rl", digest, str(root),
                                   "--exclude-dir=.git", "--exclude-dir=__pycache__"],
                                  capture_output=True, text=True)
            hits.extend(line for line in proc.stdout.splitlines() if line.strip())
        producers = [h for h in hits if Path(h).suffix in {".py", ".sh", ".yml", ".yaml"}]
        record_only = [h for h in hits if Path(h).suffix in {".json", ".md"}]
        report(f"recorded {label}", bool(producers),
               f"produced by {len(producers)} source file(s)" if producers else
               f"appears only in {len(record_only)} record(s) and is produced by no source; "
               f"the exact manifest it names cannot be rebuilt or verified by anyone")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sdk-root", type=Path, default=Path(os.environ.get("STEGVERSE_SDK_SOURCE_ROOT", "/home/user/stegverse-sdk")))
    ap.add_argument("--stegos-root", type=Path, default=Path(os.environ.get("STEGVERSE_STEGOS_ROOT", "/home/user/stegos")))
    ap.add_argument("--github-root", type=Path, default=Path(os.environ.get("STEGVERSE_GITHUB_SOURCE_ROOT", "/home/user/stegverse-labs/.github")))
    args = ap.parse_args()

    for label, root in (("SDK", args.sdk_root), ("StegOS", args.stegos_root)):
        if not root.is_dir():
            print(f"{label} source root not present: {root}", file=sys.stderr)
            return 2

    github_root = args.github_root if args.github_root.is_dir() else None
    roots = [args.sdk_root] + ([github_root] if github_root else [])

    print(f"SDK    : {args.sdk_root}")
    print(f"StegOS : {args.stegos_root}")
    print(f".github: {github_root or 'not present (locator/hash checks cover the SDK only)'}\n")

    check_pinned_resolver(args.sdk_root, args.stegos_root)
    check_live_posture_binding(args.sdk_root, args.stegos_root)
    check_sovereign_validation_gap(args.sdk_root, args.stegos_root)
    check_locator_has_a_producer(args.sdk_root, github_root)
    check_recorded_hash_has_a_producer(roots)

    print()
    if findings:
        print(f"{len(findings)} unresolved:")
        for f in findings:
            print(f"  - {f}")
        return 3
    print("every check resolved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
