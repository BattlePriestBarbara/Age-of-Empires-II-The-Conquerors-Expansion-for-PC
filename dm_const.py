"""Where are the DM constants (deathmatch-unit-max / unit-max / fifteen-percent-pop) defined?
   Plus: who else touches goal secondary-build?"""
import os
import re

W = os.path.dirname(os.path.abspath(__file__))
KEYS = ["secondary-build", "deathmatch-unit-max", "unit-max", "fifteen-percent-pop",
        "civ-dark-rush", "defconst", "set-difficulty-parameter", "population-headroom"]
out = []
for d in ("aok_drs", "x1_drs", "x1p1_drs"):
    p = os.path.join(W, d)
    if not os.path.isdir(p):
        continue
    out.append("#" * 70)
    out.append("DIR " + d)
    for f in sorted(os.listdir(p)):
        t = open(os.path.join(p, f), "rb").read().decode("latin-1")
        rows = t.split("\n")
        hits = {k: [i for i, r in enumerate(rows) if k in r] for k in KEYS}
        if not any(hits.values()):
            continue
        out.append("--- %s (%d lines)" % (f, len(rows)))
        for k in KEYS:
            if not hits[k]:
                continue
            out.append("   [%s] %d hits: lines %s" %
                       (k, len(hits[k]), ", ".join(str(i + 1) for i in hits[k][:25])))
            for i in hits[k][:8]:
                out.append("        %5d| %s" % (i + 1, rows[i].rstrip()))
    out.append("")

open(os.path.join(W, "dm_const_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_const_out.txt", len(out), "lines")
