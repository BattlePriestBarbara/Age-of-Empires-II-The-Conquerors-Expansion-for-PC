"""dm_errs.py -- dump the AI preprocessor's whole error catalogue plus any
limit/"constant" related strings, and the AI symbol table region.
"""
import os
import re
import sys

GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
data = open(os.path.join(GAME, "AoK HD.exe"), "rb").read()
out = []


def strings(buf, minlen=4):
    cur = []
    for c in buf:
        if 32 <= c < 127:
            cur.append(chr(c))
        else:
            if len(cur) >= minlen:
                yield "".join(cur)
            cur = []


out.append("=== every ERR#### string in the exe (AI error catalogue)")
errs = sorted(set(s for s in strings(data) if re.search(r"ERR\d{4}", s)))
for s in errs:
    out.append("   %s" % s)

out.append("\n=== strings mentioning nested / constant / too many / limit")
for s in sorted(set(strings(data, 5))):
    low = s.lower()
    if any(k in low for k in ("nested", "constant", "too many", "limit",
                              "redefin", "undefined", "unknown", "invalid")):
        out.append("   %s" % s[:150])

out.append("\n=== symbol / token table around 0x373600-0x374600")
region = data[0x373600:0x374600]
out.append("   " + "".join(chr(c) if 32 <= c < 127 else ("\n   " if c == 0 else ".")
                           for c in region))

open("dm_errs_out.txt", "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_errs_out.txt  (%d ERR strings)" % len(errs))
