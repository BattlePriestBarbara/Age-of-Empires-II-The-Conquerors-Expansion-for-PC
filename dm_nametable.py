"""dm_nametable.py -- dump the code that references the .per name table
(0x543980..0x543c10) and the "%s%s.per" users, to learn whether the engine
opens AI scripts from the DRS (name -> anib id) or from loose AI\\*.per files.
"""
import os
import re

W = os.path.dirname(os.path.abspath(__file__))
GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
data = open(os.path.join(GAME, "AoK HD.exe"), "rb").read()
out = []


def dump(va, size, title):
    off = va - 0x400000
    out.append("\n=== %s  @VA 0x%08x" % (title, va))
    for k in range(off, min(len(data), off + size), 16):
        chunk = data[k:k + 16]
        out.append("   %08x  %s   %s"
                   % (k, " ".join("%02x" % b for b in chunk),
                      "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)))


dump(0x543960, 0x2d0, "the 29 x 'offset name' references (ascending VA)")
dump(0x508cf0, 0xc0, "'%s%s.per' user #1")
dump(0x5ab3e0, 0x250, "'%s%s.per' users #2..#5")

out.append("\n=== which functions are involved (call targets from 0x543960..0x543c70)")
region = data[0x143960:0x143c70]
for m in re.finditer(rb"\xe8(.)(.)(.)(.)", region):
    rel = int.from_bytes(m.group(1) + m.group(2) + m.group(3) + m.group(4),
                         "little", signed=True)
    here = 0x543960 + m.start()
    out.append("   call 0x%08x  (from 0x%08x)" % (here + 5 + rel, here))

open(os.path.join(W, "dm_nametable_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_nametable_out.txt")
