"""Dump the train/build/research rules of the DM script plus the can-* vocabulary."""
import os
import re
from collections import Counter

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "x1_drs", "anib_60002.bin")
C = os.path.join(os.path.dirname(os.path.abspath(__file__)), "x1_drs", "anib_60027.bin")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dm_train_out.txt")


def load(p):
    with open(p, "rb") as f:
        raw = f.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


dm = load(P)
con = load(C)
rows = dm.split("\n")
crows = con.split("\n")
lines = []

lines.append("=== can-* vocabulary used in DM script ===")
for key in ("can-train", "can-research", "can-build", "can-sell-commodity", "can-buy-commodity"):
    c = Counter(re.findall(r"\(%s\s+([a-zA-Z0-9_-]+)" % key, dm))
    lines.append("-- %s: %s" % (key, ", ".join(sorted(c))))
lines.append("")

lines.append("=== every rule containing (train ...) with its conditions ===")
for i, r in enumerate(rows):
    if "(train " not in r:
        continue
    s = i
    while s > 0 and "(defrule" not in rows[s]:
        s -= 1
    e = i
    while e < len(rows) - 1 and rows[e].strip() != ")":
        e += 1
    for j in range(s, min(e + 1, len(rows))):
        lines.append("%5d| %s" % (j + 1, rows[j].rstrip("\r")))
    lines.append("")

lines.append("")
lines.append("=== rules containing (build ...) : only conditions ===")
for i, r in enumerate(rows):
    if "(build " not in r:
        continue
    s = i
    while s > 0 and "(defrule" not in rows[s]:
        s -= 1
    conds = [rows[j].strip() for j in range(s, i)]
    lines.append("%5d| %s   ==> %s" % (i + 1, " ".join(conds), r.strip()))
lines.append("")

lines.append("=== constants file: unit-max / deathmatch-unit-max blocks ===")
for i, r in enumerate(crows):
    if re.search(r"unit-max|population-cap|defconst .*(pop|max)", r):
        for j in range(max(0, i - 8), min(len(crows), i + 3)):
            lines.append("%5d| %s" % (j + 1, crows[j].rstrip("\r")))
        lines.append("   ---")

lines.append("")
lines.append("=== constants file: every defconst line (name value) ===")
for i, r in enumerate(crows):
    m = re.search(r"\(defconst\s+([a-zA-Z0-9_-]+)\s+([^\)]+)\)", r)
    if m:
        lines.append("%5d| %-34s %s" % (i + 1, m.group(1), m.group(2).strip()))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote", OUT, len(lines), "lines")
