"""dm_limit.py -- PE level lookup: where does the AI preprocessor compare its
nesting depth, and against what value?  (ERR3003: Preprocessor nesting too deep)
"""
import os
import re
import struct
import sys

GAME = os.environ.get("AOE2HD_DIR") or (r"D:\新建文件夹 (10)\3DMGAME_Age_of_Empires_II_HD.CHS.Green"
        r"\Age of Empires II HD")
path = os.path.join(GAME, "AoK HD.exe")
data = open(path, "rb").read()
out = []

# ---- PE headers (proper DOS->PE) ----
e_lfanew = struct.unpack_from("<I", data, 0x3c)[0]
assert data[e_lfanew:e_lfanew + 4] == b"PE\0\0", "bad e_lfanew 0x%x" % e_lfanew
nsec, = struct.unpack_from("<H", data, e_lfanew + 6)
opt = e_lfanew + 24
magic, = struct.unpack_from("<H", data, opt)
image_base = struct.unpack_from("<I", data, opt + 28)[0]
secoff = e_lfanew + 24 + struct.unpack_from("<H", data, e_lfanew + 20)[0]
secs = []
for i in range(nsec):
    o = secoff + 40 * i
    name = data[o:o + 8].rstrip(b"\0").decode("latin-1")
    vsize, va, rawsize, rawptr = struct.unpack_from("<IIII", data, o + 8)
    secs.append([name, va, vsize, rawptr, rawsize])
out.append("e_lfanew=0x%x magic=0x%04x image_base=0x%08x sections=%d"
           % (e_lfanew, magic, image_base, nsec))
for s in secs:
    out.append("   %-8s VA=0x%08x vsize=0x%06x raw=0x%08x size=0x%06x" % tuple(s))


def off2va(off):
    for name, va, vsize, rawptr, rawsize in secs:
        if rawptr <= off < rawptr + rawsize:
            return image_base + va + (off - rawptr), name
    return None, None


def va2off(va):
    rva = va - image_base
    for name, sva, vsize, rawptr, rawsize in secs:
        if sva <= rva < sva + max(vsize, rawsize):
            return rawptr + (rva - sva), name
    return None, None


for needle in (b"ERR3003: Preprocessor nesting too deep",
               b"ERR2012: Constant Already Defined",
               b"ERR3006: Missing #end-if",
               b"too many nested #includes",
               b"ERR3004: Unexpected #else",
               b"AI Script Error",
               b"AILog\\%s.log",
               b"AI\\%s"):
    hits = [m.start() for m in re.finditer(re.escape(needle), data)]
    out.append("\n### %s  (%d hit)" % (needle.decode("latin-1"), len(hits)))
    for h in hits:
        va, sec = off2va(h)
        out.append("   string @file 0x%08x -> VA %s (%s)"
                   % (h, ("0x%08x" % va) if va else "?", sec))
        if va is None:
            continue
        for r in [m.start() for m in re.finditer(re.escape(struct.pack("<I", va)),
                                                data)]:
            rva, rsec = off2va(r)
            out.append("      ref @file 0x%08x (VA 0x%08x, %s)" % (r, rva, rsec))
            lo, hi = max(0, r - 48), min(len(data), r + 32)
            for k in range(lo, hi, 16):
                chunk = data[k:k + 16]
                out.append("         %08x  %s  %s"
                           % (k, " ".join("%02x" % c for c in chunk),
                              "".join(chr(c) if 32 <= c < 127 else "."
                                      for c in chunk)))
open("dm_limit_out.txt", "w", encoding="utf-8").write("\n".join(out))
print("wrote dm_limit_out.txt")
