"""Tight report: every (cc-add-resource ...) use across all unpacked DRS + its guard context."""
import os

W = os.path.dirname(os.path.abspath(__file__))
out = []
for d in ("aok_drs", "x1_drs", "x1p1_drs"):
    p = os.path.join(W, d)
    if not os.path.isdir(p):
        continue
    out.append("=" * 70)
    out.append("DIR " + d)
    for f in sorted(os.listdir(p)):
        fp = os.path.join(p, f)
        t = open(fp, "rb").read().decode("latin-1")
        rows = t.split("\n")
        hits = [i for i, r in enumerate(rows) if "cc-add-resource" in r]
        if not hits:
            continue
        out.append("--- %s : %d hits (%d lines)" % (f, len(hits), len(rows)))
        # show first 3 with full rule context
        for i in hits[:3]:
            s = i
            while s > 0 and "(defrule" not in rows[s]:
                s -= 1
            out.append("   rule at line %d:" % (s + 1))
            for j in range(s, min(i + 3, len(rows))):
                out.append("      %5d|%s" % (j + 1, rows[j].rstrip()))
        if len(hits) > 3:
            out.append("   ... and %d more hits" % (len(hits) - 3))
        out.append("")

open(os.path.join(W, "dm_cheat2_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_cheat2_out.txt", len(out), "lines")
