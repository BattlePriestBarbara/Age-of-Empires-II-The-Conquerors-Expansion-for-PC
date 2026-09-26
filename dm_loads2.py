"""Dump x1 60026 in full and list every (load "...deathmatch...") call site."""
import os
import re

W = os.path.dirname(os.path.abspath(__file__))
out = []
L = [x.rstrip("\r") for x in open(os.path.join(W, "x1_drs", "anib_60026.bin"), "rb").read().decode("latin-1").split("\n")]
out.append("### x1_drs/anib_60026.bin full (%d lines)" % len(L))
for i, x in enumerate(L):
    out.append("%4d| %s" % (i + 1, x))
out.append("")
out.append("=== every (load \"...deathmatch...\") site in all unpacked DRS ===")
for d in ("aok_drs", "x1_drs", "x1p1_drs"):
    p = os.path.join(W, d)
    for f in sorted(os.listdir(p)):
        if not f.endswith(".bin"):
            continue
        rows = [x.rstrip("\r") for x in open(os.path.join(p, f), "rb").read().decode("latin-1").split("\n")]
        for i, x in enumerate(rows):
            if re.search(r'\(\s*load\s+"', x) and re.search(r"deathmatch|death-match", x, re.I):
                out.append("%s %s %6d| %s" % (d, f, i + 1, x.strip()))
open(os.path.join(W, "dm_loads2_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok", len(out))
