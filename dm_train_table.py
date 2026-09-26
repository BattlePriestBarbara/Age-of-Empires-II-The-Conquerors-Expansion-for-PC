"""Compact table of every (train ...) rule in the DM script: which gate does it use?"""
import os
import re

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "x1_drs", "anib_60002.bin")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dm_train_table.txt")
with open(P, "rb") as f:
    raw = f.read()
try:
    txt = raw.decode("utf-8")
except UnicodeDecodeError:
    txt = raw.decode("latin-1")
rows = txt.split("\n")
lines = ["%6s %-9s %-16s %s" % ("line", "secbld", "train", "conditions")]
for i, r in enumerate(rows):
    m = re.search(r"\(train\s+([a-zA-Z0-9_-]+)\)", r)
    if not m:
        continue
    s = i
    while s > 0 and "(defrule" not in rows[s]:
        s -= 1
    conds = []
    for j in range(s + 1, i):
        c = rows[j].strip()
        if not c or c == "=>":
            continue
        conds.append(c)
    sec = "yes" if any("secondary-build" in c for c in conds) else "NO"
    lines.append("%6d %-9s %-16s %s" % (i + 1, sec, m.group(1), " ".join(conds)))

# also: which goals guard the ungated rules
lines.append("")
lines.append("=== counts by gate ===")
sec_yes = sum(1 for l in lines[1:] if " yes " in l)
lines.append("rules gated by secondary-build: %d" % sec_yes)
lines.append("rules NOT gated: %d" % (len(lines) - 2 - sec_yes))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote", OUT, len(lines), "lines")
