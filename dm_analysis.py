"""Analyse the Deathmatch AI script (anib 60002) and the constants file (anib 60027)."""
import os
import re
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "dm_analysis_out.txt")

X1 = os.path.join(BASE, "x1_drs")
AOK = os.path.join(BASE, "aok_drs")


def load(p):
    with open(p, "rb") as f:
        raw = f.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def tokens(txt):
    return re.findall(r"\(([a-zA-Z][a-zA-Z0-9_-]*)", txt)


lines = []
dm = load(os.path.join(X1, "anib_60002.bin"))
lines.append("=== x1 anib_60002.bin (= petersen deathmatch.per) %d bytes, %d lines ===" % (
    len(dm.encode("latin-1")), dm.count("\n") + 1))
lines.append("defrule count: %d" % dm.count("(defrule"))
lines.append("")
lines.append("--- first 90 lines ---")
for i, r in enumerate(dm.split("\n")[:90], 1):
    lines.append("%5d| %s" % (i, r.rstrip("\r")))

lines.append("")
lines.append("--- deathmatch-unit-max contexts (first 12) ---")
rows = dm.split("\n")
shown = 0
for i, r in enumerate(rows):
    if "deathmatch-unit-max" in r:
        for j in range(max(0, i - 6), min(len(rows), i + 4)):
            lines.append("%5d| %s" % (j + 1, rows[j].rstrip("\r")))
        lines.append("  ---")
        shown += 1
        if shown >= 12:
            break

# special #load / #if blocks in the DM file
lines.append("")
lines.append("--- preprocessor lines ---")
for i, r in enumerate(rows):
    s = r.strip()
    if s.startswith("#"):
        lines.append("%5d| %s" % (i + 1, s))

lines.append("")
lines.append("--- token frequency (top 120) ---")
cnt = Counter(tokens(dm))
for tok, c in cnt.most_common(120):
    lines.append("   %-42s %d" % (tok, c))

lines.append("")
lines.append("--- unit names used in (train X) ---")
tr = Counter(re.findall(r"\(train\s+([a-zA-Z0-9_-]+)", dm))
for tok, c in tr.most_common():
    lines.append("   train %-40s %d" % (tok, c))

lines.append("")
lines.append("--- subjects in (research X) ---")
rs = Counter(re.findall(r"\(research\s+([a-zA-Z0-9_-]+)", dm))
for tok, c in rs.most_common():
    lines.append("   research %-40s %d" % (tok, c))

lines.append("")
lines.append("--- timers (enable-timer X N) ---")
tm = Counter(re.findall(r"\(enable-timer\s+([a-zA-Z0-9_-]+)\s+([0-9]+)", dm))
for (tok, n), c in tm.most_common():
    lines.append("   enable-timer %-28s %-6s x%d" % (tok, n, c))

lines.append("")
lines.append("--- all (load \"...\") in DM file ---")
for m in sorted(set(re.findall(r'\(load\s+"([^"]+)"', dm))):
    lines.append("   " + m)

# ---- item facts used with numbers
lines.append("")
lines.append("--- facts with numeric comparisons (unit/pop/resource related) ---")
NUMPAT = re.compile(
    r"\((population|housing-headroom|soldier-count|villager|wood-amount|food-amount|gold-amount|stone-amount|"
    r"unit-type-count-total|unit-type-count|building-type-count|building-type-count-total|game-time|"
    r"current-age|current-age-time|military-population|civilian-population|idle-farm-count|"
    r"can-train|can-research|can-build|resource|unit-type-count-total)\s*([a-zA-Z0-9_-]*)\s*([<>=!]+)\s*([0-9a-zA-Z_-]+)")
pairs = Counter()
for m in NUMPAT.finditer(dm):
    pairs[(m.group(1), m.group(2), m.group(3), m.group(4))] += 1
for k, c in pairs.most_common(80):
    lines.append("   (%s %s %s %s)  x%d" % (k[0], k[1], k[2], k[3], c))

# ---- constants file
con = load(os.path.join(X1, "anib_60027.bin"))
lines.append("")
lines.append("=== x1 anib_60027.bin (= petersen constants.per) ===")
lines.append("--- defconts mentioning deathmatch / pop / timer ---")
for i, r in enumerate(con.split("\n")):
    if re.search(r"deathmatch|defconst|pop\b", r, re.I):
        lines.append("%5d| %s" % (i + 1, r.rstrip("\r")))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote", OUT, len(lines), "lines")
