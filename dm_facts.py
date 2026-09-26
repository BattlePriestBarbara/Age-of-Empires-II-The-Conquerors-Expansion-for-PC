"""Facts needed before patching: DM age-up path, AI.txt content, DRS entry table layout."""
import os

W = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("AOE2HD_DIR") or r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD"
out = []

p = os.path.join(GAME, "AI", "AI.txt")
if os.path.exists(p):
    raw = open(p, "rb").read()
    out.append("AI\\AI.txt bytes=%d repr=%r" % (len(raw), raw))
else:
    out.append("AI\\AI.txt NOT FOUND at %s" % p)

raw2 = open(os.path.join(W, "x1_drs", "anib_60002.bin"), "rb").read()
t = raw2.decode("latin-1")
rows = t.split("\n")
out.append("\n=== 60002 lines 1348-1440 (difficulty blocks / age up) ===")
for i in range(1347, 1440):
    out.append("%5d| %s" % (i + 1, rows[i].rstrip()))

out.append("\n=== 60002 rules mentioning age research ===")
for i, r in enumerate(rows):
    if "research" in r and ("age" in r):
        out.append("%5d| %s" % (i + 1, r.rstrip()))

out.append("\n=== 60002 rules mentioning cc-add-resource ===")
for i, r in enumerate(rows):
    if "cc-add-resource" in r or "add-resource" in r:
        out.append("%5d| %s" % (i + 1, r.rstrip()))

out.append("\n=== 60002 mentions of population-headroom / housing-headroom ===")
for i, r in enumerate(rows):
    if "headroom" in r:
        out.append("%5d| %s" % (i + 1, r.rstrip()))

open(os.path.join(W, "dm_facts_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_facts_out.txt", len(out), "lines")
