"""The re-arm mechanism: anib_60007 (supplement.per) + anib_60009 secondary-build flow."""
import os

W = os.path.dirname(os.path.abspath(__file__))
out = []
for d in ("x1_drs", "aok_drs"):
    for f, lo, hi, title in ((60007, 310, 400, "60007 supplement secondary-build flow"),
                             (60009, 545, 620, "60009 secondary-build flow start")):
        p = os.path.join(d and W and d, "anib_%d.bin" % f)
        if not os.path.exists(p):
            out.append("missing " + p)
            continue
        rows = open(p, "rb").read().decode("latin-1").split("\n")
        out.append("=" * 70)
        out.append("%s  %s  (%d lines)  %s" % (d, os.path.basename(p), len(rows), title))
        for i in range(lo - 1, min(hi, len(rows))):
            out.append("   %5d| %s" % (i + 1, rows[i].rstrip()))
        out.append("")

out.append("=== all uses of '(goal secondary-build 0)' as a CONDITION (all files) ===")
for d in ("aok_drs", "x1_drs", "x1p1_drs"):
    p = os.path.join(W, d)
    if not os.path.isdir(p):
        continue
    for f in sorted(os.listdir(p)):
        t = open(os.path.join(p, f), "rb").read().decode("latin-1")
        for i, r in enumerate(t.split("\n")):
            if r.strip() == "(goal secondary-build 0)":
                out.append("   %s/%s %5d| %s" % (d, f, i + 1, r.rstrip()))

open(os.path.join(W, "dm_rearm_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_rearm_out.txt", len(out), "lines")
