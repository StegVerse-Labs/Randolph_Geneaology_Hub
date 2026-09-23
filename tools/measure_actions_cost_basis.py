#!/usr/bin/env python3
"""Measure the GitHub Actions cost basis for StegVerse from retained run evidence.

The existing corpus in StegVerse-Labs/.github/cost-basis/ is estimates, and says so:
44 of its 61 records carry zero empirical samples and none carries more than one. The
canonical free-tier task requires COSTS_MEASURED_NOT_ESTIMATED, so this measures instead.

Two facts decide an Actions bill, and neither is run duration:

  visibility  Actions minutes on a public repository are free. A public repository with
              forty thousand runs bills nothing; a private one with a tenth of that bills
              for all of them. Attributing cost by run count without visibility inverts
              the answer.
  rounding    Private-repository runs bill by the minute, rounded UP, per run. A sixteen
              second run bills a full minute. Where the median run is well under a minute
              the bill is set by how many times a workflow runs, not how long it takes.

Runner class multiplies the rounded minutes: Linux x1, Windows x2, macOS x10.

This reads public run metadata and local workflow files. It runs no workflow, spends
nothing, and grants no authority. Figures are measured observations, not budgets,
forecasts, commitments or prices.

Exit 0 when every requested repository was measured, 2 when none could be read.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.github.com"
SCHEMA = "stegverse.measured-actions-cost-basis/v1"

# GitHub's published per-minute multipliers for private-repository runners.
MULTIPLIER = {"linux": 1, "windows": 2, "macos": 10}
DEFAULT_REPOS = [
    "StegVerse-Labs/Site",
    "StegVerse-Labs/StegOS",
    "StegVerse-Labs/TVC",
    "StegVerse-Labs/continuity-vault-kit",
    "StegVerse-Labs/stegfin-governance",
    "StegVerse-Labs/Randolph_Geneaology_Hub",
]


def api(path: str) -> dict:
    req = urllib.request.Request(
        f"{API}{path}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "stegverse-cost-basis"},
    )
    with urllib.request.urlopen(req, timeout=30) as fh:
        return json.load(fh)


def runner_class(label: str) -> str:
    low = label.lower()
    if "macos" in low:
        return "macos"
    if "windows" in low:
        return "windows"
    return "linux"


def workflow_runner_map(checkout: Path) -> dict[str, str]:
    """Map each workflow file path to its runner class, read from the local checkout.

    Asking the API for each run's jobs would cost a request per run for a value the
    workflow file already states. Absent a checkout, every run is assumed Linux, which
    understates a macOS bill tenfold -- so the summary reports whether a map was used.
    """
    mapping: dict[str, str] = {}
    wf_dir = checkout / ".github" / "workflows"
    if not wf_dir.is_dir():
        return mapping
    for path in sorted(wf_dir.glob("*.y*ml")):
        cls = "linux"
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if stripped.startswith("runs-on:"):
                cls = runner_class(stripped.split("runs-on:", 1)[1])
                if cls != "linux":
                    break
        mapping[f".github/workflows/{path.name}"] = cls
    return mapping


def duration_seconds(run: dict) -> float | None:
    started, updated = run.get("run_started_at"), run.get("updated_at")
    if not started or not updated:
        return None
    try:
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        sec = time.mktime(time.strptime(updated, fmt)) - time.mktime(time.strptime(started, fmt))
    except (ValueError, OverflowError):
        return None
    # A negative or day-long span is a clock or retention artefact, not a run.
    return sec if 0 <= sec < 86400 else None


def measure(repo: str, sample: int, checkout: Path | None) -> dict | None:
    try:
        meta = api(f"/repos/{repo}")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        print(f"  {repo}: unreadable ({exc})", file=sys.stderr)
        return None

    private = bool(meta.get("private"))
    runner_map = workflow_runner_map(checkout) if checkout and checkout.is_dir() else {}

    runs: list[dict] = []
    total_runs = 0
    page = 1
    while len(runs) < sample:
        try:
            data = api(f"/repos/{repo}/actions/runs?per_page=100&page={page}")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            print(f"  {repo}: run page {page} unreadable ({exc})", file=sys.stderr)
            break
        total_runs = data.get("total_count", total_runs)
        batch = data.get("workflow_runs", [])
        if not batch:
            break
        runs.extend(batch)
        page += 1

    durations: list[float] = []
    billed_units = 0  # rounded minutes x runner multiplier
    actual_seconds = 0.0
    by_class: dict[str, int] = {}
    unmapped = 0

    for run in runs[:sample]:
        sec = duration_seconds(run)
        if sec is None:
            continue
        durations.append(sec)
        actual_seconds += sec
        path = run.get("path") or ""
        cls = runner_map.get(path)
        if cls is None:
            cls = "linux"
            unmapped += 1
        by_class[cls] = by_class.get(cls, 0) + 1
        billed_units += math.ceil(sec / 60) * MULTIPLIER[cls]

    if not durations:
        print(f"  {repo}: no measurable runs", file=sys.stderr)
        return None

    sampled = len(durations)
    actual_minutes = actual_seconds / 60
    # Public repositories are not billed for standard runners at all.
    billed = billed_units if private else 0
    overhead = (1 - actual_minutes / billed_units) if billed_units else 0.0

    return {
        "repository": repo,
        "visibility": "private" if private else "public",
        "billed_for_actions_minutes": private,
        "total_runs_reported": total_runs,
        "sampled_runs": sampled,
        "runner_classes_observed": dict(sorted(by_class.items())),
        "runs_without_runner_mapping": unmapped,
        "runner_map_available": bool(runner_map),
        "duration_seconds": {
            "median": round(statistics.median(durations), 1),
            "mean": round(statistics.fmean(durations), 1),
            "max": round(max(durations), 1),
        },
        "sample_actual_minutes": round(actual_minutes, 1),
        "sample_billable_units": billed_units,
        "sample_billed_units": billed,
        "per_minute_rounding_overhead": round(overhead, 3),
        "measurement_basis": "RETAINED_WORKFLOW_RUN_METADATA",
        "authority_effect": "NONE_COST_BASIS_ONLY",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", action="append", dest="repos", help="owner/name; repeatable")
    ap.add_argument("--sample", type=int, default=100, help="runs to sample per repository")
    ap.add_argument("--checkout-root", type=Path, default=Path("/home/user"),
                    help="directory holding local clones, for runner-class mapping")
    ap.add_argument("--out", type=Path, help="write the measured record here")
    args = ap.parse_args()

    repos = args.repos or DEFAULT_REPOS
    measured = []
    for repo in repos:
        name = repo.split("/")[-1]
        checkout = None
        for candidate in (name, name.lower()):
            if (args.checkout_root / candidate).is_dir():
                checkout = args.checkout_root / candidate
                break
        row = measure(repo, args.sample, checkout)
        if row:
            measured.append(row)

    if not measured:
        print("no repository could be measured", file=sys.stderr)
        return 2

    billed = [r for r in measured if r["billed_for_actions_minutes"]]
    free = [r for r in measured if not r["billed_for_actions_minutes"]]
    record = {
        "schema": SCHEMA,
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sample_per_repository": args.sample,
        "repositories": measured,
        "summary": {
            "repositories_measured": len(measured),
            "billed_repositories": sorted(r["repository"] for r in billed),
            "free_repositories": sorted(r["repository"] for r in free),
            "runs_reported_in_billed_repositories": sum(r["total_runs_reported"] for r in billed),
            "runs_reported_in_free_repositories": sum(r["total_runs_reported"] for r in free),
        },
        "not_claimed": [
            "No dollar amount is asserted; per-minute rates and plan allowances are account state, not run evidence.",
            "Sampled runs are the most recent, not a uniform sample of all history.",
            "Durations are wall-clock from run metadata and include queueing.",
            "This measures GitHub Actions only, not provider, sandbox, Node, governance or custody cost.",
        ],
        "authority_effect": "NONE_COST_BASIS_ONLY",
    }

    print(f"{'repository':42} {'vis':8} {'runs':>7} {'med':>6} {'billable':>9} {'actual':>8} {'rounding':>9}")
    print("-" * 94)
    for r in measured:
        print(f"{r['repository']:42} {r['visibility']:8} {r['total_runs_reported']:>7} "
              f"{r['duration_seconds']['median']:>5.0f}s {r['sample_billable_units']:>9} "
              f"{r['sample_actual_minutes']:>7.1f}m {r['per_minute_rounding_overhead']*100:>8.1f}%")
    print(f"\nbilled repositories : {', '.join(record['summary']['billed_repositories']) or 'none'}")
    print(f"free repositories   : {', '.join(record['summary']['free_repositories']) or 'none'}")
    print(f"runs in billed repos: {record['summary']['runs_reported_in_billed_repositories']}")
    print(f"runs in free repos  : {record['summary']['runs_reported_in_free_repositories']}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
