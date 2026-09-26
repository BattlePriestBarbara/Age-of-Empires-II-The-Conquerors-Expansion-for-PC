"""Look at the death-match villager logic + the AI folder stub file."""
import os
import re

W = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("AOE2HD_DIR") or r"D:\新建文件夹 (10)\3DMGAME_Age_of_EMPires_II_HD.CHS.Green".replace("of_EMPires", "of_Empires")
GAME = os.environ.get("AOE2HD_DIR") or r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green\Age of Empires II HD"
out = []
p = os.path.join(GAME, "AI", "AI.txt")
raw = open(p, "rb").read() if os.path.exists(p) else b"<missing>"
out.append("AI\\AI.txt = %r (%d bytes)" % (raw, len(raw)))

for path in (os.path.join(W, "x1_drs", "anib_60002.bin"),):
    rows = open(path, encoding="latin-1").read().split("\n")
    out.append("")
    out.append("--- (need-deathmatch-villagers ...) sites in petersen deathmatch.per ---")
    for i, r in enumerate(rows):
        if "need-deathmatch-villagers" in r:
            out.append("%5d| %s" % (i + 1, r.rstrip("\r")))
    out.append("")
    out.append("--- (train villager) / villager rules ---")
    for i, r in enumerate(rows):
        if re.search(r"\(train\s+villager\)|villager-count|defconst need-deathmatch-villagers", r):
            out.append("%5d| %s" % (i + 1, r.rstrip("\r")))
txt = "\n".join(out)
open(os.path.join(W, "dm_villagers_out.txt"), "w", encoding="utf-8").write(txt + "\n")
print(txt[:6000])
