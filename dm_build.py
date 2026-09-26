"""All (build X) rules in the DM scripts: what is gated on what?"""
import os
import re

W = os.path.dirname(os.path.abspath(__file__))
out = []
for d in ("x1_drs", "aok_drs"):
    p = os.path.join(W, d, "anib_60002.bin")
    t = open(p, "rb").read().decode("latin-1")
    rows = t.split("\n")
    out.append("=" * 70)
    out.append("%s/anib_60002.bin : %d lines" % (d, len(rows)))
    # track preprocessor context per line
    depth = []
    ctx = {}
    cur = []
    for i, r in enumerate(rows):
        s = r.strip()
        if s.startswith("#load-if-defined") or s.startswith("#load-if-not-defined"):
            cur.append(s.split()[1] if len(s.split()) > 1 else s)
        elif s.startswith("#end-if"):
            if cur:
                cur.pop()
        ctx[i] = list(cur)
    for i, r in enumerate(rows):
        m = re.search(r"\(build\s+([a-zA-Z0-9_-]+)\)", r)
        if not m:
            continue
        s = i
        while s > 0 and "(defrule" not in rows[s]:
            s -= 1
        conds = [rows[j].strip() for j in range(s + 1, i) if rows[j].strip() and rows[j].strip() != "=>"]
        also = [rows[j].strip() for j in range(i + 1, min(i + 6, len(rows)))
                if rows[j].strip() and rows[j].strip() != ")" and not rows[j].strip().startswith("(defrule")]
        out.append("%6d| %-14s pp=%s" % (i + 1, m.group(1), ",".join(ctx[i]) or "-"))
        out.append("        conds: %s" % " ".join(conds))
        if also:
            out.append("        acts+: %s" % " | ".join(also))
    out.append("")
    out.append("--- headroom tokens: housing=%d population=%d" %
               (t.count("housing-headroom"), t.count("population-headroom")))
    out.append("")

open(os.path.join(W, "dm_build_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_build_out.txt", len(out), "lines")
