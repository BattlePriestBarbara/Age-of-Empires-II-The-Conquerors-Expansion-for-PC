"""dm_popswitch.py -- decode the engine's switch that defines POPULATION-CAP-*,
to see what happens for a lobby population limit of 500 (default branch?).
"""
import os

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


dump(0x45c900, 0x170, "difficulty switch + pop-cap switch")
dump(0x45cc00, 0x40, "jump table A (difficulty?)")
dump(0x45cc10, 0x40, "jump table B (pop-cap?)")

# what is at 0x904020 / 0x903ffc / 0x904004 ?
out.append("\n=== refs to the globals used by these switches")
import re
import struct
for va in (0x904020, 0x903ffc, 0x904004, 0x904008):
    pat = struct.pack("<I", va)
    sites = []
    i = data.find(pat, 0x1000, 0x2f0000)
    while i != -1 and len(sites) < 12:
        sites.append("0x%08x" % (0x400000 + i - 2))
        i = data.find(pat, i + 1)
    out.append("   0x%08x  written/read at (first 12): %s" % (va, ", ".join(sites)))

open(os.path.join(W, "dm_popswitch_out.txt"), "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_popswitch_out.txt")
