"""Per-file keyword counts across extracted anib AI scripts."""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "probe2_out.txt")
PATTERNS = [
    "deathmatch-unit-max",
    "DEATH-MATCH",
    "cc-add-resource",
    "(train ",
    "attack-now",
    "defconst",
    "(load \"",
    "(build ",
    "research",
    "cheat",
    "difficulty",
]

lines = []
# only the columns that matter, compact output
COLS = ["deathmatch-unit-max", "DEATH-MATCH", "cc-add-resource", "(train ", "(build ", "(load \""]
for d in ("x1_drs", "aok_drs", "x1p1_drs"):
    p = os.path.join(BASE, d)
    if not os.path.isdir(p):
        continue
    lines.append("== %s ==" % d)
    lines.append("file".ljust(18) + "size".rjust(8) + "".join(x[:18].rjust(20) for x in COLS))
    for f in sorted(os.listdir(p)):
        fp = os.path.join(p, f)
        if os.path.isdir(fp):
            continue
        with open(fp, "rb") as fh:
            raw = fh.read()
        try:
            txt = raw.decode("utf-8")
        except UnicodeDecodeError:
            txt = raw.decode("latin-1")
        low = txt.lower()
        counts = [low.count(x.lower()) for x in COLS]
        if sum(counts) == 0:
            continue
        lines.append(f.ljust(18) + str(len(raw)).rjust(8) + "".join(str(c).rjust(20) for c in counts))
    lines.append("")

# find cc-add-resource lines with context
lines.append("== cc-add-resource contexts ==")
for d in ("x1_drs", "aok_drs", "x1p1_drs"):
    p = os.path.join(BASE, d)
    if not os.path.isdir(p):
        continue
    for f in sorted(os.listdir(p)):
        fp = os.path.join(p, f)
        if os.path.isdir(fp):
            continue
        with open(fp, "rb") as fh:
            raw = fh.read()
        try:
            txt = raw.decode("utf-8")
        except UnicodeDecodeError:
            txt = raw.decode("latin-1")
        if "cc-add-resource" not in txt.lower():
            continue
        rows = txt.split("\n")
        for i, r in enumerate(rows):
            if "cc-add-resource" in r.lower():
                lines.append("%s\\%s L%d: %s" % (d, f, i + 1, r.strip()))

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
print("wrote", OUT, len(lines), "lines")
