"""Inspect the population-cap constants used by the death-match unit rules."""
import glob
import os
import re

W = os.path.dirname(os.path.abspath(__file__))
out = []
for pat in (r"defconst\s+(deathmatch-unit-max|unit-max|deathmatch-villager-max|villager-max)\b",
            r"deathmatch-unit-max",
            r"\bunit-max\b"):
    out.append("### /%s/" % pat)
    for d in ("aok_drs", "x1_drs", "x1p1_drs"):
        for p in sorted(glob.glob(os.path.join(W, d, "anib_*.bin"))):
            rows = open(p, encoding="latin-1").read().split("\n")
            for i, r in enumerate(rows):
                if re.search(pat, r):
                    out.append("%-4s %-16s %5d| %s" % (d, os.path.basename(p), i + 1, r.strip()))
    out.append("")
open(os.path.join(W, "dm_caps_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("lines=%d" % len(out))
