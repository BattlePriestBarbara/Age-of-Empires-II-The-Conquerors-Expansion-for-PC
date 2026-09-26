"""List every POPULATION-CAP block in petersen constants (x1) with its deathmatch-unit-max."""
import os
import re

W = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(W, "x1_drs", "anib_60027.bin")
rows = open(p, encoding="latin-1").read().split("\n")
out = []
cur_cap = None
for i, r in enumerate(rows):
    m = re.search(r"#load-if-defined\s+(POPULATION-CAP-\d+)", r)
    if m:
        cur_cap = m.group(1)
    m = re.search(r"defconst\s+deathmatch-unit-max\s+(\d+)", r)
    if m and cur_cap:
        out.append("%-22s line %4d  deathmatch-unit-max = %s" % (cur_cap, i + 1, m.group(1)))
open(os.path.join(W, "dm_popcaps_out.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
