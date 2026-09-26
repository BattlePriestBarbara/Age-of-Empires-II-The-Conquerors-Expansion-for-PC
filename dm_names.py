"""dm_names.py -- (a) the hardcoded .per name table in AoK HD.exe and its order
(= anib id order?), (b) how the engine builds the AI path ("AI\%s"), (c) who
calls the DRS lookup for those names.
"""
import os
import re
import struct

W = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
data = open(os.path.join(GAME, "AoK HD.exe"), "rb").read()
out = []


def s(off, n=90):
    b = data[max(0, off - n):off + n]
    return "".join(chr(c) if 32 <= c < 127 else ("|" if c == 0 else ".") for c in b)


out.append("=== every 'petersen' string and its address")
for m in re.finditer(rb"[ -~]*petersen[ -~]*", data):
    out.append("   @0x%08x (file 0x%08x)  '%s'"
               % (m.start() + 0x400000, m.start(), m.group(0).decode("latin-1")))

out.append("\n=== every '.per' string")
for m in re.finditer(rb"[ -~]{4,}\.per\x00", data):
    out.append("   @0x%08x  '%s'" % (m.start() + 0x400000, m.group(0)[:-1].decode("latin-1")))

out.append("\n=== strings mentioning 'AI' as a path / extension")
for pat in (rb"AI\x00", rb"AI\\[ -~]{0,20}\x00", rb"\.ai\x00", rb"[ -~]{0,10}AI\x5c[ -~]{0,10}\x00"):
    for m in re.finditer(pat, data):
        off = m.start()
        if off + 0x400000 < 0x370000 or off + 0x400000 > 0x390000:
            continue
        out.append("   @0x%08x  %r  ctx=%s" % (off + 0x400000, m.group(0), s(off, 40)))

out.append("\n=== the AI-name table region around the .per names (hex+ascii)")
if re.search(rb"petersen", data):
    first = re.search(rb"petersen deathmatch\.per\x00", data)
    if first:
        out.append("   'petersen deathmatch.per' @0x%08x" % (first.start() + 0x400000))

out.append("\n=== data refs (absolute VA) to each .per name -> code that uses the table")
names = [m for m in re.finditer(rb"[ -~]{4,}\.per\x00", data)]
for m in names[:40]:
    va = m.start() + 0x400000
    refs = [x.start() for x in re.finditer(re.escape(struct.pack("<I", va)), data)]
    out.append("   %-28s VA 0x%08x refs=%d %s"
               % (m.group(0)[:-1].decode("latin-1"), va, len(refs),
                  " ".join("0x%08x" % (r + 0x400000) for r in refs[:6])))
open(os.path.join(W, "dm_names_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_names_out.txt")
