"""Show, for each DM-relevant script, the DEATH-MATCH sections + file tails + rule counts."""
import os

DIRS = [os.path.join(os.path.dirname(os.path.abspath(__file__)), d) for d in ("aok_drs", "x1_drs", "x1p1_drs")]
NAMES = {
    60001: "ai petersen rules.per", 60002: "petersen deathmatch.per", 60003: "petersen constants?",
    60004: "petersen fishboat.per", 60005: "petersen warboat.per", 60006: "petersen warboat island.per",
    60007: "petersen supplement.per", 60008: "petersen difficulty loads.per", 60009: "petersen full tech.per",
    60010: "petersen map loads.per", 60011: "petersen civ loads.per", 60012: "petersen gather.per",
    60013: "petersen diplomacy.per", 60014: "petersen dip bully.per", 60015: "petersen dip insult.per",
    60016: "petersen wonder.per", 60017: "petersen castle.per", 60018: "petersen market.per",
    60019: "petersen tower.per", 60020: "petersen upgrades.per", 60021: "petersen rush.per",
    60022: "petersen groups.per", 60023: "petersen resign.per", 60024: "wonder kill.per",
    60025: "wonder rush.per", 60026: "randomgame.per", 60027: "petersen constants.per",
    60028: "petersen dip liar.per", 60029: "petersen dip feeder.per",
}
TARGETS = [60002, 60004, 60007, 60013, 60027, 60028, 60029]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dm_patch_scan_out.txt")
out = []


def load(idx):
    for d in DIRS:
        p = os.path.join(d, "anib_%d.bin" % idx)
        if os.path.exists(p):
            raw = open(p, "rb").read()
            try:
                t = raw.decode("utf-8")
            except UnicodeDecodeError:
                t = raw.decode("latin-1")
            return d, p, t
    return None, None, None


for idx in TARGETS:
    d, p, txt = load(idx)
    out.append("=" * 70)
    out.append("anib_%d.bin  %s   dir=%s  bytes=%d  lines=%d" % (idx, NAMES.get(idx, "?"), os.path.basename(d), len(txt.encode("utf-8", "ignore")), txt.count("\n") + 1))
    rows = txt.split("\n")
    hits = [i for i, r in enumerate(rows) if "DEATH" in r.upper()]
    out.append("  DEATH mentions at lines: %s" % [h + 1 for h in hits][:40])
    for h in hits:
        out.append("  --- context around line %d ---" % (h + 1))
        for j in range(max(0, h - 5), min(len(rows), h + 6)):
            out.append("  %5d| %s" % (j + 1, rows[j].rstrip()))
        out.append("")
    out.append("  --- last 12 lines ---")
    for j in range(max(0, len(rows) - 12), len(rows)):
        out.append("  %5d| %s" % (j + 1, rows[j].rstrip()))
    out.append("")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("wrote", OUT, len(out), "lines")
