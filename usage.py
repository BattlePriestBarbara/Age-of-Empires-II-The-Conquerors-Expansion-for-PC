"""Where are unit-max / need-deathmatch-villagers / villager training used?"""
import glob
import os
import re

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"x1_drs")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"usage_out.txt")
lines = []


def load(p):
    with open(p, "rb") as f:
        raw = f.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


lines.append("=== per-file counts: unit-max / deathmatch-unit-max / need-deathmatch-villagers / train villager ===")
for p in sorted(glob.glob(os.path.join(D, "anib_*"))):
    t = load(p)
    n1 = len(re.findall(r"\(population\s*<\s*unit-max\)", t))
    n2 = len(re.findall(r"deathmatch-unit-max", t))
    n3 = len(re.findall(r"need-deathmatch-villagers", t))
    n4 = len(re.findall(r"\(train villager\)", t))
    n5 = len(re.findall(r"unit-max", t))
    if n1 or n2 or n3 or n4 or n5:
        lines.append("%-18s %6d bytes  pop<unit-max=%3d  dm-unit-max=%3d  need-dm-vill=%3d  train-villager=%3d  all-unit-max=%3d"
                     % (os.path.basename(p), len(t), n1, n2, n3, n4, n5))
lines.append("")

dm = load(os.path.join(D, "anib_60002.bin"))
rows = dm.split("\n")
lines.append("=== DM script: rules mentioning need-deathmatch-villagers (whole rule) ===")
seen = set()
for i, r in enumerate(rows):
    if "need-deathmatch-villagers" not in r:
        continue
    s = i
    while s > 0 and "(defrule" not in rows[s]:
        s -= 1
    if s in seen:
        continue
    seen.add(s)
    e = i
    while e < len(rows) - 1 and rows[e].strip() != ")":
        e += 1
    for j in range(s, min(e + 1, len(rows))):
        lines.append("%5d| %s" % (j + 1, rows[j].rstrip("\r")))
    lines.append("")

lines.append("=== DM script: rules mentioning (train villager) ===")
seen = set()
for i, r in enumerate(rows):
    if "(train villager)" not in r:
        continue
    s = i
    while s > 0 and "(defrule" not in rows[s]:
        s -= 1
    if s in seen:
        continue
    seen.add(s)
    e = i
    while e < len(rows) - 1 and rows[e].strip() != ")":
        e += 1
    for j in range(s, min(e + 1, len(rows))):
        lines.append("%5d| %s" % (j + 1, rows[j].rstrip("\r")))
    lines.append("")

lines.append("=== main AI (anib_60001.bin): villager / army size logic samples ===")
main = load(os.path.join(D, "anib_60001.bin"))
mrows = main.split("\n")
for i, r in enumerate(mrows):
    if "(train villager)" in r or "unit-max" in r:
        s = i
        while s > 0 and "(defrule" not in mrows[s]:
            s -= 1
        for j in range(s, i + 1):
            lines.append("%5d| %s" % (j + 1, mrows[j].rstrip("\r")))
        lines.append("")
        if len(lines) > 3000:
            break

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote", OUT, len(lines), "lines")
