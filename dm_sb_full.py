"""Every `secondary-build` use in the DM-loaded set, with rule context. Also file line-ending info."""
import os
import re

W = os.path.dirname(os.path.abspath(__file__))
out = []
for d in ("aok_drs", "x1_drs"):
    for f in ("anib_60002.bin", "anib_60007.bin", "anib_60010.bin", "anib_60012.bin",
              "anib_60013.bin", "anib_60015.bin", "anib_60016.bin", "anib_60021.bin",
              "anib_60026.bin", "anib_60027.bin"):
        p = os.path.join(W, d, f)
        raw = open(p, "rb").read()
        rows = raw.decode("latin-1").split("\n")
        hits = [i for i, x in enumerate(rows) if "secondary-build" in x]
        if not hits:
            continue
        out.append("### %s %s  (%d lines, crlf=%s, ends_nl=%s)  %d hits" %
                   (d, f, len(rows), b"\r\n" in raw, raw.endswith(b"\n"), len(hits)))
        # group hits into rule blocks (walk back to the enclosing "(defrule")
        shown = set()
        for i in hits:
            a = i
            while a > 0 and "(defrule" not in rows[a]:
                a -= 1
            b = i
            while b < len(rows) - 1 and not rows[b].strip().startswith(")"):
                b += 1
            if (a, b) in shown:
                continue
            shown.add((a, b))
            out.append("  --- rule at lines %d-%d ---" % (a + 1, b + 1))
            for j in range(a, min(b + 1, a + 22)):
                out.append("  %6d| %s" % (j + 1, rows[j].strip()))
        out.append("")
open(os.path.join(W, "dm_sb_full_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok", len(out))
