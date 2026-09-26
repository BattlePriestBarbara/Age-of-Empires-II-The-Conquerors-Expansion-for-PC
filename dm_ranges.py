"""Dump selected line ranges / rule blocks from the x1 Deathmatch AI script."""
import os
import re

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "x1_drs", "anib_60002.bin")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dm_ranges_out.txt")
with open(P, "rb") as f:
    raw = f.read()
try:
    txt = raw.decode("utf-8")
except UnicodeDecodeError:
    txt = raw.decode("latin-1")
rows = txt.split("\n")
lines = []


def dump(name, a, b):
    lines.append("=== %s  (lines %d-%d) ===" % (name, a, b))
    for i in range(a - 1, min(b, len(rows))):
        lines.append("%5d| %s" % (i + 1, rows[i].rstrip("\r")))
    lines.append("")


dump("difficulty blocks #1", 1345, 1435)
dump("difficulty blocks #2", 1675, 1710)
dump("tail", 2820, len(rows))

# rules containing resource checks
lines.append("=== rules mentioning *-amount ===")
for i, r in enumerate(rows):
    if re.search(r"(gold|wood|food|stone)-amount", r):
        a = i + 1
        # back up to the (defrule
        s = i
        while s > 0 and "(defrule" not in rows[s]:
            s -= 1
        e = i
        while e < len(rows) - 1 and "\n)" != rows[e] and rows[e].strip() != ")":
            e += 1
        for j in range(s, min(e + 1, len(rows))):
            lines.append("%5d| %s" % (j + 1, rows[j].rstrip("\r")))
        lines.append("  ---")

# rules mentioning housing-headroom / population-headroom
lines.append("=== rules mentioning headroom ===")
for i, r in enumerate(rows):
    if "headroom" in r:
        s = i
        while s > 0 and "(defrule" not in rows[s]:
            s -= 1
        e = i
        while e < len(rows) - 1 and rows[e].strip() != ")":
            e += 1
        for j in range(s, min(e + 1, len(rows))):
            lines.append("%5d| %s" % (j + 1, rows[j].rstrip("\r")))
        lines.append("  ---")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote", OUT, len(lines), "lines")
