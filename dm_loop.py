"""Dump the DM reset/loop rules near line 2343 and the villager / need-deathmatch-villagers rules."""
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "x1_drs", "anib_60002.bin")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dm_loop_out.txt")
with open(P, "rb") as f:
    raw = f.read()
try:
    txt = raw.decode("utf-8")
except UnicodeDecodeError:
    txt = raw.decode("latin-1")
rows = txt.split("\n")
lines = []


def block(a, b, title):
    lines.append("=== %s (lines %d-%d) ===" % (title, a, b))
    for i in range(a - 1, min(b, len(rows))):
        lines.append("%5d| %s" % (i + 1, rows[i].rstrip("\r")))
    lines.append("")


block(2300, 2420, "around the secondary-build reset")

lines.append("=== rules setting need-deathmatch-villagers YES ===")
seen = set()
for i, r in enumerate(rows):
    if "need-deathmatch-villagers YES" in r:
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

lines.append("=== rules with (train villager) ===")
seen = set()
for i, r in enumerate(rows):
    if "(train villager)" in r:
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

lines.append("=== every rule whose conditions mention villager count ===")
seen = set()
for i, r in enumerate(rows):
    if "unit-type-count" in r and "villager" in r:
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

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote", OUT, len(lines), "lines")
