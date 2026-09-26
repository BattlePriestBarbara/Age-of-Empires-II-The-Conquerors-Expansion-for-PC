"""Map the DM AI load hierarchy: DEATH-MATCH #ifs, (load ...) graph, secondary-build loop."""
import glob
import os
import re

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"x1_drs")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"dm_loads_out.txt")
lines = []


def load(p):
    with open(p, "rb") as f:
        raw = f.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


NAMES = {
    60001: "ai petersen rules.per", 60002: "petersen deathmatch.per", 60003: "petersen upgrades.per",
    60004: "petersen fishboat.per", 60005: "petersen dip liar.per", 60006: "petersen warboat.per",
    60007: "petersen supplement.per", 60008: "petersen difficulty loads.per", 60009: "petersen full tech.per",
    60010: "petersen map loads.per", 60011: "petersen civ loads.per", 60012: "petersen tower.per",
    60013: "petersen diplomacy.per", 60014: "petersen castle.per", 60015: "petersen resign.per",
    60016: "petersen wonder.per", 60017: "petersen market.per", 60018: "petersen dip boomer.per",
    60019: "petersen gather.per", 60020: "petersen dip feeder.per", 60021: "petersen groups.per",
    60022: "petersen dip insult.per", 60023: "petersen dip bully.per", 60024: "petersen warboat island.per",
    60025: "petersen rush.per", 60026: "randomgame.per", 60027: "petersen constants.per",
    60028: "wonder rush.per", 60029: "wonder kill.per",
}

lines.append("=== per-file: DEATH-MATCH / GAME-TYPE mentions and (load ...) targets ===")
for p in sorted(glob.glob(os.path.join(D, "anib_*"))):
    t = load(p)
    fid = int(re.search(r"anib_(\d+)", p).group(1))
    dm_mentions = [m.group(0).strip() for m in re.finditer(r"#load-if[^\n]*DEATH[^\n]*", t)]
    loads = sorted(set(re.findall(r"\(load\s+\"([^\"]+)\"", t)))
    if dm_mentions or loads:
        lines.append("--- %s  (%s)  %d bytes" % (os.path.basename(p), NAMES.get(fid, "?"), len(t)))
        for m in dm_mentions:
            lines.append("      IF: %s" % m)
        for l in loads:
            lines.append("      LOAD: %s" % l)
lines.append("")

lines.append("=== anib_60026.bin (randomgame.per) full text ===")
t26 = load(os.path.join(D, "anib_60026.bin"))
for i, r in enumerate(t26.split("\n")):
    lines.append("%5d| %s" % (i + 1, r.rstrip("\r")))
lines.append("")

lines.append("=== anib_60008.bin (petersen difficulty loads.per) full text ===")
t08 = load(os.path.join(D, "anib_60008.bin"))
for i, r in enumerate(t08.split("\n")):
    lines.append("%5d| %s" % (i + 1, r.rstrip("\r")))
lines.append("")

lines.append("=== DM file: lines mentioning secondary-build ===")
dm = load(os.path.join(D, "anib_60002.bin"))
for i, r in enumerate(dm.split("\n")):
    if "secondary-build" in r:
        lines.append("%5d| %s" % (i + 1, r.rstrip("\r")))
lines.append("")

lines.append("=== DM file: context of first (set-goal secondary-build 1) rules ===")
rows = dm.split("\n")
seen = set()
for i, r in enumerate(rows):
    if "secondary-build 1" in r:
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
