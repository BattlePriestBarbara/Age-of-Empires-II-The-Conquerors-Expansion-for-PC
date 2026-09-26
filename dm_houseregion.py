"""Dump the house/difficulty region of both DM variants + all preprocessor lines after 1600."""
import os

W = os.path.dirname(os.path.abspath(__file__))
out = []
for d, lo, hi in (("x1_drs", 1655, 1745), ("aok_drs", 1240, 1330)):
    p = os.path.join(W, d, "anib_60002.bin")
    t = open(p, "rb").read().decode("latin-1")
    rows = t.split("\n")
    out.append("=" * 70)
    out.append("%s  (%d lines)" % (d, len(rows)))
    out.append("--- preprocessor lines with line number >= %d ---" % 1600)
    for i, r in enumerate(rows):
        if r.startswith("#"):
            out.append("   %5d| %s" % (i + 1, r.rstrip()))
    out.append("--- region %d..%d ---" % (lo, hi))
    for i in range(lo - 1, min(hi, len(rows))):
        out.append("   %5d| %s" % (i + 1, rows[i].rstrip()))
    out.append("")

open(os.path.join(W, "dm_houseregion_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_houseregion_out.txt", len(out), "lines")
