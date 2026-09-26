"""Exact shipped usage of resource cheats / cheat actions, with context."""
import os

W = os.path.dirname(os.path.abspath(__file__))
PATS = ["cc-add-resource", "cc-add",
        "set-strategic-number sn-cap-civilian-builders",
        "deathmatch-unit-max", "unit-max", "hd-dm", "cheat"]
out = []
for d in ("aok_drs", "x1_drs", "x1p1_drs"):
    p = os.path.join(W, d)
    if not os.path.isdir(p):
        continue
    out.append("=" * 70)
    out.append("DIR " + d)
    for f in sorted(os.listdir(p)):
        t = open(os.path.join(p, f), "rb").read().decode("latin-1")
        rows = t.split("\n")
        for i, r in enumerate(rows):
            if any(k in r for k in PATS):
                lo = max(0, i - 4)
                hi = min(len(rows), i + 3)
                out.append("--- %s line %d" % (f, i + 1))
                for j in range(lo, hi):
                    out.append("   %5d|%s" % (j + 1, rows[j].rstrip()))
                out.append("")

open(os.path.join(W, "dm_cheat_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_cheat_out.txt", len(out), "lines")
