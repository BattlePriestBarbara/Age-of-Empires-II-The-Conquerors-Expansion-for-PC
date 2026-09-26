"""Find where unit-max is defined and show the pop-cap / deathmatch-unit-max #if context."""
import glob
import os
import re

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"x1_drs")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unitmax_out.txt")
lines = []


def load(p):
    with open(p, "rb") as f:
        raw = f.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


lines.append("=== files defining unit-max / pop-cap / deathmatch-unit-max ===")
for p in sorted(glob.glob(os.path.join(D, "anib_*"))):
    t = load(p)
    for m in re.finditer(r"\(defconst\s+(unit-max|pop-cap|deathmatch-unit-max)\b[^\n]*", t):
        ln = t[: m.start()].count("\n") + 1
        lines.append("%-18s L%-6d %s" % (os.path.basename(p), ln, m.group(0).strip()))

lines.append("")
lines.append("=== x1 anib_60027.bin: lines around each pop-cap block (with #if context) ===")
con = load(os.path.join(D, "anib_60027.bin"))
crows = con.split("\n")
idxs = [i for i, r in enumerate(crows) if "pop-cap" in r]
for i in idxs:
    # find enclosing #load-if up to 60 lines back
    start = i
    for j in range(i, max(-1, i - 80), -1):
        if crows[j].lstrip().startswith("#load-if") or crows[j].lstrip().startswith("#end-if"):
            start = j
            break
    lines.append("--- block at line %d (context from %d) ---" % (i + 1, start + 1))
    for j in range(start, min(len(crows), i + 4)):
        lines.append("%5d| %s" % (j + 1, crows[j].rstrip("\r")))

lines.append("")
lines.append("=== every # directiive in anib_60027.bin ===")
for i, r in enumerate(crows):
    if r.lstrip().startswith("#"):
        lines.append("%5d| %s" % (i + 1, r.rstrip("\r")))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("wrote", OUT, len(lines), "lines")
