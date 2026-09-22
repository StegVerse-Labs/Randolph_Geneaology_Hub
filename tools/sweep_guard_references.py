#!/usr/bin/env python3
import re, json
from pathlib import Path
REPOS = ["site","stegos","tvc","continuity-vault-kit","stegverse-labs/.github",
         "stegfin-governance","stegverse-sdk","Randolph_Geneaology_Hub"]
# directory-level runs that sweep a whole tree
BULK = re.compile(r'pytest[^\n|;&]*\s(tests?/?\S*)|unittest\s+discover|pytest\s+-q\s*$|pytest\s*$', re.M)

print(f"{'repo':<26} {'guards':>7} {'ref':>6} {'bulk':>6} {'unref':>7} {'%unref':>7}")
print("-"*66)
tot_g=tot_u=0; detail={}
for name in REPOS:
    root=Path("/home/user")/name
    if not root.is_dir(): continue
    wfs=[]
    for d in (root/".github"/"workflows", root/"workflows"):
        if d.is_dir(): wfs += list(d.glob("*.y*ml"))
    if not wfs: continue
    wf="\n".join(f.read_text(encoding="utf-8",errors="replace") for f in wfs)
    bulk_dirs=set()
    for m in BULK.finditer(wf):
        g=m.group(1)
        if g: bulk_dirs.add(g.rstrip('/').split('/')[0])
        else: bulk_dirs.add("tests")
    guards=[]
    for pat in ("tests/**/*.py","test/**/*.py","scripts/check_*.py","scripts/validate_*.py","tools/test_*.py"):
        guards+=[p for p in root.glob(pat) if p.is_file() and "__pycache__" not in str(p)]
    guards=sorted(set(guards))
    ref=bulk=unref=0; un=[]
    for g in guards:
        rel=g.relative_to(root).as_posix(); stem=g.stem; mod=rel[:-3].replace("/",".")
        top=rel.split("/")[0]
        if rel in wf or stem in wf or mod in wf: ref+=1
        elif top in bulk_dirs: bulk+=1
        else: unref+=1; un.append(rel)
    if not guards: continue
    print(f"{name:<26} {len(guards):>7} {ref:>6} {bulk:>6} {unref:>7} {100.0*unref/len(guards):>6.0f}%")
    tot_g+=len(guards); tot_u+=unref; detail[name]=un
print("-"*66)
print(f"{'TOTAL':<26} {tot_g:>7} {'':>6} {'':>6} {tot_u:>7} {100.0*tot_u/max(tot_g,1):>6.0f}%")
Path("/tmp/unreferenced.json").write_text(json.dumps(detail,indent=1))
