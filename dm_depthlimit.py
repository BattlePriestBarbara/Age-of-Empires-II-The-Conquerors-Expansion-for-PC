"""dm_depthlimit.py -- dump the AI preprocessor depth-check helper (0x42767E)
and its jump table siblings, to read the exact nesting limit.
"""
import os
import re
import struct

GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
data = open(os.path.join(GAME, "AoK HD.exe"), "rb").read()
out = []


def dump(va, size, title):
    off = va - 0x400000
    out.append("\n=== %s  @VA 0x%08x (%d bytes)" % (title, va, size))
    for k in range(off, min(len(data), off + size), 16):
        chunk = data[k:k + 16]
        out.append("   %08x  %s   %s"
                   % (k, " ".join("%02x" % b for b in chunk),
                      "".join(chr(c) if 32 <= c < 127 else "." for c in chunk)))


dump(0x4285EC, 16, "directive dispatch jump table (4 entries: id-1)")
for i in range(4):
    t = struct.unpack_from("<I", data, 0x4285EC - 0x400000 + 4 * i)[0]
    out.append("   table[%d] = 0x%08x" % (i, t))

dump(0x42767E, 224, "depth-check helper (called for #load-if-defined)")

# interpret every 'cmp reg, imm8' (83 /7 ib) and 'cmp reg, imm32' (81 /7)
out.append("\n=== cmp immediate scan inside the whole 0x427600-0x427c00 window")
base = 0x427600
win = data[base - 0x400000:base - 0x400000 + 0x600]
for m in re.finditer(rb"\x83([\xf8-\xff])(.)", win):
    out.append("   cmp r%d, 0x%02x   @0x%08x"
               % ((m.group(1)[0] - 0xf8), m.group(2)[0], base + m.start()))
for m in re.finditer(rb"\x81([\xf8-\xff])(.{4})", win):
    out.append("   cmp r%d, 0x%08x  @0x%08x"
               % ((m.group(1)[0] - 0xf8), struct.unpack("<I", m.group(2))[0],
                  base + m.start()))
open("dm_depthlimit_out.txt", "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_depthlimit_out.txt")
